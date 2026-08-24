# `20260823_map_msp_color_style_edit_v2` — stage 1 proposal

Status date: 2026-08-23 (America/Los_Angeles).

This proposes the v15.1 color/style revision for Cartofreako generated
imagery. It responds to
[`20260823_map_msp_color_style_edit_v2.md`](20260823_map_msp_color_style_edit_v2.md)
(the human review of the v15 artifacts). Nothing here is implemented yet: no
generator, profile, Makefile, or generated artifact has been changed.

## 1. Requirements restated

From the human review of the v15 artifacts
(`assets.generated.20280815.tar.xz`), using the color-revised resources in
`assets.generated.20260815.msp.edit/`, produce a v15.1 regeneration that:

1. Adopts the revised color resources across generated artifacts: new color
   profiles, adjusted Izzi generation colors, and the same updated colors
   applied to the other projections.
2. Moves the map legend from top-left to bottom-right, with no
   clipping/masking of underlying cartography as a hard requirement
   (overlapping Antarctica is acceptable). The current placement clips
   cartography on AuthaGraph and Dymaxion in every `anthropocene-*` image
   (particulate and temperature, 2025 and 2026).
3. In `orbital-technosphere-global-authagraph-44-19.052559`, replaces the
   black background with white.
4. In `astro-observer-ground-multiband-authagraph-44-19.052559`:
   - moves the clipped `3C 273` label inward;
   - doubles the line weight of that label and makes it white;
   - does the same (2x, white) for the too-thin-to-see linework associated
     with the Mercury and Sagittarius A\* orbits;
   - augments each stationary item (Cygnus X-1, Centaurus A, 433 Eros,
     etc.) with Izzi `make_line_rays` at `n=10`.
5. (human addition) Produce a grayscale derivation of
   `earth-authagraph-44-19.052559 copy.webp` with blue mapped to 17% gray
   and green mapped to 29% gray.

The review also asks whether using sol-5.6 via an API key would simplify
some of the color matching, and directs that the proposal be written to
`20260823_map_msp_color_style_edit_v2_stage_1.md`.

## 2. Current-state assessment

Measured against the current `assets.generated/authagraph/screen-1080p-webp/`
set, the 20 revised `*.webp` resources (3840x1663, matching the
screen-1080p-webp geometry) differ substantially:

