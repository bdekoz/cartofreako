// alpha60 cartography projection Dymaxion -*- mode: C++ -*-

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

// The Fuller-oriented icosahedron, interrupted net, and Australia/Japan
// subfaces are derived from PROJ's Airocean implementation:
//
// Copyright information can be found in the PROJ source files.
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the "Software"),
// to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense,
// and/or sell copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
// DEALINGS IN THE SOFTWARE.

// The face-local transform below is an independent C++ expression of the
// equations published by Robert W. Gray in "Exact Transformation Equations
// for Fuller's World Map" (1995). Gray's separately published C program has
// additional non-commercial terms and is not incorporated into this file.

/**
 * @file a60-carto-projection-dymaxion.h
 * @brief Variable-frame Fuller-oriented Dymaxion/Airocean forward projection.
 */

#ifndef a60_CARTO_PROJECTION_DYMAXION_H
#define a60_CARTO_PROJECTION_DYMAXION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace a60::carto {

/// Width of the horizontal unfolded Fuller/Airocean net.
inline constexpr double dymaxion_source_width = 5.78304223331047;
/// Height of the horizontal unfolded Fuller/Airocean net.
inline constexpr double dymaxion_source_height = 2.7317789919300877;
/// Required width-to-height ratio of every Dymaxion projection frame.
inline constexpr double dymaxion_width_to_height_ratio
  = dymaxion_source_width / dymaxion_source_height;

/// True when a frame is finite, positive, and has the Dymaxion net ratio.
/// @param candidate Frame whose area is tested.
/// @return Whether the frame can carry the horizontal Dymaxion net.
inline bool
is_dymaxion_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = dymaxion_width_to_height_ratio * height;
  if (!std::isfinite(expected_width))
    return false;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

/// Validate generic projection state for the horizontal Dymaxion net.
/// @param value Projection state to validate and return.
/// @return Validated projection state.
/// @throws std::invalid_argument if its frame has the wrong dimensions.
inline projection_base
validate_dymaxion_projection_base(projection_base value)
{
  if (!is_dymaxion_frame(value.pframe))
    throw std::invalid_argument(
      "Dymaxion projection frame must have finite, positive dimensions "
      "with the Fuller/Airocean width-to-height ratio");
  return value;
}

