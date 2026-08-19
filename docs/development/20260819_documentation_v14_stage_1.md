# Cartofreako v14 documentation update — stage-1 proposal and options

Status date: 2026-08-19 (America/Los_Angeles).

This is a proposal only. No documentation file was changed, nothing was
committed or pushed, and no remote object was touched while this document was
written. It is the stage-1 deliverable requested in
[`20260819_documentation_v14_explore.md`](20260819_documentation_v14_explore.md).

## 1. What v14 actually is (verified evidence)

The generated-assets v14 deposit on UCB Active Archive Object Storage (AAO)
exists and is complete. Facts used throughout this proposal:

| Fact | Value | Evidence |
| --- | --- | --- |
| Immutable prefix | `cartofreako/v14` in `adekosnik-bucket01` at `https://s3-ewh.ist.berkeley.edu` | [`docs/releases/v14-aao-upload-profile.json`](../releases/v14-aao-upload-profile.json) |
| Completion marker | `https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/release.json` | [`reports/cartofreako-v14-aao-upload-receipt.json`](../../reports/cartofreako-v14-aao-upload-receipt.json) |
| Upload status | `complete`, 2026-08-16T17:21:50Z, full-download verification passed | same receipt |
| Object inventory | 1,349 objects, 1,618,300,704 stored bytes | same receipt |
| Archive invoice | [`reports/archive-invoice-cartofreako-v14-2026-08-17.pdf`](../../reports/archive-invoice-cartofreako-v14-2026-08-17.pdf), 3 pages, embedded fonts, QA renders | [`...provenance.json`](../../reports/archive-invoice-cartofreako-v14-2026-08-17.provenance.json) |
| Source identity | commit `a51f1d8`, source tag `UNAVAILABLE`, generated 2026-08-16T09:35:46Z | staged tree `build/s3-release-v14/README.md` on eureka |
| Staged tree | `build/s3-release-v14/` on eureka (indexes, products, runtime, viewer, manifest, marker) | eureka inspection 2026-08-19 |
| Live reachability | HTTP 200 for `release.json` from eureka on 2026-08-19; endpoint times out from rizal (route/VPN) | eureka curl check |

The staged tree carries the exact published layout:
`products/<lifecycle>/<projection>/{master,print,full,thumbnail,screen-1080p/{png,webp}}`
plus `indexes/`, `runtime/api-3/`, `viewer.html`, `README.md`, `SHA256SUMS`,
and `release.json`. Counts: 217 master SVG gzip, 217 print PDF, 217 full PNG,
217 screen PNG, 217 screen WebP, 198 thumbnails, 45 indexes, 17 runtime files.
The current corpus is entirely `standard`; the `optional` and `exploration`
partitions are declared but empty in the uploaded tree.

The release is frozen at the Stage 15A input freeze `c3263c1` (217 artifacts,
33 pass IDs, 11 projection IDs, 14 approved slices). Eureka is the
machine-bound release host; its raster baselines are the ones frozen and
published.

## 2. Corpus delta v13 → v14 (what the docs must newly represent)

Compared with the sealed v13 tree (`build/s3-release-v13`, 211 artifacts / 32
passes), v14 changed the standard corpus as follows:

| Change | Passes / artifacts | Effect on documentation |
| --- | --- | --- |
| Added `network-groundstations` | 6 whole-map products, one per projection | New plates must appear in every projection contact sheet and in the pass page |
| Added `anthropocene-particulate-2025` and `anthropocene-particulate-2026` | 6 + 6 products | Dual-year particulate family must appear in gallery data; currently absent |
| Removed `cloud-atmosphere` from the standard corpus | −6 products | `docs/pages/passes/cloud-atmosphere.md` gallery include must not point at v14 objects that do not exist; keep v13 links plus a status note |
| Removed legacy `anthropocene` observation atlas | −6 products | `_data/generated_passes.yml` stem must be dropped; the "retained legacy atlas" sentence in the gallery include is now false for v14 |
| Renamed `fiber-synthesized` → `network-fiber` | 6 products, new stems | Gallery stems and pass-page include parameter must change |
| Renamed `network-infrastructure-sites` → `network-cdn` | 6 products, new stems | Same |
| Added `screen-1080p` PNG and WebP for every product | 217 + 217 objects | New consumer-facing family to document and link |

