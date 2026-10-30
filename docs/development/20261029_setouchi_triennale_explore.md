Step 1:
Render up-to-date plates for the Authagraph projection from current cartofreako sources, current izzi sources, and current data. Ouput full print size svg, png, and pdf resources. Also include a per-country detail of Japan for all plates.

Previous reference:
https://bdekoz.github.io/cartofreako/docs/pages/gallery/authagraph.html

Step 2:
Write a proposal and exhibition stratagies for the Setouchi Triennale. Provide 1-5 options each for exhibition, events, and site installations. Make a show catalog in pdf for each using the simplest visual design style and clearest, most succistinct verbal and written language style.

Reference information on the Stouchi Triennale:
/home/bkoz/src/cartofreako/assets.static/setouchi-triennale

This is the canonical web site:
https://setouchi-artfest.jp/en/proposals

Reference conference ideas:
20261021 cartofreako freakout.pdf

Put all output in
output/setouchi-triennale-2028

## Updated working plan — 2026-10-29

The target is Setouchi Triennale **2028**. Keep all generated material in
`output/setouchi-triennale-2028`.

1. Recompile the generators against the current cartofreako and sibling izzi
   sources. Render the 32 reference-gallery plates and both bathymetry plates
   as 44 × 19.052559 inch SVG/PDF masters and 300 dpi PNGs. Make a Japan
   companion for every plate; use explicit Setouchi observer/context sheets
   for celestial products, for which a geographic crop is undefined.
2. Refresh available primary data and preserve its actual observation dates,
   units, missing values, source files, and checksums. The broken UNdata
   refinery export has a verified alternative in the official UNSD SDMX API.
3. Integrate the user-supplied OPEC 2026 report from `assets.static/petroleum/opec`.
   Include all countries and regional series supplied in the World Oil Outlook
   2026 workbooks. Keep projections distinct from historical observations. Add
   independent sources for Russia, Brazil, Canada, Venezuela, Mexico, the USA,
   and Japan. Store each source under `assets.static/petroleum/<source>/`. Keep throughput, capacity, crude production, and product
   output distinct. Do not merge conflicting years or units silently.
4. Produce three options each for exhibitions, events, and site installations,
   with a simple PDF show catalog for each. Develop a recommended proposal,
   concept layouts, estimated budgets, production schedule, and a concise
   application draft grounded in the supplied site report and conference ideas.
5. Validate file counts, print dimensions, image dimensions, country coverage,
   source attribution, and representative rendered pages. Append the final
   inventory, human-gated reviews, and concrete next steps below.

Official call checked 2026-10-29:
https://setouchi-artfest.jp/en/proposals
The current application deadline is **2026-11-02 10:00 JST**. Proposals and
reference materials must fit within ten A4 pages per plan; the call permits
at most three plans per applicant/group. The exploration catalogs are separate
from the eventual submission. No application, payment, or outreach is included
in this unattended production task.

Working context: the user requested the snapshot-dyad starting context to be
the message “what is the missing upstream URL, look to see if it has been
changed and find update”. The local marker was recorded on 2026-10-29; it was
not backdated. Marker ID: `SD-EVENT-20261029-5c33b88e`.

## Produced outputs — 2026-10-29

Open the [public world/Japan gallery](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/).
The local visual index is `output/setouchi-triennale-2028/index.html`; all
generated deliverables are in `output/setouchi-triennale-2028`.

- **38 world plates and 38 Japan companions**, each in SVG, PDF and PNG:
  **228 print files**. The set includes the 32 reference-gallery plates, both
  bathymetry plates, three petroleum additions, and separate high/low-resolution
  swarm plates.
- Full sheet size: **44 × 19.052559 inches**. PDF page size is
  3,168 × 1,371.784248 points; PNGs are 13,200 × 5,716 pixels at 300 dpi.
- **Nine four-page show catalogs**: three exhibitions (E1–E3), three events
  (V1–V3), and three site installations (I1–I3). Each includes a visitor
  experience, candidate place, concept layout, materials, planning budget,
  schedule, source references and human review decisions.
