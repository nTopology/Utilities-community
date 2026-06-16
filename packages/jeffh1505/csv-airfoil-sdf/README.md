# CSV Airfoil SDF

Import airfoil coordinate data from a CSV file and generate a smooth signed-distance-field (SDF) implicit body ready for use in nTop workflows.

See the included `csv-airfoil-support-article.pdf` for a detailed walkthrough.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities-community.git
```

The package lives at `packages/jeffh1505/csv-airfoil-sdf/`.

## Usage

1. Open `csv-airfoil-sdf.ntop` in nTop 4.12+.
2. Import your airfoil CSV coordinates as a list of points and connect to the `Input Airfoil CSV` input.
3. Set the `Root Point` to position the profile in your workspace.
4. Use the output `Airfoil Profile` directly in your nTop design workflow.

Refer to `CSV Airfoil Support Article.pdf` for full details and examples.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| Root Point | Point | Origin point for the airfoil profile |
| Input Airfoil CSV | List of Points | Airfoil coordinate points imported from CSV |
| **Airfoil Profile** | Profile | Main result — airfoil profile ready for use in nTop workflows |

## License

MIT.
