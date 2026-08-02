// alpha60 cartography projection Star-X -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2026, Benjamin De Kosnik <b.dekosnik@gmail.com>
//
// The local face geometry is the Cahill-Keyes construction by Gene Keyes,
// programmed by Mary Jo Graça. See cart0freak0-cahill-keyes.h for its
// attribution and use terms.

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef cart0freak0_STAR_X_H
#define cart0freak0_STAR_X_H 1

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>

#include "cart0freak0-cahill-keyes.h"

namespace a60::carto {

/**
   Star-X uses the historic four-panel 34:44 carrier, reduced to 17:22.

   A normalized Cahill-Keyes map is 22 by 11 units. Its two 11-by-11
   four-face groups are stacked in a 17-by-22 carrier, leaving three units
   of margin on either side. The ratio is therefore 17/22.
*/
inline constexpr double star_x_width_to_height_ratio = 17.0 / 22.0;

/**
   Vertical separation between the two square group carriers, expressed as
   a fraction of frame height. Zero preserves the original edge-to-edge
   carrier placement; a negative value overlaps the carriers and pulls the
   visible octants toward the center.

   The default is -4.5/44, so a 34-by-44 drawing moves the upper group down
   2.25 units and the lower group up 2.25 units.
*/
inline constexpr double star_x_default_group_shift_ratio = 2.25 / 44.0;
inline constexpr double star_x_default_group_gap_ratio
  = -2 * star_x_default_group_shift_ratio;

struct star_x_layout
{
  double group_gap_ratio = star_x_default_group_gap_ratio;
};

inline star_x_layout
validate_star_x_layout(const star_x_layout value)
{
  if (!std::isfinite(value.group_gap_ratio)
      || value.group_gap_ratio < -0.5
      || value.group_gap_ratio > 0)
    throw std::invalid_argument(
      "Star-X group gap ratio must be finite and within [-0.5, 0]");
  return value;
}

/// True when a frame has finite, positive dimensions in the required
/// 17:22 Star-X aspect ratio. The tolerance admits floating-point
/// roundoff, not approximate aspect ratios.
inline bool
is_star_x_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = star_x_width_to_height_ratio * height;
  if (!std::isfinite(expected_width))
    return false;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

inline projection_base
validate_star_x_projection_base(projection_base value)
{
  if (!is_star_x_frame(value.pframe))
    throw std::invalid_argument(
      "Star-X projection frame must have finite, positive dimensions "
      "with a 17:22 width-to-height ratio");
  return value;
}

namespace star_x_detail {

struct point_2d
{
  double x;
  double y;
};

enum class face_group
{
  one,
  two
};

struct assembled_point
{
  point_2d point;
  face_group group;
};

/**
   Assemble a centered Cahill-Keyes native point into the Star-X carrier.

   The native projector below uses scaffold altitude 1/4. Its complete
   M-layout is therefore 1 unit wide by 1/2 unit high. Each four-face
   group is a 1/2-by-1/2 square. Group one (negative native x) is placed
   below the frame midpoint. Group two is rotated 180 degrees and placed
   above it. A signed carrier gap separates or overlaps the two groups;
   results are normalized to the full 17:22 frame.
*/
inline assembled_point
assemble_native_point(const double cahill_keyes_x,
                      const double cahill_keyes_y,
                      const star_x_layout layout = {})
{
  constexpr double group_side = 0.5;
  constexpr double side_margin = 3.0 / 22.0;
  const bool second_group = cahill_keyes_x >= 0;
  const double half_gap = layout.group_gap_ratio / 2;

  const double x_in_height_units
    = second_group
        ? side_margin + group_side - cahill_keyes_x
        : side_margin + group_side + cahill_keyes_x;
  const double y = second_group
                     ? group_side / 2 + cahill_keyes_y - half_gap
                     : 3 * group_side / 2 - cahill_keyes_y + half_gap;
  return {{x_in_height_units / star_x_width_to_height_ratio, y},
          second_group ? face_group::two : face_group::one};
}

inline assembled_point
project_to_normalized_map(const double latitude, const double longitude,
                          const star_x_layout layout = {})
{
  // For a unit-height Star-X carrier, each group side is 1/2 and the
  // source Cahill-Keyes frame is 1 by 1/2. Its scaffold altitude is 1/4.
  static const ck_native::forward_projection forward(0.25);
  const double adjusted_longitude
    = cahill_keyes_registered_longitude(longitude);
  const auto [x, y] = forward(adjusted_longitude, latitude);
  return assemble_native_point(x, y, layout);
}

} // namespace star_x_detail

/// Construct generic projection state from a variable-size 17:22 frame.
/// Only frame_area is retained; map placement remains cartography's job.
inline projection_base
make_star_x_projection_base(const frame& map_frame, string raster_name,
                            const star_x_layout variable_layout = {})
{
  const star_x_layout layout = validate_star_x_layout(variable_layout);
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_star_x_projection_base(
    {projection_frame, 0, 0, star_x, std::move(raster_name)});
  const auto zero
    = star_x_detail::project_to_normalized_map(0, 0, layout).point;
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/**
   Variable-size Star-X projection.

   The forward transform preserves the Cahill-Keyes half-octant formulas
   and M-layout registration. It splits that layout into its left and
   right four-face groups, places the left group below the center, and
   rotates the right group 180 degrees into the upper half.
*/
struct starxproj : public projection_base, public projection_api
{
  star_x_layout layout;

  explicit starxproj(const projection_base value,
                     const star_x_layout variable_layout = {})
  : projection_base(validate_star_x_projection_base(value)),
    layout(validate_star_x_layout(variable_layout))
  {
    const auto zero
      = star_x_detail::project_to_normalized_map(0, 0, layout).point;
    longitude_zero_x = zero.x * pframe.width();
    latitude_zero_y = zero.y * pframe.height();
  }

  /// Make a projection for any valid 17:22 frame. Frame placement offsets
  /// are deliberately discarded; the projection owns only frame_area.
  explicit starxproj(const frame& variable_frame, string raster_name = {},
                     const star_x_layout variable_layout = {})
  : starxproj(make_star_x_projection_base(variable_frame,
                                           std::move(raster_name),
                                           variable_layout),
              variable_layout)
  { }

  starxproj(const starxproj&) = default;

  string
  image_filename(const raster_mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  a60::point_2t
  meridians_to_point_2d(const double latitude,
                        const double longitude) const override
  {
    if (!std::isfinite(latitude) || !std::isfinite(longitude))
      throw std::invalid_argument(
        "Star-X latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Star-X latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Star-X longitude must be in [-180, 180] degrees");

    const auto projected = star_x_detail::project_to_normalized_map(
      latitude, longitude, layout).point;
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

inline starxproj
make_star_x_projection(const frame& map_frame, string raster_name = {},
                       const star_x_layout layout = {})
{
  return starxproj(map_frame, std::move(raster_name), layout);
}

} // namespace a60::carto

#endif
