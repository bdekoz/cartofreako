# `audit-generated` reviewer worksheet — stage 1 proposal

Status date: 2026-08-19 (America/Los_Angeles).

This proposes a new Devastation Pacific house-style document type,
`audit-generated`, that produces a print-and-annotate PDF worksheet for a
human review of Cartofreako generated imagery. It responds to
[`20260819_reviewer_form.md`](20260819_reviewer_form.md). Nothing here is
implemented yet; no registry, spec, contract, checker, or builder file has
been changed.

## 1. Requirements restated

The PDF MUST contain exactly three ordered sections:

1. **General Notes** — three ruled lines for handwritten comments.
2. **Itemized Release** — for every Cartofreako image in the release: a box
   carrying the image name and three ruled lines for comments.
3. **Itemized Speculative** — for every Cartofreako image produced by
   `make all-experiments` (Marshall Islands speculations, water debris,
   PurpleAir, Equal Earth, Majuro, atoll canary, and siblings): the same
   name-box plus three ruled lines.

The workflow is: generate the worksheet, print it, make handwritten notes,
then transcribe the reviews into an augmented PDF or a webform on
`situationshipin.space` for action.

## 2. Registry proposal

Add one canonical `document_type` value:

- **`audit-generated`** — a print-first reviewer worksheet that itemizes a
  declared generated-image release corpus and a declared speculative-image
  corpus, with fixed comment lines per item and per document, for
  handwriting-first human review and later transcription into a structured
  entry surface.

Registration touches, following the `DP-0039` / `DP-0050` precedent:

- New decision record `decisions/DP-0053-audit-generated-document-type.md`.
- Specification amendment: add `audit-generated` to the version-3.9 registry
  with a short normative section (section 2.7 item plus a dedicated
  subsection); publish as **3.10** with `supersedes: 3.9`.
- `contracts/document-metadata.schema.json`: add the value to the
  `document_type` enum.
- `docs/grammar_document_types.md`: add the row and the reference section.
- `AGENTS.md`: add the item with its required sections and checker.
- `CHANGELOG.md` and `docs/development_next_steps.md` entries.

No alias, default, or migration map is added. The canonical spelling is the
single value `audit-generated`.

## 3. Section architecture

### Cover block

First page states: `document_type: audit-generated`, selected `style`, the
release identity (v14 prefix, source commit, receipt), the speculative
generation identity (host, freeze commit), the observation cutoff, and the
exact item counts for both itemized sections. Evidence statuses
(`OBSERVED` / `UNAVAILABLE`) appear beside each count.

### 3.1 General Notes

One headed section with **exactly three** ruled lines. The lines span the
text measure and are spaced for handwriting (~9–10 mm apart). Nothing else
lives in this section.

### 3.2 Itemized Release

One box per released image. Each box contains:

- the artifact ID (`<pass>.<projection>.<layout>`),
- the released object stem and its v14 product path,
- three ruled comment lines.

**Decided scope (2026-08-19): C — every released image family.** One box per
released object: 217 master `.svg.gz`, 217 print PDF, 217 full PNG,
198 thumbnail PNG, 217 screen-1080p PNG, and 217 screen-1080p WebP — 1,283
boxes total, matching the sealed v14 receipt's product count. Ordering is
deterministic: projection directory order, then pass ID, then family. A
compact cover summary repeats the same counts so omissions are visible.

The earlier scope options are superseded by this decision:

- A — 217 full plates only (superseded);
- B — A plus the 217 screen-1080p pairs (superseded);
- C — every released image family (**selected**).

**Expanded set (2026-08-19):** the Cartofreako worksheet reviews the expanded
image set, not the AAO release alone. Itemized Release keeps all 1,283
released families; Itemized Speculative keeps the 41 speculative images and
gains the GPU-control images as a labeled sub-block (434 items, 2 recipes ×
217), replacing the earlier summary-line treatment. The cover states both the
released and the expanded totals so the two sets never blur.

### 3.3 Itemized Speculative

Same box format for the `make all-experiments` speculative outputs. Default
scope (41 items):

