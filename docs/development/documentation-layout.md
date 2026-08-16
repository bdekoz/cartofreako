---
layout: default
title: Documentation architecture
---

# Documentation architecture

**Implemented:** 2026-08-10
**Status:** current architecture record

[Documentation index](../pages/README.md) ·
[Development records](README.md) ·
[Machine-readable navigation](../pages/navigation.json)

## Outcome

Cartofreako's authored product documentation is organized as one topic-oriented
tree under `docs/pages/`. Development and stage-ledger records live in
`docs/development/`. The original migration moved 72 existing Markdown
documents, created section landing pages, and recalculated repository-relative
links from their original locations. A 2026-08-15 follow-up split moved
`docs/pages/development/` to `docs/development/` so development records remain
first-class but do not sit inside the authored product tree. The user
explicitly approved breaking the former `docs/*.md` URLs, so the old locations
have no compatibility stubs.

Markdown remains the source of truth. The same files are readable in a Git
checkout, on GitHub, and through the repository-root Jekyll build used by
GitHub Pages.

## Current tree

```text
docs/pages/
  README.md                    compact technical index
  navigation.json             ordered machine-readable navigation
  getting-started/            prerequisites and generation workflows
  gallery/                    image-first landing page and six contact sheets
  projections/<family>/       context, implementation, and bibliography
  passes/                     generation-pass contracts and metric status
  data/                       acquisition and source-data notes
  runtime/                    forward/reverse and browser-consumer APIs
  history/                    dated status and request/projection ledgers
  releases/                   GitHub and UCB AAO product procedures/evidence

docs/development/
  README.md                    development index and stage-ledger landing page
  documentation-layout.md     this architecture record
  stage-*.md                   active and closed stage development ledgers
  *-speculations-v01.md        local speculative render and slice records
```

`docs/profile-markers/` remains separate because it is evidence metadata, not
authored product documentation. `docs/doxygen/` remains the generated native
API destination. The non-Markdown templates, viewers, and upload profile in
`docs/releases/` remain implementation inputs; their human-readable release
documentation lives in `docs/pages/releases/`.

## Information classes

| Class | Location | Interpretation |
| --- | --- | --- |
| First use | `getting-started/` | Runnable prerequisites and generation entry points |
| Visual discovery | `gallery/` | S3-backed thumbnails with full PNG, layered SVG, and print PDF actions |
| Projection reference | `projections/<family>/` | Mathematical context, implementation contract, and sources |
| Pass reference | `passes/` | Source identity, transformation, lifecycle class, output, and limitations |
| Runtime integration | `runtime/` | Native/WebAssembly forward and reverse APIs and consumer plans |
| Current development | `docs/development/` | Implemented architecture and active stage convergence records |
| Historical evidence | `history/` | Non-authoritative request ledgers and dated state snapshots |
| Release/preservation | `releases/` | Product-specific GitHub and UCB AAO procedures and observed evidence |

A historical document must point readers toward a current implementation when
one exists. A current how-to should not require readers to reconstruct a
workflow from the request ledger.

## Repository ownership boundary

Cartofreako owns projection and pass semantics, exact generated-product
inventory, product validation, galleries, release profiles, report content,
and observed publication evidence. Shared UCB Active Archive transport and
annual Alpha60 campaign operations are authoritative in
[`alpha60-clusterops`](https://github.com/alpha60-devops/alpha60-clusterops).

The cross-repository comparison on 2026-08-10 found no annual-campaign
Markdown files in Cartofreako to migrate or delete. The current operational
material already exists only in `alpha60-clusterops`, is linked from its
documentation index, and includes the newer shared-AAO and sealed headless
closeout rules:

- [annual campaign observer](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/docs/year-campaign-observer.md);
- [2023 unattended architecture](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/docs/year-2023-unattended-architecture.md); and
- [shared AAO upload interface](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/docs/storage/shared-aao-upload.md).

Do not add `year-*-unattended.md`, `year-campaign-observer.md`, or annual
campaign runbooks to Cartofreako. Link to the operations authority instead.
Cartofreako retains only its product-specific AAO wrapper and release facts.

## Navigation and URL policy

`navigation.json` records the ordered section landing pages. The Jekyll header,
root project index, and authored pages link directly into the new tree. The
canonical Pages routes are derived from the Markdown paths; for example:

```text
/docs/pages/gallery/
/docs/pages/projections/cahill-keyes/implementation.html
/docs/pages/passes/resources/metric-catalog.html
/docs/pages/runtime/projection-api.html
/docs/development/stage-16.html
```

The migration intentionally does not preserve paths such as
`/docs/gallery.html`, `/docs/cahill-keyes-implementation-notes.html`, or the
pre-split `/docs/pages/development/stage-16.html`.
Repository-relative Markdown links remain preferred inside authored pages so
they work both before and after Jekyll rendering.

## Verification contract

`make check-docs` performs an offline check of local Markdown and HTML links,
case-sensitive paths, directory landing pages, and Markdown heading anchors.
External research URLs are excluded from the default check. GitHub Pages runs
the same gate before Jekyll builds, preventing a file move from silently
publishing broken local navigation.

The required documentation checks are:

```sh
make check-docs
git diff --check
```

This architecture replaces the earlier Stage 11 staged-migration proposal.
Because URL breakage was explicitly accepted, the implementation was done as
one coherent move rather than retaining duplicate stubs through another
release.
