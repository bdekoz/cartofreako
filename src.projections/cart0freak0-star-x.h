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
#include <array>
#include <cmath>
#include <limits>
#include <numbers>
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

/**
   Page-centered enlargement applied after the two face groups have been
   assembled. A factor of one preserves the assembled carrier; the historic
   Star-X presentation enlarges that carrier to 120 percent.
*/
inline constexpr double star_x_default_enlargement_factor = 1.2;

/// Outer radius of the eight-point North-pole star as a fraction of height.
inline constexpr double star_x_polar_star_outer_radius_ratio = 1.25 / 44.0;
/// Inner radius of the North-pole star relative to its outer radius.
inline constexpr double star_x_polar_star_inner_radius_factor = 0.4;

/// Fixed geographic boundary of the unified Antarctic quadrant cut.
inline constexpr double star_x_antarctic_cutoff_latitude_degrees = -60;
/// Geographic-bearing rotation of the unified Antarctic cap.
inline constexpr double star_x_antarctic_bearing_offset_degrees = 0;
/// Bottom clearance retained by the cap boundary in every Star-X frame.
inline constexpr double star_x_antarctic_bottom_clearance_ratio = 0.25 / 44.0;
/// Quarter-degree samples used to register the rendered cap boundary.
inline constexpr std::size_t star_x_antarctic_boundary_sample_count = 1440;

/// Configurable placement and final scale of the Star-X arrangement.
struct star_x_layout
{
  /// Signed group separation as a fraction of the complete frame height.
  double group_gap_ratio = star_x_default_group_gap_ratio;
  /// Page-centered scale applied after group assembly.
  double enlargement_factor = star_x_default_enlargement_factor;
};

