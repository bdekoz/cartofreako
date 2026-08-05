# Network-swarm generation implementation notes

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Generation methods](generation-methods.md) ·
[Pinned network-swarm data](../assets.static/network-swarm/README.md)

## Outcome and claim boundary

Stage 4.4 is implemented as a reproducible, projection-aware
`generate-network-swarm` pass. It detiles cumulative GeoJSON swarm features,
preserves every raw `properties.downloaders` field, and renders one
network-swarm atlas on each of the six production projections. The result is
a density and access-characteristics map. It is not a graph: the input contains no
source/destination pairs, routes, peer relationships, or measured edges, so
the renderer does not invent them.

The confirmed design uses H3 parent cells to discover local groups and
Izzi's radial hexagon fill to make dense places legible. Clustering changes
only display positions. Optional thin tethers point back to each feature's
true projected coordinate and must not be interpreted as traffic paths.

## Feasibility evaluation and source decision

The supplied cumulative aggregate is a good fit for this pass because every
feature has a geographic Point, a valid H3 index, a common H3 resolution, and
the same downloader object. It is already spatially aggregated and requires
no address-level plotting. The implementation pins the corrected source:

| Property | Pinned value |
| --- | --- |
| Archive | `house-of-the-dragon-301-cumulative-aggregate.geojson.zip` |
| Source repository | `alpha60-devops/alpha60-results-dragons` |
| Source commit | `0eafe44b18215e368074ce78d2354ec881298777` |
| Archive SHA-256 | `ec51be8cafcdc2e009874e2aebd84927dc5c3d87ec589c0fe5d8d1df0818e0b8` |
| GeoJSON SHA-256 | `9fbd453d174df834208718e110396c5a22bff4312aeeff3e42d0175510b0ff69` |
| Dataset and interval | `house-of-the-dragon-301`, 2026-06-22 through 2026-07-26 |
| Duration | `cumulative`, index 0 |
| Partition | H3 resolution 5, minimum downloader `size` 3 |
| Features | 23,825 unique Point features and H3 cells |
| Downloader `size` sum | 19,187,402 |
| License | GPL-3.0-or-later |

The source's top-level `swarm_features_size` is retained verbatim as reported
metadata, but it is not relabeled as the sum of `downloaders.size`; those are
different values with different source semantics. H3 identifiers are parsed
as unsigned 64-bit integers and serialized both as canonical H3 strings and
decimal strings. They are never passed through an IEEE-754 JSON number.

The nine specialized fields overlap. In this snapshot, 210 features have a
specialized-field sum greater than `size`. Consequently `mobile`,
`satellite`, `tor`, `tor_exit_nodes`, `vpn`, `relay`, `proxy`, `hosting`, and
`service` are independent observations, not pieces of a partition or a
stacked total.

## Variable input and bounded preparation

The committed ZIP is the offline default. `scripts/prepare-network-swarm-data.sh`
accepts one local `.zip`, `.geojson`, or `.json` file, so another compatible
source does not require a code change. For ZIP input it requires exactly one
flat, safely named JSON member, validates the archive CRC, and caps expanded
content at 64 MiB. Preparation is atomic and does not change the destination
timestamp when the bytes are already current.

```sh
make prepare-network-swarm-data
make generate-network-swarm
```

Override the source or the prepared destination explicitly:

```sh
make NETWORK_SWARM_SOURCE=/absolute/path/cumulative.geojson.zip \
  prepare-network-swarm-data generate-network-swarm
```

`NETWORK_SWARM_SOURCE` may point directly to an already uncompressed
`.geojson` or `.json`; the same bounded staging and content comparison still
apply.
`NETWORK_SWARM_GEOJSON` changes the staging destination rather than bypassing
preparation.

The parser intentionally requires the implemented cumulative swarm contract:
a `FeatureCollection`, hexagon partition metadata, a uniform valid H3
resolution, unique H3 cells, Point coordinates in range, and unsigned values
for all ten downloader fields. Missing, malformed, duplicate, or inconsistent
data stops generation rather than silently becoming zero.

## Configuration profile

[`network-swarm-profile.json`](../assets.static/network-swarm/network-swarm-profile.json)
owns the decisions that may reasonably change between captures:

- source and parent H3 resolutions;
- marker radius and tether threshold in physical inches;
- label budget, nonzero opacity floor, and tether visibility;
- fixed per-field scale references; and
- archive/member names, both digests, repository commit, and license.

The default groups H3 resolution-5 cells under resolution-3 parents. The raw
snapshot has 4,404 such parents, a median of two features per parent, a
90th-percentile group size of 14, and a largest group of 48. Resolution 4
mostly produces singletons, while resolution 2 creates groups as large as
266; resolution 3 was selected as the useful compromise.

Fixed scale references are snapshot nonzero 99th percentiles. A value `v`
and reference `q` produce

```text
u = clamp(log(1 + v) / log(1 + q), 0, 1)
opacity(v) = 0                         when v = 0
opacity(v) = m + (1 - m)u             otherwise
```

where the default nonzero floor `m` is 0.18. Fixed references make maps and
future compatible snapshots visually comparable; one extreme city cannot
rescale every other mark. Raw counts remain attached to SVG elements, so the
perceptual transform does not replace source data.

## H3 and projection-safe honeycomb placement

Clustering follows this deterministic sequence:

1. validate every source cell and verify its H3 resolution;
2. compute `cellToParent(source, 3)`;
3. split each parent group by the selected projection's native face/cell;
4. project all true coordinates and average each component in page space;
5. sort component members by descending `downloaders.size`, then H3 ID;
6. request center-filled positions from Izzi's
   `radiate_hexagon_honeycomb()` and put the largest value at the center; and