/// Icosahedral face selection, Fuller transformation, and net layout helpers.
namespace dymaxion_detail {

/// Pi in radians.
inline constexpr double pi = 3.141592653589793238462643383279502884;
/// Number of drawable faces after the Australia and Japan splits.
inline constexpr std::size_t face_count = 23;

/// Point in the unfolded net's native coordinate system.
struct point_2d
{
  double x; ///< Horizontal coordinate.
  double y; ///< Vertical coordinate, increasing upward in native space.
};

/// Cartesian vector on or inside the unit sphere.
struct vector_3d
{
  double x; ///< First Cartesian component.
  double y; ///< Second Cartesian component.
  double z; ///< Third Cartesian component.
};

/// Triangle on the sphere or an icosahedron face plane.
using triangle_3d = std::array<vector_3d, 3>;
/// Triangle in the unfolded two-dimensional net.
using triangle_2d = std::array<point_2d, 3>;

/// Add two three-dimensional vectors component-wise.
/// @param left First vector.
/// @param right Second vector.
/// @return Component-wise sum.
inline constexpr vector_3d
operator+(const vector_3d left, const vector_3d right)
{ return {left.x + right.x, left.y + right.y, left.z + right.z}; }

/// Subtract two three-dimensional vectors component-wise.
/// @param left Minuend vector.
/// @param right Subtrahend vector.
/// @return Component-wise difference.
inline constexpr vector_3d
operator-(const vector_3d left, const vector_3d right)
{ return {left.x - right.x, left.y - right.y, left.z - right.z}; }

/// Multiply a vector by a scalar.
/// @param value Vector to scale.
/// @param scalar Scale factor.
/// @return Scaled vector.
inline constexpr vector_3d
operator*(const vector_3d value, const double scalar)
{ return {value.x * scalar, value.y * scalar, value.z * scalar}; }

/// Divide a vector by a nonzero scalar.
/// @param value Vector to scale.
/// @param scalar Nonzero divisor.
/// @return Scaled vector.
inline constexpr vector_3d
operator/(const vector_3d value, const double scalar)
{ return {value.x / scalar, value.y / scalar, value.z / scalar}; }

/// Subtract two planar points component-wise.
/// @param left Minuend point.
/// @param right Subtrahend point.
/// @return Component-wise difference.
inline constexpr point_2d
operator-(const point_2d left, const point_2d right)
{ return {left.x - right.x, left.y - right.y}; }

/// Multiply a planar point by a scalar.
/// @param value Point or vector to scale.
/// @param scalar Scale factor.
/// @return Scaled point.
inline constexpr point_2d
operator*(const point_2d value, const double scalar)
{ return {value.x * scalar, value.y * scalar}; }

/// Add two planar points component-wise.
/// @param left First point.
/// @param right Second point.
/// @return Component-wise sum.
inline constexpr point_2d
operator+(const point_2d left, const point_2d right)
{ return {left.x + right.x, left.y + right.y}; }

/// Three-dimensional dot product.
/// @param left First vector.
/// @param right Second vector.
/// @return Scalar dot product.
inline constexpr double
dot(const vector_3d left, const vector_3d right)
{ return left.x * right.x + left.y * right.y + left.z * right.z; }

/// Right-handed three-dimensional cross product.
/// @param left First vector.
/// @param right Second vector.
/// @return Vector perpendicular to both inputs.
inline constexpr vector_3d
cross(const vector_3d left, const vector_3d right)
{
  return {left.y * right.z - left.z * right.y,
          left.z * right.x - left.x * right.z,
          left.x * right.y - left.y * right.x};
}

/// Scalar triple product used by the oriented spherical half-space tests.
/// @param first First vector.
/// @param second Second vector.
/// @param third Third vector.
/// @return Scalar triple product.
inline constexpr double
determinant(const vector_3d first, const vector_3d second,
            const vector_3d third)
{ return dot(first, cross(second, third)); }

/// Euclidean vector magnitude.
/// @param value Vector to measure.
/// @return Euclidean length.
inline double
length(const vector_3d value)
{ return std::sqrt(dot(value, value)); }

/// Unit vector in the same direction as a nonzero vector.
/// @param value Nonzero vector.
/// @return Normalized vector.
inline vector_3d
normalized(const vector_3d value)
{ return value / length(value); }

/// Convert geographic coordinates to an exact-pole unit vector.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Unit Cartesian direction.
inline vector_3d
geographic_vector(const double latitude, const double longitude)
{
  if (latitude == 90)
    return {0, 0, 1};
  if (latitude == -90)
    return {0, 0, -1};
  const double canonical_longitude = longitude == 180 ? -180 : longitude;
  const double phi = latitude * pi / 180;
  const double lambda = canonical_longitude * pi / 180;
  const double cosine = std::cos(phi);
  return {cosine * std::cos(lambda),
          cosine * std::sin(lambda),
          std::sin(phi)};
}

/**
   Return the Fuller-oriented spherical face table.

   The first eighteen entries are complete icosahedron faces. Entries 18--19
   partition the Australia face, and 20--22 partition the Japan face. Split
   vertices lie in their parent face planes and need not be unit vectors.

   @return Twenty-three oriented spherical faces or subfaces.
*/
inline constexpr std::array<triangle_3d, face_count>
spherical_faces()
{
  return {{
    {{{0.42015242670871, 0.07814524940278296, 0.9040825506150193},
      {0.5188367303273644, 0.8354203803782358, 0.18133183755726245},
      {0.9950094394362416, -0.09134779527642793, 0.040147175877166645}}},
    {{{0.42015242670871, 0.07814524940278296, 0.9040825506150193},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754},
      {0.5188367303273644, 0.8354203803782358, 0.18133183755726245}}},
    {{{0.42015242670871, 0.07814524940278296, 0.9040825506150193},
      {-0.5154559599440418, -0.381716898287133, 0.7672009925177475},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754}}},
    {{{0.42015242670871, 0.07814524940278296, 0.9040825506150193},
      {0.3557814025329447, -0.8435800024661781, 0.40223422660292557},
      {-0.5154559599440418, -0.381716898287133, 0.7672009925177475}}},
    {{{0.42015242670871, 0.07814524940278296, 0.9040825506150193},
      {0.9950094394362416, -0.09134779527642793, 0.040147175877166645},
      {0.3557814025329447, -0.8435800024661781, 0.40223422660292557}}},
    {{{0.9950094394362416, -0.09134779527642793, 0.040147175877166645},
      {0.5188367303273644, 0.8354203803782358, 0.18133183755726245},
      {0.5154559599440418, 0.381716898287133, -0.7672009925177475}}},
    {{{0.5154559599440418, 0.381716898287133, -0.7672009925177475},
      {0.5188367303273644, 0.8354203803782358, 0.18133183755726245},
      {-0.3557814025329447, 0.8435800024661781, -0.40223422660292557}}},
    {{{-0.3557814025329447, 0.8435800024661781, -0.40223422660292557},
      {0.5188367303273644, 0.8354203803782358, 0.18133183755726245},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754}}},
    {{{-0.5154559599440418, -0.381716898287133, 0.7672009925177475},
      {-0.9950094394362416, 0.09134779527642793, -0.040147175877166645},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754}}},
    {{{-0.5154559599440418, -0.381716898287133, 0.7672009925177475},
      {-0.5188367303273644, -0.8354203803782358, -0.18133183755726245},
      {-0.9950094394362416, 0.09134779527642793, -0.040147175877166645}}},
    {{{-0.5154559599440418, -0.381716898287133, 0.7672009925177475},
      {0.3557814025329447, -0.8435800024661781, 0.40223422660292557},
      {-0.5188367303273644, -0.8354203803782358, -0.18133183755726245}}},
    {{{-0.5188367303273644, -0.8354203803782358, -0.18133183755726245},
      {0.3557814025329447, -0.8435800024661781, 0.40223422660292557},
      {0.4146822253203352, -0.6559624054348008, -0.6306758078914754}}},
    {{{0.4146822253203352, -0.6559624054348008, -0.6306758078914754},
      {0.3557814025329447, -0.8435800024661781, 0.40223422660292557},
      {0.9950094394362416, -0.09134779527642793, 0.040147175877166645}}},
    {{{0.5154559599440418, 0.381716898287133, -0.7672009925177475},
      {0.4146822253203352, -0.6559624054348008, -0.6306758078914754},
      {0.9950094394362416, -0.09134779527642793, 0.040147175877166645}}},
    {{{-0.42015242670871, -0.07814524940278296, -0.9040825506150193},
      {-0.3557814025329447, 0.8435800024661781, -0.40223422660292557},
      {-0.9950094394362416, 0.09134779527642793, -0.040147175877166645}}},
    {{{-0.42015242670871, -0.07814524940278296, -0.9040825506150193},
      {-0.9950094394362416, 0.09134779527642793, -0.040147175877166645},
      {-0.5188367303273644, -0.8354203803782358, -0.18133183755726245}}},
    {{{-0.42015242670871, -0.07814524940278296, -0.9040825506150193},
      {-0.5188367303273644, -0.8354203803782358, -0.18133183755726245},
      {0.4146822253203352, -0.6559624054348008, -0.6306758078914754}}},
    {{{-0.42015242670871, -0.07814524940278296, -0.9040825506150193},
      {0.4146822253203352, -0.6559624054348008, -0.6306758078914754},
      {0.5154559599440418, 0.381716898287133, -0.7672009925177475}}},
    {{{-0.3557814025329447, 0.8435800024661781, -0.40223422660292557},
      {-0.38796691462082733, 0.3827173765316976, -0.6531583886089725},
      {0.5154559599440418, 0.381716898287133, -0.7672009925177475}}},
    {{{-0.42015242670871, -0.07814524940278296, -0.9040825506150193},
      {0.5154559599440418, 0.381716898287133, -0.7672009925177475},
      {-0.38796691462082733, 0.3827173765316976, -0.6531583886089725}}},
    {{{-0.9950094394362416, 0.09134779527642793, -0.040147175877166645},
      {-0.3557814025329447, 0.8435800024661781, -0.40223422660292557},
      {-0.5884910224298405, 0.5302967343924689, 0.06276480180379439}}},
    {{{-0.3557814025329447, 0.8435800024661781, -0.40223422660292557},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754},
      {-0.5884910224298405, 0.5302967343924689, 0.06276480180379439}}},
    {{{-0.9950094394362416, 0.09134779527642793, -0.040147175877166645},
      {-0.5884910224298405, 0.5302967343924689, 0.06276480180379439},
      {-0.4146822253203352, 0.6559624054348008, 0.6306758078914754}}},
  }};
}

