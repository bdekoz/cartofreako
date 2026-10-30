# Network-swarm generation

[Documentation index](../README.md) ·
[Generation guide](../getting-started/generation.md) ·
[Default generation styles](../getting-started/generation-styles.md) ·
[Historical aggregate renderer](../history/network-swarm-aggregate.md)

## Default renderer and source

Ordinary `generate-network-swarm` targets use **alpha60-carto-geo's native
weighted member circles**, with the selected Cartofreako projection. The
standalone default is AuthaGraph. The adapter reuses Alpha60 cache ingestion,
unique BTIH coalescing, weighting, member colors and native circle geometry.

The default media collection is **Dan Da Dan 210**. Its local cache is
`../alpha60-samples-cache/dan-da-dan-210.cache/cache.20260304.tar.xz`:
383 cumulative documents covering 2025-09-04 through 2026-03-04. Generation
produces separate **1080p/4K** and **720p/SD** sheets. Each circle retains its
native radius and color at **5% fill opacity**. Observations across torrents
are not counts of unique people, connections or traffic.

The high partition contains 2,804,935 native circles; the low partition
contains 876,541 for this cache. These are verification counts for the pinned
source, not limits or sampling quotas for another input.

## Generate, export and make Japan details

```sh
make generate-network-swarm-authagraph
make generate-network-swarm-artifacts
```

The first command generates both AuthaGraph bands; the second generates the
six projection pairs and their PDF/PNG companions. Override
`NATIVE_SWARM_CACHE_ARCHIVE`, `NATIVE_SWARM_CACHE_DIRECTORY` or
`NATIVE_SWARM_GEOLOCATION_DB` to select local source inputs. Source archives
are extracted into ignored build storage. The native renderer caches results
using its binary, geolocation database, archive digest and input-file
fingerprints; changed inputs invalidate that cache.

For compatibility with existing catalog identifiers, the unqualified
`network-swarm-...svg` filename contains the **1080p/4K** sheet. It is identical
to the explicit `network-swarm-ge-1080p-...svg` alias. The other sheet is
`network-swarm-lt-1080p-...svg`. Both bands appear in the standard artifact
manifest and normal PDF/PNG/thumbnail build rules.

```sh
make generate-japan-detail   JAPAN_SOURCE=assets.generated/authagraph/svg/network-swarm-authagraph-44-19.052559.svg
```

Japan enlargement preserves the physical area of each world circle and the
5% opacity, clips to the geographic viewport and keeps coastlines at 1 pt.
For this source, 144,555 high-band circles intersect the Japan viewport. The
crop includes neighboring countries; it is not a Japan-only total.

PDF/PNG exports use [`export-native-swarm.py`](../../../scripts/export-native-swarm.py).
It splits rendering into ordered layers of at most 50,000 circles while
retaining geometry, transforms, clipping, CSS and paint order. It refuses
unsupported group compositing that would change results at a split boundary.
The PDF stays vector, and PNG resolution is controlled by `PNG_LONG_SIDE` or
an explicit `--dpi`. No circle is sampled away. Source and export receipts
record counts and SHA-256 digests.

## Build and verification

The [default styles guide](../getting-started/generation-styles.md#source-and-build-requirements)
lists native and Python dependencies, source overrides and print commands.
The key implementation files are
[`generate-native-swarm.cc`](../../../src.generate/generate-native-swarm.cc),
[`generate-native-swarm.py`](../../../scripts/generate-native-swarm.py),
[`generate-japan-detail.py`](../../../scripts/generate-japan-detail.py) and
[`generation-style.json`](../../../generation-style.json).

`make check-generation-style` checks physical crop scaling and pixel equality
between full and partitioned fixture renders. Real-cache verification also
compares native world counts, circle geometry, opacity, Japan-visible counts
and export conservation receipts.

The older GeoJSON/H3 aggregate renderer remains available directly through
`src.generate/generate-network-swarm PROJECTION PROFILE.json INPUT.geojson`,
with its source and layout tests retained. Its historical source/profile
variables no longer select the default Make renderer.
