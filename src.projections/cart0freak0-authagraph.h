// alpha60 cartography projection AuthaGraph -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2026, Benjamin De Kosnik <b.dekosnik@gmail.com>

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
 * @file cart0freak0-authagraph.h
 * @brief AuthaGraph forward projection, tetrahedral geometry, and presets.
 */

#ifndef cart0freak0_AUTHAGRAPH_H
#define cart0freak0_AUTHAGRAPH_H 1

#include <algorithm>
#include <array>
#include <cstddef>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace a60::carto {

/// Width of the checked-in A3 AuthaGraph source plate, in PDF points.
inline constexpr double authagraph_page_width = 1190.55;
/// Height of the checked-in A3 AuthaGraph source plate, in PDF points.
inline constexpr double authagraph_page_height = 841.89;
/// Horizontal offset of the map viewport within the A3 source plate.
inline constexpr double authagraph_map_left = 107.101118;
/// Vertical offset of the map viewport within the A3 source plate.
inline constexpr double authagraph_map_top = 199.632551;
/// Height of the map viewport measured from the A3 source plate.
inline constexpr double authagraph_map_height = 422.690833;

/// Required width-to-height ratio, `4 / sqrt(3)`, of the rectangular net.
inline constexpr double authagraph_width_to_height_ratio
  = 2.309401076758503058036595122007829823;
/// Width of the map viewport measured from its height and required ratio.
inline constexpr double authagraph_map_width
  = authagraph_width_to_height_ratio * authagraph_map_height;

/// True when a frame has finite, positive dimensions in the required
/// 4:sqrt(3) AuthaGraph aspect ratio. The tolerance admits floating-point
/// roundoff, not approximate aspect ratios.
/// @param candidate Frame to validate.
/// @return `true` when the dimensions are finite, positive, and ratio-correct.
inline bool
is_authagraph_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = authagraph_width_to_height_ratio * height;
  if (!std::isfinite(expected_width))
    return false;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

/// Validate generic projection state for use by AuthaGraph.
/// @param value Projection state to validate and return.
/// @return The validated projection state.
/// @throws std::invalid_argument if the frame is not a valid AuthaGraph frame.
inline projection_base
validate_authagraph_projection_base(projection_base value)
{
  if (!is_authagraph_frame(value.pframe))
    throw std::invalid_argument(
      "AuthaGraph projection frame must have finite, positive dimensions "
      "with a 4:sqrt(3) width-to-height ratio");
  return value;
}

