# Starlink groundstation update: work record and staged plan

Implementation date: 3 November 2026.

The `network-groundstations` pass now reads the supplied
`starlink-global-gateways-pops.20261103.kml` snapshot through a reproducible,
high-fidelity GeoJSON conversion. Conversion, native integration and local
validation are complete. The remaining stages below describe optional source
exploration and a subsequent product refresh.

## Objective and source scope

Create `starlink-global-gateways-pops.20261103.geojson`, retain the KML's
geometries and descriptive information, and make the new snapshot available
through the existing groundstation generation targets. The reusable converter
is [scripts/convert-kml-geojson.py](../../scripts/convert-kml-geojson.py).

Both source and converted files live in
`assets.static/network-groundstations/`. The source document is titled
**Unofficial Starlink Global Gateways & PoPs**. Its filename supplies the
snapshot date; that date is not a verification date for every location or
operating-status claim.

| Verified source property | Count |
| --- | ---: |
| Placemarks / output features | 780 |
| Point features | 656 |
| LineString features | 124 |
| Coordinate tuples, including altitude | 1,009 |
| Source folders | 10 |
| Shared Style definitions | 118 |
| Shared StyleMap definitions | 59 |
| Records containing repeated custom-field names | 294 |

The older `20250902` input contains 618 records: 499 points and 119 lines.
The difference is 162 source records. A record-level comparison has not been
performed, so this difference does not establish 162 newly built stations.
The newer document includes PoPs, backbone links, community gateways,
community-gateway satellite links and quad-band gateways alongside regional
gateway folders.

The current profile records the supplied document title and both file hashes.
Its repository and commit fields are empty, and its license field states
`Not specified in the supplied KML`. These details are not copied from the
older alpha60 snapshot.

```text
KML SHA-256
8fc79a58f69f007a8321768200ee9beb816376cb1338f157f4c73c777d660c55

GeoJSON SHA-256
83929aa67dffac33dd85ef536e490fc7e6b239b486446f187bb95ab00612470a
```

## Work completed

The converter uses Python's standard library and emits one feature per
Placemark in source order. It retains longitude, latitude and altitude,
including original coordinate text in the metadata. Every numeric coordinate
in this snapshot was compared with the source using decimal arithmetic;
none changed. Geometry is neither simplified nor deduplicated.

Ordinary feature properties expose `Name`, HTML `description`, `styleUrl`,
`folder_path` and `extended_data`. Custom fields remain ordered name/value
entries because the source repeats field names within individual records.
Empty values, Unicode, links and descriptive status strings are preserved.

`properties.kml` retains each Placemark's XML information as a JSON tree.
Collection-level `kml.document` retains the document and folder structure,
shared styles and style maps, with references to feature IDs. The tree keeps
namespace-qualified element names, attributes, element order and text,
including geometry settings such as `tessellate`. XML formatting whitespace,
namespace prefixes and CDATA wrappers are not retained. Referenced URLs are
stored without being fetched.

The converter handles Point, LineString, LinearRing, Polygon and MultiGeometry
inputs. Invalid coordinates, unsupported geometry and NetworkLink inputs
produce explicit errors. Output is deterministic; `--check` compares an
existing file without rewriting it, and conversion replaces its destination
only after successful validation. The native groundstation pass continues to
accept Point and LineString features, which cover this entire snapshot.

| Component | Implemented change |
| --- | --- |
| `scripts/convert-kml-geojson.py` | Executable, reusable converter and verification mode |
| `tests/test-convert-kml-geojson.py` | Seven tests covering source fidelity, reconstruction, geometry, invalid inputs and output preservation |
| `assets.static/network-groundstations/network-groundstations-profile.json` | Selects the new GeoJSON; declares 780 features, the snapshot date and KML/GeoJSON provenance |
| `assets.static/network-groundstations/SHA256SUMS` | Pins the profile, original KML, converted GeoJSON and historical JSON |
| `src.generate/network-groundstations-data.h` | Reads the configured filename and checks its embedded KML provenance against the profile |
| `src.generate/network-groundstations-generation.h` | Derives the gateway group date from the dataset and writes the current source title, filenames and hashes into SVG metadata |
| `Makefile` | Uses the new input and includes reproducibility and converter tests in `check-network-groundstations` |
| `.gitignore` | Narrow exceptions admit the supplied KML and converted GeoJSON |
| `docs/pages/passes/network-groundstations.md` | Documents conversion, metadata, rendering and verification |

Rendering uses the existing red links and triangular marks. Each feature's
first coordinate supplies its mark, so 780 marks are source records rather
than a count of unique physical gateways. The source's KML styling remains
available in GeoJSON but is not applied to the map. The dated group is now
`starlink-gateways-20261103`.

## Validation and local artifacts

`make check-network-groundstations` passed: all four checksum entries matched,
the stored GeoJSON matched a fresh conversion, and all seven tests passed.
The tests compare every feature's coordinates and custom fields, reconstruct
the source XML information from the retained trees, and verify the profile's
source hashes. GDAL independently opened the GeoJSON and reported 780 features.

The native generator compiled with the repository's warning-as-error flags.
All six standard projections generated successfully: Cahill–Keyes, AuthaGraph,
Dymaxion, Myriahedral, Star-X and Voronoi. Each SVG passed the generator's
checks. A separate inspection confirmed 780 marks, 124 links, the new date,
the configured input filename and both source hashes in every SVG.

The validation SVGs are under
`build/network-groundstations-20261103/<projection>/svg/`. An AuthaGraph PNG
at `build/network-groundstations-20261103/preview-authagraph.png` was rendered
at 1,600 pixels wide and visually inspected. These are local build artifacts.
The full PDF, PNG and derivative product set has not been regenerated, and
the published v14 previews still describe the historical snapshot.

## Staged plan

