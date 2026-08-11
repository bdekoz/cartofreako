# Stage 15 R2 — anthropocene water-debris feasibility

Status: **historical feasibility gate satisfied by a bounded
exploration-only experiment; no promotion**

Checked: 2026-08-10

Historical contract: `contracts/water-debris-evidence-v1.schema.json`

Historical source manifest: `fixtures/water-debris-evidence/v1/manifest.json`
Implemented experiment contract:
`contracts/anthropocene-water-debris-experiment-v1.schema.json`
Implemented manifest: `fixtures/anthropocene-water-debris/v1/manifest.json`

## Decision

The original “do not implement” decision applied to a proposed merged global
debris field. That stop remains valid: the reviewed sources do not establish
one redistributable global spatial package with dates, units, uncertainty,
and reuse rights across shoreline counts, surface samples, modeled
concentration, river emissions, cleanup tracks, and depth profiles.

A narrower implementation gate is now satisfied. Twelve 2025/2026 **atlas
edition** SVGs render only five geolocated North Pacific depth-profile stations
observed in 2018. Every other source family remains context-only or
`UNAVAILABLE`; no garbage-patch polygon or invented thickness is drawn. The
edition label is not represented as an observation year. All five points pass
qualified forward/reverse checks in all six projection layouts.

The standard observation family has separately migrated to
`anthropocene-particulate-2025` and
`anthropocene-particulate-2026`. The water-debris products remain
exploration-only and outside default generation, release, and publication.

## Source findings

| Source | What it can support | What it cannot establish here |
| --- | --- | --- |
| [NOAA MDMAP](https://marinedebris.noaa.gov/our-work/monitoring/marine-debris-monitoring-and-assessment-project) | Dated, protocol-based shoreline macro-debris observations and interactive export | Open-ocean concentration, river emissions, operational tracks, or depth |
| [NOAA 2024 national survey record](https://www.fisheries.noaa.gov/inport/item/73092) | CC0 candidate-site geometry and survey-design context | Debris observations or a global layer |
| [The Ocean Cleanup GPGP overview](https://theoceancleanup.com/great-pacific-garbage-patch/) | Evidence vocabulary for samples, modeled concentration, cleanup, and vertical distribution | A checked redistributable coordinate/raster package or reuse license |
| [2015–2022 North Pacific study](https://doi.org/10.1088/1748-9326/ad78ed) | Publication-level context for repeated trawl/aerial sampling and modeled change | Authorization to redistribute underlying spatial observations or graphics |
| [North Pacific depth study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7203237/) | CC BY 4.0 station coordinates and observed depth profiles from 2018; five station locations are rendered | A global depth field, patch boundary, or permission to infer depth where it was not observed |

NOAA MDMAP remains useful for a later shoreline-observation experiment, but no
MDMAP observation export is bundled here. The Ocean Cleanup overview and
modeled illustrations support vocabulary and source discovery only; they are
not traced into atlas geometry.

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

## Implemented bounded gate

The first experiment now satisfies the minimum gate without broadening it:

- one CC BY 4.0 depth-profile source supplies five actual coordinates, dates,
  and maximum sample depths;
- `depth-profile` is the only rendered evidence class;
- source periods and North Pacific geographic limits remain visible;
- observation, context-only, and unavailable states are distinct;
- all five records have qualified forward/reverse fixtures in all six
  layouts;
- the observed layer is capped at 60% opacity and the title uses the doubled
  scale, without treating opacity as uncertainty; and
- the manifest explicitly denies standard lifecycle, default generation, and
  public release.

The checked contact sheet is
[`output/anthropocene-water-debris-v01/contact-sheet.png`](../output/anthropocene-water-debris-v01/contact-sheet.png).
A global garbage-patch surface or depth depiction is still unsupported.

## Stop conditions

- No website illustration or publication figure becomes source geometry.
- No world coverage is inferred from a national or North Pacific study.
- No missing observation becomes zero debris.
- No surface polygon acquires invented thickness or depth.
- No research prototype enters standard or optional generation without a
  separate reviewed promotion decision.
