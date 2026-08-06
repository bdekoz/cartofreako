# Transitional Stage 6a resources profile

> This v1 profile is scheduled for replacement by the
> [Stage 6b resources design](../../docs/resources-enrichment-plan.md). Stage
> 6b does not reuse these values and will remove the old generated product;
> only the historical method decision remains in
> [`generation-methods.md`](../../docs/generation-methods.md).

`resources-profile.json` is the complete offline input to the
`generate-resources` pass. It contains two deliberately separate collections:

- all 40 commodity headings, world totals, and asterisk-marked leading
  producer shares from the 1960 production matrix in R. Buckminster Fuller and
  John McHale's 1963 *Inventory of World Resources, Human Trends, and Needs*;
- four source- and year-labelled modern comparison indicators from FAO and
  IRENA.

The historical collection is a bounded factual transcription, not the full
126-country-by-40-commodity matrix. Thirty-nine commodities have a reported
leader. Thorium is the one source column printed `N.A.`; the profile preserves
that as null and the generator never turns it into zero. Source unit
abbreviations are retained without conversion.

`SHA256SUMS` pins the complete profile used by `make check`, independently of
the historical source-PDF digest embedded inside the profile.

Normal generation is offline and does not need the historical scan:

```sh
make fetch-natural-earth-10m
make generate-resources-cahill-keyes
```

Use `make generate-resources` for all six deterministic `.svg.gz` archives or
`make generate-resources-artifacts` for compressed SVG, PDF, and PNG output.
Plain SVGs are ignored Inkscape intermediates. Inspect one with
`gzip -cd assets.generated/svg/resources-ck-44-22.svg.gz > /tmp/resources-ck.svg`.
Override the profile with `RESOURCES_PROFILE=/absolute/path/profile.json`.

Decompress every SVG archive beneath `assets.generated` in place, retaining
the compressed files:

```sh
find assets.generated -type f -name '*.svg.gz' \
  -exec gzip --decompress --keep -- {} +
```

## Source and redistribution boundary

The source is the Buckminster Fuller Institute's
[Phase I, Document 1 catalog page](https://www.bfi.org/resource/phase-i-document-1-inventory-of-world-resources-human-trends-and-needs-1963/).
The transcribed table is on one-based PDF pages 62–73. The source PDF used for
the audit had SHA-256:

```text
11f0a4f7617a34b58bf620bba62ddbfe01a6389dffc348e95142b86db964f816
```

The scan is not redistributed and there is no automated fetch target. BFI's
[legal terms](https://www.bfi.org/about-bfi/legal/) reserve rights in site
content and limit site access, while its
[licensing page](https://www.bfi.org/about-bfi/contact/licensing/) directs
permission requests for Fuller publications to the Fuller Estate. Maintainers
must obtain an authorized source copy and review the current terms before
re-auditing it. The checked profile records factual values and provenance; it
does not grant rights to the underlying publication or its page images.

## Maintainer transcription aid

[`scripts/transcribe-fuller-minerals.py`](../../scripts/transcribe-fuller-minerals.py)
is an audit aid for an authorized local copy. It requires Poppler,
Python OpenCV, and Tesseract, none of which are needed for normal generation.
Render the source pages at exactly 150 DPI:

```sh
mkdir -p /tmp/cartofreako-fuller-pages
pdftoppm -f 62 -l 73 -r 150 -png authorized-inventory.pdf \
  /tmp/cartofreako-fuller-pages/cartofreako-minerals
python3 -B scripts/transcribe-fuller-minerals.py \
  /tmp/cartofreako-fuller-pages /tmp/full-resource-matrix-audit.json
```

Review `audit.unparsed_nonblank_cells`, every inferred leader mark, every
column sum, and the page image itself. OCR output is never an authoritative
replacement for `resources-profile.json`; promotion requires a human
side-by-side audit and an updated source digest and page citation.

The [transitional implementation notes](../../docs/resources-implementation-notes.md)
record the checked code until replacement. The durable historical conclusion
will remain in [generation methods](../../docs/generation-methods.md), while
the [Stage 6b plan](../../docs/resources-enrichment-plan.md) defines the sole
future resources product.
