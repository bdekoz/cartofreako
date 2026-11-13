# Make workflow v4: data selection, render recovery and full atlas completion

Work record opened 11 November 2026, America/Los_Angeles. All human-facing
times in this record use PST/PDT; identifiers and machine receipts retain UTC.

The user approved unattended correction and completion of `make atlas-optional`,
including recovery of the saved native work and documentation of every fix.
This record preserves the diagnoses, fixes, commands, checks and completed result.

## Current status

**Complete at 6:39:03 PM PST on 11 November 2026.** Run
`20261112t003745z-8638649d869b` passed all 11 stages and all three full output
validators. The selected dataset remains `20261111t043605z-cf34314e91c3`.
`.cartofreako/data/build-current.json` now selects this completed run.

| Delivery | Completed output |
| --- | --- |
| Native standard products | 223 products and 223 checked screen PNG/lossless-WebP pairs |
| Default atlas | 39 subjects / 156 separate map and legend sheets |
| Atlas books | World 80 pages; Japan 80 pages; combined 158 pages |
| Stage 1 ocean | 9 measure/period selections / 36 sheets |
| Stage 2 climate | 32 measure/period views / 128 sheets and 4 scientific figures |

Independent completion verification passed for **4,054 artifact files /
28,897,128,685 bytes**, all 324 recorded implementation files, the publication
pointer, book hashes/page counts and recovery evidence. The original 1,067
native files and 916 source cache files remain unchanged. The two screen
readers, 98 Python regressions, Node path checks, 82 actual optional frames
and representative PDF reviews passed. The final production unit run also
passed, with one optional external-reference comparison skipped as explained
in the completion record below.

The displayed ocean periods remain **2025 full year**, **2026 through
9 November**, and the matched **2025 January 1–November 9** window. Existing
historical inputs supply the scientific baselines and record comparisons.
This render did not acquire new provider data. No human decision or required
build work remains outstanding.

## Starting state

- Selected dataset: `20261111t043605z-cf34314e91c3`.
- Manifest SHA-256: `1713b9952e82c2dbe7c7dd26f4d303e7258ddc35751ffacd14e0090716d8443c`.
- All 12 sources validated; 31,382 input files, 87,171,142,762 bytes.
- Failed build: `20261111t072338z-dd008eb13287`.
- Started 10 November at 11:23:38 PM PST; failed state written 11 November
  at 1:09:51 AM PST, after 1 hour 46 minutes.
- 911 required non-screen targets are present. The native directory contains
  1,067 files / 7,441,711,943 bytes including supporting metadata and source files.
- Missing: 223 screen PNGs, 223 lossless WebPs and their catalog. Atlas,
  Stage 1 ocean and Stage 2 climate output directories do not yet exist.
- No build processes are running and no completed-build pointer is published.

The original state records an `all-resilient` exit status of 2. Its terminal
output was not retained. A read-only input lookup reproduced `ENOENT` at the
first screen input: the exporter hardcoded `assets.generated/`, while all 223
source plates are available under the selected run's `native/` directory.
The exporter and canonical manifest were unchanged from the failed build's
Git revision, so this mismatch also existed during that run.

## Fixes and recovery work

### Screen output bindings

`scripts/generate-screen-1080p.mjs` now resolves the native directory from
`GENERATED_DIR` or the selected `DATASET_OUTPUT_ROOT`, retaining the legacy
default when neither is set. It rejects conflicting bindings. Canonical
manifest paths remain stable identifiers and are mapped to the selected
directory for SVG/gzip, PDF, full PNG, screen PNG and WebP access.
Screen worker count also honors `ASSET_JOBS` unless `SCREEN_JOBS` overrides it.

Regression coverage includes legacy/custom/edition paths, conflicting roots,
path traversal and mismatched source stems. The real 223-plate export passed
end-to-end rendering, source stability and lossless PNG/WebP pixel checks.

### Recovery provenance and remaining work

The old build pins revision `8b76ec6` and a dirty working tree. Its originally
recorded implementation file bytes still match, but later commits and added
scripts mean ordinary `--resume` must reject the current checkout. Recovery
will create a new run, retain the failed run unchanged, and record the hashes
and origin of reused native files. It will not rewrite the failed run's identity.

`--reuse-native-from BUILD_ID` starts a new run. It requires the same dataset
manifest, unchanged native producers and Make graph, and a failed source run.
Only the coordinator/screen exporter, the post-native atlas compositor/sheet
exporter/H3 presentation helper and the independent observer-study scripts may
differ. Legacy
JavaScript/runtime/font files omitted by the original
fingerprint are checked against the original Git revision. The actual recovery
precheck verified **317 producer files**. Copied files are hashed before and
after copying; symlinks, empty outputs, concurrent changes and conflicting
destinations are rejected. Screen outputs and their catalog are regenerated.
The new run retains the original build state and a `validation/reused-native.json`
receipt; the failed source run is not rewritten.

### Logs, implementation identity and publication

The coordinator now saves each stage's redacted combined output under `logs/`,
and records its phase, command, PID, start/end time and return code in the build
state. Implementation identity now includes JavaScript/runtime helpers, fonts,
the generation profile and the standard artifact manifest as well as the
previous Python/native/configuration files. End-of-run checking discovers the
file inventory again so files added during a build cannot evade the check.

The final receipt previously included the mutable build-state JSON, then
changed that file from `building` to `complete`, invalidating its recorded
hash. The receipt now excludes its own file and the mutable state, and includes
the previously omitted WebP and compressed SVG exports. The recovery receipt
and original producer state remain part of the pinned delivery evidence.

### Screen validation and initial regression results

The canonical inventory contains **223** plates. Two screen validators still
hardcoded **217** plates, **84** resource masters and **1,085** parent/output
records. They now compare exact catalog IDs against the canonical manifest
and derive resource/pass/file totals from that independent inventory. Both
readers accept the selected native output directory.

Passed before the full build:

- `python3 tests/test-atlas-recovery.py`: **10 tests**, including independent
  copies, rejected data/code changes, symlinks, mid-copy mutations, stale screen
  exclusion, stable receipt membership and retained/redacted failure logs.
- `python3 tests/test-data-workflow.py`: **40 tests**.
- `node tests/test-screen-output-paths.mjs`: legacy/custom/edition bindings,
  conflict, traversal and source-stem checks.
- JavaScript syntax and `git diff --check`.

Recovery invocation:

```sh
make ASSET_JOBS=2 atlas-optional \
  ATLAS_OPTIONAL_ARGS='--reuse-native-from 20261111t072338z-dd008eb13287'
```

At this initial checkpoint, atlas composition, optional products, full validation
and publication remained to be completed. The execution record below follows
that work through completion.

## Execution record

