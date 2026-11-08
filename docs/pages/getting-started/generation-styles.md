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
generators and the CDN, swarm and Japan detail builders. These layer generators
do not require files under `output/setouchi-triennale-2028/`.

The **current default atlas** uses the **2026-11-03 MSP 5 settings** with
**wine/amber** selected: `#240413` ground and `#fcc553` text. The `atlas`
section of the same JSON selects the approved recipe and saves the Setouchi
frame, map/legend sequence, PDF selection, title typography and 300 dpi
exports. Data colors remain distinct. `make atlas` applies this presentation
to the current **39 default World/Japan subjects**, with **156 separate
map/legend sheets**. The dated ST2 and MSP deliveries remain inputs. The
November 8 review verified all 156 SVG/PDF/PNG sheets. The current catalog
also contains 14 optional prototypes, including the completed Stage 1/2
climate reviews. Aggregate-book assembly still needs the catalog-size update
described below; the individual sheet exports are complete.

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
| Network swarm | Native **alpha60-carto-geo** weighted member circles, **5% opacity**, Dan Da Dan 210. **1080p/4K and 720p/SD are separate plates**. Japan retains the world plate's physical circle areas. Location names use fill only, with **0 stroke width**, in both scopes and resolutions. |

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
provides the frame and the [MSP 5 review](../../development/20261103_starlink_update_explore.md)
provides the wine/amber presentation. The [completed November 8 record](../../development/20261108_anthropocene_ocean_temperature_stage_1.md)
updates the selection to **39 defaults**, numbered **01–39**, with World/Japan
map and separate legend/source sheets: **78 maps and 78 legends**.

The [current catalog](../../../config/atlas-plates.json) groups historical
coral-reef threat under Anthropocene and petroleum studies under Energy.
Minerals include distinct rare-earth, lithium and uranium colors, with a
separate comparison plate. Bathymetry remains optional. The selected
solar/atmosphere plate uses the saved November 6/7 H3r5 treatment: amber
ground, white coastlines and 100 opacity bands over 0–400 W/m².

The shared composition retains the 44 × 19.052559-inch sheet, 43.5-inch
centered map image, approved world displacement, Atkinson Hyperlegible,
wine `#240413` and amber `#fcc553`. Measured palettes and source coordinates
remain defined by the individual products. Each separate legend carries
its own source dates, units and interpretation.

The MSP 5 inputs retain the reviewed groundstation petals, aperture proxies,
full-opacity fiber links, 6 pt Starlink labels, 1.5× sunbursts, vendor symbols
and 12 pt all-sky labels. Japan's orbital observer retains its October 29
positions. The recipe remains in
[`config/msp-speculations-20261103.json`](../../../config/msp-speculations-20261103.json);
the alternate reviewed palettes are ultramarine/porcelain, plum/ice and
midnight/champagne. These RGB settings are not printer calibration profiles.

### Build stages and validation status

The current delivery has **156 verified SVG/PDF/PNG sheets**. Its inputs
include the retained Setouchi/ST2 and MSP editions and November mineral
supplements. These local sources must be available before composition;
see the [Stage 1 reproduction record](../../development/20261108_anthropocene_ocean_temperature_stage_1.md#reproduction-and-verification).

```sh
make atlas-sheets
python3 scripts/build-atlas-defaults.py --output output/atlas --check --skip-exports
python3 scripts/export-setouchi-sheets.py --delivery output/atlas --workers 3
python3 scripts/build-atlas-defaults.py --output output/atlas --check
```

`ATLAS_SOURCE`, `ATLAS_BASE` and `ATLAS_OUTPUT` select the input edition,
composition intermediates and output directory. Defaults are the retained
first Setouchi delivery, `build/atlas-st2-base/` and `output/atlas/`. A complete
existing ST2 base can also be reused directly:

```sh
python3 scripts/build-atlas-defaults.py \
  --source output/setouchi-triennale-2028-st2 --output output/atlas
```

The map/legend folders and export receipts are local build products. Ordinary
sheet validation checks hashes and geometry without fetching new data.

| Receipt under `output/atlas/sources/` | Current scope |
| --- | --- |
| `atlas-presentation.json` | Saved settings, source/configuration hashes and all 156 SVG records |
| `sheet-export-manifest.json` | All 156 individual PDF/PNG/preview exports |
| `sheets-validation.json` | Passed 156-sheet verification, including subject presentation checks |
| `atlas-catalog.json` | The 53-name catalog: 39 defaults and 14 optional prototypes |

**Aggregate PDF books remain deferred.** The final assembly used by
`make atlas` still asserts the historical 38-subject/152-sheet inventory in
`scripts/build-setouchi-revision-review.py`. Its 75-page per-scope and
147-page combined counts describe the earlier 36-subject PDF selection,
which omitted Bathymetry. They are not completion claims for the current
39-subject books. The catalog-size update, current filename bindings and
new aggregate-book verification are recorded in the
[follow-up note](../../development/20261108_documentation_followup.md).

The completed [Stage 2 review](../../development/20261108_anthropocene_ocean_temperature_stage_2.md)
has a separate optional delivery: eight year identities, 32 measure/period
views and 128 map/legend sheets. It uses the same presentation system with
measure-specific keys and its own explicit build targets. World/Japan scopes
apply to ocean/coastal views; the India pilot uses World/India. Neither this
review nor the current default-atlas composition is part of `make all`'s
standard native projection graph.

### Setouchi application edition (ST31–ST33)

To assemble the revised World/Japan covers and indexes, the ten-page A4
application, the complete two-page CV converted to A4, and a WordPress draft:

```sh
make setouchi-v3 SETOUCHI_V3_DATE=2026-11-01
```

This reads the completed `output/setouchi-triennale-2028-st2/` delivery and
writes `output/setouchi-triennale-2028-v3/`; it preserves the existing map
and legend PDFs. The [ST3 proposal record](../../development/20261101_setouchi_triennale_proposal.md)
documents the application, source materials, canonical WordPress page 3175,
validation and publication handoff. Ghostscript is required for the full CV
conversion. The builder and validator also produce an offline HTML index,
source receipts and checksums. No WordPress write is part of this Make target.

The build needs Python 3.11 or later, lxml, Shapely, Pillow and ReportLab;
Inkscape, Fontconfig and Poppler (`pdfinfo`, `pdfunite`); and the native swarm
export dependencies described above. `build/generation-context` uses the
usual C++/GDAL build dependencies. The bundled
[Atkinson Hyperlegible fonts](../../../assets/fonts/atkinson-hyperlegible/README.md)
are checksum-verified and selected through repository-local Fontconfig.
The historical ST2 edition passed its 152-sheet SVG, PDF and 300 dpi PNG
checks, recorded in that delivery's `sources/sheets-validation.json`.
The current wine/amber atlas validation scope is recorded above.
