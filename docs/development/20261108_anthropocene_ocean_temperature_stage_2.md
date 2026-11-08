# Anthropocene water temperature — Stage 2 plan and completion record

Plan date: **Sunday, 8 November 2026**.

**Status: all four approved families are implemented and validated.**
Implementation revision: **`04114b36e83e8df025b2ca2f5850a2adc12b6d5d`**,
committed and pushed to `origin/main`; the remote branch was verified.
The local edition contains **eight optional year identities, 32 measure/period
views and 128 separate map/legend sheets**, with four scientific figures.
Open the [review index](../../output/ocean-temperature-stage-2-20261108/index.html),
[validation receipt](../../output/ocean-temperature-stage-2-20261108/validation.json),
or [package guide](../../output/ocean-temperature-stage-2-20261108/GIT-CONTENTS.md).
The subsequent [documentation and build follow-up](20261108_documentation_followup.md)
records work deferred for the next session, including the Eureka rebuild and
aggregate default-atlas books; it does not reopen the completed Stage 2 data
or individual-sheet checks.
The approved method contract is retained below, followed by actual findings,
completion evidence and remaining human decisions. The completed
repository reorganization and first ocean review remain in the
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

The four families now have eight registered year identities. Measures and
matched-window variants belong under those identities rather than becoming
additional default passes. All eight are validated prototypes in the
[atlas catalog](../../config/atlas-plates.json), with `default: false`.
The inventory increased from 45 named plates to **53: 39 defaults and
14 prototypes**. The default atlas still contains **39 passes and 156 sheets**;
all default SVG/PDF/PNG receipts passed again after catalog integration.

Existing absolute SST, SST anomaly and record-day views remain separate.
Coral Degree Heating Weeks stays an independently sourced overlay on the
absolute water-temperature map; neither the new marine heatwave index nor
thermal-season length replaces DHW or the historical 2011 reef-threat plate.

## Starting evidence and data dependencies

| Input or reusable component | Starting evidence | Stage 2 completion |
| --- | --- | --- |
| NOAA OISST v2.1 | 1982–2026 SST/ice files and mask; 91 pinned input receipts; daily H3r5 working arrays and native-center membership | Computed seasonal thresholds, event ledgers and season diagnostics over 596,710 source-supported H3 cells |
| Stage 1 ocean products | 2025 full year, 2025 matched window and 2026 YTD; monthly arrays; paired regional summaries; 36 map/legend sheets | Reused fixed daily support, dates and export machinery; events were calculated from daily arrays |
| CPC land temperature | Existing native yearly TMAX/TMIN cache and land preparation pipeline | Audited 32 TMAX inputs; separately acquired 2026 through November 7; retained the older land-plate cache |
| India particulate | Expanded 24-reference-monitor selection and separate AirGradient series; daily eligibility and matched station-date tables | Audited 25 canonical monitors and 13,487 station-day rows; joined containing CPC cells and retained separate monitor classes |
| Rendering and catalog | H3r5 renderer, common AuthaGraph frames, separate legend builder and current catalog checks | Exported 128 sheets, added eight optional identities and preserved the 39 default selections |

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
**November 7**. Eligible reference PM2.5 ends on **November 4**;
the partial November 5 records do not pass the daily gate. The separate
AirGradient series ends on **October 2**. Refreshed CPC TMAX contains 311 dates
through **November 7**. Every joined product ends at its own shared valid
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

| Parameter | Implemented setting |
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

Reuse the [approved Setouchi styling](20261106_setouchi_triennale_futures.md)
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

The following repository additions are implemented. Shared calculations live
in `scripts/ocean_stage_2.py` and the compiled
`scripts/ocean-stage-2-kernels.cc`; source acquisition, sensitivity figures and
independent validation remain separate entry points.

