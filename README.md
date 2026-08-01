# cartofreako

This repository contains a native C++20 forward implementation of the
Cahill-Keyes projection. `ckproj::meridians_to_point_2d(latitude, longitude)`
implements `projection_api` without invoking Node.js or creating temporary
files.

The construction in
`src/a60-carto-projection-cahill-keyes-native.h` follows Mary Jo Graça's
`assets/cahill-keyes/MegamapMaker-prep9.pl`, including the A-L graticule zones,
supple-zone circle intersection, and eight-octant Megamap assembly. All
original 10,000-unit construction measurements are scaled from the selected
projection height.

Run the standalone algorithm and API compatibility checks with:

```sh
make check
```

The API test covers every geographic location rendered by
`augment_carto_geo_specific`, including near-pole and near-antimeridian probes
and the twelve named cities.

## Variable map frames

`ckproj` accepts any positive, finite `a60::carto::frame` whose width is
exactly twice its height. It derives the projection origin and mathematical
scale from `frame.frame_area`; invalid aspect ratios throw
`std::invalid_argument`.

For example, the checked-in 44-by-22-inch raster is 13200 by 6600 pixels at
300 DPI:

```c++
const a60::carto::frame::area dimensions {13200, 6600};
const a60::carto::frame map_frame {dimensions};
const auto projection = a60::carto::make_cahill_keyes_projection(
  map_frame, "visionscarto-cahillkeyes-44x22.300");
```

The same construction supports the SVG's 4224 by 2112 logical coordinate
frame, small display maps, fractional dimensions, and other 2:1 sizes. The
existing named projection constants remain available as compatibility
presets over this variable-size API.

## Documentation

The [documentation index](index.md) links the geometric context, formula-level
implementation notes, source bibliography, and relevant code and tests.

## Attribution

The projection design is by Gene Keyes, based on B.J.S. Cahill's octahedral
map. The computational construction was written in Perl by Mary Jo Graça. See
the notices in `MegamapMaker-prep9.pl` regarding attribution, non-commercial
use, and commercial licensing. Keyes documents the projection's
[development history](https://www.genekeyes.com/MENUS/C-K-linklist.html),
[construction specification](https://www.genekeyes.com/B.J.S._CAHILL_RESOURCE.html),
and [Beta-2 implementation](https://www.genekeyes.com/BETA-2-FOXIT/Beta-2-Foxit.html).
