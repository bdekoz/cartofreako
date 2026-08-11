# Stage 15 R2 — anthropocene water-debris feasibility

Status: **exploration-only feasibility complete; generator not ready**

Checked: 2026-08-10

Contract: `contracts/water-debris-evidence-v1.schema.json`
Source manifest: `fixtures/water-debris-evidence/v1/manifest.json`

## Decision

Do not implement `anthropocene-water-debris` yet. Credible source families
exist, but this pass would combine unlike evidence: shoreline counts, sampled
surface points, modeled concentration, modeled river emissions, operational
cleanup tracks, and depth profiles. The prototype did not establish one
redistributable global spatial package with dates, units, uncertainty, and
reuse rights across those classes.

The existing `anthropocene` pass remains the legacy multi-source climate,
fire, and smoke atlas. The dated temperature IDs remain
`anthropocene-temperature-2025` and `anthropocene-temperature-2026`; no rename
or migration is warranted.

## Source findings

| Source | What it can support | What it cannot establish here |
| --- | --- | --- |
| [NOAA MDMAP](https://marinedebris.noaa.gov/our-work/monitoring/marine-debris-monitoring-and-assessment-project) | Dated, protocol-based shoreline macro-debris observations and interactive export | Open-ocean concentration, river emissions, operational tracks, or depth |
| [NOAA 2024 national survey record](https://www.fisheries.noaa.gov/inport/item/73092) | CC0 candidate-site geometry and survey-design context | Debris observations or a global layer |
| [The Ocean Cleanup GPGP overview](https://theoceancleanup.com/great-pacific-garbage-patch/) | Evidence vocabulary for samples, modeled concentration, cleanup, and vertical distribution | A checked redistributable coordinate/raster package or reuse license |
| [2015–2022 North Pacific study](https://doi.org/10.1088/1748-9326/ad78ed) | Publication-level context for repeated trawl/aerial sampling and modeled change | Authorization to redistribute underlying spatial observations or graphics |
| [North Pacific depth study](https://doi.org/10.1038/s41598-020-64465-8) | Evidence that measured concentration may vary with depth | A global depth field or permission to infer depth where it was not observed |

NOAA MDMAP is immediately useful for a shoreline-observation experiment, but
that narrower product should say exactly what it measures. The Ocean Cleanup
materials support feasibility and source discovery; their page images and
modeled illustrations must not be traced into atlas polygons.

## Required evidence model

Every future record belongs to exactly one of these classes:

1. observed shoreline debris;
2. observed surface sample;
3. modeled concentration field;
4. modeled river emission;
5. recorded cleanup operation; or
6. observed depth profile.

Each record requires source identity, observation/model time, coordinates and
CRS, units, sampling effort or model resolution, uncertainty, access method,
license, redistribution decision, and preparation history. A model boundary
is not a measured edge. Cleanup location is not concentration. A shoreline
count is not an ocean raster. Unknown depth is `UNAVAILABLE`, never zero.

## Minimum implementation gate

Before creating `src.generate/generate-anthropocene-water-debris.cc`:

- establish at least one redistributable spatial dataset with coordinates,
  dates, units, uncertainty, and a reproducible download;
- choose a single evidence class for the first canary rather than merging all
  classes;
- check the source-specific geographic and temporal coverage;
- define visual grammar that labels observation versus model and keeps missing
  data visible;
- add forward and reverse selection fixtures with evidence-record identity;
- document a 60% maximum observed-field opacity and the existing doubled-title
  rule without implying visual opacity equals uncertainty; and
- obtain a separate implementation and lifecycle decision.

The safest first canary is a NOAA MDMAP shoreline-observation plate with a
declared survey period and sampling-effort limitation. A global garbage-patch
surface or depth depiction is not yet supported.

## Stop conditions

- No website illustration or publication figure becomes source geometry.
- No world coverage is inferred from a national or North Pacific study.
- No missing observation becomes zero debris.
- No surface polygon acquires invented thickness or depth.
- No research prototype enters standard or optional generation.
