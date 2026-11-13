# Check a package before upload

Read this for the bundle path: notebooks with outside files, reports, images, or several notebooks. A single small notebook needs only the first two sections. Scale the checks to the package.

## Confirm what is being published

- Know which file is the final version. Do not publish a copy named `latest` or `final2` without confirming it is the one the user means.
- Separate the main notebook from alternate versions, part notebooks, and unfinished trials. Include only what the user wants shared, and name alternates clearly.
- Work on a copy. Do not change the user's original files.
- Confirm the license for everything included, including third-party data, CAD, and images. Public availability is not a license. Keep any credits or source links the original license requires.

## Keep private material out

Everything in the package is public. Check files, images, and reports for:

- customer or employer data, confidential geometry, credentials, and tokens;
- personal file paths (`C:\Users\<name>\...`), account names, and unrelated applications in screenshots;
- generated caches, application binaries, and logs that were not asked for.

When unsure, leave the item out and tell the user.

## Notebooks (`.ntop`)

- **Dependencies:** list every file the notebook reads (airfoils, CAD, tables, textures, other notebooks) and include the ones the user is allowed to share. Embedded custom blocks travel inside the notebook, but imported files do not.
- **Paths:** find machine-specific paths and classify each as an input, an output, or text. For inputs, include the file in the package and tell the user to point the notebook at it after download; do not silently rewrite paths. For outputs, say where the user can set a working folder.
- **Do not edit the notebook binary by hand.** Plain text search cannot clear nested or compressed data, and a broken edit can make the file unopenable. If a path or private value is inside the notebook, ask the user to fix it in nTop and re-save.
- **Say what was tested.** State the nTop version the notebook was built and opened in. If the published copy was not reopened, say so in the README.
- **Embedded blocks:** if the package has part notebooks and an assembly that embeds them, explain how to refresh the assembly after editing a part.

## Reports and images

- Keep the HTML report and its images together, and make links point to the delivered filenames. Do not leave broken links.
- Keep limits visible: assumptions, units, and what the study does and does not show. Do not present an exploratory result as a qualified one.
- Look for private content inside the report, not only the visible page: image metadata, inline image data, and embedded scripts can hold copies of an image that was removed from view.
- Remove remote font and script dependencies if the report should work offline.
- Open the report once at desktop and phone widths and check that images and links work.

## Final check

- The manifest `id` and `author` match the folder names, and `packageFile` and `coverImage` exist in the folder. The validator does not check that these files exist.
- Look at the staged files with `git diff --cached --stat` and confirm nothing unexpected is included, such as hidden files, `.gitattributes` changes you did not intend, or files from outside the package folder.
- A passing validator only checks the manifest. It does not check the notebook or its contents.