Replacement run: `20261111t202442z-25a7c5fad7fa`, started **12:24:42 PM PST**.
Its output directory is
`output/data-editions/20261111t043605z-cf34314e91c3/builds/20261111t202442z-25a7c5fad7fa/`.
The complete invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-PST.log`.

The data wrapper revalidated the selected input bytes before starting the
coordinator. Recovery copied and verified all **1,067 files / 7,441,711,943 bytes**.
Prerequisite checks passed. The `all-resilient` stage completed at **12:29:17 PM
PST**, producing all 223 screen PNG/WebP pairs under the new run from the
recovered native parents.

Additional checks on these actual outputs passed:

- JSON Schema validation of the 223-entry catalog.
- Independent Python reader: **223 artifacts / 1,115 files**, hashes and affine
  matrices verified.
- Node consumer check: **223 artifacts, 11 layouts and 14 slices**, parent/output
  hashes, affine round trips, geographic picking and rejection of padding.

The Node check initially could not import an unbuilt projection runtime. The
current C++ runtime was compiled outside the fingerprinted source tree with
`make WEB_BUILD_DIR=build/workflow-v4-runtime wasm-projections`; its unchanged
JavaScript wrapper was copied beside the compiled module. The test now accepts
`SCREEN_RUNTIME_MODULE` for an isolated runtime build, retaining its normal
source-tree default. The successful command was:

```sh
GENERATED_DIR=output/data-editions/20261111t043605z-cf34314e91c3/builds/20261111t202442z-25a7c5fad7fa/native \
SCREEN_RUNTIME_MODULE=build/workflow-v4-runtime/cartofreako-web.mjs \
node tests/test-screen-1080p.mjs
```

The selected atlas catalog contains **39 default identities**, producing
**156 World/Japan map and legend sheets**. The ocean and climate configurations
retain **2025** and **2026 through 9 November**; no new provider acquisition is
part of this rendering task.

### Dense cloud SVG parser failure

The first recovery run composed geometry, graticules, earth and water, then
stopped in the cloud presentation step. Its retained `logs/003-atlas.log`
identifies `settings_for()` in `scripts/setouchi_h3_trials.py`: libxml2 rejected
a path attribute beyond its default 10 MB input limit (`Huge input lookup`).
The generated World and Japan SVGs are 384,287,496 and 384,512,105 bytes.
This was a parser limit, not a failed download or evidence of exhausted RAM.

The settings reader now uses the same large local SVG support as the subsequent
map composer, with entity expansion and external resource loading disabled.
The source geometry, H3 resolution, observation values, paint and viewports are
unchanged. A regression fixture contains attributes larger than 10 MB in both
World and Japan files and checks the resulting styles and Japan viewport.
That test and a read of the actual two dense SVGs passed.

Dependency inspection confirmed this helper is used by atlas/H3/ocean review
presentation, after native generation. It is therefore an explicit additional
post-native recovery exception; native producers and the Make graph still
must match. The recovery suite now has **11 passing tests**, including this
specific exception. The complete cloud rendering step passed in
`build/workflow-v4-cloud-check/`: all seven layers rendered for both World and
Japan, and every linked layer exists. The failed recovery run remains intact,
and no completed-build pointer has been published.

The generation/build guides were also corrected to the current canonical
inventory: **223 standard products, 34 pass IDs and 90 resource masters**.
They distinguish the selected run's `native/` tree from the legacy
`assets.generated/` location. Historical release and frozen benchmark
inventories retain their original counts.

### Second recovery invocation

The same recovery command was started again after the large-SVG check passed.
The new run verifies **316 unchanged native producer files**; the H3
presentation helper is now recorded among the allowed post-native changes.
The invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-2-PST.log`.
Run ID: `20261111t204206z-be3ec8b4682c`, started **12:42:06 PM PST**. This run
was deliberately stopped during screen regeneration after the separate PDF
check exposed the image-decoder restriction below. Its coordinator recorded
the interrupted child stage as failed (exit `-15`) and retained the log. This
was an operator stop for a verified rendering problem, not a new data or
native-generator failure.

### Linked-image decoding and false-success protection

The full cloud PDF check exposed a second problem in the restricted execution
environment: its local socket restrictions prevent D-Bus startup and image
decoding. Inkscape returned zero while reporting `Pixbuf::create_from_file`
errors and omitting linked PNG layers. The same World PDF was only 524,570
bytes with those layers missing, versus 438,024,976 bytes when rendered with
working local D-Bus access. The successful PDF was rasterized and visually
checked: atmospheric observations, white coastlines and the complete map
frame are present.

`scripts/export-setouchi-sheets.py` now checks each export's output for image
decoder failures as well as checking the process exit status. It retains a
redacted export log and fails rather than accepting a PDF/PNG with missing
layers. Ordinary unrelated Inkscape warnings remain nonfatal.
The export fingerprint was advanced to `separate-sheets-v3-checked-image-decoder`
and includes the exporter source hash, so earlier unchecked exports cannot
be accepted from cache after this fix.

The aggregate now runs a functional linked-image preflight after its normal
prerequisite check and before the expensive rendering stages. It renders a
small SVG referencing a known PNG and verifies the exported dimensions and
actual center pixel. Probe files are retained under `validation/image-decoder/`.
The standalone command is:

```sh
python3 scripts/export-setouchi-sheets.py \
  --delivery build/workflow-v4-decoder-probe --check-image-decoder
```

The real probe passes with normal local D-Bus access. The unattended build is
therefore being run through the authorized host execution path. This does
not require provider downloads or a change to the selected dataset.

`tests/test-atlas-export.py` adds four passing checks: zero-exit decoder errors
are rejected, unrelated warnings are retained, nonzero exits still fail, and
private environment values are redacted. Together with the 40 workflow, 11
recovery and one dense-SVG tests, **56 Python regression tests pass** after
these changes. The sheet exporter is an explicit additional post-native
recovery exception; the new run still verifies **315 unchanged producer files**.

### Third recovery invocation

The same recovery command was started with the verified local D-Bus access.
Its invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-3-PST.log`.
Run ID: `20261111t204739z-e3f6a8acd94b`, started **12:47:39 PM PST**. Its image
decoder preflight passed. It was stopped cleanly at **12:49:29 PM PST** while
regenerating screens, to include the visual correction below in one consistent
implementation record.

### Cloud annotation contrast

Rasterized PDF review found that the Japan cloud sheet inherited amber text
from the dark-page theme, then changed its background to the same amber.
That made its header, source dates and explanatory notes invisible. The
compositor now paints cloud annotations in the atlas's dark ink (`#240413`),
while retaining the amber page, observation colors, white coastlines, geometry
and source-date text. Both SVG attributes and overriding CSS are updated.

The corrected Japan PDF was regenerated with working image decoding and
rasterized for review. Its header, per-layer source periods and notes are now
legible. The regression test verifies text/tspan paint, retained opacity, and
unchanged observation paths/linked-image definitions. The dense-SVG suite now
has two tests; the combined Python regression total is **57 passing tests**.

The atlas compositor is explicitly allowed to change during native recovery,
because all atlas sheets are rebuilt. The final recovery precheck verifies
**314 unchanged native producer files** and records all nine allowed changed
post-native/independent files by name.

