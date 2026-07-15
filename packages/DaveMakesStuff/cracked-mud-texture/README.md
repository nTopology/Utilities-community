# Cracked Mud Texture

Create a complex "cracked mud" texture using multiple cellular noise functions.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/cracked-mud-texture/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input body to texture
3. Modify parameters to achieve desired crack pattern
4. Use a "Surface Roughness" block to add final texture as needed

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Body` | Implicit Body | Body to texture |
| `1 Crack Dist Function` | Bool | Distance function for large primary cracks |
| `1 Crack Width` | Scalar Value | Width of large primary cracks |
| `1 Crack Depth` | Scalar Value | Depth of large primary cracks |
| `1 Crack Frequency` | Scalar Value | Frequency of large primary cracks |
| `2 Crack Dist Function` | Bool | Distance function for small secondary cracks |
| `2 Crack Start Width` | Scalar Value | Width at start of small secondary cracks. Set to zero for no secondary cracks |
| `2 Crack Start Depth` | Scalar Value | Depth at start of small secondary cracks. Set to zero for no secondary cracks |
| `2 Crack Variety` | Integer Value | Number of different secondary crack patterns to use when filling in cells between primary cracks. Higher numbers create more diverse crack patterns |
| `2 Crack Freq Min` | Scalar Value | Minimum frequency to use when generating the range of small secondary crack patterns |
| `2 Crack Freq Max` | Scalar Value | Maximum frequency to use when generating the range of small secondary crack patterns |
| `2 Crack Reach` | Scalar Value | Distance that secondary cracks reach in to the cells formed by the primary cracks. |
| `1 Crack Width` | Scalar Value | Width of large primary cracks. |
| `Random Seed` | Integer Value |Random Seed for generating crack pattern |
| `Textured Body Output` | Implicit Body | Main result |


## License

MIT.
