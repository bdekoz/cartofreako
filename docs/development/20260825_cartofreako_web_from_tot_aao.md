# Cartofreako GitHub Pages dual image backends (AAO + top-of-tree) — stage 1 proposal

Status date: 2026-08-25 (America/Los_Angeles).

This proposes making the GitHub Pages site switchable between two image
backends: the immutable Berkeley Active Archive Object (AAO/S3) objects, and a
local top-of-tree (TOT) view of the generated assets that needs no UCB VPN or
network access at all. It does not propose uploading anything to AAO,
changing the product object layout, or changing the generated corpus.

## 1. Goal

The site has exactly one documentation tree today, and every released-image
URL in it is hardcoded to the immutable S3 prefix `cartofreako/v14/`. That is
correct for public visitors but makes local review depend on the Berkeley
route/VPN: from `rizal`, `s3-ewh.ist.berkeley.edu` does not resolve without it
(verified 2026-08-25; `docs/pages/releases/aao-v14.md` records the same
limitation).

The goal is one source tree with a selectable image backend:

| Backend | Source | Audience | Dependency |
| --- | --- | --- | --- |
| `aao` | Immutable S3 `cartofreako/v14/` (later `v15` when deposited) | Public visitors; alternate deployment selected via `.github/deploy-backend` | Public HTTPS only |
| `tot` | Top-of-tree `assets.generated/`, staged into the same product layout under a repo-local root | Live default and local review/preview | None; fully offline |

The switch must not fork the documentation pages. Gallery pages, contact
sheets, and the SVG viewer stay single-authored; only the resolved base URL
changes. The `tot` snapshot is not just a local preview: it must be committable
and deployable to GitHub Pages so the site can be browsed from a host without
Berkeley route/VPN access, while the `aao` build remains available as the
alternate deployment selected via `.github/deploy-backend`. The live default
is `tot` (D7).

## 2. Current-state assessment (verified)

### 2.1 Build and deploy

- Jekyll with `jekyll-theme-minimal`; `_config.yml` carries only title,
  theme, and Sass settings.
- `.github/workflows/jekyll-gh-pages.yml` runs `make check-docs`, then
  `actions/jekyll-build-pages` from `./`, then deploys to GitHub Pages at
  `https://bdekoz.github.io/cartofreako/`. The stock Pages build action
  builds from `_config.yml` alone; a custom-config build must invoke `jekyll`
  directly and upload the artifact itself.
- `make check-docs` is `scripts/check-doc-links.py` plus the pass-status
  check. The link checker validates repository-local links only: it skips
  `http(s)://` destinations and any destination containing `{{`/`{%`, and it
  scans tracked `.md`/`.html` sources (not the rendered `_site/`).

### 2.2 Where the AAO base is hardcoded today

| File | Hardcoded content |
| --- | --- |
| `_includes/generated-snapshot.md` | `release_base`, `viewer_base`, `preview_base` assigns; v14 narrative; `release.json` completion-marker link |
| `_includes/v14-pass-gallery.md` | `release_base` and `viewer_base` assigns for all six projections |
| `_includes/v14-projection-gallery.md` | Same, for the six water plates |
| `docs/pages/gallery/README.md` | Top-of-page `release_base`/`viewer_base` assigns; subject-card URLs built from those variables |
| `index.md` | Absolute S3 thumbnail URLs in the generated-artifact preview table (lines ~545–556) and the "resolve against `cartofreako/v14/`" narrative (~line 267) |
| `docs/releases/v14-aao-viewer.html` | `releaseBase` JavaScript constant; fetch/decompress streaming with CORS fallback |
| `docs/pages/README.md`, `docs/pages/releases/README.md`, `docs/pages/releases/aao-v14.md`, `docs/pages/runtime/consumer-release-usage.md` | "current browser-facing mirror is v14" narrative |

### 2.3 The two object layouts

The published AAO product layout:

