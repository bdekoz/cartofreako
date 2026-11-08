# Current delivery and deferred follow-up — 8 November 2026

The completed Stage 2 implementation is committed and pushed as
`04114b36e83e8df025b2ca2f5850a2adc12b6d5d`. Its
[completion record](20261108_anthropocene_ocean_temperature_stage_2.md)
contains the methods, results, validation and human-gated decisions.

Current delivery:

- **53 named atlas plates: 39 defaults and 14 optional prototypes.** The
  default World/Japan edition has 156 verified separate map/legend sheets.
- Stage 1 contributes four optional SST/anomaly identities and a separate
  coral thermal-stress overlay. Stage 2 contributes eight optional year
  identities, 128 review sheets and four scientific figures. The remaining
  two optional identities are Bathymetry.
- Numerical, export, catalog, pass-status and generation-style checks passed
  for the implementation. The standard native artifact manifest has 223
  entries. Existing published galleries retain their dated source editions.
- The current resource profile contains 59 definitions: 16 implemented
  metrics and 43 exploration-only definitions, including the completed
  lithium and uranium additions among the implemented metrics.

The documentation refresh updates the main entry points and current counts.
The user deferred further work before exiting and restarting. Resume with
the following concrete items; no Eureka build was started in this session.

1. **Eureka rebuild.** The intended commands are `make clean; make all` on
   Eureka after pulling the committed work. `make all` selects the standard
   native projection graph. Default-atlas composition and Stage 2 climate
   preparation/rendering have separate explicit targets. Host dependencies,
   local source availability and the actual clean rebuild remain to be checked.
2. **Documentation checker.** The existing `make check-docs` invocation
   failed before reporting all link results: `scripts/check-doc-links.py`
   raised `ValueError` while treating
   `scripts/templates/setouchi-futures-manual.html` as relative to the
   absolute repository root. Inspect self-fragment resolution and unexpanded
   template links, then rerun the repository-wide check. This documentation
   update does not claim that full gate passed.
3. **Current aggregate atlas books.** The individual 156 sheets passed, but
   `scripts/build-setouchi-revision-review.py` still asserts 38 entries and
   152 exports for the historical edition. Update the assembly and filename
   binding checks for the current catalog before declaring the full
   `make atlas` books complete. This is separate from `make all`.
4. **Publication and fresh-checkout links.** Review the local-only delivery
   indexes and their ignored print-master links before any gallery
   publication. A fresh checkout needs to regenerate those print masters;
   curated previews, normalized data and receipts are already committed.

Default promotion, public-gallery publication and expanded provider access
remain the human decisions listed at the end of the Stage 2 record.
