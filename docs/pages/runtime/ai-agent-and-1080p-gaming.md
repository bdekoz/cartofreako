# AI Workflows assessment and 1080p gaming consumer improvement plan

**Status:** Stage 14 consumer v1 implemented for the complete checked standard
matrix: 205 artifacts, 31 pass IDs, 11 layouts, and 14 approved slices.
Independent collaborator review remains external evidence; GPU formats, masks,
and benchmarking are assigned to the
[Stage 15 ledger](../development/stage-15.md)

**Evidence basis:**
the local delivery report `reports/cartofreako-audit-outcomes-01.md`,
the [forward/reverse API](projection-api.md), the
[WebAssembly runtime](../../../src.wasm/README.md), the current
[generation contract](../getting-started/generation.md), and the
[Stage 15 GPU benchmark ledger](../development/stage-15.md)

## Outcome

Make Cartofreako straightforward for two additional consumers without
weakening its archive and art practice:

1. an AI agent can discover, compare, verify, and cite an artifact through
   machine-readable metadata rather than scraping filenames or inspecting a
   multi-gigabyte archive; and
2. a game or exhibition application can load an exact 1920 × 1080 derivative,
   place it on a flat surface, and use the projection runtime for picking and
   annotation without treating an interrupted map as an equirectangular globe
   texture.

The layered SVG and physical-size PDF are the authoritative archive and art
objects. The existing 44-inch leading-edge plate family and A0 output are
authoritative print presentations. The print family does not force every plate
into a 44 × 30 rectangle: the available leading/long edge targets 44 inches
and the other edge follows the projection's exact aspect ratio. The
3840-pixel PNG remains the full raster. Stage 14's 1080p PNG/lossless-WebP
files are additive access/runtime derivatives with explicit parent IDs. Stage
15 owns any KTX2, GPU texture, Float32, or mask experiment. No derivative
target may become an input to an authoritative archive, art, or print target.

## Assessment disposition

| Assessment recommendation | Current repository state | Work left by this plan |
| --- | --- | --- |
| `RECOMMENDATION-REVERSE` | Complete in runtime API 3 for all six projection families, including face/component candidates and residuals | Screen-to-projection affine transforms and geographic-picking fixtures now cover the standard matrix; independent downstream trials remain useful |
| `RECOMMENDATION-JS` | Core ESM/TypeScript, artifact discovery and deterministic receipts, typed-array batches, abortable workers, Canvas, SVG, D3, and offline Three.js are implemented | Multi-party clean-room use remains external evidence; GPU and engine-specific adapters belong to Stage 15 |
| `RECOMMENDATION-GAMING` | The 205-product 1920 × 1080 PNG/lossless-WebP matrix, affine picking, Canvas, raw flat-plane, and Three.js r185 interaction paths are checked | Benchmark GPU products and any MapLibre, Godot, or Unity adapter separately in Stage 15 |

The existing S3 `release.json` proves aggregate release identity and counts,
but it is not an artifact catalog. It cannot answer a request such as “the
2026 temperature pass in a Pacific layout, at 1080p, with reverse picking.”
The current 480-pixel thumbnails are useful for human contact sheets but too
small for game UI and detailed agent inspection.

## Non-negotiable archive, art, and print contract

Derivative work begins with a frozen master baseline and stops if it changes.
The baseline records:

- every canonical SVG `width`, `height`, `viewBox`, layers, and parent source;
- every PDF `MediaBox`, physical width and height, page count, and orientation;
- the existing 44-inch leading-edge projection frames (`44 × 22`, `44 × 19.052559`,
  `44 × 20.78461`, `44 × 24.75`, `34 × 44`, and `44 × 22.916667`);
- the A0 portrait and landscape placement/imposition contract, including
  margins, bleed, and any color-profile assumptions; and
- the 3840-pixel full PNG and 480-pixel thumbnail contracts.

Repository inspection exposes the six projection-specific frames: each keeps
its exact ratio while placing 44 inches on the appropriate horizontal or
vertical leading edge. A0 imposition is not currently named as a Make target,
so the first implementation task is to locate and document its authoritative
command rather than silently invent a replacement.