/// Return the vertical Airocean net triangles before landscape rotation.
/// @return Twenty-three planar triangles in the native vertical net.
inline constexpr std::array<triangle_2d, face_count>
vertical_faces()
{
  return {{
    {{{1.8211859946200586, 3.1543866727148018},
      {1.8211859946200586, 4.205848896953069},
      {2.7317789919300877, 3.6801177848339353}}},
    {{{1.8211859946200586, 3.1543866727148018},
      {0.9105929973100293, 3.6801177848339353},
      {1.8211859946200586, 4.205848896953069}}},
    {{{1.8211859946200586, 3.1543866727148018},
      {0.9105929973100293, 2.628655560595668},
      {0.9105929973100293, 3.6801177848339353}}},
    {{{1.8211859946200586, 3.1543866727148018},
      {1.8211859946200586, 2.1029244484765344},
      {0.9105929973100293, 2.628655560595668}}},
    {{{1.8211859946200586, 3.1543866727148018},
      {2.7317789919300877, 3.6801177848339353},
      {2.7317789919300877, 2.628655560595668}}},
    {{{2.7317789919300877, 3.6801177848339353},
      {1.8211859946200586, 4.205848896953069},
      {2.7317789919300877, 4.731580009072203}}},
    {{{1.8211859946200586, 5.257311121191336},
      {1.8211859946200586, 4.205848896953069},
      {0.9105929973100293, 4.731580009072203}}},
    {{{0.9105929973100293, 4.731580009072203},
      {1.8211859946200586, 4.205848896953069},
      {0.9105929973100293, 3.6801177848339353}}},
    {{{0.9105929973100293, 2.628655560595668},
      {0.0, 3.1543866727148018},
      {0.9105929973100293, 3.6801177848339353}}},
    {{{0.9105929973100293, 2.628655560595668},
      {0.9105929973100293, 1.5771933363574009},
      {0.0, 2.1029244484765344}}},
    {{{0.9105929973100293, 2.628655560595668},
      {1.8211859946200586, 2.1029244484765344},
      {0.9105929973100293, 1.5771933363574009}}},
    {{{0.9105929973100293, 1.5771933363574009},
      {1.8211859946200586, 2.1029244484765344},
      {1.8211859946200586, 1.0514622242382672}}},
    {{{1.8211859946200586, 1.0514622242382672},
      {1.8211859946200586, 2.1029244484765344},
      {2.7317789919300877, 1.5771933363574009}}},
    {{{1.8211859946200586, 0.0},
      {1.8211859946200586, 1.0514622242382672},
      {2.7317789919300877, 0.5257311121191336}}},
    {{{0.0, 5.257311121191336},
      {0.9105929973100293, 4.731580009072203},
      {0.0, 4.205848896953069}}},
    {{{0.0, 1.0514622242382672},
      {0.0, 2.1029244484765344},
      {0.9105929973100293, 1.5771933363574009}}},
    {{{0.9105929973100293, 0.5257311121191336},
      {0.9105929973100293, 1.5771933363574009},
      {1.8211859946200586, 1.0514622242382672}}},
    {{{0.9105929973100293, 0.5257311121191336},
      {1.8211859946200586, 1.0514622242382672},
      {1.8211859946200586, 0.0}}},
    {{{0.9105929973100293, 4.731580009072203},
      {0.45529649865501465, 4.994445565131769},
      {0.9105929973100293, 5.78304223331047}}},
    {{{0.9105929973100293, 0.5257311121191336},
      {1.8211859946200586, 0.0},
      {0.9105929973100293, 0.0}}},
    {{{0.0, 4.205848896953069},
      {0.9105929973100293, 4.731580009072203},
      {0.6070619982066862, 4.205848896953069}}},
    {{{0.9105929973100293, 4.731580009072203},
      {0.9105929973100293, 3.6801177848339353},
      {0.6070619982066862, 4.205848896953069}}},
    {{{0.0, 3.1543866727148018},
      {0.3035309991033431, 3.6801177848339353},
      {0.9105929973100293, 3.6801177848339353}}},
  }};
}

