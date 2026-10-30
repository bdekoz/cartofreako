
make the following revsions to:
20261029_setouchi_triennale_explore.md

ST2A : legend informatics

Change the legend style to instead use the style in example
cartofreako/assets.static/legend-informatics/resources-mineral-rare-earth-mine-production-2025-authagraph-44-19.legend-rework.svg

Change all plates that use legends to use this style, this revised wording.

ST2B : Make a data plate bibliography that includes the data sources for each of the plates

ST2C: Do a 95% shrink of the cartographic plate, and evaluate if that reduction allows the fiber rings to be drawn around the continent of africa without interruptions. If not, is there another crop or resize or position that would?

Reference the current plates:

network-groundstations-authagraph-44-19.052559.png

/home/bkoz/src/cartofreako/output/setouchi-triennale-2028/plates/world/png/network-fiber-authagraph-44-19.052559.png

## Working scope — 2026-10-30

The preceding documentation update is published, including the
[Setouchi review guide](../pages/gallery/setouchi-2028.md). This second pass
revises the complete 38 world/Japan pairs from the first delivery.

- **ST2A:** use the supplied rare-earth SVG as the legend design reference:
  vertical right-edge title, right-aligned units and period, compact method
  and coverage notes, and a stacked key. Apply it to every existing legend
  in both scopes. Preserve metric meanings, classifications, dates, data
  colors and the approved physical line weights. Simplify wording and
  format numeric labels without changing the underlying class boundaries.
- **ST2B:** assemble a bibliography indexed to every plate, including common
  map geometry, original providers, actual snapshots, derived measures and
  the differences between world and Japan/Setouchi companions.
- **ST2C:** interpret “95% shrink” as a plate scaled to 95% of its current
  dimensions. Compare that framing with the original and alternative
  placement/crops for the fiber and groundstation references. Distinguish
  page-edge clipping from projection seams and source-route discontinuities.

Keep the first delivery and its published review edition available while
building the revision separately. Append measured results, output locations
and any remaining human decisions below as the work completes.

## Framing decision and requested proof — 2026-10-30

The human revised ST2C after the first comparisons: use a maximum image
width of **43.5 inches on the 44-inch sheet**, scale proportionally, and then
make the horizontal move. This supersedes 95% for the requested proof.

The resulting scale is `43.5 / 44 = 0.9886363636` (**98.863636%**).
The centered image is 43.5 × 18.836053 inches on a 44 × 19.052559-inch
sheet: 0.25-inch left/right margins and 0.108253-inch top/bottom margins.
The cyclic move is 10% of image width: +4.4 source inches, or **+4.35 inches
on the sheet**. The revised legends stay in their right-edge positions
within the scaled image; only cartography wraps horizontally.

The proof scales all artwork proportionally, including the fiber stroke
from 0.5 pt to 0.494318 pt; fiber opacity remains 75%. The source route
coordinates are unchanged. The ordinary ST2A plates retain their approved
physical line weights. Review of the shifted proof remains a human
decision before adopting this framing across any other plates.

The requested proof is available locally at
`output/setouchi-triennale-2028-st2/proofs/43p5-cyclic/index.html`, with the
two-page, full-size `setouchi-43p5-shifted-proof.pdf` beside it. Both plates
also have individual SVG, PDF and 300 dpi PNG masters. PDF sheet dimensions,
13,200 × 5,716-pixel raster dimensions and clear white margin bands passed
validation.

All **14 matched boundary pairs** on ACE, WACS and 2Africa now meet inside
the sheet (computed maximum gap below `1.1e-14` inches). Centering at 95%
alone left those pairs 41.8 inches apart. This is a change of the horizontal
AuthaGraph seam, not an invented connection or a repair to source geometry.
Visual inspection confirms the west/south Africa rings are inside the
image. The seam moves through the Americas/Antarctica; the shifted South
America also sits beneath part of the fiber legend. **Human review:**
approve the framing and choose whether to reposition that legend before
promoting this proof to the main atlas. This proof does not silently change
the registration of the other world plates.

## Human proof review and fix plan — 2026-10-30

The human reviewed the 43.5-inch proof and **approved the horizontal move**.
Two changes are requested before the next proof:

1. **Consolidate Antarctica in the lower-left corner.** Remove the orphaned
   portion at the lower right and present Antarctica as one contiguous
   mainland entity at the left. The human explicitly accepts that this is
   geographically displaced. Record the adjustment on the separate legend
   and in SVG provenance; do not describe the adjusted map as an unchanged
   geographic registration. Preserve all network route and landing data.
