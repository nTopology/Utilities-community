# Filter Beams by Length in a Containment

This custom block filters lattice beams selectively by the length in a defined containment.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-beams-by-length-in-a-containment/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Lattice` | lattice_body | Lattice on which filtering is to be done by length in a containment |
| `Condition` | comparison_enum | Logical arguments used with the filter criteria, Length. |
| `Length` | Scalar | The filter criteria, beam length from the Lattice. |
| `Beam thickness` | Scalar Field | Thickness of the Lattice Beams |
| `Containment` | Implicit Body | Containment region for the filtering |
| `Choice` | Choice | Use Refined Bounding Box option only if the Final Lattice is incorrectly trimmed and has undesired rounded ends |
| `Tolerance` | Scalar | Tolerance for the Refined Bounding Box |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final` | lattice_body | Filters the lattice beams by the length in the defined containment. |

## License

MIT.