/// Rotate the official vertical net into its horizontal orientation.
/// @return Twenty-three planar triangles in the native horizontal net.
inline constexpr std::array<triangle_2d, face_count>
planar_faces()
{
  std::array<triangle_2d, face_count> result {};
  const auto vertical = vertical_faces();
  for (std::size_t face = 0; face < result.size(); ++face)
    for (std::size_t vertex = 0; vertex < result[face].size(); ++vertex)
      result[face][vertex] = {
        dymaxion_source_width - vertical[face][vertex].y,
        vertical[face][vertex].x,
      };
  return result;
}

/// Test whether a spherical direction lies in an oriented face.
/// @param face Oriented spherical triangle.
/// @param point Direction to test.
/// @return Whether all three oriented half-space tests pass.
inline bool
contains(const triangle_3d& face, const vector_3d point)
{
  constexpr double tolerance
    = 8 * std::numeric_limits<double>::epsilon();
  return determinant(point, face[1], face[2]) <= tolerance
         && determinant(face[0], point, face[2]) <= tolerance
         && determinant(face[0], face[1], point) <= tolerance;
}

/// Select the first containing face, preserving the net's edge tie rule.
/// @param point Unit geographic direction.
/// @return Index in `[0, face_count)`.
/// @throws std::logic_error if floating-point input matches no face.
inline std::size_t
containing_face(const vector_3d point)
{
  constexpr auto faces = spherical_faces();
  for (std::size_t index = 0; index < faces.size(); ++index)
    if (contains(faces[index], point))
      return index;
  throw std::logic_error("Dymaxion point is outside all spherical faces");
}

