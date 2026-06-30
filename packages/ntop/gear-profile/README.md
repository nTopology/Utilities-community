# Gear Profile

This workflow creates a gear profile based on the inputs below.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/gear-profile/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Number of Teeth` | Integer | Total number of teeth on the gear. Common values: 12–20 for pinions, 20–60 for standard gears. More teeth = smoother transmission but larger diameter. |
| `Pressure Angle` | Scalar | Angle (degrees) between the tooth force direction and the tangent to the pitch circle. Standard values are **20°** (most common, ISO/AGMA default) or **14.5°** (legacy). Higher angles increase tooth strength but raise bearing loads. |
| `Module` | Scalar | Ratio of pitch diameter to number of teeth (mm/tooth). Controls overall gear size — larger module = bigger, stronger teeth. Common values: 1, 1.25, 1.5, 2, 2.5, 3, 4, 5. Two meshing gears must share the same module. |
| `Dedendum Clearance` | Scalar | Extra radial depth below the pitch circle, beyond the standard dedendum, to prevent tip-to-root contact with a mating gear. Typically **0.25 × module** (e.g. 0.5 mm for module 2). |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Gear Profile` | new_profile | Output. |

## License

MIT.