```text
products/<lifecycle>/<projection>/
├── master/<stem>.svg.gz
├── print/<stem>.pdf
├── full/<stem>.png
├── thumbnail/<stem>.png            (whole-map projections only)
└── screen-1080p/{png,webp}/<stem>.{png,webp}
```

The local generated tree is projection-first and family-named differently:

```text
assets.generated/<projection>/
├── svg/<stem>.svg                  (84 of 217 also have a pre-made .svg.gz)
├── pdf/<stem>.pdf
├── png/<stem>.png
├── thumbnail/<stem>.png
├── screen-1080p/<stem>.png
├── screen-1080p-webp/<stem>.webp
└── gpu-control-2k-{landscape,portrait}/
```

Two details matter for a TOT stager:

- **Slices.** Locally the five Myriahedral slice projections share the single
  `assets.generated/myriahedral/` directory; the catalog
  (`assets.generated/catalog/artifacts-v1.json`) is the only place that
  records the per-artifact `projectionId` and exact parent paths. The stager
  must drive off the catalog's `parents.svg.path`, `parents.pdf.path`,
  `parents.fullPng.path`, `screen.png.path`, and `screen.webp.path`, not off a
  directory walk.
- **Master gzip.** The AAO `master/` objects are `.svg.gz`. Only 84 local
  SVGs already have gzip companions; `scripts/build-generated-assets-s3-release-v14.sh`
  gzips the remainder with `gzip --best --no-name`. The TOT stager needs the
  same step.

The catalog also carries `sourceRevision.gitCommit`, which is exactly what a
TOT snapshot needs for self-description and staleness checks.

### 2.4 Measured sizes

Family totals across the current local tree (`du`, 2026-08-25):

| Family | Size | Commit-safe? |
| --- | ---: | --- |
| Thumbnails | 10.9 MB | yes |
| Screen-1080p WebP | 54.6 MB | yes |
| Full-resolution WebP (q90, derived) | ~33 MB | yes — the committed full-size family |
| Screen-1080p PNG | 90.3 MB | no (redundant with WebP for preview) |
| Full PNG | 260.4 MB | no — local `full-raster` authority only |
| Print PDF | 753.2 MB | no (Pages 1 GB soft limit) |
| Master SVG | 2,110.3 MB | no |
| Whole tree | ~3.4 GB | no |

Useful tiers:

| Tier | Families | Size |
| --- | --- | ---: |
| `preview` | thumbnail + screen-1080p WebP | ~66 MB |
| `browse` | `preview` + full-resolution WebP | ~102 MB |
| `full` | everything | ~3.4 GB |

Measured 2026-08-25: deriving the full-size family as lossy WebP (quality 90)
from the full PNGs yields 34,862,162 bytes across 217 artifacts — about 13%
of the 260.4 MB PNG family — at unchanged 3840-pixel-longest-side
dimensions. The staged `browse` tree is 101,811,924 bytes total. The lossy
WebP is a preview-only access derivative; the lossless full PNG remains the
`full-raster` authority in AAO and `assets.generated/png/`.

The committed/deployed TOT variant is `browse`; master SVG and print PDF stay
local-only. A local-only TOT preview can stage `full` and has no size
constraint.

### 2.5 Existing staging precedent

`scripts/build-generated-assets-s3-release-v14.sh` already produces the
product layout offline: it reads the frozen Stage-14 input fixture, gzips
masters, copies PDF/PNG/screen/thumbnail families, and writes a README plus
metadata. The TOT stager is the same operation with two differences: the
input is the live catalog instead of a frozen fixture, and the destination is
the repo-local `assets.tot/` instead of the upload staging tree.

## 3. Requirements

R1. Both backends are selectable; the live default is `tot`, and `aao` is a
manual dispatch deployment.

R2. The `tot` backend works fully offline: no DNS resolution of the Berkeley
host, no VPN, no network fetch, all artifacts served from the same site.

R3. One source tree; no duplicated gallery/contact-sheet pages.

R4. The layered-SVG viewer works for the `aao` backend and for local
`full`-tier `tot` previews; a deployed `browse`-tier `tot` site omits the
layered-SVG action instead of linking to a missing master.