Net: 217 artifacts across 33 passes. Every whole-map projection contact sheet
is now 33 passes, not the "32 passes" wording currently in the docs.

Path translation for every retargeted URL:

| Role | v13 path | v14 path |
| --- | --- | --- |
| Preview / thumbnail | `tree/<proj>/thumbnail/<stem>.png` | `products/standard/<proj>/thumbnail/<stem>.png` |
| Full PNG (plate) | `tree/<proj>/png/<stem>.png` | `products/standard/<proj>/full/<stem>.png` |
| Print PDF | `tree/<proj>/pdf/<stem>.pdf` | `products/standard/<proj>/print/<stem>.pdf` |
| Layered SVG | `tree/<proj>/svg/<stem>.svg.gz` via `viewer.html?asset=<proj>/svg/<stem>.svg.gz` | `products/standard/<proj>/master/<stem>.svg.gz` (see viewer defect in §6) |
| Screen 1080p | absent | `products/standard/<proj>/screen-1080p/{png,webp}/<stem>.{png,webp}` |
| Indexes | absent | `indexes/artifacts-v1.json`, `indexes/by-pass/`, `indexes/by-projection/` |
| Runtime | absent | `runtime/api-3/` with `runtime-manifest.json` |

Thumbnails exist only for the six whole-map projections (33 each = 198). The
five Myriahedral slice directories have no thumbnail family; do not generate
thumbnail links for them.

## 3. File-by-file documentation plan

### 3.1 New release record

Create `docs/pages/releases/aao-v14.md`, modeled on `aao-v13.md`:

- Deposit identity table (endpoint, bucket, prefix, marker URL).
- Receipt and invoice references, uploader run ID, completion timestamp.
- The v14 object layout and the count table above.
- The §2 corpus delta, including removals and renames.
- Verification evidence: `standard` + `full_download` checks; eureka 200 check.
- Immutability policy: never repair or replace bytes under `cartofreako/v14/`;
  a correction requires a new prefix (for example `v14.1` or `v15`).
- Known defects in §6, stated plainly rather than silently repaired.
- A consumer quick-reference (artifact ID → URL) pointing at
  `indexes/artifacts-v1.json`.

### 3.2 Retarget every v13 link that should now point at v14

| File | Changes |
| --- | --- |
| `index.md` | Update the "v13 public S3 release" narrative (§ "Generated artifact previews") to v14; retarget the thumbnail preview table rows (geometry, graticules, earth, water, bathymetry-roulette, and any others) to `products/standard/...` paths; update the two `assets.generated/` and "Releases" link rows that cite `aao-v13.md` as the current mirror |
| `docs/pages/README.md` | "Inspect the immutable generated release" row: `aao-v13.md` → `aao-v14.md`, marker link → `cartofreako/v14/release.json`; "Inspect v13 paths..." row gains the v14 sibling; projection table "32-pass contact sheet" → "33-pass" |
| `docs/pages/releases/README.md` | Header link list gains `v14 S3 publication (aao-v14.md)`; rewrite the "current browser-facing mirror is v13" paragraph to v14; keep v13 procedure text as historical runbook; update the v14 invocation example to match the completed run |
| `docs/pages/gallery/README.md` | `release_base` → `/cartofreako/v14`; retarget the subject cards; "Stage 13 catalog contains 32 released whole-map passes" → v14 wording with 33 passes; include reference → `v14-projection-gallery.md` |
| `_includes/v13-projection-gallery.md` | Retarget to v14 paths; rename to `_includes/v14-projection-gallery.md` and update the include site |
| `_includes/v13-pass-gallery.md` | Retarget to v14 paths (thumbnail/full/print/master); rename to `_includes/v14-pass-gallery.md` |
| `_includes/generated-snapshot.md` | `release_base`, `projection_tree`, `viewer_base`, and `preview_base` move to v14 products layout; header links "Stage 13 convergence notes"/"S3 v13 publication" become v14 equivalents; rewrite the narrative (33 passes, no legacy atlas, JAXA cloud no longer standard) |
| `docs/pages/gallery/{authagraph,cahill-keyes,dymaxion,myriahedral,star-x,voronoi}.md` | Front-matter `preview_path: tree/<proj>/thumbnail` → `products/standard/<proj>/thumbnail` |
| `_data/generated_passes.yml` | Stems: `network-infrastructure-sites` → `network-cdn`; `fiber-synthesized` → `network-fiber`; add `network-groundstations`, `anthropocene-particulate-2025`, `anthropocene-particulate-2026`; remove `anthropocene` legacy and `cloud-atmosphere` |
| `docs/pages/passes/astronomy.md` | Retarget the 18 v13 PNG table links to `products/standard/<proj>/full/...` |
| `docs/pages/passes/bathymetry/roulette.md` | Retarget the 6 v13 PNG links |
| `docs/pages/passes/network-fiber.md` | Include parameter `stem="fiber-synthesized"` → `stem="network-fiber"`; include filename update |
| `docs/pages/passes/cloud-atmosphere.md` | The pass left the standard v14 corpus. Keep the v13 gallery (historical), add a status note, and stop implying v14 inclusion |
| `docs/pages/passes/network-groundstations.md` | Add a v14 product table (six projections × full PNG / print PDF / master SVG / screen-1080p), mirroring `astronomy.md` |
| `docs/pages/runtime/ai-agent-and-1080p-gaming.md` | Update the "public-input recovery" v13 reference to v14; link the published `screen-1080p` family and `runtime/api-3/` |
| `docs/pages/releases/v13-to-v14-consumer-layout.md` | Either fold the cutover table into the new `aao-v14.md` and mark this file superseded, or rewrite it to record the now-published layout (`published: false` and "proposed-v14" wording are stale) |
| `docs/pages/navigation.json` | Bump `updated`; no new section is required, but verify the releases entry renders the new page |