| Implemented path | Responsibility |
| --- | --- |
| `config/ocean-stage-2-20261108.json` | Edition, source references, scientific parameters, windows, thresholds and scales |
| `scripts/prepare-ocean-climate-baseline.py` | Shared, versioned seasonal means/percentiles and support diagnostics |
| `scripts/prepare-marine-heatwaves.py` | Daily flags, event ledger, interval summaries and baseline sensitivity |
| `scripts/prepare-ocean-thermal-seasons.py` | Local seasonal cycles, crossings, eligibility, censoring and sensitivities |
| `scripts/prepare-coastal-compound-heat.py` | Audited coastal pairs, land/ocean daily joins and joint counts |
| `scripts/prepare-heat-particulate-coexposure.py` | Station crosswalks, calendar joins, separate monitor classes and matched cohorts |
| `scripts/build-ocean-stage-2-plates.py` | Prototype maps, separate legends and local review index |
| `scripts/analyze-ocean-stage-2.py` | Baseline/amplitude sensitivity, matched comparisons, coverage and method-example figures |
| `scripts/fetch-ocean-stage-2.py` | Hash-checked restoration of the separate CPC refresh and pinned event-detector reference |
| `scripts/validate-ocean-stage-2.py` | Independent numerical checks, support/ledger reconciliation and export receipts |
| `output/ocean-temperature-stage-2-20261108/` | Curated normalized outputs, source/method receipts, proofs and validation; ignored bulk caches and print intermediates |

Reuse [ocean decoding and H3 helpers](../../scripts/ocean_temperature.py) and
[Stage 1 plate construction](../../scripts/build-ocean-temperature-plates.py)
where their contracts fit. Keep production preparation separate from an
independent reference calculation. Add meaningful numerical fixtures for the
new scientific rules; documentation edits alone do not need new tests.

## Execution sequence and completion checks

| Step | Completed work | Completion evidence |
| --- | --- | --- |
| 2.1 | Audited pinned inputs and froze the method configuration | 79 source-file hashes verified; CPC refresh through November 7; separate India cutoffs and calendars |
| 2.2 | Computed shared baselines and marine heatwaves | 20 independent calendar baselines, 60 cell-period checks, pinned-reference fixture and all 5,081,997 event rows reconciled |
| 2.3 | Implemented thermal seasons and coverage masks | 40 independent cell-year checks; complete/open/missing/multiple-cycle fixtures; full-field amplitude and persistence sensitivity |
| 2.4 | Constructed coastal pairs and daily joins | 8,993 pairs; all 110,119 saved sightlines checked; 16 raw pair-years and eight land/ocean percentile checks |
| 2.5 | Joined India monitors to CPC heat context | 25 canonical monitors, 13,487 station-day rows, 848 monthly coverage rows and 14 independent hourly PM/CPC spot checks |
| 2.6 | Rendered and inspected supported variants | 128 SVG/PDF/PNG sheets, 32 views, four figures and 455 index links checked; World/Japan/India visual review |
| 2.7 | Registered eight optional prototypes and recorded findings | 53 named/39 default/14 prototype catalog passed; status/style/artifact checks passed; default 156 sheets verified |
| 2.8 | Delivered the implementation and curated evidence through the authorized commit/push | Bulk caches and print intermediates excluded; the implementation commit containing this record identifies the delivery, with remote verification reported on completion |

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

## Completed results and interpretation

### Matched daily comparisons

These are descriptive comparisons of the retained snapshot. They use the
same eligible support in each year; their populations, spatial weights and
observation windows differ, so they must not be pooled into an exposure score.
The annual 2025 maps remain separate from the matched 2025 comparisons.
Comparison totals include shared eligible days at supports below the map's
80% period-coverage gate; the display gate controls which marks receive a
value color, not which independently valid days exist in the ledgers.

