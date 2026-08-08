# Fiber synthesized static dataset

This directory is a validated cleanup and union of the TeleGeography
submarine-cable API snapshots `v3.2022` and `v3.20260805`. It is not the
set difference `new - old`; `assets.static/fiber-evolution` remains reserved
for a future strict difference dataset.

The default rendered layer is `v3.20260805`. The cleaned union contains every
newer observation plus only unmatched `v3.2022`-only observations, so
matched older geometry is not drawn twice. The source-separated observation
files retain both inputs for audit.

- `routes.geojson`: cleaned union used by the standard generation pass
- `landings.geojson`: cleaned-union landing points
- `systems.json`: identity evidence, matches, and snapshot-only classifications
- `route-observations.geojson`: both source route observations
- `landing-observations.geojson`: both source landing observations
- `manifest.json`: source pins, counts, policies, caveats, and payload hashes
- `SHA256SUMS`: integrity list for this directory

The union has 746 comparison identities, 767
route features, and 2037 landing features. A label such
as `v3.2022-only` or `v3.20260805-only` records snapshot membership only;
it does not prove construction or decommission.

Source map data is licensed CC BY-NC-SA 3.0 Unported. Generated artifacts
retain that license boundary.