### Fourth recovery invocation

The recovery command was restarted with all fixes and the verified local
image-decoder access. Its invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-4-PST.log`.
Run ID: `20261111t205358z-51683d859ab7`, started **12:53:58 PM PST**. Input
verification read the complete selected snapshot before the coordinator began.
Recovery copied and verified the 1,067 native files again; the normal
prerequisites and actual linked-image pixel probe passed. The run reached
`all-resilient` at **12:54:18 PM PST** and completed it at **12:58:27 PM PST**.
The schema, Python reader and Node geographic-picking checks passed again on
this run's actual 223-entry screen catalog and 1,115 linked files.

The corrected cloud step completed, followed by the network, Anthropocene,
astronomy, orbital and first four resource subjects. After **23 of 39** atlas
subjects, composition stopped at a stale food-production source name. Its
failure is retained in `logs/004-atlas.log`; no completed-build pointer was
published.

### Resource source names and reference periods

Checking the entire remaining catalog found three outdated source stems:

| Frozen catalog source stem | Actual native source | Reference period |
| --- | --- | --- |
| `resources-food-food-production-index-latest-2024` | `resources-food-food-production-index-2022` | 2022 |
| `resources-flora-forest-area-percent-2024` | `resources-flora-forest-area-percent-2023` | 2023 |
| `resources-fauna-coral-reef-threat-2011` | `anthropocene-coral-reef-threat-2011` | Reefs at Risk Revisited 2011 |

The compositor now resolves released resource filenames from the selected
edition's metric profile, including its actual `output_tag` and
`reference_period`, and uses the same reef namespace as the native generator.
Exact released tags take precedence; an unknown, unreleased or ambiguous
selection fails. It does not guess a nearby file or relabel 2022/2023 data as
2024. Frozen catalog IDs remain stable identifiers; they are not evidence of
an observation year. Map metadata, native legends and the composition receipt
retain the actual reference period. The dataset manifest remains unchanged.

Before composing any atlas subject, the builder now checks every required
native source and writes `sources/native-source-selection.json`, recording
the selected filenames, hashes, catalog names, actual periods and resource
profile hash. All **34 native-backed selections** pass on the saved files;
the remaining **five atlas-only subjects** are generated directly.

Six additional regression tests cover dated food/forest aliases, a different
snapshot year without hardcoded replacement years, reef naming, rejected
unreleased/missing/ambiguous metrics, and exact-tag precedence. The 40 workflow
tests also pass after this change; the combined Python regression total is
now **63**. The remaining 16 subjects composed successfully as **64 map and
legend sheets** under
`output/data-editions/20261111t043605z-cf34314e91c3/checks/workflow-v4-remaining/`
before the next full run. Sixteen representative food, forest, reef and mineral
comparison sheets also passed real PDF/PNG export, dimensions and margins.
The actual food and forest map metadata and visible legends identify 2022
and 2023 respectively.

### Resource legend panel contrast

PDF inspection found another inherited theme mismatch: native resource legends
retain an explicitly identified white `resource-legend-panel`, while the atlas
theme changes their text to amber. The current-atlas compositor now applies the
selected page color to that panel in maps and separate legends. It streams the
same theme adapter as before and changes only this unmeasured panel, preserving
resource swatches, metric values, geometry and source-period text. The shared
native-generation implementation is unchanged.

The presentation suite passes **eight tests**, including the new panel check
for both map and legend contexts; the combined relevant Python total is
**71 tests**. The actual corrected food-production subject was recomposed and
exported as four World/Japan map/legend sheets under
`output/data-editions/20261111t043605z-cf34314e91c3/checks/workflow-v4-resource-panel/`.
All exports pass. Rasterized PDF review confirms readable amber type on wine
paper and unchanged data swatches.

### Fifth recovery invocation

The aggregate was restarted with the complete set of fixes and the verified
local image-decoder access. Its invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-5-PST.log`.
The native recovery comparison still verifies **314 unchanged producer files**;
all additional repairs are within the recorded post-native compositor.
Run ID: `20261111t212705z-cf0ad156b69b`, started **1:27:05 PM PST**. Native
recovery, prerequisites and the linked-image pixel probe passed; screen
generation began at **1:27:26 PM PST**.
`all-resilient` completed at **1:31:32 PM PST**. Both independent screen
readers passed on this run: 223 artifacts / 1,115 files, hashes, affine
matrices, geographic picking and no-crop checks. The full 34-source atlas
preflight also passed before composition started.

All 39 subjects composed as 156 sheets. **155 sheets passed export**, but the
World all-sky map stopped the aggregate at **2:02:09 PM PST**. No completed-build
pointer was published. The failure and all produced sheets remain in the run.

### Declared all-sky margins and prompt export failures

The all-sky SVG declares a side margin of **0.1515254408298148 inches**, inherited
from the approved World layout's halved side margins. The exporter instead
checked a hardcoded 74-pixel band (approximately one quarter inch at 300 dpi),
which included legitimate glyphs starting at pixel 45. The rendered page was
intact; the assertion was checking outside its declared clear margin.

The exporter now reads the declared physical margin, rounds inward and leaves
one additional pixel clear of the antialiased boundary. This sheet therefore
checks 44-pixel side bands. Ordinary sheets retain the established 74-pixel
side and 31-pixel top/bottom bands. Invalid, nonfinite or untestably narrow
declared margins fail explicitly; the background-pixel check remains mandatory.

Export scheduling now submits only as many sheets as there are workers. A
failure identifies its sheet immediately, cancels pending work and waits only
for exports already running. Previously, the executor waited for all queued
sheets before displaying the assertion. The exporter fingerprint includes the
new implementation, so older receipts cannot pass as newly validated exports.

The exporter suite now has **nine passing tests**, including the actual
all-sky margin geometry, rejection of a pixel inside the clear margin, invalid
declarations and cancellation of the remaining queue. Four World/Japan
all-sky map/legend sheets passed real PDF/PNG export under
`checks/workflow-v4-all-sky-margin/atlas`; both existing full-size all-sky PNGs
also pass the corrected margin check.

### Marine-heatwave cutoff shadowing

Review of the still-pending optional stages found a second deterministic
runtime error before the next aggregate run: `prepare-marine-heatwaves.py`
used `cutoff` both as the imported date function and a loop variable. Python
therefore treated it as an uninitialized local at the initial `cutoff()` call;
the later comparison label also attempted to call the loop's date value.
The loop variable is now `period_end`, leaving the selected cutoff function
available throughout preparation.

A complete one-cell command fixture exercises the real event kernel, ledgers,
product files and monthly comparison through November 9. It verifies 365 days
for full-year 2025 and 313 days for both matched 2025 and 2026 YTD. All **13
Stage 2 tests pass**, including this new command-level regression. The overall
relevant Python total is **89 tests**. Marine preparation runs only after the
native and atlas stages, so it is now an explicit post-native recovery
exception; none of its old optional output is reused. All native producer
bytes are still checked.