7. shift an entire cluster just enough to keep its marks inside the frame.

Step 3 is essential for unfolded maps. Two geographically local cells can
land on opposite sides of a projection cut; placing them in one page-space
honeycomb would create a false cross-seam group. On Cahill-Keyes, the 4,404
raw parents become 4,418 projection-safe components.

Izzi's routine walks neighbors with basis directions derived from
`(2r, 0)` and `(r, sqrt(3)r)`. Its current floating-point hash and epsilon
equality policies can admit numerically equivalent centers through different
BFS paths. The adapter requests a bounded surplus, canonicalizes returned
coordinates onto the routine's own `r`/`sqrt(3)r` lattice, rejects
non-finite values, verifies uniqueness, and retains the nearest required
centers. This integrates the shared radial-fill algorithm without allowing a
duplicate display cell to hide a source feature.

## Visual system and semantic layers

The visual research suggested a restrained atlas rather than a simulated
network diagram. Arjen van Susteren's *Metropolitan World Atlas* informed the
consistent framed comparison and standard mark grammar. Lucille Tenazas's
[MNL–SF–MINY–SF2–ROME–NY2 work](https://2023.agi-open.com/speakers/lucille-tenazas)
informed the dark field, limited accent palette, and structured date band.
The concrete downloader glyph vocabulary begins with Alpha60's
[`augment_swarm_features_geojson`](https://github.com/bdekoz/alpha60/blob/da07af121a20cb9f696b057e1425e82055b92cc3/src/a60-carto-geo.cc)
prior art and extends it to all current object fields.

| Field | Encoding |
| --- | --- |
| `size` | Full honeycomb hexagon; log-scaled blue-to-amber intensity |
| `mobile` | Green center disk |
| `satellite` | Crimson center triangle |
| `hosting` | Violet outer hexagon outline |
| `service` | Pink ring |
| `vpn` | Cyan diamond outline |
| `tor` | Orange upper-left mini-hexagon |
| `tor_exit_nodes` | Pale-yellow upper-right square |
| `relay` | Periwinkle slash |
| `proxy` | Pale crossed slashes |

All projections contain the same discoverable layer contract:

```text
network-swarm-background
terrestrial-land
cluster-tethers
downloaders-total
access
  downloaders-mobile
  downloaders-satellite
infrastructure
  downloaders-hosting
  downloaders-service
privacy-routing
  downloaders-vpn
  downloaders-tor
  downloaders-tor-exit-nodes
  downloaders-relay
  downloaders-proxy
labels
legend-and-provenance
```

The dark ocean and subdued Natural Earth land preserve geographic context
without competing with the marks. Labels are a deterministic, collision-grid
bounded selection from the largest totals. Every base feature stores its H3
IDs, parent, projection cell, cluster size, country, city, GeoNames ID, and
all ten raw downloader counts. Root metadata stores source digests, source
commit, interval, data version, counts, cluster statistics, and projection.

## Products

`make generate-network-swarm` writes the six layered SVGs. `make
generate-network-swarm-artifacts` adds the matching PDF and
3840-pixel-long-side PNG files. Each PNG below links to the generated review
artifact:

| Projection | Network-swarm preview |
| --- | --- |
| Cahill-Keyes | [`network-swarm-ck-44-22.png`](../assets.generated/png/network-swarm-ck-44-22.png) |
| AuthaGraph | [`network-swarm-authagraph-44-19.052559.png`](../assets.generated/png/network-swarm-authagraph-44-19.052559.png) |
| Dymaxion | [`network-swarm-dymaxion-44-20.78461.png`](../assets.generated/png/network-swarm-dymaxion-44-20.78461.png) |
| Myriahedral | [`network-swarm-myriahedral-44-24.75.png`](../assets.generated/png/network-swarm-myriahedral-44-24.75.png) |
| Star-X | [`network-swarm-star-x-34-44.png`](../assets.generated/png/network-swarm-star-x-34-44.png) |
| Voronoi | [`network-swarm-voronoi-44-22.916667.png`](../assets.generated/png/network-swarm-voronoi-44-22.916667.png) |

Per-projection targets use `generate-network-swarm-PROJECTION`. The canonical
project-generation profile name is `network-swarm`; the former `network` name
and short `swarm` name remain input aliases.

## Verification and limitations

`make check` verifies both source digests, exact snapshot metadata and totals,
overlapping category behavior, H3 parent statistics, one-to-one honeycomb
positions for cluster sizes 1 through 48, and bounded finite layouts on all
six projections. Every generator also reopens its SVG and checks the viewBox,
complete layer vocabulary, provenance metadata, exact base feature count, and
absence of non-finite output.

The atlas remains subject to source semantics and collection bias. A
cumulative interval does not show simultaneity, rate, direction, bandwidth,
or causation. City labels and H3 centroids are aggregate annotations, not
precise endpoint locations. Specialized classifications can overlap, and
their source methodology is not re-derived by this renderer. Comparisons
across future snapshots are meaningful only when collection coverage,
duration, minimum threshold, H3 resolution, and classification methods are
compatible.

Future work worth investigating includes a time-aligned snapshot series,
uncertainty and missing-coverage fields, configurable privacy suppression,
and genuine origin/destination or autonomous-system flows when an input with
explicit edge semantics is available. Those would be new data contracts,
not inferred extensions of this cumulative Point collection.