`make check-print-contract` is the gate before generating consumer
derivatives. It compares physical dimensions and page geometry, not raster file hashes,
because PDF encoder bytes can vary while the art/print contract remains exact.
A screen-specific label or line-weight adjustment, if later needed, uses an
explicitly named screen style and cannot modify the canonical SVG/PDF style.

## Product tiers

| Tier | Product | Authority and intended use |
| --- | --- | --- |
| Archive/art master | Layered SVG and physical-size PDF | Authoritative editable, preserved, and exhibited object; unchanged |
| Large-format print | Exact-ratio 44-inch-leading-edge plates and A0 | Authoritative physical presentation; unchanged |
| Full raster | Existing longest-side 3840 PNG | High-resolution review and derivative comparison; unchanged |
| Preview | Existing 480-pixel PNG | Contact sheets and rapid browsing; unchanged |
| Screen | Exact 1920 × 1080 contain-fit PNG and lossless WebP | Game UI, exhibits, presentations, and agent visual selection |
| GPU | Stage 15 2048 × 1024 controls and optional KTX2/Basis candidates | Flat planes and GPU upload; benchmarked before adoption and never described as a globe texture |
| Interaction | Projection manifest, affine transform, optional topology/feature masks, runtime API 3 | Picking, tooltips, annotations, and linked views |

The default fit policy is `contain`. No lobe, Antarctic component, title,
legend, or evidence note may be cropped. The catalog records the background,
padding, floating-point content rectangle, and affine transform. `cover` is
allowed only for a separately named, explicitly reviewed slice.

Star-X needs a 1920 × 1080 contain derivative for ordinary game screens and a
later 1080 × 1920 portrait derivative for vertical installations. The
landscape version will have substantial side padding by design; it must not be
stretched to fill the screen.

## Artifact catalog v1

The v1 generator creates `assets.generated/catalog/artifacts-v1.json` against
[`contracts/artifacts-v1.schema.json`](../../../contracts/artifacts-v1.schema.json).
It contains the 205 products named by the checked
[`standard-artifact-manifest-v1.json`](../../../contracts/standard-artifact-manifest-v1.json):
31 standard pass IDs across six projection families, 11 layouts, and 14
approved slices. Optional and exploration-only passes remain excluded unless a
later version explicitly opts them in. Each logical plate has one stable record with
PNG/WebP variants rather than unrelated records per file. Minimum fields are:

- stable artifact ID, title, human-reviewed alt text, subject/pass, lifecycle
  state (`standard`, `optional`, or `exploration-only`), year and source period;
- an explicit authority class (`archive-art-master`, `print-presentation`,
  `full-raster`, `access-derivative`, or `runtime-derivative`) so an agent never
  mistakes a convenient screen file for the preserved artwork;
- projection family, layout, slice, native frame, cut topology, native-cell
  count, component count, and inverse mode;
- source dataset IDs, license/attribution, missing-data semantics, limitations,
  accessibility notes, and any governance or publication restriction;
- for every variant: parent/master ID, derivation recipe/version, URL/path,
  MIME type, byte count, SHA-256, pixel or physical dimensions, transparency,
  color space, and role;
- for screen/GPU variants: fit mode, canvas, content rectangle, padding,
  projected-to-screen matrix, and compatible runtime API/ABI versions;
- links to preview, 1080p PNG/WebP, full PNG, SVG-gzip viewer, PDF, optional
  mask, and recovery package; and
- provenance tying the record to the source commit, generated-assets release,
  and immutable AAO prefix when one exists.

The catalog distinguishes `UNAVAILABLE` from false, zero, and empty. Alt text
starts from a deterministic metadata template and receives human review; an
agent-generated description is never promoted to source evidence merely
because it sounds plausible.

## Agent-facing interface

Add a small ESM/TypeScript library and a headless command-line wrapper over the
same pure query functions:

