More changes.

Blanket change, all plates
label layer : text should have the izz::style object set _M_stroke_opacity to 0.0;

MX3.0: Central title and legend all in one style for all plates

Use the style in anthropocene-particulate-2025-authagraph-44-19.052559.png for the legend, only:
 - center the legend block
 - the title text is fine but 2x the legend items (aka "record highs", etc)


MX3.1: astro

For all of these plates:

1. astro-all-sky-authagraph-44-19.052559.png
2. astro-observer-ground-multiband-authagraph-44-19.052559.png
3. astro-observer-hubble-authagraph-44-19.052559.png

Change:

label layer : text should have the izz::style object set _M_stroke_opacity to 0.0;

transient layer: good job on the rays, now make then 2x wider

celestial-reference layer: all celestial-equator-sements-[1,2,3] lines will now be _M_stroke_size 2 and color izzi::color::white


MX3.2: cdn

For
network-cdn-authagraph-44-19.052559.png

Scale size of individual hexagon graphics 2x


MX3.3: fiber

For
network-fiber-authagraph-44-19.052559.png

Set fiber line style for current to  _M_stroke_size to 1px and _M_stroke_opacity to 0.8, and _M_stroke_color to color::black for all lines in group "network-fiber", and also include the "network-fiber-landings" layer


MX3.4: groundstations

For
network-groundstations-authagraph-44-19.052559.png

Set the _M_stroke_size on the lines in layer "starlink-gateway-links" to 1 px


MX3.5: orbital technosphere global

/home/bkoz/src/cartofreako/assets.generated/authagraph/png/orbital-technosphere-global-authagraph-44-19.052559.png

Set all "norad-*" elements in layer "objects-megaconstellation" to _M_fill_color rgb(255,29,16)


MX 3.6: orbital technosphere observer

Set layer "background-observer" color to wcag light gray instead of black.










Then, just regenerate
/home/bkoz/src/cartofreako/assets.generated/authagraph/png

As a canary for human approval, not all plates and all projections.

## Approved implementation plan — 2026-08-24

Human-approved interpretations:

- Pixel scale: 1 px = 0.0115 map units (plates render at 44 units =
  3840 px), so 2 px = 0.023 units.
- Legend placement: horizontally centered, bottom-anchored.
- MX3.0: adopt the anthropocene-particulate legend style on every plate;
  title text stays as-is (0.42), legend items are 2x (0.204).
- WCAG light gray: `svg::color::wcag_lgray` = `rgb(148, 148, 148)`.
- MX3.6: switch the orbital-observer foreground to dark (approved).

Changes:

1. Blanket, all plates: set `_M_stroke_opacity` to `0.0` in every label
   typography helper that carries a stroke (anthropocene particulate and
   temperature, cloud-atmosphere, astro, network-swarm,
   network-groundstations, orbital observer).
2. MX3.0, all legend-bearing plates: white 0.94 panel, bold title `0.42`
   `rgb(42,40,36)`, provenance `0.105` `rgb(87,82,74)`, item text `0.204`
   `rgb(54,51,46)`, block horizontally centered at the bottom.
3. MX3.1, astro plates: stationary rays stroke `0.01 -> 0.02`;
   celestial-equator segments white with stroke size `0.023` (2 px).
4. MX3.2, network-cdn: hexagon marker radii x2 in `add_cloud_marker`, and
   cloud label offsets track the doubled radius.
5. MX3.3, network-fiber: all lines in the `network-fiber` group become
   black, opacity 0.8, stroke 0.0115 (1 px), including both
   `network-fiber-landings` circle strokes.
6. MX3.4, network-groundstations: `starlink-gateway-links` stroke
   `0.006 -> 0.0115`.
7. MX3.5, orbital-technosphere global: megaconstellation `norad-*` markers
   fill `rgb(255,29,16)`.
8. MX3.6, orbital-technosphere observer: background
   `svg::color::wcag_lgray`; foreground labels, reference lines, and
   optical-candidate marker strokes switch to dark.

Regeneration (canary): AuthaGraph SVGs for the affected passes, then
AuthaGraph PNG exports only. No screen-1080p composites, catalog refresh,
other projections, or commit until the human approves the visual result.

## Changes since the approved plan — 2026-08-24

Iterative refinements applied during the AuthaGraph canary review:

- Legend block moved back to bottom-right with titles right-aligned at a
  50px margin; extra vertical rows added so enlarged text no longer
  overlaps.
- Legend width minimized (shrink-to-fit from content), all non-title
  legend text set to 12 point, item text right-aligned.
- The `coverage-note` layer was folded into the legend as a right-aligned
  line under the title (all plates that have one: particulate,
  temperature, cloud-atmosphere), at 12 point.
- Legend items converted to a two-column table: column 1 is the color key
  (black outline when the key is white), column 2 is the left-aligned
  12pt label with a 10px gap. Key symbols scaled 1.5x. The table sits
  above the title+text block and has no panel background.
- The legend panel rect now frames only the title + text block: its top
  is 40pt above the title glyphs, and its width is the title text width
  plus 50px margins left and right.
- Cartography: `precipitation_rate_mm_h` elements in the cloud-atmosphere
  plate now render at 20% opacity.

Human approval of the AuthaGraph canary received 2026-08-24; the full
rebuild of every projection and plate (SVG, PNG/PDF, screen-1080p
composites, and catalog) is in progress.
