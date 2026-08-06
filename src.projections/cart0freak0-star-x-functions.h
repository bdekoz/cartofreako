// alpha60 Star-X projected-path utilities -*- mode: C++ -*-

// alpha60
// cartography projection path functions

// Copyright (c) 2026 Benjamin De Kosnik <b.dekosnik@gmail.com>

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
 * @file cart0freak0-star-x-functions.h
 * @brief Geographic seam topology and paired-edge routing for Star-X paths.
 */

#ifndef cart0freak0_STAR_X_FUNCTIONS_H
#define cart0freak0_STAR_X_FUNCTIONS_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <tuple>

#include "cart0freak0-star-x.h"

namespace a60::carto::star_x_path_detail {

/// Geographic coordinate used while locating a Star-X path transition.
struct geographic_coordinate
{
  double latitude; ///< Latitude in degrees.
  double longitude; ///< Longitude in degrees.
};

/// Topological disposition of a boundary in the assembled Star-X net.
enum class edge_kind
{
  retained_hinge, ///< Neighboring cells retain one coincident planar edge.
  intra_group_fold, ///< Cut between face pairs in one rigid square group.
  inter_group_fold ///< Cut between the lower and rotated upper groups.
};

/// One-sided limits where a geographic path leaves and re-enters a cut net.
struct edge_transition
{
  point_2t exit; ///< Limiting point on the source cell's boundary copy.
  point_2t entry; ///< Limiting point on the destination boundary copy.
  geographic_coordinate geographic_entry; ///< First point in the next cell.
  edge_kind kind; ///< Hinge or one of the two Star-X fold classes.

