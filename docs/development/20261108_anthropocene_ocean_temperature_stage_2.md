# Anthropocene water temperature — Stage 2 plan

Plan date: **Sunday, 8 November 2026**.

**Status: all four plate families are approved for unattended implementation.**
This separate document records the implementation plan, dependencies,
acceptance criteria and remaining human decisions. It is not a claim that
Stage 2 data products or maps have already been generated. The completed
repository reorganization and ocean review remain in the
[Stage 0/1 record](20261108_anthropocene_ocean_temperature_stage_1.md).

Build a local prototype edition for 2025 and 2026 that adds marine heatwaves,
ocean thermal seasons, compound coastal heat, and an India heat–particulate
pilot. Preserve the distinction between observed inputs and derived indices.
Use separate measures and legend keys, with explicit dates, denominators,
coverage and method versions. Routine implementation and validation choices
can be resolved unattended; human-gated decisions are collected at the end.

## Approved scope and plate identities

| Order | Canonical family; `YYYY` means a four-digit year | Principal view | Additional review measures |
| --- | --- | --- | --- |
| 1 | `anthropocene-marine-heatwave-YYYY` | Days belonging to qualifying marine heatwave events | Longest observed event duration; cumulative intensity in °C-days; event ledger |
| 2 | `anthropocene-ocean-thermal-season-YYYY` | Warm-season onset departure from local climatology, in days | Completed season length and length departure; observed warm days for incomplete seasons |
| 3 | `anthropocene-coastal-compound-heat-YYYY` | Days with unusual land heat and adjacent-ocean warmth | Shared eligible days; co-occurrence fraction; separate land-only and ocean-only counts |
| 4 | `anthropocene-heat-particulate-coexposure-YYYY` | Date-aligned unusual heat and elevated PM2.5 at the selected India monitors | Eligible station-days; co-occurrence fraction; separate heat-only and PM-only counts |

The four families imply eight prospective year identities. Measures and
matched-window variants belong under those identities rather than becoming
additional default passes. Register only implemented, validated prototypes
in the [atlas catalog](../../config/atlas-plates.json), with `default: false`.
The starting inventory is **45 named plates: 39 defaults and six prototypes**.
Eight validated additions would make 53 named plates and 14 prototypes,
while the default atlas would still contain 39 passes and 156 sheets.

Existing absolute SST, SST anomaly and record-day views remain separate.
Coral Degree Heating Weeks stays an independently sourced overlay on the
absolute water-temperature map; neither the new marine heatwave index nor
thermal-season length replaces DHW or the historical 2011 reef-threat plate.

## Starting evidence and data dependencies

| Input or reusable component | Already available | Stage 2 work still required |
| --- | --- | --- |
| NOAA OISST v2.1 | 1982–2026 SST/ice files and mask; 91 pinned input receipts; daily H3r5 working arrays and native-center membership | Derive seasonal percentile thresholds and event/season fields; freeze parameters and new receipts |
| Stage 1 ocean products | 2025 full year, 2025 matched window and 2026 YTD; monthly arrays; paired regional summaries; 36 map/legend sheets | Reuse dates, support and export machinery; do not derive daily events from period means |
| CPC land temperature | Existing native yearly TMAX/TMIN cache and land preparation pipeline | Audit actual dates, grid, source-day semantics and baseline completeness; acquire a separately dated refresh if needed |
| India particulate | Expanded 24-reference-monitor selection and separate AirGradient series; daily eligibility and matched station-date tables | Audit monitor crosswalks and dates; join qualified PM2.5 observations to the chosen land-temperature support |
| Rendering and catalog | H3r5 renderer, common AuthaGraph frames, separate legend builder and current catalog checks | Add prototype products, coverage views, source keys and export validation |

The [OISST acquisition ledger](../../output/ocean-temperature-20261108/data/acquisition-manifest.json),
[ocean package guide](../../output/ocean-temperature-20261108/GIT-CONTENTS.md),
[CPC fetcher](../../scripts/fetch-anthropocene-cpc-data.sh), and
[completed India study](20261108_particulate_data_enrichement_explore_v2_india.md)
are the starting provenance. The India study's
[validation receipt](../../output/india-particulate-20261108/enrichment/validation.json)
and [inventory](../../output/india-particulate-20261108/enrichment/inventory.json)
describe the selected observation network; they do not establish national
representativeness.