| Stage | Status | Work and completion criterion |
| --- | --- | --- |
| 1. Inventory and pin the source | Complete | Identify document structure, geometry counts, repeated fields and file hashes; preserve the original KML. |
| 2. Implement faithful conversion | Complete | Produce the named GeoJSON through the durable script; preserve coordinates and metadata; verify deterministic output and failure behavior. |
| 3. Integrate the native pass | Complete | Select the input through the profile, update Make dependencies and source pins, and derive date/provenance from the selected snapshot. |
| 4. Validate locally | Complete | Pass checksum and conversion tests, open the result with GDAL, generate all six projections and inspect a raster preview. |
| 5. Explore source semantics and changes | Proposed | Compare the two snapshots and review folder, status and style meanings before introducing classifications or change claims. |
| 6. Refresh selected products | Proposed | Generate the desired delivery products, synchronize their legends and bibliography with their actual inputs, and review the resulting maps. |

Stage 5 should produce an inspectable correspondence between old and new
records using geometry, location and names, with ambiguous matches retained
for review. Added, removed and changed source records should remain distinct
from claims about construction, closure or operation. Repeated locations and
links should remain traceable to their original features. Any derived
gateway/PoP/backbone/status categories should preserve the original folder,
style reference and custom fields and explain how the category was assigned.

Stage 6 can first regenerate SVG, PDF and PNG products in a separate build
directory. A new Setouchi delivery also needs a coordinated update of
`scripts/build-setouchi-bibliography.py` and
`scripts/revise-setouchi-plates.py`: both still contain the historical
2 September 2025 / 618-record description. Their source lists and labels must
match the chosen delivery snapshot before that delivery is rebuilt. Existing
published products retain their original dates and provenance.

The current `generation-profile.json` selection was not changed by this
integration. Use the explicit groundstation targets below to render the pass.
Source-style rendering or new semantic symbols would be a separate change
following the Stage 5 review.

## Reproduction commands

Run from the repository root:

```sh
python3 scripts/convert-kml-geojson.py \
  assets.static/network-groundstations/starlink-global-gateways-pops.20261103.kml \
  assets.static/network-groundstations/starlink-global-gateways-pops.20261103.geojson

make check-network-groundstations

make -j2 generate-network-groundstations \
  GENERATED_DIR=build/network-groundstations-20261103
```

For a subsequent full product refresh:

```sh
make -j2 generate-network-groundstations-artifacts \
  GENERATED_DIR=build/network-groundstations-20261103
```

An intentional source or conversion change requires updating the profile's
counts, date and hashes as appropriate, then regenerating `SHA256SUMS` and
running the checks before rendering. The KML, GeoJSON, converter, tests,
integration changes and this record belong in the same repository handoff.
Generated build products and unrelated local archives are excluded.

See the maintained [Network Groundstations implementation notes](../pages/passes/network-groundstations.md)
for the conversion metadata layout and rendering details.

## Orbital Technosphere follow-up: named constellations