### Sixth recovery invocation

The same complete recovery command is running with the all-sky margin and
marine cutoff fixes. The invocation log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-6-PST.log`.
Its precheck verifies **313 unchanged producer files**, with ten explicitly
recorded post-native/independent changes. The combined **89 Python tests** and
screen-path Node checks pass. Rasterized PDF review also confirms the corrected
World all-sky export retains its complete map within the declared margins.
Run ID: `20261111t221444z-97ebad9f3d84`, started **2:14:44 PM PST**, after the
wrapper reverified the immutable input files. The ocean product metadata also
confirms the selected November 11 snapshot and the intended 365/313-day windows.
Native recovery and both prerequisites passed. `all-resilient` ran from
**2:15:05 to 2:19:11 PM PST**. Independent Python and Node checks passed on this
run's 223 screen products, 1,115 linked files, hashes, affine/geographic picking
and no-crop checks. Atlas composition is proceeding from these verified outputs.
All 39 subjects completed composition by **2:32 PM PST**, including the dense
clouds and all corrected resource selections. The run then began the complete
156-sheet export pass with the declared-margin checks.
The World all-sky export passed in 4.82 seconds, including the corrected
margin check. All **156 sheets** passed `check-current-build.py --atlas` by
**2:50 PM PST**. No image-decoder or margin failure was reported. The coordinator
then entered World, Japan and combined PDF book assembly.
The atlas stage passed at **2:51:30 PM PST**. Its books contain **80 World
pages**, **80 Japan pages** and **158 combined pages**, with 78/78/156 exported
sheets plus two front-matter pages per book. `current-books.json` records their
hashes and source-PDF hashes. World PDF cover/contents and the complete contact
sheet were visually reviewed; the contents fit and all 39 subjects are present.
Ocean period comparisons, JMA/OISST comparisons and scientific figures passed
by **2:52:27 PM PST**, when full Stage 1 ocean plate rendering began.
All **nine ocean measure/period products / 36 World/Japan map and legend
sheets** completed. These cover SST/coral heat stress, anomaly and record days
for 2025 full year, 2026 YTD and matched 2025. The actual SST PDF and legend were
rasterized and reviewed: linked data layers, coral outlines, keys, source notes
and the full-year date label are present and legible.
Full ocean validation passed before **3:04 PM PST**, including 90 native grids,
32 independently recomputed cell-periods and all 36 exported sheets.
The next stage began computing the 1991–2020 climate baseline for **596,710
occupied ocean H3 cells** from the immutable edition's stored arrays.
Baseline calculation completed in **750.7 seconds**, with all 596,710 cells
processed and the combined arrays written. Marine-heatwave preparation began
by **3:17 PM PST** and passed the formerly shadowed `cutoff()` call on the actual
full dataset. A mid-run identity check also confirmed all **323 implementation
file hashes** still match the run's original record after helper compilation.
Marine preparation completed all three periods, followed by both thermal-season
years and coastal compound-heat preparation. The India join completed with
**25 monitors / 13,558 audited source station-days**. Stage 2's comparison figures
also completed, and the full preparation target passed at **3:25:06 PM PST**.
The coordinator then began the climate plate render and validation target.
The selected registry requires **32 measure/period views / 128 map-and-legend
sheets**: 36 marine-heatwave, 32 thermal-season, 24 coastal-compound-heat and
36 India heat/particulate-coexposure sheets. The first three families use World
and Japan views; coexposure uses World and India views.

### Optional regional annotations

Visual review of the India PDF found that the map's geography and observation
layers were correct, but the borrowed Japan frame retained its visible
`JAPAN / ANTHROPOCENE LAND TEMPERATURE 2026` heading, Japan sidebar and the native
land record-high legend. The same template problem affected optional Japan
ocean/climate maps. Existing validators checked arrays, links and hashes but
did not check the visible frame annotations against the product metadata.

The coordinator's render child was stopped at **3:41:33 PM PST**, leaving the
sixth run failed with exit `-15`. Its files and state remain retained; nothing
was published as a completed build. At that point 125 climate PDFs and 123
complete export receipts were present.

The shared optional-map annotation helper now replaces the borrowed regional
heading and sidebar with the actual region, measure, year and reporting window.
It removes the inherited land-temperature legend and links to the correct
companion source/legend sheet. The India viewport supplies its display region
explicitly instead of inheriting the Japan template's name. World map geometry,
regional viewports, observation values and paint are unchanged.

Both ocean validators now compare map titles, region, cutoff, visible regional
heading, period label and companion link with the corresponding product
metadata, and reject the stale template groups. Six regression tests cover
Japan and India, full-year/matched/YTD/season labels, retained geometry, stale
captions and the shared frame integration. The combined Python total is now
**95 passing tests**, plus the screen-path Node checks.

Seven actual corrected regional frames were exported under
`checks/workflow-v4-optional-labels/`: Japan SST, matched record days, marine
events, thermal season and coastal heat, plus India joint-day and fraction
views. All pass. Rasterized India and Japan SST PDFs show the correct titles,
periods, regional notes and companion links; the obsolete land-temperature
legend is absent.

Parallel checks also exposed that `setouchi_h3_trials.render_svg()` launched
Inkscape directly, unlike the sheet exporters. The functional decoder probe
passed, but simultaneous direct helper exports collided on D-Bus. This helper
now uses the existing per-invocation `run-inkscape.sh` isolation wrapper.
All seven parallel regional exports pass with that change.

### Independent scientific review before the next run

The sixth run's completed scientific products were checked read-only, without
altering that failed run or accepting its incomplete/mislabeled exports:

- 15,171 source files verified by hash.
- 20 independently calculated ocean calendar baselines and 60 cell-periods.
- 5,098,859 marine-event ledger rows reconciled to product totals.
- 40 independent thermal-season cell-years.
- 8,993 coastal pairs, 110,119 line-of-sight memberships, 16 independent
  pair-years and eight land/ocean baseline checks.
- 25 India monitors, 13,558 station-days, 848 station-month coverage rows,
  14 independent hourly-source checks and 3,809 matched station-days.

Every check passed. The retained check log is
`.cartofreako/data/operator-logs/cartofreako-v4-science-check.log`.

### Seventh recovery invocation and cache candidates

The same complete `--reuse-native-from 20261111t072338z-dd008eb13287` command
is running with the annotation and isolated-helper fixes. Its log is
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-7-PST.log`.
The precheck verifies **309 unchanged native producer files**, with 15
explicitly recorded post-native/independent changes.

