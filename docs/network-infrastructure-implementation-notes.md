# Network-infrastructure generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Source profiles](../assets.static/network-infrastructure/README.md)

## Outcome

Stage 9 is implemented as one C++20 `generate-network-infrastructure` program
with two products:

- the ordinary **sites** product maps located cloud and CDN records and is part
  of `make all`; and
- the explicitly requested **topology** product adds TeleGeography submarine
  cable routes, landing points, Internet-exchange facilities, and logical
  exchange-to-facility membership.

Both products use the six production projections, Natural Earth land context,
Atkinson Hyperlegible labels, deterministic Izzi radial-hexagon detiling, SVG
provenance, and SVG/PDF/PNG artifact targets. The topology product is not a
dependency of `make all` and cannot be selected accidentally through profile
`"all"`.

## Feasibility and audited source snapshots

The three sources are structurally compatible once their meanings remain
separate:

| Source | Pinned snapshot | Implemented evidence |
| --- | --- | --- |
| [`bdekoz/cloud_cdn_cache`](https://github.com/bdekoz/cloud_cdn_cache) | commit `1be1eb04e73320e0337a74a99686cd532f09ad9b`, manifest dated 2026-08-05 | 28 canonical layers, 27,378 records, 1,003 rendered provider-declared Point records |
| [TeleGeography Submarine Cable Map](https://github.com/telegeography/www.submarinecablemap.com) | content snapshot `v3.20260805` | 697 cable systems, 718 route features, 1,930 route parts, 28,150 vertices, and 1,922 landing points |
| [TeleGeography Internet Exchange Map](https://github.com/telegeography/www.internetexchangemap.com) | commit `2b9c36ad7fad083c0b4db998c4dedadc1ba89027`, 2022-09-20 | 1,772 geolocated facilities, 1,103 exchanges, and 2,581 source membership entries |

The cable source's `MultiLineString` features are source-drawn physical route
geometry. Cable detail records supply the source's planned flag, RFS year, and
landing memberships. The snapshot contains 91 systems marked planned and 606
not marked planned. The generator preserves that source status and does not
reinterpret it using the current date.

The Internet Exchange Map is an incidence dataset. It says that an exchange
is present in a building; it does **not** say that two buildings have a direct
fiber link, that participants peer with one another, or that a particular
route carries traffic. Building `18438` repeats one São Paulo exchange entry,
so the generated metadata records 2,581 raw entries, 2,580 unique incidences,
and one duplicate. The relationship is rendered once.

The two facilities carrying each of `minap-milan-italy` and
`netix-milan-italy` have distinct source records but identical coordinates.
Those two incidences are retained as co-located logical hubs with their
building counts and semantic metadata; no zero-length or invented route is
drawn. SVG metadata records the number of such co-located groups.

The selected cloud snapshot contains 13,631 null-geometry observed presences
and 11,659 geocoded observed presences. They remain part of source totals, but
the ordinary profile excludes both from rendering. Its 1,003 located records
are provider-declared sites, not a connectivity graph.

## Claim boundary

The renderer distinguishes three kinds of evidence:

1. solid cyan or dashed amber paths are source-backed submarine cable route
   geometry, with the dash indicating the source's planned flag and the solid
   group meaning only “not marked planned” in that historical snapshot;
2. dashed magenta spokes are source-backed exchange-to-building membership
   joined through a clearly marked, derived spherical centroid; and
3. point marks are source records for cloud/CDN sites, cable landings, or
   Internet-exchange facilities.

No edge is inferred between a cable landing, an exchange facility, and a
cloud/CDN location. Geographic proximity is not connectivity. Root SVG
metadata states `data-inferred-cross-source-edges="0"`, and the visible legend
states that dashed IX membership is not physical fiber. Display-displacement
tethers produced by clustering carry their own non-network semantics.

The old Alpha60 `augment_carto_composite` routine informed the source-layer
decomposition. Its broad runtime-global composition was not copied. The new
implementation uses strict profile and input validation, current projection
frames, seam-aware paths, named SVG layers, and reproducible artifact checks.

## Source configuration and pinning

The source repositories remain external. The Makefile defaults to sibling
checkouts:

```text
NETWORK_INFRASTRUCTURE_CLOUD_SOURCE=../cloud_cdn_cache
SUBMARINE_CABLE_SOURCE=../www.submarinecablemap.com
INTERNET_EXCHANGE_SOURCE=../www.internetexchangemap.com
```

Override any root without editing code:

```sh
make \
  NETWORK_INFRASTRUCTURE_CLOUD_SOURCE=/data/cloud_cdn_cache \
  SUBMARINE_CABLE_SOURCE=/data/www.submarinecablemap.com \
  INTERNET_EXCHANGE_SOURCE=/data/www.internetexchangemap.com \
  generate-network-infrastructure-topology
```

[`network-infrastructure-sites-profile.json`](../assets.static/network-infrastructure/network-infrastructure-sites-profile.json)
and
[`network-infrastructure-topology-profile.json`](../assets.static/network-infrastructure/network-infrastructure-topology-profile.json)
pin source provenance, relative paths, primary-file SHA-256 digests, the
aggregate digest of all referenced cable detail records, snapshot versions,
exact counts, layer switches, physical marker dimensions, label limits, and
artifact-license notices.

Before generation, `scripts/check-network-infrastructure-sources.sh` checks the
cloud and Internet-exchange revisions and verifies all content digests. The
submarine `v3.20260805` source is accepted by content and does not need to be a
Git checkout: the route index, landing index, and deterministic aggregate of
all referenced cable details must match exactly. The C++ parser then validates
the configured counts and every consumed GeoJSON structure.

The current committed cloud snapshot is used deliberately. Relative to the
preceding audited commit, it grows from 27 to 28 canonical layers and from
15,726 to 27,378 records. The additional layer contains 11,659 geocoded
observed presences. Because the ordinary profile excludes observed scope, its
provider-declared rendered set remains 1,003. The manifest and every referenced
GeoJSON/report agree in the clean Git tree; mutable working-tree data was not
used to establish the pin.

## Normal and opt-in Make workflows

The normal site atlas is generated with:

```sh
make generate-network-infrastructure
make generate-network-infrastructure-artifacts
```

The first command writes six SVGs. The second writes six SVGs, PDFs, and PNGs.
Per-projection targets use `generate-network-infrastructure-PROJECTION`.
The project generation-profile pass name is `network-infrastructure`, with
`infrastructure` accepted as an alias. It always means the non-TeleGeography
site product.

Topology is an explicit license opt-in:

```sh
make generate-network-infrastructure-topology
make generate-network-infrastructure-topology-artifacts
make EXTERNAL_PASSES=network-topology \
  NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
  generate-authorized-external
```

The requested new rule is `generate-network-infrastructure-topology`. Its
`-artifacts` companion adds all PDFs and PNGs, while
`generate-network-infrastructure-topology-PROJECTION` builds one SVG. Source
The authorized wrapper first validates the acknowledgement and every pinned
source, then invokes the `-artifacts` target. Source checks can be run
independently:

```sh
make check-network-infrastructure-sources
make check-network-infrastructure-topology-sources
```

## License boundary

The cloud repository states that its original dataset is ODC-By 1.0 and that
provider snapshots can retain source-specific terms. Both TeleGeography map
repositories state
[CC BY-NC-SA 3.0 Unported](https://creativecommons.org/licenses/by-nc-sa/3.0/).
Consequently:

- generator source remains under cartofreako's GPL-3.0-or-later terms;
- TeleGeography source data is not copied into this repository;
- every topology SVG embeds source commits, hashes, counts, the explicit
  opt-in flag, and the CC license;
- every topology image visibly attributes TeleGeography and states the
  noncommercial/share-alike boundary; and
- topology products are excluded from `make all` and generation-profile
  `"all"`.

The profiles and documentation preserve the cloud source's separate terms as
well. This implementation record describes the distribution boundary; it is
not legal advice or separate commercial permission from TeleGeography.

## Parsing and normalized model

The cloud loader walks only `manifest.layers`, never derived views. For every
canonical layer it verifies the advertised feature count and null-geometry
count, rejects duplicate `record_id` values, accepts only finite WGS84 Points
or null geometry, and retains provider, service, entity type, lifecycle,
source scope, location precision, and name.

The cable loader first discovers unique cable IDs from route features, then
loads the corresponding detail record through a restricted identifier and
relative directory. It verifies every route part has at least two finite WGS84
coordinates, every `feature_id` is unique, every detail ID matches its
filename, and every cable landing membership resolves to a known landing.

The exchange loader requires finite Point buildings, unique building IDs,
nonempty exchange arrays, stable exchange names, and exact pinned raw counts.
Duplicate building/exchange pairs are counted and deduplicated only for
rendering.

## Seam-safe route geometry

Each open route is split explicitly at ±180 degrees and densified to no more
than two degrees per source step. The shared `project_path()` routine then
finds native projection-cell transitions and separates true unfolded cuts.
This prevents a cable or logical membership connector from drawing a false
straight segment across unrelated projection faces.

For a multi-building exchange, the derived logical hub is the normalized mean
of the building unit vectors:

```text
v_i = (cos φ_i cos λ_i, cos φ_i sin λ_i, sin φ_i)
v̄   = Σv_i / |Σv_i|
φ_h = atan2(v̄_z, hypot(v̄_x, v̄_y))
λ_h = atan2(v̄_y, v̄_x)
```

Each source incidence is drawn from that hub to its building with a dashed
stroke and explicit `logical-membership` metadata. This is a display construct
for a source-backed bipartite relation, not a physical route estimate.

## Projection-safe point detiling

Cloud sites, landings, and IX buildings enter one collision layout so unlike
marks cannot hide one another. Each point is projected, assigned its native
projection cell, and binned into a configurable page-space collision cell.
Groups are sorted deterministically by semantic priority and source ID.

The implementation calls Izzi's `radiate_hexagon_honeycomb()` and canonicalizes
its floating-point output onto the routine's radius/√3-radius lattice. It asks
for a bounded surplus, removes numerically duplicate centers, retains the
nearest required centers, and shifts the whole cluster only enough to stay in
the map frame. A thin optional tether connects a displaced mark to its true
projected point and is explicitly labeled as display displacement.

Clustering changes neither coordinates stored in source metadata nor topology.
Cable lines and logical membership paths always terminate at true projected
coordinates and are never clustered.

## SVG layer and mark contract

Every product contains the same discoverable group vocabulary, with disabled
topology groups empty in the sites product:

```text
network-infrastructure-background
terrestrial-land
submarine-cables
  submarine-cables-not-planned
  submarine-cables-planned
internet-exchange-membership
  internet-exchange-logical-hubs
infrastructure-cluster-tethers
cloud-cdn-sites
landing-points
internet-exchange-buildings
submarine-cable-labels
infrastructure-labels
network-infrastructure-legend-and-provenance
```

Edge POPs use amber hexagons; data centers use cyan squares; regions and zones
use violet diamonds or triangles; cable landings use cyan circles; and IX
facilities use magenta squares. Raw source IDs, entity types, names, provider,
membership counts, native cells, cluster sizes, and true projected coordinates
remain machine-readable on the marks.

## Products

Normal site-atlas previews:

| Projection | PNG |
| --- | --- |
| Cahill-Keyes | [`network-infrastructure-sites-ck-44-22.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-ck-44-22.png) |
| AuthaGraph | [`network-infrastructure-sites-authagraph-44-19.052559.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-authagraph-44-19.052559.png) |
| Dymaxion | [`network-infrastructure-sites-dymaxion-44-20.78461.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-dymaxion-44-20.78461.png) |
| Myriahedral | [`network-infrastructure-sites-myriahedral-44-24.75.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-myriahedral-44-24.75.png) |
| Star-X | [`network-infrastructure-sites-star-x-34-44.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-star-x-34-44.png) |
| Voronoi | [`network-infrastructure-sites-voronoi-44-22.916667.png`](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/png/network-infrastructure-sites-voronoi-44-22.916667.png) |

Opt-in topology PNGs are local authorized-generation products. They were not
included in the credential-free v12 S3 object release, so the GitHub Pages
documentation does not publish preview links for them. A future topology
release must upload and verify those objects before adding public URLs.

## Verification and limitations

`make check` verifies both profiles, license gates, dateline splitting,
densification, unique Izzi layouts for cluster sizes 1 through 64, finite
bounded point layouts, logical hub construction, and route generation on all
six projections. Each generator reopens its SVG and checks the viewBox, layer
contract, exact source mark counts, route counts, logical-membership counts,
provenance, license metadata, configured font, invalid XML controls, and
non-finite output.

The cable data is the bounded `v3.20260805` view, while the Internet-exchange
data remains a historical 2022 view. Neither should be presented as live
infrastructure state. A route feature does not encode
capacity, traffic, latency, ownership of each segment, or present operational
health. An IX membership does not enumerate participant ASNs or peering
relationships. Cloud records combine unlike entity types and coverage
methods; 1,003 plotted records are not 1,003 distinct physical buildings.

Useful future work includes periodic licensed TeleGeography refreshes,
participant/ASN evidence from a source with compatible rights, temporal
comparison profiles, capacity fields with explicit units and provenance, and
a separate opt-in co-location-candidate analysis. None should be represented
as observed topology without an appropriate source.
