# Conformal Vector Field

Create a vector field that is conformal to the surface of an input body with option to align with plane or direction

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/conformal-vector-field/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input the body and reference plane to use when generating conformal vector field
3. Select whether to align vector field with the normal or plane of above Reference Plane input.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Body` | Implicit Body | Body to use to create conformal field |
| `Reference Plane` | Plane | Reference geometry for aligning vector field |
| `Align with` | Choice | Select whether to align vector field with the normal or plane of above Reference Plane input. |
| `Output Vector Field` | Vector Field | Main result |


## License

MIT.