```js
const catalog = await loadArtifactCatalog(url);
const matches = catalog.query({
  purpose: "flat-map-ui",
  viewport: [1920, 1080],
  subject: "anthropocene-temperature",
  year: 2026,
  projection: ["myriahedral-pacific", "dymaxion"],
  interaction: "inverse-picking"
});
const choice = catalog.select(matches, {prefer: "screen-webp-lossless"});
```

Selection is deterministic and explainable. It returns scored reasons and
rejections, not an opaque model ranking. A companion decision receipt records:

- catalog and artifact IDs plus hashes;
- requested purpose, viewport, projection, slice, year, and layers;
- selected variant and why alternatives were rejected;
- source period, license, limitations, seam policy, and governance fields;
- runtime version and exact projected-to-screen transform; and
- any human override.

The agent workflow is preview-first: query the catalog, inspect the 480 preview
or 1080p WebP, escalate only the selected item to full PNG/SVG/PDF, verify its
checksum, then retain the decision receipt. No agent target performs network
authorization, external-source acceptance, GitHub release, or UCB AAO upload.

## AI Workflows assessment

The [Marshall Islands projection and slice experiment](../development/marshall-islands-speculations-v01.md)
moves one part of this plan from a proposed agent interface to an implemented
workflow canary. A single headless target turns a bounded research question
into five checksummed PNG comparisons using public Cartofreako and Izzi code,
immutable v13 S3 inputs, Natural Earth context, explicit projection/slice
choices, and a portable review prompt. This supports describing Cartofreako as
an **AI-assisted atlas explorer**, with important limits: the implementation
assists search, comparison, rendering, and handoff; it does not make model
output authoritative research evidence or supply community consent,
interpretation, scientific validation, or permission to publish.

| Workflow property | Current evidence | Assessment |
| --- | --- | --- |
| Context portability | YAML front matter carries the report section, evidence boundary, projection hypotheses, public inputs, output hashes, and relevant snapshot-dyad marker IDs | OBSERVED in the experiment document |
| Unattended execution | `make render-marshall-islands-speculations-v01` produced five deterministic PNG-only products at declared dimensions | OBSERVED on the development host; independent reproduction remains UNAVAILABLE |
| Public-input recovery | The renderer can use the public v13 S3 archive when local generated assets are absent and records the exact source boundary | OBSERVED in code and the successful local run; a fresh-host recovery run remains to be witnessed |
| Cross-agent handoff | A compact prompt tells another agent which house-style skill, repositories, evidence subset, checks, and limits to use | IMPLEMENTED contract; successful use by an independent agent or collaborator remains INFERRED |
| Collaborative revision | The package can be given to an invited reviewer, who can reproduce, challenge, and return one labeled variant without this chat history | INFERRED until a collaborator completes and records that loop |
| Governance and legal limits | The document separates observed source facts, inferred proposals, local review, publication authority, and the user's patentability hypothesis | OBSERVED safeguards; patentability, inventorship, ownership, prior art, and disclosure effects are NOT EVALUATED |

The reusable handoff sequence is:

1. extract only the relevant audit context into machine-readable front matter;
2. attach relevance-marker IDs as a context index, never as a transcript,
   consent record, or transfer authorization;
3. resolve public, versioned inputs and execute one deterministic headless
   target;
4. return human-viewable images plus hashes, source periods, limitations, and
   a reproduction command as the decision receipt;
5. let the next collaborator inspect, reproduce, reject, or revise one
   hypothesis; and
6. require human and, where applicable, community review before promotion into
   the research atlas or any publication surface.

This is a stronger agent workflow than passing a prose prompt alone because
the handoff joins intent, executable procedure, immutable evidence references,
outputs, and claim boundaries. It is not yet a demonstrated multi-party
workflow: the next verification gate is a clean-room run by a collaborator or
independent agent, followed by a recorded comparison between the expected and
returned artifact receipt.

