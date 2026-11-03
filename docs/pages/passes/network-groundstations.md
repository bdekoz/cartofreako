# Network Groundstations implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md)

## Status and scope

`network-groundstations` is a **standard, default-rendered pass** drawing the
Starlink gateway/POP records in every projection. Its checked-in
input lives in `assets.static/network-groundstations`, so ordinary generation
does not need network access.

The current input is `starlink-global-gateways-pops.20261103.geojson`, converted
from the supplied **Unofficial Starlink Global Gateways & PoPs** KML snapshot.
It contains 780 records: 656 `Point` features and 124 `LineString` features,
with 1,009 coordinate tuples across 10 source folders. The first coordinate
of each record is rendered as a mark; lines include backbone and community
gateway links as described by the source. Records are retained in source
order, including repeated locations and links. Their presence does not
establish current operation.

The profile selects the input with `source.geojson` and pins both the KML
and GeoJSON hashes. The supplied KML does not identify a repository commit
or a license, so those details are not inherited from the older alpha60
snapshot. The 618-record `20250902` input remains available for historical
products.

## Reproduce the conversion

```sh
python3 scripts/convert-kml-geojson.py \
  assets.static/network-groundstations/starlink-global-gateways-pops.20261103.kml \
  assets.static/network-groundstations/starlink-global-gateways-pops.20261103.geojson
```

The converter uses Python's standard library. Add `--check` to compare the
existing output with a fresh conversion without writing. It preserves
longitude, latitude and altitude without rounding or simplifying; all
source coordinate decimals in this snapshot are verified against the output.

Each feature exposes `Name`, `description` (HTML retained), `styleUrl`,
`folder_path`, and ordered `extended_data` entries. In this input, 294
records repeat custom field names, so entries remain an ordered list with
empty strings preserved. Names, status text, links and Unicode are retained.

The complete Placemark XML information is retained as a JSON tree in
`properties.kml`. Collection-level `kml.document` retains the document and
folder hierarchy, all 118 styles and 59 style maps, and references to features
by `feature_id`. Tree nodes carry namespace-qualified `tag`, optional
`attributes`, `text`, ordered `children` and significant `tail` text. This
also preserves geometry settings such as `tessellate`, original coordinate
text and fields without GeoJSON equivalents. XML formatting whitespace,
namespace prefixes and CDATA wrappers are not retained. URLs remain data;
the converter does not retrieve them.

The converter supports Point, LineString, LinearRing, Polygon and
MultiGeometry inputs and rejects unsupported geometry or NetworkLink inputs
explicitly. Conversion is deterministic and replaces the destination only
after successful validation. After intentionally refreshing the input,
update the profile's feature count, date and hashes, then `SHA256SUMS`.

## Default rendering

The pass follows the alpha60 Starlink gateway style:

| Layer | Mark |
| --- | --- |
| `starlink-gateway-links` | thin red lines for gateway-to-POP links |
| `starlink-gateways-20261103` | red triangles (`rgb(255,29,16)`) at record locations, fill opacity 0.33 |

The group date follows the selected profile. The source's KML styles are
preserved in GeoJSON; rendering continues to use the pass's red symbols.
The legend states `NETWORK GROUNDSTATIONS / <datestamp>` and the record count.
All products use the Stage 13 light-gray background and 2× plate title.

## Build targets and profile selectors

```sh
make generate-network-groundstations
make generate-network-groundstations-artifacts
make generate-network-groundstations-cahill-keyes
```

`network-groundstations`, `groundstations`, and `starlink` are
generation-profile aliases. Because the pass is standard, its six SVG, PDF,
PNG, and Cahill–Keyes snapshot products are part of the ordinary `make all`
graph.

## Antenna capability studies / Setouchi AuthaGraph

The [three capability studies](../../../output/groundstation-capabilities-20261103/index.html)
compare radial spokes, concentric rings and radial petals. Each has a
44 × 19.052559-inch map PDF, a separate Setouchi legend/attribution PDF,
editable compressed SVGs and WebP previews. They use the same dark
MSP speculation 1 palette and the confirmed horizontal AuthaGraph framing.

The studies distinguish **590 antenna-site point records**, **66 PoPs** and
**124 supplied links**. Antenna triangles occupy the centers of invisible
hexagonal cells, using the CDN projected grouping grid and shared honeycomb
offset routine. Cell spacing accommodates each group's largest triangle;
collision displacement is recorded and drawn with source-position tethers.
PoPs remain fixed-size open circles; line endpoints do not acquire antenna
marks in these studies.

For 538 antenna records, triangle area follows the largest complete listed
bank aperture, `max(N × π × D² / 4)`. The remaining 52 have a hollow square
at the triangle center to mark unknown size. Band inventories are never summed. The source includes plans,
partial builds and retired records, so this is a listed-hardware proxy,
not measured throughput or installed capacity. A minimum source radius of
0.04 inch applies to 23 small known records. Patterns encode capability
categories; outlines encode source-reported status.

The [evidence receipt](../../../output/groundstation-capabilities-20261103/capability-evidence.json)
retains raw ordered fields, duplicate-field resolutions, calculation inputs,
exceptions, source IDs, coordinates and display positions. The source has
294 repeated-field sets: populated/blank pairs are reconciled without
discarding the populated value, numerically equivalent values agree, and
conflicting populated values remain unresolved. Three fractional antenna
counts and two composite diameters are excluded from numeric interpretation.

```sh
make groundstation-capability-studies \
  GENERATED_DIR=build/orbital-technosphere-20261103 ASSET_JOBS=2
python3 scripts/verify-groundstation-capabilities.py
```

The three pattern studies are a separate comparison set; the standard
rendering and original MSP color proofs remain available. The detailed
decisions and validation record are in the
[November 3 work log](../../development/20261103_starlink_update_explore.md).

## Published v14 previews

Network Groundstations is a new v14 pass and is present in all six
whole-map projections of the immutable v14 AAO release:

These published previews use the historical `20250902` snapshot. Local
regeneration uses the current profile and does not modify the release.

| Projection | Full PNG |
| --- | --- |
| Cahill-Keyes | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/cahill-keyes/full/network-groundstations-ck-44-22.png) |
| AuthaGraph | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/authagraph/full/network-groundstations-authagraph-44-19.052559.png) |
| Dymaxion | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/dymaxion/full/network-groundstations-dymaxion-44-20.78461.png) |
| Myriahedral | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/myriahedral/full/network-groundstations-myriahedral-44-24.75.png) |
| Star-X | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/star-x/full/network-groundstations-star-x-34-44.png) |
| Voronoi | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/voronoi/full/network-groundstations-voronoi-44-22.916667.png) |

Each product also has a 480-pixel thumbnail, a print PDF, a master
`.svg.gz`, and 1920 × 1080 PNG/WebP derivatives under the same projection
directory.

## Verification

`make check-network-groundstations` verifies every checked static payload
against `SHA256SUMS`, checks reproducible conversion, and runs the converter
tests. The tests compare all coordinates and custom fields with the KML,
reconstruct its XML information from the GeoJSON, and exercise invalid
inputs and output preservation. The generator reopens every SVG and checks its viewBox,
required semantic groups, exact groundstation element counts, provenance
metadata, font, and finite coordinates.
