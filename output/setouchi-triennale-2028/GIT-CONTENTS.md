# Versioned review materials

The repository contains the visual index, all 76 world/Japan previews, nine
catalogs, proposal documents, contact sheets, coral prototypes, source notes,
validation receipts and build scripts. Open `index.html` locally to review the
previews and supporting documents.

The full print delivery is generated locally: `plates/` contains the SVG/PDF
masters and 300 dpi PNGs, and `setouchi-tri-explore-v1.pdf` is the 111-page
aggregate. These approximately 2.76 GiB of delivery files are not all Git
contents. Print-download links need those local exports. Compiled executables,
downloaded source datasets, native participant caches, logs and superseded
renders also remain local. The repository's existing generated-asset convention
is retained; no Git LFS migration or separate artifact publication is included.

`manifest.json` and `SHA256SUMS` describe the complete local delivery, not just
the files in a clone. Run the checksum verification against that complete
delivery. The build scripts and source receipts document its pinned local
inputs; see `README.md` for the production sequence and sibling dependencies.

The development document's statements about untracked outputs and no commit
describe the initial unattended production pass. The subsequent user request
to commit and push covers this versioned review package and the associated
repository source, documentation and tests. The full-resolution aggregate and
plate masters remain available in the original workspace.