/**
   Orthogonal basis for one complete Fuller-oriented icosahedron face.

   `z` passes through the spherical face center, `y` points from that center
   toward the face's first vertex, and `x` completes the right-handed frame.
*/
struct face_basis
{
  vector_3d x; ///< Local transverse axis.
  vector_3d y; ///< Local first-vertex axis.
  vector_3d z; ///< Local face-center axis.
};

/// Return the unsplit parent triangle of a face or subface.
/// @param face_index Drawable face or subface index.
/// @return Complete parent icosahedron face.
inline triangle_3d
parent_spherical_face(const std::size_t face_index)
{
  constexpr auto faces = spherical_faces();
  if (face_index < 18)
    return faces[face_index];
  if (face_index < 20)
    return {{faces[18][0], faces[19][0], faces[18][2]}};
  return {{faces[20][0], faces[20][1], faces[21][1]}};
}

/// Construct a stable local coordinate basis for a complete face.
/// @param parent Complete oriented icosahedron face.
/// @return Orthonormal face-local basis.
inline face_basis
make_face_basis(const triangle_3d& parent)
{
  const vector_3d center = normalized(parent[0] + parent[1] + parent[2]);
  const vector_3d toward_first = normalized(
    parent[0] - center * dot(parent[0], center));
  return {cross(toward_first, center), toward_first, center};
}