2. **Separate maps and legends for every plate, global and Japan.** The
   human confirmed this applies to the entire ST2 set, not only the two
   framing proofs. Use paired files such as `network-fiber.svg` and
   `network-fiber-legend.svg`. Cartographic/data sheets must be legend-free;
   the companion legend retains the supplied informatics style, units,
   dates, classifications, source references and interpretation notes.

These decisions supersede the earlier proposed in-map legend relocation.
The horizontal move is accepted; the remaining task is to proof the
Antarctica adjustment and the separate-sheet layout. The map/legend split
applies to all **38 world/Japan pairs: 76 maps and 76 legend sheets**.
The shifted framing and Antarctica consolidation apply to the world fiber
and groundstation plates under review; other map registrations remain as
documented until a broader framing change is requested.

### Implementation and verification plan

- Extract each revised legend to its own SVG and emit a legend-free map.
  Retain 44 × 19.052559-inch sheet coordinates and physical typography so
  the sheets can be composed consistently. Supply compact legend previews
  for review as well as full-size SVG/PDF masters.
- Apply the requested 43.5-inch maximum image width as a centered,
  proportional print inset to all map sheets. This produces the same
  0.25-inch side margins throughout the edition. The horizontal seam move
  remains specific to the two reviewed world network maps. The proportional
  reduction also scales symbols and strokes by 98.863636%; opacity is
  unchanged, and the separate legends record the resulting physical size.
- Update the two shifted world maps to the accepted 43.5-inch image width
  and +4.35-inch printed horizontal move. Reassemble Antarctica at the
  lower left, with no lower-right orphan. Keep the intentional displacement
  explicit in the companion legend and provenance receipt.
- Export the new map/legend pairs, update the bibliography and paired
  review index, and rebuild the aggregate PDF and contact sheets.
- Verify route, landing, monitor, swarm and resource data conservation;
  distinguish the authorized Antarctica geometry/placement change from
  unchanged data geometry. Check margins, the 14 Africa cable joins,
  complete legend coverage, source links and PDF dimensions.
- Visually inspect the consolidated Antarctica, both network proofs,
  representative world/Japan maps and all contact sheets. Append the
  results, exact output paths and any remaining human decisions here.

**Pending human proof:** approve the consolidated Antarctica placement and
the standalone legend layout after the revised files are ready. The prior
physical print, Japanese caption, attribution and exhibition-production
reviews remain recorded in the first development plan.

### Legend bibliography placement — further human review

The human requested two additional revisions to the separate sheets:

- Show **only the plate number** in the footer. Remove “Sources and class
  definitions: plate bibliography” and similar wording.
- Set that number in **36-point bold**, with normal (non-italic) styling.
- Use a **white fill and a black 0.5-point outline at 100% opacity** for
  the plate number. The typography remains 36-point bold. The human
  clarified that this identifies the plate, not its position in the PDF.
- Put the **data bibliography on each corresponding legend sheet**, using
  its available space. The aggregate must pair each map with its legend
  and source bibliography, rather than append an integrated bibliography
  at the end.

Update all 76 legend sheets with the relevant providers, source URLs,
snapshots, units/methods and Japan/world distinctions. Retain the source
ledger and documentation bibliography as audit resources, but omit the
standalone integrated bibliography from the aggregate PDF. Re-export the
legend sheets and verify that each map's sources are present on its paired
page and that the footer contains only its number.

## Completed revision and review handoff — 2026-10-30

ST2A, ST2B and ST2C are implemented, including all subsequent human layout
instructions. The current local edition is
`output/setouchi-triennale-2028-st2/`. Earlier proof notes above remain the
decision history; the following describes the final files.

### Current outputs

| Output within the ST2 delivery | Contents |
| --- | --- |
| `index.html` | Searchable review of 38 subjects, paired world/Japan maps and expandable legend/source sheets. |
| `maps/{world,japan}/{svg,pdf,png,preview}/` | 76 legend-free cartographic/data sheets. |
| `legends/{world,japan}/{svg,pdf,png,preview}/` | 76 separate legends, each with its data bibliography. Files pair as `network-fiber.svg` and `network-fiber-legend.svg`, for example. |
| `setouchi-tri-explore-v2-world.pdf` | 79 pages: CARTOFREAKO/date title, World edition notes and index, then 38 world map/legend-bibliography pairs. |
| `setouchi-tri-explore-v2-japan.pdf` | 79 pages: CARTOFREAKO/date title, Japan edition notes and index, then 38 Japan map/legend-bibliography pairs. |
| `setouchi-tri-explore-v2.pdf` | Combined 155-page edition with the same title, edition notes and index, then world map, world legend/sources, Japan map and Japan legend/sources for each subject. No integrated bibliography is appended. |
| `proofs/43p5-antarctica-left/index.html` | Current fiber/groundstation proof, with a four-sheet `setouchi-network-separated-proof.pdf`. |
| `contact-sheets/` | Eight world/Japan contact sheets and their combined PDF. |
| `plate-source-bibliography.{json,md,html,pdf}` | Supplementary source audit copies, separate from the aggregate. |
| `sources/` | Sheet provenance, export hashes, geometry checks, aggregate manifest and browser-check receipts. |