To avoid repeating unchanged work, the new run is also receiving genuine cache
candidates from the sixth run: atlas PDF/PNG/preview exports and their original
receipts, plus climate-baseline chunks and their original input/hash receipts.
Files are copied into independent files and hashed before/after copying. Dataset
identity, unchanged baseline producers, baseline input keys and source state
stability are checked. No completed-group validation or build pointer is copied.
Normal composition, sheet export and baseline commands still check their own
input keys and output hashes, rejecting or replacing stale candidates. The
new run retains the exact copying procedure, source state hash and candidate
file hashes in `sources/reused-render-caches.json`.
Run ID: **`20261111t235701z-b2ab91c31265`**, started **3:57:01 PM PST**.
Cache recovery copied **156 atlas export entries and 146 baseline chunks**:
916 independent files / 2,817,494,577 bytes, with unchanged source state.
The native recovery, prerequisites and functional image-decoder probe passed;
screen regeneration is running. Copied export receipts are candidates until
this run's exporter checks the freshly composed SVGs against them.
All 223 screen products and both independent readers passed. The atlas was
composed afresh as 39 subjects; **all 156 exports matched the saved cache keys
and file hashes** and were accepted by the normal exporter. The current-atlas
validator passed by **4:15 PM PST**, followed by fresh book assembly. This
retained normal source/export validation while avoiding another full raster
and PDF export pass.

### World title creation and eighth-run preflight

The seventh run completed all 36 Stage 1 sheets, then failed the new annotation
check at **4:27:55 PM PST**. All nine World maps had no root SVG title; their
parent template stores a source-cartography title inside `defs`. The helper
previously replaced existing root titles only. Regional templates have root
titles, so the seven regional PDF checks did not expose this case.

`optional_map_annotations.py` now creates a missing root title, normalizes
duplicate root titles, and relabels the source-cartography title while keeping
the Natural Earth basemap title. The validator still requires exactly one
correct root title. Three added regressions cover the missing-title World
template, duplicate-title normalization and preservation of the basemap title.
The annotation test file now has nine passing tests.

Preflight now includes every actual optional map frame: 18 Stage 1 maps and
64 Stage 2 maps, with the correct measure/period metadata and linked-image
checks. Actual PDF checks add World SST and World marine heatwave maps to
the seven regional cases. Failed output receipts and run identities are not
rewritten; the correction will be recorded by a new build run.

All 82 frame checks passed: 18 ocean maps and 64 climate maps. The stopped sixth
run had saved 63 climate SVGs; the check constructed the remaining view from
its complete metadata, tiles and the actual atlas template. No failed output
was modified. Nine real World/Japan/India PDF exports passed, as did all
98 Python regression tests and the Node screen-path checks. Logs:
`.cartofreako/data/operator-logs/cartofreako-v4-title-regression.log` and
`.cartofreako/data/operator-logs/cartofreako-v4-optional-labels-check-2.log`.

The eighth full invocation uses the same native recovery command, with log
`.cartofreako/data/operator-logs/atlas-recovery-20261111-attempt-8-PST.log`.
It receives the same independently verified cache candidates from the sixth
run; normal atlas and baseline commands must validate them before reuse.

Eighth run ID: **`20261112t003745z-8638649d869b`**, started November 11 at
**4:37:45 PM PST**. Native recovery, prerequisites and the functional image
probe passed. Cache recovery again copied 916 independent files /
2,817,494,577 bytes, with source state and source files unchanged.

During the eighth run, shared Alpha60 header
`/home/bkoz/src/alpha60/src/a60-svg-cumulative-country.h` changed at
**4:39:59 PM PST**, after this build began. Make detected the dependency and
rebuilt the native swarm adapter, then its dependent maps. All 324 recorded
Cartofreako implementation files still matched the run identity. The complete
resilient graph remains responsible for rebuilding affected native outputs;
normal atlas cache checks use the resulting fresh SVG hashes. An additional
read-only observation of external Alpha60/izzi source hashes is retained in
`sources/external-renderer-observation.json` for a completion-time comparison;
it does not claim those external sources were pinned at run start.

The original native swarm receipts show roughly 8–11 minutes between completed
projections. Recompiling its shared dependency invalidated the binary-keyed
raw render cache, so all six projection variants require fresh rendering.
At 4:50 PM PST the first renderer was active on one CPU core with approximately
11.8 GB of reads and 4.0 GiB resident memory; this was ongoing computation,
not a provider retry. No new data acquisition is involved.

At **4:55 PM PST**, the regenerated Cahill–Keyes swarm SVGs (both partitions
and the existing high-resolution alias) were checked against the original
failed run and were byte-for-byte identical. AuthaGraph was rendering next.
The original ten-minute screen-reader watcher expired while waiting for the
expanded native stage; it was requeued with a three-hour wait. That operator
watcher does not control the build or mark a stage failed. Both readers will
run only after the full `all-resilient` stage passes.

To overlap independent work, a separate operator invocation was launched for
Star-X and Voronoi raw swarm rendering while the main Make continued Dymaxion.
It runs the unchanged `generate-native-swarm.py` with the selected manifest,
cache documents, geolocation database and binary in separate work directories.
Only the resulting raw SVGs and original input markers are eligible for reuse;
no final native map or completed validation is copied into the run. Transfer
waits for the producer's shared render lock, compares the complete input
signature with the freshly rebuilt Cahill–Keyes signature (apart from projection),
and independently hashes every copied file. Main Make still checks the normal
signature and composes/exports the final native maps. The exact operator script,
commands and copy hashes are retained in `sources/native-prefetch.json`.

By **5:20 PM PST**, Myriahedral had finished and both parallel raw caches
were copied under the shared render lock. Star-X and Voronoi had each passed
the normal producer's raw render and SVG composition in their separate work
directories. The run now retains `sources/native-prefetch.json` with the exact
operator procedure, original input markers and hashes for all six transferred
files. Normal Make proceeded to consume those cache candidates and finish
its native maps and derivatives.

Four later low-resolution swarm PDF/PNG pairs (Dymaxion, Myriahedral, Star-X
and Voronoi) were also exported in separate scratch directories with the
unchanged normal exporter and Make's 3840-pixel setting. Each retains every
native circle and must match the source hash, expected circle count, PDF
header and PNG dimensions. Fresh outputs may be installed only while the
serial Make is still in its earlier high-resolution group, with unchanged
and inactive destinations. Otherwise the candidate is left unused. This
uses newly rendered bytes and their genuine export receipts, without changing
source timestamps or inventing cache-validation records. The exact commands,
procedure and installed hashes are recorded in `sources/native-export-prefetch.json`.

By **5:31 PM PST**, all four parallel native PDF/PNG exports passed and were
installed while main Make was still processing its earlier high-resolution
projections. Their genuine export receipts and 12 file hashes are retained in
`sources/native-export-prefetch.json`. The main build continued with Myriahedral;
its normal dependency checks skipped the already current later targets.

The complete native `all-resilient` stage passed by **5:42 PM PST** and the
coordinator started atlas composition. A post-native check confirmed all
171 observed external source hashes remain unchanged, all six swarm
provenances name the same current renderer binary, and all 12 installed
parallel export files retain their original verified hashes. The final
223-product screen catalog was then checked by both independent readers.

The two independent screen readers both passed the final catalog: 223 products,
1,115 parent/output files, 11 layouts and 14 slices, with affine/geographic
picking, lossless output, hashes and no-crop checks. Their logs are
`.cartofreako/data/operator-logs/atlas-recovery-attempt-8-screen-python.log` and
`atlas-recovery-attempt-8-screen-node.log` in the same directory.

