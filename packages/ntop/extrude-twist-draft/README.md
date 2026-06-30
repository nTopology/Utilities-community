# Extrude Twist Draft

This custom block takes a profile and will extrude with a draft angle and a twist rate.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extrude-twist-draft/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Profile` | new_profile | The profile to be extruded and twisted |
| `Distance` | Scalar | The distance to extrude |
| `Twist Rate` | Scalar | The rate of twist affecting the body |
| `Draft Angle` | Scalar | Please choose the No draft Option if you have a draft angle of 0, otherwise there will be a 1 deg draft angle applied to your part. |
| `Choice` | Choice | Choice of how the draft is applied |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Body` | Implicit Body | Applies Twist to the extruded profile |

## License

MIT.
