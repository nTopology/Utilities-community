# Replace File Extension

This custom block replaces the file extension of a file path with an option to add a suffix before the extension.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/replace-file-extension/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Path` | file_path | Original path |
| `New extension` | Text | New file extension |
| `Suffix` | Text | Optional suffix to add to the path before the new extension. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `New Path` | file_path | Adds the new extension to the file name |

## License

MIT.
