# Data update and visualization pipeline — implementation plan

Requested plan date: **8 November 2026**.

**Status: implemented; live acquisition and full print acceptance remain
pending.** The original aggregate was added
in commit `2e37e2f`; the implementation below replaces its current-data lane
with edition acquisition/selection and adds the complete `atlas-optional`
aggregate. Historical maintainer targets remain available explicitly.

## Implementation record

The transaction layer is implemented in [dataset.py](../../scripts/dataset.py),
[data-update.py](../../scripts/data-update.py),
[data_sources.py](../../scripts/data_sources.py), and
[data_http.py](../../scripts/data_http.py). It provides isolated inputs,
content hashes, conditional HTTP and identity-checked partial resume, source
checkpoints, native/scientific validation, immutable manifest resolution,
locking, and atomic activation. `--candidate-only` and failed-run resume are
available. No real edition has been activated during implementation.

[dataset-context.py](../../scripts/dataset-context.py) freezes build bindings
before Make expands its graph. [atlas-optional.py](../../scripts/atlas-optional.py)
orders the complete build, and
[build-current-atlas.py](../../scripts/build-current-atlas.py) composes newly
rendered sources. The current path derives observer profiles, retains H3r5
atmosphere/radiation presentation, renders audited petroleum/mineral values,
and produces catalog-derived books/contact sheets. Scientific scripts use
selected paths and actual cutoffs; India fetches the configured monitor
inventory from the public archive.

Full builds use an additional `builds/<build-id>/` directory beneath their
edition output. This keeps stable artifact references and preserves the last
completed output tree if a rebuild fails. The build pointer names that exact
run and receipt. Standalone `all`/`atlas` subsets use their edition folders.
The local convenience script is left unchanged until full live acceptance,
as required by this plan.

Verification: **76 Python tests pass**, covering transaction/failure/resume
and HTTP fixtures,
recursive binding/override checks, a real native-frame World/Japan composition
test showing a changed input changes the map, retained legend/PDF export,
existing ocean scientific regressions, prerequisite installer tests and
native validator compilation. Both native validation executables compile,
including the swarm ingestion-only check. Scientific prerequisites and the
OpenMP compile/link/runtime probe pass on this host. Native FIRMS coverage
fixtures and the existing Anthropocene particulate generation checks pass.
All 462 local links in the ten updated documents pass their focused link check.
The documentation checker's self-fragment crash is repaired; its full scan
still reports 30 pre-existing anchor/template-link errors in unrelated
historical documents and unexpanded HTML templates.

Outstanding production acceptance is explicit: the initial validation session
had no exported `FIRMS_MAP_KEY`, and the original sibling-path swarm archive
was absent. On November 9 the configured default was changed to the supplied,
readable archive at
`/mnt/gold/src/alpha60-samples-cache.gold/dan-da-dan-210.cache/cache.20260304.tar.xz`;
the local-input preflight now accepts it. With the source credentials exported,
retain the activated manifest and full-build receipts from the two-command
workflow. Until that succeeds, this record does not claim fresh-checkout/live-source
acceptance or completion of the rollout criteria.

## FIRMS coverage repair follow-up