- An [eight-page application draft](https://github.com/bdekoz/cartofreako/blob/385650cfd88f8596134b787cc87bcee59b171389/output/setouchi-triennale-2028/proposal/shared-sea-atlas_application-draft.pdf),
  [proposal and options](https://github.com/bdekoz/cartofreako/blob/385650cfd88f8596134b787cc87bcee59b171389/output/setouchi-triennale-2028/proposal/proposal-and-options.md),
  ten-page atlas contact sheets, and a four-page petroleum source annex.
- An offline petroleum source explorer (`sources/petroleum-explorer.html`),
  source tables, observation-period notes, build scripts, validation results
  and checksums.

The recommended exhibition is **E1 Shared Sea Atlas**, to develop with an
Awashima host for autumn 2028. Its planning allowance is **JPY 2,050,000**,
including the stated travel/access allowances and contingency; this is not a
quote or an award. V1 is the simplest event and I1 the simplest independent
installation. No venue, speaker, partner or funding commitment is assumed.

### Petroleum integration and upstream repair

The original OPEC directory was moved intact to
`assets.static/petroleum/opec`. Other assets are nested by source under
`assets.static/petroleum`: EIA, ANP Brazil, Statistics Canada, UNSD, and source
checks for Austria's WKO and the Energy Institute.

The supplied report is **World Oil Outlook 2026**, not the Annual Statistical
Bulletin. The import retains all **14 workbooks, 202 worksheets and 17,920
nonempty cells**. Its register includes **209 named countries and territories**;
**17** have separately indexed numeric country cells. Countries covered only
by regional definitions or report text remain in the register. Regional totals
are never assigned to each country.

The new petroleum plates are:

1. EIA 2025 petroleum and other liquids production: **36 countries**, including
   Russia, Brazil, Canada, Venezuela, Mexico and the USA. Bahrain is a point
   because the 1:110m country geometry lacks its polygon.
2. OPEC 2030 total-liquids projection: **14 individually supported countries**,
   with component cells retained. Future values are explicitly projections.
3. OPEC report country coverage: distinguishes indexed country figures from
   countries without a separate numeric value.

Independent national series add Brazilian crude/condensate production and
refinery feed, Canadian crude/equivalent production and refinery inputs, and
US crude refinery input. Canada’s 2025 monthly crude and equivalent totals
reconcile to 310,930,332 m³. EIA is the integrated independent source for
Russia, Venezuela and Mexico; no newer government dataset from those countries
was ingested. Production, throughput, capacity, outages, mass and volume remain
separate measures. Japan remains in the UNSD refinery layer.

The missing upstream URL was the UNdata `DownloadHandler.ashx` refinery export.
It returns HTTP 404; no moved handler was confirmed. The working official
alternative is:

https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A..GR.086/?startPeriod=2018&format=csv

The repository fetcher now uses that endpoint plus the official energy
structure. `scripts/normalize-undata-refinery.py` validates annual GR/086
throughput, units and duplicates before producing the preparer's CSV. Its
689 observations exactly match the prepared extract. Japan 2024 remains
120,404.978 thousand metric tonnes. The Energy Institute and WKO report
retrieval failures are recorded; no unsupported observations were added.

### Source freshness and reproducibility

Temperature observations now run through **28 October 2026**. JAXA atmosphere
sources and selected astronomy/orbital catalogs were refreshed on 29 October.
The World Bank resource release is 8 October; food/forest labels were updated
to reflect the newer observation years. WRI's reef source is an unchanged
2011 baseline. Celestial/solar calculations use a fixed 29 October 2026
20:00 UTC reference instant, separate from observation dates.

Some particulate and infrastructure sources retain older labelled snapshots.
A global fire-detection refresh needs a NASA FIRMS key, which was unavailable;
this does not provide surface PM2.5. The Japanese government PM2.5 route is now
verified in the separate enrichment findings.
NASA SSC validation-reference refresh timed out; the 16 successfully retrieved
CelesTrak groups were retained. See
[source periods and limits](https://github.com/bdekoz/cartofreako/blob/385650cfd88f8596134b787cc87bcee59b171389/output/setouchi-triennale-2028/sources/data-quality.md).
The outputs should be described as a dated study edition rather than as a live
atlas. Current code/izzi revisions, input hashes and commands are recorded in
`sources/repository-state.json`, `sources/generation-plan.json` and `build/`.

The earlier Fuller file rename is complete as
`20260929_buckminister_fuller_swarm_integration.md`; its contents are unchanged.

## Human-gated reviews and next steps

1. **Choose the submission scope.** Review the nine catalogs and select no more
   than three plans. E1 is the recommended exhibition. Keep the exploration
   catalogs separate from the application packet.
2. **Finish applicant material.** Confirm name/contact details, write or supply
   the verified CV and select prior-work images. The application draft is eight
   A4 pages, leaving at most two pages for these additions under the ten-page
   limit. No biography or partner commitment was fabricated.
3. **Recheck the call, then pay and submit if proceeding.** The official page
   checked 29 October states an extended deadline of **2 November 2026,
   10:00 JST** (**1 November, 17:00 America/Los_Angeles**). Confirm the final
   requirements and JPY 1,500 fee per plan before payment. Application, payment,
   correspondence and submission remain human actions.
4. **Agree the place and collaboration.** Confirm an available room with the
   festival/host, pay local collaborators for their work, and agree credit and
   use of local texts or visitor contributions. Obtain actual venue permissions
   and schedule access before committing fabrication or travel.
5. **Review the physical design.** Measure the room, check accessible routes,
   seated reading, mounting, glare and label size. Make physical print proofs.
   I2 requires site-specific structural/wind review before fabrication.
6. **Review language, data and attribution.** Translate and review Japanese
   captions; confirm source definitions, observation periods and excerpt/reuse
   terms. Refresh the selected data 6–8 weeks before opening. FIRMS can refresh
   fire detections; surface PM2.5 needs monitoring-station or explicitly labelled
   model data. Refresh dated infrastructure inventories before describing them
   as current in 2028.
7. **Confirm costs and make the final production edition.** Obtain printing,
   fabrication, packing, freight, travel and installation quotations; reconcile
   taxes and site requirements within the selected budget. Approve the final
   print list, produce spares and a care guide, and agree removal/return plans.

8. **Review new visual encodings on a print proof.** Confirm the shared
   temperature day-count bins, fully opaque izzi-hue resource colours and
   honeycomb reef selection, now approved by the user. The Voronoi and circle alternatives remain in
   the prototype gallery. Do not interpret symbol area as reef area. Include
   both AuthaGraph swarm resolution plates and transparent-land atmosphere
   plates in the same physical legibility and overprinting proof.
9. **Review and extend the implemented particulate coverage.** Japan MOE,
   China CNEMC via Quotsoft, selected Indian CPCB/AirNow monitors, and a separate
   AirGradient sensor are ingested. Review the historical Chinese station
   coordinate crosswalk, backfill earlier Japanese 2025 months from finalized
   NIES releases, and expand the selected Indian urban sample to an exhaustive
   location inventory. Check source-owner reuse terms before public exhibition.
   OpenAQ's public archive needs no key; API access can help inventory expansion.
   PurpleAir remains a bounded outdoor-sensor/calibration pilot requiring an
   authorized key and agreed point budget. EANET republication is a separate gate.
   Review the flagged extreme/repeated concentrations with station operators
   before using them in a public comparison; completeness checks do not certify
   instrument accuracy. Japanese numeric `999x` missing/error codes are excluded.

No application, payment, outreach, commit, push or public publication was made.

### Validation completed

All **76 plate triplets** passed SVG/PDF size, one-page PDF, PNG pixel size,
300 dpi metadata, parse/integrity and export-freshness checks. All nine catalogs
are four A4 pages; the application draft is eight A4 pages. All **17,920 OPEC
cells** were compared directly with the source workbooks. The 14-country OPEC
projection sums and six requested EIA country series were checked against
source cells/tables. The UNSD normalizer rejects wrong units, duplicates,
unknown status and nonfinite values, including with Python optimization enabled.

Representative map, Japan-detail, legend, catalog and proposal pages were
visually inspected. The output index was opened at desktop and phone widths;
petroleum dataset selection and country search passed in headless Chrome.
All local index links resolve. This is a digital review; physical print proofs
and the human decisions above remain required before exhibition production.

Machine results: `output/setouchi-triennale-2028/sources/validation.json`.
Visual/browser scope: `sources/visual-review.json` and
`sources/browser-validation.json`. Final inventory and integrity hashes:
`manifest.json` and `SHA256SUMS` at the output root.

### Aggregate exploration PDF — 2026-10-29

The requested local `output/setouchi-triennale-2028/setouchi-tri-explore-v1.pdf`
collects the visual index, all 38 world/Japan pairs, nine catalogs, application
draft, contact sheets, petroleum annex, source-period notes and the human
reviews above. The map artwork remains vector-based for zooming. This study
volume is separate from the eventual ten-page application packet. The aggregate
and full-resolution plate masters remain local generated files. The index,
previews and build scripts were subsequently committed; see
[versioned review materials](https://github.com/bdekoz/cartofreako/blob/385650cfd88f8596134b787cc87bcee59b171389/output/setouchi-triennale-2028/GIT-CONTENTS.md).

Rebuild with `build/build_aggregate.py` in the output directory using ReportLab,
Beautiful Soup, Markdown, pdfrw and pypdf. Assembly provenance and PDF checks
are recorded in `sources/aggregate-pdf.json` and
`sources/aggregate-pdf-validation.json`.

### Fiber styling revision — 2026-10-29

At the user’s request, the global and Japan-detail fiber route lines now use
**0.5 pt effective width and 75% opacity** at full sheet size. Japan route
strokes compensate for the 4.422099× enlargement. A later detail revision halves Japan landing-symbol diameters and sets their
outlines to 0.5 pt; global landing symbols retain their existing styling. SVG, PDF, 300 dpi PNG, previews, affected catalog images,
contact sheets and the aggregate PDF were regenerated. Route-level checks are
in `sources/fiber-style.json`.

### Inland river styling revision — 2026-10-29

At the user’s request, inland river lines on the water plates now use
**0.75 pt globally and 1.5 pt in the Japan detail**, at full sheet size,
with **85% opacity**. Japan strokes compensate for the native-projection
enlargement. The SVG, PDF, 300 dpi PNG, preview, catalog, application, contact
sheet and aggregate PDF outputs were refreshed. Measurements from the SVGs
and exported PDF graphics are recorded in `sources/water-river-style.json`.


### Visual and source refinement pass — 2026-10-29

- **CDN:** replaced the August snapshot from `cloud_cdn_cache` with the latest
  local `cloud_cdn_cache.bkoz` manifest, **21 October 2026**, pinned to commit
  `2234be5c9bce123d26639e79935e54dd8f8785a8`. All 42 canonical layers and
  **28,243 typed records** are accounted for: 13,140 source points, 1,405
  derived reference positions and 13,698 unplotted records. Alpha60's latest
  r8 vendor-reel strategy supplies named vendor colours, radial honeycombs at
  33% fill, opaque outlines, approximate-reference triangles, separate
  locality claims and collision-filtered labels. Native AuthaGraph geometry
  is retained for the atlas; the Japan legend is separately typeset.
- **Swarm:** uses Alpha60's native cumulative-cache renderer with
  `/home/bkoz/src/alpha60-samples-cache/dan-da-dan-210.cache/cache.20260304.tar.xz`.
  All 383 cumulative documents cover **4 September 2025–4 March 2026**.
  **1080p/4K and 720p/SD each have their own full-size AuthaGraph plate and
  Japan detail**, replacing the earlier combined Cahill–Keyes sheet. The
  Alpha60 projection template supplies the same AuthaGraph geometry as the
  atlas. Native member colours, weighted circles and **5% opacity** remain;
  the world plates retain **2,804,935 and 876,541 circles**, respectively.
  Japan's enlarged geographic viewport keeps the world plate's physical
  circle-area scale and includes neighbouring countries. It is not a
  Japan-only total. librsvg/Cairo exports every circle as vector artwork,
  preserving paint order and embedding fonts. The adapter, build scripts,
  source hashes and partition receipts are retained in the output directory.
- **Japan details:** all geographic coastlines are **1 pt**, including the
  AuthaGraph swarm details. Fiber landing diameters are halved; outlines are
  **0.5 pt**. Route lines remain **0.5 pt / 75%**. Rivers remain at the
  requested **0.75 pt global / 1.5 pt Japan / 85%**.
- **Temperature:** shared, non-overlapping bins are **1–5, 6–10, 11–20,
  21–40, 41–80 and 81+ record days**. Red is reserved for counts above 40.
  Both fields contain 11,945 covered cells; 339 in 2025 and 526 in the partial
  2026 field exceed 40. Those unequal observation windows are not presented
  as a full-year change estimate. Counts and source digests are in
  `sources/temperature-classification.json`.
- **Resources:** all data colours are fully opaque, including forest, rare
  earths, fisheries, food and human indicators. Fourteen metrics use **70
  distinct named izzi-hue colours**, with no exact RGB reused between metrics.
  Petroleum comparisons share a brown family; solar uses six yellow/orange
  classes, explicitly keyed in MW. Japan's solar value is **92,211 MW**.
  Installed capacity is not generation; future companions should compare
  annual additions, capacity per person and measured generation.
- **Coral:** three global/Japan prototypes compare bounded Voronoi cells,
  radial honeycombs and composition circles. The atlas uses honeycombs, which
  retain the class mix across **7,215 original cells in 844 display groups**.
  Every membership and threat count is preserved in the comparison ledger.
  Filled display footprints do not measure reef extent or current condition.
- **Particulate research:** findings are saved in
  [20261029_particulate_data_enrichement_explore.md](20261029_particulate_data_enrichement_explore.md).
  Japanese NIES finalized data and Sora-mame provisional data are the preferred
  first integration. A Kagawa September 2026 request returned 12 stations
  with numeric PM2.5 readings. PurpleAir is a conditional supplement, with
  no claim of superior Japan coverage without an inventory and calibration.

Within the local delivery, review `sources/resource-color-key.html` and
`prototypes/coral-reef/index.html`, plus the
[visual annex](https://github.com/bdekoz/cartofreako/blob/385650cfd88f8596134b787cc87bcee59b171389/output/setouchi-triennale-2028/proposal/visual-revisions-and-coral-prototypes.pdf).
The revised index, catalogs and aggregate retain the source periods and
human reviews above. No submission, publication or commit is part of this pass.

### Japan Water coastline correction — 2026-10-29

The separate Natural Earth coastline layer in **Japan / Water** now uses
**1 pt effective strokes**, matching the Japan outline in **Rare-earth mine
production**. Its former 0.025 inch source stroke became about 7.96 pt under
the 4.422099× Japan enlargement. The correction covers every coastline in the
Japan viewport, including neighbouring countries and islands. Coastline
opacity remains 90%; the shared Japan outline is 1 pt at 80% opacity, and
Japan rivers remain 1.5 pt at 85% opacity.

The Japan Water SVG/PDF/PNG, preview, affected catalogs, application, contact
sheets and aggregate PDF are refreshed. Physical PDF measurements are recorded
in `sources/water-coastline-style.json`. The existing print-proof review applies.

### Particulate implementation, ITU routes and atmosphere revision — 2026-10-29

Both years of the world and Japan particulate plates now include measured
PM2.5, with observed-day rings and separate >35 µg/m³ day counts. A station-day
requires at least 18 valid hours; multiple stations in one cell count once per
local date. Existing EPA AQI, smoke, fire and weather values are preserved.

| Source | 2025 reporting sites / period | 2026 reporting sites / period |
| --- | --- | --- |
| Japan MOE / Soramame | 1,076 / November–December | 1,095 / January–September |
| China CNEMC via Quotsoft | 1,686 / January–December, with missing dates | 1,345 / January–28 October, with missing dates |
| Selected Indian CPCB / AirNow monitors | 16 / available records within January–December | 16 / available records through 26 October |
| AirGradient community sensor, India | 1 / available records September–December | 1 / available records through 2 October |

All 47 Japanese prefectures were requested. China's station coordinates use a
disclosed 2022 inventory; the Indian set is 14 cities, not a national census.
Japan's earlier 2025 months remain unavailable in this ingestion. Commercial
sensor measurements are kept separate. PurpleAir requires an authorized key
and point budget; IQAir's free AQI product does not provide the annual mass
concentration history required here. OpenAQ's public AWS archive required no key.

The [particulate source page](../pages/data/anthropocene-particulate.md) gives
units, providers, APIs, date ranges, quality rules, licences and commercial
alternatives. It is linked from the documentation index, source-data index and
Anthropocene implementation notes. The earlier research note now records this
implementation. Raw responses, station joins and normalized station-days are
retained under `assets.static/anthropocene/asia-pm25/`; preparation and validation
receipts are in the delivery's `sources/` tree. Two Japanese `9999` missing-value
codes were removed before averaging. Unusually high provider-reported values
remain separately flagged for review, not silently clipped.

The fiber plates now include **37,397 ITU public terrestrial fibre features**
in **Kelly green (#4CBB17), 0.5 pt and 75% opacity** at both scales. The source
contains 35,212 operational, 639 under-construction, 1,248 planned and 298
proposed features; status dashes remain visible. There are 202 features
intersecting Japan's land polygons. ITU route geometry is schematic, not a
surveyed right-of-way. The acquisition script and provenance receipt preserve
the anonymous WFS query and digest; microwave/restricted layers are excluded.

The atmosphere plates place land outlines above the observations with fill opacity **0**.
Cloud fractions use pink classes; aerosol optical depth uses rose outlines;
rainfall stays blue; shortwave radiation uses gold outlines. Separating fills
and outlines removes the earlier gray blend. Japan was on the nighttime side
of the retained cloud snapshot, so no positive daytime cloud retrieval is
invented for Japan. Atmospheric observations remain visible across land and sea.

The approved coral honeycomb visualization is retained. Native generator checks,
independent PM2.5 raw-day recalculations, unique cell-day totals, legacy-value
conservation, physical fiber strokes and updated export dimensions/freshness
are recorded in the delivery validation files. The index, catalogs, contact
sheets, visual annex and aggregate PDF include the revised plates.


### Swarm projection and separate resolution plates — 2026-10-29

The requested swarm revision uses **AuthaGraph throughout**. The 1080p/4K
partition and the 720p/lower-resolution partition now occupy separate atlas
pages, each paired with its Japan detail. Both use the requested Dan Da Dan
cache and Alpha60's native weighted-circle visualization. The atlas therefore
contains **38 world/Japan pairs**. The former combined Cahill–Keyes outputs
are retained only in `superseded/swarm-cahill-keyes/`, outside the delivery
inventory. Provenance is in `sources/swarm-refresh.json` and the two
`network-swarm-*.json` receipts.

The atmosphere revision keeps land above the observations with **fill opacity
0**; the separate coastline layer supplies the visible outline. There are no
land fills hiding the atmospheric fields. Updated SVG, PDF, 300 dpi PNG,
previews, catalogs, contact sheets and the aggregate PDF carry both revisions.

**Human review and next steps:** review the two swarm bands independently in
the index and aggregate, then include these plates in the existing physical
print proof for label legibility and 5% circle overprinting. Keep the cache
period and the distinction between observations and unique people in the
exhibition captions. The earlier venue, attribution and production reviews
remain in force; no additional account or data acquisition is needed for this
revision.


### Generation styles saved as repository defaults — 2026-10-30

The approved physical strokes, resource colors, temperature classes,
outline-only foreground land, coral honeycombs, CDN vendor reel and separate
native Alpha60 swarm bands now drive ordinary Cartofreako regeneration.
[`generation-style.json`](../../generation-style.json) is the shared style
source; [Default generation styles](../pages/getting-started/generation-styles.md)
documents the build wiring, source pins, Japan details, exports and checks.
The development projection is AuthaGraph. Builders no longer depend on this
edition's output directory.

Fresh normal Make targets reproduced all 844 coral groups and their 7,215
memberships, 28,243 CDN records and both native swarm circle counts. The Japan
high-band crop retained 144,555 visible circles. The standard artifact manifest
includes both resolution bands. The approved delivery and its checksum
receipts remain frozen; these defaults govern subsequent regenerations.

**Human review and next steps:** no additional review is required to save or
reuse the defaults. The existing venue, attribution and physical print-proof
reviews above remain the next production steps. Source refreshes retain their
own dates and provenance; applying the defaults does not imply new observations.


### World and Japan web review — 2026-10-30

The [review guide](../pages/gallery/setouchi-2028.md) is linked from the project
homepage, repository README, documentation index and visual gallery. It gives
reviewers the current collection, visual changes and feedback instructions.
The frozen delivery tree is excluded from the documentation site because its
print-download links require local generated files. The documentation link
check validates public pages separately and rejects links into that local-only
tree; retained source records are linked to their versioned GitHub files.

The [Setouchi review gallery](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/)
pairs all **38 world plates and 38 Japan detail plates** from the latest
complete delivery. It is also listed in the site's
[Proofs catalog](https://situationshipin.space/proofs.html). Search and scope
controls support paired, world-only and Japan-only viewing. Each plate opens
a zoomable image and an individual review form; the collection can download
all saved decisions and notes as one JSON file. Notes stay in the reviewer's
browser until downloaded or submitted through the existing review workflow.

Review images are **3,840 × 1,663 lossless WebP**, downsampled from the verified
13,200 × 5,716 PNG masters. These are screen review copies; the existing
300 dpi masters and aggregate PDF remain the print deliverables. The published
[source inventory](https://situationshipin.space/review/media/cartofreako-setouchi-2028-20261030/plates.json)
records every master and review-image SHA-256, source caption and dimensions.
It identifies Cartofreako commit
`385650cfd88f8596134b787cc87bcee59b171389` and delivery-manifest SHA-256
`89ec09e943a2425ae488a5e04ff43898f7be2ac741e9153fc007d531118f05b9`.
The frozen delivery itself was not modified for publication.

The site implementation is commit
`e3d0e5b03d5e776dc65e07b300052c3578749e08` in
`bdekoz/situationshipin.space`. Its preparation and publication scripts retain
the hash checks and regenerate the gallery from a complete delivery. Existing
review entries are preserved. The new screen review package adds about
60 MiB; the site's total review payload is about 251 MiB within its updated
256 MiB cap.

The [Pages deployment](https://github.com/bdekoz/situationshipin.space/actions/runs/41106927988)
completed successfully. Live verification fetched **308 files**, including all
76 full images, 76 thumbnails and 76 individual review pages with their
manifests: every response was HTTP 200 and matched its prepared SHA-256.
Desktop (1,440 px) and phone (390 px) browser checks passed for image loading,
search, scope filters, note persistence, combined feedback download and the
Proofs catalog link, with no horizontal overflow or script errors. Saved
feedback with stale image hashes is excluded from the current collection.

**Human review and next steps:** review the world and Japan companions in the
gallery, save per-plate decisions and download the combined notes for the next
revision. In particular, review both swarm resolution bands separately and
check the enriched particulate coverage and thin ITU routes at both scales.
Public availability does not approve an individual plate. The existing venue,
attribution and physical print-proof reviews remain the production gates.


### ST2 separate map and legend/source edition — 2026-10-30

The [second development pass](20261030_setouchi_triennale_explore_2.md)
is implemented in `output/setouchi-triennale-2028-st2/`. It contains 76
legend-free maps and 76 separate legend sheets, each carrying its data
bibliography. Separate World and Japan PDFs each have 75 pages, including
the requested **CARTOFREAKO / 2026-10-30** title page, edition notes and plate
index and 36 map/legend pairs. Bathymetry Roulette and Bathymetry Hamonshu
are excluded from the PDFs. The combined 147-page `setouchi-tri-explore-v2.pdf` places each legend
immediately after its map and has no appended bibliography. The
[source bibliography](../pages/gallery/setouchi-2028-bibliography.md) also
provides a searchable documentation copy and checksum ledger.

All maps have a centered 43.5-inch image on the 44-inch sheet. The world
fiber and groundstation maps use the accepted horizontal move and the
requested consolidated lower-left Antarctica. Plate numbers identify
subjects 01–38, shared across world/Japan companions, in 36 pt bold with
white fill and a fully opaque black 0.5 pt outline. Regeneration is saved
as `make setouchi-st2`; the [generation guide](../pages/getting-started/generation-styles.md#setouchi-st2-print-layout)
records dependencies and output locations.

**Human review and next steps:** proof the consolidated Antarctica and the
separate legend/source layout in the new local edition, including the
outlined plate numbers at actual print size. The ST2 document records all
checks and the remaining production decisions. The existing web gallery
continues to show the first edition.
