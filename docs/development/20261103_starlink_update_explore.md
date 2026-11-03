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
Observer SVGs were regenerated and checked locally; the website's observer
previews retain their older capture.

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
