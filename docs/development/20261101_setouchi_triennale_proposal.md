Resources:
/home/bkoz/src/cartofreako/assets.static/setouchi-triennale/

1. Art CV for Benjamin De Kosnik
20261101-art-cv-2p.pdf

2. Proposed project description
20261101 setouchi proposal.pdf


Plan: do the following steps

ST31: edit setouchi-triennale-2028 st2 japan and world atlas as follows

- first page, add "JAPAN" or "WORLD" in the same size type as CARTOFREAKO, centered on the bottom line, and put the date of the publication/generation in the middle in a font size that is half
- 2 page, remove "ST2 Japan atlas" and use "Japan Atlas" instead
  - atlas sheet size in metric cm,  not inches
  - remvoe map image width and margins info
  - change to "remain recorded in the development document"

- 3 page, change the following titles: "Native geometry" to "Cartography Geometry", "Graticules" to "Cartographic Graticules", "Network CDN/source records" to "Network CDN and Cloud", "Network Groundstations" to "Network Starlink Groundstations"

ST32: generate proposal or proposals based on guidelines in

20261029_setouchi_triennale_explore.md
https://setouchi-artfest.jp/en/proposals

The proposals can be no more than 10 pages in A4 size. Use relevant sections of the Japan and world atlas for visuals.

Output files in:
output/setouchi-triennale-2028-v3

ST33: generate wordpress page for futures/setouchi

## Implemented — 2026-11-01

The user approved ST31–ST33 for unattended implementation and supplied the
final canonical permalink during production:
<https://benjamin.dekosnik.com/futures/setouchi-2028/>. This supersedes the
shorter path above. The existing WordPress page is **3175**; its editor
preview is <https://benjamin.dekosnik.com/?page_id=3175&preview=true>.

