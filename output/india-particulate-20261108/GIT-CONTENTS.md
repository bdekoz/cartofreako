# India particulate review package: 8 November 2026

This versioned package accompanies the
[India enrichment analysis](../../docs/development/20261108_particulate_data_enrichement_explore_v2_india.md).
It contains the station inventory, daily observations and paired measurements,
episode and coverage tables, descriptive fire/weather/model context, the separate
2022 LongPMInd grid, atlas profiles and GeoJSON, review figures, acquisition
receipts and validation results. The small, time-sensitive public FIRMS snapshot
and selected source metadata are included. Ingestion, preparation, plotting and
validation code lives in the repository's `scripts/` directory.

Eligible 2026 PM2.5 observations reach 4 November and PM10 reaches 2 November;
8 November is the requested cutoff and acquisition date. The current selected
network and national 2024 backfill have different periods and coverage. Model
grids and fire detections are separate from reference-monitor observations.
See the analysis for units, thresholds, attribution, source-quality findings and
access limitations. Credit XKDR, CPCB and US Department of State/AirNow for the
2024 compilation; LongPMInd v2 is DOI `10.5281/zenodo.14557027`, CC BY 4.0.

Following the existing Setouchi review-package convention, downloaded bulk
OpenAQ/XKDR/LongPMInd caches, redundant Japanese/Chinese inputs, hourly exports,
the initial full atlas build, full SVG previews and logs remain in the local
workspace. The local files have not been removed. This commit does not publish
the full archive or change the public gallery.

`enrichment/validation.json`, acquisition manifests and preparation receipts
describe the complete local production run, including files absent from a clone.
Full reprocessing and the complete validation command require those local inputs
or their reacquisition; mutable upstream services may return later revisions.
The original IITM HTML snapshot also remains local; its extracted numerical
series and discrepancy flags are versioned in `enrichment/context/`.

`GIT-SHA256SUMS` covers only the versioned files in this package, excluding itself.
Verify it from this directory:

```bash
sha256sum -c GIT-SHA256SUMS
```

The repository's ten focused regression tests can be run independently of the
bulk downloaded datasets:

```bash
python3 tests/test_india_particulate_enrichment.py
```

Run that test command from the repository root with the analysis dependencies
and H3 library installed. The analysis document records the full production
commands and the limitations that remain.
