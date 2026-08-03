# Myriahedral bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](myriahedral-context.md) ·
[Implementation notes](myriahedral-implementation-notes.md)

## Foundational publication

Jarke J. van Wijk, “Unfolding the Earth: Myriahedral Projections,” *The
Cartographic Journal*, volume 45, issue 1, pages 32–42, 2008.

- [Author-hosted paper and project page](https://vanwijk.win.tue.nl/myriahedral/)
- [Paper PDF](https://vanwijk.win.tue.nl/myriahedral/CAJ103.pdf)
- [DOI: 10.1179/000870408X276594](https://doi.org/10.1179/000870408X276594)
- [TU/e Research Portal record](https://research.tue.nl/en/publications/unfolding-the-earth-myriahedral-projections)

This is the primary description of subdividing a sphere into many faces,
optimizing cuts through the dual graph, and unfolding the resulting tree into
a planar map.

## Previous implementation

Hannes Schulz and contributors,
[`temporaer/myriaworld`](https://github.com/temporaer/myriaworld).

The repository describes itself as a rugged implementation of van Wijk's
method. The C++20 code in this repository reimplements its relevant forward
geometry cleanly; it does not copy its runtime architecture or retain its
external dependency chain.

Important primary files and records:

- [README and documented example command](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/README.md)
- [`SPHEmesh.cpp`: icosahedron and recursive face order](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/src/SPHEmesh.cpp)
- [`cutting.cpp`: minimum spanning tree and flattening traversal](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/src/cutting.cpp)
- [`geo.cpp`: triangle-to-triangle coordinate transfer](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/src/geo.cpp)
- [`read_shapefile_data.cpp`: mesh graph, smoothing, and edge weighting](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/src/read_shapefile_data.cpp)

The pinned revision is the upstream head inspected while implementing this
projection. Pinning makes line history and algorithm provenance reproducible.

## Configuration evidence and adopted tree

The upstream README publishes this example:

```sh
./myriaworld --depth 5 --sigma 0.4 --wlon 3. \
  --output test --alpha 1 --rotate 0 \
  --clat 313 --clon -65 --roll -315 --render png
```

That command is valuable evidence for the intended depth, preprocessing
pipeline, and available controls. It does **not** generate a tree that aligns
with the black-and-white sample's visible geographic branches. The upstream
repository does not preserve a command line alongside each sample asset, and
the configuration question remains recorded in
[upstream issue #2](https://github.com/temporaer/myriaworld/issues/2).

For this implementation, the historical preprocessing was reproduced with
the exact face overlap data and candidate trees were compared against visible
geographic anchors in the requested raster. The adopted compatibility
configuration is depth `5`, Gaussian sigma `0.7`, `wlat=0.5`, `wlon=0.1`,
`clat=-60`, `clon=-65`, full flattening, and a final `335` degree rotation.
It is reproducible and visually registered, but it is not represented as the
unrecoverable original command that created the PNG.

## Geographic source data

[Natural Earth](https://www.naturalearthdata.com/) provides public-domain map
data at several scales. The historical workflow used the 1:10m countries and
ocean datasets to estimate land coverage and choose favorable cuts.

- [Natural Earth vector repository](https://github.com/nvkelso/natural-earth-vector)
- [Natural Earth terms of use](https://www.naturalearthdata.com/about/terms-of-use/)

Natural Earth and S2 geometry are preprocessing provenance only. Neither is a
runtime dependency of `a60::carto::myriaproj`.

## Local base raster

The registration asset is:

[`assets.static/myriahedral/black-white-downsampled.png`](../assets.static/myriahedral/black-white-downsampled.png)

Properties verified during implementation:

| Property | Value |
| --- | --- |
| Dimensions | `4480 x 2520` pixels |
| Canvas ratio | `16:9` |
| Color model | 8-bit grayscale PNG |
| SHA-256 | `1228cae3fdcbdcb867952135e9eeaec7d894c092eb8dae828d0dd61ad8658fd7` |

The digest is identical to the upstream
[`samples/black-white-downsampled.png`](https://github.com/temporaer/myriaworld/blob/011d6f8ef0725c0c5f3ba44b66f13d7cf6ac038a/samples/black-white-downsampled.png)
at the pinned revision.

The raster supplies visual context and the `16:9` compatibility canvas. It is
not sampled or used as a numeric lookup table by the forward transform.

## Licensing note

The `cartofreako` implementation is distributed under the license stated in
its source headers and repository. The upstream author stated in
[myriaworld issue #1](https://github.com/temporaer/myriaworld/issues/1) that
the code and sample image could be used under BSD terms. At the inspected
revision, however, the upstream repository did not contain a standalone
`LICENSE` file. That issue comment is therefore the available upstream record,
not a substitute for legal advice or a newly invented license text.

Natural Earth states that its data is in the public domain. Van Wijk's paper
is cited for the projection method; no paper text or figure is incorporated
into the implementation.

## Related local documentation

- [Implementation notes](myriahedral-implementation-notes.md) contain the
  exact formulas, fixed-tree design, API, scaling, tests, and limits.
- [Geometric context](myriahedral-context.md) illustrates the primal mesh,
  dual tree, cuts, quadrants, axes, and source-canvas relationship.
- [`docs/converge-projection-myriahedral.md`](converge-projection-myriahedral.md)
  preserves the staged implementation brief.
- [`assets.static/myriahedral`](../assets.static/myriahedral/README.md) preserves
  the exact reconstruction artifacts and checksums used by the implementation.
