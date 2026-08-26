# Cartofreako website v2 — stage 1 plan and options

Status date: 2026-08-26 (America/Los_Angeles).

This is a proposal only. No documentation file was changed, nothing was
committed or pushed, and no remote object was touched while this document was
written. It is the stage-1 deliverable requested in
[`20260826_cartofreako_website_v2.md`](20260826_cartofreako_website_v2.md).
Implementation starts only after human approval.

## 1. Goal

Restructure the documentation tree and regenerate the GitHub Pages site so
that the long single landing page becomes a set of purpose-built pages, the
six projection contact sheets follow one reviewed plate order, and the whole
site carries the Devastation Pacific house style the way `devp.ac` does. The
regenerated site continues to serve the committed top-of-tree (`tot`) image
snapshot, which is already the recorded live backend in
[`.github/deploy-backend`](../../.github/deploy-backend).

The four work items are:

| Item | Work |
| --- | --- |
| DY#1 | Move the repository-layout and source-guide material out of `index.md` |
| DY#2 | Move the build/artifact-catalog material out of `index.md` |
| DY#3 | Reorder the gallery contact sheets to one canonical plate order and remove the Art-passes group |
| DY#4 | Restyle the site with the Devastation Pacific house style, using `devp.ac` as the worked example |

The final stage regenerates GitHub Pages with those changes over the `tot`
images, per the human follow-up.

## 2. Current state (verified)

Evidence gathered while writing this plan:

| Fact | Value |
| --- | --- |
| Landing page | [`index.md`](../../index.md), 692 lines, Jekyll `default` layout, opens with `{% include image-backend.md %}` |
| Section map | `Start with the maps` (14), `Since the v13...` (24), `Project and build` (52), `Repository layout` (67), `Documentation map` (88), `Choose a projection` (139), `Build and generated artifacts` (155), `Complete released artifact catalog` (248), `Resource metric catalog and pass classes` (317), six projection sections (360–481), `Source guide` (482), `Attribution and licensing` (651) |
| Gallery pages | Six thin front-matter pages under `docs/pages/gallery/`, all including `_includes/generated-snapshot.md` |
| Plate order authority | [`_data/generated_passes.yml`](../../_data/generated_passes.yml) — categories, ids, labels, stems, alt text; consumed once by `generated-snapshot.md` |
| Pass count today | 33 in `generated_passes.yml` (4 foundations, 5 sky/orbital, 8 networks+Anthropocene, 14 resources, 2 art) |
| Image backend | `.github/deploy-backend` = `tot`; `_config.yml` `image_backend: tot`; full images are WebP, layered SVG and print PDF hidden for `tot` |
| TOT snapshot | `assets.tot/` staged by `scripts/build-tot-preview.sh --tier browse` from `assets.generated/catalog/artifacts-v1.json`; manifest records 217 artifacts |
| Deploy | `.github/workflows/jekyll-gh-pages.yml` runs `make check-docs`, `make check-tot-snapshot`, Jekyll build, `check-doc-links.py --walk _site`, then Pages deploy on push to `main` |
| House-style reference | The `devp.ac` repository (`/home/bkoz/src/devp.ac`) is a plain static site with `assets/css/site.css` implementing the house palette, Atkinson typography, accent bar, hard-left alignment, underlined links, and square corners |

Ruby/Jekyll are not installed on this host, so the rendered build and
deployment run through the GitHub workflow. Local verification is limited to
`make check-docs` and the source link checker.

## 3. DY#1 — split `index.md` into `source_layout_conventions.md`

Move these two sections verbatim into a new
`docs/pages/getting-started/source_layout_conventions.md` (planned file):

- `## Repository layout` (current lines 67–86)
- `## Source guide` (current lines 482–650)

The new page gets `layout: default`, a title, and the
`{% include image-backend.md %}` include, because the source-guide table
contains `{{ release_base }}` image links that only resolve when that include
has run.

**Link rebasing.** The moved text uses repo-root-relative paths written for a
file at the repository root. From `docs/pages/getting-started/`, every such
path must gain the correct `../` prefix. The moved sections touch these
families: `src.projections/`, `src.generate/`, `src.wasm/`, `tests/`,
`assets.static/`, `docs/pages/...`, `docs/development/...`, `Makefile`, and
`generation-profile.json`. The `#generated-artifact-previews` anchor moves to
the DY#2 page, so the repository-layout row that points at it becomes a link
to `build.md#generated-artifact-previews`.

**Retarget incoming links.** After the split, these existing references to
`index.md#generated-artifact-previews` must point at the DY#2 page instead:

- [`README.md`](../../README.md) line 156
- [`docs/pages/getting-started/generation.md`](../pages/getting-started/generation.md) line 13
- [`docs/pages/passes/resources/implementation.md`](../pages/passes/resources/implementation.md) line 5
- [`docs/pages/passes/resources/metric-catalog.md`](../pages/passes/resources/metric-catalog.md) line 7
- [`docs/development/20260815_stage-13.md`](20260815_stage-13.md) line 158
- [`docs/development/20260815_stage-12.md`](20260815_stage-12.md) line 5

