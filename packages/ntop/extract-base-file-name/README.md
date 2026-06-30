# Extract Base File Name

This custom block extracts the base file name from a file path with an option to include the file extension. For example, "C/Users/NAME/Downloads/model.stl" -> "model"/"model.stl"

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extract-base-file-name/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Path` | file_path | Original path |
| `Include extension` | bool | Option to remove the file extension |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Output` |  | Output. |

## License

MIT.
