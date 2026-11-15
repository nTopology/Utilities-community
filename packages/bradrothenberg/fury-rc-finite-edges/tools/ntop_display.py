"""Display records for a notebook written by `ntopcl convert`.

`ntopcl convert` stores the computation only (chunks turhe, main, cache). nTop itself adds display
chunks when it saves a notebook:

  sections      {"decorations": [{name, description, collapse}], "poles": [0, n1, ..., N]}
                consecutive index ranges over the top-level variables
  open          one row per node of the notebook tree with its collapsed state
  view          per body: shown or hidden, colour, display style
  viewport      camera
  customColors, res, tools   small records, taken unchanged from a notebook saved by nTop

This module reads and writes the container and builds those records. The computation blocks are
never edited: inside `main` only the order of the root group's inputs (the order of the notebook)
and the display names of variables may change.

Container: 'MAGIC%$1' + chunk count (u64) + 8 zero bytes + table entries (16-byte name, u64 end
offset relative to the first chunk) + 80 zero bytes, then the chunks. A chunk is 'MAGIC@@9' +
type (16) + name (16) + size (u64), padded to 128 bytes, then the payload. `ntopfn` chunks hold
chunks; `obj_container` chunks hold an 8-byte count and chunks.

Rows of `open` (the rule reproduces the rows of two notebooks saved by nTop, see --selftest):
  100_            the notebook root
  100_<i>         top-level variable i
  100_<i>_0       the block inside the variable, then _<k> for each input, recursively
  a reference to another variable is a leaf; literal values are leaves
"""
import json
import math
import struct
import sys
from pathlib import Path

MAGIC = b'MAGIC@@9'
HEADER = 128
ORDER = ['turhe', 'main', 'cache', 'customColors', 'open', 'res', 'sections', 'tools', 'view', 'viewport']
DISPLAY = ('customColors', 'open', 'res', 'sections', 'tools', 'view', 'viewport')
UIID0 = 4022


class Chunk:
    def __init__(self, typ, name, payload, children=None, prefix=b''):
        self.typ, self.name, self.payload, self.children, self.prefix = typ, name, payload, children, prefix

    def serialize(self):
        body = self.prefix + b''.join(c.serialize() for c in self.children) if self.children is not None else self.payload
        head = MAGIC + self.typ.encode().ljust(16, b'\0') + self.name.encode().ljust(16, b'\0') + struct.pack('<Q', len(body))
        return head.ljust(HEADER, b'\0') + body

    def find(self, name, typ=None):
        if self.name == name and (typ is None or self.typ == typ):
            return self
        for c in self.children or []:
            r = c.find(name, typ)
            if r is not None:
                return r
        return None


def _parse(buf, start, end):
    out, pos = [], start
    while pos < end:
        assert buf[pos:pos + 8] == MAGIC, 'no chunk marker at %d' % pos
        typ = buf[pos + 8:pos + 24].rstrip(b'\0').decode()
        name = buf[pos + 24:pos + 40].rstrip(b'\0').decode()
        size = struct.unpack('<Q', buf[pos + 40:pos + 48])[0]
        p0, p1 = pos + HEADER, pos + HEADER + size
        if typ == 'ntopfn':
            out.append(Chunk(typ, name, None, _parse(buf, p0, p1)))
        elif typ == 'obj_container':
            out.append(Chunk(typ, name, None, _parse(buf, p0 + 8, p1), buf[p0:p0 + 8]))
        else:
            out.append(Chunk(typ, name, buf[p0:p1]))
        pos = p1
    return out


def load(path):
    raw = Path(path).read_bytes()
    assert raw[:8] == b'MAGIC%$1', 'not an nTop container'
    return _parse(raw, raw.find(MAGIC, 24), len(raw))


def dump(chunks):
    chunks = sorted(chunks, key=lambda c: ORDER.index(c.name))
    body, table = b'', b''
    for c in chunks:
        body += c.serialize()
        table += c.name.encode().ljust(16, b'\0') + struct.pack('<Q', len(body))
    return b'MAGIC%$1' + struct.pack('<Q', len(chunks)) + b'\0' * 8 + table + b'\0' * 80 + body


def fn_chunk(chunks):
    return next(c for c in chunks if c.name == 'main').find('fn', 'json')


def code_of(chunks):
    return json.loads(fn_chunk(chunks).payload)