The historical `v13-s3-viewer.html` files link to the live site URL rather
than the source tree and are left untouched.

## 4. DY#2 — split `index.md` into `build.md`

Move this one top-level section, including both of its subsections, into
`docs/pages/getting-started/build.md` (planned file; current lines 155–359):

- `## Build and generated artifacts`
- `### Complete released artifact catalog` (contains the
  `<a id="generated-artifact-previews">` anchor)
- `### Resource metric catalog and pass classes`

Same rebasing rule as DY#1 for `generation-profile.json`, `Makefile`,
`assets.generated/`, `docs/pages/...`, and the pass-note links. The
`generated-artifact-previews` anchor stays inside this page and keeps its id.

**After DY#1+2, `index.md` keeps:** the deck, `Start with the maps`, `Since
the v13...`, `Project and build`, `Documentation map`, `Choose a projection`,
the six short projection summaries, and `Attribution and licensing`. The two
removed blocks are replaced by short pointer sections linking to the new
pages, so the landing page stays a real entry point without duplicating the
deep content.

**Index updates.** Add both new pages to
[`docs/pages/getting-started/README.md`](../pages/getting-started/README.md)
and to the `Start, build, and generate` table in
[`docs/pages/README.md`](../pages/README.md). No `navigation.json` change is
needed because the section entry already points at the getting-started README.

## 5. DY#3 — one canonical gallery plate order

The requested order, translated onto the current stem names in
[`_data/generated_passes.yml`](../../_data/generated_passes.yml):

| Group (new id) | Passes, in order |
| --- | --- |
| `projection-foundations` | geometry, graticules, earth, water, **atmosphere** |
| `sky-and-orbital-passes` | astro-observer-hubble, astro-all-sky, astro-observer-ground-multiband, orbital-technosphere-observer, orbital-technosphere-global |
| `networks` | network-groundstations, network-fiber, network-cdn, network-swarm |
| `anthropocene` | anthropocene-particulate-2025, anthropocene-particulate-2026, anthropocene-temperature-2025, anthropocene-temperature-2026 |
| `stage-12-resources` | all 14 resources, unchanged internal order |
| *(removed)* | both Art passes: bathymetry-roulette, bathymetry-hamonshu |

This splits today's `Networks and Anthropocene` group into `networks` and
`anthropocene`, and deletes the `Art passes` group.

### 5.1 Decision point — the "atmosphere" plate

The order puts an atmosphere plate between water and the sky plates. The only
atmosphere-family pass in the repository is **Cloud-atmosphere** (stem
`cloud-atmosphere`). That pass is credentialed/optional and was removed from
the standard corpus at v14, so it is absent from the current catalog,
`assets.tot/`, and `_data/generated_passes.yml`. The local generated tree does
hold six `cloud-atmosphere-*` plates (an authorized run from August 15, with
the AuthaGraph plate regenerated August 24), but they are not staged in TOT.

Two options:

**A — Include Cloud-atmosphere (restore it to the snapshot).** Add a
`Cloud-atmosphere` entry to the foundations group, regenerate/restage the six
plates into `assets.tot/` (thumbnail and full WebP), and extend or override
`build-tot-preview.sh` so this preview-only pass is staged without changing
the standard artifact manifest. Result: 32 plates, matching the task order
exactly. Cost: the pass is credentialed, the v14 standard corpus intentionally
excluded it, and restaging mixes a preview-only pass into the committed TOT
snapshot.

**B — Skip the atmosphere slot for now.** Reorder the 31 plates that exist in
TOT and leave a documented gap/note that Cloud-atmosphere returns when a fresh
authorized run is available. Result: 31 plates. Cost: the delivered order
diverges from the literal task list by one slot.

**Recommended:** B for the site regeneration, with A as a follow-up only if
the human confirms they want Cloud-atmosphere promoted back into the live TOT
snapshot. The gallery data change is identical either way except for one
entry, so switching later is a one-line edit plus a restage.

### 5.2 Ripple edits for DY#3

- `_includes/generated-snapshot.md`: "33 standard passes" count wording and
  any group narrative; the loop itself needs no logic change.
- `docs/pages/gallery/README.md`: the subject-grid cards link
  `#networks-and-anthropocene` (Star-X and Myriahedral) and `#art-passes`
  (Voronoi). Retarget to the new `#networks` / `#anthropocene` ids and pick a
  replacement for the removed Art-passes card; update the "33 passes" list.
- `docs/pages/README.md`: "33-pass contact sheet" and the six "33 passes"
  table links change to the new count.
- `index.md` and the moved build page: any "33 passes" / "32 passes" prose and
  the stale "thirty-second pass is Cloud-atmosphere" sentence.