| Family | Items | Source of truth |
| --- | ---: | --- |
| Marshall Islands speculations | 5 PNG plates | `output/marshall-islands-speculations-v01/` |
| Equal Earth positioning | 5 PNG plates | `output/equal-earth-positioning-speculations-v01/` |
| Water debris | 12 plates (6 layouts × 2025/2026) | `fixtures/anthropocene-water-debris/v1/manifest.json`; persisted as `output/anthropocene-water-debris-v01/contact-sheet.png` |
| PurpleAir interface | 12 SVGs (2 years × 6 projections) | `assets.generated/<proj>/svg/anthropocene-particulate-purpleair-*.svg` |
| Majuro full pass | 6 layouts | `fixtures/atoll-evidence/v1/pass-manifest.json` |
| Atoll evidence canary | 1 PNG | `output/atoll-evidence-canary-v01/` |

**Revised (2026-08-19):** per the expanded-image-set request, the 434
GPU-control PNGs (2 recipes × 217) are now itemized in a labeled sub-block
inside Itemized Speculative instead of the earlier summary-line treatment.

### 3.5 Second worksheet — Izzi Generation 20260818

The same three-section architecture also produces a worksheet for the
`izzi-generation-20260818` review set published at
`https://situationshipin.space/review/izzi-generation-20260818/`. Its
**Itemized Release** section holds the 27 member passes of the 2026-08-18
top-of-tree `make-check` generation run (guilloche, moiré, and
surface-tension reference passes), each with its review ID, media path, and
three comment lines. Its **Itemized Speculative** section is
`UNAVAILABLE — no speculative corpus is declared for this set.`

The authoritative item source is the local situationshipin.space repository
(`review/izzi-generation-20260818/` manifest plus the referenced generation
index, members: 27, generation commit
`d16b47f4327fee1371860e0ae885c17c2ed60089`, source repository
`bdekoz/situationshipin.space`). The live page is the published mirror.

### 3.4 Layout mechanics

- Fixed left-aligned grid; boxes are full-measure rectangles with a thin
  rule; the three comment lines are ruled baselines, not borders.
- Atkinson Hyperlegible Next for names; Atkinson Hyperlegible Mono for IDs
  and paths.
- About 14–16 boxes per page with `break-inside: avoid`; a section break
  starts Itemized Speculative on a new page.
- No gradients, shadows, icons, or decorative cards (house-style §2.2).
- Page folios and a compact front-matter index of the three sections.

## 4. Input contract

The worksheet must be reproducible from one frozen input, so handnotes can be
keyed to stable IDs later:

- New checked-in inventory manifest,
  `contracts/audit-generated-inventory-v1.json` (house-style repo), holding
  `general_notes`, `release_items[]`, and `speculative_items[]` with
  `id`, `name`, `release_path_or_UNAVAILABLE`, `kind`, and `status`.
- Cartofreako supplies the item lists: the v14 catalog
  (`fixtures/gpu-benchmark/v1/stage-14-inputs.json` + the v14 receipt) for
  release items and the pass manifests / `output/` inventory for speculative
  items.
- The generated worksheet must reconcile exactly against this manifest; an
  item cannot be added, dropped, or renamed between runs without updating
  the manifest.

## 5. Section contract and checker

- `contracts/audit-generated-sections.json` — canonical section order and
  required fields.
- `scripts/check-audit-generated-report.py` — declares
  `DOCUMENT_TYPE = "audit-generated"` and verifies:
  - the three sections exist in order with the exact headings;
  - General Notes has exactly three ruled lines;
  - every inventory item appears exactly once with the correct name and
    three comment lines;
  - item counts on the cover match the manifest;
  - the PDF has embedded fonts, selectable text, a valid page count, and
    passes the shared accessibility preflight (report "targets WCAG 2.2 AA",
    never claim PDF/UA without the verification).

Follow the `archive-invoice` precedent for the lightweight metadata path and
the `assess-outcomes` precedent for the checker-and-contract path; this type
needs the checker because the item reconciliation is its core correctness
property.

## 6. Builder

New `scripts/build-audit-generated.py` in the house-style repository:

- Inputs: the frozen inventory manifest plus the optional style selection.
- Pipeline: inventory → templated Markdown/HTML → `pandoc` → styled HTML →
  headless Chrome `--headless=new` PDF (the same engine as
  `build-hot-to-trot.py` and `build-manual.py`).
- Emits: the print worksheet PDF, its `.metadata.json`, and a section
  manifest for checker input.
- Keeps generated QA intermediates out of Git; the only admitted artifact is
  a reviewed, source-backed PDF under an explicit user decision.

Two output variants:

- **Print worksheet** — ruled-line boxes only, rendered through the
  pandoc + headless Chrome pipeline.
- **Entry-form variant** — the same layout with fillable PDF form fields
  (three text fields per box plus the General Notes fields) so typed reviews
  can be entered and exported. Built with the ReportLab AcroForm API (pypdf
  is not installed on rizal; ReportLab is), with a disclosed tagging
  caveat: form PDFs receive the structural check but no PDF/UA claim.

**Decided (2026-08-19): ship both variants** for each worksheet.

## 7. Transcription handoff (`situationshipin.space`)

The typed-review surface must reuse the same stable item IDs so worksheet
rows and web rows reconcile one-to-one:

- **Option 1 — augmented PDF entry:** fillable text fields per comment line;
  reviews exported as FDF/JSON keyed by item ID. Lowest new infrastructure;
  weaker accessibility guarantees for form PDFs.
- **Option 2 — webform:** a page on `situationshipin.space` that imports the
  same inventory manifest, renders General Notes and the two itemized
  sections, and stores one response per item ID. Best accessibility and
  review UX; requires work in that separate repository.
- **Option 3 — both:** worksheet for paper, webform for transcription,
  sharing the manifest. Recommended long-term; Option 2 is the first web
  step.

This proposal does not authorize publication, transfer, or any change to
`situationshipin.space`; that remains a separate bounded task in that
repository.

## 8. Implementation options

- **Option A — house-style type only.** Register `audit-generated`, add the
  contract/checker/builder/template, and let Cartofreako pass the frozen
  inventory in. No webform work.
- **Option B — A plus Cartofreako inventory pinning.** Freeze a checked
  Cartofreako inventory file for v14 release items and the current
  speculative set, so the worksheet is reproducible from committed inputs.
- **Option C — B plus the `situationshipin.space` webform** (Option 3 above).
- **Option D — all previous, plus both worksheets.** A + B + C, and generate
  two worksheets from one builder: the Cartofreako v14 release worksheet and
  the `izzi-generation-20260818` worksheet (27 member passes from the
  situationshipin.space review index). Transcription for the Izzi set reuses
  the existing per-review-page decision/note form on situationshipin.space
  keyed by the same review IDs, instead of building a new form.

Recommended sequence: Option D. Deliver both printed worksheets from the
frozen inventories, then wire transcription to the existing
situationshipin.space review form.

**Approved (2026-08-19): Option D** — implement the full type, freeze both
inventories, generate both worksheets (Cartofreako v14 and
`izzi-generation-20260818`), each in print and fillable-entry variants, and
leave the situationshipin.space transcription surface as the existing
per-review-page form.

## 9. Verification plan

- `scripts/check-audit-generated-report.py` passes on a generated sample.
- Render and inspect every page of the sample PDF before delivery
  (AGENTS.md rule 8).
- `pdffonts` / `pdftotext` checks: embedded/subset fonts and selectable text.
- Contrast check on ruled lines and labels against the paper background; use
  `house-style` or a validated `randoma11y-accent` pairing.
- Reconciliation test: delete or rename one inventory item and confirm the
  checker fails; add a duplicate and confirm it fails.
- Page-count sanity with the decided scope: 1,283 release boxes ≈ 81 pages,
  41 speculative boxes ≈ 3 pages, 434 GPU-control boxes ≈ 27 pages, plus
  cover, index, and General Notes.

## 10. Open questions

Resolved (2026-08-19):

1. **Option D approved** (was: approve Option B, then Option C).
2. **Release scope C — all families** (1,283 boxes).
3. **GPU controls: summary line only** (revised 2026-08-19 to itemized
   under the expanded-image-set request).