The atlas stage passed by **5:57 PM PST**: all 39 subjects were composed afresh,
all 156 export candidates matched the normal cache keys and file hashes, and
all three books were assembled (World 80 pages, Japan 80 pages, combined 158
pages). The coordinator proceeded to full ocean comparisons, figures and
optional map rendering. No optional ocean/climate PDF from a failed run was
reused.

Full Stage 1 ocean validation passed by **6:10 PM PST**: 90 native grids,
32 independently recomputed cell-periods and all 36 exported sheets. This
includes the World-title and regional-annotation checks that stopped the
seventh run. Stage 2 preparation then began.

The normal baseline producer accepted all 146 saved chunks after checking
its current input keys and each chunk hash; it recomputed zero chunks and
assembled fresh arrays for all 596,710 ocean cells. The new baseline metadata
and all four recorded array hashes exactly match the independently reviewed
sixth-run baseline. Marine-event preparation followed immediately.

Stage 2 preparation passed by **6:20 PM PST**, completing all marine-event
periods, both thermal-season years, coastal support, the India monitor join
and four scientific figures. The coordinator then started the complete
128-sheet climate render and validation target with the corrected annotations.

## Completion and independent acceptance

All 128 Stage 2 sheets finished, and full climate validation passed at
**6:38:28 PM PST**. The coordinator published the complete run at
**6:39:03 PM PST**, after hashing the artifacts and checking that implementation
identity had not changed. The invocation exited successfully. The full-build
receipt SHA-256 is:

```text
3caf087330c79f2f668c9a48c9f833f445aae1fee65be21c908ebd2c29057d4b
```

The independent acceptance script then re-read the published pointer and
receipt, checked every one of the 4,054 artifact hashes, verified all 324
implementation files, and used `pdfinfo` to confirm the three book page counts.
It also checked all 34 native atlas selections, original failed-run evidence,
all 171 observed external source hashes, six matching native renderer receipts,
two independently prepared raw swarm caches and four parallel PDF/PNG pairs.
All checks passed. The run retains its real pre-commit revision and dirty-tree
identity; committing the finished code does not rewrite historical receipts.

Full climate validation verified 15,171 source files, 20 independent calendar
baselines, 60 cell-periods, 5,098,859 reconciled marine-event rows, 40
thermal-season cell-years, 8,993 coastal pairs, 110,119 line-of-sight memberships,
16 independently checked pair-years, eight land/ocean baselines, 25 monitors,
13,558 station-days, 848 station-month coverage rows and 3,809 matched
station-days. It checked all 128 exported sheets, four scientific figures and
455 index links. Both ocean and climate validation have `data_only: false`.

The production Stage 2 unit invocation ran 13 tests: 12 passed and one optional
integration comparison was skipped because the dataset-bound output does not
contain `research/marineHeatWaves.py`. That comparison had passed earlier in
the standalone 13-test invocation, where the local reference was available.
The current run's independent numerical and source-data validation completed
in full. The final India PDF was also rasterized and visually checked: region,
measure, 2025 interval, notes and legend link are correct; the inherited Japan
heading and land-temperature legend are absent.

The completed output root is:

```text
output/data-editions/20261111t043605z-cf34314e91c3/builds/20261112t003745z-8638649d869b/
```

Its principal deliveries and records are:

- `native/catalog/artifacts-v1.json` and the projection-specific native exports.
- `atlas/atlas-world.pdf`, `atlas/atlas-japan.pdf`, `atlas/atlas-combined.pdf`.
- `anthropocene-optional/ocean/index.html` and its 36 map/legend sheets.
- `anthropocene-optional/climate/index.html` and its 128 map/legend sheets.
- `validation/full-build.json`, `validation/build-state.json` and retained stage logs.
- `sources/reused-render-caches.json`, `sources/native-prefetch.json`,
  `sources/native-export-prefetch.json` and `sources/external-renderer-observation.json`.

Operator acceptance evidence is retained at
`.cartofreako/data/operator-logs/atlas-recovery-attempt-8-final-verification.json`;
the exact verifier is `cartofreako-v4-verify-build.py` in the same directory.
The generation and build guides now cover supported native recovery, strict
resume identity, image-decoder preflight, declared margins, source-period
resolution, optional-map annotation checks, current product counts and the
shared native-source dependency behavior observed during this run.

## Legend and delivery-layout refinement — 11 November 2026

### User review and approved requirements

After reviewing the completed atlas, the user reported inconsistent legend
typography, especially for Network CDN, Network Fiber, both Network Swarm
plates and Anthropocene particulate. Atmosphere and Water provide the
reference for a coherent companion-sheet treatment. The later requirements in
[`20261109_starlink_star_light_v3.md`](20261109_starlink_star_light_v3.md)
also apply throughout the atlas:

- Use **landscape A3, 420 × 297 mm**, for legend plates.
- Reverse the accepted randoma11y wine/amber pair on legends: **amber
  `#fcc553` background and wine `#240413` text**. Preserve measured and
  categorical symbol colors, class boundaries, units and source dates.
- Use consistent physical typography from v3: **27 pt titles, 15 pt section
  headings, 12 pt observer notes, 11 pt body text and 10.5 pt sources**,
  with the bundled Atkinson Hyperlegible fonts. Reflow content into the page;
  do not enlarge a native map legend as one graphic.
- Include four clearly identified sections: **Legend**, **Data sources**,
  **Observer note**, and **How to read this plate**. Observer notes must
  distinguish projected geographic views from celestial views and explain
  what World, Japan and India scopes actually mean for the relevant product.
- Audit the bibliography for **every plate**, including Water, whose current
  companion omits it. Each legend must identify its actual providers,
  datasets/releases, applicable reference periods and citations. Resolve
  these from the bound source profiles and recorded inputs; a generic
  dataset-manifest pointer does not constitute a plate bibliography.
- Regenerate the affected legend exports and the World, Japan and combined
  atlas books using the completed dataset and existing cartographic sheets.
- Present completed deliveries at **`output/data-edition/20261111/atlas/`**
  and **`output/data-edition/20261111/anthropocene-optional/`**. The singular
  `data-edition` and compact date are intentional. Dataset and build IDs
  remain in provenance records and internal working storage.

The user explicitly requested this refinement and its documentation; no
additional design approval is pending. This subsection records the plan
before implementation. The successful build described above remains the
baseline and is not evidence that this refinement has already been rendered.

### Diagnosis

The current builder has multiple legend paths. The four approved Star Light
World legends already use A3; most other subjects still use a 44-inch sheet.
The native-legend fallback fits an entire extracted group by its bounds,
retaining incompatible source font sizes and fonts. Some native labels even
carry fractional `pt` sizes inside transformed coordinates. This produces
very different effective typography from the Atmosphere/Water compositor.
The native fallback also retains opaque legend panels and the map's dark
page theme. Japan groundstations have a separate wide-sheet implementation.
The existing validator checks files and hashes but does not enforce the
physical legend page size, shared type scale or required explanatory sections.

