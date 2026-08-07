# Cartofreako generated assets v12

This immutable object release mirrors the generated-asset bundle published
with source release `v20260807`. The source tag resolves to commit
`2bd3d760fef540addfcbb4f8002ef7b283d8000f`.

The release root is `cartofreako/v12/` in the Berkeley S3-compatible bucket
`adekosnik-bucket01`:

```text
cartofreako/v12/
├── tree/
│   ├── svg/
│   ├── pdf/
│   ├── png/
│   └── thumbnail/cahill-keyes/
├── package/assets.generated.v12.tar.xz
├── README.md
├── viewer.html
├── SHA256SUMS
└── release.json
```

The package remains the authoritative extracted snapshot: 673 files, including
187 full SVGs and 84 adjacent SVG-gzip copies. The browser-delivery `tree/`
contains 589 files. It replaces every full SVG with one explicit
`tree/svg/*.svg.gz` object, preserving the 84 supplied gzip files and creating
103 deterministic gzip files for the remaining SVGs. These objects are served
as `application/gzip` without `Content-Encoding`; no uncompressed or
transparent-gzip `.svg` object is published.

The Cahill–Keyes contact sheet displays the 28 supplied 480-by-240 PNG
thumbnails. Selecting one opens `viewer.html`, which fetches its same-origin
`.svg.gz` object and streams it through `DecompressionStream("gzip")` before
display. The viewer also exposes the compressed and decompressed downloads.
Keeping the viewer and SVG gzip files at the same S3 origin avoids a CORS
dependency.

All 594 objects are public-read and carry an immutable one-year cache policy.
`release.json` is the completion marker and was uploaded only after the other
objects passed checksum verification. `SHA256SUMS` covers the stored bytes of
all 592 payload objects; it excludes itself and `release.json`.

The recovery package is byte-for-byte identical to the GitHub release asset:

```text
dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a  assets.generated.v12.tar.xz
```

Project documentation and complete release notes are available at
<https://github.com/bdekoz/cartofreako/releases/tag/v20260807>.
