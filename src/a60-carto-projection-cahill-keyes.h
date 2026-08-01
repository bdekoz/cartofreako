// alpha60 cartography projection Cahill-Keyes -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2018-2025, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_PROJECTION_CK_H
#define a60_CARTOGRAPHY_PROJECTION_CK_H 1

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

#include "a60-carto-projection-cahill-keyes-native.h"

namespace a60::carto {

inline constexpr double cahill_keyes_width_to_height_ratio = 2.0;

/// True when a frame has finite, positive dimensions in the required 2:1
/// Cahill-Keyes aspect ratio. The tolerance admits floating-point roundoff,
/// not approximate aspect ratios.
inline bool
is_cahill_keyes_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = cahill_keyes_width_to_height_ratio * height;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

inline projection_base
validate_cahill_keyes_projection_base(projection_base value)
{
  if (!is_cahill_keyes_frame(value.pframe))
    throw std::invalid_argument(
      "Cahill-Keyes projection frame must have finite, positive dimensions "
      "with a 2:1 width-to-height ratio");
  return value;
}

/// Construct generic projection state from a variable-size map frame.
/// The projection origin is the center of frame.frame_area.
inline projection_base
make_cahill_keyes_projection_base(const frame& map_frame, string raster_name)
{
  return validate_cahill_keyes_projection_base(
    {map_frame, map_frame.width() / 2, map_frame.height() / 2,
     cahill_keyes, std::move(raster_name)});
}

/**
   Cahill-Keyes projection.

   https://en.wikipedia.org/wiki/Gene_Keyes
   http://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-&-coastline.html
   https://gist.github.com/espinielli/4259835
   https://observablehq.com/@fil/cahill-keyes-projection
*/
struct ckproj : public projection_base, public projection_api
{
  ck_native::forward_projection forward;

  ckproj(const projection_base d)
  : projection_base(validate_cahill_keyes_projection_base(d)),
    forward(pframe.height() / 2)
  { }

  /// Make a projection for any valid 2:1 map frame. The raster name is kept
  /// separate from size so one projection implementation fits every scale.
  explicit
  ckproj(const frame& map_frame, string raster_name = {})
  : ckproj(make_cahill_keyes_projection_base(map_frame,
                                              std::move(raster_name)))
  { }

  ckproj(const ckproj&) = default;

  string
  image_filename(const raster_mode v) const
  {
    const string cartodata = "visionscarto-map";
    auto& rtr = io::get_run_time_resources();
    string ret(io::end_path(rtr.data) + cartodata + "/" + name);
    if (v == outline)
      ret += "-outline";
    if (v == inverse)
      ret += "-inverse";
    if (v == raster_mode(outline | inverse))
      ret += "-outline-inverse";
    if (v == grid)
      ret += "-grid";
    if (v == glitch)
      ret += "-gitch";
    return ret + ".png";
  }