### Implementation and regeneration plan

1. Consolidate legend layout around the A3 design. Reflow source-derived
   keys and text at explicit physical sizes, retaining symbol geometry and
   data colors. Add the four named sections and scope-specific observer text;
   keep source periods and limitations attached to the correct products.
   Audit the plate-to-source mapping and bibliography against the selected
   dataset, including geographic basemaps, astronomy, networks and every
   resource metric. Do not copy obsolete dates from a retained edition.
2. Apply the same companion-sheet requirements to the optional ocean and
   climate legends. Keep their scientific products, map exports and source
   observations unchanged; verify that regeneration preserves their keys,
   thresholds, coverage notes and citations.
3. Add a supported legends-only refresh for a verified completed build.
   Retain the previous successful receipt, reuse unchanged maps and data,
   record the new legend implementation and exports, and reassemble all
   three atlas books. Avoid new provider acquisition or recomputing native
   swarm, ocean or climate analyses for a typography change.
4. Publish the verified result under the requested date-based delivery path.
   Keep incomplete work and historical build identities internal, and switch
   the visible delivery only after validation. Preserve existing evidence
   and compatibility with recorded older build paths.
5. Verify A3 dimensions, the reversed palette, physical font sizes, all four
   section labels, symbol/label conservation, source and map hashes, links
   and book page order/counts. Rasterize representative PDFs, including CDN,
   Fiber, Swarm, particulate, Atmosphere, Water, groundstations and optional
   climate products, and inspect for clipping, overlap and readability.
6. Record the actual changes, checks, resulting delivery paths and any
   limitations here, and update the build/generation guidance to match the
   supported refresh command and simplified output layout.

### Implemented refinement and source audit

The shared `atlas_legends.py` compositor now reflows source keys and prose
onto landscape A3. Native font transforms and opaque inherited panels no
longer determine the companion typography. Keys retain their original class
labels and categorical paints; the four accepted Star Light World sheets
retain their approved symbols and reading notes. Japan groundstations now
uses the same A3 layout. Atlas and optional validators check physical page
dimensions, the reversed palette, type sizes, section labels and text bounds.

`atlas_bibliography.py` resolves a bibliography for every default subject.
Water now identifies Natural Earth 5.1.1's physical layers and has a twelve-step
bathymetry key sampled from the actual native layer paints. Projection geometry
and graticules are identified as calculated coordinates rather than observations.
Resource citations use each selected metric's actual reference period and
provider release. Atmosphere cites the separate JAXA products and their actual
observation intervals. Network CDN includes a readable source appendix with
the input-layer references and the complete retained 365-reference provider
bibliography, explicitly distinguishing supporting context from plotted inputs.
Fiber gains status-stroke keys; both Swarm legends gain representative swatches
from their actual source palettes, with the map's 5% opacity explained.

Two interpretation corrections accompany the bibliography audit. The Japan
ground-observer astronomy and orbital views are calculated from **Setouchi,
34.45°N / 133.99°E**; they must not be described as San Francisco views with a
Japan locator. The Hubble companion remains a spacecraft view. India's
heat–particulate co-exposure uses CPC and OpenAQ observations; OISST is not
listed as an input to that family. Geographic context is cited separately.

The particulate audit found a stale source-profile label: NASA FIRMS remains
marked `configured-optional`, although the prepared data includes **18,466,569
FIRMS rows across 365 days in 2025**, and **16,866,048 rows across 314 days in
2026, through 10 November**. Bibliography inclusion now follows the prepared
source statistics and detection dates. Both particulate legends explicitly
cite NASA FIRMS without exposing acquisition credentials. The immutable data
and profiles are retained unchanged; this fixes their presentation and citation.

The particulate profiles also retain old `available_through` configuration
hints. The preparer does not refresh these hints, so they are no longer printed
as measured source cutoffs. The legends identify the observation year and
provider-specific coverage; FIRMS dates come from the ingested date list.
Groundstations includes the supplied KML filename and the actual FCC and
Ofcom references used for capability interpretation, with their limits stated.
All optional ocean and climate legends also cite the selected Natural Earth
release for their geographic context. Repeated refreshes replace the prior
source column instead of accumulating duplicate text.

The supported refresh is:

```sh
make atlas-optional ASSET_JOBS=4 ATLAS_OPTIONAL_ARGS='--refresh-legends'
```

It verifies the selected dataset and completed parent artifacts, checks the
unchanged scientific producer fingerprints, refreshes **78 atlas legends and
82 optional legends**, reuses maps and numerical products, reassembles the
three books, and checks the exports. Mutable legend files, metadata and
frontmatter have independent copies; unchanged large maps/native/data files
are shared locally and checked against the retained parent. A failed refresh
must be restarted with `--refresh-legends`, rather than resumed as a native
rebuild. This prevents a native command from rewriting shared accepted maps.

Completed deliveries are published by an atomic date-directory link at
`output/data-edition/20261111/`. Private work and run identities are retained
under `.cartofreako/data/render-runs/`; previous output paths remain usable as
historical evidence. The climate method document is bundled in its delivery,
so its link does not depend on the private directory depth. The full-build
pointer records both the public path and internal storage path.

The first refinement run, `20261112t054624z-b77ab7bad8d4`, rendered the sheets
and passed the export checks. It was **not published**: the FIRMS source audit
and portable-method-link fix changed the implementation before final sealing,
and the existing implementation-identity guard rejected publication. Its
failed state is retained. The second run, `20261112t055430z-ab5505442cfd`,
likewise remained unpublished while the final source-date audit changed the
implementation. Both runs passed their export validations and preserved the
original completed delivery. The final run starts from that original verified
atlas with the completed citation corrections.

### Completed refinement delivery

The final refresh, **`20261112t060251z-217cedb60b4f`**, passed all three
export validations and published at **10:07:25 PM PST on 11 November 2026**.
It uses the same frozen dataset, `20261111t043605z-cf34314e91c3`.

The visible delivery is now:

```text
output/data-edition/20261111/
  atlas/index.html
  atlas/atlas-world.pdf                     80 pages
  atlas/atlas-japan.pdf                     80 pages
  atlas/atlas-combined.pdf                 158 pages
  atlas/sources/plate-bibliography.html
  anthropocene-optional/ocean/index.html
  anthropocene-optional/climate/index.html
  validation/full-build.json
```

All **160 distinct SVG/PDF legend pairs** use A3: **78 atlas**, **18 ocean**
and **64 climate**. The atlas bibliography covers all **39 subjects**. The
new full receipt contains **4,059 artifacts** and **327 implementation-file
fingerprints**. Its SHA-256 is
`b6825d735556fd2994fd8c8b18f68aaa07dc0120d02782bd67f2f95d7ebd08be`.
All **4,054 parent artifacts remain unchanged**; the new delivery reuses
**3,404 unchanged artifacts**, including **490 map artifacts**. Map generation,
scientific calculations and provider acquisition were not rerun.