Open the local v3 delivery at `output/setouchi-triennale-2028-v3/index.html`.
The [versioned delivery files](https://github.com/bdekoz/cartofreako/tree/main/output/setouchi-triennale-2028-v3)
include the proposal, A4 CV, previews and generation records; full-size atlas
PDFs remain local generated files.

- **ST31 complete:** revised Japan Atlas and World Atlas,
  `setouchi-tri-explore-v3-japan.pdf` and `setouchi-tri-explore-v3-world.pdf`
  in the local v3 output directory,
  each 75 pages. The title and JAPAN/WORLD have identical bold type sizes;
  the centered date between them is half that size. Edition notes use
  **111.76 × 48.39 cm**, omit image-width/margin information, and use
  “remain recorded in the development document.” Both indexes use all four
  requested replacement titles. The 144 map and legend sheets come from
  checksum-verified ST2 PDFs. These front-matter changes also apply to future
  atlas builds through the shared builder and `generation-style.json`.
- **ST32 complete:** one integrated [ten-page A4 application](https://github.com/bdekoz/cartofreako/blob/main/output/setouchi-triennale-2028-v3/cartofreako-x-setouchi-proposal.pdf),
  **Cartofreako × Setouchi — A public atlas studio**, based on the supplied
  1 November project description. It includes both atlas scales, the
  36-subject index, a dimensioned concept drawing, four named workshops and
  an open-studio strand, materials, schedule, a **JPY 2,310,000** estimate,
  selected CV and references. Awashima in autumn is the preferred setting;
  the room and named collaborators are proposed, not booked or confirmed.
  The application includes its reference material within the ten pages.
- **ST33 complete as generated content:** [WordPress draft files](https://github.com/bdekoz/cartofreako/tree/main/output/setouchi-triennale-2028-v3/wordpress),
  Gutenberg block HTML, page metadata, seven-asset media manifest and upload
  instructions for the existing page 3175. The canonical URL and preview
  were unavailable to the web reader and no authenticated WordPress tool
  is connected. The page is generated locally; media upload and inserting
  the blocks into WordPress remain the publication step. The media-rebinding
  command accepts the actual uploaded URLs instead of guessing them.
- **Additional requested CV conversion complete:** the
  [full two-page CV in A4](https://github.com/bdekoz/cartofreako/blob/main/output/setouchi-triennale-2028-v3/20261101-art-cv-2p-a4.pdf)
  preserves every text token and all three embedded fonts. The original
  US Letter PDF is retained. The application uses a concise selected CV;
  the full two-page version is a separate deliverable, not an extra appendix
  to the ten-page application.

### Reproduction and delivery records

```sh
make setouchi-v3 SETOUCHI_V3_DATE=2026-11-01
```

The build reuses the completed ST2 delivery and does not fetch observations.
It uses Python with ReportLab, Pillow, lxml and Beautiful Soup, Poppler,
Ghostscript for the CV conversion, and headless Chrome for local page checks.
Override `SETOUCHI_ST2_OUTPUT` for the source delivery or `SETOUCHI_V3_OUTPUT`
for the destination. The final WordPress URL is saved in the proposal builder.

The output's `sources/` directory preserves the supplied PDFs and text
extractions, the source bibliography, atlas assembly ledger, figure hashes,
budget calculations, CV conversion command, checked call requirements and
validation results. `manifest.json` and `SHA256SUMS` inventory the delivery.

Validation passed for all 150 atlas pages, the ten A4 application pages and
both A4 CV pages. All 144 retained map/legend text layers match the source
pages in sequence; representative World/Japan maps, a legend and a native
swarm map also render pixel-identically. Eleven distinct map previews retain
their source checksums and at least 300 dpi at their placed PDF sizes. The
budget reconciles to JPY 2,310,000. Concept and selected CV each fit within
half an A4 page. All ten application pages, both CV pages and the revised
cover were visually inspected. Desktop (1440 px) and mobile (390 px) checks
passed for the delivery index, application HTML and WordPress preview:
images loaded, local links resolved and there was no horizontal overflow.
The eight existing generation-style tests also passed. Chrome required an
approved sandbox escalation because its `setsockopt` call was blocked in the
restricted environment; no external site was modified during these checks.

The official call and linked guidelines were rechecked on 1 November 2026:
the proposal/reference packet must fit within ten A4 pages. The full atlas
volumes are supplementary downloads rather than application appendices.

The local delivery does not submit an application or make a payment. The
official form's separate contact and payment fields remain outside this
document-generation task. Venue agreement, contributor arrangements,
Japanese text review and physical print proofs remain exhibition production
work, as recorded in the earlier development documents.

## Editorial revisions and status — 2026-11-02

The generated application incorporates the subsequent requested wording:

- Opening: “Cartofreako is a tool to approach the world and learn, design,
  and anticipate possible futures.”
- The next sentence starts “For the 2028 Setouchi Triennale,”.
- The atlas description ends “food, energy and minerals from around the world.”
- Under “One installation, five ways to take part”, the introduction now
  starts “Five events and workshops are proposed, with two detailed in this
  proposal: Hamonshu Revisited;”. The rest of the event list is retained.

Page 10 now contains **eight selected talks**, adding five from the supplied
CV: *War, Weapons, and the Web* (2025), *Digital Expansionism and
Counter-Expansionism as Cyberwarfare* (2024), *UKR-RUS Leak Analysis* (2022),
*Writing Art in Digital Space* (2016), and *The Machine is Learning Aesthetics*
(2016). Full titles and the supplied collaborator credits are retained in
the application. All six **Public Collections** are included: Freehome,
Hong Kong Open Printshop, New Holland Island, Garage Archive Collection,
HDK and Printed Matter, with their supplied locations.

The updated PDF remains ten A4 pages. Its selected CV occupies **362.5 pt**,
under half an A4 page. The full standalone A4 CV preserves both original
pages, all text, three embedded fonts and five distinct hyperlink targets.
The latest page renders, PDF/HTML checks, source and download hashes, browser
receipts and checksums include these revisions. Pages 1–9 retained their
text during the page-10 expansion.

One editorial consistency item remains: the requested page-1 wording says
“two detailed”, while pages 4–7 still contain four workshop sections. No
request to remove or shorten those sections has been made. Reconcile this
wording with the intended selection during any further content revision.

### Short summary

The supplied summary is **312 characters**, including spaces and punctuation
and excluding Markdown formatting:

> Cartofreako × Setouchi proposes a public atlas studio for the 2028 Setouchi Triennale. Japan and world maps connect the Seto Inland Sea to global networks, media, climate, oceans and resources. Five events and workshops invite residents and visitors to discuss, draw, print and imagine possible futures together.

### Application and publication record

The [official call](https://setouchi-artfest.jp/en/proposals), checked again
on **2026-11-02**, now states that applications closed at **10:00 JST on
2 November 2026** (**17:00 PST on 1 November**). No application or payment
was made by this agent, and no user submission receipt is recorded here.
The user's submission outcome remains unrecorded; the deadline is no longer
an upcoming task. No alternative submission route was verified.

WordPress content is prepared for page **3175**, with the canonical permalink
<https://benjamin.dekosnik.com/futures/setouchi-2028/>. A live publication has
not been verified. Its local package includes the asset manifest and a
command to substitute the uploaded media URLs into the Gutenberg blocks.

The [remaining-work list](20261101_setouchi_triennale_explore_3.md) now
distinguishes completed document preparation from submission records,
WordPress publication and exhibition production.

### Dyad status check

The canonical Cartofreako window records were inspected read-only on
**2026-11-02**: **zero open windows**. The latest window,
`SD-EVENT-20261029-5c33b88e`, is `CLOSED`, with closure at
`2026-11-01T17:07:34Z` by end marker `SD-EVENT-20261101-a6236496`.
This agrees with the corrected association in the
[existing receipt](../profile-markers/20261101-sd-receipt.json).
The canonical ledger checksum still matches that receipt's post-correction
checksum. The frozen August ledger's `ACTIVE` relevance metadata is not an
open-window indicator. No marker was opened, closed or recorded by this check.