Requested on 3 November 2026: inspect and update the
[published AuthaGraph global map](https://bdekoz.github.io/cartofreako/assets.tot/products/standard/authagraph/full/orbital-technosphere-global-authagraph-44-19.052559.webp),
and group satellite constellations by name. Starlink and Iridium are examples;
the grouping should also cover other named constellations and fleets.
The agreed presentation is separate named SVG groups and legend entries,
while retaining each satellite at its calculated geographic position.
The user also requested individual satellite names on a layer separate from
the vector dots. The OMM feed provides `OBJECT_NAME` and `NORAD_CAT_ID`.
The user specified the hierarchy as `starlink/name,locpoint`: each named
constellation is a parent layer containing `name` and `locpoint` sublayers.
Every admitted satellite receives a name label and a vector dot, joined by
NORAD ID. XML IDs are unique across the SVG (for example `starlink-name` and
`starlink-locpoint`), while the editor sublayer names are `name` and
`locpoint`. Name layers
will default to hidden to keep the full-population map legible and can be
enabled in an SVG editor. This supersedes the former small label budget for
the new profile.

The downloaded published image matches the local preview byte for byte
(SHA-256 `61acd99b4b9f45ff00634b757191b259cff7a55deaa66a2b32cd966607b7c07a`).
Its generation profile uses `2026-08-13T15:36:00Z`. The renderer currently
groups objects by broad role; Starlink, OneWeb, Kuiper, Qianfan and Hulianwang
share the red megaconstellation layer, while Iridium NEXT, Globalstar and
ORBCOMM share the communications layer. Membership is already joined by
NORAD catalog ID, providing a foundation for named groups without adding
duplicate satellite marks.

### Implementation plan and staging

| Stage | Current status | Work and acceptance |
| --- | --- | --- |
| O1. Inspect the published map and source pipeline | Complete | Confirm the published bytes, snapshot date, existing role groups, membership joins and shared historical dependencies. |
| O2. Capture a current dated snapshot | Complete | Retrieve the active catalog and configured membership/debris feeds; record acquisition times, source URLs and hashes; use an explicit propagation instant. Preserve the historical snapshot. |
| O3. Define named constellations and fleets | Complete | Add profile-driven IDs, display names and colors; include the named communications, Earth-observation and navigation groups supplied by CelesTrak. Keep generic and unmatched populations visible. |
| O4. Render named groups and a count legend | Complete | Emit one satellite mark per NORAD ID, named editable SVG groups, consistent colors and legend counts. Retain all source memberships and handle overlapping fleet catalogs deterministically. |
| O5. Validate and review | Complete | Test membership/overlap behavior, count conservation, source freshness and propagation; render global and observer products across projections; visually inspect AuthaGraph. |
| O6. Refresh previews and record results | Complete | Refresh the relevant preview assets with a dated provenance receipt; document actual source coverage, exclusions, commands and remaining limitations here. |

The initial named coverage is Starlink, OneWeb, Kuiper, Qianfan, Hulianwang,
Iridium, Globalstar, ORBCOMM, Intelsat, SES, Eutelsat, Telesat, Planet, Spire,
GPS, GLONASS, Galileo and BeiDou. These are catalog-defined constellations or
fleets; the term megaconstellation is not imposed on every group. The
[current CelesTrak directory](https://celestrak.org/NORAD/elements/)
supplies the membership feeds. A residual role group remains necessary for
objects outside these named catalogs; this is not a complete operator registry.

### Working notes

- Preserve the existing August data: historical orbital regression tests and
  the Hubble astronomy profile refer to it. The new snapshot gets a dated
  directory and becomes the default for new Orbital Technosphere generation.
- Keep the active catalog as the primary population. Membership files classify
  existing objects; bounded debris supplements remain separate, including
  Iridium 33 debris rather than folding it into the active Iridium fleet.
- Overlapping memberships must not create duplicate marks or inflated totals.
  Retain all memberships in metadata and use documented profile precedence
  for the single displayed group.
- Source acquisition must stop on HTTP errors and respect the provider's
  two-hour cache interval. Do not report a failed refresh as current data.
  [CelesTrak GP format and usage documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php)
- Refreshing catalog elements and choosing a propagation instant are separate
  operations. Keep the existing seven-day age and six-hour future tolerances
  and report rejected or failed objects.
- NASA SSC reference data is an independent validation input. Its timestamp
  must remain explicit if current ephemerides cannot be retrieved; retaining
  the historical reference does not make it a current validation observation.
- Representative tracks and labels are overlays, not membership evidence.
  Named groups should remain selectable even where orbital tracks overlap.

### Agreed satellite layer structure

```text
starlink
  name       satellite names; hidden by default
  locpoint   satellite vector dots
iridium
  name
  locpoint
oneweb
  name
  locpoint
...one parent for each configured constellation or fleet
```

The parent selects the whole constellation; its two children can be toggled
or styled independently in an SVG editor. A dot keeps its source coordinates,
object name and NORAD ID. The corresponding text uses the source object name
and carries the same NORAD ID plus a reference to the dot's SVG ID. Both
children retain the displayed constellation ID. The text and dot have
different globally unique SVG IDs.

Implementation order: define and validate the named membership registry;
assign each admitted satellite to one display parent; emit every dot into
`locpoint`; emit every corresponding name into `name`; add the named count
legend; then validate the SVG hierarchy and all associations. Overlapping
source memberships remain available in metadata and resolve by explicit
profile order, so a satellite appears in one display group. Every visible
object in the global product must have exactly one dot and one name, and
the observer product must apply the same horizon filter to both children.

Acceptance checks will compare per-layer counts with the admitted catalog,
verify unique SVG IDs and matching NORAD IDs, ensure the name layer contains
text while `locpoint` contains markers, and confirm that toggling names does
not alter satellite positions or the constellation totals. Default PNG/WebP
exports show the dots and legend; editable SVGs retain the complete names.

### Implemented snapshot and validation results

The current dataset is
`assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json`.
Its explicit propagation instant is **2026-11-03T17:10:00Z**. Acquisition
retrieved 26 CelesTrak OMM catalogs: the active population and 25 membership
or debris feeds. `acquisition.json` records the URL, retrieval time, SHA-256,
record count and epoch coverage for each feed; `SHA256SUMS` pins the complete
snapshot, profile and receipt.

The active input contains 16,844 records. After the existing seven-day age
and six-hour future filters, the global product plots **17,909 objects**:
16,808 active objects and 1,101 bounded debris records. Forty-four loaded
records were filtered by epoch; zero failed SGP4 propagation. The observer
product plots 1,088 objects above the captured San Francisco horizon.

The current NASA SSC query failed with a network-unreachable error. Its
historical response remains explicitly tagged `historical-validation-only`
at `2026-08-13T15:36:00Z`. The refreshed November positions use the current
CelesTrak elements and SGP4; the historical NASA reference is not evidence
of a contemporaneous independent comparison.

| Named parent | Plotted objects in the global product |
| --- | ---: |
| Starlink (`starlink`) | 11,155 |
| OneWeb (`oneweb`) | 651 |
| Kuiper (`kuiper`) | 391 |
| Qianfan (`qianfan`) | 256 |
| Hulianwang (`hulianwang`) | 235 |
| Iridium (`iridium`) | 80 |
| Globalstar (`globalstar`) | 36 |
| ORBCOMM (`orbcomm`) | 14 |
| Planet (`planet`) | 129 |
| Spire (`spire`) | 72 |
| Intelsat (`intelsat`) | 55 |
| SES (`ses`) | 67 |
| Eutelsat (`eutelsat`) | 29 |
| Telesat (`telesat`) | 17 |
| GPS (`gps`) | 32 |
| GLONASS (`glonass`) | 24 |
| Galileo (`galileo`) | 31 |
| BeiDou (`beidou`) | 52 |

Residual role layers account for 3,247 other active objects, 154 other
Earth-observation objects, 43 science objects, 19 other navigation objects,
19 human-presence objects and 1,101 debris records. These groups also use
separate `name` and `locpoint` children. The named display assignment follows
profile order and preserves all original membership IDs on the dot.

`make check-orbiting` covers the historical SGP4/NASA reference test, the
new named-group conservation/overlap tests and the current snapshot hashes.
All passed. Four additional acquisition tests passed: duplicate IDs are
rejected, fresh cached payloads are reused, a failed partial capture installs
nothing, and an existing snapshot cannot be overwritten.

All twelve global/observer SVGs generated successfully across Cahill–Keyes,
AuthaGraph, Dymaxion, Myriahedral, Star-X and Voronoi. The independent XML
validator verified unique SVG IDs, exact source names, layer types, hidden
name-layer defaults, and matching NORAD IDs for every dot/name pair. Each
global SVG contains 17,909 pairs and each observer SVG contains 1,088 pairs.
The AuthaGraph raster was visually inspected with the named count legend.

The durable implementation is in `src.generate/orbiting-data.h` and
`src.generate/orbiting-generation.h`. The default Make input selects the new
dated profile; Hubble's astronomy input and the historical orbital tests keep
the August elements. `scripts/refresh-orbiting-snapshot.py` and the existing
shell entry point capture future snapshots in new directories rather than
mutating a checked reference. Active populations exceeding the configured
budget now fail explicitly instead of being silently truncated.

```sh
make check-orbiting
make -j2 generate-orbiting GENERATED_DIR=build/orbital-technosphere-20261103
python3 scripts/verify-orbiting-layers.py \
  --profile assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json \
  --report build/orbital-technosphere-20261103/validation.json \
  build/orbital-technosphere-20261103/*/svg/orbital-technosphere-*.svg
```

On the restricted development host, `CXX=/usr/bin/g++` bypassed a read-only
compiler cache and `INKSCAPE_RUNNER=env` bypassed unavailable D-Bus sockets
for PNG export. These were command-line environment workarounds, not changes
to the compiler or renderer defaults.

### Preview refresh and delivery

The six global previews under `assets.tot/products/standard/<projection>/`
now use the November snapshot. Full WebP, 480-pixel thumbnail PNG and
1920 × 1080 WebP variants were refreshed. The screen derivatives use the
existing contain layout with `#f4f5f5` padding. The original AuthaGraph URL
therefore resolves to the updated image once these repository changes are
deployed by Pages.

`assets.tot/orbital-technosphere-20261103.json` records the source profile,
snapshot checksum manifest, generator source hashes, six source SVG hashes
and all 18 derivative hashes. `assets.tot/manifest.json` records this as a
partial update, retaining the historical base revision for the other maps.
The preview checker validates every updated product against this receipt.
At this first preview refresh, observer SVGs were regenerated and checked
locally while the website's observer previews retained their older capture.
The subsequent debris-symbol update below refreshes both products.

The editable AuthaGraph master is
`build/orbital-technosphere-20261103/authagraph/svg/orbital-technosphere-global-authagraph-44-19.052559.svg`.
The raster preview cannot contain editable SVG layers; open the master in an
SVG editor to toggle `starlink/name`, `starlink/locpoint`, and the corresponding
children of the other constellations. All names are present in that master.

After exporting the six global PNGs at a 3,840-pixel long side, the focused
preview update is reproducible with:

```sh
python3 scripts/stage-orbiting-preview.py \
  --build-root build/orbital-technosphere-20261103 \
  --profile assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json
python3 scripts/check-tot-snapshot.py
```

The downloaded CSVs retain their original CRLF bytes. A scoped
`.gitattributes` rule prevents Git newline normalization from changing their
acquisition hashes on checkout. The earlier Starlink groundstation work and
the historical orbital input bytes remain intact.

### Initial debris symbol follow-up: both plates (superseded below)

The requested mark for debris is a **black triangle**. The final scope is
both global and observer plates, across all six projections, with matching
legend keys. Each debris object keeps its NORAD ID, metadata, projected
position and separate `name`/`locpoint` layers. The shared renderer supplies
an upright equilateral triangle centered on the position, with an opaque
black fill. Its 0.022-inch circumradius preserves approximately the filled
area of the previous 0.014-inch circular mark. Illumination state remains in
the metadata; other object styles retain their illumination treatment.

The staged plan is:

1. Update the shared object and legend symbol renderer for both products.
2. Extend the SVG validator to check closed, nondegenerate black triangles,
   matching legend keys and the existing one-to-one name associations.
3. Regenerate and verify all twelve SVGs, visually inspect both AuthaGraph
   plates, and export their six-projection PNG/WebP previews.
4. Extend the preview script with `--product global|observer`, retain a
   separate source receipt for each product, check the documentation and
   preview receipts, then commit and push.

The observer website previews will now use the same pinned November
snapshot as the global previews. No new acquisition or propagation instant
is introduced for this symbol change. After all twelve PNGs are exported at
a 3,840-pixel long side, stage both products with:

```sh
for product in global observer; do
  python3 scripts/stage-orbiting-preview.py \
    --product "$product" \
    --build-root build/orbital-technosphere-20261103 \
    --profile assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json
done
python3 scripts/check-tot-snapshot.py
```

### Revised symbols and Setouchi plate layout: complete follow-up scope

This update covers every request since the named-constellation delivery.
The initial request was a black debris triangle on the observer plate,
expanded to both global and observer plates. That intermediate renderer was
built and checked locally, with 1,101 debris markers per global plate and
53 per observer plate; it was not committed or published. The following
symbol rules supersede it and apply to **both products in all six projections**:

| Object or display group | Marker | Color |
| --- | --- | --- |
| Debris, including Iridium 33 debris | `x` | Solid black |
| Starlink | Sunburst | Existing Starlink red |
| Intelsat | Square | Existing Intelsat color |
| Remaining Earth-observation objects, including Planet and Spire | Upright triangle | Existing group/role color |
| Other objects | Circle | Existing group/role color |

Debris takes precedence, followed by the named Starlink and Intelsat rules,
then the Earth-observation role. Each object retains its catalog ID, original
name, source memberships and position. The `name` and `locpoint` children
remain independently editable, with names hidden by default. Legend keys
must use the same shape and color as the corresponding location markers.

The requested presentation adopts the Setouchi ST2 separate-sheet style:
one map plate and one matching legend/attribution plate for every projection
and product. Map plates have no overlaid legend. Legend plates use Atkinson
Hyperlegible, vertical right-edge headings, stacked keys with counts, and
the source bibliography at left. Proportional white map margins follow the
saved atlas scale; each projection retains its geographic/celestial framing.
The source panel credits CelesTrak, the SGP4 reference implementation,
Natural Earth where used, Cartofreako and the projection documentation. It
identifies the pinned calculation time and separates the historical NASA
SSC validation reference from the current plotted element data.

The revised staging is:

1. Implement the shared marker rules and matching legend symbols, including
   named and residual Earth-observation groups and any empty legend entries.
2. Add a durable map/legend composition step to the orbital Make targets,
   using the existing Setouchi typography helpers and saved atlas style.
3. Verify all twelve map/legend pairs for symbol geometry, black debris,
   preserved names/IDs/counts, independent layers, separation, attribution,
   matching companion filenames and complete source provenance.
4. Export the separate plates, visually inspect global and observer examples,
   refresh both preview families, and expose each companion legend from the
   gallery. Update receipts and documentation, then commit and push.

The preview script's new `--product global|observer` selection and separate
receipts are retained. The observer website previews advance to the same
November snapshot already used by the global product. The calculation
instant remains `2026-11-03T17:10:00Z`; no new source capture is required.

### Global Starlink IDs and three metallic-paper speculations

The global plate must show Starlink catalog IDs at **10 pt**. The request's
"NOAH id" is interpreted as **NORAD catalog ID**, the identifier present in
these source catalogs. A visible `starlink/id` text layer is added only to
the global map, alongside the existing hidden `name` layer and visible
`locpoint` layer. Other vendors receive no ID layers. Observer names remain
hidden. The final physical type size accounts for the proportional sheet
framing; each ID links to its corresponding marker by NORAD ID.

The print study was initially requested as **MSP speculation 1** and is now
expanded to **three speculations**. Its subject scope is limited to the
updated `network-groundstations`, `orbital-technosphere-global`, and
`orbital-technosphere-observer` plates, each with its separate legend and
attribution companion. The groundstation source is the high-fidelity
20261103 Starlink conversion completed earlier in this record. Projection
coverage is **AuthaGraph only**, as confirmed in the follow-up. The studies
use the complete Setouchi setup: a 43.5-inch image on the 44-inch sheet,
the +4.35-inch printed cyclic horizontal adjustment, and the established
lower-left Antarctic land inset where terrestrial land is present. The
observer sheet uses the same cyclic frame without terrestrial land. This
is separate from the standard six-projection orbital update.

The supplied physical observations are: an Epson Stylus Pro 9000 running
low on cyan and light magenta, metallic glossy paper, better results with
dark backgrounds, and grays printing as pale violet. The observed violet
cast takes precedence over a generic assumption that reducing ink supply
predicts a known color response. The studies will therefore use dark,
green-biased neutral backgrounds and restrained magenta reduction, with
different documented strengths. Pure-black debris x marks remain black;
lighter text and sufficient background separation must keep symbols and
10 pt IDs legible. Shapes, source data, geometry and group identities remain
constant across the color studies.

These are reproducible visual hypotheses, not measured device corrections.
The cartridge warning does not quantify channel loss, and no measured
printer/paper ICC profile or printed color target was supplied. The exact
paper brand is unspecified. The [Epson Pro 9000 manual](https://files.support.epson.com/pdf/pro9k_/pro9k_u1.pdf)
documents the six ink channels and low/empty indicators;
[Epson's metallic glossy paper description](https://epson.com/For-Work/Paper/Pro-Imaging/Metallic-Photo-Paper-Glossy/m/S045590)
provides general paper context, not identification or calibration of the
user's stock. The compensation parameters will be saved with each study.

Additional stages are: build the three color variants from the verified
separate plates; export matching map/legend previews and print files; supply
an inspectable comparison and color recipe; verify source identities,
black debris, retained symbol shapes and Starlink-only 10 pt IDs; append
results here and include the completed work in the authorized commit/push.

### Completed follow-up and print-study delivery

All revised stages are implemented. The standard orbital build now produces
**twelve map/legend pairs (24 sheets)** across six projections. Both products
use black debris x marks, Starlink sunbursts, Intelsat squares and triangles
for the remaining Earth-observation objects. The global plates have
**11,155 visible Starlink NORAD IDs at 10 pt** in `starlink/id`. No other
vendor has an ID layer, and observer IDs are absent. Original satellite
names remain in the hidden `name` sublayers. Each global plate retains
17,909 objects, including 1,101 debris; each observer plate retains 1,088
objects, including 53 debris.

All twelve standard map/legend pairs were exported to SVG, PDF and PNG.
The map and legend WebP/thumbnail/screen derivatives are staged under
`assets.tot`, with separate global and observer receipts. The gallery now
provides a **Legend and attribution** action for each orbital map. The
standard artifact manifest remains scoped to its existing map inventory;
companion legends have dedicated export targets and preview receipts.

The [MSP review index](../../output/msp-speculations-20261103/index.html)
contains **three studies × three subjects × map/legend = 18 sheets**. The
subjects are the current groundstations, global orbital technosphere and
observer orbital technosphere, all in the confirmed Setouchi AuthaGraph
frame. The existing `setouchi_world_framing.py` supplies the exact 43.5-inch
image, +4.35-inch printed cyclic move and common lower-left Antarctic inset.
No Antarctic inset appears on the celestial observer sheet.

| Study | Background | Land | Magenta reduction | Cyan emphasis | Saturation factor | Foreground lightness floor |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MSP speculation 1 / Charcoal green | `#26382f` | `#4c6655` | 0.10 | 0.06 | 0.90 | 0.50 |
| MSP speculation 2 / Olive graphite | `#343b24` | `#68764a` | 0.18 | 0.12 | 0.82 | 0.56 |
| MSP speculation 3 / Deep forest | `#152e28` | `#3a6d59` | 0.26 | 0.18 | 0.75 | 0.62 |

These are chosen recipe parameters, not measured percentages of lost ink.
For chromatic foreground colors, the recipe subtracts the common black
component in a simple CMY decomposition, emphasizes residual cyan and
reduces residual magenta, then applies the saved HLS lightness floor and
saturation factor. Near-neutral colors use explicit green-biased replacements.
Background, land and text colors are assigned explicitly. Every debris x
retains its opaque black stroke; a pale backing stroke provides contrast on
the dark paper field. Map and legend keys use the same color transformation.
The groundstation symbols and supplied route geometry remain intact.

The exact recipes are in
[`config/msp-speculations-20261103.json`](../../config/msp-speculations-20261103.json).
[`build-msp-speculations.py`](../../scripts/build-msp-speculations.py) saves
source/output hashes, framing records and the old-to-new color mapping.
Its geometry comparison checks that color processing preserves source
coordinates, names, IDs and type. Exports are cached only when the SVG,
font provenance and delivered file hashes agree.

Each of the 18 MSP sheets has a full-size vector PDF, a 3,840-pixel WebP and
a compressed editable SVG: **54 delivered files**, plus the index, recipes,
manifest and validation report. Uncompressed SVG and PNG working masters
are under `build/msp-speculations-20261103/`. The PDFs retain the physical
44 × 19.052559-inch sheet; Atkinson Hyperlegible is embedded. All three
palettes and the revised attribution layout were visually inspected.

Validation passed for the orbital and groundstation tests, pinned source
hashes, all twelve standard map/legend pairs, all 18 delivered MSP sheets
and their 54 file hashes, source counts, exact Setouchi framing, black debris,
marker geometry, matching names, Starlink-only 10 pt IDs and PDF page sizes.
The groundstation studies retain all 780 current placemarks and both the
KML and GeoJSON hashes. Documentation links, preview receipts and the
standard artifact manifest checks passed. The dense global ID field is
intentional: every admitted Starlink ID is shown as requested, with the
editable `id` layer available separately from the markers.

Reproduce the print study after generating the current standard inputs:

```sh
make msp-speculations \
  GENERATED_DIR=build/orbital-technosphere-20261103 ASSET_JOBS=2
python3 scripts/verify-msp-speculations.py
```

On this restricted host, `CXX=/usr/bin/g++` remains the compiler-cache
workaround. The MSP exporter uses the repository-local, verified font
environment and direct Inkscape export. The historical NASA reference
remains explicitly historical; these print studies do not refresh source
data or establish a calibrated printer/paper correction.

### Typography revision: global Starlink text at 9 pt

The subsequent request reduces global Starlink text from 10 pt to **9 pt**.
This applies to the visible `starlink/id` NORAD labels and the hidden
`starlink/name` text layer. Both use 9 physical points after the proportional
map framing. Other vendor labels and the observer plate are unchanged.

Regenerate all six standard global map/legend pairs, then the global
map/legend pair in each of the three MSP studies. Preserve the existing
9-point label setting when transferring the standard Starlink name and ID
layers into the Setouchi cyclic frame. Update the legend explanation,
review index, preview receipts and validators; verify every global Starlink
name and ID size, then commit and push the revision. The prior 10 pt results
above describe the earlier delivery; this section supersedes that type size.

Completed the 9 pt revision: all six standard global map/legend pairs and
all three MSP global pairs were regenerated. SVG checks verified both the
hidden names and visible NORAD IDs after framing; all 18 MSP sheets and
54 delivered files passed validation. The six standard global preview
pairs and receipts were restaged.

### Groundstation capability studies: request, evidence and staging

The next request targets `network-groundstations-authagraph-44-19.052559.pdf`:
scale the groundstation marks by antenna size/capability, reuse the CDN
grouping and honeycomb layout, replace each hexagonal mark with an
equilateral triangle centered in its hexagonal cell, and compare one to
three radial fill treatments for different capabilities. Continue the
Setouchi AuthaGraph horizontal framing and separate map/legend sheets with
attribution. Use one dark MSP palette across the three pattern studies so
the comparison changes the symbol treatment rather than the paper recipe.

The source contains 590 antenna-site point records, 66 PoP point records,
and 124 link records. All 590 antenna-site records have ExtendedData.
These are source records, not a verified census of unique, operating sites:
four coordinate pairs repeat, including upgrades and a duplicate place
name. Retain their identities in grouping and evidence; do not silently
merge the records or turn link endpoints into antenna sites.

1. **Normalize and inspect evidence.** Preserve raw ExtendedData, source IDs,
   status, dates, application links and coordinates in a durable capability
   receipt. Strictly parse positive diameters and integral antenna counts.
   Examples needing attention include three E-band counts of `1.85`, two
   composite `1.85+1.999` sizes, partially built inventories and contradictory
   frequency/operational fields. Missing or ambiguous values stay unknown.
2. **Define the visual quantity.** Use the largest complete documented
   antenna bank's geometric aperture, `max(N × π × D² / 4)`, as a size proxy.
   Do not sum across bands: shared Ka/E hardware and overlapping records
   could otherwise be double-counted. This is listed hardware, potentially
   licensed or planned, not measured throughput, installed capacity or
   operational RF performance. Preserve incomplete-bank flags and distinguish
   unknown size from zero. Validate the interpretation of diameter units
   against primary technical material without imputing a generic model to
   every station.
3. **Reuse CDN placement.** Use its projected grouping grid and shared
   `hexoffsets` routine, one source point per cell, with a centered equilateral
   triangle for each antenna record. Keep true positions and displacement
   tethers inspectable. Use sufficient cell spacing for the largest triangle;
   do not change grouping totals or cap away small records. Keep PoPs and
   supplied lines as distinct network context.
4. **Compare three fills.** Build radial spokes, concentric arcs and radial
   petals with explicit keys for the source's capability classes. Keep the
   size mapping, grouping, source records, frame and palette identical.
   Show reported operational versus unconfirmed/planned/retired status
   separately from capability, and retain unknown capability marks.
5. **Deliver and verify.** Export three map/legend PDF pairs, editable SVGs,
   previews and a review index. Check source accounting, scaling, triangle
   geometry, placement, pattern coverage, page dimensions and attribution;
   visually inspect the maps, legends and enlarged symbols. Append results,
   remaining evidence limits and reproduction commands here; commit and push.

This section records all decisions since the preceding typography entry.
The earlier MSP color hypotheses and the 9 pt global Starlink setting
remain in effect. Groundstation capability studies are a separate comparison
set, so the original three color proofs remain available.

### Capability study implementation and results

Completed all three pattern options in
[the capability review](../../output/groundstation-capabilities-20261103/index.html):
radial spokes, concentric rings and radial petals. Each option contains
`network-groundstations-authagraph-44-19.052559.pdf` and its separate
`-legend.pdf`, plus editable `.svg.gz` and 3840-pixel WebP previews.
The review page includes enlarged vector pattern keys. There are six
print sheets and 18 PDF/SVG/WebP delivery files; the evidence receipt,
manifest and validation record accompany them.

All options use MSP speculation 1's charcoal-green background, its pale
green neutral for the pattern interiors, and its adjusted red for the
triangle outlines. Pattern interiors were lightened after inspecting the
first proofs. Ring radii fit inside the triangle's incircle so the second
ring remains distinguishable from a single ring; petals have a wider
interior than spokes. Unknown size uses a hollow central square, which
cannot be confused with the circular pattern in the ring study. These are categorical textures, not radiation
patterns, antenna counts or a new RF model. No pattern has been promoted
to the ordinary six-projection pass. The earlier MSP color proofs remain
available unchanged, and global Starlink text remains at 9 pt.

The durable implementation is
[`groundstation_capabilities.py`](../../scripts/groundstation_capabilities.py)
for interpretation and
[`build-groundstation-capabilities.py`](../../scripts/build-groundstation-capabilities.py)
for layout, symbols, sheets and exports. The saved
[configuration](../../config/groundstation-capabilities-20261103.json)
records the formula, scale, palette, patterns and primary-source references.

| Evidence or display quantity | Result |
| --- | ---: |
| Source antenna-site records | 590 |
| Records with a usable listed bank aperture | 538 |
| Unknown-size records | 52 |
| Records with at least one incomplete bank inventory | 91 |
| Source PoP points / supplied links | 66 / 124 |
| Repeated field sets reconciled | 294 |
| Invalid fractional count fields / composite diameter fields | 3 / 2 |
| Records whose status describes a partial build | 113 |
| Exact-coordinate duplicate groups / records in those groups | 4 / 8 |
| Records with no source date | 123 |
| Projected CDN-style groups / largest group | 493 / 10 |
| Small known records using the radius floor | 23 |

An initial last-value read of repeated fields produced 498 usable records
and 92 unknown sizes. The source-preserving review found 163 repeated-field
sets containing one populated value and a blank, plus the equivalent
`5.0`/`5` pair. Reconciliation recovered 40 records with usable size pairs,
giving the final **538 / 52** split. Identical repetitions are also recorded;
ordered raw entries remain intact. The parser accepts `32.` as the integral
number 32, rejects `1.85` as an antenna count, and does not treat
`1.85+1.999` as one diameter. A future conflict between different populated
values is explicitly unresolved rather than resolved by entry order.

The source does not state diameter units in its field labels. This study
interprets numeric antenna sizes as metres, consistent with the FCC's
SpaceX listings of 1.47 m and 1.85 m antennas. The indexed primary-source
excerpts were inspected; direct requests for those two FCC PDFs returned
HTTP 403. The complete
[Starlink submission to Ofcom, 19 March 2025](https://www.ofcom.org.uk/siteassets/resources/documents/consultations/category-3-4-weeks/consultation-temporary-ngso-gateway-access-to-e-band/starlink-supporting-submission-for-temporary-e-band-ngso-gateway-licence.pdf?v=397735)
was inspected: pp. 4–5 describe existing V4 hardware supporting both Ka and
E transmission. This supports avoiding a sum of band inventories. It does
not independently verify the supplied 2026 site inventory. The FCC source
references are
[DOC-374641A1](https://docs.fcc.gov/public/attachments/DOC-374641A1.pdf) and
[DOC-395259A1](https://docs.fcc.gov/public/attachments/DOC-395259A1.pdf).

The visual quantity is the largest **complete listed bank** among the
available Ka, E, combined Ka/E, Q/V and W fields. Incomplete banks remain
flagged even when another bank can size the record. No diameters are
imputed from a generic antenna model or a free-text sighting. Port speeds,
uplink/downlink fields, frequency availability and operational booleans
are not converted into throughput. Source capability keys are Ka (217),
Ka+E (243), E-only (9), Q/V (1), quad-band (66), community gateway (21),
TT&C (4), Ku (1), and unspecified/conflicting band (28). Community gateway
is a source role; it is not a separate RF band.

321 records have at least one TRUE operational flag without an overriding
negative status; 250 are unconfirmed/planned; 19 have retired/withdrawn
status text. These are source-claim classes. The two conflicts between an
operational flag and an explicit negative status, four band/operational
disagreements, and all partial-build statements are retained in the
[evidence receipt](../../output/groundstation-capabilities-20261103/capability-evidence.json).
A license or a listed 40-antenna inventory is not relabeled as 40 installed,
working dishes.

Placement reuses `generation-style.json:cdn.group_grid_in` (0.0625 source
inch), the CDN's source-family grouping principle, and the exact shared
`cartofreako_style.hexoffsets` function. One point record occupies each cell,
with no record cap. Antenna radius is `0.045 × sqrt(A / 13.577335130284366)`
source inches, floored at 0.04; an unknown-size triangle uses 0.055.
Each group's hex radius is at least 0.08 inch and 1.24 times its largest
triangle radius. A deterministic collision pass moves whole groups to the
nearest clear honeycomb offset. This preserves membership and readable
symbols but displaces display positions: the median displacement is 0.265
printed inch and the maximum 1.924 inches. Tethers show the source positions;
all positions and group movements are in the receipt. There are no
overlapping symbol circumcircle bounds in the delivered layout.

Each capability has separate editable `locpoint` and hidden `name` layers;
names use 9 physical points. Hex construction guides are also a hidden
editable layer. The Setouchi frame retains the 43.5-inch image, +4.35-inch
printed horizontal shift and lower-left Antarctic terrestrial inset. The
infrastructure's geographic reference is retained separately from display
placement and from the editorial land inset.

Validation passed nine focused interpretation tests, source hash and
record accounting, all 590 triangles' equal side lengths and centroids,
containment inside their hex cells, CDN grouping/offset membership,
collision bounds, radial pattern primitives and clipping, matching hidden
name records, identical geometry across all three options, and all 18
delivered file hashes. All six PDFs are one page at 44 × 19.052559 inches;
the sampled legend PDF embeds Atkinson Hyperlegible. Rendered maps and
legends were inspected, along with the browser review page and enlarged
keys. These are screen and vector checks; physical metallic-paper output
has not been measured.

```sh
make groundstation-capability-studies \
  GENERATED_DIR=build/orbital-technosphere-20261103 \
  CXX=/usr/bin/g++ ASSET_JOBS=2
python3 scripts/verify-groundstation-capabilities.py
```

The build target generates the current native groundstation input if
needed, runs the interpretation tests, exports all six capability sheets,
and validates the delivery. The original KML and high-fidelity GeoJSON
are inputs and are not rewritten by the study builder.

## Randoma11y redesign and MSP speculation 4 / subsequent decisions

The user asked whether the green represented the intended design or the
predicted printed result. Green was an earlier design choice and an
unmeasured attempt to counter the reported violet cast; it was never a
measured prediction of the final hue. The user subsequently rejected green,
requested a different Randoma11y pair for each capability option, and
extended the redesign to the MSP studies. The current recipes supersede
the green palettes described above; those descriptions remain a record of
the earlier proofs.

Use each selected pair's dark member for the ground and its light member
for foreground marks and type. This was the stated working assumption
after the optional palette-role question received no answer. Do not apply
the earlier CMY/green adjustment to these new colors. Land is a 16% blend
of foreground into ground, and muted context a 68% blend. Debris remains
black x marks with a light backing stroke for contrast. Color differences
between vendors give way to the selected foreground hue; editable vendor
groups, marker shapes and illumination opacity remain available.

These pairs were generated on the public Randoma11y website using HEX
format and its default APCA mode. Original browser values, CSS, share
URLs, orientation and application-bundle hash are retained in
[the palette source receipt](../../config/randoma11y-pairs-20261103.json).
The contrast ratios below are independently calculated for the exact sRGB
pair. They describe the source colors, not metallic-paper contrast or
accessibility of the complete plate. Printed hue remains unmeasured with
low cyan and light magenta; blue, violet and amber are design intentions.

| Study / capability option | Design | Ground | Marks and type | Source sRGB contrast |
| --- | --- | --- | --- | ---: |
| MSP 1 / option 1 spokes | [Wine / amber](https://randoma11y.com/%23fcc553/%23240413) | `#240413` | `#fcc553` | 12.03:1 |
| MSP 2 / option 2 rings | [Ultramarine / porcelain](https://randoma11y.com/%23193fb8/%23f5eae7) | `#193fb8` | `#f5eae7` | 7.28:1 |
| MSP 3 / option 3 petals | [Plum / ice blue](https://randoma11y.com/%2373def9/%232a0c41) | `#2a0c41` | `#73def9` | 11.04:1 |
| MSP 4 / adopted petals | [Midnight blue / champagne](https://randoma11y.com/%23ead784/%23010434) | `#010434` | `#ead784` | 13.62:1 |

MSP speculation 4 contains all three subjects with separate map and
legend/attribution sheets:

- **Orbital global:** Starlink's visible NORAD ID layer and hidden full-name
  layer use 7 physical points. Keep the editable `starlink/name`,
  `starlink/id` and `starlink/locpoint` children. Paint the text first,
  then Starlink's own sunbursts, then every other satellite marker group.
  Other vendors retain their hidden names and have no visible ID layer.
- **Both orbital plates:** Starlink uses the sunburst shape at 1.5 times its
  previous linear dimensions, centered on the same satellite position.
  Scale the corresponding legend key too. Observer name visibility and
  type size retain their earlier settings.
- **Groundstations:** adopt the complete `option-3-petals` capability
  visualization, including 590 antenna triangles, 66 PoPs, 124 supplied
  links, all size/status conventions, source-position tethers and separate
  attribution legend. Apply MSP 4's midnight/champagne pair to it.
- **Land order:** Antarctica is basemap artwork, like the other continents.
  Move its inset before the cyclic source window in the shared Setouchi
  framing function so labels and vectors draw above it. Regenerate the
  current MSP and capability studies with that ordering. Keep the
  43.5-inch image and +4.35-inch printed horizontal adjustment.

The staged implementation and review plan is:

1. Save the four actual Randoma11y pairs and replace the green recipes.
   Give each capability option its own pair without changing its records,
   antenna interpretation, triangle sizes or CDN grouping/placement.
2. Correct the shared land ordering. Add the MSP 4 font, marker and paint
   order variant. Reuse the audited petal map and its full legend as MSP 4's
   groundstation source rather than reconstructing a separate inventory.
3. Regenerate six capability sheets and 24 MSP sheets as vector PDF,
   editable SVG.gz and WebP. Update review pages, color/source receipts and
   pass documentation; retain the existing standard products separately.
4. Verify pair provenance and actual SVG paint, record accounting,
   unchanged capability geometry, 7/9 pt global text, 1.5× sunburst geometry
   and fixed centroids, marker order, Antarctic order, page dimensions and
   delivery hashes. Inspect rendered maps, legends and review pages.
5. Append validation results here, then commit and push under the user's
   standing instruction.

### Delivery and validation

The [MSP review page](../../output/msp-speculations-20261103/index.html)
now contains four studies and 24 map/legend sheets. The
[capability review page](../../output/groundstation-capabilities-20261103/index.html)
contains the three recolored pattern pairs, with enlarged pattern keys.
All 30 sheets have PDF, SVG.gz and WebP companions: 90 delivered files.
The source pairs are linked on the review pages and printed on the legends.

Validation passed for all output hashes, unique SVG IDs, source accounting,
cyclic framing, palette receipt and actual SVG paint, and single-page PDF
dimensions of 44 × 19.052559 inches. The capability records, summary and
placement were compared with the preceding committed study and are
identical; the 538 sized / 52 unknown split remains unchanged. Nine focused
source-interpretation tests also pass.

MSP 4's groundstation map and legend preserve option 3's geometry and
text outside the color note. Both orbital variants preserve satellite
positions and non-Starlink marker geometry. All **11,155 global** and
**549 observer** Starlink sunbursts, plus their legend keys, are exactly
1.5× in linear size about the original centroids. The global name/ID text
measures 7 physical points; studies 1–3 remain 9 points. The observer's
hidden name geometry and type size are unchanged. The final SVG ordering
puts all global satellite markers after Starlink text and all Antarctic
land before the data window. Black debris x marks and the existing shape
rules remain intact.

Rendered maps, legends and both complete browser overviews were inspected.
All 30 WebP images loaded at their expected 3840-pixel width, with no browser
runtime errors or horizontal overflow at the reviewed 1600-pixel viewport.
The review pages' 127 local links/image references resolve. Sampled MSP 4
PDFs embed Atkinson Hyperlegible. The documentation checker passed 166
files and 1,771 local links; the existing ToT snapshot check also passed.
These checks validate source files and digital delivery, not the final
printed hue on the unmeasured printer/paper combination.

```sh
make msp-speculations \
  GENERATED_DIR=build/orbital-technosphere-20261103 \
  CXX=/usr/bin/g++ ASSET_JOBS=2
python3 scripts/verify-msp-speculations.py
python3 scripts/verify-groundstation-capabilities.py
```

The MSP target now builds and verifies the capability studies before using
the petal source. Its receipt records the adopted capability manifest and
evidence hashes, and distinguishes the deliberate MSP 4 geometry/type
changes from the subsequent color-only operation.
