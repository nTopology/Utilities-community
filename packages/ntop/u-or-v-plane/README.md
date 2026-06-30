# U or V Plane

This custom block will place a plane that is centered at the UV Origin with a normal pointing in the U or V direction.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/u-or-v-plane/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Face` | brep_face | The Face to reference for the UV origin |
| `U or V Plane` | Choice | The direction you want the plane normal to face |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Chosen Plane` | plane | The choice of which plane direction to use |

## License

MIT.
