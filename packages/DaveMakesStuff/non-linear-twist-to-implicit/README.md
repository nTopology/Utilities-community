# Non Linear Twist to Implicit

Add a field-driven variable twist to an implicit around the z axis

[Watch the Tutorial Video](https://youtu.be/JQYW8jneh4E)

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/non-linear-twist-to-implicit/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input implicit body to apply twist to.
3. Input scalar field (in degrees) to drive twist along z axis
4. Tune parameters. Export via the standard nTop exporters.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| Implicit | Implicit Body | Required. |
| Rotation Field | Scalar Field (in degrees) | Required. |
| Output | Implicit Body | Main result. |

## License

MIT.
