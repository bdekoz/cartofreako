# Icosahedral Voronoi bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](voronoi-context.md) ·
[Implementation notes](voronoi-implementation-notes.md)

This bibliography separates the exact D3 version that controls the C++
numbers from general D3 API documentation, standard gnomonic cartography,
historical Voronoi terminology, related polyhedral research, and local
verification. Web resources were last checked on 2026-08-01.

## Source hierarchy

When references differ in scope or version, this implementation uses them in
the following order:

1. `d3-geo-polygon` **v1.12.1** for the twelve vertices, twenty-face order,
   parent tree, face-site behavior, shared-edge unfolding, and explicit
   `angle`, `rotate`, `scale`, and `center` values;
2. D3's official projection documentation for the inherited default
   translation and the semantics of rotation, center, scale, and screen axes;
3. the local C++ header for the native vector and affine formulas that
   reproduce those semantics; and
4. the local API test for the fixed numeric compatibility record.

The current `d3-geo-polygon` branch is useful documentation, but it is not the
numeric version target. Pinning the links below prevents later upstream
refactoring from silently changing the implementation's stated provenance.

## Controlling upstream implementation

1. **Bostock, Mike, and contributors.**
   [`d3-geo-polygon` v1.12.1](https://github.com/d3/d3-geo-polygon/tree/v1.12.1),
   2020. ISC-licensed D3 module for clipping, polyhedral projections, and
   spherical polygon operations.

   - [Pinned package metadata](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/package.json)
     records version `1.12.1`, package authorship, contributors, dependencies,
     and the ISC license identifier.
   - [Pinned commit `7f1e0ae42b6b3bb474f792f2c4b53bf4ff50f4ab`](https://github.com/d3/d3-geo-polygon/commit/7f1e0ae42b6b3bb474f792f2c4b53bf4ff50f4ab)
     is the commit referenced by the v1.12.1 tag.
   - [Pinned ISC license](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/LICENSE)
     contains the notice whose applicable portion is retained in the C++
     header.

   The module is the direct implementation source. It is not merely an
   example image or a high-level description.

2. **D3 Icosahedral map source.**
   [`src/icosahedral.js` at v1.12.1](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/src/icosahedral.js).

   This file is the controlling source for:

   - `theta = atan(0.5)` and the two staggered five-vertex rings;
   - the exact twenty triples of icosahedron vertex indices;
   - the exact twenty-entry parent array;
   - `.angle(0)`, `.rotate([108,0])`, `.scale(131.777)`, and
     `.center([162,0])`; and
   - attribution of the Icosahedral map implementation to Jason Davies
     (2013), Enrico Spinielli (2017), and Philippe Rivière (2017–2018).

   The C++ implementation ports the active default tree. It does not use the
   different, commented Myriahedral example near the end of this source file.

3. **D3 polyhedral Voronoi source.**
   [`src/polyhedral/voronoi.js` at v1.12.1](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/src/polyhedral/voronoi.js).

   This file supplies the upstream algorithmic structure: derive each default
   site from the spherical polygon centroid, center a unit-scale gnomonic
   projection on that site, choose the site with minimum spherical distance,
   connect faces using the parent array, and delegate planar assembly to the
   generic polyhedral projection.

4. **D3 generic polyhedral source.**
   [`src/polyhedral/index.js` at v1.12.1](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/src/polyhedral/index.js).

   This source finds the two shared vertices of every parent/child pair,
   projects the edge in both local faces, composes each node transform through
   the tree, and applies the final raw-output vertical orientation. It also
   implements D3's inverse traversal and streaming outline construction;
   those latter facilities are not part of the local forward point API.

5. **D3 affine matrix source.**
   [`src/polyhedral/matrix.js` at v1.12.1](https://github.com/d3/d3-geo-polygon/blob/v1.12.1/src/polyhedral/matrix.js).

   This is the direct source for the six-coefficient matrix representation,
   shared-edge similarity transform, transform multiplication order, and
   inverse matrix used by upstream. The C++ port implements the forward
   construction and multiplication, but does not need the inverse matrix.

## Official D3 API and projection semantics

6. **D3 `geoPolyhedralVoronoi` API.**
   [`d3-geo-polygon` v1.12.1 API reference](https://github.com/d3/d3-geo-polygon/tree/v1.12.1#geoPolyhedralVoronoi).

   The official module documentation defines the projection as polygons
   arranged in a tree, describes the parent-index array, explains the role of
   Voronoi sites, and notes that a gnomonic face projection is the generally
   applicable local projection. The pinned sources above, rather than the
   evolving prose on the default branch, control exact v1.12.1 behavior.

7. **Bostock, Mike, and Observable.**
   [D3 geographic projection reference](https://d3js.org/d3-geo/projection).

   The reference documents the wrapper around a raw projection. In
   particular:

   - spherical `projection.rotate` is applied before the raw transform;
   - `projection.center`, `projection.scale`, and `projection.translate`
     control planar registration;
   - the default translation is `[480,250]`, described as the center of a
     `960 x 500` area; and
   - SVG and Canvas convention place positive screen `y` downward.

   These inherited semantics explain the C++ source-canvas constants that do
   not appear explicitly in v1.12.1's `icosahedral.js`.

8. **D3 geographic projection overview.**
   [D3 `d3-geo` reference](https://d3js.org/d3-geo).

   This is supporting context for spherical geographic coordinates, adaptive
   resampling, clipping, projection streams, and the distinction between a
   point transform and rendering complete lines or polygons. The local API
   intentionally implements the forward point transform only.

## Cartographic and geometric background

9. **Snyder, John P.** *Map Projections—A Working Manual*. U.S. Geological
   Survey Professional Paper 1395, 1987, pp. 164–168.
   [USGS publication record](https://pubs.usgs.gov/publication/pp1395) ·
   [Report PDF](https://pubs.usgs.gov/pp/1395/report.pdf) ·
   [DOI: 10.3133/pp1395](https://doi.org/10.3133/pp1395)

   Chapter 22 describes the gnomonic projection as a central perspective onto
   a tangent plane, gives its spherical formulas and scale behavior, and
   explains why great circles become straight lines. Snyder is the standard
   cartographic background for interpreting each local face; he is not the
   source of D3's icosahedron topology, tree, or registration constants.

10. **Voronoï, Georges.** “Nouvelles applications des paramètres continus à
    la théorie des formes quadratiques. Deuxième mémoire. Recherches sur les
    parallélloèdres primitifs.” *Journal für die reine und angewandte
    Mathematik*, volume 134, 1908, pp. 198–287.
    [EuDML bibliographic record and full text](https://eudml.org/doc/149291) ·
    [DOI: 10.1515/crll.1908.134.198](https://doi.org/10.1515/crll.1908.134.198)

    This is the historical source of the nearest-site tessellation terminology.
    The local implementation uses the modern spherical form—regions of points
    nearest to finite unit-sphere sites—but does not derive numeric constants
    from this paper.

11. **van Wijk, Jarke J.** “Unfolding the Earth: Myriahedral Projections.”
    *The Cartographic Journal*, volume 45, issue 1, 2008, pp. 32–42.
    [TU/e Research Portal record](https://research.tue.nl/en/publications/unfolding-the-earth-myriahedral-projections) ·
    [Author project page and paper](https://vanwijk.win.tue.nl/myriahedral/) ·
    [DOI: 10.1179/000870408X276594](https://doi.org/10.1179/000870408X276594)

    Van Wijk supplies related research context for cutting a polyhedral face
    graph to a tree and unfolding it. The D3 Icosahedral source includes a
    commented alternative parent tree associated with this paper's figure 8.
    The active default tree implemented here is different, and this projection
    retains only twenty faces; see the separate
    [Myriahedral documentation](myriahedral-context.md) for the repository's
    5120-face implementation.

## Attribution and licensing record

The relevant roles are distinct:

- Mike Bostock is the author named by the v1.12.1 package and the copyright
  holder named by its ISC license.
- Jason Davies, Enrico Spinielli, and Philippe Rivière are credited in the
  controlling `icosahedral.js` for implementing the Icosahedral map in D3.
- Georges Voronoï supplies the historical tessellation name; his publication
  is background rather than copied software.
- John Snyder and Jarke van Wijk supply cartographic and polyhedral context;
  their publication text and figures are not incorporated into the code.

The applicable ISC notice from `d3-geo-polygon` v1.12.1 is preserved in
[`src/cart0freak0-voronoi.h`](../src/cart0freak0-voronoi.h). The remainder of
the repository continues under the licensing stated by its own headers and
project files. Removing a JavaScript runtime dependency does not remove
upstream attribution obligations.

## Repository implementation and verification sources

12. **Icosahedral Voronoi C++20 forward projection.**
    [`src/cart0freak0-voronoi.h`](../src/cart0freak0-voronoi.h).

    This file contains the fixed vertices, faces, parents, nearest-dot-product
    dispatch, tangent bases, gnomonic formula, edge transforms, tree
    composition, D3 rotation and registration, normalized variable-frame
    scaling, validation, public class, factory, and `960 x 500` preset.

13. **Icosahedral Voronoi public API test.**
    [`tests/test-voronoi-projection-api.cc`](../tests/test-voronoi-projection-api.cc).

    The test preserves seventeen v1.12.1 reference coordinates, selected
    affine-transform coefficients, site/topology checks, variable-size
    proportionality, complete integer-degree global coverage, antimeridian
    equivalence, invalid input, raster naming, and the common API contract.

14. **Staged implementation brief.**
    [`docs/converge-projection-voronoi.md`](converge-projection-voronoi.md).

    This local note records the three requested stages: native C++20
    projection, variable map sizes under an aspect-ratio constraint, and the
    current documentation set. It is project history, not an independent
    mathematical source.

## Terminology and claim boundary

These documents use intentionally narrow claims:

- **“Icosahedral Voronoi projection”** means this fixed D3-compatible
  twenty-face map, not every projection or diagram based on Voronoi cells.
- **“Voronoi cell”** means one nearest-centroid spherical triangle used for
  face dispatch.
- **“Source canvas”** means D3's default `960 x 500` coordinate registration;
  no source raster is required or sampled.
- **“D3-compatible”** means agreement with the v1.12.1 forward point outputs
  and fixed settings. It does not claim that the C++ point API implements D3's
  inverse, projection stream, clipping, or adaptive resampling.
- **“Gnomonic”** supports the straight-great-circle property within each face.
  It does not support equal-area, conformal, or equidistant claims.
- **“Continuous”** applies across retained tree hinges only. The eleven
  non-tree adjacencies are deliberate cuts.

---

[Documentation index](../index.md) ·
[Geometric context](voronoi-context.md) ·
[Implementation notes](voronoi-implementation-notes.md)