The supplied rare-earth design now governs the separate legends: vertical
right-edge headings, units and periods, compact method/coverage text and
stacked keys. Each bibliography occupies the left part of the sheet. The
bundled Atkinson Hyperlegible fonts replace an unintended host font
substitution and are embedded in the PDF legends. Classification boundaries,
data colors and observational periods are preserved. The bibliography
documents **49 source records across 38 subjects**, including actual input
dates, provider URLs, derived measures, source limitations and checksum
provenance. Exact class definitions are retained in the ledger.

The footer contains **only the plate number**, 01–38. World and Japan
companions share the subject's ordinal. These are plate identifiers,
independent of positions in the aggregate PDF. The number is **36 pt bold,
normal style, white fill, black 0.5 pt outline, 100% opacity**.

All 76 maps use the centered 43.5 × 18.836053-inch image on the
44 × 19.052559-inch sheet. Margins are 0.25 inches left/right and 0.108253
inches top/bottom. Artwork and strokes scale proportionally by 98.863636%;
opacity stays unchanged. Fiber strokes therefore print at **0.494318 pt
and 75% opacity**. The separate legends retain their physical type sizes.

The two world network proofs use the accepted +4.35-inch printed horizontal
move. Antarctica is translated as one mainland entity into the lower-left
corner, with no lower-right orphan; it is neither rotated nor rescaled
independently. Its deliberate displacement is explicit on the corresponding
legend sheets. All other land geometry and all network data are preserved.
The approved original groundstation SVG's local edits were retained.
The earlier `proofs/43p5-cyclic/` files and `prototypes/africa-framing/`
comparisons remain historical proofs; `plates/` contained intermediate
combined sheets in the initial handoff. The standard-filename correction
below moves those intermediates under `sources/composition/`; `plates/`
now contains the approved separate map and legend files as well.

### Verification and reproduction

- All **152 sheets passed** `scripts/validate-setouchi-sheets.py`, including
  source links, exact plate-number styling, full-size PDF dimensions,
  13,200 × 5,716-pixel PNGs and recorded export hashes.
- The non-legend map data were conserved. For the shifted network maps,
  the route, landing and gateway layers match their source layers; all land
  vertices are retained within the parser's `1e-8`-inch numerical tolerance.
  All **14 matched Africa cable endpoint pairs** meet inside the image,
  with a maximum measured gap below `1.1e-14` inches.
- The PNG exporters verified white margin bands. All eight contact sheets,
  both shifted network maps and representative dense, celestial and resource
  legends were visually inspected. All 76 bibliography panels fit.
- Before the title-page addition below, the aggregate had 154 pages; the current network proof has four
  full-size sheets. Font inspection confirms embedded Atkinson regular,
  bold and italic faces in the representative legend PDF.
- All **854 local HTML asset/download links** resolve. Desktop (1440 px)
  and phone (390 px) browser checks passed for search, geographic scope,
  expanding legends and loading both network proofs, with no horizontal
  overflow or script errors.
- Repository checks passed: Python compilation, `make check-docs` (161
  files and 1,600 local links), pass-status validation, top-of-tree snapshot
  validation and the `make -n setouchi-st2 ASSET_JOBS=4` regeneration plan.

