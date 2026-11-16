"""Scalar block graph with one level of virtual subsystems, written as a Simulink MDL file.

The pattern: Python only writes the graph. Every equation is a chain of primitive blocks (Sum, Product, Gain-free
Constant, Trigonometry, Math, Sqrt, MinMax, Saturate, Abs, Step) and every state is an explicit
Integrator. No integration happens here.

Carried over from an earlier flight study by the same author with one addition: `schedule()`, a
time table (library block "Repeating Sequence": linear interpolation of a workspace vector over a
workspace time vector), used for the command inputs.

Differences from the F1 builder:
  - every block belongs to a named subsystem; signals that cross a subsystem boundary get an Outport
    in the source subsystem, an Inport in the destination subsystem and a line at the root level,
  - blocks carry a label, a unit and an optional physical part, which go into the wiring manifest,
  - block positions are a layered layout so the Unlinked renderer draws a readable diagram.

Stable signal IDs after Unlinked flattens the subsystems are "<subsystem SID>/<block SID>".
"""
from __future__ import annotations

import collections
import json


class Node:
    __slots__ = ('g', 'i')

    def __init__(self, g, i):
        self.g, self.i = g, i

    # arithmetic builds blocks in the subsystem that is current when the expression is written
    def __add__(self, o):
        return self.g.op('Sum', [self, o], Inputs='++')

    __radd__ = __add__

    def __sub__(self, o):
        return self.g.op('Sum', [self, o], Inputs='+-')

    def __rsub__(self, o):
        return self.g.op('Sum', [o, self], Inputs='+-')

    def __mul__(self, o):
        return self.g.op('Product', [self, o], Inputs='**')

    __rmul__ = __mul__

    def __truediv__(self, o):
        return self.g.op('Product', [self, o], Inputs='*/')

    def __rtruediv__(self, o):
        return self.g.op('Product', [o, self], Inputs='*/')

    def __neg__(self):
        return self.g.op('Product', [self, -1], Inputs='**')

    def n(self, label, unit=None, part=None):
        """Label this block (and optionally give its unit and the aircraft part it belongs to)."""
        d = self.g.nodes[self.i - 1]
        d['label'] = label
        d['named'] = True
        if unit is not None:
            d['unit'] = unit
        if part is not None:
            d['part'] = part
        return self


