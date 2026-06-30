# Filter Beams by Direction

Filter lattice beams by direction using a scalar field. Select whether to filter for beams that are either parallel or perpendicular to the field gradient. The "Extent" input determines how much the selected beams adhere to the "parallel" or "perpendicular" criteria. An "Extent" value of 1 return beams that meet the criteria exactly, while a value of 0 returns all beams. A warning is given if no beams meet the criteria.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/filter-beams-by-direction/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input lattice and apply selection criteria

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Lattice` | Lattice| Lattice to evaluate |
| `Direction Field` | Scalar Field | The gradient of this field is used to filter beams |
| `Filter for` | Choice | Select to filter beams parallel or perpendicular to field gradient |
| `Extent` | Scalar Value | Scalar value between 0 and 1 to determine how strictly selected beams adhere to "Filter for" criteria |
| `Filtered Lattice` | Lattice | Main Result |

## License

MIT.