Run `make setouchi-st2 ASSET_JOBS=4` to reproduce the saved presentation from
the pinned first delivery and local source caches. The
[generation guide](../pages/getting-started/generation-styles.md#setouchi-st2-print-layout)
records dependencies, overrides and the map/legend defaults. This is a
presentation revision of recorded observations, not a data refresh.
The [documentation bibliography](../pages/gallery/setouchi-2028-bibliography.md)
and its JSON ledger are linked from the Cartofreako gallery documentation.

### Remaining human review and next steps

1. **Approved:** the human accepted the network proof and confirmed that its
   separate cartography/data and legend/data bibliography sheets apply to
   every world and Japan plate. The standard-filename correction below
   addresses the combined export found during that review.
2. Print representative map and legend sheets at actual size. Check the
   proportional line weights, dense particulate bibliography and outlined
   36 pt plate number, along with the existing 5% swarm overprinting review.
3. Resolve the Japanese captions, attribution, venue and production decisions
   already recorded in the first development plan before exhibition output.
4. After this proof review, publish a new dated web review collection if
   desired. The current situationshipin.space collection remains the first
   edition; the completed ST2 print and review files are local.

No further source acquisition or account access is needed to review this
revision. The first delivery remains available with its original receipts.

## Human approval and standard-filename correction — 2026-10-30

The human approved the network proof's **two-sheet setup** and repeated
that it applies to **all plates**, then identified
`anthropocene-temperature-2025-authagraph-44-19.052559.png` as still combining
cartography and a legend. The file was an older combined ST2 export under
`plates/world/png/`. The separate sheets and aggregate were correct, but
leaving combined exports at the familiar filenames made the delivery
inconsistent. Checking only the new map/legend folders missed that defect.

The corrected delivery preserves the approved arrangement for every subject
and both scopes: **cartography/data sheet, then legend/data bibliography
sheet**. All 608 standard SVG, PDF, PNG and preview filenames now resolve
to the verified 76 maps and 76 separate legend/source sheets. For example:

- `plates/world/png/anthropocene-temperature-2025-authagraph-44-19.052559.png`
  is cartography and data only.
- `plates/world/png/anthropocene-temperature-2025-authagraph-44-19.052559-legend.png`
  is the separate legend and data bibliography.

The Japan filenames use the same pairing with their existing `-japan`
suffix. The review index links to these standard files and leads with the
then-current 154-page proof. Each map remains immediately followed by its
legend/bibliography in the PDF.

Combined build inputs and old exports were preserved under
`sources/composition/`. The composition and intermediate-export scripts
now write there, so regeneration cannot put a combined sheet back under
`plates/`. The Make target publishes and checks the standard filenames after
export. `sources/standard-plate-files.json` records every binding and hash.

The reported temperature map and its legend were inspected as two separate
images. Regenerating the world/Japan temperature pair preserved all 12
standard SVG/PDF/PNG checksums and the approved separation. Final checks
cover every standard filename, its separate-sheet export checksum and the
aggregate's map/legend sequence. The accepted network proof and underlying
map data are retained. The remaining physical print, caption, attribution
and venue reviews above still apply.

The rebuilt review has 855 working local asset/download links and all 76
map/legend pairs in the required PDF order. Desktop and phone browser checks
passed with the corrected standard filenames, including the network sample.
The full sheet validator passed all 152 sheets and all 608 standard filename
bindings, including export checksums and preservation of the map data.

## Title page and separate World/Japan PDFs — 2026-10-30

The human requested an added first page containing only **CARTOFREAKO** and
the date in the largest fitting type, then requested separate World and
Japan PDFs. Each new edition opens with the same white 44 × 19.052559-inch
sheet and two black Atkinson Hyperlegible Bold lines: `CARTOFREAKO` and
`2026-10-30`. Each line fills the 43.5-inch printable width; the resulting
font sizes are approximately **429.69 pt** and **563.21 pt**, respectively.
There is no footer, page number or additional wording on the title sheet.

The World and Japan files each contain **79 pages**: title, edition notes,
scope-specific index, then 38 cartography/data and legend/data bibliography
pairs. Their first subject occupies PDF pages 4–5 and the last occupies
78–79. The combined edition is retained at the existing filename with
**155 pages**, and its index now starts the first subject at pages 4–7.
Plate identifiers remain 01–38. All individual cartography and legend
masters retain their existing content and file bindings.

The review index links directly to both separate PDFs. The generator and
`make setouchi-st2` save this arrangement for future builds; the title date
defaults to the current Los Angeles date. Use `SETOUCHI_ST2_DATE=2026-10-30`
with Make, or `--date 2026-10-30` with
`scripts/build-setouchi-revision-review.py`, to reproduce this date.
The revision manifest records the title typography and exact sheet sequence
for each PDF.

Verification passed for both 79-page editions and the 155-page combined
file: exact title/date text, printable bounds, scope membership, map/legend
order and corrected index references. First, temperature and final legend
pages match the corresponding standalone PDFs. The World and Japan title
pages render identically, and Atkinson Bold is embedded. All 858 local
review links resolve. The individual sheet-export manifest is unchanged.