The staged 2026 Suomi-NPP inputs reached 202 of 216 snapshot dates (93.5%).
The 14 missing dates coincide with the documented March, April, June and
July 2026 instrument outages in
[NASA's outage log](https://modaps.modaps.eosdis.nasa.gov/services/production/outages_suomi_npp.html).
S-NPP also ceased science delivery on November 2, 2026. Acquisition now
defaults to NOAA-20 standard processing plus NRT while retaining explicit
sensor overrides, the 95% calendar-date gate, geographic checks and unique
H3 cell-day semantics. New acquisition replaces the managed FIRMS directory
and names each chunk with its start date. Preparation checks the fire feeds
first and reports covered counts, percentages and missing dates on failure.
The preceding OGR unclosed-ring warnings are a separate geometry diagnostic.

Offline fetch tests cover default and overridden sensor selection, removal
of stale sensor files, chunk dates and preservation of prior staging on a
download failure. Native tests reproduce the 202/216 outage failure, test
95%/94% boundaries, retain the world-region audit, and verify that overlapping
standard/NRT detections do not multiply H3 cell-days. Live NASA reacquisition
still requires the key in the invoking shell.

## CPC download repair follow-up

The edition downloader initially bypassed the CPC fetcher's bounded-range
strategy, so NOAA's proxy could truncate full/open-ended yearly NetCDF
transfers repeatedly. CPC now requests verified 2 MiB ranges through the
shared HTTP cache, retaining conditional freshness checks, immutable objects
and identity-checked resume. Existing partial downloads can continue without
deleting the failed run or restarting previously completed sources.
The initial five-retry policy exhausted its 62-second fallback window during
the subsequent 96-file acquisition. The downloader now uses a configurable
30-minute budget per request/range, randomized exponential backoff, and
`Retry-After` seconds/dates. Persistent provider pacing is shared across files,
processes, runs and both PSL hostnames. Throttling increases the interval;
ten successful requests reduce it gradually. Logs include the filename,
retained/expected bytes, elapsed time, next retry and remaining budget.
The Make settings and optional bulk endpoint are documented in the
[generation guide](../pages/getting-started/generation.md#noaa-download-controls).
URL-specific receipts/partials retain provenance when selecting a different
endpoint; endpoint switching never appends unverified partials. The original
THREDDS default is retained to preserve existing partial-file resume.
Changed implementation fingerprints require a new acquisition run; shared
HTTP objects and partials still carry forward without rewriting old journals.
CPC files checked on the same UTC calendar day now reuse hash-verified complete
objects across update runs without network requests. Their receipt retains the
actual provider-check time and records `same-utc-day` cache acquisition. The
next day's new run revalidates conditionally. This is separate from the existing
same-run checkpoint policy and does not change other providers' freshness rules.
Regression fixtures cover truncated transfers, partial-file migration,
conditional revalidation, changed provider identities, ignored ranges and
inconsistent or unvalidated partial responses.

Follow-up verification: `make check-dataset` passes 58 tests and
`tests/test-data-update.py` passes seven more. The four updated documents pass
193 local-link checks. Live acquisition resumed the retained 58 MiB
`tmax.1981.nc` partial, recovered through repeated NOAA 429 responses, and
completed all 87,362,645 bytes. SHA-256 matches the HTTP receipt; GDAL opens
the 720×360 grid and 365 daily bands. A second same-day fetch with network
access explicitly disabled reused the cached object and preserved its original
provider-check time. Five complete CPC objects are now available in the shared
cache. Full acquisition remains pending an exported `FIRMS_MAP_KEY` in the
invoking environment; no active edition was changed during these checks.

## Intended user workflow

After installing prerequisites and configuring required source credentials:

```sh
make data-update
make ASSET_JOBS=2 atlas-optional
```

`data-update` must acquire the latest usable inputs for the configured
products, prepare and validate a complete dataset edition, and atomically
select that edition for subsequent local builds. `atlas-optional` must build
the complete set previously requested: standard native artifacts, the default
World/Japan atlas, optional Anthropocene ocean-temperature products, and the
Stage 2 optional climate products, including their validation and exports.
The optional Anthropocene scope is the four implemented Stage 1 year
identities and eight implemented Stage 2 year identities, including their
measure/period variants. This does not add planned, unimplemented families
or move the separate bounded PurpleAir/water-debris experiments into the
default atlas catalog.

Both commands must report the exact dataset ID and observation periods they
used. A successful update followed by a build must not silently read an older
checked-in profile, retained SVG, or hard-coded November working directory.
The update and build remain separate operations: downloading data does not
start rendering, and building a selected edition does not contact providers.

## Current behavior and implementation gaps

The [Makefile](../../Makefile) shares `EXPERIMENT_DATA_FETCH_TARGETS` between
`all-experiments-fetch` and `data-update`. The latter currently runs 17
fetch, preparation, or verification goals serially. It preserves each
child's existing date limits, caches, output paths, and promotion behavior;
it does not yet establish a dataset selection shared by the builds.

| Component | Current behavior | Required change |
| --- | --- | --- |
| Astronomy | `fetch-astro-data` replaces bounded catalogs in the configured directory; observation profiles retain their own calculation times. | Acquire into a dataset edition; distinguish catalog freshness from calculation time and record both. |
| Orbital data | A new dated directory is created under `build/`; native generation defaults to the checked-in November 9 profile. | Bind generation to the successfully acquired profile for the selected edition. Preserve the optional historical NASA reference status. |
| Particulate observations | Fetches use configured annual profiles; preparation writes `.prepared/` candidates while generation reads checked GeoJSON/profile pairs. | Resolve actual available coverage, generate candidate profiles with matching hashes, and select the complete validated pairs together. |
| CPC temperatures | A readable existing yearly NetCDF is reused without checking for a newer provider revision. Preparation requires a raw-manifest hash already pinned in the profiles. | Revalidate mutable yearly files, inspect their time axes, and generate profiles and prepared data as one transaction. |
| Resources | Fetching updates the base snapshot; the mineral extension is rebuilt into a dated directory with fixed edition labels and audited additions. | Preserve per-metric observation years; remove hard-coded edition labels from the current-data path and validate any newly available source editions. |
| Cloud-atmosphere and atoll evidence | Preparation is available, but its outputs and receipts are not part of a common dataset contract. | Include their actual coverage, prepared artifacts, and dependencies in the edition manifest. |
| Network inputs | Swarm preparation uses a pinned archive; synthesized fiber uses configured local snapshots. External checkouts and groundstation snapshots have no general latest-provider refresh rule. | Snapshot the consumed inputs and explicitly classify them as pinned/local unless a supported refresh adapter exists. |
| Default atlas | `atlas` composes retained Setouchi/ST2 and approved MSP rendered sheets. Updating raw observations does not replace that cartography. | Reuse the presentation rules and render new data layers from the selected edition. |
| Optional ocean/climate | Scripts use dated roots, fixed target years/cutoffs, pinned context files, and retained India observations. | Parameterize acquisition, daily arrays, product windows, preparation, rendering, and validation through the same dataset context. |

Relevant evidence:

- [Particulate fetcher](../../scripts/fetch-anthropocene-particulate-data.sh),
  [preparer](../../scripts/prepare-anthropocene-particulate-data.sh), and
  [profile/data verifier](../../scripts/verify-anthropocene-particulate-data.sh).
- [CPC fetcher](../../scripts/fetch-anthropocene-cpc-data.sh) and
  [temperature preparation wrapper](../../scripts/prepare-anthropocene-temperature-data.sh).
- [Orbital snapshot recorder](../../scripts/refresh-orbiting-snapshot.py).
- [Resource extension](../../scripts/prepare-mineral-additions.py).
- [Atlas compositor](../../scripts/build-atlas-defaults.py) and
  [presentation revision script](../../scripts/revise-setouchi-plates.py).
- [OISST acquisition](../../scripts/fetch-ocean-temperature.py),
  [ocean context acquisition](../../scripts/fetch-ocean-context.py), and
  [Stage 2 context](../../scripts/ocean_stage_2.py).
- [Current build follow-up](20261108_documentation_followup.md), including
  remaining historical 38-entry/152-sheet assumptions in atlas composition
  and aggregate review-book generation.

## Definition of “latest available”

Capture one UTC `requested_as_of` at update startup. Resolve each source
against that instant and the requested product years; do not recalculate the
run boundary independently in each child process.

1. **Availability is observed.** Inspect provider listings, metadata, and
   actual timestamps in downloaded files. The host date, download time, or
   successful HTTP status does not establish observation coverage.
2. **Mutable files are revalidated.** Use conditional HTTP requests where
   supported. Reuse unchanged content after a successful freshness check;
   replace changed bytes with a new content-addressed object. A changed
   current-year file must not be accepted merely because its old cached
   copy remains parseable. Without reliable validators, use a documented
   source-specific refresh policy and verify newly downloaded content.
3. **Provider cadence is respected.** Retain CelesTrak's two-hour reuse
   policy and existing refusal handling. Do not introduce repeated requests
   just to make a run appear newer. Record when cached data were last checked
   and when a later check is permitted.
4. **Actual usable dates govern products.** Source coverage, QA-eligible
   coverage, and common support in a joined product are separate fields.
   A new ocean date does not advance a coastal or station product beyond
   its usable land-temperature or PM2.5 support. Do not fill unavailable
   observations with zero or extend coverage labels past eligible data.
5. **Preliminary observations remain identified.** Preserve provider
   preliminary/final flags, publication lag, gaps, and incomplete seasons or
   heatwave events. A new data edition can contain the same observation
   dates with revised provider values.
6. **Static inputs remain dated.** A pinned archive, baseline, 2011 reef
   study, or manually audited mineral table is not relabeled as a current
   observation. The manifest must disclose which inputs were checked for
   newer provider data and which remain explicitly pinned.
7. **Configured years remain explicit.** Initially preserve the 2025 full-year
   and 2026 year-to-date product identities. Updating data does not silently
   add a new catalog year. A future year rollover requires generated
   year-specific identities, compatible profiles, and its own validation.

An unavailable required source fails the update. The previous valid edition
remains selected. A failed remote freshness check must not become a claim
that an old cache is the latest available dataset. The NASA SSC reference is
an existing exception by role: a dated `historical-validation-only`
reference is permitted while fresh CelesTrak catalogs drive current positions.

## Dataset edition and activation contract

Introduce a versioned dataset schema, a small Python resolver/validator, and
an explicit product/source dependency registry. Proposed locations:

```text
config/data-products.json                 # product groups, methods, source policies
contracts/dataset-manifest-v1.schema.json
scripts/data-update.py                    # acquire, prepare, validate, activate
scripts/dataset-context.py                # resolve one edition for a build
.cartofreako/data/cache/sha256/            # immutable acquired objects
.cartofreako/data/runs/<run-id>/           # in-progress receipts and resumable state
.cartofreako/data/editions/<dataset-id>/   # complete immutable dataset editions
.cartofreako/data/current.json            # atomic reference to validated edition
```

These paths are proposed. Keep dataset storage out of ordinary `make clean`;
cache cleanup must be an explicit later operation that preserves referenced
editions. Never hard-link mutable user source files into the immutable store.

The manifest must contain:

| Area | Required fields |
| --- | --- |
| Identity | Schema version, immutable dataset ID, requested as-of time, resolution time, selected product groups and years, parent edition if any. |
| Reproducibility | Repository revision plus digests of relevant working-tree implementations, configuration, method versions, spatial support, and baseline definitions. A dirty worktree must be identified accurately. |
| Sources | Logical source ID, public/redacted URL, provider edition, content hash/size, retrieval and freshness-check times, HTTP validators where useful, acquisition mode, and source-specific reuse policy. |
| Coverage | Actual observation start/end, QA-eligible support, geographic/station scope, missingness, preliminary/final status, and the reason any source is intentionally pinned. |
| Prepared inputs | Relative paths and hashes for each profile, normalized dataset, raw manifest, grid/membership, station crosswalk, and dependency ledger. |
| Products | Canonical product IDs, their exact input IDs, calculation times where applicable, observation windows, shared-support rules, and validation receipts. |
| State | Acquisition/preparation/validation outcomes and activation eligibility. Failed or incomplete runs cannot be current. |

FIRMS keys, authenticated URL tokens, and `.netrc` contents must never enter
manifests, command transcripts, source notes, or exceptions printed in logs.
Use the existing secret-safe credential checks and sanitize provider errors.

Activation is automatic for the local current-data workflow after the
declared checks pass. This is the concrete replacement for today's manual
profile/candidate selection. It does not overwrite historical editions,
promote optional prototypes to default catalog status, or publish a gallery.
Do not replace a checked profile hash merely to suppress a mismatch: generate
and validate a new profile/data pair in the candidate edition first.

Only a complete, validated manifest may replace `current.json`, using a
same-filesystem atomic rename. Failed runs retain resumable state and report
the failing source, recovery action, and still-active dataset ID. Serialize
activation with a lock; a concurrent build can continue using its already
resolved immutable edition.

## Make and build interfaces

### `make data-update`

Refactor the current aggregate into a thin entry point for the update runner.
Reuse the existing source logic through parameterized adapters instead of
maintaining a second set of download implementations. Continue sharing the
experimental source registry with `all-experiments-fetch`; preserve that
target's documented clean/build behavior separately.

The runner performs, in order:

1. Resolve product scope, run boundary, required sources, and storage paths.
2. Check credentials, scientific/native prerequisites, local inputs, and
   estimated disk needs before large downloads. Keep the existing FIRMS
   request/recovery instructions in the error log.
3. Discover availability, revalidate caches, and acquire immutable inputs.
4. Resolve product windows and materialize edition-specific profiles.
5. Prepare normalized data and shared working arrays from those inputs.
6. Validate schemas, hashes, coverage, source joins, and scientific invariants.
7. Write the final manifest, atomically activate it, and print a concise
   source/coverage summary plus the next build command.

Start with bounded or serial acquisition and preparation. Shared expensive
inputs must be acquired once. Resume verified work after interruption without
repeating large downloads or mixing bytes from different remote revisions.

### Selection shared by all builds

Add a single resolver used by `all`, `all-resilient`, `atlas`, optional
builders, and their direct generation targets. Proposed selection interface:

```sh
make atlas-optional                          # use the active validated edition
make DATASET_MANIFEST=/path/to/dataset.json atlas-optional
make DATASET=legacy all                      # explicit historical/repository mode
```

The resolver must run before recipe expansion that needs dataset-specific
paths. It generates a validated build context and Make variable file, then
passes the exact immutable manifest path to every recursive Make and Python
process. Propagate resolution failures as errors; do not hide them inside
`$(shell ...)` or evaluate arbitrary manifest values as Make syntax.

Freeze the selection once per invocation. In particular, both passes of
`all-resilient` must use the same edition even if another update activates a
new current pointer between passes. Respect explicit profile overrides only
in a documented custom/legacy mode; reject combinations that mix a selected
current edition with unrelated profiles or prepared files.

After the migration is complete, current-data builds without a valid active
edition must stop with instructions to run `make data-update` or explicitly
choose `DATASET=legacy`. Do not silently fall back to retained November data.
Keep historical regression tests and explicit legacy builds fully offline.

### New `make atlas-optional`

This is the requested **complete build aggregate**, including the default
plates as well as the optional Anthropocene products. It is not an alias
for only the additional climate sheets.

| Previously listed command/stage | Responsibility in the proposed workflow |
| --- | --- |
| `make check-prerequisites` | Check the required toolchain before update/build work; include scientific Python, NetCDF, Cairo, and OpenMP checks needed by these products. |
| `mkdir -p build/tmp` | Create managed temporary/cache directories as Make prerequisites. |
| `make ASSET_JOBS=2 all-resilient` | Build the standard native artifacts against the resolved dataset context. |
| `make ASSET_JOBS=2 atlas` | Compose and export the current World/Japan default atlas from newly rendered source sheets. |
| `make generate-ocean-temperature-preview` | Prepare as needed and render the full Stage 1 SST, coral, anomaly, record-day, and matched-period products; do not select the reduced SST-only preview. |
| `make fetch-ocean-stage-2` | Acquisition belongs in `data-update`. The build checks the selected inputs locally and does not fetch again. Preserve a separate frozen-edition restore path. |
| `make prepare-ocean-stage-2` | Build missing/stale Stage 2 derived arrays from the same resolved ocean, CPC, and India inputs. |
| `make render-ocean-stage-2` | Render marine heatwaves, thermal seasons, coastal compound heat, and India heat/particulate views and exports. |
| `make check-ocean-stage-2` | Run the corresponding scientific and export validation, alongside the Stage 1, atlas, and standard artifact checks. |

Implement `atlas-optional` as an ordered dependency graph or a controlled
serial orchestration over these stages. `-j` must not race data preparation,
atlas template generation, or validation against an incomplete render.
`ASSET_JOBS` must control optional exporters too; remove their independent
hard-coded worker counts. Preserve failed-stage exit status and never print
an aggregate completion message after an incomplete build.

Write products to an edition-specific tree, for example:

```text
output/data-editions/<dataset-id>/native/
output/data-editions/<dataset-id>/atlas/
output/data-editions/<dataset-id>/anthropocene-optional/ocean/
output/data-editions/<dataset-id>/anthropocene-optional/climate/
output/data-editions/<dataset-id>/validation/
```

Every map, legend, raster, PDF, PNG, index, and book must record or trace to
the dataset ID and its input hashes. A build-current pointer may advance
only after that requested output set passes validation. Selecting new data
must not relabel an old completed atlas as the new build. Do not overwrite
tracked historical output directories or replace an unmanaged directory
with a symlink during migration.

## Implementation stages

### 1. Establish the context and transaction layer

Add the source/product registry, manifest schema, context loader, update-run
state machine, activation lock, and atomic pointer handling. Add tests for
incomplete manifests, wrong hashes, path resolution, secret redaction,
resume behavior, concurrent updates, and explicit historical selection.
Expose candidate resolution without activation for debugging; default
`data-update` activates only after full validation.

**Exit:** a synthetic complete edition can be selected and reproduced;
failed or partial editions cannot replace it. No real source or build is
declared migrated merely because it has an entry in the registry.

### 2. Migrate current native source adapters

- Add destination/context arguments to astronomy, resources, orbital,
  cloud-atmosphere, atoll, particulate, and CPC wrappers. Eliminate in-place
  mutation from the current-data lane while preserving explicit historical
  workflows.
- Audit astronomy's observer dependencies as well as its catalogs: the
  current astronomy fetcher does not refresh the Hubble platform elements.
  Resolve that OMM input through the shared CelesTrak acquisition, validate
  epoch age at the selected calculation instant, and generate matching
  observer profiles. Keep configured observer positions and astronomical
  calculation times explicit; a fresh catalog alone does not make an old
  observer ephemeris current.
- Update mutable CPC files using provider revalidation and actual time axes;
  generate raw manifests and matching temperature profiles together.
- Resolve source-specific particulate coverage, FIRMS standard/NRT overlap,
  canonical IDs, annual archives, and current-year files without double
  counting or pretending all sources reach the same date.
- Generate new resource edition metadata without changing observation years.
  Source-release discovery and schema/PDF changes require validated parsers;
  unsupported new editions must fail visibly or remain explicitly pinned,
  never silently inherit a “latest” label.
- Snapshot the actual consumed local network/groundstation data. Do not
  `git pull` unrelated checkouts, rewrite their revisions, or invent an
  unavailable upstream refresh mechanism.
- Bind native generators to the new manifest and validate generated profile
  hashes, totals, finite states, coverage, and existing source constraints.

**Exit:** changing a validated input changes the corresponding native build;
unchanged verified content reuses its artifacts. An orbital build uses the
new profile, and an Anthropocene build uses its new profile/GeoJSON pair.

### 3. Migrate ocean and optional Anthropocene acquisition/preparation

Parameterize [OISST fetching](../../scripts/fetch-ocean-temperature.py),
[context fetching](../../scripts/fetch-ocean-context.py),
[Stage 1 preparation](../../scripts/prepare-ocean-temperature.py), coral
preparation, `ocean_stage_2.py`, and every Stage 2 preparation script. Remove
fixed output roots, date counts such as 311, and literal November 7 cutoffs
from the current-data path. Audit imported module globals as well as CLI
defaults so changing one root cannot leave a hidden historical dependency.

Acquire the newest supported CRW/JMA context into a new edition while retaining
the frozen context config for historical reproduction. Share the current
mutable CPC acquisition across native temperature plates and the optional
coastal/India products instead of using disconnected caches.

The India product needs a real adapter for the already configured reference
monitor and AirGradient inputs. Discover their latest authorized available
observations, validate station metadata, deduplicate station/date rows, and
retain separate monitor classes. Do not expand the monitor selection or
claim national coverage as part of this work. If current observation access
cannot be implemented from the existing sources, report that dependency as
unresolved and do not claim the complete latest optional set is delivered.

Retain the validated scientific methods: 1991–2020 climatology, historical
record ordering, calendar/leap rules, native-grid/H3 support, ice and missing
data policies, coverage denominators, heatwave gap rules, incomplete seasons,
and station/timezone join semantics. Cache keys include source hashes,
support geometry, parameters, and implementation hashes. Preserve and
validate monthly, matched-period, sensitivity, diagnostic, and figure outputs.

**Exit:** the same immutable inputs reproduce the frozen scientific results;
an extended current-year input advances only the eligible affected products,
with accurate dates and incomplete-period flags.

### 4. Regenerate atlas sources and apply the retained presentation

Refactor the current atlas path so data layers are generated from the dataset
context before composition. Reuse approved framing, palette, symbols, label
sizes, separate legends, and layout recipes; do not reuse a historical map
layer just because it has the approved appearance.

Replace hard-coded Setouchi/MSP source choices in the current-data path with
logical product bindings. Include the World and Japan observer, clouds,
groundstations, fiber, minerals, and land-temperature layers in the audit.
Date-bound historical captions and orbital positions must not leak into a
new dataset's source sheets. Where a view needs a different observer profile,
derive and hash that profile explicitly from the edition's configured view.

Update bibliography and legend generation to use actual manifest periods,
methods, units, source URLs, and coverage. Replace historical 38/152 and other
fixed total assertions with expectations derived from
[the catalog](../../config/atlas-plates.json) and selected product measures.
Keep the 39 current default identities and optional prototype status unless
the catalog is deliberately changed. Repair current atlas book/review-index
assembly as part of this stage, not just individual SVG exports.

**Exit:** modifying a dataset layer changes the expected map and legend
receipts; a completed current atlas cannot contain an untracked retained
source sheet from another data edition.

### 5. Add `atlas-optional`, validation, and documentation

Wire the complete aggregate described above and add it to `list-targets`.
Reuse existing render/export code after it accepts the shared context.
Extend prerequisite checks and installation documentation for the scientific
dependencies; use a documented Python environment instead of uncontrolled
system-wide `pip` installation.

Update these user-facing documents in the same implementation stage:

| Document | Required update |
| --- | --- |
| [README](../../README.md) | Present `make data-update` then `make atlas-optional` as the complete current-data workflow; explain the smaller `all` and `atlas` scopes. |
| [Generation guide](../pages/getting-started/generation.md) | Document activation, source coverage, manifest selection, cache freshness, output directories, failure/resume behavior, and historical replay. Replace today's candidate-only limitations after implementation is verified. |
| [Prerequisites](../pages/getting-started/prerequisites.md) | Include scientific dependencies, disk/cache expectations, P-Tree/FIRMS and configured India access, key-recovery logs, and environment setup. |
| [Generation styles](../pages/getting-started/generation-styles.md) | Explain current-data atlas composition and the retained presentation; separate it from historical ST2/MSP reproduction. |
| [Generation methods](../pages/getting-started/generation-methods.md) | State which optional products the aggregate builds, their unchanged scientific methods, observation windows, and prototype lifecycle. |
| [Source layout conventions](../pages/getting-started/source_layout_conventions.md) | Describe edition manifests, source storage, current pointers, dataset-specific outputs, and receipt locations. |
| [Orbital notes](../pages/passes/orbital-technosphere.md) and [Anthropocene notes](../pages/passes/anthropocene/implementation.md) | Document automatic validated local selection, historical replay, actual source lag, and how maps/legends identify their selected inputs. |

Preserve dated completion records as historical evidence; add links to the
new workflow instead of rewriting their captured observations as current.
Update any convenience build script to invoke `atlas-optional` after the new
aggregate is verified. Do not leave the old multi-command sequence documented
as sufficient to consume newly updated datasets.

## Validation and acceptance

Use local fixture providers and small scientific fixtures before any full
acquisition. Tests must exercise behavior rather than merely compare a
hard-coded list of commands.

| Scenario | Required evidence |
| --- | --- |
| Provider updates a still-readable current-year file | Freshness discovery detects it; a new hash and edition are produced; old inputs remain reproducible. |
| Provider reports unchanged data | Network reuse follows policy; content and derived artifacts are reused; freshness-check time remains distinguishable from retrieval time. |
| Missing key, source outage, invalid payload, or parser drift | Clear failure, no secret leakage, no incomplete activation, and the previous current pointer remains intact. |
| Interrupted download or preparation | Resume verifies partial identities and completed hashes; no mixed provider revisions or published partial manifest. |
| Unequal source lags or missing days | Product windows and joined denominators reflect eligible shared support, with missingness retained. |
| Corrupted raw/prepared input or profile mismatch | Validation fails before rendering; rewriting a checksum alone cannot make the scientific validation pass. |
| Changing only an orbital/temperature/PM2.5 input | The dependent native plates, atlas layers, legends, and optional products change as expected; unrelated products can stay cached. |
| Concurrent update during a build | Every artifact and both resilient build passes retain one resolved dataset ID. |
| Parallel or keep-going invocation | No fetch/prepare/template races and no aggregate success after a failed required stage. |
| Full optional selection | Default atlas plus all requested optional families, periods, maps, legends, figures, PDFs, PNGs, indexes, and books have nonempty outputs and matching receipts. |
| Historical replay | Explicit legacy/pinned selection reproduces historical input selection and validated scientific outputs without network access. |
| Fresh checkout | Documented setup and two-command workflow work without an ignored pre-existing atlas or hidden dated working arrays. |

For the first real run, retain availability receipts, the activated manifest,
coverage summaries, numerical/export validations, and a full-build receipt.
Verify the actual data-to-artifact dependency chain for representative World
and Japan sheets from every family. Compare observation dates and hashes,
not only file modification times or whether the build exited successfully.

The repository-wide documentation checker currently has a recorded
self-fragment/path-handling failure. Repair it or explicitly report that
separate failure; validate all new links and runnable examples regardless.
Do not claim a full documentation gate passed from a changed-lines-only check.

## Rollout and completion criteria

Implement the transaction layer first, then native adapters, ocean/India
preparation, atlas regeneration, and finally the complete aggregate. Retain
explicit historical entry points while testing the current lane. Switch the
default resolver to current-data mode only when all selected product families
have real manifest bindings and the fresh-checkout acceptance test passes.

The work is complete when `make data-update` followed by
`make atlas-optional` produces the requested full plate set from one validated
edition, automatically selects that update locally, reports truthful
per-product coverage, and succeeds without manual profile/hash editing or
retained rendered-data substitutions. An optional family without a working
fresh-data adapter is an outstanding item, not a completed rollout.

Public publication, changes to scientific definitions, broader station/provider
access, and promotion of prototype identities into the default catalog are
outside this implementation plan. They are not prerequisites for coding or
testing the workflow defined here.