Historical pages stay historical: `s3-v12.md`, `aao-v13.md`, `stage-13.md`,
and the v20260806–v20260813 notes must continue to identify their immutable
objects. Do not rewrite their v12/v13 URLs.

### 3.3 Verification after the edits

`make check-docs` validates repository-local links only
(`scripts/check-doc-links.py` explicitly works without network access), so it
cannot prove the new S3 URLs resolve. Add an external check run from eureka
(which reaches the endpoint):

```sh
ssh eureka "bash -lc 'curl -sS -o /dev/null -w \"%{http_code} %{url_effective}\n\" <url>'" \
  # repeated for every newly introduced cartofreako/v14 URL
```

Accept only 200s. rizal cannot run this check today (endpoint timeout), so
the external verification belongs to eureka or to a Berkeley-VPN session.

## 4. New-plates representation checklist

Complete when all of the following are true:

- [ ] All six `network-groundstations` plates appear in every projection
      contact sheet and in the pass page.
- [ ] Both `anthropocene-particulate-2025` and `anthropocene-particulate-2026`
      appear in the gallery data and the Anthropocene pass documentation.
- [ ] `network-fiber` and `network-cdn` stems replace the retired stems
      everywhere in gallery data and pass pages.
- [ ] The removed `cloud-atmosphere` and legacy `anthropocene` plates are no
      longer presented as current-release products, and their removal is
      recorded in the release notes.
- [ ] The new `screen-1080p` PNG/WebP family is linked and explained once
      (recommended home: `runtime/ai-agent-and-1080p-gaming.md` plus the
      v14 release record).
- [ ] No v14 thumbnail URL is generated for a Myriahedral slice directory.

## 5. Documentation improvement suggestions

Missing sections for the release:

- **v14 release notes** (`aao-v14.md`) — currently absent; the only v14
  artifacts are the receipt and invoice PDFs under `reports/`.
- **v14 consumer layout reference** — the layout table in §2 belongs in
  `aao-v14.md`, replacing the stale "proposed-v14" candidate document.
- **How to resolve an artifact ID to a URL** — `indexes/artifacts-v1.json`
  is machine-readable and published, but no page explains the ID grammar
  (`<pass>.<projection>.<layout>`) or the authority classes
  (`archive-art-master`, `print-presentation`, `full-raster`,
  `access-derivative`).
- **Runtime consumption note** — `runtime/api-3/` and `runtime-manifest.json`
  are published but not linked from the runtime section.
- **A "which release am I looking at" note** — after the retarget, readers
  need one sentence distinguishing the live v14 mirror from the historical
  v12/v13 records.

Navigation improvements:

- Add the v14 release record to the release index and to the
  "Releases and preservation" table in `docs/pages/README.md`.