The edition date is November 8. The pinned ocean observations end on
**November 7**. Eligible reference PM2.5 currently ends on **November 4**;
the partial November 5 records do not pass the daily gate. Read CPC's actual
cutoff from its files. Every joined product ends at its own shared valid
support, which may be earlier than any provider's nominal endpoint.

Keep source caches immutable. A needed CPC refresh goes into a new Stage 2
cache with new hashes; it must not silently alter the retained land plates.
Full national India backfill, ERA5 and additional international SST providers
are extensions, not prerequisites for the approved local prototypes.

## Shared method and acquisition contract

1. **Freeze the edition and methods.** Add a versioned Stage 2 configuration
   containing source references, baseline years, calendar rules, thresholds,
   coverage gates, pair geometry and display scales. Record retrieval time,
   source version, URL, hash and preliminary/final status for every input.
   Audit existing caches before downloading. Keep original variables and units.
2. **Preserve spatial support.** Ocean analysis retains Stage 1's fixed native
   centers per H3r5 cell, complete-member daily mean and sea-ice screen.
   Missing or ice-excluded member days remain missing. H3r5 is a display and
   aggregation grid, not an increase in the 0.25° ocean or native CPC resolution.
   Station and coastal products retain their actual measurement or pairing
   support; do not fill unsampled hexagons.
3. **Save daily eligibility alongside values.** Carry source-valid,
   baseline-valid and joint-valid flags separately. Retain the existing 80%
   period coverage rule for ordinary count/rate maps; persistent-event and
   crossing measures need additional continuity checks. Missing observations,
   insufficient baseline, an undefined season and a measured zero are distinct.
4. **Use a declared fixed baseline.** Start with 1991–2020 so the new ocean
   indices can be read alongside Stage 1 anomalies. Percentile climatologies
   are new calculations; they are not NOAA's distributed anomaly field.
   Require at least 24 distinct baseline years and 80% of expected pooled
   observations per calendar window. Save the actual support counts.
5. **Retain monthly and comparable annual products.** Produce 2025 full-year,
   2026 YTD and matched calendar-window views where the statistic permits.
   Both sides of a comparison use the same eligible cell-days or station-days.
   Report numerator, denominator and cohort changes. Mark partial months.
   Completed seasons and incomplete seasons require different measures.
6. **Keep analysis independent of rendering.** Save daily/event ledgers,
   period summaries, coverage, parameters and digests before making maps.
   Process the daily archive in bounded spatial chunks with restartable
   outputs. Cache thresholds by input and method hash, not just by year.
7. **Version later revisions.** Preserve the November 8 snapshot. A future
   weekly review can refresh provisional inputs; freeze later monthly and
   annual editions after verifying provider latency and revision status.
   Record this policy without installing a recurring job as part of Stage 2.