- `docs/pages/runtime/README.md` and `artifact-selection.md` reference the
  217-product/33-pass catalog; those describe the frozen catalog, not the
  gallery order, and stay unless the human asks otherwise.

## 6. DY#4 — house-style restyle modeled on `devp.ac`

`devp.ac` applies the house style with a small standalone stylesheet
(`assets/css/site.css`): the house token palette (`--dp-paper #fcfbf7`,
`--dp-ink #14171a`, `--dp-accent #173a55`, `--dp-muted #4d565d`,
`--dp-rule #9da8af`, `--dp-soft #eef1f2`), the Atkinson Hyperlegible
font stack with system fallbacks, a 7px Pacific-blue accent bar, hard-left
alignment, underlined links with a visible focus outline, mono kickers and
numeric labels, bordered module cards with square corners, and no gradients,
shadows, or rounded "dashboard" styling.

Cartofreako today uses `jekyll-theme-minimal` plus a large inline `<style>`
block in [`_layouts/default.html`](../../_layouts/default.html).

Three options:

**A — House tokens on the current layout (recommended).** Move the inline
style into a real `assets/css/site.css` modeled on `devp.ac`'s stylesheet,
keeping `jekyll-theme-minimal` as the structural base. Adopt the house palette,
Atkinson stack, accent bar, underlined links, square corners, and mono labels;
port the existing gallery/table/defer-render rules unchanged. Lowest risk,
keeps every current layout class working.

**B — Full `devp.ac` parity.** Drop `jekyll-theme-minimal` and rebuild the
layout and stylesheet as a direct adaptation of `devp.ac`'s markup/CSS
(`.wrap`, `header.site`, `.accent-bar`, `.hero`, `.metric-grid`, `.callout`,
`footer.site`). Closest to the letter of "do the same, but with cartofreako",
but it touches every page's rendered shell and needs more cross-browser and
mobile verification before it can ship.

**C — Palette-only touch-up.** Keep the current inline styles and only swap
the color/font values to the house tokens. Fastest, but leaves the house
style half-applied and does not fix the rounded summary blocks or the theme's
non-house link treatment.

**Recommended:** A. It delivers the visually recognizable `devp.ac` treatment
while preserving the gallery components that are specific to cartofreako, and
it converts the one-off inline block into a maintainable stylesheet as a
bonus.

House-style rules carried over in every option: no gradients/shadows/glass,
square corners, underlined links, left-aligned body and headings, right-aligned
numeric columns, `#173a55` accent (not `#0066cc`), and WCAG 2.2 AA contrast
with color never the sole carrier of meaning.

## 7. Declutter suggestions (3)

1. **Fold the six projection summaries into one projections page.** The
   AuthaGraph-through-Voronoi blocks (lines 360–481) duplicate
   `docs/pages/projections/`. Keep the compact `Choose a projection` table on
   `index.md` and link out; move the long prose into the projections README.
2. **Retire the landing-page `Documentation map` table.** It duplicates
   `docs/pages/README.md`. Replace it with a four-line "start here" list
   (gallery, build, projections, releases) and let the hub own the full map.
3. **Move the `Since the v13...` changelog off the landing page.** Put it in
   `docs/pages/releases/` and keep a one-paragraph "what changed" summary with
   a link on `index.md`.

These are additive cleanup steps after DY#1–4; none is required for the
regeneration to be correct.

## 8. Staged execution

1. **Stage 1 — page splits (DY#1+2).** Create the two new pages, rebase
   links, replace the removed blocks in `index.md`, retarget incoming links,
   update the two README indexes.
2. **Stage 2 — gallery order (DY#3).** Edit `generated_passes.yml` per the
   chosen atmosphere option, fix the include count wording, retarget gallery
   README cards and `docs/pages/README.md` counts. If option A is approved,
   restage `assets.tot/` first with the six Cloud-atmosphere plates.
3. **Stage 3 — restyle (DY#4).** Implement the chosen restyle option.
4. **Stage 4 — verify locally.** `make check-docs` and, if the TOT tree was
   touched, `make check-tot-snapshot`; confirm no source link regressions.
5. **Stage 5 — regenerate GitHub Pages.** Commit the approved changes and
   push to `main`. The existing workflow builds with the `tot` backend
   (already selected) and deploys. This stage is the only one that touches a
   remote and is deliberately gated on human approval.

Stages 1–4 are local edits; stage 5 is the regeneration the human requested.

## 9. Open questions for approval

1. DY#3 "atmosphere": Option B (skip Cloud-atmosphere, 31 plates) or Option A
   (restore it into TOT, 32 plates)?
2. DY#4 restyle: Option A (house tokens on current layout), B (full `devp.ac`
   parity), or C (palette-only)?
3. Regeneration now: confirm pushing to `main` with the `tot` backend at the
   end, which triggers the public GitHub Pages deploy.
4. Declutter ideas 1–3: implement now, or keep them as follow-ups?