Validation included **82 focused tests**: 14 legend/delivery regressions,
11 recovery, 8 presentation, 9 export and 40 data-workflow tests. All 15
modified Python modules compile; `git diff --check` passes. The three changed
documentation files pass their local-link check (132 links).

Twelve representative PDFs were rasterized and visually inspected: Water,
Atmosphere, CDN, Fiber, Swarm, particulate, all-sky astronomy, Japan
groundstations, ocean SST/coral exposure, marine heatwaves, Japan coastal
compound heat and India heat–particulate co-exposure. Their source columns,
keys and explanatory sections fit the A3 page without clipped or overlapping
text. Review images and the review record are retained in
`.cartofreako/data/operator-logs/atlas-a3-legend-review/`.

The accepted build log is
`.cartofreako/data/operator-logs/atlas-a3-legend-refresh-accepted-20261111.log`.

A separate verification pass checked all **4,059 artifact hashes**, all
**160 single-page A3 PDFs and their SVG typography**, and all **39 nonempty
plate bibliographies**. It confirmed the hashes of **2,064 map/native/data
files** against the original receipt, unchanged book input ordering, the
**80 / 80 / 158** page counts, and A3 dimensions at every legend page inside
each book. It also resolved **1,060 local links** through the public date path
using browser URL normalization, including the bundled climate method note.
The result is recorded in
`.cartofreako/data/operator-logs/atlas-a3-legend-final-verification.json` and
`.cartofreako/data/operator-logs/atlas-a3-independent-verification.log`;
the verifier is retained with the visual-review artifacts.

## Legend and network-map corrections — 12 November 2026

The follow-up audit found that **140 of the 160 legends** repeated the same
geographic Observer Note, with only World, Japan or India substituted. The
remaining sheets used network or astronomy variants. At the user's request,
the section is removed from every current atlas, ocean and climate legend,
including the retained SLSL layouts. Reading guidance moves to the top of its
column; symbols, bibliography and physical type are retained. Refreshing an
older serialized legend model discards its observer paragraph, and the
validator rejects the removed section.

The user's page references identify Network fiber on page 15 and Network
groundstations on page 17 in the World and Japan books. Submarine cable
routes and landing points now use the selected dyad's light member (amber
`#fcc553`); green terrestrial routes, geometry, line widths and status dashes
are retained. Matching amber legend keys have a dark outline so they remain
visible on the reversed legend paper. The groundstation World map had a
native light ocean rectangle above its dark sheet paper; that rectangle now
uses the dark member (wine `#240413`). The same presentation corrections apply
to both geographic editions and their combined book inputs.

The supported selective refresh is:

```sh
make atlas-optional ASSET_JOBS=4 \
  ATLAS_OPTIONAL_ARGS='--refresh-maps network-fiber network-groundstations'
```

It refreshes the selected map exports, every legend, the three books and the
contact sheets, while retaining the scientific products. Replaced map SVGs
use atomic replacement, and selected map exports are detached before rendering
so that shared files in the accepted parent remain unchanged.

The initial legend-only attempt, `20261113t043541z-dd66433ea757`, exported all
156 atlas sheets but failed source validation. Its records pointed to a removed
historical build directory, although identical native inputs remained in the
accepted delivery. Refresh now rebinds these paths to retained inputs only
after matching their original SHA-256 values, preserving the original paths
as provenance. The failed attempt did not replace the accepted delivery.

Focused verification passes **87 tests**: 17 legend/delivery, 10 presentation,
9 export, 11 recovery and 40 data-workflow tests. These include route paint
and status preservation, groundstation background isolation, readable legend
keys, Observer Note removal and refusal to rebind changed source bytes.

The next review run, `20261113t044252z-a42f1283ca86`, passed all three export
validators. Visual inspection identified old fiber prose that still described
black cables. Correcting that prose during rendering caused the implementation
guard to withhold publication. The final run,
**`20261113t045014z-8dc2bb237484`**, includes the wording correction and published
successfully at **8:55:03 PM PST on 12 November**, at the existing
`output/data-edition/20261111/` path.

Independent verification passed for all **160 legend SVG/PDF pairs**, confirming
no Observer Note section and aligned reading headings. It also checked the
network maps' requested paint against unchanged geometry, all artifact hashes,
unchanged remaining map/native/data files, book input order and **80 / 80 / 158**
page counts, and **1,060 local links**. Both selected map PDFs, representative
atlas and optional legend PDFs, and World book pages 15 and 17 were rasterized
for visual review. The receipt is
`.cartofreako/data/operator-logs/atlas-presentation-refresh-verification.json`;
the final log is
`.cartofreako/data/operator-logs/atlas-presentation-refresh-final-20261112.log`.

### Orbital palette and cyclic seam follow-up

The user requested the Setouchi coloring on World book pages 37 and 39
(orbital global positions and observer directions), and removal of the vertical
strip on page 37. The retained Setouchi sheets establish white page paper,
global water `rgb(242,244,243)`, land `rgb(216,221,219)`, observer sky
`rgb(148,148,148)`, and type `rgb(40,42,46)`. The equator and tracks use gray;
the observer horizon is orange. These context colors now override the atlas
wine/amber theme for the two orbital subjects, in both geographic editions.
Categorical satellite marker colors, source epochs and scientific positions
are retained.

The current World source contained an `orbital-image-frame` inset inside the
outer cyclic page frame. Repeating that inset and its opaque native background
created a vertical strip at the wrap boundary. The World adapter now applies
the page margin once, removes repeated source paper, and paints one correctly
colored image background beneath the three cyclic source references. Targeted
previews confirm a continuous seam; regressions check unchanged satellite
attributes and idempotent presentation updates.

The refresh published as **`20261113t054328z-8f8b6a07f3a4`** at **9:48:51 PM
PST on 12 November**. The World book pages 37 and 39 were rasterized from the
delivered PDF and reviewed, along with the Japan observer PDF. Japan retains
its distinct angular sky panel on white paper and pale geographic locator;
the gray sky applies to the World all-sky sheet. All 16 selected orbital map
artifacts in the accepted parent retain their original hashes. The focused
checks now total **88 passing tests**, including the Setouchi context and cyclic
inset regression. The build log is
`.cartofreako/data/operator-logs/atlas-orbital-setouchi-refresh-20261112.log`.

Independent verification passed for all **4,060 artifact hashes**, **160 legend
SVG/PDF pairs**, **2,048 unchanged map/native/data files**, **1,060 local links**,
and the **80 / 80 / 158** page books with unchanged input order. Satellite mark
attributes are unchanged in all four refreshed orbital SVGs; the existing
fiber and groundstation paint corrections also remain intact. The receipt is
`.cartofreako/data/operator-logs/atlas-orbital-setouchi-verification.json`, with
the independent log beside it as
`atlas-orbital-setouchi-independent-20261112.log`.