/**
   Apply Gray's exact Fuller transformation in a face-local unit triangle.

   The three `a` values are spherical arc distances from the point to the
   face edges. Their symmetric combinations form a planar equilateral
   triangle whose edges have unit length after division by the icosahedron's
   spherical edge arc. Consequently every complete face edge has exact,
   uniform scale rather than the center-biased scale of a gnomonic mapping.

   @param point Direction on the unit sphere (non-unit split vertices are
   normalized defensively).
   @param basis Local axes of the point's complete icosahedron face.
   @return Point in the centered canonical equilateral triangle.
*/
inline point_2d
project_to_fuller_triangle(const vector_3d point, const face_basis& basis)
{
  const vector_3d unit = normalized(point);
  const double local_x = dot(unit, basis.x);
  const double local_y = dot(unit, basis.y);
  const double local_z = dot(unit, basis.z);
  if (local_z <= 0)
    throw std::logic_error(
      "Dymaxion transformation selected a point behind its face");

  static const double square_root_three = std::sqrt(3.0);
  static const double square_root_five = std::sqrt(5.0);
  static const double spherical_edge_arc
    = 2 * std::asin(std::sqrt(5 - square_root_five) / std::sqrt(10.0));
  static const double half_edge_arc = spherical_edge_arc / 2;
  static const double vertex_to_edge
    = std::sqrt(3 + square_root_five) / std::sqrt(5 + square_root_five);
  static const double chord_edge
    = std::sqrt(8.0) / std::sqrt(5 + square_root_five);

  const double scale
    = std::sqrt(5 + 2 * square_root_five)
      / (local_z * std::sqrt(15.0));
  const double projected_x = local_x * scale;
  const double projected_y = local_y * scale;
  const double a1_prime
    = 2 * projected_y / square_root_three + chord_edge / 3;
  const double a2_prime
    = projected_x - projected_y / square_root_three + chord_edge / 3;
  const double a3_prime
    = chord_edge / 3 - projected_x - projected_y / square_root_three;
  const auto arc_distance = [=](const double distance) {
    return half_edge_arc
           + std::atan((distance - chord_edge / 2) / vertex_to_edge);
  };
  const double a1 = arc_distance(a1_prime);
  const double a2 = arc_distance(a2_prime);
  const double a3 = arc_distance(a3_prime);
  return {(a2 - a3) / (2 * spherical_edge_arc),
          (2 * a1 - a2 - a3)
            / (2 * square_root_three * spherical_edge_arc)};
}

/// Cached exact-transform registration for one face or split subface.
struct face_geometry
{
  face_basis basis; ///< Complete parent face's local axes.
  triangle_2d canonical; ///< Split vertices in the exact Fuller triangle.
  triangle_2d planar; ///< Corresponding vertices in the interrupted net.
};

/// Complete immutable registration of all 23 drawable triangles.
struct layout_data
{
  std::array<face_geometry, face_count> faces; ///< Drawable registrations.
};

/// Build face-local exact-transform registrations once per process.
/// @return Complete immutable layout registration.
inline layout_data
make_layout()
{
  layout_data result {};
  constexpr auto spherical = spherical_faces();
  constexpr auto planar = planar_faces();
  for (std::size_t face = 0; face < result.faces.size(); ++face)
    {
      face_geometry& geometry = result.faces[face];
      geometry.basis = make_face_basis(parent_spherical_face(face));
      geometry.planar = planar[face];
      for (std::size_t vertex = 0; vertex < 3; ++vertex)
        geometry.canonical[vertex] = project_to_fuller_triangle(
          spherical[face][vertex], geometry.basis);
    }
  return result;
}

/// Process-wide lazily initialized exact Fuller layout.
/// @return Shared immutable layout registration.
inline const layout_data&
layout()
{
  static const layout_data value = make_layout();
  return value;
}

/**
   Apply the exact Fuller transform in one selected face and register it in
   the interrupted horizontal net.

   @param face_index Selected face or subface.
   @param point Unit geographic direction.
   @return Point in the unnormalized horizontal native net.
*/
inline point_2d
project_on_face(const std::size_t face_index, const vector_3d point)
{
  const face_geometry& face = layout().faces[face_index];
  const point_2d canonical = project_to_fuller_triangle(point, face.basis);
  const point_2d edge0 = face.canonical[1] - face.canonical[0];
  const point_2d edge1 = face.canonical[2] - face.canonical[0];
  const point_2d relative = canonical - face.canonical[0];
  const double divisor = edge0.x * edge1.y - edge0.y * edge1.x;
  const double alpha
    = (relative.x * edge1.y - relative.y * edge1.x) / divisor;
  const double beta
    = (edge0.x * relative.y - edge0.y * relative.x) / divisor;
  return face.planar[0] + (face.planar[1] - face.planar[0]) * alpha
                        + (face.planar[2] - face.planar[0]) * beta;
}