To generalize the canary, define a checked `atlas-experiment-v1` schema for the
front matter and add a JSON result receipt containing tool/runtime versions,
resolved input hashes, output hashes, warnings, and review disposition. Keep
the prompt human-readable, but make the schema and receipt the stable
agent-to-agent contract. A later catalog can then discover completed
experiments alongside released plates without treating speculative outputs as
archive or art masters.

## Game-facing interface

Stage 14 implements two progressively richer paths:

1. **Static flat map:** load the exact 1920 × 1080 PNG/WebP into a UI panel or
   flat Three.js plane. This path needs no WASM.
2. **Interactive flat map:** map pointer coordinates through the catalog's
   inverse affine transform, then call runtime API 3 `inverse()`. Preserve all
   ambiguous candidates. A future Stage 15 topology mask may supply a
   native-cell/component qualifier without changing those semantics.

The examples cover Canvas 2D, a dependency-free flat-plane record, and an
offline checked Three.js r185 plane/raycast/reverse-pick path. Later
MapLibre, Unity, or Godot importers, Float32/WebGL adapters, and topology or
feature-ID masks are Stage 15 candidates. They must consume the same catalog
and transform contract rather than create engine-specific projection
semantics. Their product definitions, benchmark, and acceptance rules now live
in the [Stage 15 ledger](../development/stage-15.md).

## Implemented v1 layout and Make surface

Keep the existing projection-first tree:

```text
assets.generated/
├── catalog/artifacts-v1.json
└── <projection>/
    ├── svg/                 # unchanged authoritative master
    ├── pdf/                 # unchanged authoritative master
    ├── png/                 # unchanged 3840 product
    ├── thumbnail/           # unchanged 480 product
    ├── screen-1080p/        # exact 1920 × 1080 PNG
    └── screen-1080p-webp/   # exact lossless WebP
```

The checked v1 targets remain independently invocable even though the promoted
screen products are now part of the standard generated graph:

```text
make generate-screen-1080p
make check-screen-1080p
make consumer-assets-v1
```

`generate-screen-1080p` uses high-quality Lanczos downsampling from the
unchanged 3840-pixel parent PNG, exact 1920 × 1080 contain-fit placement,
WCAG-light-gray `#f4f5f5` padding, and lossless WebP. It verifies pixel
equivalence between decoded PNG and WebP and re-hashes the SVG, PDF, and full
PNG parents after every derivative. `check-screen-1080p` validates all 205
records and their 1,025 declared files, hashes, frames, matrices, padding
rejection, and qualified forward/screen/reverse picks. It also runs a minimal
independent Python reader and the offline Three.js browser canary.
`consumer-assets-v1` adds the broader headless browser consumer checks.

The complete checked standard matrix is part of `make all`. Stage 15
separately owns KTX2, semantic layers, masks, and their
promotion evidence. None of these targets depends on
`release-ucb-aao-s3`.

## Implementation sequence

### 0. Freeze archive/art, print, and runtime baselines

- Inventory current exact-ratio, 44-inch-leading-edge and A0 workflows.
- Implement `check-print-contract` with SVG and PDF physical-size fixtures.
- Record runtime API 3/ABI 1 manifests and representative round-trip fixtures.

Exit gate: a consumer target cannot change any canonical SVG/PDF frame, print
target, 3840 PNG rule, or archived-art identity.

### 1. Render the complete standard 1080p matrix — implemented

The implemented v1 renders all 205 products in the checked standard manifest,
including Coral Reefs, Fiber Synthesized, the five Myriahedral perspectives,
four Cahill–Keyes strips, eight Cahill–Keyes octants, and two Myriahedral face
groups. It uses the existing reviewed 3840-pixel PNG as the declared parent so
the screen product cannot silently select a different SVG renderer or font
environment.

Exit gate: exact 1920 × 1080 output, no crop, readable title/legend, no severe
moire aliasing, correct opacity, and recorded transform for every ratio.

### 2. Build catalog and deterministic agent tools — implemented

- Define and validate catalog, request, and decision-receipt schemas.
- Populate records from generation profiles and release manifests, not from
  filename guesses alone.