  /// Return whether this transition starts a new projected subpath.
  /// @return `true` for either fold class; `false` for a retained hinge.
  bool
  is_fold() const noexcept
  { return kind != edge_kind::retained_hinge; }
};

/// Return the registered Star-X path cell for a geographic coordinate.
/// Cells 0-3 are northern quadrants and cells 4-7 their southern partners.
/// @param point Finite geographic coordinate in the public Star-X domain.
/// @return Registered cell number in `[0, 7]`.
/// @throws std::invalid_argument if the coordinate is outside the domain.
inline std::uint8_t
path_cell(const geographic_coordinate point)
{
  if (!std::isfinite(point.latitude) || point.latitude < -90
      || point.latitude > 90)
    throw std::invalid_argument(
      "Star-X path latitude must be finite and within [-90, 90]");
  if (!std::isfinite(point.longitude) || point.longitude < -180
      || point.longitude > 180)
    throw std::invalid_argument(
      "Star-X path longitude must be finite and within [-180, 180]");

  const int octant = cahill_keyes_registered_octant(point.longitude);
  return static_cast<std::uint8_t>(
    octant - 1 + (point.latitude < 0 ? 4 : 0));
}

/// Return the rigid square group containing a registered path cell.
/// @param cell Registered Star-X cell in `[0, 7]`.
/// @return Lower group one or rotated upper group two.
/// @throws std::invalid_argument if the cell is outside `[0, 7]`.
inline star_x_detail::face_group
face_group_for_cell(const std::uint8_t cell)
{
  if (cell >= 8)
    throw std::invalid_argument("Star-X path cell must be within [0, 7]");
  return cell % 4 < 2
           ? star_x_detail::face_group::one
           : star_x_detail::face_group::two;
}

/// Interpolate a geographic source edge along the short longitude arc.
/// @param left First endpoint.
/// @param right Second endpoint.
/// @param fraction Interpolation parameter, normally in `[0, 1]`.
/// @return Interpolated coordinate canonicalized into `[-180, 180]`.
inline geographic_coordinate
interpolate(const geographic_coordinate left,
            const geographic_coordinate right, const double fraction)
{
  double right_longitude = right.longitude;
  if (right_longitude - left.longitude > 180)
    right_longitude -= 360;
  else if (right_longitude - left.longitude < -180)
    right_longitude += 360;
  double longitude
    = left.longitude + fraction * (right_longitude - left.longitude);
  if (longitude > 180)
    longitude -= 360;
  else if (longitude < -180)
    longitude += 360;
  return {
    left.latitude + fraction * (right.latitude - left.latitude),
    longitude,
  };
}

/// Project a geographic coordinate through the configured Star-X transform.
/// @param projection Configured Star-X point projection.
/// @param point Geographic coordinate to project.
/// @return Concrete output-frame coordinate.
inline point_2t
project(const starxproj& projection, const geographic_coordinate point)
{
  return projection.meridians_to_point_2d(
    point.latitude, point.longitude);
}

/// Euclidean separation between two projected points.
/// @param left First projected point.
/// @param right Second projected point.
/// @return Euclidean distance in output-frame units.
inline double
point_distance(const point_2t left, const point_2t right)
{
  return std::hypot(std::get<0>(right) - std::get<0>(left),
                    std::get<1>(right) - std::get<1>(left));
}

/// Classify a one-sided cell transition in the assembled Star-X topology.
/// @param projection Configured Star-X projection, used for scale tolerance.
/// @param left_cell Cell containing the outgoing one-sided limit.
/// @param right_cell Cell containing the incoming one-sided limit.
/// @param exit Projected outgoing limit.
/// @param entry Projected incoming limit.
/// @return Retained hinge, intra-group fold, or inter-group fold.
/// @throws std::invalid_argument if either cell is invalid or they are equal.
inline edge_kind
classify_edge(const starxproj& projection, const std::uint8_t left_cell,
              const std::uint8_t right_cell, const point_2t exit,
              const point_2t entry)
{
  if (left_cell >= 8 || right_cell >= 8 || left_cell == right_cell)
    throw std::invalid_argument(
      "Star-X edge classification requires two distinct valid cells");

  const std::uint8_t left_sector = left_cell % 4;
  const std::uint8_t right_sector = right_cell % 4;
  if (left_sector != right_sector
      && face_group_for_cell(left_cell) != face_group_for_cell(right_cell))
    return edge_kind::inter_group_fold;

  const double scale = std::max({
    1.0,
    projection.pframe.width(), projection.pframe.height(),
    std::abs(std::get<0>(exit)), std::abs(std::get<1>(exit)),
    std::abs(std::get<0>(entry)), std::abs(std::get<1>(entry)),
  });
  const double tolerance
    = 256 * std::numeric_limits<double>::epsilon() * scale;
  if (point_distance(exit, entry) <= tolerance)
    return edge_kind::retained_hinge;
  return edge_kind::intra_group_fold;
}

/**
   Locate the first topological transition along one geographic source edge.

   For a coarse edge spanning at least one 90-degree registered sector, the
   search first samples finely enough to isolate its first transition even
   when later transitions also lie on the edge. It then bisects that bracket
   in geographic space and projects its one-sided limits. Inter-group cuts are
   always folds. Within a group, coincident limits are retained hinges and
   separated limits are paired fold edges.

   Longitude interpolation follows the short arc across `+180/-180`. A path
   that deliberately takes the long way around the globe must provide an
   intermediate geographic waypoint.

   @param projection Configured Star-X point projection.
   @param source_left First geographic endpoint.
   @param source_right Second geographic endpoint.
   @return First hinge/fold transition, or no value for one continuous cell.
*/
inline std::optional<edge_transition>
first_edge_transition(const starxproj& projection,
                      const geographic_coordinate source_left,
                      const geographic_coordinate source_right)
{
  const auto locate_transition
    = [&projection](geographic_coordinate limit_left,
                    geographic_coordinate limit_right,
                    const std::uint8_t left_cell)
      -> edge_transition
    {
      for (int iteration = 0; iteration != 56; ++iteration)
        {
          const geographic_coordinate middle
            = interpolate(limit_left, limit_right, 0.5);
          if (path_cell(middle) == left_cell)
            limit_left = middle;
          else
            limit_right = middle;
        }

      const std::uint8_t next_cell = path_cell(limit_right);
      if (next_cell == left_cell)
        throw std::logic_error(
          "Star-X path transition did not enter a new cell");
      const point_2t exit = project(projection, limit_left);
      const point_2t entry = project(projection, limit_right);
      return edge_transition {
        exit,
        entry,
        limit_right,
        classify_edge(projection, left_cell, next_cell, exit, entry),
      };
    };

  const std::uint8_t source_left_cell = path_cell(source_left);
  const std::uint8_t source_right_cell = path_cell(source_right);
  double longitude_span = source_right.longitude - source_left.longitude;
  if (longitude_span > 180)
    longitude_span -= 360;
  else if (longitude_span < -180)
    longitude_span += 360;
  // A linear edge spanning less than one registered sector cannot leave and
  // later return to its starting cell. This is the normal densified-generator
  // case and avoids scanning every continuous source edge.
  if (std::abs(longitude_span) < 90)
    {
      if (source_left_cell == source_right_cell)
        return std::nullopt;
      return locate_transition(
        source_left, source_right, source_left_cell);
    }

  constexpr std::size_t scan_steps = 128;
  geographic_coordinate bracket_left = source_left;
  std::uint8_t bracket_cell = source_left_cell;

  for (std::size_t step = 1; step <= scan_steps; ++step)
    {
      const geographic_coordinate sample
        = step == scan_steps
            ? source_right
            : interpolate(source_left, source_right,
                          static_cast<double>(step) / scan_steps);
      const std::uint8_t sample_cell = path_cell(sample);
      if (sample_cell == bracket_cell)
        {
          bracket_left = sample;
          continue;
        }
      return locate_transition(bracket_left, sample, bracket_cell);
    }

  return std::nullopt;
}

} // namespace a60::carto::star_x_path_detail

#endif