/// Project a coordinate into the native horizontal net.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Point in the unnormalized horizontal native net.
inline point_2d
project_to_unfolded_net(const double latitude, const double longitude)
{
  const vector_3d point = geographic_vector(latitude, longitude);
  return project_on_face(containing_face(point), point);
}

/// Convert a native, lower-left-origin net point to an upper-left unit map.
/// @param point Native net point.
/// @return Upper-left-origin normalized point.
inline point_2d
normalize_planar_point(const point_2d point)
{
  return {std::clamp(point.x / dymaxion_source_width, 0.0, 1.0),
          std::clamp(1 - point.y / dymaxion_source_height, 0.0, 1.0)};
}

/// Project a geographic coordinate into an upper-left-origin unit map.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Upper-left-origin normalized point.
inline point_2d
project_to_normalized_map(const double latitude, const double longitude)
{ return normalize_planar_point(project_to_unfolded_net(latitude, longitude)); }

} // namespace dymaxion_detail

/// Construct generic projection state from a variable-size Dymaxion frame.
/// Only frame_area is retained; placement belongs to `cartography`.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional backing-raster filename.
/// @return Validated generic projection state with its origin initialized.
inline projection_base
make_dymaxion_projection_base(const frame& map_frame, string raster_name)
{
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_dymaxion_projection_base(
    {projection_frame, 0, 0, dymaxion, std::move(raster_name)});
  const auto zero = dymaxion_detail::project_to_normalized_map(0, 0);
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/**
   Variable-size Fuller-oriented Dymaxion/Airocean projection.

   The forward transform chooses one of 23 oriented spherical triangles,
   evaluates Gray's exact edge-distance equations in its complete parent
   face, registers the result in Fuller's interrupted landscape net, and
   scales that net through `pframe.frame_area` without anisotropic distortion.
*/
struct dymaxionproj : public projection_base, public projection_api
{
  /// Construct from validated generic state.
  /// @param value Generic projection state with a ratio-correct frame.
  explicit dymaxionproj(const projection_base value)
  : projection_base(validate_dymaxion_projection_base(value))
  { }

  /// Construct for any finite, positive, ratio-correct frame.
  /// @param variable_frame Frame whose area supplies the projection size.
  /// @param raster_name Optional backing-raster filename.
  explicit dymaxionproj(const frame& variable_frame, string raster_name = {})
  : dymaxionproj(make_dymaxion_projection_base(
      variable_frame, std::move(raster_name)))
  { }

  /// Copy an existing Dymaxion projection.
  dymaxionproj(const dymaxionproj&) = default;

  /// Resolve the optional raster against the runtime resource directory.
  /// @param mode Raster mode retained for `projection_api` compatibility.
  /// @return Runtime resource path followed by the configured raster name.
  string
  image_filename([[maybe_unused]] const raster_mode mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  /// Project geographic latitude and longitude into the configured frame.
  /// @param latitude Latitude in degrees in `[-90, 90]`.
  /// @param longitude Longitude in degrees in `[-180, 180]`.
  /// @return Upper-left-origin point in `pframe.frame_area` coordinates.
  /// @throws std::invalid_argument for non-finite or out-of-domain input.
  a60::point_2t
  meridians_to_point_2d(const double latitude,
                        const double longitude) const override
  {
    if (!std::isfinite(latitude) || !std::isfinite(longitude))
      throw std::invalid_argument(
        "Dymaxion latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Dymaxion latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Dymaxion longitude must be in [-180, 180] degrees");

    const auto projected = dymaxion_detail::project_to_normalized_map(
      latitude, longitude);
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

/// Construct a variable-size Dymaxion projection.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional backing-raster filename.
/// @return Configured Dymaxion projection.
inline dymaxionproj
make_dymaxion_projection(const frame& map_frame, string raster_name = {})
{ return dymaxionproj(map_frame, std::move(raster_name)); }

/// Canonical native net frame, useful as a unit-scale numerical preset.
inline const frame pdymaxion_source {
  dymaxion_source_width, dymaxion_source_height
};

/// Canonical Dymaxion projection in the native net dimensions.
inline const dymaxionproj dymaxion_source {pdymaxion_source};

} // namespace a60::carto

#endif
