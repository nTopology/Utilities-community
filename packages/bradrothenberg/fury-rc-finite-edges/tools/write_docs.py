"""Write the generated parts of the documentation from the current model and results.

  python tools/write_docs.py

  reference/SOURCES.md     every reference photograph with page, credit and what it was used for
  docs/INPUTS.md           the input table of the notebook
  docs/MATCH.md            photograph overlays and the overlap numbers (docs/img/match_*.jpg)
  docs/ANALYSIS.md         the analysis results gathered in one place
"""
import json, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import design

DOCS, IMG, RES = ROOT / 'docs', ROOT / 'docs' / 'img', ROOT / 'analysis' / 'results'
IMG.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ sources
m = json.loads((ROOT / 'reference' / 'public' / 'manifest.json').read_text(encoding='utf-8'))
lines = ['# Reference photographs', '',
         'Public photographs and renderings collected for this model, in `reference/public/`. They are kept for reference only; the',
         'rights stay with the owners named in the credit column. US Air Force photographs are public domain.', '',
         '| File | View | Used for | Credit | Page |', '|---|---|---|---|---|']
for i in m:
    lines.append(f"| `{i['file']}` | {i['view']} | {i['good_for']} | {i['credit']} | {i['page']} |")
lines += ['', 'Other sources', '',
          '- Baseline notebook: "Fury RC finite edges" from the nTop community site, in `source/fury-rc-finite-edges/` (MIT licence, see the folder).',
          '- AIM-120 length 12 ft and diameter 7 in: US Air Force fact sheet values, used as the scale in photograph 07.',
          '- Engine envelope and dry weight: Williams International figures for the civil FJ44-4A.',
          '- Measurements taken from the photographs: `PROPORTIONS.md`.']
(ROOT / 'reference' / 'SOURCES.md').write_text('\n'.join(lines), encoding='utf-8')

# ------------------------------------------------------------------ inputs
lines = ['# Inputs of the notebook', '', 'Every input is a variable in sections 01 to 05 of `native/notebook/fury.ntop`. Values are the Fury match.', '']
section = None
for name, value, sec, text in design.table():
    if sec != section:
        section = sec
        lines += ['', f'## {sec}', '', '| Input | Value | What it does |', '|---|---:|---|']
    lines.append(f'| {name} | {value:g} | {text} |')
(DOCS / 'INPUTS.md').write_text('\n'.join(lines), encoding='utf-8')

# ------------------------------------------------------------------ match
mj = ROOT / '.local' / 'match_final' / 'match.json'
if mj.exists():
    res = json.loads(mj.read_text())
    lines = ['# How well the model matches the photographs', '',
             'Each photograph is mapped into the model frame from a few picked points (nose tip, nozzle centre, wing tips), and the model',
             'silhouette is drawn on it. Orange: outline of the model. Cyan: outline of the aircraft found in the photograph (against the sky).',
             'Overlap is intersection over union of the two silhouettes; the outline distance is given in percent of the fuselage length',
             '(1 % of length = 4 in). Landing gear, missile, pylon and nose boom are in the photographs and not in the model outline, so they',
             'are left out of the score where a score window is set (`reference/match_views.json`).', '',
             '| View | Photograph | Overlap | Outline distance, median | Outline distance, 90 % of the outline within |', '|---|---|---:|---:|---:|']
    for r in res:
        d = r.get('outline_distance_percent_length', {})
        lines.append(f"| {r['view']} | `{r['file']}` | {r.get('overlap_iou', float('nan')):.3f} | {d.get('photo_to_model_median', float('nan')):.2f} % | {d.get('photo_to_model_p90', float('nan')):.2f} % |")
        src = mj.parent / f"{r['view']}.jpg"
        if src.exists():
            shutil.copy2(src, IMG / f"match_{r['view']}.jpg")
    lines += ['', '## Side view', '', '![side](img/match_side_07.jpg)', '', '## Plan view (underside)', '', '![plan](img/match_plan_01.jpg)', '',
              'The plan photograph is an oblique view, so the near fuselage side and the fin show beside the planform; that is most of the',
              'difference in the plan numbers.', '',
              '## Checked by eye, not scored', '',
              '- Front view (photographs 12 to 14): arch upper section, chine overhanging the cowl, wide shallow inlet, 1.5 deg anhedral.',
              '- Inlet (photographs 07, 18, 19): lower lip station, chevron lower lip, side walls leaning forward, the pointed splitter plate under the',
              '  forebody and the diverter slot above it. The slot height and the plate thickness are estimates.',
              '- Paint and markings (photographs 04, 05, 06, 07, 17): two greys, designation, tail code, serial, insignia. Positions from the photographs;',
              '  the lettering is a plain stroke font, panel lines are a representative layout at the frames, spars and doors.',
              '- Not modelled: landing gear (door outlines only), pylons, antennas, the dorsal sensor fairing.',
              '', 'Measured proportions and how the scale was found: `reference/PROPORTIONS.md`.']
    (DOCS / 'MATCH.md').write_text('\n'.join(lines), encoding='utf-8')

# ------------------------------------------------------------------ analysis
parts = ['# Analysis results', '',
         'All numbers are estimates made on the model, in US customary units. Scripts are in `analysis/`; the json beside each result keeps SI values.', '']
for stem in ('mass', 'duct', 'vlm', 'cfd'):
    f = RES / f'{stem}.md'
    if f.exists():
        text = f.read_text(encoding='utf-8').replace('\n# ', '\n## ')
        parts += ['#' + text if text.startswith('# ') else text, '']
        if stem == 'duct' and (RES / 'duct.png').exists():
            shutil.copy2(RES / 'duct.png', IMG / 'duct.png')
            parts += ['![duct](img/duct.png)', '']
        if stem == 'cfd':
            parts += ['Geometry revision: the flow body of these runs was made before the diverter slot and the splitter plate were added to the model. '
                      'The inlet is faired over in the flow body, so the change is local to the inlet; the runs were not repeated on the final shape.', '']
sys.path.insert(0, str(ROOT / 'tools'))
import readme_parts
compare = readme_parts.methods_compared()
if compare:
    parts += ['## The two aerodynamic estimates side by side', '', compare, '']
check = readme_parts.native_check()
if check:
    parts += ['## Notebook against the Python model', '', check[0].upper() + check[1:], '']
(DOCS / 'ANALYSIS.md').write_text('\n'.join(parts), encoding='utf-8')
readme_parts.run()
print('written')