/// Validate a Star-X layout configuration.
/// @param value Layout to validate and return.
/// @return The validated layout.
/// @throws std::invalid_argument if either setting is non-finite or unsupported.
inline star_x_layout
validate_star_x_layout(const star_x_layout value)
{
  if (!std::isfinite(value.group_gap_ratio)
      || value.group_gap_ratio < star_x_minimum_group_gap_ratio
      || value.group_gap_ratio > star_x_maximum_group_gap_ratio)
    throw std::invalid_argument(
      "Star-X group gap ratio must be finite and within [-0.5, 0]");
  if (!std::isfinite(value.enlargement_factor)
      || value.enlargement_factor <= 0)
    throw std::invalid_argument(
      "Star-X enlargement factor must be finite and positive");
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

/// The four practical Star-X page quadrants in geographic sector order.
enum class quadrant : std::size_t
{
  lower_left = 0, ///< Pacific sector, source Q1.
  lower_right = 1, ///< Americas sector, source Q2.
  upper_right = 2, ///< Europe/Africa sector, rotated source Q3.
  upper_left = 3, ///< Asia/Australia sector, rotated source Q4.
};

/// Public longitudes through the centers of the four Star-X quadrants.
inline constexpr std::array<double, 4> quadrant_center_longitudes {
  -156, -66, 24, 114,
};

/// Normalized Star-X point paired with its selected face group.
struct assembled_point
{
  point_2d point; ///< Point in the complete normalized Star-X carrier.
  face_group group; ///< Four-face group containing the point.
};

/// Scale a normalized carrier point about the center of its page.
/// @param value Point in normalized page coordinates.
/// @param factor Positive enlargement factor.
/// @return Page-centered scaled point.
inline point_2d
enlarge_about_page_center(const point_2d value, const double factor)
{
  return {0.5 + factor * (value.x - 0.5),
          0.5 + factor * (value.y - 0.5)};
}

/**
   Assemble a centered Cahill-Keyes native point into the Star-X carrier.

   The native projector below uses scaffold altitude 1/4. Its complete
   M-layout is therefore 1 unit wide by 1/2 unit high. Each four-face
   group is a 1/2-by-1/2 square. Group one (negative native x) is placed
   below the frame midpoint. Group two is rotated 180 degrees and placed
   above it. A signed carrier gap separates or overlaps the two groups.
   The assembled point is then enlarged about the center of the complete
   page; results are normalized to the full 17:22 frame.

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
  const point_2d assembled {
    x_in_height_units / star_x_width_to_height_ratio, y
  };
  return {enlarge_about_page_center(assembled, layout.enlargement_factor),
          second_group ? face_group::two : face_group::one};
}

/// Project a geographic coordinate into the normalized Star-X carrier.
/// @param latitude Geographic latitude in degrees.
/// @param longitude Geographic longitude in degrees.
/// @param layout Valid arrangement configuration.
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

/// Select the Star-X quadrant containing a public geographic longitude.
/// @param longitude Finite longitude in `[-180, 180]`.
/// @return The quadrant selected by the registered Cahill-Keyes sector cuts.
inline quadrant
quadrant_for_longitude(const double longitude)
{
  if (!std::isfinite(longitude) || longitude < -180 || longitude > 180)
    throw std::invalid_argument(
      "Star-X quadrant longitude must be finite and within [-180, 180]");
  return static_cast<quadrant>(
    cahill_keyes_registered_octant(longitude) - 1);
}

/// Return the center longitude of a Star-X quadrant.
/// @param value Practical page quadrant.
/// @return Public geographic longitude through its center.
inline double
quadrant_center_longitude(const quadrant value)
{
  return quadrant_center_longitudes[static_cast<std::size_t>(value)];
}

/// Project directly into a concrete Star-X frame without constructing an API
/// adapter. This is used by the layer-aware polar-cap compositor.
/// @param latitude Geographic latitude.
/// @param longitude Geographic longitude.
/// @param map_frame Complete Star-X output frame.
/// @param layout Star-X carrier configuration.
/// @return Point in concrete output-frame coordinates.
inline point_2d
project_to_frame(const double latitude, const double longitude,
                 const frame& map_frame,
                 const star_x_layout layout = {})
{
  const point_2d normalized
    = project_to_normalized_map(latitude, longitude, layout).point;
  return {normalized.x * map_frame.width(),
          normalized.y * map_frame.height()};
}

/// Return the outer South-Pole tip for one practical page quadrant.
/// @param value Practical page quadrant.
/// @param map_frame Complete Star-X output frame.
/// @param layout Star-X carrier configuration.
/// @return Projected South-Pole tip in output-frame coordinates.
inline point_2d
antarctic_source_tip(const quadrant value, const frame& map_frame,
                     const star_x_layout layout = {})
{
  return project_to_frame(
    -90, quadrant_center_longitude(value), map_frame, layout);
}

/// Measure a point in one Antarctic fragment from its outer quadrant tip.
/// @param latitude Geographic latitude.
/// @param longitude Geographic longitude.
/// @param map_frame Complete Star-X output frame.
/// @param layout Star-X carrier configuration.
/// @return Euclidean source-frame distance from the selected South-Pole tip.
inline double
antarctic_source_radius(const double latitude, const double longitude,
                         const frame& map_frame,
                         const star_x_layout layout = {})
{
  const point_2d point
    = project_to_frame(latitude, longitude, map_frame, layout);
  const point_2d tip = antarctic_source_tip(
    quadrant_for_longitude(longitude), map_frame, layout);
  return std::hypot(point.x - tip.x, point.y - tip.y);
}

/** Reassemble one Star-X Antarctic fragment around a common local pole.

    Cahill-Keyes octant edges bend outside its small polar construction zone,
    so one constant rigid rotation per quadrant cannot make the complete cap
    seamless. This mapping retains each point's exact distance from its
    original outer South-Pole tip and normalizes only its geographic bearing.
    Neighboring quadrant edges therefore coincide at every latitude while
    the cap keeps the source projection's radial scale.

    @param latitude Geographic latitude.
    @param longitude Geographic longitude in `[-180, 180]`.
    @param map_frame Complete Star-X output frame.
    @param bearing_offset Rotation of the assembled cap in degrees.
    @param layout Star-X carrier configuration.
    @return Point relative to the common South Pole.
*/
inline point_2d
project_antarctic_fragment_local(
  const double latitude, const double longitude, const frame& map_frame,
  const double bearing_offset = 0, const star_x_layout layout = {})
{
  const double radius
    = antarctic_source_radius(latitude, longitude, map_frame, layout);
  const double radians = (longitude + bearing_offset)
                         * std::numbers::pi_v<double> / 180;
  return {radius * std::sin(radians), -radius * std::cos(radians)};
}

/// Reassemble one fragment point and translate it to a shared page pole.
/// @param latitude Geographic latitude.
/// @param longitude Geographic longitude.
/// @param map_frame Complete Star-X output frame.
/// @param target_pole Destination South Pole in output-frame coordinates.
/// @param bearing_offset Rotation of the assembled cap in degrees.
/// @param layout Star-X carrier configuration.
/// @return Reassembled point in output-frame coordinates.
inline point_2d
project_antarctic_fragment(
  const double latitude, const double longitude, const frame& map_frame,
  const point_2d target_pole, const double bearing_offset = 0,
  const star_x_layout layout = {})
{
  const point_2d local = project_antarctic_fragment_local(
    latitude, longitude, map_frame, bearing_offset, layout);
  return {target_pole.x + local.x, target_pole.y + local.y};
}

/** Pure projection registration for the fixed-60-degree-South cap.

    The cap boundary and placement are derived only from the Star-X frame,
    layout, and projected geographic boundary. No coastline, land mask, or
    other thematic dataset participates. The bottommost sampled boundary
    point is placed one quarter carrier unit above the bottom of the canonical
    34-by-44 frame (one quarter inch in the generated SVG), with that
    clearance scaled proportionally for every valid frame.
*/
struct antarctic_cap_registration
{
  double cutoff_latitude; ///< Fixed geographic cutoff in degrees.
  double bearing_offset; ///< Geographic-bearing rotation in degrees.
  double maximum_boundary_radius; ///< Largest source radius at the cutoff.
  double boundary_local_bottom; ///< Largest local y value on the boundary.
  double bottom_clearance; ///< Required visible clearance in frame units.
  point_2d target_pole; ///< Registered common South Pole in frame units.
};

/// Register the unified Antarctic cap without consulting source data.
/// @param map_frame Complete ratio-correct Star-X output frame.
/// @param variable_layout Star-X carrier configuration.
/// @return Fixed-cut cap registration and its visible bottom clearance.
inline antarctic_cap_registration
make_antarctic_cap_registration(
  const frame& map_frame, const star_x_layout variable_layout = {})
{
  if (!is_star_x_frame(map_frame))
    throw std::invalid_argument(
      "Star-X Antarctic cap requires a valid 17:22 frame");
  const star_x_layout layout = validate_star_x_layout(variable_layout);
  double maximum_radius = 0;
  double local_bottom = -std::numeric_limits<double>::infinity();
  for (std::size_t sample = 0;
       sample <= star_x_antarctic_boundary_sample_count; ++sample)
    {
      const double longitude
        = -180 + 360 * static_cast<double>(sample)
                   / star_x_antarctic_boundary_sample_count;
      const point_2d local = project_antarctic_fragment_local(
        star_x_antarctic_cutoff_latitude_degrees, longitude, map_frame,
        star_x_antarctic_bearing_offset_degrees, layout);
      maximum_radius = std::max(
        maximum_radius, std::hypot(local.x, local.y));
      local_bottom = std::max(local_bottom, local.y);
    }
  if (!std::isfinite(maximum_radius) || maximum_radius <= 0
      || !std::isfinite(local_bottom))
    throw std::logic_error(
      "Star-X 60-degree-South cap has no finite boundary");

  const double clearance
    = map_frame.height() * star_x_antarctic_bottom_clearance_ratio;
  const point_2d target {
    map_frame.width() / 2,
    map_frame.height() - clearance - local_bottom,
  };
  if (target.x - maximum_radius < 0
      || target.x + maximum_radius > map_frame.width()
      || target.y - maximum_radius < 0)
    throw std::logic_error(
      "Star-X Antarctic cap registration does not fit its frame");
  return {
    star_x_antarctic_cutoff_latitude_degrees,
    star_x_antarctic_bearing_offset_degrees,
    maximum_radius,
    local_bottom,
    clearance,
    target,
  };
}

/**
   Construct the sixteen alternating vertices of an eight-point polar star.

   @param map_frame Star-X output frame.
   @param outer_radius_ratio Outer radius as a fraction of frame height.
   @param inner_radius_factor Inner radius relative to the outer radius.
   @return Vertices in clockwise screen order, beginning at the upper tip.
*/
inline std::array<point_2d, 16>
make_north_pole_star(
  const frame& map_frame,
  const double outer_radius_ratio = star_x_polar_star_outer_radius_ratio,
  const double inner_radius_factor = star_x_polar_star_inner_radius_factor)
{
  std::array<point_2d, 16> vertices {};
  const point_2d center {map_frame.width() / 2, map_frame.height() / 2};
  const double outer_radius = map_frame.height() * outer_radius_ratio;
  for (std::size_t i = 0; i < vertices.size(); ++i)
    {
      const double radius = i % 2 == 0
                              ? outer_radius
                              : outer_radius * inner_radius_factor;
      const double angle
        = -std::numbers::pi_v<double> / 2
          + static_cast<double>(i) * std::numbers::pi_v<double> / 8;
      vertices[i] = {center.x + radius * std::cos(angle),
                     center.y + radius * std::sin(angle)};
    }
  return vertices;
}

} // namespace star_x_detail

/// Construct generic projection state from a variable-size 17:22 frame.
/// Only frame_area is retained; map placement remains cartography's job.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @param variable_layout Arrangement to validate and retain.
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
   rotates the right group 180 degrees into the upper half, and uniformly
   enlarges the complete result about the page center.
*/
struct starxproj : public projection_base, public projection_api
{
private:
  star_x_layout layout_; ///< Validated placement and scale configuration.

public:
  /// Construct from generic projection state and a layout.
  /// @param value Generic projection state with a ratio-correct frame.
  /// @param variable_layout Arrangement configuration.
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
  /// @param variable_layout Arrangement configuration.
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

  /// Return the configured page-centered enlargement.
  /// @return Scale applied after face-group assembly.
  double
  enlargement_factor() const noexcept
  { return layout_.enlargement_factor; }

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
/// @param layout Arrangement configuration.
/// @return Configured Star-X projection.
inline starxproj
make_star_x_projection(const frame& map_frame, string raster_name = {},
                       const star_x_layout layout = {})
{
  return starxproj(map_frame, std::move(raster_name), layout);
}

} // namespace a60::carto

#endif
