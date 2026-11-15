"""Make the converted notebook readable: sections with descriptions, collapsed blocks, body colours, camera.

  python tools/organize_fury.py [stem]

Reads native/notebook/converted/<stem>.ntop (the raw `ntopcl convert` output) and <stem>_layout.json (which
section every variable belongs to, written with the recipe) and writes native/notebook/<stem>.ntop.
Only display records and the order of the variables change; the computation is compared before and after.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import ntop_display as D

FOLDER = ROOT / 'native' / 'notebook'
RAW = FOLDER / 'converted'

DESCRIPTION = {
    '00 Coordinates': 'Start here. X, Y and Z are fields that give the position of every point in metres: X runs aft from the nose tip, '
                      'Y to the right wing, Z up from the fuselage reference line. Every shape below is a formula of these three fields. '
                      'A shape is a field that is negative inside the part and positive outside.',
    '01 Inputs | Fuselage': 'Change these numbers to resize the fuselage. Length stretches every station; the two scales stretch the cross sections. '
                            'Scale 1 is the reference aircraft.',
    '02 Inputs | Wing': 'Wing planform and thickness. The planform is a straight-tapered trapezoid: apex station, leading-edge sweep, root and tip chord, span.',
    '03 Inputs | Tail': 'Tail type switches between the conventional tail (0: one fin and two horizontal tails) and a V-tail (1: two canted panels). '
                        'Both tail sets have their own planform inputs; only the selected one is built into the bodies.',
    '04 Inputs | Inlet, duct and engine': 'Where the inlet lip sits and how its edges are swept, the diverter slot and the splitter plate above the inlet, '
                                          'the lip wall thickness and the nozzle exit size.',
    '05 Inputs | Structure and fuel': 'Thickness of the skin and of the webs, where the wing spars sit on the chord, and the gap kept around the fuel. '
                                      'The structure is a representative layout, not a stressed design.',
    '06 Derived dimensions': 'Nothing to edit here. Every input is converted once to metres and radians (and to sines, cosines and tangents); '
                             'the geometry below only uses these converted values, so you can read each dimension as a number.',
    '07 Reference coordinates': 'The fuselage is drawn at the size of the reference aircraft. These three fields are X, |Y| and Z divided by the '
                                'length, width and height scales, so one set of guide curves serves every size. |Y| makes the left side a mirror of the right.',
    '10 Fuselage guide curves': 'Each guide is a smooth curve of one fuselage dimension against station (metres along the reference aircraft): half width, '
                                'crown height, chine height, underside height, belly height, duct sizes and a few shape weights. '
                                'Edit the control points of a guide to reshape the fuselage. They were set from side, plan and front photographs.',
    '11 Fuselage lofts': 'A loft is one Spline DF cross section whose control points ride on the guides. Upper loft: crown to chine. '
                         'Underside loft: chine to keel, continued aft as the duct roof. Lower loft: the inlet cowl and belly. '
                         'Section 13 puts them together.',
    '12 Inlet, duct and nozzle': 'The inlet is the lower fuselage cut by the lip surface: a chevron lower lip and side walls that lean forward. The duct air is the space below the roof loft, above the '
                                 'floor loft and one lip thickness inside the cowl; it runs to the round engine face. The splitter plate is the upper lip of the inlet: it sits one diverter '
                                 'height below the forebody underside, and the slot between them is closed behind the lip by a swept wedge, so the forebody boundary layer '
                                 'leaves to the sides. The jet pipe is a cone to the nozzle exit.',
    '13 Fuselage': 'The fuselage: under the upper loft and above the lower side, cut at the nose and at the nozzle, with the duct and the jet pipe hollowed out. '
                   'The lower side is the forebody underside in front and the inlet cowl behind the lip surface.',
    '14 Wing': 'One lifting panel, mirrored. The span coordinate runs along the panel, the normal coordinate is the distance from its chord plane. '
               'Leading-edge station, chord and thickness are straight lines of the span coordinate, and one airfoil Spline DF gives the section.',
    '15 Tail': 'The fin, the horizontal tails and the V-tail are built exactly like the wing. The tail type input adds a large offset to the tail set '
               'that is not selected, which moves it out of the model.',
    '16 Exterior': 'Fuselage, wing and tail joined with smooth fillets: this is the outer mold line.',
    '20 Structure': 'The skin is the outer mold line shelled inward. Ring frames follow the inner skin and go round the inlet duct; bulkheads close the '
                    'fuel cells and carry the engine. Spars sit at chord fractions, ribs at span fractions.',
    '30 Engine and systems': 'An engine envelope of FJ44-4 size on the duct axis, the jet pipe, the air data boom and the usable forebody volume. Representative.',
    '31 Fuel': 'Fuel fills the fuselage between the tank bulkheads and the wing box between the front and rear spars, a clearance away from skin, '
               'duct and structure. The main gear bay is kept free.',
    '40 Bodies': 'The finished bodies. Show or hide them here. The skin, panel lines, paint and markings are shown when the notebook opens; hide them to see the structure, engine and fuel.',
    '99 Checks': 'The outer mold line evaluated at a few fixed points. The same numbers are computed outside nTop (native/notebook/<stem>_checks.json); '
                 'they agree when the notebook computes the intended shape.',
    '21 Panel lines': 'Panel lines are a pattern: a field that is negative on the lines, drawn in a flat view and pushed straight through the aircraft. '
                      'Fuselage breaks sit at the frames, wing and tail lines on the spars and ribs, and the doors are rectangle outlines. '
                      'The pattern is cut into the skin as shallow grooves, and a dark body fills the grooves so they show.',
    '22 Paint and markings': 'Paint works like the panel lines: a flat pattern meets a thin layer on the outer mold line. The dark band is drawn in the side view, '
                             'lettering is built from straight strokes, the national insignia from a disc, a star and two bars. Side lettering uses the side of '
                             'the aircraft (+1 right, -1 left) so it reads correctly on both sides.',
}
SHOWN = {'Skin', 'Air data boom', 'Panel lines', 'Paint, dark grey', 'Markings, light', 'Markings, dark', 'Formation lights'}


def organize(stem='fury'):
    target, raw = FOLDER / f'{stem}.ntop', RAW / f'{stem}.ntop'
    layout = json.loads((FOLDER / f'{stem}_layout.json').read_text())
    template = json.loads((FOLDER / 'display_template.json').read_text())
    chunks = D.load(raw)
    assert [c.name for c in chunks] == ['turhe', 'main', 'cache'], [c.name for c in chunks]
    fn = D.fn_chunk(chunks)
    code = json.loads(fn.payload)
    before = json.loads(fn.payload)
    byid = {b['id']: b for b in code['code']}
    top = D.top_level(code)
    final = layout['final_bodies']
    sections = layout['sections']
    missing = [n for n in layout['variables'] if n not in {name for _, name, _ in top}]
    assert not missing, missing[:10]
    key = {i: layout['variables'].get(name, sections[-1]) for i, name, _ in top}
    base = [i for s in sections for i, _, _ in top if key[i] == s]
    # top-down order: a variable used by an earlier one is moved up, just ahead of its first user, into that section
    rank = {s: n for n, s in enumerate(sections)}
    refs = D.references(code)
    order, done = [], set()

    def visit(i, sec):
        if i in done:
            return
        done.add(i)
        if rank[sec] < rank[key[i]]:
            key[i] = sec
        for j in refs.get(i, ()):
            if j in key:
                visit(j, key[i])
        order.append(i)
    sys.setrecursionlimit(10000)
    for i in base:
        visit(i, key[i])
    assert sorted(order) == sorted(i for i, _, _ in top)
    inputs = {inp['instanceId']: inp for inp in byid[100]['inputs']}
    byid[100]['inputs'] = [inputs[i] for i in order]
    pos = {i: n for n, i in enumerate(order)}
    forward = sorted({byid[i]['name'] for i, r in D.references(code).items() for j in r if pos[j] > pos[i]})
    used = [s for s in sections if any(key[i] == s for i in order)]
    counts = {s: sum(key[i] == s for i in order) for s in used}
    poles, n = [0], 0
    for s in used:
        n += counts[s]
        poles.append(n)
    fn.payload = json.dumps(code, separators=(',', ':')).encode()
    D.set_json(chunks, 'sections', dict(decorations=[dict(collapse=True, description=DESCRIPTION.get(s, '').replace('<stem>', stem), name=s) for s in used], poles=poles))
    rows = D.open_rows(code, collapsed=True)
    D.set_json(chunks, 'open', rows)
    D.set_json(chunks, 'view', [D.view_row(i, byid[i]['type'] == 'implicit', final.get(byid[i]['name'], (0.65, 0.66, 0.73, 1.0)),
                                           byid[i]['name'] in SHOWN) for i in order])
    for name in ('customColors', 'res', 'tools'):
        D.set_json(chunks, name, template[name])
    D.set_json(chunks, 'viewport', D.viewport(template['viewport'], eye=(-8.5, -9.5, 6.0), target=(4.6, 0.0, 0.2), half_height=5.0))
    after = json.loads(fn.payload)
    for data in (before, after):
        root = next(b for b in data['code'] if b['id'] == 100)
        root['inputs'] = sorted(root['inputs'], key=lambda x: x['instanceId'])
    assert before == after, 'display pass changed the computation'
    data = D.dump(chunks)
    out = target
    try:
        target.write_bytes(data)
    except PermissionError:
        out = FOLDER / f'{stem}_organized.ntop'           # the notebook is open in nTop
        out.write_bytes(data)
    check = D.load(out)
    assert D.dump(check) == data and [c.name for c in check] == D.ORDER
    report = dict(notebook=out.name, variables=len(order), sections=counts, final_bodies=len(final), bodies_shown=sorted(SHOWN & set(final)),
                  variables_used_before_they_are_defined=forward, computation_unchanged=True,
                  source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), output_sha256=hashlib.sha256(data).hexdigest())
    (FOLDER / f'{stem}_presentation.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    return report


if __name__ == '__main__':
    organize(sys.argv[1] if len(sys.argv) > 1 else 'fury')