/// Internal geometry used to evaluate and unfold the AuthaGraph tetrahedron.
namespace authagraph_detail {

/// Pi in radians.
inline constexpr double pi = 3.141592653589793238462643383279502884;
/// Square root of two used by the published analytic formula.
inline constexpr double sqrt_two = 1.414213562373095048801688724209698079;
/// Square root of three used by tetrahedral face geometry.
inline constexpr double sqrt_three = 1.732050807568877293527446341505872367;
/// Scale of a unit-vector tetrahedron edge in the unfolded net.
inline constexpr double tetrahedron_scale = 0.816496580927726032732428024901963798;
/// Width of the complete unnormalized tetrahedral net.
inline constexpr double unfolded_width = 4 * tetrahedron_scale;
/// Height of the complete unnormalized tetrahedral net.
inline constexpr double unfolded_height = sqrt_two;

// Register the cyclic tetrahedron net with the map rectangle in the source
// PDF.  Its four singular vertices are separated by one quarter-map width.
inline constexpr double horizontal_shift = -0.08797138953590078; ///< Source-plate horizontal registration.

/// Cartesian point in the unfolded two-dimensional construction.
struct point_2d
{
  double x; ///< Horizontal coordinate.
  double y; ///< Vertical coordinate.
};

/// Cartesian vector on or near the unit sphere.
struct vector_3d
{
  double x; ///< First Cartesian component.
  double y; ///< Second Cartesian component.
  double z; ///< Third Cartesian component.
};

/// Convert angular degrees to radians.
/// @param value Angle in degrees.
/// @return The angle in radians.
inline constexpr double
degrees_to_radians(const double value)
{ return value * pi / 180; }

/// Convert a signed degrees-minutes-seconds angle to radians.
/// @param degrees Whole-degree component.
/// @param minutes Arc-minute component.
/// @param seconds Arc-second component.
/// @param sign Direction multiplier, normally `1` or `-1`.
/// @return The signed angle in radians.
inline constexpr double
dms_to_radians(const double degrees, const double minutes,
               const double seconds, const double sign)
{
  return sign * degrees_to_radians(
    degrees + (minutes + seconds / 60) / 60);
}

/// Convert spherical longitude and latitude to a unit Cartesian vector.
/// @param longitude Longitude in radians.
/// @param latitude Latitude in radians.
/// @return Unit vector at the requested spherical coordinate.
inline vector_3d
longitude_latitude_to_vector(const double longitude, const double latitude)
{
  const double latitude_cosine = std::cos(latitude);
  return {latitude_cosine * std::cos(longitude),
          latitude_cosine * std::sin(longitude),
          std::sin(latitude)};
}

/// Compute the dot product of two three-dimensional vectors.
/// @param left Left operand.
/// @param right Right operand.
/// @return Scalar dot product.
inline constexpr double
dot(const vector_3d& left, const vector_3d& right)
{ return left.x * right.x + left.y * right.y + left.z * right.z; }

/// Compute the right-handed cross product of two vectors.
/// @param left Left operand.
/// @param right Right operand.
/// @return Vector perpendicular to both operands.
inline constexpr vector_3d
cross(const vector_3d& left, const vector_3d& right)
{
  return {left.y * right.z - left.z * right.y,
          left.z * right.x - left.x * right.z,
          left.x * right.y - left.y * right.x};
}

/// Construct a unit tangent at a spherical pole toward another meridian.
/// @param pole Unit vector defining the local north pole.
/// @param meridian Unit vector selecting the local prime-meridian direction.
/// @return Normalized tangent vector in the pole's tangent plane.
inline vector_3d
unit_tangent_toward(const vector_3d& pole, const vector_3d& meridian)
{
  const double parallel = dot(pole, meridian);
  vector_3d tangent {meridian.x - pole.x * parallel,
                     meridian.y - pole.y * parallel,
                     meridian.z - pole.z * parallel};
  const double magnitude = std::sqrt(dot(tangent, tangent));
  tangent.x /= magnitude;
  tangent.y /= magnitude;
  tangent.z /= magnitude;
  return tangent;
}

/// Return the four published geographic tetrahedron vertices.
/// @return Stable vertex array whose order controls net assembly.
inline const std::array<vector_3d, 4>&
tetrahedron_vertices()
{
  // Vertex placement published with the AuthaGraph construction.  The array
  // order also defines how the 24 projected triangles are assembled.
  static const std::array<vector_3d, 4> vertices {
    longitude_latitude_to_vector(
      dms_to_radians(149, 27, 3.56868, 1),
      dms_to_radians(76, 52, 51.82608, 1)),
    longitude_latitude_to_vector(
      dms_to_radians(97, 21, 25.2126, 1),
      dms_to_radians(27, 57, 9.99792, -1)),
    longitude_latitude_to_vector(
      dms_to_radians(133, 16, 57.93168, -1),
      dms_to_radians(22, 55, 41.65104, -1)),
    longitude_latitude_to_vector(
      dms_to_radians(18, 51, 8.037, -1),
      dms_to_radians(6, 38, 13.37028, -1)),
  };
  return vertices;
}

/// Express a unit vector in a pole-centered longitude/latitude system.
/// @param value Geographic unit vector to transform.
/// @param pole Unit vector serving as the local north pole.
/// @param prime_meridian Unit vector selecting local zero longitude.
/// @return Local longitude in `x` and latitude in `y`, both in radians.
inline point_2d
local_longitude_latitude(const vector_3d& value,
                         const vector_3d& pole,
                         const vector_3d& prime_meridian)
{
  const vector_3d tangent = unit_tangent_toward(pole, prime_meridian);
  const vector_3d perpendicular = cross(tangent, value);
  const double sine_longitude = dot(pole, perpendicular);
  const double cosine_longitude = dot(tangent, value);
  const double sine_latitude = std::clamp(dot(pole, value), -1.0, 1.0);
  return {std::atan2(sine_longitude, cosine_longitude),
          std::asin(sine_latitude)};
}

/// Compute a non-negative floating-point remainder.
/// @param value Dividend.
/// @param modulus Positive modulus.
/// @return A value in `[0, modulus)`.
inline double
positive_modulo(const double value, const double modulus)
{
  const double remainder = std::fmod(value, modulus);
  return remainder < 0 ? remainder + modulus : remainder;
}

/// A point projected into one of six sectors around a tetrahedron vertex.
struct triangle_projection
{
  point_2d point; ///< Analytic point in the canonical planar triangle.
  int sector; ///< Zero-based 60-degree sector around the selected vertex.
};

/// Project pole-centered spherical coordinates into a canonical triangle.
/// @param local Local longitude and latitude in radians.
/// @return Planar coordinates and the selected 60-degree sector.
inline triangle_projection
project_spherical_triangle(const point_2d& local)
{
  // Narukawa, "Formulation of AuthaGraph Map Projection and an Evaluation
  // of its Distortion", Map 60(1), 2022, equations 2.22 and 2.23.
  // https://doi.org/10.11212/jjca.60.1_1
  constexpr double sector_angle = pi / 3;
  int sector = static_cast<int>(
    std::floor((local.x + sector_angle) / sector_angle));
  sector %= 6;
  if (sector < 0)
    sector += 6;

  const double longitude = positive_modulo(
    local.x + sector_angle, 2 * sector_angle) - sector_angle;
  const double latitude_cosine = std::cos(local.y);
  const double c = (2 + std::cos(longitude)) * latitude_cosine
                   / (sqrt_two * latitude_cosine + std::sin(local.y));
  const double equal_area_angle = longitude - std::asin(std::clamp(
    std::sin(longitude) / sqrt_three, -1.0, 1.0));

  return {{2 / pi * c * equal_area_angle,
           (sqrt_two - c) / sqrt_three},
          sector};
}

/// Select a tetrahedron vertex and assemble its projected sector into the net.
/// @param latitude Geographic latitude in radians.
/// @param longitude Geographic longitude in radians.
/// @return Point in the unnormalized cyclic tetrahedral net.
inline point_2d
project_to_unfolded_tetrahedron(const double latitude,
                                const double longitude)
{
  const vector_3d geographic = longitude_latitude_to_vector(
    longitude, latitude);
  const auto& vertices = tetrahedron_vertices();

  std::size_t closest = 0;
  double closest_dot = dot(geographic, vertices.front());
  for (std::size_t index = 1; index < vertices.size(); ++index)
    {
      const double candidate = dot(geographic, vertices[index]);
      if (candidate > closest_dot)
        {
          closest = index;
          closest_dot = candidate;
        }
    }

  const std::size_t next = (closest + 1) % vertices.size();
  const point_2d local = local_longitude_latitude(
    geographic, vertices[closest], vertices[next]);
  const triangle_projection triangle = project_spherical_triangle(local);
  const std::size_t number = closest * 6
                             + static_cast<std::size_t>(triangle.sector);

  // Coefficients of v0=(1,0) and v1=(1/2,sqrt(3)/2) for the 24 triangle
  // origins in the rectangular tetrahedron net.
  static constexpr std::array<std::array<int, 2>, 24> origins {{
    {{1, 1}}, {{1, 1}}, {{2, 1}}, {{2, 1}}, {{2, 2}}, {{0, 2}},
    {{0, 0}}, {{2, 0}}, {{1, 1}}, {{1, 1}}, {{0, 1}}, {{0, 1}},
    {{3, 1}}, {{3, 1}}, {{2, 1}}, {{2, 1}}, {{2, 0}}, {{4, 0}},
    {{0, 2}}, {{2, 2}}, {{3, 1}}, {{3, 1}}, {{0, 1}}, {{0, 1}},
  }};

  // Rotation angles in sixths of pi.
  static constexpr std::array<int, 24> rotation_sixths {{
    -1, -1, 1, 1, 3, -3,
    -3, 3, 5, 5, -5, -5,
    5, 5, -5, -5, -3, 3,
    3, -3, -1, -1, 1, 1,
  }};

  const double origin_x = tetrahedron_scale
                          * (origins[number][0] + origins[number][1] / 2.0);
  const double origin_y = tetrahedron_scale * origins[number][1]
                          * sqrt_three / 2;
  const double angle = rotation_sixths[number] * pi / 6;
  const double cosine = std::cos(angle);
  const double sine = std::sin(angle);

  return {cosine * triangle.point.x - sine * triangle.point.y + origin_x,
          sine * triangle.point.x + cosine * triangle.point.y + origin_y};
}

/// Project geographic coordinates into the normalized AuthaGraph rectangle.
/// @param latitude Geographic latitude in degrees.
/// @param longitude Geographic longitude in degrees.
/// @return Screen-oriented point whose coordinates nominally lie in `[0, 1]`.
inline point_2d
project_to_normalized_map(const double latitude, const double longitude)
{
  const point_2d unfolded = project_to_unfolded_tetrahedron(
    degrees_to_radians(latitude), degrees_to_radians(longitude));
  const double normalized_x = positive_modulo(
    unfolded.x / unfolded_width + horizontal_shift, 1);
  const double normalized_y = std::clamp(
    unfolded.y / unfolded_height, 0.0, 1.0);
  return {normalized_x, 1 - normalized_y};
}

} // namespace authagraph_detail