class Graph:
    def __init__(self, name):
        self.name = name
        self.nodes = []
        self.links = []                 # (src i, dst i, dst port)
        self.subs = collections.OrderedDict()   # name -> dict(description, part)
        self.cur = None
        self._const = {}
        self.outputs = collections.OrderedDict()

    # ---- subsystems
    def subsystem(self, name, description, part=None):
        if name not in self.subs:
            self.subs[name] = dict(description=description, part=part)
        self.cur = name
        return self

    # ---- blocks
    def add(self, kind, label=None, **p):
        assert self.cur is not None, 'choose a subsystem first'
        i = len(self.nodes) + 1
        self.nodes.append(dict(i=i, kind=kind, label=label or '', named=bool(label), params={k: str(v) for k, v in p.items()},
                               sub=self.cur, unit=None, part=None))
        return Node(self, i)

    def c(self, x):
        """Constant block in the current subsystem: a number or the name of a workspace variable."""
        if isinstance(x, Node):
            return x
        key = (self.cur, repr(float(x)) if isinstance(x, (int, float)) else str(x))
        if key not in self._const:
            n = self.add('Constant', Value=key[1])
            self.nodes[n.i - 1]['label'] = key[1]
            self.nodes[n.i - 1]['named'] = isinstance(x, str)
            self._const[key] = n
        return self._const[key]

    def op(self, kind, args, **p):
        args = [self.c(a) for a in args]
        n = self.add(kind, **p)
        for port, src in enumerate(args, 1):
            self.links.append((src.i, n.i, port))
        return n

    def trig(self, kind, *x):
        return self.op('Trigonometry', list(x), Operator=kind)

    def sin(self, x):
        return self.trig('sin', x)

    def cos(self, x):
        return self.trig('cos', x)

    def tan(self, x):
        return self.trig('tan', x)

    def asin(self, x):
        return self.trig('asin', x)

    def acos(self, x):
        return self.trig('acos', x)

    def atan2(self, y, x):
        return self.trig('atan2', y, x)

    def sqrt(self, x):
        return self.op('Sqrt', [x], Operator='sqrt')

    def pow(self, x, y):
        return self.op('Math', [x, y], Operator='pow')

    def abs(self, x):
        return self.op('Abs', [x])

    def min(self, a, b):
        return self.op('MinMax', [a, b], Function='min', Inputs='2')

    def max(self, a, b):
        return self.op('MinMax', [a, b], Function='max', Inputs='2')

    def clip(self, x, lo, hi):
        """Saturation with fixed limits (numbers or workspace expressions)."""
        return self.op('Saturate', [x], LowerLimit=str(lo), UpperLimit=str(hi))

    def clip_dyn(self, x, lo, hi):
        """Saturation with signal limits: min(max(x, lo), hi)."""
        return self.min(self.max(x, lo), hi)

    def step(self, time, before, after, label):
        return self.add('Step', label, Time=str(time), Before=str(before), After=str(after))

    def schedule(self, label, t_var, y_var, unit=None, part=None):
        """Command time table: y(t) by linear interpolation of the workspace vector y_var over t_var.
        Written as the library block "Repeating Sequence"; the time vector ends after the end of the run,
        so it never repeats."""
        n = self.add('Reference', label, SourceBlock='simulink/Sources/Repeating Sequence', rep_seq_t=t_var, rep_seq_y=y_var)
        d = self.nodes[n.i - 1]
        d['unit'], d['part'] = unit, part
        return n

    def state(self, label, initial, unit=None, part=None):
        n = self.add('Integrator', label, InitialCondition=str(initial))
        d = self.nodes[n.i - 1]
        d['unit'], d['part'] = unit, part
        return n

    def derivative(self, state, value):
        sub = self.cur
        self.cur = self.nodes[state.i - 1]['sub']     # a literal derivative becomes a constant beside the state
        v = self.c(value)
        self.cur = sub
        self.links.append((v.i, state.i, 1))

    def output(self, name, node, unit, part=None, note=None):
        assert name not in self.outputs, name
        self.outputs[name] = dict(node=node.i, unit=unit, part=part, note=note)
        d = self.nodes[node.i - 1]
        if not d['named']:
            d['label'], d['named'] = name, True
        if d['unit'] is None:
            d['unit'] = unit
        if part is not None and d['part'] is None:
            d['part'] = part

    # ---- writing
    def _prepare(self):
        """Subsystem SIDs, boundary ports and unique block names."""
        if getattr(self, '_ready', False):
            return
        sid = len(self.nodes)
        self.sub_sid = {}
        for s in self.subs:
            sid += 1
            self.sub_sid[s] = sid
        self.inports = collections.OrderedDict()    # (dst sub, src node) -> dict(sid, port)
        self.outports = collections.OrderedDict()   # src node -> dict(sid, port)
        n_in = collections.Counter()
        n_out = collections.Counter()
        for a, b, _ in self.links:
            sa, sb = self.nodes[a - 1]['sub'], self.nodes[b - 1]['sub']
            if sa == sb:
                continue
            if a not in self.outports:
                sid += 1
                n_out[sa] += 1
                self.outports[a] = dict(sid=sid, port=n_out[sa], sub=sa)
            if (sb, a) not in self.inports:
                sid += 1
                n_in[sb] += 1
                self.inports[(sb, a)] = dict(sid=sid, port=n_in[sb], sub=sb)
        self.n_in, self.n_out = n_in, n_out
        self.last_sid = sid
        # unique names inside each subsystem
        used = collections.defaultdict(set)
        for d in self.nodes:
            base = d['label'] if d['named'] else {'Sum': 'add', 'Product': 'mul', 'Constant': 'const'}.get(d['kind'], d['kind'].lower())
            if d['kind'] == 'Constant' and not d['named']:
                base = d['params']['Value']
            name = base
            if name in used[d['sub']] or not d['named']:
                name = f'{base} #{d["i"]}'
            used[d['sub']].add(name)
            d['name'] = name
        for a, o in self.outports.items():
            o['name'] = self._port_name(used, o['sub'], 'out ' + self.nodes[a - 1]['name'])
        for (sb, a), p in self.inports.items():
            p['name'] = self._port_name(used, sb, 'in ' + self.nodes[a - 1]['name'])
        self._layout()
        self._ready = True

    @staticmethod
    def _port_name(used, sub, base):
        name, k = base, 1
        while name in used[sub]:
            k += 1
            name = f'{base} ({k})'
        used[sub].add(name)
        return name

    def _layout(self):
        """Layered left-to-right placement per subsystem. Integrators start a new chain."""
        ins = collections.defaultdict(list)
        for a, b, _ in self.links:
            ins[b].append(a)
        depth = {}

        def d_of(i, stack=()):
            if i in depth:
                return depth[i]
            d = self.nodes[i - 1]
            if d['kind'] in ('Integrator', 'Constant', 'Step', 'Reference'):
                depth[i] = 1 if d['kind'] == 'Integrator' else 0
                return depth[i]
            best = 0
            for a in ins[i]:
                if self.nodes[a - 1]['sub'] != d['sub']:
                    best = max(best, 1)
                elif a in stack:
                    continue
                else:
                    best = max(best, d_of(a, stack + (i,)) + 1)
            depth[i] = best
            return best

        import sys
        sys.setrecursionlimit(10000)
        rows = collections.defaultdict(lambda: collections.Counter())
        for d in self.nodes:
            k = d_of(d['i'])
            if d['kind'] == 'Constant':
                # put a constant one column left of its first user
                users = [b for a, b, _ in self.links if a == d['i']]
                k = max(0, min((d_of(b) for b in users), default=1) - 1)
            r = rows[d['sub']][k]
            rows[d['sub']][k] += 1
            d['pos'] = (140 + k * 150, 30 + r * 46, 140 + k * 150 + 90, 30 + r * 46 + 30)
            d['col'] = k
        self.sub_cols = {s: (max(c) if c else 0) for s, c in rows.items()}
        cnt = collections.Counter()
        for (sb, a), p in self.inports.items():
            r = cnt[('i', sb)]
            cnt[('i', sb)] += 1
            p['pos'] = (20, 30 + r * 30, 50, 30 + r * 30 + 14)
        for a, o in self.outports.items():
            r = cnt[('o', o['sub'])]
            cnt[('o', o['sub'])] += 1
            x = 140 + (self.sub_cols.get(o['sub'], 0) + 1) * 150 + 60
            o['pos'] = (x, 30 + r * 30, x + 30, 30 + r * 30 + 14)

    def flat_id(self, i):
        """Stable signal ID of node i in the flattened graph."""
        self._prepare()
        return f'{self.sub_sid[self.nodes[i - 1]["sub"]]}/{i}'

    def write_mdl(self, path, stop=60, step=1 / 240):
        self._prepare()
        q = lambda x: json.dumps(str(x))
        L = ['Model {', f' Name {q(self.name)}', ' Version 8.0', ' Solver "ode4"', ' StartTime "0"', f' StopTime "{stop}"',
             f' FixedStep "{step!r}"', ' System {', f'  Name {q(self.name)}']
        names = list(self.subs)
        for k, s in enumerate(names):
            col, row = k % 4, k // 4
            x, y = 60 + col * 260, 60 + row * 220
            h = 40 + 14 * max(self.n_in[s], self.n_out[s], 2)
            L += ['  Block {', '   BlockType SubSystem', f'   Name {q(s)}', f'   SID "{self.sub_sid[s]}"',
                  f'   Position [{x}, {y}, {x + 150}, {y + h}]', f'   Ports [{self.n_in[s]}, {self.n_out[s]}]', '   System {',
                  f'    Name {q(s)}']
            for (sb, a), p in self.inports.items():
                if sb == s:
                    L += ['    Block {', '     BlockType Inport', f'     Name {q(p["name"])}', f'     SID "{p["sid"]}"',
                          '     Position [%d, %d, %d, %d]' % p['pos'], f'     Port "{p["port"]}"', '    }']
            for d in self.nodes:
                if d['sub'] != s:
                    continue
                L += ['    Block {', f'     BlockType {d["kind"]}', f'     Name {q(d["name"])}', f'     SID "{d["i"]}"',
                      '     Position [%d, %d, %d, %d]' % d['pos']]
                L += [f'     {k2} {q(v)}' for k2, v in d['params'].items()]
                L += ['    }']
            for a, o in self.outports.items():
                if o['sub'] == s:
                    L += ['    Block {', '     BlockType Outport', f'     Name {q(o["name"])}', f'     SID "{o["sid"]}"',
                          '     Position [%d, %d, %d, %d]' % o['pos'], f'     Port "{o["port"]}"', '    }']
            done = set()
            for a, b, port in self.links:
                sa, sb = self.nodes[a - 1]['sub'], self.nodes[b - 1]['sub']
                if sb == s:
                    src = self.nodes[a - 1]['name'] if sa == s else self.inports[(s, a)]['name']
                    L += ['    Line {', f'     SrcBlock {q(src)}', '     SrcPort 1', f'     DstBlock {q(self.nodes[b - 1]["name"])}',
                          f'     DstPort {port}', '    }']
                if sa == s and sb != s and a not in done:
                    done.add(a)
                    L += ['    Line {', f'     SrcBlock {q(self.nodes[a - 1]["name"])}', '     SrcPort 1',
                          f'     DstBlock {q(self.outports[a]["name"])}', '     DstPort 1', '    }']
            L += ['   }', '  }']
        for (sb, a), p in self.inports.items():
            o = self.outports[a]
            L += ['  Line {', f'   SrcBlock {q(o["sub"])}', f'   SrcPort {o["port"]}', f'   DstBlock {q(sb)}', f'   DstPort {p["port"]}', '  }']
        L += [' }', '}']
        path.write_text('\n'.join(L) + '\n', encoding='utf-8')

    # ---- manifests
    def signals_manifest(self):
        self._prepare()
        return {name: dict(id=self.flat_id(o['node']), unit=o['unit'], block=self.nodes[o['node'] - 1]['name'],
                           subsystem=self.nodes[o['node'] - 1]['sub'], **({'part': o['part']} if o['part'] else {}),
                           **({'note': o['note']} if o['note'] else {}))
                for name, o in self.outputs.items()}

    def wiring_manifest(self):
        self._prepare()
        ins = collections.defaultdict(list)
        for a, b, port in self.links:
            ins[b].append((port, a))
        out_name = {o['node']: name for name, o in self.outputs.items()}
        blocks = []
        for d in self.nodes:
            blocks.append(dict(sid=d['i'], id=self.flat_id(d['i']), type=d['kind'], label=d['name'], named=d['named'],
                               subsystem=d['sub'], params=d['params'], unit=d['unit'], part=d['part'],
                               output=out_name.get(d['i']), column=d['col'],
                               inputs=[dict(port=p, sid=a, id=self.flat_id(a)) for p, a in sorted(ins[d['i']])]))
        subs = []
        for s, info in self.subs.items():
            members = [d for d in self.nodes if d['sub'] == s]
            subs.append(dict(name=s, sid=self.sub_sid[s], description=info['description'], part=info['part'],
                             blocks=[d['i'] for d in members], block_count=len(members),
                             types=dict(collections.Counter(d['kind'] for d in members)),
                             states=[dict(sid=d['i'], id=self.flat_id(d['i']), label=d['name'], unit=d['unit'],
                                          initial=d['params']['InitialCondition']) for d in members if d['kind'] == 'Integrator'],
                             inputs=[dict(from_sid=a, from_id=self.flat_id(a), from_subsystem=self.nodes[a - 1]['sub'],
                                          label=self.nodes[a - 1]['name'], unit=self.nodes[a - 1]['unit'], port=p['port'],
                                          boundary_id=f'{self.sub_sid[s]}/{p["sid"]}')
                                     for (sb, a), p in self.inports.items() if sb == s],
                             outputs=[dict(sid=a, id=self.flat_id(a), label=self.nodes[a - 1]['name'], unit=self.nodes[a - 1]['unit'],
                                           port=o['port'], to_subsystems=sorted({sb for (sb, a2) in self.inports if a2 == a}))
                                      for a, o in self.outports.items() if o['sub'] == s]))
        bus = collections.OrderedDict()
        for (sb, a), p in self.inports.items():
            d = self.nodes[a - 1]
            bus.setdefault((d['sub'], sb), []).append(dict(sid=a, id=self.flat_id(a), label=d['name'], unit=d['unit'], part=d['part'],
                                                           output=out_name.get(a)))
        return dict(blocks=blocks, subsystems=subs,
                    connections=[dict(src=a, dst=b, port=p) for a, b, p in self.links],
                    subsystem_links=[dict(src=k[0], dst=k[1], signals=v) for k, v in bus.items()],
                    counts=dict(blocks=len(self.nodes), connections=len(self.links), subsystems=len(self.subs),
                                boundary_ports=len(self.inports) + len(self.outports),
                                states=sum(d['kind'] == 'Integrator' for d in self.nodes),
                                types=dict(collections.Counter(d['kind'] for d in self.nodes))))
