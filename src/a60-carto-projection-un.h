// alpha60 cartography projection UN -*- mode: C++ -*-

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

#ifndef a60_CARTOGRAPHY_PROJECTION_UN_H
#define a60_CARTOGRAPHY_PROJECTION_UN_H 1

namespace a60::carto {

/**
   United Nations (UN) Map of the World, 4170, revisions 11-13.
   This is a CC image file that has been
   subsequently tweaked to come up with the base .svg file in use
   here.

   Base SVG image:
   un-world-map-4170r12-meridians-22x17-2013.svg

   The current approach is to assume an equirectangular projection,
   with the standard parallel at the equator (plate carrée).
*/
struct erproj : public projection_base, public projection_api
{

  /// Fudge constants for each plane.
  double	k_x;
  double	k_y;

  erproj(const projection_base d, double x, double y)
  : projection_base(d), k_x(x), k_y(y) { }

  erproj(const erproj&) = default;

  string
  image_filename(const raster_mode v) const
  {
    const string cartodata = "united-nations-map";
    auto& rtr = io::get_run_time_resources();
    string ret(io::end_path(rtr.data) + cartodata + "/" + name);
    if (v == outline)
      ret += "-outline";
    if (v == inverse)
      ret += "-outline-inverse";
    return ret + ".png";
  }

  /// Assumes projection with no distortion, which is most certainly
  /// not correct.
  a60::point_2t
  meridians_to_point_2d(const double lt, const double lng) const
  {
    bool ltp = lt >= 0.0;
    bool lngp = lng >= 0.0;

    // Position point on map.
    double x0 = this->longitude_zero_x;
    double xdelta = std::abs((pframe.width() / 360) * lng);
    double y0 = this->latitude_zero_y;
    double ydelta = std::abs((pframe.height() / 180) * lt);

    if (ltp)
      y0 -= ydelta;
    else
      y0 += ydelta;

    if (lngp)
      x0 += xdelta;
    else
      x0 -= xdelta;

    x0 += k_x;
    y0 += k_y;

    return std::make_tuple(x0, y0);
  }
};


/// 1x
/// 22 x 17 map

/// un-world-map-4170r13, longitude range (-180 to 180)
const frame pun_1x(1892, 949);
const erproj er96 = { { pun_1x, 874, 475, equirectangular, "un-world-map-4170r13-w1892-h949" },
		      11.5, -0.5 };

  const erproj er300 = { { pun_1x, 874, 475, equirectangular, "un-world-map-4170r13-w6306-h3164" },
		       11.5, -0.5 };

/// 2.66x
/// 44 x 34 map
/// un-world-map-4170r13, 96 dpi, longitude range [-180 to 180]
const frame pun_2x(5046, 2532);
const erproj er96_2x = { { pun_2x, 2340, 1267, equirectangular, "un-world-map-4170r13-2.5x-w5046-h2532" },
			   20, -1 };

const erproj er300_2x = { { pun_2x, 2340, 1267, equirectangular, "un-world-map-4170r13-2.5x-w7884-h3956" }, 20, -1 };

const vd tiles_er_2x_h = { -3084, 100, -1550 };
const vd tiles_er_2x_v = { 542 };

}// namespace carto

#endif
