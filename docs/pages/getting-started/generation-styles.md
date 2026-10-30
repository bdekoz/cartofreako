---
layout: default
title: Default generation styles
---

# Default generation styles

[Documentation index](../README.md) · [Generation guide](generation.md) ·
[Generation methods](generation-methods.md)

The styles approved during the Setouchi 2028 review are the defaults for
ordinary Cartofreako regeneration. They are saved in
[`generation-style.json`](../../../generation-style.json), used by the native
generators and the CDN, swarm and Japan detail builders. No script or file
under `output/setouchi-triennale-2028/` is required to generate them.

[`generation-profile.json`](../../../generation-profile.json) selects which
passes to run. Its development selection is AuthaGraph, Earth and Water.
The standalone renderers also default to AuthaGraph; explicitly selected
projections retain their own geometry and use the same physical style values.

## Reviewed defaults

| Plate or layer | Default encoding |
| --- | --- |
| Network fiber | Oceanic and ITU terrestrial routes: **0.5 pt, 75% opacity**. ITU routes use Kelly green `#4cbb17`. |
| Japan fiber | Same physical route stroke; landing radius is half the earlier enlarged symbol, with a **0.5 pt** outline. |
| Water | Rivers: **0.75 pt globally**, **1.5 pt in Japan**, 85% opacity. |
| Japan coastlines | **1 pt**, including Water's separate coastline layer. |
| Resources | **100% fill opacity**, with separate named `izzi-hue` colors for each metric. No white mixing or opacity tints. Petroleum uses browns; solar uses yellow through orange. The JSON records all 70 resource colors without reuse. |
| Installed solar capacity | Six classes: **0–<100, 100–<1,000, 1,000–<10,000, 10,000–<50,000, 50,000–<200,000 and ≥200,000 MW**. Missing countries stay neutral. The visible key is generated from the saved boundaries. |
| New daily high records | **1–5, 6–10, 11–20, 21–40, 41–80 and ≥81 days** per H3 cell. Yellow at low counts, orange through dark red at high counts; zero remains neutral. Complete and partial years share the same count classes. |
| Cloud / atmosphere | Opaque pink cloud classes, blue precipitation, separate aerosol and shortwave outlines. Foreground land has **0 fill opacity**; visible coastlines remain above the data. |
| Coral threat | Radial honeycombs on a **0.16 in** grouping grid, up to **61 displayed cells** per group. Every source membership and threat class is retained; capped groups preserve the class mix and every present class. Symbol footprints are not reef area. |
| CDN | Alpha60 vendor-reel r8 colors, **33% fill** honeycombs, a **320-record** display cap, approximate-reference triangles, separate locality claims and restrained labels. |
| Network swarm | Native **alpha60-carto-geo** weighted member circles, **5% opacity**, Dan Da Dan 210. **1080p/4K and 720p/SD are separate plates**. Japan retains the world plate's physical circle areas. |

The shared resource opacity takes precedence over the legacy `display` opacity
field in source profiles. Source years, units, coverage, classification rules
and observations remain controlled by their source profiles.

## Generate and export

From the repository root:

```sh
make generation-plan
make
make generate-network-fiber-authagraph generate-network-cdn-authagraph
make generate-network-swarm-authagraph
make generate-resources-fauna-reefs-authagraph
make generate-japan-detail \
  JAPAN_SOURCE=assets.generated/authagraph/svg/water-authagraph-44-19.052559.svg
```

`generate-network-swarm-PROJECTION` creates both resolution bands. For existing
catalog consumers, `network-swarm-PROJECTION...svg` is the 1080p/4K plate, with
an identical explicit `network-swarm-ge-1080p-PROJECTION...svg` alias.
`network-swarm-lt-1080p-PROJECTION...svg` is the 720p/SD plate. The standard
artifact manifest includes both bands across all six projections.

Normal PDF and PNG targets use the bounded-memory native swarm exporter:

```sh
make assets.generated/authagraph/pdf/network-swarm-authagraph-44-19.052559.pdf
make assets.generated/authagraph/pdf/network-swarm-lt-1080p-authagraph-44-19.052559.pdf
```

