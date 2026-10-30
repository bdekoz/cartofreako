# Fuller paired-role integration

`src.generate/network-swarm-data.h` now retains an optional uploader role and the
source selection policy while preserving existing downloader-only consumers.
Unknown policy values are rejected. The existing network-swarm generation test
passes with the modified header.

`src.generate/fuller-swarm-analysis.h` supplies the bounded native integration:

- Validated H3 identities and actual H3-parent aggregation, retaining member IDs,
  known per-field sums and field coverage. Missing contributions are not observed
  zeros. These sums do not establish distinct people.
- Existing projection runtime integration; all six production projection names
  are exercised by the focused Izzi integration test. Geographic and analytic
  identities remain independent of projected positions.
- A hypothetical global service model, outside projection code: interval capacity
  is days × GB/day; sent = min(capacity, demand / (1 − loss)); delivered = sent ×
  (1 − loss); shortfall = demand − delivered. Parameters must be finite, days
  positive and loss in [0,1). Collection transfer may serve as an explicitly
  modeled demand, not inferred historical infrastructure load.

The native application is `../izzi/examples/fuller-studies.cc` relative to this
checkout. It shares selection between two geographic projections, paired
matrices, expandable H3 parent details and fixed weekly histories. Registered
map/grid changes are instantaneous, with no interpolated observations. The study
uses six fixed illustrative records per title and exports all retained source
rows separately.

Scope boundary: the existing production clustering/canonicalization path is not
migrated to the new lattice. Per-indicator map layer controls, displacement
tethers and regional scenario routing/shortfall maps remain unfinished. The
bounded scenario is global; no cell receives a fabricated share of collection
transfer. See Izzi's `docs/development/fuller-implementation.md` for build commands,
the Stage 0–8 acceptance map, source receipts and accessibility-test limits.