| Revised file | RMSE vs current | Observed change |
|---|---:|---|
| anthropocene-particulate-2025 | 0.163 | Background cream -> white; interior tint and marker colors adjusted |
| earth | 0.481 | Significant recoloring |
| astro-observer-ground-multiband | 0.582 | Document/map background -> deep blue (#00018B) |
| orbital-technosphere-global | 0.639 | Dark navy background replaced (revised copy shows dark green; item 3 overrides to white) |

The revised set covers 18 AuthaGraph passes plus one Dymaxion
(`01-dymaxion-full-water-rmi-locator`) and one Cahill-Keyes
(`02-cahill-keyes-octant-1-five-contexts`) reference. The generators are
projection-agnostic (each `src.generate/*-generation.h` is fed a
`projection_context`), so updating the shared constants and profile data
propagates one color decision to all six projections (authagraph,
cahill-keyes, dymaxion, myriahedral, star-x, voronoi) and to every output
family (SVG, PNG, WebP, PDF, thumbnail).

Color decisions live in two places:

- Generator constants in `src.generate/*-generation.h`, for example the
  anthropocene legend band `{249,247,240}` and the orbiting background
  `{10,28,39}` (`orbiting-generation.h`, `add_background`,
  `technosphere-ocean` rect).
- Data-driven profile colors, for example per-metric `"color": "#d94841"`
  fields in `assets.static/anthropocene/anthropocene-particulate-2025-profile.json`.

All legends are top-anchored today:

| Generator file | Legend element | Current placement |
|---|---|---|
| `anthropocene-particulate-generation.h` | `legend-and-provenance` band | `{0, 0, w, 1.25}` |
| `anthropocene-temperature-generation.h` | `legend-and-provenance` | title at `{0.30, 0.21}` |
| `network-swarm-generation.h` | `legend-and-provenance` band | `{0, 0, w, 0.82}` |
| `network-groundstations-generation.h` | band | `{0, 0, w, 0.82}` |
| `network-infrastructure-generation.h` | band | `{0, 0, w, 0.96}` |
| `fiber-synthesized-generation.h` | band | `{0, 0, w, 1.08}` |
| `cloud-atmosphere-generation.h` | band | `{0, 0, w, 1.05}` |
| `resources-generation.h` | `resource-legend-panel` (2 sites) | `{0.30, 0.30, w, 1.38}` |

For item 4, the generated SVG shows the mechanism of each defect:

- `3C 273` projects to `cx=0.000337` (the AuthaGraph left seam), so its
  `r=0.065` marker is half-clipped. `add_label`
  (`astro-generation.h`) clamps labels at the right edge only.
- Label stroke is `midnightblue`, width `0.01`
  (`label_typography()`).
- Mercury's true-angular-size outline is a dashed circle with stroke width
  `0.001` (invisible at 1080p), and Sagittarius A\*'s ring is magenta
  `rgb(255,0,255)` at width `0.035`.
- Stationary objects are drawn by `add_marker` (`astro-generation.h:458`);
  there is no ray ornamentation today. Izzi's
  `make_line_rays(origin, style, r, nrays)` exists in
  `izzi-svg-render-basics.h:498`; note its default `r=4` (map units) must
  be overridden, its internal PRNG is unseeded (non-deterministic output),
  and its angle range uses `2 * 22/7` (integer division; about 6 radians
  rather than 2*pi).

## 3. Proposed implementation

### 3.1 Color adoption (item 1)

Add a small extraction-and-compare harness under `scripts/` (ImageMagick is
already required by the render pipeline):

1. For each revised WebP, sample the document background corners, the map
   frame interior, and a per-layer k-means palette (4-8 clusters) against
   the layer ids in the corresponding current SVG.
2. Produce one mapping table: revised region -> hex color -> owning
   generator constant or profile JSON field.
3. Apply the constants in `src.generate/*-generation.h` and the metric
   `color` fields in the affected `assets.static/anthropocene/*-profile.json`
   files.
4. Iterate: regenerate, re-measure RMSE/Delta-E against the revised
   reference, and stop when each revised pass is under an agreed threshold
   (proposal: RMSE <= 0.02 per revised pass, plus a human eyeball pass on
   authagraph and dymaxion).

The Dymaxion and Cahill-Keyes references act as cross-projection spot
checks for the same constants. Because every projection shares the
generators, no per-projection color tables are needed.

### 3.2 Legend placement (item 2)

Introduce one shared bottom-right legend placement helper (bottom-right
corner, inset equal to the frame margin) and retarget the eight legend
sites above. Requirements:

- The legend may not mask non-Antarctic cartography. To satisfy this with a
  full-width band is not possible on AuthaGraph/Dymaxion, so the proposal
  is a compact bottom-right panel sized to the legend content, not a strip.
- Antarctica overlap is explicitly allowed.
- Panel opacity and border follow the existing resource-legend-panel
  styling; the panel may be fully transparent where it covers only
  Antarctica.
- Apply to particulate and temperature first (the cited defects), then the
  network/cloud/resource legends for consistency, since item 2 says "all
  maps".

### 3.3 Orbital white background (item 3)

Change the `product_kind::global` background in
`orbiting-generation.h` `add_background` from `{10,28,39}` to white
`{255,255,255}` (id `technosphere-ocean`). The revised resource's dark
green intermediate state is treated as superseded by this instruction.
Because tracks, labels, and subdued land were tuned for a dark field, audit
`orbiting-generation.h` stroke/fill constants after the change and re-map
any low-contrast elements (e.g., light satellite tracks and white text) to
dark-on-white equivalents. Keep the observer variant's night-sky
background unchanged unless the reviewer says otherwise.

[human review] the goal is to match background/earth/ocean the same as:
/home/bkoz/src/cartofreako/assets.generated/authagraph/png/network-groundstations-authagraph-44-19.052559.png



### 3.4 Astro label and ray fixes (item 4)

In `src.generate/astro-generation.h`:

1. Add a left-edge inset in `add_label` symmetric to the existing right
   clamp, and clamp edge markers so `x >= marker_radius`; `3C 273` then
   renders fully inside the frame.
2. Change the `3C 273` label stroke from `midnightblue` `0.01` to white
   `0.05` (doubled and white as specified). Decision point: extend the
   white 2x stroke to all astro labels for consistency, or keep it scoped
   to `3C 273` only.
3. Mercury outline: stroke width `0.001 -> 0.002`, white, opacity 1.
   Sagittarius A\* ring: stroke `rgb(255,0,255)` `0.035` -> white `0.07`
   (2x). If the reviewer meant different "orbit" linework, this is the
   default mapping and gets verified against the reference WebP.
4. Call Izzi `make_line_rays` with `nrays=10`, white style, and radius
   scaled to the marker (`r = 3 * marker_radius`, overriding the `r=4`
   default) for each stationary object. Proposed "stationary" definition:
   every object in the `deep-sky` and `transients` layers, plus
   `solar-system` objects whose kind is `asteroid` or `comet` (covers
   Cygnus X-1, Centaurus A, Sgr A\*, M87\*, 433 Eros, Apophis, 67P, and
   the GRBs); the Sun and planets remain plain markers.
5. Determinism: seed or replace the ray angle RNG so regenerated artifacts
   remain checksum-stable; flag the upstream `22/7` range quirk and either
   accept its ~343-degree coverage or fix in Izzi. (human: yes)
6. (human addition) The Hubble product has the same too-small clipped line
   class: `uranus-true-angular-size-segment-1` (dashed, stroke `0.001`,
   sub-pixel). Make it white and 2x as with Mercury. The planet outline
   style is shared (`true_size_style` in `astro-generation.h`), so one
   constant change covers Mercury, Venus, Jupiter (ground) and Uranus
   (Hubble).

### 3.5 sol-5.6 assessment (review question)

Per official OpenAI documentation search results: `gpt-5.6-sol` is the
GPT-5.6 family frontier model, takes image input, and its documented
endpoint surface includes `v1/images/generations` and `v1/images/edits`,
with `max` reasoning effort available; the sol-5.6 naming in the sibling
Izzi project means `gpt-5.6-sol-max` hosted by OpenAI. Direct fetches of
`developers.openai.com` model pages returned 403 in this environment, and
the Image edit API reference page lists `gpt-image-1.5`, `gpt-image-1`,
`gpt-image-1-mini`, `chatgpt-image-latest`, and `dall-e-2` as its supported
models; whether `gpt-5.6-sol-max` is accepted by `v1/images/edits` is
therefore uncertain and should be confirmed against the live API before
committing.

Recommendation: keep the deterministic pipeline as the source of truth.
The color changes must propagate to six projections, three raster
families, PDFs, and checksummed catalogs; pixel-level `images/edits`
recoloring of individual WebPs cannot propagate to SVG/PDF and would break
the reproducible-artifact contract. Use sol-5.6 as an optional accelerator
in a bounded pilot: feed each revised WebP plus the current SVG palette and
ask for per-region hex mappings, then apply those mappings as generator
constants exactly as in 3.1. Acceptance for adopting the API path:
proposed palettes reach the same RMSE threshold in fewer iterations than
manual extraction, outputs are re-applied deterministically through the
generators, and provenance/keys follow the existing house-style rules
(Izzi documents sol-5.6 provenance gaps in its workflows section 5.5).
Requires `OPENAI_API_KEY`; the existing secret-checking conventions apply.

Human: ok, if needed will be stage_2

### 3.6 Earth grayscale derivation (item 5)

Derive `earth-authagraph-44-19.052559.gray-blue17-green29.webp` from the
revised resource in `assets.generated.20260815.msp.edit/` using the channel
weighting `gray = 0.17 * blue + 0.29 * green` (red contributes nothing),
implemented with an ImageMagick `-fx` expression so the conversion is exact
and repeatable. Produced 2026-08-23 as
`assets.generated.20260815.msp.edit/earth-authagraph-44-19.052559.gray-blue17-green29.webp`.
This is a derived resource only; it does not change the earth generator or
the generated plate.

## 4. Regeneration and verification

After the edits:

1. Regenerate the affected passes: `make generate-orbiting`,
   `generate-astro`, `generate-anthropocene-particulate`,
   `generate-anthropocene-temperature`, and (for legend changes)
   `generate-network-swarm`, `generate-network-groundstations`,
   `generate-network-infrastructure`, `generate-fiber-synthesized`,
   `generate-cloud-atmosphere`, `generate-resources`.
2. Rebuild the 1080p PNG/WebP families and catalogs
   (`screen-1080p-webp`, `artifacts-v1.json`), then run the existing
   gates: `make check-docs`, `make check-artifact-selection`,
   `make check-screen-1080p`, and `tests/check-all-experiments.sh`.
3. Run the 3.1 compare harness against the 20 revised references and
   report RMSE/Delta-E per pass.
4. Archive v15.1 with the same tarball/manifest conventions as v15, and
   refresh SHA256SUMS where those are published.

(human decision) First regeneration is AuthaGraph plates only, so the
reviewer can check internal consistency before the other five projections
are regenerated.

## 5. Open decisions for the reviewer

1. Legend form: compact bottom-right panel (yes) versus a
   bottom-anchored full-width strip that is allowed to sit over
   Antarctica.
2. Astro label strokes: white 2x only for `3C 273` (literal reading) or
   all labels (visual consistency: human yes).
3. Confirm the white orbital background overrides the dark-green
   intermediate in the revised resource. Yes, see note above
4. Confirm the "stationary items" set in 3.4.4 (deep-sky + transients +
   asteroids/comets). Yes.
5. Approve the sol-5.6 pilot in 3.5 and confirm API key availability; if
   not approved, colors are derived with the local ImageMagick harness
   only. Yes.
6. Acceptance RMSE threshold for item 1 (proposed 0.02 per revised pass).

## 6. Sequencing

1. Stage 1 (this document): assessment and proposal.
2. Stage 2: color extraction harness + palette mapping table; apply item 1
   constants and profiles.
3. Stage 3: legend helper and item 2 relocation; item 3 orbital background.
4. Stage 4: astro label/ray fixes (item 4).
5. Stage 5: full regeneration, gates, compare report, v15.1 archive.
6. Optional parallel: sol-5.6 pilot against stages 2 and 4 outputs.
