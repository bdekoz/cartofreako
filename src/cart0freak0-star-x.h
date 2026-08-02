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

/**
 * @file cart0freak0-star-x.h
 * @brief Star-X arrangement of the native Cahill-Keyes octants.
 */

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
/// Default signed gap between group carriers as a fraction of frame height.
inline constexpr double star_x_default_group_gap_ratio
  = -2 * star_x_default_group_shift_ratio;
/// Smallest supported group gap ratio, representing 50-percent overlap.
inline constexpr double star_x_minimum_group_gap_ratio = -0.5;
/// Largest supported group gap ratio, with the carriers edge-to-edge.
inline constexpr double star_x_maximum_group_gap_ratio = 0;

/// Configurable placement of the two four-face Star-X groups.
struct star_x_layout
{
  /// Signed group separation as a fraction of the complete frame height.
  double group_gap_ratio = star_x_default_group_gap_ratio;
};

/// Validate a Star-X layout configuration.
/// @param value Layout to validate and return.
/// @return The validated layout.
/// @throws std::invalid_argument if the gap ratio is non-finite or unsupported.
inline star_x_layout
validate_star_x_layout(const star_x_layout value)
{
  if (!std::isfinite(value.group_gap_ratio)
      || value.group_gap_ratio < star_x_minimum_group_gap_ratio
      || value.group_gap_ratio > star_x_maximum_group_gap_ratio)
    throw std::invalid_argument(
      "Star-X group gap ratio must be finite and within [-0.5, 0]");
  return value;
}

/// True when a frame has finite, positive dimensions in the required
/// 17:22 Star-X aspect ratio. The tolerance admits floating-point
/// roundoff, not approximate aspect ratios.
/// @param candidate Frame to validate.
/// @return `true` when the dimensions are finite, positive, and ratio-correct.
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

/// Validate generic projection state for use by Star-X.
/// @param value Projection state to validate and return.
/// @return The validated projection state.
/// @throws std::invalid_argument if its frame does not have a 17:22 ratio.
inline projection_base
validate_star_x_projection_base(projection_base value)
{
  if (!is_star_x_frame(value.pframe))
    throw std::invalid_argument(
      "Star-X projection frame must have finite, positive dimensions "
      "with a 17:22 width-to-height ratio");
  return value;
}

/// Internal Cahill-Keyes-to-Star-X assembly helpers.
namespace star_x_detail {

/// Point in a normalized two-dimensional carrier.
struct point_2d
{
  double x; ///< Horizontal coordinate.
  double y; ///< Vertical coordinate.
};

/// Four-face carrier group selected by a native Cahill-Keyes point.
enum class face_group
{
  one, ///< Lower group assembled from the negative-x native half.
  two ///< Upper, rotated group assembled from the non-negative-x half.
};

/// Normalized Star-X point paired with its selected face group.
struct assembled_point
{
  point_2d point; ///< Point in the complete normalized Star-X carrier.
  face_group group; ///< Four-face group containing the point.
};

/**
   Assemble a centered Cahill-Keyes native point into the Star-X carrier.

   The native projector below uses scaffold altitude 1/4. Its complete
   M-layout is therefore 1 unit wide by 1/2 unit high. Each four-face
   group is a 1/2-by-1/2 square. Group one (negative native x) is placed
   below the frame midpoint. Group two is rotated 180 degrees and placed
   above it. A signed carrier gap separates or overlaps the two groups;
   results are normalized to the full 17:22 frame.

   @param cahill_keyes_x Native centered Cahill-Keyes x coordinate.
   @param cahill_keyes_y Native centered Cahill-Keyes y coordinate.
   @param layout Valid group-placement configuration.
   @return Normalized Star-X point and its selected face group.
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

/// Project a geographic coordinate into the normalized Star-X carrier.
/// @param latitude Geographic latitude in degrees.
/// @param longitude Geographic longitude in degrees.
/// @param layout Valid group-placement configuration.
/// @return Normalized point and selected four-face group.
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
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @param variable_layout Group placement to validate and retain.
/// @return Validated generic projection state with its origin initialized.
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
private:
  star_x_layout layout_; ///< Validated group placement used by the transform.

public:
  /// Construct from generic projection state and a layout.
  /// @param value Generic projection state with a ratio-correct frame.
  /// @param variable_layout Group placement configuration.
  explicit starxproj(const projection_base value,
                     const star_x_layout variable_layout = {})
  : projection_base(validate_star_x_projection_base(value)),
    layout_(validate_star_x_layout(variable_layout))
  {
    const auto zero
      = star_x_detail::project_to_normalized_map(0, 0, layout_).point;
    longitude_zero_x = zero.x * pframe.width();
    latitude_zero_y = zero.y * pframe.height();
  }

  /// Make a projection for any valid 17:22 frame. Frame placement offsets
  /// are deliberately discarded; the projection owns only frame_area.
  /// @param variable_frame Ratio-correct output frame.
  /// @param raster_name Optional registered raster filename.
  /// @param variable_layout Group placement configuration.
  explicit starxproj(const frame& variable_frame, string raster_name = {},
                     const star_x_layout variable_layout = {})
  : starxproj(make_star_x_projection_base(variable_frame,
                                           std::move(raster_name),
                                           variable_layout),
              variable_layout)
  { }

  /// Copy a Star-X projection.
  /// @param other Projection to copy.
  starxproj(const starxproj& other) = default;

  /// Return the configured signed carrier gap.
  /// @return Gap as a fraction of complete frame height.
  double
  group_gap_ratio() const noexcept
  { return layout_.group_gap_ratio; }

  /// Resolve the registered raster against the runtime data directory.
  /// @param mode Raster variant requested by the common API; unused here.
  /// @return Full runtime-resource path to the registered raster.
  string
  image_filename([[maybe_unused]] const raster_mode mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  /// Project a geographic coordinate into the configured Star-X frame.
  /// @param latitude Latitude in degrees, in `[-90, 90]`.
  /// @param longitude Longitude in degrees, in `[-180, 180]`.
  /// @return Output-frame coordinate in screen-axis orientation.
  /// @throws std::invalid_argument if either coordinate is non-finite or out
  /// of range.
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
      latitude, longitude, layout_).point;
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

/// Construct a variable-size Star-X projection.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @param layout Group placement configuration.
/// @return Configured Star-X projection.
inline starxproj
make_star_x_projection(const frame& map_frame, string raster_name = {},
                       const star_x_layout layout = {})
{
  return starxproj(map_frame, std::move(raster_name), layout);
}

} // namespace a60::carto

#endif