R5. Both configurations pass the documentation gates; the `tot` build has no
broken artifact links.

R6. A TOT snapshot records its source revision and is detectable as stale.
TOT is deliberately mutable; it never claims AAO immutability.

R7. Repository and Pages footprint stay bounded; nothing over the Pages
1 GB soft limit is committed.

R8. Bumping the AAO backend from v14 to v15 is a one-value change once that
deposit exists.

R9. The `tot` snapshot is the live GitHub Pages deployment by default.
Deployments record the snapshot's source revision and are never described as
an AAO deposit; switching to `aao` is an explicit, committed edit to
`.github/deploy-backend` that persists until changed again.

## 4. Proposed design

### 4.1 Backend selector in site config

Keep the two bases as flat site keys so the override file only flips the
selector (a nested map would be wholesale-replaced by Jekyll config merging):

```yaml
# _config.yml — backend keys and fallback default. The authoritative
# deployment choice is .github/deploy-backend, applied by the workflow.
image_backend: tot
image_backend_aao_label: "AAO v14 (immutable)"
image_backend_aao_base: https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14
image_backend_aao_viewer: /docs/releases/viewer.html
image_backend_aao_full_suffix: .png
image_backend_aao_full_label: "Full PNG"
image_backend_aao_layered: true
image_backend_aao_print: true
image_backend_tot_label: "Top of tree (snapshot)"
image_backend_tot_base: /assets.tot
image_backend_tot_viewer: /docs/releases/viewer.html
image_backend_tot_full_suffix: .webp
image_backend_tot_full_label: "Full WebP"
image_backend_tot_layered: false
image_backend_tot_print: false
```

```text
# .github/deploy-backend — the persisted deployment choice; edit and commit
# to switch, because both are read by the one Pages workflow.
tot
```

```yaml
# _config.aao.yml — applied when .github/deploy-backend selects aao
image_backend: aao
```

```yaml
# _config.tot.yml — parity override for local previews:
# bundle exec jekyll serve --config _config.yml,_config.tot.yml
image_backend: tot
```

A shared include resolves the active backend and derives the values every
gallery include already uses:

```liquid
{% if site.image_backend == "tot" %}
  {% assign release_base = site.image_backend_tot_base | relative_url %}
  {% assign viewer_base = site.image_backend_tot_viewer | relative_url %}
  {% assign backend_label = site.image_backend_tot_label %}
  {% assign full_suffix = site.image_backend_tot_full_suffix %}
  {% assign full_label = site.image_backend_tot_full_label %}
  {% assign show_layered = site.image_backend_tot_layered %}
  {% assign show_print = site.image_backend_tot_print %}
{% else %}
  {% assign release_base = site.image_backend_aao_base %}
  {% assign viewer_base = site.image_backend_aao_viewer %}
  {% assign backend_label = site.image_backend_aao_label %}
  {% assign full_suffix = site.image_backend_aao_full_suffix %}
  {% assign full_label = site.image_backend_aao_full_label %}
  {% assign show_layered = site.image_backend_aao_layered %}
  {% assign show_print = site.image_backend_aao_print %}
{% endif %}
```

`relative_url` makes the TOT paths correct both locally (empty `baseurl`,
`/assets.tot`) and on Pages (`/cartofreako/assets.tot`); the AAO value is an
absolute URL and is copied through untouched. This is Liquid 4, which the
current GitHub Pages Jekyll already uses.

### 4.2 One shared include

New `_includes/image-backend.md` holds the snippet above. Every consumer
replaces its hardcoded assigns with `{% include image-backend.md %}`:
`generated-snapshot.md`, the two pass/projection galleries,
`docs/pages/gallery/README.md`, and the preview table in `index.md`. Path
construction stays byte-identical to today (the product layout), so no
per-backend filename or extension logic is introduced anywhere.

The places that are not path-only need a small branch:

