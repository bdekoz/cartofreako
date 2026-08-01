// alpha60 cartography projection -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2016-2025, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_PROJECTION_H
#define a60_CARTOGRAPHY_PROJECTION_H 1

namespace a60::carto {

/// Projection types.
  enum projection_mode
    {
      authagraph,
      cahill_keyes,
      equirectangular,
      myriahedral,
      voroni
    };


/**
   Projection: the visual representation, mapping 3D to 2D.

   Transforming spherical shapes to 2D surfaces is not trivial.

   Doing this correctly requires
   1. 2D representation
   2. math representing the 3D -> 2D transformation, ie the projection.

   Potential projections for world maps are: Voroni, Cahill-Keyes,
   Robinson, Winkel Tripel, Natural Earth, AuthaGraph WorldMap, etc.
*/
struct projection_base
{
  /**
     Raster versions.

     3 base maps for all viz
     cgphy    - gray land white outline map on white
     cgphyout - white land black outline map on white aka (outline)
     cgphyinv - black land white outline map on black
     aka (outline x inverse)
  */
  enum raster_mode { filled, outline, inverse, grid, glitch };

  /// Projection size.
  frame			pframe;

  /// Meridian center point (0,0) and origin in pixels for drawing.
  double		longitude_zero_x;
  double		latitude_zero_y;

  /// Projection raster file name.
  projection_mode	pmode;
  std::string		name;
};

/// Abstract base class for derived projections.
struct projection_api
{
  projection_api() = default;
  projection_api(const projection_api&) = default;
  projection_api& operator=(const projection_api&) = default;

  /// Get the filename from the path to the image used in the base map.
  virtual string
  image_filename(const projection_base::raster_mode v) const = 0;

  /// Draws geographic data on globe to a 2D point on the projection.
  virtual a60::point_2t
  meridians_to_point_2d(const double lt, const double lng) const = 0;
};

} // namespace carto

#endif
