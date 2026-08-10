# AI-agent and 1080p gaming consumer improvement plan

**Status:** proposed post-Stage-14 implementation plan
**Evidence basis:**
[`cartofreako-audit-outcomes-01`](../reports/cartofreako-audit-outcomes-01.md),
the [forward/reverse API](forward-reverse-projection-api.md), the
[WebAssembly runtime](../src.wasm/README.md), and the current
[generation contract](generation.md)

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
3840-pixel PNG remains the full raster. New 1080p, WebP, KTX2, and mask files
are additive access/runtime derivatives with explicit parent IDs. No
derivative target may become an input to an authoritative archive, art, or
print target.

## Assessment disposition

| Assessment recommendation | Current repository state | Work left by this plan |
| --- | --- | --- |
| `RECOMMENDATION-REVERSE` | Complete in runtime API 3 for all six projection families, including face/component candidates and residuals | Add the screen-to-projection affine transform and game picking fixtures; do not redesign the inverse mathematics |
| `RECOMMENDATION-JS` | Core ESM, TypeScript, immutable capability metadata, typed-array batches, workers, Canvas, SVG, and D3 are implemented | Add artifact discovery, deterministic selection, decision receipts, cancellation for long work, multi-bound Pacific slices, and runnable Three.js/WebGL examples |
| `RECOMMENDATION-GAMING` | A checked 1920 × 1080 Myriahedral example exists, but the release graph has no general 1080p, WebP, power-of-two, mask, or KTX2 products | Build and validate the derivative graph without changing archive/art masters |

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

Add a `check-print-contract` gate before generating consumer derivatives. It
compares physical dimensions and page geometry, not raster file hashes,
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
| GPU | Exact 2048 × 1024 contain-fit PNG; optional KTX2/Basis after benchmarks | Flat planes and GPU upload; never described as a globe texture |
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

Create `assets.generated/catalog/artifacts-v1.json` plus a checked JSON Schema.
Each logical plate has one stable record with format variants rather than one
unrelated record per file. Minimum fields are:

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

## Game-facing interface

Implement three progressively richer paths:

1. **Static flat map:** load the exact 1920 × 1080 PNG/WebP into a UI panel or
   flat Three.js plane. This path needs no WASM.
2. **Interactive flat map:** map pointer coordinates through the catalog's
   inverse affine transform, then call runtime API 3 `inverse()`. Preserve all
   ambiguous candidates; use known native-cell/component masks to qualify a
   result when available.
3. **Dynamic geometry:** use the existing command buffer on a worker and add a
   checked Float32/WebGL adapter. Keep Float64 as the authoritative CPU result
   and measure conversion error before adopting a GPU path.

Initial examples cover Canvas 2D and a Three.js plane. A later MapLibre custom
layer, Unity importer, or Godot importer consumes the same catalog and
transform contract rather than creating engine-specific projection semantics.

Optional masks are additive. A topology mask encodes native cell/component for
qualified picks; a feature-ID mask links visible marks to catalog records; and
transparent semantic-layer rasters allow approved layer composition. Every
mask needs lossless encoding, a value dictionary, a matching transform, and
licensing approval. Anti-aliased display colors are never decoded as IDs.

## Proposed generated layout and Make surface

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
    ├── screen-1080p-webp/   # exact lossless WebP
    ├── texture-2k/          # exact 2048 × 1024 PNG/KTX2
    └── mask/                # optional topology/feature masks
```

Proposed targets remain separate from archive/art/print generation:

```text
make generate-screen-1080p
make generate-game-textures
make generate-agent-catalog
make check-print-contract
make check-consumer-assets
make consumer-assets
```

Do not add KTX2, semantic layers, or masks to `make all` until their tools,
licenses, determinism, and QA are proven. The 1080p PNG/WebP and catalog can be
promoted after the canary phase. None of these targets may depend on
`release-ucb-aao-s3`.

## Implementation sequence

### 0. Freeze archive/art, print, and runtime baselines

- Inventory current exact-ratio, 44-inch-leading-edge and A0 workflows.
- Implement `check-print-contract` with SVG and PDF physical-size fixtures.
- Record runtime API 3/ABI 1 manifests and representative round-trip fixtures.

Exit gate: a consumer target cannot change any canonical SVG/PDF frame, print
target, 3840 PNG rule, or archived-art identity.

### 1. Render a representative 1080p canary

Render water in all six projections, then add dense canaries for Bathymetry
Roulette, Fiber Synthesized or network infrastructure, Anthropocene
Temperature, coral reefs, and Star-X's Antarctic component. Compare direct SVG
rendering with a high-quality 3840-to-1080 downsample.

Exit gate: exact 1920 × 1080 output, no crop, readable title/legend, no severe
moire aliasing, correct opacity, and recorded transform for every ratio.

### 2. Build catalog and deterministic agent tools

- Define and validate catalog/request/decision-receipt schemas.
- Populate records from generation profiles and release manifests, not from
  filename guesses alone.
- Add ESM/TypeScript query functions and a JSON-only headless CLI.
- Add checksum, broken-link, missing-field, lifecycle, and source-period tests.

Exit gate: an offline agent can select and explain one artifact without opening
an SVG, parsing a filename, or inventing license/source facts.

### 3. Complete 1080p derivatives

- Generate exact contain-fit PNG and lossless WebP for every released whole-map
  product and approved slice.
- Add the projected-to-screen matrix and content bounds to every record.
- Add gallery links without replacing full PNG, SVG, or PDF links.

Exit gate: all variants resolve from the catalog and round-trip to their
authoritative parent identity and checksum.

### 4. Add interactive game examples

- Implement pointer-to-projected conversion and candidate-aware picking.
- Add Canvas and Three.js examples covering a unique interior, a cut, an
  overlapping Star-X carrier/cap point, and a South Pole candidate set.
- Move large batches to the existing worker and add `AbortSignal` cancellation
  around long consumer operations.

Exit gate: headless Chromium screenshots and picking fixtures pass at
1920 × 1080; no example maps an interrupted plate onto a sphere as if it were
equirectangular.

### 5. Evaluate GPU derivatives

- Benchmark 2048 × 1024 PNG, WebP, and KTX2/Basis on representative integrated
  and discrete-GPU systems.
- Prototype topology masks before feature-ID masks.
- Set size, decode, upload, and visual-error budgets from measured canaries
  rather than imposing one arbitrary limit on every art style.

Exit gate: adopt KTX2 or Float32 only when it materially improves the measured
game path and stays within declared visual and positional tolerances.

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

Start the catalog and screen derivatives as optional development outputs.
Promote 1080p PNG/WebP plus the catalog to the standard generated graph only
after phases 0–4 pass for every standard pass and projection. Keep KTX2 and
semantic masks optional until phase 5 establishes measured benefit and
licensing. The authoritative archive/art and print products remain standard
throughout; their preservation is a prerequisite, not a later cleanup task.
