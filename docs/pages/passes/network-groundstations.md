# Network Groundstations implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md)

## Status and scope

`network-groundstations` is a **standard, default-rendered pass** drawing the
alpha60 Starlink gateway/POP records in every projection. Its checked-in
input lives in `assets.static/network-groundstations`, so ordinary generation
does not need network access.

The dataset is the alpha60 `starlink-global-gateways-pops.20250902` snapshot
(618 records) from
[`bdekoz/alpha60-data`](https://github.com/bdekoz/alpha60-data), vendored with
its SHA-256 pin. Each record is either a gateway `Point` or a
gateway-to-POP `LineString`; the first coordinate of each record is rendered
as the groundstation mark.

## Default rendering

The pass follows the alpha60 Starlink gateway style:

| Layer | Mark |
| --- | --- |
| `starlink-gateway-links` | thin red lines for gateway-to-POP links |
| `starlink-gateways-20250902` | red triangles (`rgb(255,29,16)`) at gateways, fill opacity 0.33 |

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

## Published v14 previews

Network Groundstations is a new v14 pass and is present in all six
whole-map projections of the immutable v14 AAO release:

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
against `SHA256SUMS`. The generator reopens every SVG and checks its viewBox,
required semantic groups, exact groundstation element counts, provenance
metadata, font, and finite coordinates.