| Measure | Matched support | 2025 | 2026 |
| --- | --- | ---: | ---: |
| Marine heatwave event-span fraction | January 1–November 7; 162,464,171 shared eligible H3 cell-days; approximate area weights from fixed native centers | 22.17% | 30.73% |
| Date-aligned coastal joint exceedance | January 1–November 7; 1,743,216 shared eligible pair-days | 142,768 days / 8.19% | 175,110 days / 10.05% |
| Date-aligned heat–PM2.5 co-occurrence, reference monitors | January 1–November 4; 3,734 shared eligible station-days in the selected India network | 233 days / 6.24% | 318 days / 8.52% |

The [monthly comparison figure](../../output/ocean-temperature-stage-2-20261108/figures/matched-cooccurrence.png)
shows within-year changes and explicitly marks partial November. Its source
tables retain each month's numerators and denominators:
[marine](../../output/ocean-temperature-stage-2-20261108/data/marine-matched-comparison.json),
[coastal](../../output/ocean-temperature-stage-2-20261108/data/coastal-comparisons.json),
and [India](../../output/ocean-temperature-stage-2-20261108/data/india-comparisons.json).
These are neither national population estimates nor event-attribution results.

### Marine events, uncertainty at boundaries and baseline sensitivity

The shared climatology uses linear quantile interpolation, 11 nonleap calendar
days pooled across 30 baseline years, February 29 interpolation before the
31-slot circular smoothing, and at least 24 years and 264 of 330 pooled
samples in every contributing window. All 31 constituent windows must be
supported. The baseline covers 596,710 source-supported H3 cells; 501,647 have
a complete supported annual seasonal curve. Counts retain the minimum
support across the smoothing window.

Daily detection includes 2024 context before the displayed 2025/2026 years.
The 2025 matched view is independently cut off on November 7 before event
qualification. Confirmed spans include observed cooler interruptions of at
most two days; missing or ice-excluded days are barriers. Full event dates
and interval-clipped contributions are both saved. The three ledgers total
5,081,997 event rows; overlapping annual/matched products are not independent
event inventories.

**Fine pale outlines identify an unobserved event boundary or a pending short
run.** This is a completeness cue. A run of fewer than five hot days touching
an unknown edge remains pending, and its days are excluded from the
event-eligible denominator while remaining in observed-day coverage. Open
event durations and intensities are observed contributions, not estimates of
their eventual totals. The outline width was reduced after proof review so
the value colors remain visible. Gray outlines retain source support that
fails the displayed measure's eligibility gate.

