# Setouchi Triennale 2028 — remaining work

Status updated **2026-11-02**. This is the active task list following
[ST2](20261030_setouchi_triennale_explore_2.md). The
[first development plan](20261029_setouchi_triennale_explore.md) retains the
proposal, exhibition options and initial source research.

## Completed baseline

All requested atlas generation and styling work is complete. The reviewed
2026-10-31 generation includes the shared world framing, Antarctica at the
lower left, separate map and legend/data bibliography sheets, and fill-only
swarm location names in both resolutions for World and Japan.

The map-generation defaults were saved in
[`generation-style.json`](../../generation-style.json) at `b44c962`;
the reference generation is `098e9f1`. Rebuild with
`make atlas ASSET_JOBS=4`. See the
[generation guide](../pages/getting-started/generation-styles.md#setouchi-st2-print-layout)
for source requirements and overrides.

The source atlas delivery is `output/setouchi-triennale-2028-st2/`:
75-page World and Japan PDFs, a 147-page combined PDF, and 76 map/legend
pairs in the review archive. Bathymetry Roulette and Hamonshu remain in the
archive and are excluded from the PDFs. Validation and reproduction results
are recorded in ST2.

The [ST31–ST33 proposal pass](20261101_setouchi_triennale_proposal.md) is
complete in `output/setouchi-triennale-2028-v3/`: revised 75-page World and
Japan volumes, one ten-page A4 application, the complete two-page CV
converted to A4, and a WordPress draft for page 3175. The shared atlas builder
saves the new covers, centimetre notes and requested index titles. Rebuild
the application delivery with `make setouchi-v3 SETOUCHI_V3_DATE=2026-11-01`.

## 1. Application package and submission record

The [official call](https://setouchi-artfest.jp/en/proposals), rechecked on
**2026-11-02**, states that applications **closed on 2 November at 10:00 JST**,
equivalent to **1 November at 17:00 America/Los_Angeles (PST)**. No submission
or payment was made by this agent. A user submission, if any, is not recorded
in the repository; the date is no longer an upcoming deadline.

- [x] Develop the supplied 1 November project description into one integrated
  proposal, **Cartofreako × Setouchi — A public atlas studio**, with a planning
  budget of **JPY 2,310,000**. The earlier nine catalogs remain exploration
  alternatives rather than the current application packet.
- [x] Include the supplied CV and atlas visuals in a ten-page A4 packet;
  expand page 10 to eight selected talks and all six Public Collections.
  Preserve a separate complete two-page A4 CV.
- [x] Apply the requested opening and workshop-introduction wording; record
  the 312-character summary in the proposal development document.
- [ ] Record any actual payment/submission receipts, exact submitted files
  and outcome. Do not infer a user submission from document preparation.
- [ ] Reconcile the requested page-1 phrase “two detailed” with the four
  workshop sections still present on pages 4–7 before any further use.
- [ ] If no application was submitted, record that outcome and verify any
  future route before treating it as available; none has been verified here.

## 2. Physical proofs and exhibition production

- [ ] Print representative World and Japan maps and their legend sheets at
  actual size. Check the 43.5-inch image area, proportional strokes, shifted
  world framing, Antarctic inset and Water's retained subsea geography.
- [ ] Include both swarm resolution bands in both scopes. Review fill-only
  location-name legibility and the 5% circle overprinting. Also check the
  outlined 36 pt plate numbers and dense particulate bibliography.
- [ ] Proof the approved temperature bins, opaque resource palettes, coral
  honeycombs and outline-only atmosphere land layer on the intended paper.
- [ ] Translate and review Japanese captions. Confirm source definitions,
  observation periods, attribution and source-owner reuse terms for exhibition.
- [ ] Confirm the venue, room measurements, access, local collaborators,
  credits and permissions. Check accessible routes, mounting, glare and label
  size; obtain site-specific structural/wind review if installation I2 is chosen.
- [ ] Obtain printing, fabrication, packing, freight, travel and installation
  quotations. Reconcile the budget, approve the final print list, and prepare
  spares, a care guide and removal/return arrangements.
- [ ] Schedule a selected-source refresh 6–8 weeks before opening, including
  dated infrastructure inventories. Record observation dates independently
  of render dates and approve the resulting production edition.

Completion evidence: annotated print-proof decisions, reviewed captions and
credits, confirmed venue arrangements, approved budget and production files.

## 3. Publish the latest ST2 web review

The existing publication record covers the
[first-edition review collection](https://situationshipin.space/review/cartofreako-setouchi-2028-20261030/).
The latest ST2 review and print PDFs are local.

- [ ] Prepare a new dated situationshipin.space review collection from the
  current ST2 delivery, retaining the first edition as a reference.
- [ ] Publish both World and Japan scopes, both swarm resolution bands,
  separate map/legend previews and links to the current World and Japan PDFs.
  Mark the two bathymetry studies as excluded from the PDF selection.
- [ ] Check desktop/mobile search, scope filtering, expanded legends,
  download links and agreement between online previews and the local masters.
- [ ] Update the Cartofreako review guide and record the public URL, source
  revision, publication receipt and verification results here.

Completion evidence: a dated public collection serving the current ST2
generation, with working map/legend and PDF links.

### WordPress proposal page

- [x] Prepare Gutenberg content, four map images, three download references,
  metadata and a local preview for existing page **3175**, with canonical URL
  <https://benjamin.dekosnik.com/futures/setouchi-2028/>.
- [ ] Upload the seven listed media/download assets and substitute their
  actual HTTPS URLs using the provided media-map command.
- [ ] Insert the blocks into the existing page, verify the site's preview
  and record publication. Live WordPress publication remains unverified.

## 4. Further particulate enrichment

The implemented plate already includes Japanese government measurements,
Chinese CNEMC observations via Quotsoft, selected Indian monitors and a
separately identified AirGradient sensor. Continue from the
[source documentation](../pages/data/anthropocene-particulate.md) and
[enrichment findings](20261029_particulate_data_enrichement_explore.md).

- [ ] Backfill earlier Japanese 2025 months from finalized NIES releases;
  reconcile provisional and final observations and retain the missing/error
  code exclusions.
- [ ] Review the historical Chinese station-coordinate crosswalk and obtain
  authoritative station updates where available.
- [ ] Expand the selected Indian sample and build an Asia-28 provider,
  station and year inventory. Track coverage and deduplicate official/OpenAQ
  observations; the public OpenAQ archive is accessible without an API key.
- [ ] Review negative, extreme and repeated concentrations and aggregation
  conventions with an appropriate air-monitoring reader or station operator.
- [ ] If a PurpleAir pilot is selected, obtain an authorized key and agreed
  points budget, inventory outdoor sensors, and evaluate coverage and
  calibration before purchasing broader history. Keep sensor measurements
  distinct from government monitors.
- [ ] Resolve applicable station-owner reuse terms before exhibition;
  obtain EANET republication permission if those data are selected.
- [ ] Update the source documentation, manifests and coverage summaries for
  any implemented enrichment, then regenerate and verify the affected plates.

Completion evidence: source and coordinate provenance, measured coverage
improvements, documented quality decisions and validated updated plate exports.

## Work order and decision record

Record the application outcome now that the call has closed. WordPress and
web-review publication, physical proofs and production arrangements remain
separate from the completed document generation. Schedule further particulate
enrichment as a separate source update using the saved atlas defaults.

Append decisions, completed checkboxes, output locations and verification
results here as work proceeds. This document records the remaining work;
creating it does not mark any of these tasks complete.

The dyad status was checked read-only on 2026-11-02: no Cartofreako window is
open. The October 29 window was closed on November 1, as recorded in the
[corrected receipt](../profile-markers/20261101-sd-receipt.json). This status
check did not create or end a marker.
