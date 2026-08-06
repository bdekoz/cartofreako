# Stage 11 proposal: restructure documentation

**Proposed:** 2026-08-06  
**Status:** plan only; no bulk document move is part of Stage 10

[Documentation index](../../index.md) ·
[Stage 10 notes](stage-10-webassembly.md) ·
[Convergence status](converge-generation.status-20260806.md)

## Recommendation

Move the current flat `docs/` collection into a topic-oriented nested
`docs/pages/` tree, but do it as a link-preserving migration rather than one
large rename. The first pilot should be the newly consolidated browser
documentation because it now has a clear quick-start, architecture, API,
examples, and historical boundary.

Keep Markdown as the source of truth. A static-site generator may consume it,
but the repository must remain navigable on GitHub and through local relative
links without requiring a documentation build.

## Problems to solve

The current documentation grew chronologically and has four overlapping
navigation systems:

- the large hand-maintained root [`index.md`](../../index.md);
- a mostly flat `docs/*.md` directory;
- dated reports already beginning under `docs/pages/`; and
- source-local READMEs such as [`src.wasm/README.md`](../../src.wasm/README.md)
  and data-profile notes under `assets.static/`.

As a result:

- context, implementation, bibliography, workflow, plan, and status documents
  are adjacent only by filename convention;
- historical ledgers can look like current instructions;
- the source guide in `index.md` is expensive to update and easy to stale;
- new web developers encounter the older illustrative Myriahedral tutorial
  before the production all-projection quick start; and
- moving a document risks hundreds of relative-link changes with no automated
  redirect or link check.

## Proposed tree

```text
docs/
  README.md                         documentation entry point
  navigation.json                  ordered, machine-readable navigation
  pages/
    getting-started/
      prerequisites.md
      generation.md
      review-generated-output.md
    projections/
      authagraph/
        context.md
        implementation.md
        bibliography.md
      cahill-keyes/
        context.md
        implementation.md
        bibliography.md
        slicing.md
      dymaxion/ ...
      myriahedral/ ...
      star-x/ ...
      voronoi/ ...
    generation/
      methods.md
      profiles.md
      typography.md
      natural-earth.md
    passes/
      astronomy.md
      cloud-atmosphere.md
      orbital-technosphere.md
      anthropocene/
        implementation.md
        enrichment.md
      resources/
        implementation.md
        enrichment.md
      network-swarm.md
      network-infrastructure.md
      bathymetry-roulette.md
    web/
      quick-start.md
      runtime-api.md
      geometry-buffer.md
      slicing.md
      workers.md
      frameworks.md
      illustrative-myriahedral-workflow.md
      illustrative-myriahedral-example.md
    decisions/
      generation-methods.md
      stage-10-webassembly.md
      stage-11-documentation-plan.md
    status/
      converge-generation-20260806.md
    history/
      converge-generation-ledger.md
  assets/                          documentation-only diagrams/screenshots
  doxygen/                         generated native API, still ignored
```

The exact directory spelling is less important than the separation of current
instructions, design decisions, status snapshots, and historical request
ledgers.

## Ownership rules

Use these rules before moving files:

| Document kind | Canonical location | Rule |
| --- | --- | --- |
| User task/how-to | `pages/getting-started` or `pages/web` | Lead with runnable outcome; avoid architecture history |
| Projection explanation | `pages/projections/<id>` | Keep context, implementation, and sources together |
| Generate-pass operation | `pages/passes/<pass>` | Include source contracts, products, checks, limits |
| Cross-cutting implementation decision | `pages/decisions` | Date and status the decision |
| Dated audit | `pages/status` | Immutable snapshot plus links to subsequent updates |
| Raw request/conversation ledger | `pages/history` | Clearly label non-authoritative historical material |
| Source-specific API | source-local `README.md` | Link outward to the user guide; do not duplicate it |
| Generated C++ API | `docs/doxygen` | Keep separate from authored pages |

Each authored page should gain small front matter or an equivalent machine
readable header:

```yaml
---
id: web.quick-start
title: Cartofreako WebAssembly quick start
status: current
owners: [web-runtime]
last_reviewed: 2026-08-06
redirect_from:
  - /docs/pages/webassembly-quick-start.md
---
```

Stable IDs, not filesystem paths, should drive generated navigation and link
aliases.

## Migration sequence

### Stage 11.1 — inventory and safety net

1. Add `scripts/check-doc-links.py` to validate local Markdown links, anchors,
   duplicate IDs, case, and referenced source paths.
2. Emit a machine-readable inventory containing title, kind, status, inbound
   links, and proposed destination.
3. Add the checker to `make check-docs` and CI before moving anything.
4. Record an explicit policy for generated files and external URL checks;
   normal offline checks should not require internet access.

Deliverable: link errors are visible before the migration changes paths.

### Stage 11.2 — browser-documentation pilot

Move the small, coherent browser set first:

