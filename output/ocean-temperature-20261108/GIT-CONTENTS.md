# Ocean review package — 8 November 2026

The [stage-one study](../../docs/development/20261108_anthropocene_ocean_temperature_stage_1.md)
is the interpretation and methodology record. This directory is a local
review edition, not a published default atlas or a complete raw-data archive.

Curated contents include normalized period data and metadata, coral fields,
input receipts, the paired-year and JMA comparisons, screen proofs, the
seasonal figure, export manifest, validation receipt and local review index.
The small pinned JMA sample and format readme are included for inspection.

The following large or intermediate files remain local and are ignored:

- `cache/`: the 1982–2026 NOAA yearly SST/ice files, mask and CRW originals.
- `work/`: native-center H3 membership and annual daily arrays.
- `data/monthly-*.npz`: complete twelve-month fields, reproducible from caches.
- All `maps/` and `legends/` folders: print SVG/PDF masters, including matched
  and record-day variants. SVG data layers reference `tiles/`; PDFs are
  self-contained exports.
- `tiles/`, `logs/` and source-discovery probes under `research/`, except the
  explicitly retained JMA sample/readme. The BGS compilation is not repackaged.

The review index's SVG/PDF links are available in the working directory;
another checkout must regenerate those ignored print artifacts. Preview PNGs
and normalized data are the compact inspection route. The source ledger and
`config/ocean-context-20261108.json` pin original URLs and hashes. If a provider
revises a pinned input, the fetcher rejects the replacement rather than
silently changing this edition. No source license is changed by this package.

Reproduction commands are in the stage-one study. They require the repository's
existing source atlas/assets, libnetcdf, H3, GDAL/Cairo, NumPy, SciPy for tests,
Matplotlib for the scientific figure, and Inkscape for export. Large downloads
are deliberately separate from ordinary default plate generation.
