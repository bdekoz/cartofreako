# Setouchi 2028 futures: image grids, website publishing, and outreach

Date: 2026-11-06. Status: local update prepared and validated; current presentation saved; separate H3r5/H3r8 trials completed and validated; WordPress publication deferred.

## Task and accumulated decisions

Add a visual introduction to [Cartofreako × Setouchi](https://benjamin.dekosnik.com/futures/setouchi-2028/),
**after the three existing lists and before “Two atlases, one shared table.”**
The requested subjects are the Starlink observer plate, Water, Network Fiber,
Atmosphere, and Anthropocene Temperature. Consider separate World and Japan
grids, include two or three segmented Hamonshū review images, and adopt the
typography and design of the existing
[Star-X Internet Maps page](https://benjamin.dekosnik.com/work/202x/star-x-internet-maps/).
Include a script-based publishing workflow that avoids routine WordPress UI
work. Finish with contact approaches for AuthaGraph author Hajime Narukawa.

The plan was approved, followed by the instruction to **prepare the local
update first**. The [local preview](../../output/setouchi-futures-20261106/index.html),
image package, publishing script, and unsent illustrated outreach brief are
prepared. The website, its media library, and its theme have not been changed.
No outreach has been sent. Exact live typography and authenticated publishing
remain to be checked through a supported site connection.

## Current saved settings — 6 November 2026

The [active manifest](../../config/setouchi-futures-20261106.json) and
[saved baseline](../../config/setouchi-futures-20261106-baseline.json) record
the approved local World/Japan presentation through implementation commit
`6fd6433`. The baseline is an exact copy of the settings used by the current
prepared artwork. Its SHA-256 is
`9b7c40362b6fcc2204462b21d9758e79f0419635148a5f6533126e80473eb6ae`.
It preserves the validated H3r3 edition before the subsequent H3r8 request.

| Setting | Saved value |
| --- | --- |
| Geographic composition | Modified Setouchi AuthaGraph with the existing horizontal adjustment; World and Japan views. |
| Default artwork colors | Wine `#240413` background; amber `#fcc553` submarine routes at full opacity; retained thematic and satellite-vendor colors. |
| Atmosphere background | Light amber `#fcc553`, `rgb(252,197,83)`, for both views and their thumbnail frames. |
| Atmosphere land outlines | White `#ffffff`, full opacity, in the final top layer; nominal **0.66 pt** in both views, including relocated Antarctica. Japan magnification is compensated; the outer frame gives **0.6525 pt** on the 44-inch sheets. |
| Solar-radiation opacity | **100** equally spaced levels from 0 to 1, selected per measured cell on a shared **0–400 W/m²** scale. Preserve gold strokes, source widths, and missing observations. |
| Source snapshot | Pinned October atmosphere profile and GeoJSON; radiation observation ends **15 October 2026, 23:59 UTC**. Current H3r3 artwork has 30,982 radiation cells and 98 occupied opacity levels. |
| Image delivery | 640/1280-pixel cards, 3840-pixel full-sheet details, separate legend/source PDFs. |
| Japan card crops | Water, Atmosphere, and Temperature: `[0.5, 1.75, 29.1, 17.25]` inches. Full sheets remain linked; Fiber and Observer retain the full composition. |
| Gallery layout | Two geographic rows of two maps, then a full-width observer panorama per scope; three Hamonshū crops in equal 4:3 frames; stacked phone layout. |
| Website scope | Local insertion after the three lists and before “Two atlases, one shared table”; existing theme typography inherited when published. |

Reproduce this saved edition from the repository root:

```sh
python3 scripts/update-setouchi-futures.py prepare \
  --manifest config/setouchi-futures-20261106-baseline.json --workers 2
```

The saved settings match the current `prepared.json` configuration and its
validation receipt. Print atlas masters remain the upstream sources; this
checkpoint applies to the local website package. WordPress publication and
outreach remain deferred. The revision notes below preserve the sequence of
decisions; the table above is the authoritative saved presentation.

## Recommended composition: two grids and a Hamonshū strip

Use **static grids with links to larger images**. Readers can scan the subjects
and compare the World and Japan editions without operating a carousel. The
layout also works with ordinary links and images before JavaScript loads.
A carousel can be reconsidered for an expanded portfolio, but it adds navigation
and hides examples in this short introduction. Avoid automatic advancement.

Reading order:

1. Existing introduction and three lists.
2. **World** image grid.
3. **Japan / Setouchi** image grid, in the same subject order.
4. **Hamonshū Revisited**: three individual images presented as a triptych.
5. Existing **Two atlases, one shared table** section.

Use five subjects per grid for the initial proposal. “Starlink global observer”
is interpreted as the World edition's `orbital-technosphere-observer` plate.
An optional sixth selection is
`orbital-technosphere-global`: if both orbital subjects are wanted, add the
geographic global-orbit plate to both grids, making six images per grid.
The observer view and the geographic orbit view remain separately captioned.

The implemented five-subject layout uses **two rows of two geographic maps,
followed by a full-width observer panorama** in each grid. This refines the
initial three-plus-two suggestion: core WordPress Columns blocks provide a
simple mobile stack, while the dense observer sky gets more room. The three
Hamonshū images use one three-column row. Use the same ordering in the DOM,
on screen, and in keyboard navigation. Confirm the actual theme's content
width when site access is available.

Each image gets a short visible title, one concise caption, a full-image link,
and a quieter **Legend & sources** link. Keep the detailed legend on its
separate sheet. The thumbnails introduce the work; satellite IDs and small
cartographic labels are read in the larger view.

## Map selections and captions

Use the current atlas composition in `output/atlas/`, which adopts the approved
MSP 5 wine/amber presentation, the Setouchi horizontal adjustment, and separate
map and legend sheets. Preserve source data colors and distinct satellite
vendor colors. The website's surrounding typography and background follow its
existing theme; wine/amber belongs to the artwork.
The subsequent atmosphere revision uses the pair's lighter amber `#fcc553`
as the background for both World and Japan web plates.

| Order | Subject / source stem | World image and suggested caption | Japan image and suggested caption |
| --- | --- | --- | --- |
| 1 | Water / `water` | **Water — World.** Rivers, coastlines, and generalized ocean depths. Strong opening image connecting the atlas to the sea and the Hamonshū workshop. | **Water — Japan / Setouchi.** Japan and its surrounding seas, with the Setouchi locator retained. |
| 2 | Network Fiber / `network-fiber` | **Fiber — World.** Submarine and terrestrial cable routes connect continents; route locations are schematic. | **Fiber — Japan / Setouchi.** Cable landings and terrestrial routes place Japan within wider communications networks. |
| 3 | Atmosphere / `cloud-atmosphere` | **Atmosphere — World.** Cloud, precipitation, aerosol, and radiation observations from 15–29 October 2026. | **Atmosphere — Japan / Setouchi.** The same dated atmospheric layers at the regional scale; missing daytime cloud retrievals do not mean clear sky. |
| 4 | Anthropocene Temperature / `anthropocene-temperature-2026` | **Temperature records — World, 2026.** Daily land-temperature record counts through 28 October 2026. | **Temperature records — Japan / Setouchi, 2026.** The same record-count classes in the Japan viewport, through 28 October 2026. |
| 5 | Orbital Technosphere: observer / `orbital-technosphere-observer` | **Starlink and the orbital sky — World atlas.** San Francisco observer reference, 3 November 2026, 17:10 UTC; Starlink names and distinct vendor symbols. | **Starlink and the orbital sky — Setouchi.** Observer at 34.45° N, 133.99° E, 29 October 2026, 20:00 UTC; sky field and Japan locator together. |

The observer plates show calculated satellite positions from particular
observation points. They are not maps of worldwide satellite coverage, and
the two dates do not support a same-instant observer comparison. The Japan
observer retains its October positions with the November presentation.

Temperature is a **count of record days**, not a temperature anomaly or a
complete 2026 annual result. Preserve the common count classes and the source
qualifications. The 2025 plate is available as a later comparison, but adding
both years would make this introduction longer without satisfying a new request.

Source paths, with `{scope}` equal to `world` or `japan` and `{stem}` from the
table:

- Map master: `output/atlas/maps/{scope}/svg/{stem}.svg`.
- Legend master: `output/atlas/legends/{scope}/svg/{stem}-legend.svg`.
- Existing observer preview:
  `output/atlas/maps/{scope}/preview/orbital-technosphere-observer.png`.
- Bibliography and interpretation:
  `output/atlas/plate-source-bibliography.json`.

All ten requested map SVGs exist. The two observer previews already exist.
Eight additional screen proofs were rendered from the current SVGs and
visually inspected for this plan; they were temporary research exports.
The older ST2 and published October review editions remain useful references,
but should not silently substitute for the November orbital artwork.
See the [atlas presentation guide](../pages/getting-started/generation-styles.md#setouchi-st2-print-layout)
and the [dated public review gallery](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/).

### Findings to address while preparing web images

- **Fiber needs a contrast adjustment.** In both current wine/amber screen
  proofs, black submarine lines nearly disappear into the dark ocean. Prepare
  a documented web variation with amber submarine routes and retained green
  terrestrial routes, with enough opacity to survive reduction. Update its
  matching legend swatches. Keep the route geometry and source dates intact.
  The lighter ST2 rendering is a usable fallback if the dark variation does
  not reproduce the networks clearly.
- **Japan sheets have unused space.** The terrestrial data occupies the left
  part of the separated print sheet. Define explicit thumbnail crop bounds
  that remove unused sheet space while keeping the full intended regional
  extent, data marks, and locator. Fiber routes can extend farther right than
  the land frame; account for them when defining bounds. Link the complete
  sheet from the thumbnail. Use the full observer composition so its locator
  remains associated with its sky field.
- **Atmosphere has uneven observations.** Preserve its actual footprint and
  source dates. The absent daytime cloud retrievals in the Japan snapshot
  should be explained in the caption and legend.
- **Small labels need enlargement.** Retain the approved six-point Starlink
  text and marker settings in the source plate. Supply a larger linked image
  instead of enlarging source type solely for a thumbnail.

## Hamonshū: three specific segmented images

Use one selection from each book. They move from a simple repeating motif to
a flowing field and then an expressive wave. These are scanned book details,
not photographs of a completed Setouchi workshop. The descriptive labels below
are editorial captions, not approved categories in the Hamonshū review system.

| Selection | Review image | Why it belongs / suggested alt text |
| --- | --- | --- |
| Book 1, scan 005, segment e | [hamonshu_1-005e.jpg](https://situationshipin.space/review/hamonshu-v2-book1/images/hamonshu_1-005e.jpg) | Repeating semicircular arcs establish a simple pattern. Alt: “Overlapping groups of concentric wave arcs, printed in dark ink on aged paper.” |
| Book 2, scan 003, segment a | [hamonshu_2-003a.jpg](https://situationshipin.space/review/hamonshu-v2-book2/images/hamonshu_2-003a.jpg) | Dense, sweeping currents connect historical linework with the water and fiber maps. Alt: “Interlacing curved lines form a field of flowing water and small eddies.” |
| Book 3, scan 003, segment f | [hamonshu_3-003f.jpg](https://situationshipin.space/review/hamonshu-v2-book3/images/hamonshu_3-003f.jpg) | A dotted breaking wave adds a contrasting texture and focal point. Alt: “Curling wave shapes with dotted foam and broad dark areas.” |

Suggested shared caption: **Mori Yūzan, Hamonshū (1903). Three water-pattern
details, segmented for the Izzi review collection.** Link each detail to its
book review: [Book 1](https://situationshipin.space/review/hamonshu-v2-book1/),
[Book 2](https://situationshipin.space/review/hamonshu-v2-book2/),
[Book 3](https://situationshipin.space/review/hamonshu-v2-book3/).
Carry any additional scan-source credit from the source packet into the
expanded credit; do not infer a scanning institution.

Present three separate figures at equal visual height, with their full crops
contained inside the image area and the original paper color retained. Do not
stretch the crops or remove linework to force matching aspect ratios. Two
images also work: retain Book 2's current field and Book 3's dotted wave.
Keep this strip outside the World/Japan classification.

All three public image URLs returned HTTP 200 on 6 November and matched their
respective public manifest hashes. The proxies measure 1600 × 859,
1600 × 1003, and 1600 × 1259 pixels. Their SHA-256 values are:

```text
hamonshu_1-005e.jpg  72bf5cf9668930d34e29f64383699a913dec7d2456a1f29add579f9226730c0d
hamonshu_2-003a.jpg  4f37bd971f2e8cf112e5325c5b547f319ad238a6732ded784239ea8c2b134f5a
hamonshu_3-003f.jpg  c702e2aa6ccc78d1f84a0dc16176e91dde77498aa7cb22d0eed88893194edd38
```

The published manifests contain crop bounds and source-scan hashes:
[Book 1 manifest](https://situationshipin.space/review/hamonshu-v2-book1/manifest.json),
[Book 2 manifest](https://situationshipin.space/review/hamonshu-v2-book2/manifest.json),
[Book 3 manifest](https://situationshipin.space/review/hamonshu-v2-book3/manifest.json).

## Typography and page design

The Star-X page is the **web typography and spacing reference only**; it does
not change the modified AuthaGraph map projection. Reuse the site's active theme and
native content blocks for headings, body copy, image captions, links, image
alignment, and section spacing. Inherit font families, weights, line heights,
and colors. Add only the local gallery layout rules needed for the grids.
The atlas's print type sizes do not determine the web caption size.

Both the Setouchi and Star-X URLs returned **HTTP 403** to direct automated
reads on 6 November; the public WordPress page endpoint did too. Exact live
font names, computed sizes, theme content width, and current block structure
have therefore not been verified. Do not invent those values or describe the
old local preview as the current published design.

The existing generated WordPress package identifies page **3175**, but its
saved content predates the user's three-list layout. During implementation,
fetch the current page, validate its permalink, and inspect the live Star-X
markup/styles or the corresponding installed theme files. Record the measured
heading, body, caption, image-spacing, and content-width values at desktop and
phone widths. Use that comparison to finish the layout.

Prefer core Gutenberg Group, Heading, Columns/Gallery, and Image blocks with
real media IDs. Use a scoped class such as `setouchi-futures-gallery` if extra
layout CSS is needed. Preserve normal full-image links; an existing theme
lightbox may enhance them. The accessible reading order, visible captions,
and keyboard focus must work without a custom gallery script.

## Scripted website updates

Automated page and media updates are supported by WordPress. The available
transport for this installation still needs to be established. The new
publisher replaces the earlier manual media-upload and block-paste step;
the existing proposal builder is retained.
See the [previous delivery record](20261101_setouchi_triennale_proposal.md).

Durable entry point: `scripts/update-setouchi-futures.py`, with a
versioned content manifest at `config/setouchi-futures-20261106.json` and
generated assets under `output/setouchi-futures-20261106/`. These paths and
commands are now implemented. See the
[delivery README](../../output/setouchi-futures-20261106/README.md) for setup,
rebuild, credential handling, publication, and recovery instructions.

### Transport choices

| Route | Requirements | Intended use |
| --- | --- | --- |
| **WP-CLI over SSH** | Authorized SSH access, WordPress installation path, and WP-CLI on the host. | Prefer when available. Read the actual page/theme, import media, and update page 3175 from the server. Routine updates need no web UI. See [post update](https://developer.wordpress.org/cli/commands/post/update/) and [media import](https://developer.wordpress.org/cli/commands/media/import/). |
| **WordPress REST API** | Reachable HTTPS API and an account with page-editing/media-upload permissions, authenticated with an application password. | Use authenticated page reads, media uploads, and a targeted page-content update. See [Pages](https://developer.wordpress.org/rest-api/reference/pages/), [Media](https://developer.wordpress.org/rest-api/reference/media/), and [authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/). |

Use a named SSH configuration entry or credentials supplied through a local
secret store/environment. Do not put passwords in the manifest, repository,
CLI arguments, or logs. If an application password must be provisioned and
SSH is available, WordPress supports doing so with
[WP-CLI](https://developer.wordpress.org/cli/commands/user/application-password/create/).
Neither SSH access nor an authenticated REST connection has been tested in
this task. The observed HTTP 403 must be resolved through the site's supported
access path; do not assume it proves a missing password or a disabled REST API.

### Implemented command behavior

```sh
# Local preparation; no credentials or remote writes.
python3 scripts/update-setouchi-futures.py prepare --manifest config/setouchi-futures-20261106.json
python3 tests/test-setouchi-futures.py
python3 tests/test-setouchi-radiation.py
python3 scripts/validate-setouchi-futures.py --browser

# Later, through the site's supported authenticated connection.
python3 scripts/update-setouchi-futures.py plan --page-id 3175 --transport rest
python3 scripts/update-setouchi-futures.py apply --plan output/setouchi-futures-20261106/private/publish-plan.json
python3 scripts/update-setouchi-futures.py verify --receipt output/setouchi-futures-20261106/private/publish-receipt.json --public
python3 scripts/update-setouchi-futures.py restore --backup /path/to/saved-page.json
```

`prepare` creates responsive images, Gutenberg blocks, and a local preview.
`plan` reads the current page and reports the exact content/media changes
without remote writes. `apply` executes that saved plan; it should not ask for
another web-UI operation. `verify` reads back the result. `restore` is an
explicit recovery command and never deletes uploaded media automatically.

The script implements these requirements:

1. Verify that page 3175 resolves to the requested Setouchi permalink. Save
   its raw content, status, parent, slug, template, modification time, and
   content hash before changes.
2. Identify the unique heading “Two atlases, one shared table” and the three
   preceding lists. Insert at that boundary. If the heading is missing or
   ambiguous, report the mismatch without guessing. Preserve the surrounding
   content, including edits made after the November proposal export.
3. Give the inserted Group block a stable anchor such as
   `setouchi-futures-visuals`. On subsequent runs replace that group, avoiding
   duplicate galleries. Prefer native blocks and theme styles to custom HTML
   or inline scripts that WordPress may sanitize.
4. Upload only new or changed image assets. Record source hashes, dimensions,
   crop bounds, credits, alt text, remote media IDs, and actual returned URLs
   in a persistent media manifest. Reuse those IDs on an unchanged rerun.
5. Save the planned base hash and re-read before applying. If another edit
   changed the page, rebuild the plan instead of overwriting it. A REST
   read-before-write check reduces races but is not an atomic compare-and-swap;
   both transports document that limitation. Avoid editing the same page
   during apply. Neither transport implements a database-level atomic update.
6. Update the managed gallery content while preserving the page's publication
   status, title, permalink, parent, and template. Record the resulting content
   and media receipt. Keep backup/state files outside the public asset set.
7. Read the page back and check that WordPress retained the blocks, captions,
   credits, and links. A successful API response alone is not a visual check.
   Validate the served page when access permits and report any remaining
   frontend access restriction separately.

The package contains 640/1280-pixel WebP derivatives and 3840-pixel map detail
images, with intrinsic dimensions and local `srcset`/`sizes`. WordPress media
IDs support the site's responsive-image generation when published. All figures
are lazy-loaded. Each map links to its complete sheet and matching legend PDF.
Hamonshū details link to the verified original 1600-pixel JPEG crops.

## Staging and completion criteria

| Stage | Status | Completion evidence / remaining work |
| --- | --- | --- |
| F01 — establish current page/style | Pending live access | Page 3175 is identified by the earlier package. Current raw content, insertion boundary, and measured Star-X typography still need authenticated/site access. |
| F02 — curate and export | Complete locally | Ten maps, ten legend PDFs, three Hamonshū crops; manifest with checksums, captions, dates, crop bounds, and credits. |
| F03 — compose | Complete locally; live theme pending | Two native grids and Hamonshū strip checked at desktop and phone widths. Preview type is explicitly temporary; published blocks inherit the theme. |
| F04 — automate | Implemented and tested offline | REST and SSH/WP-CLI transports; 23 publishing tests plus six radiation tests (29 total) cover publication guards and per-cell opacity/provenance. Actual server integration remains untested. |
| F05 — publish and verify | Deferred: local preparation first | No WordPress writes. Later: read current page, inspect plan, apply, verify saved content/media and frontend appearance. |
| F06 — prepare outreach | Prepared, unsent | Verified lab contact route, message draft, and one-page illustrated brief. Update the page before using the revised gallery link in outreach. |

The prepared insertion leaves the three existing lists followed by both image
grids and the Hamonshū strip, then the existing atlas section. The publisher
reads the current page and refuses missing or ambiguous insertion headings;
it never uses the stale November proposal export as replacement content.

## Local implementation record — 6 November 2026

The [preview](../../output/setouchi-futures-20261106/index.html) contains ten
map figures and three Hamonshū details. The
[manifest](../../output/setouchi-futures-20261106/prepared.json) records 49 media
files, of which 36 are used for eventual WordPress upload. The remaining
640-pixel derivatives serve the local responsive preview. Original atlas map
and legend masters remain unchanged; twenty source checksums were verified.

Both fiber variations recolor 767 submarine path elements to amber `#fcc553`
at full opacity, retaining line widths, dashes, geometry, and green land routes.
Three swatches and the explanatory text in each matching legend were updated.
Japan Water, Atmosphere, and Temperature thumbnails use bounds
`[0.5, 1.75, 29.1, 17.25]` inches on the print sheet. Complete detail images
remain linked. Fiber and observer compositions retain the full sheet so their
extended routes and sky locator are preserved.

The [entry point](../../scripts/update-setouchi-futures.py) supports `prepare`,
`plan`, `apply`, `verify`, and `restore`. Plans, before/after content, media state,
backups, and receipts use a private, Git-ignored directory. Content-addressed
media names allow reuse after interrupted uploads. Checks before and after
uploads detect page edits; readback checks saved content and metadata. Restore
refuses subsequent edits and never deletes uploaded media. The checked local
bundle contains no credentials or publication state.

Validation on 6 November:

- **29 offline tests passed**: 23 publishing tests plus six radiation tests.
  Publishing checks include preservation of surrounding content,
  duplicate-free reruns, stale title/content detection, upload interruption,
  concurrent edits during uploads and before readback, server filtering, and
  guarded restoration. Unexpected readback never authorizes automatic restore.
  Radiation checks cover the 100-level scale, per-cell opacity, retained
  geometry and widths, source identity, and missing-data guards.
- **Six Chrome captures** covered World, Japan, and Hamonshū at 1440 × 1100
  and 390 × 900. Images loaded and decoded before capture; phone figures stack,
  all thirteen images have alt text, and no horizontal overflow was found.
  Hamonshū frames have equal heights. The captures were visually reviewed.
- All local image, detail, and legend links resolve; media checksums match;
  both fiber legend texts match the amber web variation.
- The [illustrated brief](../../output/setouchi-futures-20261106/outreach/brief.pdf)
  fits one A4 page and was visually reviewed. It includes the World/Japan Water
  pair, one orbital example, and the three Hamonshū details.

Machine-readable results are in
[validation.json](../../output/setouchi-futures-20261106/validation.json).
Chrome proof captures stay in the ignored `build/setouchi-futures-qa/` directory.
No live WordPress authentication, media upload, editor round-trip, theme-layout
verification, or outreach delivery is claimed by these local checks.

### Atmosphere background revision — 6 November 2026

Replace the dark wine background on both Atmosphere web plates with the lighter
member of the selected Randoma11y pair: **amber `#fcc553`, `rgb(252,197,83)`**.
The per-subject setting is recorded in `config/setouchi-futures-20261106.json`
and applied by the durable builder to the sheet and nested background
rectangles. Each source has three matching rectangles; their paint changes
without changing observation geometry, data colors, opacity, or layer order.

Rebuilt all six atmosphere WebPs (640, 1280, and 3840 pixels for each scope),
and used the same amber behind the contained images in the gallery so Japan's
thumbnail framing does not retain dark side bands. The full-sheet links use
the revised background too. Alt text and provenance record the lighter ground.
This is a local website variation; atlas print masters retain their existing
presentation. The legend data keys and observation dates continue to apply.

Verification confirmed exactly three background-fill changes in each SVG,
with all geometry and data styles identical. The 23 publishing tests and
desktop/phone gallery checks passed; both revised image exports and their
gallery framing were visually reviewed.

### Atmosphere land-outline revision — 6 November 2026

Place land outlines above every atmospheric layer in both web plates. The
source coastlines were already last inside the shared data group, but their
thin amber strokes were faint against the newly amber background. The web
builder now separates those existing paths into a final `web-land-outlines`
layer and paints them white `#ffffff` at full opacity, following the user's
color correction. That first revision retained the original coastline geometry
and line widths; land remained unfilled. It used **0.5 pt for World** and
**1 pt for Japan**, approximately 0.494 pt and 0.989 pt after the Setouchi
framing scale. The subsequent common **0.66 pt** setting supersedes those
weights; responsive web previews scale the strokes with the image.

The World overlay preserves the three cyclic placements and their clipping,
and includes the relocated Antarctica coastline. Japan retains its viewport
clip and scaling. Coastlines are removed from the underlying data composition
to avoid drawing them twice. The final outline layer is above the complete
image composition. Atmospheric observations and the light amber ground retain
their prior settings. The six web derivatives were rebuilt, with overlay
settings recorded in the prepared manifest.

Structural checks verified all path geometry, data styles, line widths,
viewport transforms, and clips. World uses 4,343 coastline paths including
Antarctica; Japan uses 4,157. Both white-outline exports were visually checked.
The 23 publishing tests and desktop/phone gallery checks passed.

### Atmosphere saved outline weight — 6 November 2026

Set both white land outlines to a nominal **0.66 pt**, replacing the differing
World/Japan weights above. The durable `land_outline.width_pt` setting converts
points to SVG units and compensates for Japan's viewport magnification; the
World Antarctica inset uses the same weight. The common Setouchi frame scale
then produces **0.6525 pt** on the 44-inch sheets. Web previews scale the strokes
with the image. White, full opacity, top-layer placement, and the light amber
background remain the selected presentation.

Rebuilt all six atmosphere image derivatives and visually reviewed the World
and Japan previews. Every coastline path, including the World Antarctica inset, was checked at 0.66 pt
nominal. Other media and legends retain their previous bytes. The 23 publishing
tests and desktop/phone gallery checks passed.

### Radiation opacity by measured cell value — 6 November 2026

Make shortwave-radiation opacity respond to each cell's measured strength;
the follow-up instruction sets **100 opacity bands**. Both web plates use the
same fixed **0–400 W/m²** domain from the original atmosphere profile. Normalize
the value to that range, clamp to 0–1, and select the nearest of 100 equally
spaced opacity levels, including transparent and fully opaque endpoints:

```text
level = floor(clamp(value / 400, 0, 1) × 99 + 0.5)
opacity = level / 99
```

Use the matching archived JASMES observation ending **15 October 2026,
23:59 UTC**, within the 29 October atmosphere snapshot. It contains **30,982**
observed radiation cells, ranging from about **0.151 to 393.795 W/m²**. These
values occupy **98** of the 100 available levels; the two highest levels are
unused. Keep the common domain for World and Japan. Do not stretch each view
to a separate observed maximum or create values for missing observations.
The small observed values that quantize to zero opacity remain in the SVG;
transparent appearance does not prove missing data or an exact zero value.

The original renderer merged cells into six intensity paths. A new small
C++ exporter uses the existing H3 and AuthaGraph projection code to recover
the exact projected path for each archived cell. Before changing the layer,
the builder reconstructs the six original paths and checks their geometry,
counts, observation date, and dataset identity. It then groups by opacity.
The original gold stroke color, six source stroke widths, source geometry,
and radiation layer position are retained. A few opacity levels cross an
existing width boundary, so 98 occupied levels require **101 path groups**;
that does not add opacity levels. The white 0.66 pt land outline stays on top.

The durable settings live in `radiation_opacity` in the content manifest.
Implementation is in [setouchi_radiation.py](../../scripts/setouchi_radiation.py)
and [export-atmosphere-cells.cc](../../scripts/export-atmosphere-cells.cc),
with a Make target used automatically by `prepare`. The archived snapshot hash
is `2cc4b93634732766c71c9a8ba70406a94e276dcf9e4bce2e78c103644e748b0d`.
The profile hash is `90385c469a7d65775f990e51f75760e5d31ebf9563001e847fa81221cc8d2747`.
The prepared manifest records these inputs, the mapping, counts per level,
and the geometry check. Neither input is refreshed during a web rebuild.

Both companion legends gain a labeled 100-step opacity key against the amber
map background. Their missing-data wording distinguishes unobserved cells
from low-opacity observations. Six focused tests cover the full scale,
per-cell assignment, preserved geometry/widths, date mismatch, damaged paths,
duplicate/poor-quality cells, and missing-data guards.

Validation passed: 23 publishing tests plus six radiation tests, all source
checksums, both legend descriptions, and desktop/phone gallery checks. The
World and Japan exports and the new legend key were visually reviewed. The
only changed media are the six atmosphere images and their two legend PDFs.

### Uniform H3r8 analysis products — follow-up request

Use **H3 resolution 8 uniformly for the gridded analyses**, with World and
Japan drawing from the same dated products, units, quality rules, and missing
data policy. This is a new data-preparation requirement. The saved presentation
above and the current preview still use **H3r3** atmosphere and temperature
products; neither their metadata nor their grid identifiers have been relabeled.
No H3r8 replacement product was found in the local project inventory.

The proposed scope is every gridded analysis in these two galleries:
Atmosphere's seven observed layers and the 2026 temperature-record fields.
Water's coastlines, rivers, and bathymetric contours, Fiber's route geometry,
and Observer's calculated sky positions retain their native representations.
Atmosphere's calculated solar contours also remain vectors. The user was
asked whether the intended scope includes Temperature or is limited to
Atmosphere, and whether individual H3r8 cells should be drawn or aggregated
for legibility. The later request to try the four affected plates at **both
H3r5 and H3r8** resolves the trial scope: both subjects, both views, and actual
cells at each resolution. The controlled trials below supersede the pending
scope decision; an atlas-wide change of defaults remains separate.

#### Source and implementation findings

| Product | Current input | Work needed for H3r8 |
| --- | --- | --- |
| Atmosphere | October archived profile and snapshot at H3r3; all 25 original JAXA raster files are present. | Rebuild from the original rasters with a shared r8 policy. Review the current `maximum_samples_per_axis: 720` reduction before preparing finer cells. Preserve observation timestamps, quality masks, and nulls. |
| Temperature records | October archived H3r3 product; 96 staged NOAA CPC annual TMAX/TMIN files are present, with a 0.5° source grid. | Revise the preparation/storage contract before an r8 run. Preserve the 1979–2025 baseline, strict record comparison, minimum 30 history years, and 28 October cutoff. Recompute from daily inputs; record counts cannot simply be summed over spatial cells. |
| World / Japan pairing | Two viewports of shared geographic products. | Validate actual H3 identifiers as resolution 8 in every analysis product. Use the same underlying values for both views; cropping must not renormalize the radiation opacity scale. |

H3r8 has **691,776,122 cells globally**, with an average hexagon area of about
**0.737 km²**. These are grid statistics, not the spatial resolution of the
observations. See the [official H3 cell statistics](https://h3geo.org/docs/core-library/restable/).
At the baseline checkpoint, the temperature preparer enumerated every global
cell and allocated 416 calendar slots per cell for historical extrema and
history counts. At r8, those two arrays alone would require about **1.44 TB**
in decimal units. Its reader also required a fully enumerated global GeoJSON.
Changing only `h3_resolution` would therefore have been unsuitable; the trial
implementation below adds an explicit source-center domain.

Use tiled or partitioned processing with an explicit coverage/missing-data
contract. Finer indexing must retain the original source footprint and
effective observation resolution. Do not turn existing r3 means into claimed
independent r8 measurements, silently interpolate gaps, or interpret absent
sample centers as proof that the surrounding source pixel was unobserved.
For coarse rasters, choose and record the source-to-cell sampling or area
allocation method before making cross-layer comparisons.

#### Migration stages

1. **Inventory — complete.** Verify the current r3 profiles, locate their dated
   raw inputs, and save the validated visual baseline separately.
2. **Scope and representation — confirmed for the controlled trials below.**
   Atmosphere and Temperature, World and Japan, at both r5 and r8. Draw actual
   cells rather than a coarser display aggregation. Keep the analysis grid
   consistent across included subjects and both views.
3. **Prepare — complete for both trials.** Reaggregate the pinned raw samples
   at r5 and r8. Temperature's bounded source-center domain replaces the
   proposed global allocation; Atmosphere retains its observed-cell domain.
   Preserve units, source resolution, quality information, and nulls.
4. **Validate — complete for both trials.** Check actual H3 resolutions,
   declared domains, source hashes, and the unchanged daily-record method.
   World and Japan render the same validated products and share the fixed
   100-band radiation scale. No coarser display grid is substituted.
5. **Render and save — complete for both trials.** Save eight maps, separate
   legends, an r3/r5/r8 comparison gallery, and provenance. Desktop and phone
   checks pass. The H3r3 baseline remains available; adopting either trial as
   the atlas or website default is a separate decision.

The documentation/settings checkpoint at `1ef3114` did **not** run an H3r8
migration. The baseline artwork and its existing validation receipt remain
the saved H3r3 edition. The subsequent trials are a separate delivery.

### Controlled H3r5 and H3r8 plate trials — 6 November 2026

The user requested **Atmosphere and Temperature records · 2026, World and
Japan, at both H3r5 and H3r8**: eight new map plates and eight separate
legend/source sheets. Preserve the H3r3 website package as the control.
The [trial settings](../../config/setouchi-h3-trials-20261106.json) pin that
baseline and the October raw-source manifests. The durable entry point is
[build-setouchi-h3-trials.py](../../scripts/build-setouchi-h3-trials.py).

**Completed and validated:** open the
[r3/r5/r8 comparison gallery](../../output/setouchi-h3-trials-20261106/index.html).
Each new map has PDF, SVG, 300 dpi PNG, and WebP exports, with a separate
legend/source sheet. The combined four-page editions alternate map and legend:

- H3r5: [World](../../output/setouchi-h3-trials-20261106/h3r5/world.pdf) ·
  [Japan](../../output/setouchi-h3-trials-20261106/h3r5/japan.pdf).
- H3r8: [World](../../output/setouchi-h3-trials-20261106/h3r8/world.pdf) ·
  [Japan](../../output/setouchi-h3-trials-20261106/h3r8/japan.pdf).

For this experiment, change the cell resolution while keeping the observation
dates, sampled source locations, quality masks, classification, and physical
line weights fixed. Atmosphere retains `maximum_samples_per_axis: 720` from
the baseline; Temperature retains NOAA CPC's 720 × 360 source-center grid.
Both trials reaggregate the raw samples directly into their requested H3
cells. They do not subdivide an existing r3 mean or introduce interpolated
observations. The resulting gaps describe **sample-center support**, not
the complete footprint of the original raster pixels or necessarily a gap
in the original observations. This qualifies these as resolution experiments,
not new higher-detail observational products.

Temperature storage now has an explicit, optional
`aggregation.cell_domain: "source-grid-centers"` mode. It enumerates at most
259,200 source centers, while preserving the daily spatial mean, same-day
historical comparison, valid-day counts, and strict-record rules. Unstored
cells have no sampled center and are unobserved, never analyzed zero. The
default remains the original explicit global domain. The reader checks the
entire declared source-center domain, actual H3 resolutions, sorted unique
IDs, count totals, and missing-data contract. Thus this trial path avoids the
global-allocation problem without changing the record calculation.

| Trial product | Stored cells | Cells with temperature observations |
| --- | ---: | ---: |
| Atmosphere H3r5 | 1,851,097 | — |
| Atmosphere H3r8 | 3,646,239 | — |
| Temperature H3r5 | 235,802 | 62,035 |
| Temperature H3r8 | 257,960 | 62,881 |

Atmosphere counts are the union of cells with a valid value in at least one
layer. Each layer retains its own missingness and valid fraction. Temperature
counts include stored source-center cells with no valid land-temperature
observations; those remain explicitly unobserved. Counts across resolutions
are not an increase in observations and must not be interpreted as warming.

The renderer projects the actual H3 boundaries with the existing AuthaGraph
code. It paints cells using the source SVG's colors, widths, and bin order;
radiation uses the saved 100-level opacity mapping on 0–400 W/m². Data layers
are rasterized at **300 dpi at their placed size**, including Japan's zoom.
Each SVG keeps named, separately replaceable data layers linked to adjacent
PNGs; PDFs embed those layers. Land outlines, solar contours, frames, and text
remain vectors. The atmosphere background stays amber, with white nominal
0.66 pt land outlines above the data. Temperature retains its wine background.

Individual r8 cells can be smaller than a print pixel, and the retained stroke
width can dominate their appearance. The trial deliberately preserves that
weight for comparison. A later visual refinement can scale the strokes, but
would be a separate design variable. The H3r3 control remains an original
vector-derived website export; the finer trials use raster data layers.

The visual review favors **r5 for legibility at the current sheet size**.
Atmosphere reveals more of the original observation swaths; their uncovered
areas were already present in the source product. R8 makes the source-sampling
lattice and gaps more apparent. For Temperature, covered cells increase only
from 62,035 at r5 to 62,881 at r8, while their printed footprints become much
smaller. The warm fills fade at overview scale and the retained blue strokes
become relatively prominent. These changes are consequences of sampling and
mark size, not changes in climate or new measurements.

PDF packaging shares duplicate raster objects used by the cyclic World
composition. It preserves all alpha planes and dimensions, with no
downsampling or JPEG encoding. On single-hue layers it restores the source
RGB after renderer rounding; the maximum premultiplied channel change is
one 8-bit step. Packaging receipts accompany the product provenance. The
largest combined PDF is 96.53 MB, retaining 300 dpi data layers.

Validation is saved in
[validation.json](../../output/setouchi-h3-trials-20261106/validation.json).
All eight pairs passed artifact checksums, product identity, reference-vector
geometry, linked image checks, decoded PDF image dimensions, and updated legend
resolution checks. All twelve comparison images load, with three columns at
1440 px and one column at 390 px, meaningful alternative text, and no horizontal
overflow. The existing Temperature generation test and the new source-domain
test passed; the latter checks r3/r5/r8 domains, rejects invalid domains, and
confirms exact per-cell values and totals when the existing r3 product is
represented in the source-center domain. The saved website preview and
prepared-manifest hashes remain unchanged.

Rebuild from the repository root:

```sh
python3 -m pip install --target build/setouchi-h3-python -r scripts/requirements-setouchi-h3.txt
python3 scripts/build-setouchi-h3-trials.py
make check-setouchi-h3
python3 scripts/validate-setouchi-h3-trials.py --browser
```

Use `--prepare-only`, `--render-only`, or `--package-only` to resume a stage.
Inkscape needs its local D-Bus image decoder when rendering the linked PNGs;
the builder fails on decoder errors, and validation checks the embedded PDF
images independently. The [delivery notes](../../output/setouchi-h3-trials-20261106/README.md)
record dependencies, export formats, and cache locations.

Intermediate GeoJSON products and rendering caches stay in
`build/setouchi-h3-trials-20261106/`. Their hashes, source profiles, sampling
contract, and raw-input manifest hashes are saved with the delivery under
`output/setouchi-h3-trials-20261106/sources/`. Rebuilding verifies the original
JAXA and CPC file hashes; no network refresh or WordPress publication occurs.

## Contact approaches: Hajime Narukawa

Keio's current [faculty profile](https://www.keio.ac.jp/en/faculty/k_100012208/)
lists Hajime Narukawa as Associate Professor in the Faculty of Environment
and Information Studies, with map projection and geometry among his fields.
His [lab](https://narukawa-lab.jp/) connects art, engineering, geometry, and
making. That provides a specific connection to the proposed atlas studio's
folding, drawing, printing, and map-reading activities.

### Routes, in recommended order

1. **A short introduction through the lab's
   [contact form](https://narukawa-lab.jp/contact/).** It accepts a name,
   email address, and message. Lead with the artwork and one modest request:
   a brief exchange about using projection and making in a public workshop.
   The page was reachable on 6 November; form delivery has not been tested.
2. **An introduction from an existing mutual contact**, if Benjamin already
   knows someone connected to Keio, Japanese printmaking, or the Setouchi
   programme. Give that person a paragraph they can forward and the illustrated
   project link. No particular intermediary or relationship has been verified.
3. **AuthaGraph's company contact route** for a project conversation that
   develops into collaboration, technical questions, or agreed credit wording.
   The official [English information page](https://www.authagraph.com/top/lang-en/)
   and [company page](https://www.authagraph.com/category/about/lang-en/) publish
   company contact details. The web reader masks the email and direct retrieval
   returned 403, so a current email address is not asserted here.

For a physical follow-up, the lab publishes **MORI Atelier, Keio University,
5322 Endo, Fujisawa, Kanagawa 252-0882, Japan** on its
[contact page](https://narukawa-lab.jp/contact/). Offer a small printed proof
after establishing contact. The successful wine/amber print makes a useful
material example; confirm where to send it before dispatch.

### What to lead with

Recommend a maker-to-maker introduction: how projections change what visitors
notice, and how a shared table turns maps into drawing, folding, and discussion.
His company's [AuthaGraph Stamp project](https://www.authagraph.com/products/product-authagraph-stamp/lang-en/)
connects a tetrahedral stamp with lithographic mapmaking. This is a particularly
relevant reference for the proposed print workshop; describe the connection
as an interpretation, not evidence that he is interested or available.

Link the revised futures page and, if useful, a compact one-page PDF containing
the World/Japan Water pair and one network or orbital example. Include a small
Hamonshū detail to explain the workshop method. Keep full atlas downloads
available as optional links. A later technical exchange can show the horizontal
map adjustment and editorial Antarctica placement explicitly and invite his
response to those choices.

Ask first for a 15–20 minute conversation or brief written feedback. If he is
interested, discuss a guest conversation, a student exchange, or a jointly
developed workshop, including format, time, credit, and compensation. The
Setouchi activity remains a proposal; the existing records do not establish
festival selection, a confirmed venue, his participation, or endorsement.

### Unsent first-contact draft

**Subject:** Cartofreako × Setouchi — AuthaGraph, print, and a public atlas studio

> Dear Professor Narukawa,
>
> I am Benjamin De Kosnik, an artist and engineer developing Cartofreako, an
> atlas project connecting maps, networks, and printmaking. For a proposed
> public atlas studio at Setouchi 2028, I am pairing World and Japan views of
> water, atmosphere, temperature records, fiber networks, and satellites with
> activities in drawing, folding, and printing.
>
> Your work with AuthaGraph, especially the connection between geometry and
> making in the AuthaGraph Stamp project, is closely related to the questions
> I hope visitors will explore. I would value your perspective on using map
> projection as a tool for a public workshop.
>
> Would you be open to a brief conversation or a short exchange by email?
> The project overview and selected images are here:
> https://benjamin.dekosnik.com/futures/setouchi-2028/
>
> Best wishes,
> Benjamin De Kosnik

Send only when Benjamin requests it. A Japanese subject line and brief
Japanese introduction could accompany the English message if desired. Allow
roughly ten business days before one concise follow-up through the same
route; avoid simultaneous messages to the lab and company. Record any reply
and agreed next step separately from this unsent proposal.
