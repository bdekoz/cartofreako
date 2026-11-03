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