- Fix the repeated "32 passes" wording (now 33).
- In `docs/pages/releases/README.md`, move the "current mirror" paragraph to
  the top of the page so the v14 record is not buried below historical v13
  runbook text.

Workflow examples worth documenting for other users:

1. **Browse the release**: gallery → thumbnail → full PNG → print PDF.
2. **Find one product by ID**: `indexes/artifacts-v1.json` lookup → `full` or
   `print` URL, with the `.svg.gz` caveat from §6.
3. **Consume screen-1080p**: the two screen families plus `runtime/api-3/`.
4. **Verify a release**: download `SHA256SUMS`, verify a sample, then read
   `release.json` and the completion marker policy (marker last, no repair).
5. **Rebuild and review locally**: `make all-experiments-resilient` on the
   machine-bound host, then review the `output/` evidence (§7).

## 6. Defects discovered in the published v14 tree (document, do not silently fix)

1. **The published `viewer.html` is the v13 viewer.** It validates
   `asset` against `<proj>/svg/<stem>.svg.gz` and hardcodes `tree/`, so it
   cannot open any v14 `products/...` object. The upload profile's pilot check
   only required the `DecompressionStream` string, which the v13 viewer
   contains. Documentation should link the master SVGs as direct
   `.svg.gz` downloads and record the limitation; a corrected viewer requires
   a new immutable prefix (the v14 prefix cannot be repaired).
2. **The published `indexes/artifacts-v1.json` lists master SVG paths with a
   doubled `.svg.gz.gz` extension.** The actual objects are single
   `.svg.gz` (verified in the staged tree). Consumers following the index
   blindly get 404s for the master family; the release notes should state the
   defect and the correct derivation.
3. **One stale GPU-control temp file exists on eureka**:
   `assets.generated/authagraph/gpu-control-2k-portrait/network-swarm-authagraph-44-19.052559.png.tmp-133790.png`.
   It is local review evidence only (not in the uploaded tree); delete it
   during the review pass.

## 7. Human review pass: current locations of `make all-experiments` outputs

A complete current generation already exists on eureka and does not need to
be regenerated for review. It was built 2026-08-15 at the same `c3263c1`
freeze that produced the published v14 corpus.

Eureka (`/home/bkoz/src/cartofreako`), review evidence:

| What | Where | Contents |
| --- | --- | --- |
| Marshall Islands speculations | `output/marshall-islands-speculations-v01/` | 5 PNG plates (`01-…`–`05-…`) |
| Equal Earth positioning | `output/equal-earth-positioning-speculations-v01/` | 5 PNG plates |
| Water debris | `output/anthropocene-water-debris-v01/` | `contact-sheet.png` |
| Atoll evidence canary | `output/atoll-evidence-canary-v01/` | `majuro-atoll-evidence-canary.png` |
| Majuro full pass | `output/majuro-atoll-evidence-pass-v01/` | `contact-sheet.png` |
| PurpleAir interface experiment | `assets.generated/<proj>/svg/anthropocene-particulate-purpleair-{2025,2026}-<suffix>.svg` | 12 SVGs (2 years × 6 projections) |
| Majuro product SVGs/PNGs | `assets.generated/<proj>/{svg,png}/majuro-atoll-evidence-*` | 24 files |
| GPU controls | `assets.generated/<proj>/gpu-control-2k-{landscape,portrait}/` | 434 PNGs plus one stale `.tmp-` file to remove |
| Staged v14 tree | `build/s3-release-v14/` | 1,349-object mirror of the live prefix |

Rizal's working tree is missing the Majuro (0 files) and PurpleAir (0 files)
families, and its rasters predate the machine-bound freeze; treat eureka as
the authoritative review host.

Options for the review:

- **Option A — review in place (recommended).** Read the listed eureka paths
  directly, or render one combined contact sheet on eureka and copy that
  single PNG to rizal. No rebuild, no external fetches, zero re-render risk.
- **Option B — fresh full generation on eureka.** Run
  `make all-experiments-resilient` under tmux and watch the log. This re-runs
  clean, every external fetch, the resilient build, and all eight
  experiments; it needs reachable JAXA/CelesTrak/NASA hosts and roughly the
  duration of a full gate run, and its outputs should be byte-identical to
  the frozen corpus modulo host raster identity.
- **Option C — copy evidence to rizal.** `scp` the five `output/` evidence
  directories plus the Majuro/PurpleAir artifacts, then review locally.
  This is convenient but should not imply that rizal is a raster-baseline
  authority; re-generation must stay on eureka.