  /// Native C++20 forward projection. The one-degree longitude adjustment
  /// preserves registration with the existing visionscarto raster; the Perl
  /// octant formula itself uses its documented -20/70/160 degree boundaries.
  a60::point_2t
  meridians_to_point_2d(const double lt, const double lng) const
  {
    double adjusted_longitude = lng + 1;
    if (adjusted_longitude > 180)
      adjusted_longitude -= 360;
    const auto [ckx, cky] = forward(adjusted_longitude, lt);
    return std::make_tuple(longitude_zero_x + ckx, latitude_zero_y - cky);
  }
};

inline ckproj
make_cahill_keyes_projection(const frame& map_frame,
                             string raster_name = {})
{
  return ckproj(map_frame, std::move(raster_name));
}


/**
   Cahill-Keyes-as-per visionscarto.net's Cahill-Keyes Projection.

   vc.net == visioncarto.net
   https://vc.net/carte-di-base
   https://vc.net/public/fonds-de-cartes-it/visionscarto-cahillkeyes.svg

   https://observablehq.com/@fil/cahill-keyes-projection

   In the Cahill-Keyes octant assembly, y is the distance from the
   equator to the north pole, -y is the distance from the equator to
   the south pole, and the total circumfrence of the globe is a
   distance of 4y.

   For rendering to screen with this projection, derive y via
   4y = projection.width

   Since the rendered images are full-width but not full-height (for
   the octant grid where 2y = height.
*/

/// 1080P
const ckproj ck_1x1080(
  pck_1x1080, "visionscarto-cahillkeyes-1080p-1x.096");

const ckproj ck_2x1080(
  pck_2x1080, "visionscarto-cahillkeyes-1080p-2x.096");


/// ENGC

/// 1x
/// 22 x 17 map (landscape)
const ckproj ck_1xengc(
  frame {2112, 1056}, "visionscarto-cahillkeyes-engc-1x.096");

/// 2x
/// 2 x Engineering C (landscape)
/// 44 x 17 map (landscape)
const ckproj ck_2xengc(
  frame {4224, 2112}, "visionscarto-cahillkeyes-engc-2x-v3.300");

/// 2.66x
/// 44 x 34 map (landscape)
const ckproj ck_4xengc(
  frame {8448, 4224}, "visionscarto-cahillkeyes-engc-4x.096");

/// 2.5x
/// 4 x Engineering C (portrait)
/// (17 x 22) x 4 slices == (portrait) 68 x 22
const ckproj ck96_2bisx(
  frame {5280, 2640}, "visionscarto-cahillkeyes-engc-2.5x.096");
const ckproj ck300_2bisx(
  frame {16500, 8250}, "visionscarto-cahillkeyes-engc-2.5x.300");

/// 7.3x aka "star x"
/// 4 x Engineering C (portrait)
/// (17 x 22) x 2 slices (invert and mirror) top		-> 34 x 22
/// (17 x 22) x 2 slices bottom					-> 34 x 22
/// Tiled to project over North Pole				-> 34 x 44
/// Felix Gonzalez-Torres "Untitled", 1992/1993, poster SFMOMA  -> 29 x 44
const ckproj ck96_starx_engc(
  pck_7x, "visionscarto-cahillkeyes-engc-7.3x-starx.096");
const ckproj ck300_starx_engc(
  pck_7x, "visionscarto-cahillkeyes-engc-7.3x-starx.300");

/// 3x aka "star x"
/// 4 x A5 (portrait)
const ckproj ck96_starx_a5(
  pck_3x, "visionscarto-cahillkeyes-a5-3x-starx");

/// 44x22
const ckproj ck_44x22(
  f44x22h, "visionscarto-cahillkeyes-44x22.300");


const vd tiles_ck_2xengc_h = { 0, -2112 };
const vd tiles_ck_2xengc_v = { -240 };

const vd tiles_ck_2x1080p_h = { 0, -1920 };
const vd tiles_ck_2x1080p_v = { -280 };

// NB: Formula is xoff, xoff - (n * 1320) where n >= 1
const vd tiles_ck_2bisx_h = { 156, -1164, -2484, -3804 };
const vd tiles_ck_2bisx_v = { -265 };
const vd tiles_ck_2bisx_v2 = { -126, -886 };

const vd tiles_ck_4x_h = { -6208, -1754, -4570 };
const vd tiles_ck_4x_v = { 19 };

const vd tiles_ck_4x44x22_h = { 0, -1056, -2112, -3168 };
const vd tiles_ck_4x44x22_v = { 19 };

// 378, -1254, -2098, -3728
const vd tiles_ck_starx_engc_h = { 378, -1254, -2098, -3728 };
const vd tiles_ck_starx_engc_v = { -190 };

// 378, -1254, -2098, -3728
const vd tiles_ck_starx_a5_h = { 57, -503, -939, -1500 };
const vd tiles_ck_starx_a5_v = { -104 };

} // namespace carto

#endif
