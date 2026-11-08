# Stage 2 review package — 8 November 2026

The [completed Stage 2 record](../../docs/development/20261108_anthropocene_ocean_temperature_stage_2.md)
describes the methods, findings, validation and remaining human decisions.
The [review index](index.html) contains eight optional year identities and
32 measure/period views, with 128 separate map and legend sheets. It is a
local prototype edition; the default atlas remains 39 passes.

Curated Git contents include:

- Normalized period arrays and metadata for marine events, thermal seasons,
  coastal joint heat and the selected India heat–PM2.5 pilot.
- Three compressed marine event ledgers, the station-day ledger, canonical
  station crosswalk, coastal pairing/membership table and support diagnostics.
- Source hashes, pinned reference revision, method receipts, matched monthly
  comparisons and baseline, persistence, amplitude, distance, PM-threshold
  and date-alignment sensitivities.
- All 128 screen proofs, the export manifest, four standalone scientific
  figures in PNG/SVG/PDF with source/hash receipts, and validation results.

Large or intermediate files remain local and are ignored:

- `cache/`: the separately acquired 2026 CPC source file.
- `work/`: complete calendar thresholds, daily flags, intermediate coastal
  and station temperature arrays, and restartable chunks.
- `tiles/`: rendered data layers and their reusable cache.
- Every `maps/` and `legends/` directory: editable print SVGs and standalone
  PDF exports. SVGs refer to local tile images; PDFs are self-contained.
- Per-view `work/`, root logs, and the unmodified downloaded
  `research/marineHeatWaves.py` reference. Its exact URL, revision and hash are
  retained in `research/reference.json` and the acquisition ledger.

The index's SVG/PDF links work in the completed working directory. A fresh
checkout must regenerate those ignored print artifacts; retained preview
PNGs and normalized data provide the compact inspection route. Figure files
are included in Git and can be shared independently.

This package reuses the Stage 1 OISST daily working arrays, the older CPC
baseline/2025 cache, the November 8 India hourly archive and existing Natural
Earth/source-atlas assets. It does not duplicate those large inputs. Restore
the dependencies using their study records, then run the Stage 2 fetch,
prepare, render and check targets documented in the completed record.
Pinned-input hash changes are rejected rather than silently revising this
edition. Provider/source rights and evidence classes remain those recorded
by the source studies and legends.

Ocean and refreshed CPC observations end on **November 7, 2026**. Eligible
reference PM2.5 ends on **November 4**; the separate low-cost series ends on
**October 2**. Full 2025 and matched 2025 variants are distinct, and 2026 is
always partial. Local thermal seasons use adjacent-year context and are
labeled by their expected warm-peak year. No source-supported zero should
be confused with missing support or an unfinished event/season.
