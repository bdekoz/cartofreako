# Versioned Setouchi application materials

This directory versions the ten-page A4 proposal, complete two-page A4 CV,
application HTML, map previews, installation drawing, WordPress draft and
JSON source/validation records. Open `proposal.html` locally to read the
application with its figures. Open `wordpress/preview.html` to review the
content prepared for WordPress page 3175.

The full-size Japan and World atlas PDFs are local generated files, following
the existing Setouchi delivery convention. The source originals under
`sources/input/`, PDF assembly intermediates and QA page renders also remain
local. The complete local `index.html` includes atlas-download links which
require those generated PDFs. The versioned proposal and A4 CV can be opened
directly from a clone.

Regenerate the complete package from the repository root:

```sh
make setouchi-v3 SETOUCHI_V3_DATE=2026-11-01
```

This requires the completed local ST2 delivery and the supplied source PDFs
under `assets.static/setouchi-triennale/`. The proposal development document
lists dependencies, output locations, source dates and the validation scope.
No new data are fetched, and no WordPress write or application submission is
performed by the build.

`manifest.json` and `SHA256SUMS` describe the complete local delivery, including
files excluded from Git. Check the full inventory after regeneration; a clone
alone does not contain every file named there. The generated files retain
their exact bytes through `.gitattributes`.

The directory is excluded from the Jekyll documentation site. WordPress
publication uses the media-upload instructions and URL mapping in
`wordpress/README.txt`; its canonical permalink is
<https://benjamin.dekosnik.com/futures/setouchi-2028/>.
