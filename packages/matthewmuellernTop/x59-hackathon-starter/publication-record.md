# Publication record

Package: `matthewmuellernTop/x59-hackathon-starter` 1.1.0, prepared 2026-10-08.
Previous version: 1.0.0, prepared 2026-10-07.

## Changes in 1.1.0

- Main wing replaced with the Twisted 2 Panel Wing custom block, with root, panel-break
  and tip twist variables (baseline 0, -2.412, -3 deg).
- Aero Command passes root/break/tip twist and points sampled along the Top, Side and
  Bottom fuselage rails (Aero Fuselage Points, default 41); `x59_aero.py` builds the
  fuselage from them.
- New Area Ruling section: section areas of `X59 OML` at evenly spaced X stations,
  collected in Area Ruling Table.
- Reference X-59 mesh added to the Verification section (redistribution confirmed by the
  author).

## Source

- Source notebook (saved 2026-10-08 10:50): SHA-256 `b7b841fbb0d3883af78985cd5beca695e428b78c82c1ca9e1098b31bda23ec1c`

## Published files

| File | Bytes | SHA-256 |
|---|---|---|
| `LICENSE` | 1075 | `6c0df087d26fb6ac0c06b3dc7b6488d7fa6f49bd87bcfcd1bcd00ead84adc4eb` |
| `README.md` | 8294 | `62a4e4462fa4211a52de2cdf85e46d49eef0aef6da4437ccd70f6447c82f8fe4` |
| `aero-output-example.png` | 120699 | `885c203282e5d27337c7a1db4c194b0c84dd4cfb2de7987f5bbc463e1c8f5441` |
| `cover.png` | 117559 | `fd0a3d4585556d0bc06448fe1d32cecf2263c0e591eece2cf2b6cccba11b3767` |
| `manifest.json` | 798 | `0cc86cc33a9dfd48c3336333dbf054b144d88d105df919d27aa9603fb1b7cfdf` |
| `requirements.txt` | 17 | `edc84a836b67546af019cc82546366ab0ea10c84f76c057e5a72cb36e368416e` |
| `x59-hackathon-starter.ntop` | 14546996 | `b7b841fbb0d3883af78985cd5beca695e428b78c82c1ca9e1098b31bda23ec1c` |
| `x59_aero.py` | 14167 | `4135ae2e272a2f7023a0963532299da696cf85bb344ebc011aba878eb747cf72` |
| `x59-hackathon-starter.zip` | 5635199 | `bab140e3eb5c4c4bc1d6da64015b7ab80d2f97eed18f74859624bc80ecc6f98a` |

## Checks

- Byte scan of the published notebook: no user names, home-directory paths, email
  addresses or links to external files. The reference mesh is embedded.
- `Aero Script Folder` is `C:/X59_Aero`.
- Every notebook block built (e_OK) in nTop build 43139 before saving, including the
  Area Ruling table at 101 stations.
- `x59_aero.py` run on the exact command line stored in the saved notebook: cruise L/D
  7.16, best L/D 7.21, neutral point 20,898 mm, static margin +30.0% MAC at Mach 1.41,
  14,660 kg, CG 18,281 mm. `aero-output-example.png` is the plot from that run.
- Not done: reopening this copy in a public nTop 6.2 release.
