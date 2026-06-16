# Wings with Aileron

Parametric wing block with integrated aileron geometry, ready for aerodynamic and structural workflows in nTop.

See `how-to-make-ailerons-for-a-wing-block.pdf` for a full walkthrough.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities-community.git
```

The package lives at `packages/harrykeaten-design/wings-with-aileron/`.

## Usage

1. Open `wings-with-aileron.ntop` in nTop 4.12+.
2. Set the wing parameters (span, root chord, taper ratio, quarter chord angle, dihedral).
3. Define the aileron spanwise extents and chord depth factor.
4. Set hinge radius, deflection angles, and tolerance.
5. Use the output implicit body list in your downstream design or simulation workflow.

Refer to `how-to-make-ailerons-for-a-wing-block.pdf` for detailed steps and examples.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| Root Point | Point | Origin point for the wing |
| Units | Unit Length | Unit system selection |
| Wing Span | Scalar | Total wing span |
| Quarter Chord Angle | Scalar | Sweep angle at quarter chord |
| Taper Ratio | Scalar | Tip chord / root chord |
| Root Chord Length | Scalar | Chord length at the root |
| Dihedral Angle | Scalar | Wing dihedral angle |
| Factor of Start of Aileron | Scalar | Spanwise start of aileron as fraction of half-span |
| Factor of End of Aileron | Scalar | Spanwise end of aileron as fraction of half-span |
| Chord Depth for Aileron Factor | Scalar | Chordwise depth of the aileron as fraction of chord |
| Hinge Radius Aileron | Scalar | Radius of the hinge cylinder |
| Deflection Right Aileron | Scalar | Rotation angle for right aileron |
| Deflection Left Aileron | Scalar | Rotation angle for left aileron |
| Aileron Tolerance | Scalar | Gap tolerance between aileron and wing |
| TE Offset | Scalar | Trailing edge offset distance |
| **Ailerons + Wings w Cut** | List of Implicit Bodies | Main result — mirrored wing pair with ailerons and hinge cutouts |

## License

MIT.