```text
docs/pages/webassembly-quick-start.md            -> pages/web/quick-start.md
docs/pages/stage-10-webassembly.md               -> pages/decisions/stage-10-webassembly.md
docs/web-workflow.md                             -> pages/web/illustrative-myriahedral-workflow.md
docs/web-example.md                              -> pages/web/illustrative-myriahedral-example.md
```

Split the long source-local WASM README only when a section becomes a stable
public API page. Keep the README as the build/path reference.

For every move, leave a short compatibility stub at the old path containing
the new relative link. GitHub has no repository-local HTTP redirects, so the
stub is the durable redirect.

Deliverable: a working nested section and a proven redirect/checker process.

### Stage 11.3 — projection clusters

Move one projection at a time: context, implementation notes, bibliography,
and any slicing notes. Update the root index through generated navigation
rather than manually editing every table row. Keep source header links
clickable from both the nested page and the root index.

Deliverable: six self-contained projection sections with consistent local
navigation.

### Stage 11.4 — generate passes and data contracts

Move implementation/enrichment pairs together so a plan cannot be mistaken
for deployed capability. Every pass landing page should state:

- implemented products;
- profile and source paths;
- acquisition/preparation/generation commands;
- coverage and release gates;
- verification targets; and
- known scientific/licensing boundaries.

Deliverable: one current operational entry point per pass.

### Stage 11.5 — status, decisions, and history

Move the raw `converge-generation.md` ledger to `history`, the dated audit to
`status`, and accepted architecture records to `decisions`. Add conspicuous
status badges or front matter. A current page may link back to history; a
historical page must link forward to the current implementation.

Deliverable: readers can distinguish request, decision, implementation, and
dated audit.

### Stage 11.6 — generated navigation and cleanup

Generate these from `navigation.json` plus page metadata:

- the compact documentation section of root `index.md`;
- previous/next links;
- a page inventory/status report; and
- optional MkDocs/Docusaurus navigation if one is adopted.

After at least one release with passing inbound-link checks, decide whether
old-path stubs stay indefinitely or only for externally linked pages.

Deliverable: one maintained navigation source and no unclassified page.

## Link and slicing terminology migrations

Stage 11 should standardize a few terms while paths change:

- **carrier**: complete ratio-correct projected finite map;
- **viewport**: rectangular post-projection view;
- **native-cell mask**: topological face/octant selection;
- **geographic preclip**: WGS 84 source filter;
- **planar tile**: non-wrapping delivery chunk;
- **generate pass**: semantic native artifact family; and
- **layer**: group inside one output, not a synonym for pass.

This prevents the earlier Stage 7 “layer” ambiguity and keeps print slices and
browser slices aligned.

## Tooling recommendation

Start with repository-owned scripts and ordinary Markdown. Do not select a
site framework until the inventory exists. If a rendered site is later
desired, MkDocs Material is a reasonable low-complexity fit, while Docusaurus
is attractive only if versioned JavaScript API docs and interactive examples
justify its Node toolchain. Either renderer must consume the same pages and
stable IDs; it must not create a second documentation source.

Useful automation:

```text
make check-docs          local links, anchors, IDs, source paths
make docs-index          regenerate root navigation blocks
make docs-site           optional rendered site
make doxygen             existing C++ API output
```

Avoid network-checking every external research URL in the default suite.
Schedule that separately and cache the dated result because institutional data
portals change or block automation.

## Acceptance criteria

Stage 11 is complete when:

- every authored Markdown file has a stable ID, kind, status, and current
  canonical path;
- all local links and anchors pass on a case-sensitive filesystem;
- every moved externally linked page has a compatibility stub or explicit
  redirect policy;
- the root index and section navigation derive from one inventory;
- current how-to pages never depend on reading a historical ledger;
- each projection and generate pass has one obvious landing page;
- the browser quick start reaches a working example in three links or fewer;
- `make check-docs` is fast, offline, and part of CI; and
- Doxygen output remains generated and does not pollute authored-page checks.

## What not to do

- Do not move the whole directory in one commit without first adding the link
  checker.
- Do not silently delete or rewrite the chronological convergence ledger.
- Do not duplicate implementation status across several manually maintained
  indexes.
- Do not require a site generator to read source Markdown on GitHub.
- Do not mix external data snapshots or generated artifacts into
  `docs/pages`.

## First implementation batch

The recommended first Stage 11 change is bounded:

1. implement `check-doc-links.py` and `make check-docs`;
2. create `docs/navigation.json` and page metadata conventions;
3. migrate only the four browser documents listed in Stage 11.2;
4. leave compatibility stubs;
5. regenerate the documentation map; and
6. verify all repository-local links before proceeding to projection pages.

That batch proves the structure without turning documentation reorganization
into an all-repository flag day.

---

[Documentation index](../../index.md) ·
[Stage 10 notes](stage-10-webassembly.md) ·
[Web-developer quick start](webassembly-quick-start.md) ·
[Convergence status](converge-generation.status-20260806.md)