The review-20260816 `changed-plates-contact-sheet.png` on rizal is the prior
review artifact and can be regenerated on eureka from the current tree if the
user wants a before/after comparison.

## 8. Implementation options and recommendation

- **Option 1 — minimal retarget.** Only swap v13 URLs to v14 (§3.2) and add
  the six Groundstations plates. Fastest; leaves the release unrecorded and
  the viewer/index defects unexplained.
- **Option 2 — retarget + release record + corpus correction (recommended).**
  Option 1 plus `aao-v14.md`, the gallery data correction (§4), the
  cloud-atmosphere/legacy-atlas removals, the §6 defect notes, and the eureka
  link verification. This satisfies "all links point to v14" and "all new
  plates represented" with accurate evidence.
- **Option 3 — Option 2 + consumer documentation.** Also add the artifact-ID
  lookup page, runtime consumption note, and the five workflow examples.
  Best long-term value for other users; modest additional writing.

Recommended sequencing: Option 2 first, then Option 3 as a follow-up. Run
`make check-docs` plus `git diff --check` on rizal, then the external URL
check from eureka before proposing a commit.

## 9. Questions for the user before stage 2

1. Approve Option 2 (with Option 3 as follow-up)?
2. Review the existing eureka outputs in place (Option A), or first regenerate
   on eureka (Option B)?
3. Keep the historical `aao-v13.md` and `v13-to-v14-consumer-layout.md` pages
   as immutable records (recommended), with the new `aao-v14.md` as the live
   reference?
4. For the broken v14 `viewer.html`, prefer documenting direct `.svg.gz`
   download links now and shipping a corrected viewer in the next prefix?

## 10. Implementation status — 2026-08-19 (appended after execution)

Options 2 and 3 are implemented and verified locally, and the Option A review
evidence is recorded. A completion notice was delivered in the exchange;
this repository has no external notification tooling, so the exchange notice
served as the delivery.

### Completed

- All documentation links now target `cartofreako/v14/`: `index.md`, gallery
  README and includes, the six projection snapshots, pass pages (astronomy,
  bathymetry, network pages), projection documents (Dymaxion, Myriahedral),
  runtime and getting-started pages, the release runbook, and the site
  Release navigation link.
- New live reference `docs/pages/releases/aao-v14.md` records identity,
  layout, counts, verification, the corpus delta, immutability policy, and
  the known defects. Per the user's naming request, `s3-v13.md` became
  `aao-v13.md` with every reference updated; `v13-to-v14-consumer-layout.md`
  is marked as the migration reference.
- The 33-pass corpus is fully represented: Network Groundstations added
  everywhere, the dual-year particulate family added, and the removed
  Cloud-atmosphere and legacy-atlas plates are stated as historical rather
  than current.
- Option 3 content is in
  `docs/pages/runtime/consumer-release-usage.md`: artifact-ID grammar,
  authority classes, URL resolution with the `.svg.gz.gz` caveat, the
  `runtime/api-3/` note, and the five consumer workflows.
- The corrected viewer `docs/releases/v14-aao-viewer.html` handles v14
  `products/...` paths (including Myriahedral slice projections), validates
  them strictly, and falls back to a direct download when cross-origin
  streaming is blocked. The sealed in-prefix `viewer.html` cannot be
  repaired; a same-origin corrected copy ships with the next prefix.
- Consistency fixes outside strict documentation scope: `tests/test-screen-1080p.mjs`
  and `tests/read-screen-catalog.py` still asserted the old 211/32 corpus
  against the now-published 217/33 manifest; both were updated to 217
  artifacts / 33 pass IDs / 1,085 declared files, and their console evidence
  messages were corrected.

### Verification

- `make check-docs` passed (136 files, 1,333 local links), including the
  pass-status check.
- `git diff --check` is clean.
- Every referenced `_includes` file exists, and the gallery stems match the
  217/33 freeze exactly.
- The corrected viewer script passes `node --check`, and its asset-path
  validation accepts v14 products paths while rejecting v13 `tree/` paths
  and traversal attempts.

### Review pass (Option A)