- Add ESM/TypeScript query functions and a JSON-only headless CLI.
- Add checksum, broken-link, missing-field, lifecycle, and source-period tests.

Exit gate: an offline agent can select and explain one artifact without opening
an SVG, parsing a filename, or inventing license/source facts.

### 3. Complete 1080p derivatives — implemented

- Generate exact contain-fit PNG and lossless WebP for every released whole-map
  product and approved slice.
- Add the projected-to-screen matrix and content bounds to every record.
- Add gallery links without replacing full PNG, SVG, or PDF links.

Exit gate: all variants resolve from the catalog and round-trip to their
authoritative parent identity and checksum.

### 4. Add interactive game examples — implemented

- Implement pointer-to-projected conversion and candidate-aware picking.
  [`cartofreako-screen.mjs`](../../../src.wasm/cartofreako-screen.mjs) now does
  both and rejects contain-fit padding by default.
- Add Canvas and Three.js examples covering a unique interior, a cut, an
  overlapping Star-X carrier/cap point, and a South Pole candidate set.
- Move large batches to the existing worker and add `AbortSignal` cancellation
  around long consumer operations.

Current evidence: exact 1920 × 1080 Canvas, affine and geographic picks,
flat-plane geometry, worker cancellation, and an offline vendored Three.js
r185 plane/raycast/reverse-pick path pass in headless Chromium. The checked
Star-X fixtures retain carrier/cap component identity, cutoff ambiguity, and
South-Pole behavior. No example maps an interrupted plate onto a sphere as if
it were equirectangular. A collaborator-run usability review and screenshot
baseline remain external evidence, not a Stage 14 implementation dependency.

### Stage 15 handoff — GPU derivatives and benchmark

The 2048 × 1024 texture controls, KTX2/Basis candidates, topology and
feature-ID masks, Float32 positional audit, hardware matrix, benchmark metrics,
and adoption gates have moved to the
[Stage 15 GPU products and benchmark ledger](../development/stage-15.md).
Stage 15 derives its controls from the same authoritative 3840-pixel parents
and compares them against the frozen Stage 14 catalog and 1080p baseline; it
does not reopen Stage 14 print or projection semantics.

## Verification matrix

| Gate | Required evidence |
| --- | --- |
| Archive/art preservation | Canonical SVG structure and physical-size PDF identity remain authoritative; every derivative records its parent and cannot feed a master target |
| Print preservation | SVG dimensions/viewBox and PDF page boxes match all six frozen ratios; the appropriate leading edge retains its 44-inch intent; A0 imposition proofs pass; no screen target is in a print dependency chain |
| Raster integrity | Exact canvas; `contain` bounds inside canvas; alpha/background declared; all lobes, title, legend, and Star-X cap visible |
| WebP integrity | Lossless WebP decodes pixel-equivalent to its 1080p PNG; any later lossy profile gets a separate visual threshold |
| Projection interaction | Affine transform plus forward/reverse round trip is within one screen pixel for interior fixtures; cuts and overlaps remain explicit |
| Catalog completeness | Every released product has variants or an explicit `UNAVAILABLE` reason; paths, hashes, dates, licenses, and lifecycle validate |
| Agent reproducibility | Same request and catalog produce the same ordered choices and receipt; no filename scraping or live web search is required |
| Game behavior | Canvas/Three.js canaries pass at 1920 × 1080; picks cover all six families and Star-X components; interrupted maps are labeled flat-map assets |
| Accessibility | Alt text, title/legend readability, palette notes, and keyboard-accessible example controls receive human review |
| Release boundary | GitHub source publication and human-invoked UCB AAO/S3 preservation remain separate; consumer generation performs neither |

## Promotion rule

The 1080p PNG/WebP products and catalog are promoted to the standard generated
graph after phases 0–4 passed for the checked 205-product standard manifest.
GPU formats and
semantic masks remain Stage 15 exploration-only products until its measured
benefit, tooling, licensing, determinism, and QA gates pass. The authoritative
archive/art and print products remain standard throughout; their preservation
is a prerequisite, not a later cleanup task.