def set_json(chunks, name, data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    for c in chunks:
        if c.name == name:
            c.payload = payload
            return
    chunks.append(Chunk('json', name, payload))


def top_level(code):
    """(id, name, type) of the notebook's variables, in notebook order."""
    byid = {b['id']: b for b in code['code']}
    return [(i['instanceId'], byid[i['instanceId']]['name'], byid[i['instanceId']]['type']) for i in byid[100]['inputs']]


def references(code):
    """{variable id: set of the variable ids its blocks refer to}."""
    byid = {b['id']: b for b in code['code']}
    out = {}
    for inp in byid[100]['inputs']:
        refs, stack = set(), [byid[inp['instanceId']]]
        while stack:
            for x in stack.pop().get('inputs', []):
                child = byid.get(x.get('instanceId', -1))
                if child is None:
                    continue
                if child['func'].startswith('core.var<'):
                    refs.add(child['id'])
                else:
                    stack.append(child)
        out[inp['instanceId']] = refs
    return out


def tree_paths(code):
    """Paths of every node of the notebook tree, depth first, in the order nTop numbers them."""
    byid = {b['id']: b for b in code['code']}
    out = ['100_']

    def walk(block, path):
        out.append(path)
        for k, inp in enumerate(block.get('inputs', [])):
            child = byid.get(inp.get('instanceId', -1))
            if child is None:
                continue
            p = f'{path}_{k}'
            if child['func'].startswith('core.var<'):
                out.append(p)                       # reference to a variable: a leaf
            else:
                walk(child, p)

    for i, inp in enumerate(byid[100]['inputs']):
        walk(byid[inp['instanceId']], f'100_{i}')
    return out


def open_rows(code, collapsed=True):
    rows = []
    for n, path in enumerate(tree_paths(code)):
        root = path == '100_'
        rows.append(dict(collapsed=bool(collapsed and not root), modelIndex=-1, relativePath=path, uiid=11 if root else UIID0 + n - 1))
    return rows


def view_row(i, implicit, colour, visible, style=0):
    attrs = [dict(id=11, name='display_mode', type=2, value=0), dict(id=13, name='color', type=5, value=[float(v) for v in colour]),
             dict(id=22, name='display_style', type=2, value=style), dict(id=14, name='transparency', type=1, value=0), dict(id=15, name='opacity', type=3, value=50)]
    if implicit:
        zero = dict(x=0.0, y=0.0, z=0.0)
        attrs += [dict(id=101, name='implicit_clipping_show_hatched', type=1, value=1), dict(id=19, name='implicit_clipping_bounding_box_enable', type=1, value=0),
                  dict(id=20, name='implicit_clipping_bounding_box_min', type=6, value=zero), dict(id=21, name='implicit_clipping_bounding_box_max', type=6, value=zero),
                  dict(id=18, name='implicit_clipping_bounding_box_resize_trigger', type=1, value=0), dict(id=102, name='implicit_clipping_view_is_visible', type=1, value=1)]
    return dict(attributes=attrs, id=i, modelId=-1, opacity=1, transparent=False, visible=bool(visible), wireframe=False)


def _quat(d, up=(0.0, 0.0, 1.0)):
    """Orientation (x, y, z, w) of a camera looking along d: columns right, up, -d."""
    n = math.sqrt(sum(v * v for v in d))
    d = [v / n for v in d]
    r = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]]
    n = math.sqrt(sum(v * v for v in r))
    r = [v / n for v in r]
    u = [r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0]]
    m = [[r[0], u[0], -d[0]], [r[1], u[1], -d[1]], [r[2], u[2], -d[2]]]
    t = m[0][0] + m[1][1] + m[2][2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, 0.25 * s]
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        q = [0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s, (m[2][1] - m[1][2]) / s]
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        q = [(m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s, (m[0][2] - m[2][0]) / s]
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        q = [(m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s, (m[1][0] - m[0][1]) / s]
    return d, q


def viewport(template, eye, target, half_height):
    """The template viewport record with its camera moved to look from eye at target."""
    data = json.loads(json.dumps(template))
    d = [t - e for e, t in zip(eye, target)]
    dist = math.sqrt(sum(v * v for v in d))
    d, q = _quat(d)
    xyz = lambda a: dict(zip('xyz', [float(v) for v in a]))
    for pos in data['currentPositions']:
        for key in ('orthoState', 'perspState'):
            st = pos[key]
            st.update(eyePoint=xyz(eye), viewDirection=xyz(d), worldUp=xyz([0, 0, 1]), orientation=dict(x=q[0], y=q[1], z=q[2], w=q[3]),
                      pivotDistance=dist, nearClip=0.01, farClip=dist * 6)
        o = pos['orthoState']
        aspect = o['right'] / o['top'] if o.get('top') else 1.0
        o.update(left=-half_height * aspect, right=half_height * aspect, bottom=-half_height, top=half_height)
    return data


def selftest(path):
    """Rebuild the `open` rows and the camera orientation of a notebook saved by nTop and compare."""
    chunks = load(path)
    C = {c.name: c for c in chunks}
    have = json.loads(C['open'].payload)
    mine = open_rows(code_of(chunks), collapsed=False)
    a, b = [r['relativePath'] for r in have], [r['relativePath'] for r in mine]
    print(path, 'rows', len(a), len(b), 'paths equal', a == b)
    if a != b:
        k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
        print(' first difference at', k, a[max(0, k - 3):k + 4], b[max(0, k - 3):k + 4])
    st = json.loads(C['viewport'].payload)['currentPositions'][0]['orthoState']
    d, q = _quat([st['viewDirection'][k] for k in 'xyz'])
    err = max(abs(abs(q[i]) - abs(st['orientation'][k])) for i, k in enumerate('xyzw'))
    sign = {(q[i] > 0) == (st['orientation'][k] > 0) for i, k in enumerate('xyzw')}
    print(' camera orientation error', round(err, 6), 'consistent sign', len(sign) == 1)
    return a == b and err < 1e-4 and len(sign) == 1


if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        ok = all([selftest(p) for p in sys.argv[2:]])
        sys.exit(0 if ok else 1)
    if sys.argv[1] == '--template':
        # ntop_display.py --template saved.ntop out.json : keep the small display records of a notebook saved by nTop
        C = {c.name: c for c in load(sys.argv[2])}
        Path(sys.argv[3]).write_text(json.dumps({n: json.loads(C[n].payload) for n in ('customColors', 'res', 'tools', 'viewport')}, indent=1))
        print('wrote', sys.argv[3])