The evidence map and integrity checks are recorded in
`docs/development/20260819_all_experiments_review.md`: all five `output/`
directories, 12 PurpleAir SVGs, 24 Majuro files, 434 GPU-control PNGs, and
the 1,349-object staged v14 tree were present and consistent on eureka at
the `c3263c1` freeze. One stale GPU-control temp file is flagged for
deletion.

### Blocked, not finished

Eureka's `sshd` stopped answering mid-session: ICMP still answers from `ord`,
but port 22 times out from both rizal and ord. Three items wait on the host
recovering:

- the visual plate inspection and temp-file deletion (exact command recorded
  in the review file);
- running the updated screen-catalog checks on eureka, whose rasters are the
  machine-bound authority; and
- the live re-check of the new v14 URLs and bucket CORS headers (the endpoint
  returned HTTP 200 from eureka earlier the same day, and the upload receipt
  records full-download verification; rizal and ord cannot reach the endpoint
  directly).

Nothing was committed or pushed. The working tree holds the completed
changes awaiting a check-in instruction.

## 11. Recommended next steps (orchestrated)

The remaining work is ordered by dependency. Items labeled **user** require
the operator; items labeled **agent** can run unattended once their gate
condition is true.

### Phase 0 — eureka recovery (user, gate for Phases 1–3)

Restore SSH access to eureka (172.31.200.55). Verify with:

```sh
ssh eureka "bash -lc 'hostname'"
```

If the host itself is healthy and only `sshd` is down, the existing scoped
sudoers remediation on eureka covers `systemctl restart sshd`.

### Phase 1 — finish the Option A review on eureka (agent)

- Visually inspect the 13 `output/` PNGs, the 12 PurpleAir SVGs, the Majuro
  contact sheet, and one landscape plus one portrait GPU control per
  projection.
- Remove the stale temp file:

```sh
rm -- /home/bkoz/src/cartofreako/assets.generated/authagraph/gpu-control-2k-portrait/network-swarm-authagraph-44-19.052559.png.tmp-133790.png
```

- Append findings to
  `docs/development/20260819_all_experiments_review.md` and close it out.

### Phase 2 — verify the screen-catalog fixes on eureka (agent)

```sh
cd /home/bkoz/src/cartofreako
make check-screen-1080p
python3 tests/read-screen-catalog.py
```

Both must pass against the machine-bound 217/33 corpus. If they do not, fix
only the specific failing evidence and re-run before Phase 5.

### Phase 3 — external link and CORS verification (agent, from eureka or VPN)

```sh
# one 200 check per new cartofreako/v14 URL introduced by this work
curl -sS -o /dev/null -w '%{http_code} %{url_effective}\n' <url>
# CORS check for the Pages-hosted corrected viewer
curl -sSI -H 'Origin: https://bdekoz.github.io' \
  https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14/products/standard/cahill-keyes/master/geometry-ck-44-22.svg.gz
```

Record the CORS result in `aao-v14.md`: if `Access-Control-Allow-Origin` is
absent, the viewer's direct-download fallback is the supported Pages path
until the next prefix ships a same-origin viewer.

### Phase 4 — local final QA (agent)

On rizal: `make check-docs`, `git diff --check`, and a fresh read-through of
`aao-v14.md`, `consumer-release-usage.md`, and
`v14-aao-viewer.html`.

### Phase 5 — human check-in gate (user)

Review the diff, then authorize commit and push. Suggested commit split:

1. `docs: retarget documentation to the v14 AAO release` (renames, gallery,
   pass pages, runbook, index);
2. `docs: add v14 release record, consumer usage, and corrected viewer`;
3. `tests: advance screen-catalog expectations to the 217/33 corpus`.

`git` will detect the `s3-v13.md` → `aao-v13.md` rename as delete/add;
commit the pair together.

### Phase 6 — publish and post-publish verification (user/agent)

Push `main`, let GitHub Pages rebuild, then confirm the live
`docs/pages/releases/aao-v14.md`, the corrected viewer page, and a sample of
retargeted gallery links. Re-run Phase 3 once more post-publish.

### Phase 7 — same-origin viewer for the next prefix (user decision)

Decide whether the next generated-assets prefix carries the corrected viewer
as its `viewer.html`. Until then, the Pages-hosted viewer plus direct
`.svg.gz` downloads remain the documented v14 behavior.

### Phase 8 — close-out

Update this status section, and let the user issue the closing
`snapshot dyad` marker instruction; no end marker is written by the agent.