Each command creates both a vector PDF and the corresponding PNG at
`PNG_LONG_SIDE` (3840 by default). For a 300 dpi print and preview from an
existing world or Japan swarm SVG:

```sh
python3 scripts/export-native-swarm.py path/to/swarm.svg \
  --pdf path/to/swarm.pdf --png path/to/swarm.png \
  --preview path/to/swarm-preview.png --dpi 300
```

The exporter preserves every circle, its paint order, transforms and clips.
It renders at most 50,000 circles at a time and writes a conservation receipt.
Japan details use `JAPAN_OUTPUT` and `JAPAN_PROJECTION` overrides when needed;
the builder rejects celestial sheets, which require observer-specific sky
generation instead of a geographic crop.

## Source and build requirements

CDN sources are pinned separately in
[`config/cdn-sources.json`](../../../config/cdn-sources.json): the approved
`cloud_cdn_cache.bkoz` manifest dated **2026-10-21**, its digest, and the Alpha60
city, area and country reference files. Paths are relative to that config
file. Set `CDN_SOURCE_PROFILE` to use a reviewed alternative snapshot. The
canonical loader verifies the pinned files and writes record, locality and
display-group ledgers under `build/default-styles/`.

Swarm defaults read
`../alpha60-samples-cache/dan-da-dan-210.cache/cache.20260304.tar.xz` and
`../geoip-databases/ipinfo/standard_location.mmdb`. The archive remains local;
only cumulative JSON documents are extracted. Override
`NATIVE_SWARM_CACHE_ARCHIVE`, or set `NATIVE_SWARM_CACHE_DIRECTORY` to an
already extracted cumulative cache, and `NATIVE_SWARM_GEOLOCATION_DB` as needed.
Source archives and generated private cache contents are not committed.

The native adapter compiles against Alpha60 and Izzi (`ALPHA60_SRC`,
`IZZI_SRC`). It additionally needs H3, libtorrent-rasterbar, geolite2++,
libmaxminddb and OpenSSL. The compile helper accepts `LIBTORRENT_PREFIX` and
`GEOLITE2PP_PREFIX`; local defaults are `~/bin/H-libtorrent` and
`~/bin/H-geolite2pp`. Python composition uses lxml; native exports use PyGObject,
librsvg, Pycairo and Pillow. Japan legend placement also uses Inkscape.

The older GeoJSON/H3 swarm renderer remains available as a historical API and
fixture test. The ordinary swarm Make targets use native Alpha60. Similarly,
the legacy network topology API retains its separate source profiles and
authorization workflow; the ordinary CDN targets use the pinned vendor reel.

## Maintain and verify

Edit `generation-style.json`, then run:

```sh
python3 scripts/compile-generation-style.py
make check-generation-style
```

The generated, tracked
[`src.generate/generation-style.h`](../../../src.generate/generation-style.h)
keeps direct C++ builds consistent with Python renderers. Make also regenerates
the header automatically. Temperature and solar keys follow the saved bounds.
The compiler rejects invalid opacities, unordered bounds, repeated resource
colors and coral caps that cannot retain all four classes. Native Alpha60's
5% swarm opacity is currently an upstream invariant checked at compilation.

Verification on 2026-10-30 reproduced all **844 coral groups and 7,215 source
memberships**, **28,243 CDN records**, **2,804,935 high-band and 876,541 low-band
native circles**, and **144,555 high-band circles visible in the Japan crop**.
CDN was also regenerated in Star-X. Tests cover physical Japan strokes and
circle areas, honeycomb class conservation, style validation and pixel equality
between an unsplit swarm fixture and the ordered-layer exporter.

The reviewed Setouchi delivery and its receipts remain a frozen edition.
Future source refreshes use these defaults; source updates do not require
reapplying exhibition-specific styling scripts.

The [world and Japan review gallery](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/)
shows the complete Setouchi edition as 38 plate pairs, with zoomable screen
copies and downloadable feedback. It provides a visual reference for these
defaults; source dates remain those recorded in the delivery.
The [review guide](../gallery/setouchi-2028.md) explains the feedback workflow,
screen copies, print deliverables and source inventory.