- `generated-snapshot.md`'s completion-marker link points at `release.json`
  for `aao` and at `assets.tot/manifest.json` for `tot`.
- The contact-sheet "Full PNG" action becomes "Full WebP" with the
  `full_suffix`/`full_label` knobs; only the `full/` extension and label
  differ, nothing else in the path.
- The **Layered SVG** and **Print PDF** actions render only when
  `show_layered`/`show_print` are true. A deployed `browse`-tier TOT snapshot
  has neither family, so the actions are omitted rather than left as broken
  links; AAO keeps all four actions. This makes a deployed TOT site
  raster-only by design.
- The v14-specific prose ("sealed v14 release", "33 standard passes in the
  complete v14 generated-assets release") becomes backend-aware via
  `backend_label`, or moves to a neutral phrase ("the selected image
  backend"). The corpus facts themselves (33 passes, six projections) stay.

### 4.3 Top-of-tree staging

`scripts/build-tot-preview.sh` (implemented 2026-08-25), modeled on
`scripts/build-generated-assets-s3-release-v14.sh` but catalog-driven and
destination-local:

1. Read `assets.generated/catalog/artifacts-v1.json` for every standard
   artifact's `projectionId` and the parent/screen paths.
2. Emit `assets.tot/products/standard/<projection>/{master,print,full,thumbnail,screen-1080p/{png,webp}}/`
   using the catalog paths (this also places the five Myriahedral slices in
   their own projection directories).
3. Derive the `full/` family as WebP from `parents.fullPng` via ImageMagick:
   lossy `--webp-quality` (default 90) or `--webp-lossless`, converted with
   `--jobs` workers. Dimensions are preserved; quality/mode are recorded in
   the manifest. Full PNG is not copied in `preview`/`browse` tiers.
4. Gzip any master SVG that is not already gzipped
   (`gzip --best --no-name`) in the `full` tier, matching the AAO builder.
5. Write `assets.tot/manifest.json` (tier, `sourceRevision`, artifact and
   projection counts, emitted families, stored bytes, WebP mode/quality, and
   an explicit mutable-preview statement) plus a short `assets.tot/README.md`.
6. Accept `--tier preview|browse|full` (section 2.4); `full` requires
   `--allow-oversize`. The output tree is replaced atomically via a temp
   directory, so restaging never leaves a half-written snapshot.

The run that staged the current snapshot produced 217 full WebPs, 217
screen WebPs, 198 thumbnails, and 101,811,924 stored bytes. Its manifest
records `sourceRevision.gitCommit = 66922af…`, matching `HEAD`, so
`make check-tot-snapshot` passes.

### 4.4 Viewer

Add `docs/releases/viewer.html` with Jekyll front matter (`layout: none`) and
`{% include image-backend.md %}` so the build injects the active base:

```javascript
const releaseBase = {{ release_base | jsonify }} + "/";
```

The asset validation regex and DecompressionStream flow stay unchanged
because both backends use the same product layout. In `tot` builds the fetch
is same-origin, so the CORS fallback message is never triggered; in `aao`
builds the behavior matches the existing `v14-aao-viewer.html`. Keep
`v14-aao-viewer.html` untouched for existing absolute links, and point the
includes at `viewer_base` so the correct viewer is used per backend.

The viewer matters on a deployed TOT site only if the `full` tier is present
(master SVGs). The committed `browse` tier has no master family, so a
deployed TOT site suppresses the **Layered SVG** action per section 4.2; the
viewer remains in use for AAO and for local `full`-tier previews.

### 4.5 Runtime toggle — rejected (D1)

A client-side runtime toggle (bundle both backends into one deployment and
flip them with JavaScript) was considered and rejected: the switch is
build-time only. GitHub Pages still serves one live site per repository, so
AAO and TOT are deployed one at a time via the two workflows in section 4.6.

### 4.6 Deploying the TOT snapshot to GitHub Pages

Adopt the tracked-snapshot path so the TOT build is reproducible on the Pages
runner and the deployer needs no VPN either:

- Track `assets.tot/` in `main`. The repo `.gitignore` catch-all `/assets.*/`
  already matches that path, so add one explicit re-include after it:

  ```gitignore
  !/assets.tot/
  ```

- Commit the `browse` tier (~102 MB): thumbnails, screen-1080p WebP, and
  full-resolution WebP, so the **Full WebP** action resolves on the deployed
  snapshot. Master SVG and print PDF stay out of Git and out of Pages, which
  makes a deployed TOT site raster-only: the **Layered SVG** and **Print
  PDF** actions are omitted there (section 4.2). `preview` remains available
  for quick local-only checks, and `browse` is the ceiling for any TOT
  deployment.
- Restage the snapshot on a machine that has `assets.generated/`:

  ```sh
  scripts/build-tot-preview.sh --tier browse
  git add assets.tot
  git commit -m 'Refresh top-of-tree preview snapshot'
  ```

  Every restage rewrites the tree and grows history by the compressed delta,
  so restage at release or color-revision boundaries rather than per commit.
  Publishing the snapshot as a GitHub release asset and downloading it in CI
  keeps history lean but adds a second artifact flow; tracked-in-main is the
  simpler baseline.
- Single-live-site constraint: GitHub Pages serves one site per repository,
  so `aao` and `tot` cannot both be live at the same URL. Deployment is a
  persisted, committed choice (D7), not a merge or a dispatch input:

  - One workflow reads `.github/deploy-backend` (`tot` or `aao`), validates
    the value, and builds with the matching config:
    `bundle exec jekyll build --config _config.yml,_config.aao.yml` for
    `aao`, or the default config for `tot`.
  - Switching backends is an edit to `.github/deploy-backend` plus a commit
    and push; the choice persists until the next edit, including across
    unrelated pushes.

  The stock `jekyll-build-pages` action cannot read that file conditionally,
  so the workflow runs Jekyll directly: `Gemfile` pinned to the
  `github-pages` gem, `ruby/setup-ruby`, `bundle install`, then
  `bundle exec jekyll build`.
- Staleness: the workflow runs `make check-tot-snapshot` before deploying
  whenever `.github/deploy-backend` selects `tot`, so a snapshot whose
  recorded `sourceRevision` is older than `HEAD` cannot be published under
  the live default.
- Governance: a TOT Pages deployment is a mutable preview publication. It
  never updates the AAO release records and must not be described as an AAO
  deposit. The deployed pages carry `backend_label` ("Top of tree (snapshot)"),
  so the mode is visible on the site itself.

### 4.7 Staging-core refactor and local-layout adoption (D5)

Decision: refactor the release-tree builder into a shared core rather than
duplicating it, and consider adopting the AAO product layout as the local
generation output if that simplifies the pipeline.

- **Shared core now.** The TOT stager (4.3) repeats the v14 builder's
  family mapping. Extract one shared core consumed by both: it takes a case
  stream (`id`, `lifecycle`, `projectionId`, master/print/full/screen paths,
  thumbnail availability) plus tier/family flags and emits the product
  layout. The v14 builder keeps its frozen-fixture CLI and delegates to the
  core; its output must stay byte-identical (prove with a rebuild against the
  frozen Stage-14 fixture) so the v14 release record is untouched. The TOT
  stager feeds the live catalog to the same core.
- **Local-layout adoption — considered, deferred.** Making the local
  `assets.generated/<projection>/{svg,pdf,png,thumbnail,screen-1080p*}` tree
  adopt `products/<lifecycle>/<projection>/{master,print,full,thumbnail,screen-1080p/*}`
  would delete the family rename and the master gzip step from every stager.
  But the projection-first layout is load-bearing well beyond staging: it is
  defined by the Makefile `generated_artifact` helper and `GENERATED_*_DIRS`
  variables, enforced by `scripts/generate-standard-artifact-manifest.mjs`
  (`assets.generated/<proj>/svg/<stem>.svg`), and consumed by
  `scripts/generate-screen-1080p.mjs`, `scripts/check-print-pdfs.sh`, the
  Stage-15A freeze fixture, and test expectations. Adopting the product
  layout locally is a corpus-ABI change: it rewrites those consumers,
  re-freezes the Stage 15A GPU benchmark inputs on the release host, and
  updates the layout narrative in the generation docs. It does not simplify
  the immediate TOT feature, because the catalog already carries canonical
  parent paths and one stager sidesteps the layout difference. Schedule
  local-layout adoption as its own follow-on only when a future release
  rewrite already forces the re-freeze.

## 5. Options compared

| Option | Offline | Live on Pages | Repo cost | Complexity |
| --- | --- | --- | --- | --- |
| O1 build-time config switch, local TOT preview | yes (local preview) | AAO only | none tracked | low |
| O2 O1 + tracked `browse` tier, deploy to Pages via `.github/deploy-backend` | yes (deployed) | one at a time | ~102 MB | medium |
| O3 O1 + runtime client-side toggle, both backends live | yes | both at once | ~102 MB | rejected (D1) |

Rejected alternative: pointing `tot` directly at the projection-first
`assets.generated/` layout with per-backend path templates. It spreads
family/extension differences through every include and breaks the viewer's
single `master/*.svg.gz` assumption for no benefit; staging into the product
layout once (4.3) keeps every path identical except the backend-selected
`full/` extension and label.

Selected: O2 — the build-time switch plus a tracked, deployable `browse`
snapshot. O3 is rejected per D1.

## 6. File-level change list

New files:

- `_includes/image-backend.md` — backend selector and base derivation
  (implemented).
- `scripts/build-tot-preview.sh` — catalog-driven TOT staging (implemented).
- `scripts/lib-release-products.*` — shared release-tree core consumed by
  both the v14 builder and the TOT stager (D5).
- `docs/releases/viewer.html` — backend-aware viewer (implemented).
- `.github/deploy-backend` — the persisted deployment choice, `tot`
  (implemented).
- `_config.aao.yml` / `_config.tot.yml` — per-backend one-line overrides
  (implemented).
- `Gemfile` — pins the `github-pages` gem for the workflow's custom build
  (implemented; `Gemfile.lock` generated in CI or locally on first bundle).
- `assets.tot/` — committed `browse` snapshot (staged 2026-08-25; 632
  objects, 101,811,924 bytes).

Modified files:

- `_config.yml` — add the backend keys with the `tot` fallback (implemented).
- `_includes/generated-snapshot.md`, `_includes/v14-pass-gallery.md`,
  `_includes/v14-projection-gallery.md` — consume the shared include; remove
  hardcoded bases; branch the completion-marker link; neutralize v14 prose
  (implemented).
- `docs/pages/gallery/README.md` — consume the shared include (implemented).
- `index.md` — replace absolute S3 thumbnail URLs and the v14 narrative with
  the derived base (implemented).
- `docs/pages/README.md`, `docs/pages/releases/README.md` — state that the
  release browser is backend-selectable and name the default (implemented).
- `.github/workflows/jekyll-gh-pages.yml` — reads `.github/deploy-backend`,
  verifies the TOT snapshot when selected, builds with the matching config,
  checks rendered links, and deploys to Pages (implemented).
- `.gitignore` — re-include the tracked snapshot (`!/assets.tot/`) after the
  `/assets.*/` catch-all (implemented).
- `Makefile` — `build-tot-preview` and `check-tot-snapshot` convenience
  targets wrapping the script and the staleness comparison (implemented).
- `scripts/check-doc-links.py` — rendered-site `--walk` mode for `_site/`
  (implemented; wired into the workflow).

## 7. Verification

1. **Both configs build.** `jekyll build` (TOT default) and
   `jekyll build --config _config.yml,_config.aao.yml`; diff the two
   `_site` trees to confirm only image bases and the marker/narrative text
   differ.
2. **Offline proof for TOT.** In the TOT build, assert no generated page
   references `s3-ewh.ist.berkeley.edu` (`rg` over `_site/`), and load the
   gallery plus one full WebP with headless Chrome
   (`google-chrome --headless=new`) while network is unavailable.
3. **Rendered link check.** `scripts/check-doc-links.py --walk _site`
   validates every rendered `src`/`href` against files on disk and flags
   missing objects; the workflow runs it after the build. The source-level
   `make check-docs` must still pass with no network access.
4. **Staleness gate.** `make check-tot-snapshot` compares
   `assets.tot/manifest.json` `sourceRevision` to `git rev-parse HEAD` and
   fails when the snapshot predates the tree; the workflow runs it. It
   passes against the staged snapshot at `66922af…`. The workflow runs it
   only when `.github/deploy-backend` selects `tot`.
5. **WebP derivative checks.** Every `full/*.webp` must report the same
   dimensions as its `parents.fullPng` and a non-empty size; the manifest
   must record the quality/lossless mode actually used. (Verified on the
   staged snapshot: 217 full WebPs at 3840-pixel-longest-side dimensions,
   34,862,162 bytes.)
6. **Deployed acceptance.** With `.github/deploy-backend` set to `tot`, load
   the live Pages site from `rizal` with the VPN off and confirm the gallery,
   contact sheets, thumbnails, and full WebPs all resolve same-origin (zero
   requests to `s3-ewh.ist.berkeley.edu` in the network log). The **Layered
   SVG** and **Print PDF** actions must be absent, not broken.
7. **Regression.** A full `make check-docs` run and one manual gallery
   click-through per backend before committing, plus a re-deploy of the AAO
   build to confirm the switch back is clean.

## 8. Open decisions for the reviewer

D1. Resolved: build-time only. No runtime client-side toggle.

D2. Resolved: `assets.tot/` is tracked in `main` so the snapshot is
deployable (section 4.6).

D3. Resolved: the committed and deployed snapshot is the `browse` tier, and
`browse` is the ceiling for TOT deployments. Refined 2026-08-25: the
full-size family is lossy full-resolution WebP (q90) derived from the full
PNGs, not full PNG — ~102 MB staged instead of ~326 MB. `preview` is a
local-only convenience tier; the PNG `full-raster` authority stays out of
the deployed snapshot.

D4. Resolved as proposed: one `docs/releases/viewer.html` with Jekyll front
matter injecting the active backend base.

D5. Resolved: extract the shared release-tree core; adopt the AAO layout
locally only as a follow-on when a release rewrite forces the Stage-15A
re-freeze (section 4.7).

D6. Resolved: AAO default stays `v14` until the v15 AAO deposit's receipt is
checked in; only then does the registry bump to `v15`.

D7. Resolved: TOT is the live default and the choice persists by recording
the desired deployment backend in the committed `.github/deploy-backend`
file, which the single Pages workflow reads on every build. Switching is an
edit plus commit and push, not a dispatch input.

## 9. Sequencing

1. Stage 1 — this proposal; D1–D6 resolved.
2. Stage 2 — done: backend keys, `.github/deploy-backend`,
   `_includes/image-backend.md`, the retargeted includes, gallery README,
   `index.md`, the narrative docs, the unified viewer, the `Gemfile`, and
   the rewritten workflow. `make check-docs` passes.
3. Stage 3 — done: `scripts/build-tot-preview.sh`, the `browse` snapshot in
   `assets.tot/`, the `.gitignore` re-include, and the `build-tot-preview` /
   `check-tot-snapshot` Make targets.
4. Stage 4 — done: backend-aware `docs/releases/viewer.html` and the
   rendered-site `--walk` link mode. Remaining verification: local
   `jekyll serve` preview, offline proof, and viewer click-through in both
   backends.
5. Stage 5 — extract the shared release-tree core (D5); commit and push this
   change set; confirm the TOT deployment on Pages and exercise one AAO
   switch via `.github/deploy-backend`.
6. Stage 6 — final regression and documentation of the deploy-backend
   procedure in the release runbook.