The pinned reference is
[`marineHeatWaves.py` at d7292bf08ade0af213fa760b0d7e4adfe5f52894](https://github.com/ecjoliver/marineHeatWaves/blob/d7292bf08ade0af213fa760b0d7e4adfe5f52894/marineHeatWaves.py).
The complete-data fixture agrees with its detector. Two compatibility
substitutions for current NumPy run only in memory; the downloaded source and
hash remain unchanged. Strict missing-data barriers and support gates are
declared local adaptations.

The [baseline sensitivity table](../../output/ocean-temperature-stage-2-20261108/data/baseline-sensitivity.json)
compares 1991–2020 with 1982–2011 at eight illustrative source-supported
locations, using shared eligible dates. Across the 16 location-year rows,
switching to 1991–2020 changes event days by **−41 to +12** and signed
cumulative intensity by **−83.36 to +2.82°C-days**. Annual mean seasonal P90
changes range from **−0.022 to +0.212°C**. This sample is a method sensitivity,
not a global estimate or a reason to switch baselines selectively.

### Thermal-season coverage and sensitivity

The 2°C amplitude gate and seven-day persistence rule are experimental
screening choices. Warm-peak year labels use adjacent-year observations:
even the 2025 season products may use 2026 context, always with the shared
source cutoff of November 7, 2026. Completed length requires both supported
transitions. Observed warm days count valid above-midpoint days within the
available local cool-to-cool window; they are not a final season length.

| Diagnostic status | 2025 cells | 2026 cells |
| --- | ---: | ---: |
| Complete season | 339,726 | 201,074 |
| Weak seasonal amplitude | 67,980 | 67,980 |
| Incomplete climatology | 95,063 | 95,063 |
| Multiple baseline seasons | 6,491 | 6,491 |
| Onset not observed | 12 | 168 |
| Missing transition support | 4,829 | 5,134 |
| Open season | 1,973 | 152,088 |
| Multiple observed seasons | 80,636 | 68,712 |

The totals are 596,710 cells in each year, not ocean-area percentages. The
large 2026 open-season count is a source-cutoff limitation; a decrease in
completed seasons is not evidence of shorter seasons. See the
[coverage figure](../../output/ocean-temperature-stage-2-20261108/figures/season-coverage.png).

At seven-day persistence, amplitude gates of 1/2/3°C yield
206,973/201,074/164,866 complete 2026 seasons. At the 2°C gate, persistence
of 5/7/10 days yields 182,358/201,074/214,657 complete seasons; stronger
persistence rejects more brief competing cycles. Full diagnostic counts are
retained in [amplitude sensitivity](../../output/ocean-temperature-stage-2-20261108/data/season-amplitude-sensitivity.json)
and [season metadata](../../output/ocean-temperature-stage-2-20261108/data/season-products.json).

The [event/season example](../../output/ocean-temperature-stage-2-20261108/figures/event-season-example.png)
and its [daily table](../../output/ocean-temperature-stage-2-20261108/data/method-example.json)
show why winter marine heatwaves and a warm-season onset are different
measures. At the illustrated Japan-east cell, 2026 onset is 18 days later
than its baseline, and the season is still open on November 7.

### Coastal geometry and daily calendars

The pairing table retains 8,993 CPC land centers and 110,119 ocean-member
links, using the pinned Natural Earth 10 m land, ocean and shoreline vectors.
The 100 km land-to-coast and ocean-neighborhood gates use great-circle
distances. Shoreline sampling at no more than 0.05° gives nominal reference
uncertainty of about 3 km. Ocean centers must lie in the marine polygon, and
the shore-to-center segment must not cross land. The geometry audit rejected
187,032 cross-land candidates and 433 dateline-spanning planar candidates;
5,567 coastal land candidates had no visible eligible ocean support.

This is conservative center-based adjacency, not a coastline-resolving
footprint model. It can omit narrow or complex connections, and fixed H3
membership does not resolve subcell coastlines. Shared ocean members also
mean the pairs are not statistically independent. At 50 km, joint counts on
shared support are 91,220 versus 95,638 at 100 km for the full 2025 year,
and 98,494 versus 103,155 for 2026 YTD. These within-year distance tests use
different temporal lengths; they are not another year comparison.

CPC metadata specifies a **06Z-to-06Z maximum-temperature day**. Its declared
valid range of −90 to 50°C is honored, including exclusion of values above
that declared range. The OISST daily analysis and India local-day PM summaries
do not establish identical observation windows. All joins are therefore
labeled **date-aligned**, without an hourly simultaneity claim. Source and
geometry receipts remain in [CPC inputs](../../output/ocean-temperature-stage-2-20261108/data/cpc-inputs.json)
and [coastal pairing](../../output/ocean-temperature-stage-2-20261108/data/coastal-pairing.json).

### India support, monitor classes and sensitivities

The pilot preserves 24 reference monitors and one separate AirGradient
monitor. The [crosswalk](../../output/ocean-temperature-stage-2-20261108/data/india-station-crosswalk.json)
retains canonical/source IDs, native CPC assignments and coordinates. The
containing-cell center and great-circle distance are saved for every monitor.
The
13,487 station-day rows contain no duplicate canonical monitor/date keys.
Containing-cell TMAX is gridded context, not a monitor's measured air
temperature. PM2.5 uses equal-weight distinct-hour means on Asia/Kolkata
dates, with at least 18 valid hours; 35 µg/m³ is the atlas comparison
threshold, not a health boundary.

Reference-monitor map marks aggregate to 20 occupied H3 cells, counting each
cell-date at most once. A joint mark requires heat and elevated PM at the
**same monitor**; it cannot combine one monitor's heat with another's PM.
Only 11 cells pass the 80% display gate in 2026, three in full-year 2025 and
one in matched 2025. Map cell-day totals therefore differ from the
station-day comparison above. The separate low-cost series has only 22
matched station-days, insufficient for a broad year-to-year inference.

The [station coverage figure](../../output/ocean-temperature-stage-2-20261108/figures/india-station-coverage.png)
and [station summaries](../../output/ocean-temperature-stage-2-20261108/data/india-station-summary.json)
show this uneven support. [Monthly station coverage](../../output/ocean-temperature-stage-2-20261108/data/india-station-monthly-coverage.json)
retains each monitor, month and annual/matched window, including absent days
in the denominator. Sensitivity records cover PM thresholds of
25/35/50 µg/m³ and heat-date shifts of −1/0/+1 day, each on common eligible
support. Independent hourly checks read adjacent archive filenames and
select observation timestamps, because a local midnight can occur in the
previous filename's archive. The pilot remains a selected observation
network, without national interpolation or population extrapolation.

## Delivery, reproducibility and final checks

The 32 views comprise nine marine event views, eight thermal-season views,
six coastal views, six reference-monitor views and three low-cost views.
Each has two geographic scopes and a separate map and legend, giving 128
sheets. Ocean/coastal scopes are World/Japan; the India pilot uses World/India.
Proof review covered value colors, thin incomplete-event outlines, legend
legibility, the retained Setouchi locator, India support marks and all four
scientific figures. Print SVG/PDF masters are local, regenerable artifacts;
preview PNGs, normalized products, ledgers, figures and receipts are curated
for Git. See the [package guide](../../output/ocean-temperature-stage-2-20261108/GIT-CONTENTS.md).

The 12 numerical fixtures passed, including threshold ties, event length/gap
boundaries, missing support, leap calendars, reference agreement, seasonal
cycles, four-state joins and spatial/date assignment. Independent production
checks and all export checks passed as recorded in
[validation.json](../../output/ocean-temperature-stage-2-20261108/validation.json).
Catalog, pass status, generation style and the 223-entry standard-artifact
manifest passed. The rebuilt default atlas separately passed all 156 sheet
checks. Source caches, heavy daily arrays and unrelated user archives are
excluded from this delivery.

Reproduction requires the pinned Stage 1 daily ocean working arrays, the
1991–2020 and 2025 CPC cache, retained India hourly observations, existing
Natural Earth geometry and the current source atlas. Restore those using the
[Stage 1 commands](20261108_anthropocene_ocean_temperature_stage_1.md#reproduction-and-verification)
and [India study](20261108_particulate_data_enrichement_explore_v2_india.md).
Dependencies include g++/OpenMP, libnetcdf, H3, NumPy, SciPy, pandas,
GeoPandas/Shapely, Matplotlib, Pillow, lxml, GDAL/Cairo and Inkscape.
Run from the repository root:

```sh
mkdir -p build/tmp build/tmp/matplotlib
export TMPDIR="$PWD/build/tmp"
export MPLCONFIGDIR="$PWD/build/tmp/matplotlib"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1
make fetch-ocean-stage-2
make prepare-ocean-stage-2
make render-ocean-stage-2
make check-ocean-stage-2
make check-atlas-catalog check-pass-status check-standard-artifact-manifest check-generation-style
```

The fetcher rejects changed pinned bytes; a later provider revision requires
a separate edition. Threshold caches key source/method hashes; coastal and
station caches also key geometry or station assignment. Export receipts key
SVG and linked layer content. `--exports-only` rechecks sheets and figures
against an existing successful data receipt; it is not a substitute for the
full data check after changing inputs or methods. No recurring acquisition
job was installed. Commit/push is part of the already authorized delivery;
the prior approved-plan revision is `bcccdffb33fef4415c9498572dbebcd266b9880e`.

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