/// Construct generic projection state from a variable-size AuthaGraph frame.
/// The returned origin is the projected geographic coordinate (0,0).
/// @param map_frame Valid 4:sqrt(3) output frame.
/// @param raster_name Optional registered raster filename.
/// @return Validated generic projection state with its geographic origin set.
inline projection_base
make_authagraph_projection_base(const frame& map_frame, string raster_name)
{
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_authagraph_projection_base(
    {projection_frame, 0, 0, authagraph, std::move(raster_name)});
  const auto zero = authagraph_detail::project_to_normalized_map(0, 0);
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/// Validate a map viewport embedded in a larger projection frame. This is
/// used by the A3 source-plate compatibility preset; ordinary variable-size
/// projections use pframe itself as the viewport.
/// @param value Generic projection state containing the outer frame.
/// @param map_viewport Ratio-correct map rectangle inside the outer frame.
/// @return The validated generic projection state.
/// @throws std::invalid_argument if the viewport is invalid or out of bounds.
inline projection_base
validate_authagraph_layout(projection_base value, const frame& map_viewport)
{
  if (!is_authagraph_frame(map_viewport))
    throw std::invalid_argument(
      "AuthaGraph map viewport must have finite, positive dimensions with "
      "a 4:sqrt(3) width-to-height ratio");

  const double frame_width = value.pframe.width();
  const double frame_height = value.pframe.height();
  const double map_right = map_viewport.moriginx + map_viewport.width();
  const double map_bottom = map_viewport.moriginy + map_viewport.height();
  if (!std::isfinite(frame_width) || !std::isfinite(frame_height)
      || !std::isfinite(map_viewport.moriginx)
      || !std::isfinite(map_viewport.moriginy)
      || frame_width <= 0 || frame_height <= 0
      || map_viewport.moriginx < 0 || map_viewport.moriginy < 0
      || map_right > frame_width || map_bottom > frame_height)
    throw std::invalid_argument(
      "AuthaGraph map viewport must fit inside a finite, positive "
      "projection frame");
  return value;
}

/**
   Variable-size AuthaGraph projection.

   The forward transform maps the sphere to 24 triangles, unfolds the four
   tetrahedron faces into a periodic 4:sqrt(3) rectangle, then scales that
   normalized rectangle to map_frame.frame_area.

   The 2022 analytic formula approximates the earlier graphical construction
   used by assets.static/authagraph/15-SP-TESD-03-AG.pdf. The A3 compatibility preset
   uses the plate's measured map viewport so the coordinate systems align.
*/
struct agproj : public projection_base, public projection_api
{
  /// Map rectangle in projection coordinates. For an ordinary variable-size
  /// projection it is pframe.frame_area at (0,0); a source plate may embed it.
  frame map_frame;

  /// Construct from validated generic projection state.
  /// @param value State whose frame supplies the map rectangle.
  explicit agproj(const projection_base value)
  : projection_base(validate_authagraph_projection_base(value)),
    map_frame(pframe.frame_area)
  { }

  /// Construct a projection whose map occupies a viewport in a larger frame.
  /// @param value Generic state containing the outer projection frame.
  /// @param map_viewport Ratio-correct map viewport within that frame.
  agproj(const projection_base value, const frame& map_viewport)
  : projection_base(validate_authagraph_layout(value, map_viewport)),
    map_frame(map_viewport)
  { }

  /// Make a projection for any valid 4:sqrt(3) map frame. Only frame_area is
  /// used; placement in a larger cartography frame remains cartography's job.
  /// @param variable_frame Ratio-correct output frame.
  /// @param raster_name Optional registered raster filename.
  explicit agproj(const frame& variable_frame, string raster_name = {})
  : agproj(make_authagraph_projection_base(variable_frame,
                                            std::move(raster_name)))
  { }

  /// Copy an AuthaGraph projection.
  /// @param other Projection to copy.
  agproj(const agproj& other) = default;

  /// Resolve the registered raster against the runtime data directory.
  /// @param mode Raster variant requested by the common API; unused here.
  /// @return Full runtime-resource path to the registered raster.
  string
  image_filename([[maybe_unused]] const raster_mode mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  /// Project a geographic coordinate into the configured map viewport.
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
        "AuthaGraph latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "AuthaGraph latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "AuthaGraph longitude must be in [-180, 180] degrees");

    const auto projected = authagraph_detail::project_to_normalized_map(
      latitude, longitude);
    return std::make_tuple(map_frame.moriginx
                             + projected.x * map_frame.width(),
                           map_frame.moriginy
                             + projected.y * map_frame.height());
  }
};

/// Construct a variable-size AuthaGraph projection.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @return Configured AuthaGraph projection.
inline agproj
make_authagraph_projection(const frame& map_frame, string raster_name = {})
{
  return agproj(map_frame, std::move(raster_name));
}

/// A3 source-plate x coordinate of geographic `(0, 0)`.
inline constexpr double authagraph_longitude_zero_x = 120.05917135268346;
/// A3 source-plate y coordinate of geographic `(0, 0)`.
inline constexpr double authagraph_latitude_zero_y = 267.89452133439636;

/// Complete A3 source-plate frame.
inline const frame pauthagraph_a3 {
  authagraph_page_width, authagraph_page_height
};

/// AuthaGraph map viewport embedded in the A3 source plate.
inline const frame pauthagraph_a3_map {
  authagraph_map_width, authagraph_map_height,
  authagraph_map_left, authagraph_map_top
};

/// Registered projection preset for the checked-in A3 source plate.
inline const agproj ag_a3{{pauthagraph_a3,
                           authagraph_longitude_zero_x,
                           authagraph_latitude_zero_y,
                           authagraph,
                           "assets.static/authagraph/15-SP-TESD-03-AG.pdf"},
                          pauthagraph_a3_map};

} // namespace a60::carto

#endif