## Setouchi ST2 print layout

The [second Setouchi revision](../../development/20261030_setouchi_triennale_explore_2.md)
saves the subsequent print-layout decisions in the ST2 composition scripts.
Regenerate the edition with:

```sh
make setouchi-st2 ASSET_JOBS=4
```

This reads the pinned first delivery at `output/setouchi-triennale-2028/`
and its local source caches, then writes
`output/setouchi-triennale-2028-st2/`. Override `SETOUCHI_ST2_SOURCE` and
`SETOUCHI_ST2_OUTPUT` to select equivalent local delivery locations. The
command rebuilds legends, source bibliographies, map/legend sheets, exports,
the review index, framing comparisons and aggregate PDF, then validates the
result. It reuses the recorded observations; it does not fetch new data.

The saved presentation settings are:

- Separate map and legend/source sheets for all 38 world/Japan pairs.
- Separate World and Japan PDFs, each with 79 pages. Both start with a
  44-inch title sheet containing only `CARTOFREAKO` and the date, in bold
  type independently fitted to the 43.5-inch printable width. The build date
  defaults to the current date in Los Angeles; set
  `SETOUCHI_ST2_DATE=2026-10-30` to reproduce this title date.
- A centered 43.5-inch map image on a 44 × 19.052559-inch sheet. Proportional
  scaling is 98.863636%; physical strokes scale with the artwork, while
  opacity is retained. The original 0.5 pt fiber strokes print at 0.494318 pt.
- The approved +4.35-inch printed horizontal move and consolidated lower-left
  Antarctica on the world fiber and groundstation maps. Companion legends
  explicitly describe the deliberate Antarctic displacement.
- Atkinson Hyperlegible legends based on the supplied rare-earth reference,
  with each plate's source bibliography alongside the key.
- Plate numbers 01–38, shared by world and Japan companions, in 36 pt bold,
  white fill, black 0.5 pt outline and 100% opacity. The footer is number only.
- An aggregate ordered world map, world legend/sources, Japan map, Japan
  legend/sources for each subject. No bibliography is appended at the end.

The separate PDFs are `setouchi-tri-explore-v2-world.pdf` and
`setouchi-tri-explore-v2-japan.pdf`; the combined 155-page edition remains
`setouchi-tri-explore-v2.pdf`. Each edition has its own page index following
the title page and edition notes. Individual sheet numbering stays 01–38.

Full-size masters are under `maps/{world,japan}/` and
`legends/{world,japan}/`, with `svg`, `pdf`, `png` and `preview` subdirectories.
Standard filenames under `plates/{world,japan}/{svg,pdf,png}/` resolve to
these same separate sheets. For example,
`anthropocene-temperature-2025-authagraph-44-19.052559.png` contains only
cartography/data; its `-legend.png` companion contains the legend and data
bibliography. The same pairing applies to all 76 world/Japan maps and their
previews. Combined composition intermediates live only under
`sources/composition/`, outside the public plate folders.

`scripts/publish-setouchi-plate-files.py` binds all 608 standard filenames
to the verified separate SVG, PDF, PNG and preview files. The Make target
publishes these after export, and final validation checks every binding and
checksum. Use `python3 scripts/publish-setouchi-plate-files.py --check` to
audit an existing delivery without regenerating it.
The current network proof is under `proofs/43p5-antarctica-left/`; the
`prototypes/africa-framing/` variants retain the earlier comparison study.

The build needs Python 3.11 or later, lxml, Shapely, Pillow and ReportLab;
Inkscape, Fontconfig and Poppler (`pdfinfo`, `pdfunite`); and the native swarm
export dependencies described above. `build/generation-context` uses the
usual C++/GDAL build dependencies. The bundled
[Atkinson Hyperlegible fonts](../../../assets/fonts/atkinson-hyperlegible/README.md)
are checksum-verified and selected through repository-local Fontconfig.
All 152 SVGs, PDFs and 300 dpi PNGs passed the layout, source, geometry and
export checks recorded in `sources/sheets-validation.json` for this edition.
