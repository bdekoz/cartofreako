# Setouchi 2028 futures: image grids, website publishing, and outreach

Date: 2026-11-06. Status: researched proposal and implementation plan.

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

This document records the plan. The website, its media library, and its theme
have not been changed; the proposed publishing script is not implemented yet.
No outreach has been sent.

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

At a sufficiently wide content width, use three images in the first row and
two wider images in the second. With six selections, use two rows of three.
Reduce to two columns, then one column as the actual theme's content width
requires. Test a minimum useful image width around 320 CSS pixels; three
columns should not be forced into a narrow article column. Use the same
ordering in the DOM, on screen, and in keyboard navigation.

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

The Star-X page is the visual reference. Reuse the site's active theme and
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
transport for this installation still needs to be established. The current
local workflow generates blocks and expects a manual media upload and paste;
replace that publishing step while retaining the existing proposal builder.
See the [previous delivery record](20261101_setouchi_triennale_proposal.md).

Proposed durable entry point: `scripts/update-setouchi-futures.py`, with a
versioned content manifest at `config/setouchi-futures-20261106.json` and
generated assets under `output/setouchi-futures-20261106/`. These paths and
commands are an implementation specification, not existing runnable tools.

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

### Proposed command behavior

```sh
# Planned interface; implement before running.
python3 scripts/update-setouchi-futures.py prepare --manifest config/setouchi-futures-20261106.json
python3 scripts/update-setouchi-futures.py plan --page-id 3175 --transport wp-cli
python3 scripts/update-setouchi-futures.py apply --plan output/setouchi-futures-20261106/publish-plan.json
python3 scripts/update-setouchi-futures.py verify --receipt output/setouchi-futures-20261106/publish-receipt.json
python3 scripts/update-setouchi-futures.py restore --backup /path/to/saved-page.json
```

`prepare` creates responsive images, Gutenberg blocks, and a local preview.
`plan` reads the current page and reports the exact content/media changes
without remote writes. `apply` executes that saved plan; it should not ask for
another web-UI operation. `verify` reads back the result. `restore` is an
explicit recovery command and never deletes uploaded media automatically.

The script should:

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
   document that limitation, or implement an atomic hash check in the
   server-side WP-CLI path if concurrent editing needs stronger protection.
6. Update the managed gallery content while preserving the page's publication
   status, title, permalink, parent, and template. Record the resulting content
   and media receipt. Keep backup/state files outside the public asset set.
7. Read the page back and check that WordPress retained the blocks, captions,
   credits, and links. A successful API response alone is not a visual check.
   Validate the served page when access permits and report any remaining
   frontend access restriction separately.

Prepare approximately 640/1280-pixel responsive derivatives and a larger
detail image, using WebP where fine lines remain clear. Include intrinsic
dimensions and appropriate `srcset`/`sizes`; lazy-load images below the initial
viewport. Full-resolution print files stay behind explicit download links.
Each selected subject keeps a link to its matching legend/source sheet.

## Staging and completion criteria

| Stage | Work | Completion evidence |
| --- | --- | --- |
| F01 — establish current page/style | Obtain the supported read/publish connection, confirm page 3175 and the insertion boundary, inspect Star-X typography. | Saved current page and style measurements; no guessed font settings. |
| F02 — curate and export | Finalize five or six subjects per grid; record the two observer contexts; prepare the three Hamonshū selections, fiber contrast variation, and Japan crops. | Image manifest with source hashes, captions, credits, crop bounds, dates, and verified legend links. |
| F03 — compose | Build the two grids and Hamonshū strip using the site's typography and spacing. | Desktop and phone previews; all subjects visible, captions legible, no clipping or horizontal overflow. |
| F04 — automate | Implement the publisher, manifest reuse, backups, targeted block replacement, and preview mode. | Focused tests for duplicate-free reruns, stale-page detection, missing/duplicate anchors, failed uploads, and recovery. |
| F05 — publish and verify | Apply the prepared page update through the selected supported transport. | Saved before/after receipt; media and legend links resolve; public page matches the reviewed layout. |
| F06 — prepare outreach | Refine the Narukawa message and a small illustrated brief after the page is ready. | Contact route, unsent draft, accurate project status, and two or three selected examples. |

The research and plan are complete; F01–F06 describe subsequent implementation
and outreach preparation. The implementation should leave the three existing
lists followed by both image grids and the Hamonshū strip, then the existing
atlas section. Repeating the update must not duplicate blocks or media.

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