For future seasonal sampling, retain all twelve months and rank local mean
temperature, interannual anomaly variance and absolute month-to-month change
separately. Test a common cohort before selecting exhibition examples.
Warm-season peaks, winter relative heatwaves, monsoon transitions and Delhi
pollution episodes need different sampling windows; the
[Stage 1 seasonal comparisons](20261108_anthropocene_ocean_temperature_stage_1.md#seasonal-comparison-and-continuing-acquisition)
remain the observed starting evidence, not permanent peak-month assignments.

## 1. Marine heatwaves

Use the [Hobday et al. definition](https://repository.library.noaa.gov/view/noaa/63891)
of persistent warmth above a local seasonal percentile. The
[authors' reference implementation](https://github.com/ecjoliver/marineHeatWaves/blob/master/marineHeatWaves.py)
provides a comparison for the core detector. Pin its exact revision when
building fixtures. The following reference parameters are adopted explicitly:

| Parameter | Planned setting |
| --- | --- |
| Seasonal threshold | 90th percentile from an 11-day calendar window, followed by a 31-day circular moving average |
| Event qualification | At least five consecutive days strictly above the threshold; ties do not exceed |
| Short interruptions | Join qualifying runs across at most two observed below-threshold days |
| Intensity | Temperature minus the seasonal climatological mean; cumulative intensity has units °C-days |
| Leap calendar | Derive February 29 climatology/threshold from February 28 and March 1; preserve the actual February 29 observation when present |

These are event-method choices. The fixed 1991–2020 baseline, baseline support
gates and strict missing-data policy below are declared local adaptations.
They do not change Stage 1's unsmoothed calendar-day anomaly calculation or
its separate leap-day record eligibility.

Compute both the seasonal mean and percentile with pinned pooling, smoothing
and quantile interpolation rules. Do not interpolate missing daily SST or
bridge an ice/missing day. A joined event may include observed cooler gap
days: retain both event-span days and strictly above-threshold days so the
reader can distinguish them. Sum signed anomalies across the declared event
span for cumulative intensity; do not silently clip or substitute threshold
excess for climatological anomaly.

Detect events on continuous available time series across December–January,
then allocate observed days and intensity to each reporting interval. Save
full event dates separately from the interval-clipped map quantities. Flag
events whose start or end cannot be observed. An unfinished run shorter than
five days at the snapshot edge is pending, not a confirmed event or proof of
no event. The longest duration at an open edge is a lower bound.

Recompute matched-YTD detection as of each year's matched cutoff, so the
2025 comparison does not use later days to confirm an event that the 2026
snapshot cannot yet confirm. Compare 1991–2020 with a separately labeled
1982–2011 baseline on representative complete-data regions; summarize changes
in thresholds, event days and intensity rather than choosing the baseline
that produces the strongest map.

**Acceptance:** synthetic threshold ties, four/five-day runs, two/three-day
gaps, missing barriers, leap dates and year boundaries pass; complete-data
fixtures agree with the pinned reference detector; mapped totals reconcile
to the event ledger; baseline sensitivity and edge censoring are visible.

## 2. Ocean thermal seasons

This is an **experimental local seasonal index**, not a universal biological
season or a published standard imported without modification. Its purpose
is to show when a location enters its normally warm part of the year and
whether that observed season starts earlier or lasts longer.

Use the smoothed 1991–2020 seasonal mean to identify the dominant annual
cycle. The initial design sets a cell's warm threshold halfway between its
climatological minimum and maximum. Test a minimum peak-to-trough amplitude
of **2°C**, with **1°C and 3°C** sensitivity variants. These are analytical
screening choices, not ecological thresholds.

Define onset as the first day of seven consecutive valid days above the
local threshold on the warming limb; define the end using seven consecutive
valid days below it after the warm-season peak. Apply the same crossing rule
to the baseline curve and target observations. Preserve threshold ties,
missing intervals and any competing crossings in diagnostic records.

Use a local season window anchored around the climatological cool phase and
label it by the year of its expected warm peak. It may require observations
from the preceding or following calendar year. Pin deterministic tie rules
and cycle-selection rules in configuration after inspecting the baseline
diagnostics. Reject weak, multiple or poorly supported cycles when a unique
season cannot be identified; do not force an onset into every ocean cell.

Report onset departure with circular date arithmetic: negative means earlier
and positive later. A late-December versus early-January difference must not
become an approximately one-year displacement. Report completed length and
its departure only when both transitions are observed. For 2026 seasons
still underway, show observed warm days and an open-season flag in a separate
variant; do not call that quantity final season length or interpret the
November cutoff as the season's end.

**Acceptance:** Northern/Southern Hemisphere fixtures, December–January
crossings, constant-temperature cells, multiple peaks, noisy crossings,
missing transition days and incomplete seasons behave as declared. Show
amplitude and persistence sensitivity; retain masked-cell reasons and the
fraction of source-supported ocean for which the index is defined.

## 3. Compound coastal heat

Define the analytical unit as an explicit coastal land/ocean pairing. Use
native CPC daily **TMAX** for land and a fixed adjacent OISST support for
water. These are different temperature measures; each is evaluated against
its own local 1991–2020 seasonal 90th percentile. The main statistic counts
date-aligned joint exceedance days, without imposing the marine heatwave
five-day event rule or relabeling land percentile exceedance as a record.

Construct a versioned pairing table from the repository's coastline geometry,
native masks and sample centers. Start with a maximum 100 km distance to the
coast and a 100 km adjacent-ocean neighborhood, with 50 km sensitivity checks.
These distances are study parameters. Require marine adjacency on the same
side of the local coastline; reject links across intervening land or inland
water. Inspect islands, narrow straits, peninsulas and estuaries explicitly.
H3 proximity alone is insufficient evidence for a coastal relationship.

For each land support, save the shoreline reference, ocean members,
distances, geometry hash and rejection reason where applicable. Compute a
fixed-member, area-weighted adjacent-ocean mean first, then derive that
series' percentile; an "any warm ocean cell nearby" rule would change the
measure with neighborhood size. Keep both source supports visible in data
and diagnostic figures. Shared ocean members do not create statistically
independent coastal observations.

On dates with valid land, water and thresholds, retain all four states:
neither unusual, land-only, ocean-only and both. The co-occurrence rate is
`both_days / joint_eligible_days`; the denominator is not all days or only
land-hot days. Compare years using identical pair geometry and shared valid
calendar dates. Audit the CPC and OISST source-day definitions before using
the word "simultaneous"; if their daily windows differ, label the result
**date-aligned coastal co-occurrence** and document the mismatch.

**Acceptance:** deterministic pair geometry, no cross-land leakage, known
four-state fixtures, missing-side exclusions, date-boundary fixtures and
count/rate reconciliation pass. Review World/Japan coastal samples and
distance sensitivity. Interpret association only; do not infer a physical
mechanism, coastal ecological damage or human exposure from this map.

## 4. India heat–particulate co-exposure pilot

Start with the existing eligible PM2.5 station-day tables, retaining source
station IDs, coordinates, monitor class and measurement provenance. Preserve
the **18 distinct valid hours** daily gate. Keep reference monitors and
AirGradient in separate products and keys. Deduplicate mirrored records
through an explicit crosswalk; unresolved identities remain excluded or
separately labeled rather than merged by a similar station name.

Assign each monitor to its containing valid native CPC land support and save
the assignment and distance to that grid center. Do not choose a distant
replacement when the containing support is missing. Land heat is local
TMAX above its 1991–2020 calendar-day 90th percentile. It is gridded regional
heat context at the monitor, not a temperature measurement by that monitor.

Use daily PM2.5 **above 35 µg/m³** as the initial atlas comparison threshold,
matching the retained particulate convention. Label it as a comparison
threshold, not a health/safety boundary or an assertion of compliance.
Retain concentrations and make threshold sensitivity possible without
mixing PM10 or modeled historical PM into the observational PM2.5 series.

PM days use `Asia/Kolkata`. Inspect CPC's actual analysis-day definition and
date alignment before joining. If identical observation windows cannot be
established, call the output **date-aligned heat–PM2.5 co-occurrence** and
provide a separately labeled one-day alignment sensitivity. Do not imply
hourly simultaneous exposure from unlike daily summaries.

Retain a station-date table with heat, PM, threshold flags, joint validity
and exclusion reasons. Produce the same four states as the coastal measure.
Compute fractions over joint eligible station-days. Year comparisons require
the same station and calendar-date pairs; also report excluded stations and
days. A larger monitoring cohort must not appear as a rise in co-exposure.
Avoid population totals or an India-wide health burden estimate from this
selected network.

Use station-supported marks in the India view. If H3 unions are also shown,
count each local cell-date once, retain monitor counts, and label the change
of grain. Do not interpolate a national exposure surface or extrapolate the
India pilot to Japan. Full-access national archives and ERA5 can remain
documented extensions while the available reference-monitor pilot is built.

**Acceptance:** duplicate/mirror fixtures, invalid-hour days, units, timezone
boundaries, missing heat, mixed monitor classes, station assignment and
matched-cohort denominators pass. Independently recompute selected station
dates from the retained hourly observations. Save coverage by station and
month next to all co-occurrence results.

## Presentation and repository implementation

Reuse the [approved Setouchi styling](20261106_setouchi_triennale_futures.md#current-saved-settings--7-november-2026)
and [shared review-sheet builder](../../scripts/atlas_review_sheets.py):
44 × 19.052559-inch sheets, the retained modified AuthaGraph composition,
Atkinson Hyperlegible, wine `#240413` and amber `#fcc553`, and H3r5 where
supported by the data. Each view has a **cartography + data-graphics sheet
and a separate legend/source sheet**. The solar-radiation plate's white
outlines and opacity scale describe that measure; new measures get suitable
shared scales of their own within the same presentation system.

Provide World/Japan pairs for the ocean and coastal prototypes. Provide a
World location view and an India detail pair for the particulate pilot;
any Japan companion must explicitly say the pilot has no observations there.
Use shared scale boundaries across years and scopes. Onset departure uses a
zero-centered diverging scale; days and intensity use separate sequential
scales. Give missing, undefined and incomplete results distinct keys.

Legends carry measure, units, baseline, source cutoff, calendar, support,
coverage rule, method version and sources. Add event/season examples and
coverage diagnostics as standalone scientific figures with their source
tables. A review index links every map to its exact companion legend and
includes method and validation receipts.

Planned repository additions below are names for future work, not existing
commands or completed artifacts:

| Planned path | Responsibility |
| --- | --- |
| `config/ocean-stage-2-20261108.json` | Edition, source references, scientific parameters, windows, thresholds and scales |
| `scripts/prepare-ocean-climate-baseline.py` | Shared, versioned seasonal means/percentiles and support diagnostics |
| `scripts/prepare-marine-heatwaves.py` | Daily flags, event ledger, interval summaries and baseline sensitivity |
| `scripts/prepare-ocean-thermal-seasons.py` | Local seasonal cycles, crossings, eligibility, censoring and sensitivities |
| `scripts/prepare-coastal-compound-heat.py` | Audited coastal pairs, land/ocean daily joins and joint counts |
| `scripts/prepare-heat-particulate-coexposure.py` | Station crosswalks, calendar joins, separate monitor classes and matched cohorts |
| `scripts/build-ocean-stage-2-plates.py` | Prototype maps, separate legends, figures and local review index |
| `scripts/validate-ocean-stage-2.py` | Independent numerical checks, support/ledger reconciliation and export receipts |
| `output/ocean-temperature-stage-2-20261108/` | Curated normalized outputs, source/method receipts, proofs and validation; ignored bulk caches and print intermediates |

Reuse [ocean decoding and H3 helpers](../../scripts/ocean_temperature.py) and
[Stage 1 plate construction](../../scripts/build-ocean-temperature-plates.py)
where their contracts fit. Keep production preparation separate from an
independent reference calculation. Add meaningful numerical fixtures for the
new scientific rules; documentation edits alone do not need new tests.

## Execution sequence and completion checks

| Step | Work | Completion evidence |
| --- | --- | --- |
| 2.1 | Audit pinned inputs, current coverage and source calendars; freeze the method configuration | Input ledger, grid/date checks, source cutoffs and documented method choices |
| 2.2 | Compute shared baseline diagnostics; implement marine heatwaves first | Reference agreement, event fixtures, sensitivity results and reconciled ledgers |
| 2.3 | Implement thermal-season definitions and coverage masks | Circular-calendar fixtures, complete/incomplete season diagnostics and sensitivity results |
| 2.4 | Implement coastal geometry and land/ocean daily joining | Inspected pairing examples, geometry rejection audit and four-state reconciliation |
| 2.5 | Implement the India station/heat join | Audited crosswalk, timezone statement, matched station-date cohorts and independent hourly spot checks |
| 2.6 | Render all supported year/measure variants and source sheets | SVG/PDF/PNG receipt for each declared sheet; complete companion links; World/Japan and India visual review |
| 2.7 | Register validated optional prototypes and document findings | Catalog/status/style checks, unchanged default selection, completed result ledger and human decisions at the end |
| 2.8 | Commit and push the reviewed implementation and curated evidence | Recorded commit IDs and verified remote branch; bulk caches excluded |

Run a small representative numerical pilot before a full-grid calculation.
Resolve routine parameter or implementation defects using the documented
evidence and record changes to the plan. A scientifically undefined field
is a valid result when its exclusion reason and coverage are explicit;
missing credentials are not a reason to fabricate observations or abandon
the independent approved work.

Stage 2 is complete when all four families have a reproducible local review
product, appropriately censored 2025/2026 comparisons, independent numerical
checks, map/legend exports and source/method/validation receipts. Include a
completion ledger with actual outputs and deviations from this plan. Do not
mark acquisition, processing, rendering or validation complete solely because
their commands or intended paths have been documented.

## Human-gated decisions after the local review

1. **Default promotion:** choose which validated prototypes and measure
   variants enter the default atlas. Until then, retain the 39-pass default
   selection and keep Stage 2 optional.
2. **Exhibition or website publication:** choose the final years, geographic
   views and public interpretation after inspecting the local sheets and
   coverage. Repository commit/push is already requested; public gallery
   publication is a separate action.
3. **Additional provider access or expanded scope:** decide on account-bound
   national India archives, ERA5 or other restricted products only after a
   concrete benefit and acquisition scope are documented. Public inputs and
   the existing pilot remain sufficient to complete this planned edition.

Selection of the four Stage 2 families is already approved. These final
decisions do not reopen that selection or block local implementation.