4. **Ship both variants** — print worksheet plus fillable-PDF entry form.
5. **`situationshipin.space` owns the transcription surface**, and the
   frozen inventory manifest is the shared contract.
6. **Izzi set confirmed: exactly the 27 generation index members; no
   speculative corpus.** Its `Itemized Speculative` section stays
   `UNAVAILABLE`.

Resolved additions (2026-08-19):

- **Cartofreako worksheet:** use the expanded image set — released families
  (1,283) plus the 41 speculative images plus the 434 GPU-control images —
  rather than the release set alone.

## 11. Option D proposal

With the inputs above, Option D is implemented as follows.

### 11.1 Frozen inventories

- `cartofreako-v14` — release items generated from
  `fixtures/gpu-benchmark/v1/stage-14-inputs.json` plus the v14 receipt:
  1,283 items (one per released object), each with `id`, `family`,
  `projection`, `stem`, and the released `products/...` path. Speculative
  items: the 41-item set of §3.3 plus the 434 GPU-control images as the
  labeled sub-block (expanded image set).
- `izzi-generation-20260818` — release items are the 27 generation index
  members read from
  `situationshipin.space/review/media/izzi-generation-20260818/izzi-generation-20260818.index.html`
  (27 member links verified locally); speculative items are `UNAVAILABLE`
  (confirmed: no speculative corpus).

### 11.2 Builder

One house-style builder, `scripts/build-audit-generated.py`, consumes a
frozen inventory JSON plus a style choice and emits per worksheet:

1. `*-print.pdf` — pandoc → headless Chrome, ruled boxes, no form fields;
2. `*-entry.pdf` — ReportLab AcroForm build of the same layout with three
   text fields per box and three General Notes fields;
3. `*.metadata.json` and the section manifest for the checker.

The checker `scripts/check-audit-generated-report.py` verifies both variants
against the inventory (section order, exactly three notes lines, one box per
item exactly once, counts on the cover, fonts/selectable text on the print
variant, and field presence on the entry variant).

### 11.3 Outputs and verification

Private deliverables under the host's private-assets convention (never
committed): four PDFs — Cartofreako v14 print and entry, Izzi print and
entry — plus the two frozen inventories. Verify with the checker,
`pdfinfo`/`pdffonts`/`pdftotext`, a full rendered-page pass, and the
reconciliation failure tests. Expected sizes: the Cartofreako print
worksheet ≈ 112 pages (1,283 release + 41 speculative + 434 GPU-control
boxes); the Izzi worksheet ≈ 4 pages (27 members).

### 11.4 Sequence

1. Freeze the two inventories.
2. Register the `audit-generated` type (DP-0053, spec 3.10, schema, grammar,
   AGENTS.md).
3. Implement builder, checker, and contracts.
4. Generate and verify the four PDFs.
5. Hand the print PDFs to the reviewer; the existing situationshipin.space
   review form remains the transcription target.

## 12. Implementation status — 2026-08-19

Sequence 11.4 is complete:

- Frozen inventories are checked in at
  `fixtures/audit-generated/cartofreako-v14-expanded.json` and
  `fixtures/audit-generated/izzi-generation-20260818.json`.
- The type is registered in the house-style repository (DP-0053, spec 3.10,
  metadata-schema enum, grammar, AGENTS.md, CHANGELOG) and pushed.
- Builder `scripts/build-audit-generated.py`, checker
  `scripts/check-audit-generated-report.py`, section contract, and inventory
  schema are shipped.
- Human review converged on one consolidated printable-and-fillable PDF per
  worksheet. The Cartofreako worksheet itemizes every PNG in each projection's
  `assets.generated/<projection>/png/` directory (224 files) plus the 12
  `output/` speculation PNGs — 236 boxes, 27 pages, fixed three-line
  title/path header, no GPU/SVG/PDF/WebP/thumbnail items. The Izzi worksheet
  holds the 27 generation members, 6 pages. Both pass
  `check-audit-generated-report.py`, and the reviewer marked each pass.
- Transcription remains the existing situationshipin.space review form.
