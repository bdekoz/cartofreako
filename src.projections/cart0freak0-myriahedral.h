// alpha60 cartography projection Myriahedral -*- mode: C++ -*-

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
 * @file cart0freak0-myriahedral.h
 * @brief Depth-5 Myriahedral forward projection and fixed unfolding tree.
 */

#ifndef cart0freak0_MYRIAHEDRAL_H
#define cart0freak0_MYRIAHEDRAL_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace a60::carto {

/// Width of the checked-in black-and-white source raster, in pixels.
inline constexpr double myriahedral_source_width = 4480;
/// Height of the checked-in black-and-white source raster, in pixels.
inline constexpr double myriahedral_source_height = 2520;
/// Required width-to-height ratio of the registered source canvas.
inline constexpr double myriahedral_width_to_height_ratio = 16.0 / 9.0;

/// True when a frame has finite, positive dimensions in the source raster's
/// 16:9 aspect ratio. The tolerance admits floating-point roundoff only.
/// @param candidate Frame to validate.
/// @return `true` when the dimensions are finite, positive, and ratio-correct.
inline bool
is_myriahedral_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = myriahedral_width_to_height_ratio * height;
  if (!std::isfinite(expected_width))
    return false;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

/// Validate generic projection state for use by the Myriahedral projection.
/// @param value Projection state to validate and return.
/// @return The validated projection state.
/// @throws std::invalid_argument if its frame does not have a 16:9 ratio.
inline projection_base
validate_myriahedral_projection_base(projection_base value)
{
  if (!is_myriahedral_frame(value.pframe))
    throw std::invalid_argument(
      "Myriahedral projection frame must have finite, positive dimensions "
      "with a 16:9 width-to-height ratio");
  return value;
}

/// Internal sphere subdivision, tree unfolding, and face projection helpers.
namespace myriahedral_detail {

/// Pi in radians.
inline constexpr double pi = 3.141592653589793238462643383279502884;
/// Number of faces in the base icosahedron.
inline constexpr std::size_t base_face_count = 20;
/// Number of recursive four-way subdivision levels after the base mesh.
inline constexpr std::size_t subdivision_levels = 4;
/// Number of terminal spherical faces in the depth-5 mesh.
inline constexpr std::size_t face_count = 5120;
/// Prim root shared by the reconstructed and exploratory spanning trees.
inline constexpr std::size_t mst_root = 103;
/// Face used to establish the planar coordinate system before unfolding.
inline constexpr std::size_t layout_seed_face = 0;
/// Rotation applied to the unfolded planar tree before registration.
inline constexpr double layout_rotation_degrees = 335;

/// Point in the unfolded two-dimensional net.
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

/// Triangle represented by three spherical unit vectors.
using spherical_face = std::array<vector_3d, 3>;
/// Triangle represented by three points in the unfolded plane.
using planar_face = std::array<point_2d, 3>;

/// Add two three-dimensional vectors component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise sum.
inline constexpr vector_3d
operator+(const vector_3d& left, const vector_3d& right)
{ return {left.x + right.x, left.y + right.y, left.z + right.z}; }

/// Subtract two three-dimensional vectors component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise difference.
inline constexpr vector_3d
operator-(const vector_3d& left, const vector_3d& right)
{ return {left.x - right.x, left.y - right.y, left.z - right.z}; }

/// Scale a three-dimensional vector.
/// @param value Vector to scale.
/// @param factor Scalar multiplier.
/// @return Scaled vector.
inline constexpr vector_3d
operator*(const vector_3d& value, const double factor)
{ return {value.x * factor, value.y * factor, value.z * factor}; }

/// Add two planar points component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise sum.
inline constexpr point_2d
operator+(const point_2d& left, const point_2d& right)
{ return {left.x + right.x, left.y + right.y}; }

/// Subtract two planar points component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise difference.
inline constexpr point_2d
operator-(const point_2d& left, const point_2d& right)
{ return {left.x - right.x, left.y - right.y}; }

/// Scale a planar point or displacement.
/// @param value Point or displacement to scale.
/// @param factor Scalar multiplier.
/// @return Scaled point.
inline constexpr point_2d
operator*(const point_2d& value, const double factor)
{ return {value.x * factor, value.y * factor}; }

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

/// Compute the signed two-dimensional cross product.
/// @param left Left operand.
/// @param right Right operand.
/// @return Scalar determinant of the operands.
inline constexpr double
cross(const point_2d& left, const point_2d& right)
{ return left.x * right.y - left.y * right.x; }

/// Measure a three-dimensional vector.
/// @param value Vector to measure.
/// @return Euclidean magnitude.
inline double
length(const vector_3d& value)
{ return std::sqrt(dot(value, value)); }

/// Measure a two-dimensional vector.
/// @param value Vector to measure.
/// @return Euclidean magnitude.
inline double
length(const point_2d& value)
{ return std::hypot(value.x, value.y); }

/// Normalize a nonzero three-dimensional vector.
/// @param value Vector to normalize.
/// @return Unit vector in the same direction.
inline vector_3d
normalized(const vector_3d& value)
{
  const double magnitude = length(value);
  return {value.x / magnitude, value.y / magnitude, value.z / magnitude};
}

/// Find the geodesic midpoint of two spherical vertices.
/// @param left First unit vector.
/// @param right Second unit vector.
/// @return Normalized midpoint direction.
inline vector_3d
spherical_midpoint(const vector_3d& left, const vector_3d& right)
{ return normalized((left + right) * 0.5); }

/// Subdivide one spherical triangle into four child triangles.
/// @param value Parent spherical triangle.
/// @return Four consistently ordered child triangles.
inline std::array<spherical_face, 4>
subdivide(const spherical_face& value)
{
  const vector_3d a = spherical_midpoint(value[0], value[2]);
  const vector_3d b = spherical_midpoint(value[0], value[1]);
  const vector_3d c = spherical_midpoint(value[1], value[2]);
  return {{{value[0], b, a},
           {b, value[1], c},
           {a, b, c},
           {a, c, value[2]}}};
}

/// Construct the base icosahedron in the historical myriaworld face order.
/// @return Twenty consistently oriented spherical faces.
inline std::array<spherical_face, base_face_count>
make_icosahedron()
{
  // Preserve myriaworld's face order while deriving unit vertices rather than
  // inheriting its ten-decimal approximations of the golden-ratio constants.
  const double golden_ratio = (1 + std::sqrt(5.0)) / 2;
  const double unit_scale = 1 / std::hypot(golden_ratio, 1.0);
  const double tau = golden_ratio * unit_scale;
  const double one = unit_scale;
  const vector_3d za = normalized({tau, one, 0});
  const vector_3d zb = normalized({-tau, one, 0});
  const vector_3d zc = normalized({-tau, -one, 0});
  const vector_3d zd = normalized({tau, -one, 0});
  const vector_3d ya = normalized({one, 0, tau});
  const vector_3d yb = normalized({one, 0, -tau});
  const vector_3d yc = normalized({-one, 0, -tau});
  const vector_3d yd = normalized({-one, 0, tau});
  const vector_3d xa = normalized({0, tau, one});
  const vector_3d xb = normalized({0, -tau, one});
  const vector_3d xc = normalized({0, -tau, -one});
  const vector_3d xd = normalized({0, tau, -one});
  return {{{ya, xa, yd}, {ya, yd, xb}, {yb, yc, xd}, {yb, xc, yc},
           {za, ya, zd}, {za, zd, yb}, {zc, yd, zb}, {zc, zb, yc},
           {xa, za, xd}, {xa, xd, zb}, {xb, xc, zd}, {xb, zc, xc},
           {xa, ya, za}, {xd, za, yb}, {ya, xb, zd}, {yb, zd, xc},
           {yd, xa, zb}, {yc, zb, xd}, {yd, zc, xb}, {yc, xc, zc}}};
}

/// Recursively append terminal faces in stable depth-first order.
/// @param value Current spherical face.
/// @param levels Remaining four-way subdivision levels.
/// @param result Fixed terminal-face output array.
/// @param next In/out index of the next output slot.
inline void
append_subdivided_faces(const spherical_face& value,
                        const std::size_t levels,
                        std::array<spherical_face, face_count>& result,
                        std::size_t& next)
{
  if (levels == 0)
    {
      result[next++] = value;
      return;
    }
  for (const auto& child : subdivide(value))
    append_subdivided_faces(child, levels - 1, result, next);
}

/// Construct all 5,120 terminal spherical faces.
/// @return Depth-first terminal-face array aligned with the fixed tree.
/// @throws std::logic_error if subdivision does not fill the array.
inline std::array<spherical_face, face_count>
make_spherical_faces()
{
  std::array<spherical_face, face_count> result {};
  std::size_t next = 0;
  for (const auto& face : make_icosahedron())
    append_subdivided_faces(face, subdivision_levels, result, next);
  if (next != result.size())
    throw std::logic_error("Myriahedral sphere subdivision is incomplete");
  return result;
}

// The minimum-spanning tree is reconstructed for the checked-in myriaworld
// source raster from its depth-5 pipeline and historical land data. Encoding
// it as four hexadecimal digits per parent keeps the fixed topology compact
// and removes runtime Boost, S2, and shapefile dependencies from the forward
// transform.
/// Four-hex-digit parent index for each face in the fixed unfolding tree.
inline constexpr char spanning_tree_parent_hex[] =
#include "cart0freak0-myriahedral-tree.inc"
  ;

static_assert(sizeof(spanning_tree_parent_hex) - 1 == face_count * 4);

/// Convert one lowercase hexadecimal digit to its numeric value.
/// @param value ASCII digit in `0-9` or `a-f`.
/// @return Numeric value in `[0, 15]`.
inline constexpr std::uint16_t
hex_digit(const char value)
{
  return value >= '0' && value <= '9'
           ? static_cast<std::uint16_t>(value - '0')
           : static_cast<std::uint16_t>(value - 'a' + 10);
}

/// Decode the parent index of one terminal face from a compact tree.
/// @param encoded_tree Four-lowercase-hex-digit parent indices.
/// @param face Terminal face index.
/// @return Parent face index; the root names itself.
inline constexpr std::uint16_t
tree_parent(const char* encoded_tree, const std::size_t face)
{
  const std::size_t offset = face * 4;
  return static_cast<std::uint16_t>(
    (hex_digit(encoded_tree[offset]) << 12)
    | (hex_digit(encoded_tree[offset + 1]) << 8)
    | (hex_digit(encoded_tree[offset + 2]) << 4)
    | hex_digit(encoded_tree[offset + 3]));
}

/// Decode one parent from the source-raster-compatible tree.
/// @param face Terminal face index.
/// @return Parent face index; face 103 names itself.
inline constexpr std::uint16_t
tree_parent(const std::size_t face)
{ return tree_parent(spanning_tree_parent_hex, face); }

/// Compact undirected adjacency representation of the fixed face tree.
struct tree_adjacency
{
  /// Up to three neighboring tree faces for every terminal face.
  std::array<std::array<std::uint16_t, 3>, face_count> neighbors {};
  /// Number of populated neighbors for every terminal face.
  std::array<std::uint8_t, face_count> degree {};
};

/// Decode and validate one undirected tree adjacency.
/// @param encoded_tree Four-lowercase-hex-digit parent indices.
/// @return Adjacency and degree arrays for all terminal faces.
/// @throws std::logic_error if an index, degree, or edge count is invalid.
inline tree_adjacency
make_tree_adjacency(const char* encoded_tree)
{
  tree_adjacency result;
  const auto add = [&result](const std::size_t source,
                             const std::size_t target)
  {
    if (source >= face_count || target >= face_count
        || result.degree[source] >= result.neighbors[source].size())
      throw std::logic_error("Invalid Myriahedral spanning tree");
    result.neighbors[source][result.degree[source]++]
      = static_cast<std::uint16_t>(target);
  };

  std::size_t edges = 0;
  std::size_t roots = 0;
  for (std::size_t face = 0; face < face_count; ++face)
    {
      const std::size_t parent = tree_parent(encoded_tree, face);
      if (parent >= face_count)
        throw std::logic_error(
          "Myriahedral spanning tree parent is out of range");
      if (parent == face)
        {
          ++roots;
          if (face != mst_root)
            throw std::logic_error(
              "Myriahedral spanning tree has an unexpected Prim root");
          continue;
        }
      add(face, parent);
      add(parent, face);
      ++edges;
    }
  if (roots != 1 || edges + 1 != face_count)
    throw std::logic_error("Myriahedral spanning tree has the wrong size");
  return result;
}

/// Decode the source-raster-compatible tree adjacency.
/// @return Adjacency and degree arrays for all terminal faces.
inline tree_adjacency
make_tree_adjacency()
{ return make_tree_adjacency(spanning_tree_parent_hex); }

/// Test whether two internally generated spherical vertices coincide.
/// @param left First vertex.
/// @param right Second vertex.
/// @return `true` when all components have the same generated value.
inline constexpr bool
same_vertex(const vector_3d& left, const vector_3d& right)
{ return left.x == right.x && left.y == right.y && left.z == right.z; }

/// Embed the layout-seed triangle in the plane while preserving edge lengths.
/// @param value Spherical layout-seed triangle.
/// @return Planar seed triangle with its first edge on the x axis.
inline planar_face
initial_planar_face(const spherical_face& value)
{
  const vector_3d d0 = value[1] - value[0];
  const vector_3d d1 = value[2] - value[0];
  const double length0 = length(d0);
  const double length1 = length(d1);
  if (!std::isfinite(length0) || !std::isfinite(length1)
      || length0 <= 0 || length1 <= 0)
    throw std::logic_error("Myriahedral seed face has an invalid edge");

  const double x = dot(d0, d1) / length0;
  double height_squared = std::fma(-x, x, length1 * length1);
  const double tolerance = 64 * std::numeric_limits<double>::epsilon()
                           * std::max(length1 * length1, x * x);
  if (height_squared < -tolerance)
    throw std::logic_error(
      "Myriahedral seed face violates the triangle inequality");
  height_squared = std::max(0.0, height_squared);
  return {{{0, 0},
           {length0, 0},
           {x, std::sqrt(height_squared)}}};
}

/// Unfold a child face across its edge shared with a positioned parent.
/// @param parent Parent spherical face.
/// @param child Adjacent child spherical face.
/// @param parent_planar Positioned parent triangle in the plane.
/// @return Positioned child triangle on the opposite side of the hinge edge.
/// @throws std::logic_error if the supplied faces do not share exactly one
/// edge.
inline planar_face
unfold_child(const spherical_face& parent,
             const spherical_face& child,
             const planar_face& parent_planar)
{
  std::array<std::size_t, 2> parent_shared {};
  std::array<std::size_t, 2> child_shared {};
  std::size_t shared_count = 0;
  for (std::size_t p = 0; p < 3; ++p)
    for (std::size_t c = 0; c < 3; ++c)
      if (same_vertex(parent[p], child[c]))
        {
          if (shared_count >= 2)
            throw std::logic_error(
              "Myriahedral tree neighbors share too many vertices");
          parent_shared[shared_count] = p;
          child_shared[shared_count] = c;
          ++shared_count;
        }
  if (shared_count != 2)
    throw std::logic_error(
      "Myriahedral tree neighbors do not share an edge");

  std::size_t parent_third = 0;
  std::size_t child_third = 0;
  while (parent_third == parent_shared[0]
         || parent_third == parent_shared[1])
    ++parent_third;
  while (child_third == child_shared[0]
         || child_third == child_shared[1])
    ++child_third;

  const point_2d a = parent_planar[parent_shared[0]];
  const point_2d b = parent_planar[parent_shared[1]];
  const point_2d edge = b - a;
  const double edge_length = length(edge);
  if (!std::isfinite(edge_length) || edge_length <= 0)
    throw std::logic_error("Myriahedral unfolding has an invalid hinge");
  const double distance_a = length(
    child[child_third] - child[child_shared[0]]);
  const double distance_b = length(
    child[child_third] - child[child_shared[1]]);
  if (!std::isfinite(distance_a) || !std::isfinite(distance_b)
      || distance_a <= 0 || distance_b <= 0)
    throw std::logic_error(
      "Myriahedral unfolding has an invalid child edge");
  const double difference_of_squares = std::fma(
    distance_a, distance_a, -distance_b * distance_b);
  const double edge_squared = edge_length * edge_length;
  const double along = (difference_of_squares + edge_squared)
                       / (2 * edge_length);
  double height_squared = std::fma(
    -along, along, distance_a * distance_a);
  const double height_tolerance
    = 128 * std::numeric_limits<double>::epsilon()
      * std::max(distance_a * distance_a, along * along);
  if (height_squared < -height_tolerance)
    throw std::logic_error(
      "Myriahedral unfolding violates the triangle inequality");
  height_squared = std::max(0.0, height_squared);
  const double height = std::sqrt(height_squared);
  const point_2d unit = edge * (1 / edge_length);
  const point_2d perpendicular {-unit.y, unit.x};
  const point_2d candidate0 = a + unit * along + perpendicular * height;
  const point_2d candidate1 = a + unit * along - perpendicular * height;
  const double parent_side = cross(
    edge, parent_planar[parent_third] - a);
  const double candidate_side = cross(edge, candidate0 - a);
  const double side_tolerance
    = 128 * std::numeric_limits<double>::epsilon()
      * edge_length
      * std::max(length(parent_planar[parent_third] - a), height);
  if (std::abs(parent_side) <= side_tolerance
      || std::abs(candidate_side) <= side_tolerance)
    throw std::logic_error(
      "Myriahedral unfolding cannot orient a child face");
  const point_2d selected = candidate_side * parent_side < 0
                              ? candidate0 : candidate1;

  planar_face result {};
  result[child_shared[0]] = a;
  result[child_shared[1]] = b;
  result[child_third] = selected;
  return result;
}

/// Complete spherical mesh, unfolded planar mesh, and planar bounds.
struct projection_layout
{
  std::array<spherical_face, face_count> spherical; ///< Terminal sphere mesh.
  std::array<planar_face, face_count> planar; ///< Matching unfolded triangles.
  double minimum_x; ///< Minimum rotated planar x coordinate.
  double minimum_y; ///< Minimum rotated planar y coordinate.
  double maximum_x; ///< Maximum rotated planar x coordinate.
  double maximum_y; ///< Maximum rotated planar y coordinate.
};

/// Build, unfold, rotate, and measure a complete face tree.
/// @param encoded_tree Four-lowercase-hex-digit parent indices.
/// @param rotation_degrees Counterclockwise planar registration rotation.
/// @return Fully positioned projection layout.
/// @throws std::logic_error if the tree is disconnected.
inline projection_layout
make_projection_layout(const char* encoded_tree,
                       const double rotation_degrees)
{
  projection_layout result {make_spherical_faces(), {}, 0, 0, 0, 0};
  const tree_adjacency tree = make_tree_adjacency(encoded_tree);
  std::array<bool, face_count> positioned {};
  std::array<std::uint16_t, face_count> stack {};
  std::size_t stack_size = 0;

  result.planar[layout_seed_face]
    = initial_planar_face(result.spherical[layout_seed_face]);
  positioned[layout_seed_face] = true;
  stack[stack_size++] = static_cast<std::uint16_t>(layout_seed_face);
  while (stack_size != 0)
    {
      const std::size_t current = stack[--stack_size];
      for (std::size_t n = 0; n < tree.degree[current]; ++n)
        {
          const std::size_t neighbor = tree.neighbors[current][n];
          if (positioned[neighbor])
            continue;
          result.planar[neighbor] = unfold_child(
            result.spherical[current], result.spherical[neighbor],
            result.planar[current]);
          positioned[neighbor] = true;
          stack[stack_size++] = static_cast<std::uint16_t>(neighbor);
        }
    }
  if (std::find(positioned.begin(), positioned.end(), false)
      != positioned.end())
    throw std::logic_error("Myriahedral spanning tree is disconnected");

  const double angle = rotation_degrees * pi / 180;
  const double cosine = std::cos(angle);
  const double sine = std::sin(angle);
  result.minimum_x = std::numeric_limits<double>::infinity();
  result.minimum_y = std::numeric_limits<double>::infinity();
  result.maximum_x = -std::numeric_limits<double>::infinity();
  result.maximum_y = -std::numeric_limits<double>::infinity();
  for (auto& face : result.planar)
    for (auto& point : face)
      {
        point = {cosine * point.x - sine * point.y,
                 sine * point.x + cosine * point.y};
        result.minimum_x = std::min(result.minimum_x, point.x);
        result.minimum_y = std::min(result.minimum_y, point.y);
        result.maximum_x = std::max(result.maximum_x, point.x);
        result.maximum_y = std::max(result.maximum_y, point.y);
      }
  return result;
}

/// Build the source-raster-registered projection layout.
/// @return Fully positioned reference layout.
inline projection_layout
make_projection_layout()
{
  return make_projection_layout(
    spanning_tree_parent_hex, layout_rotation_degrees);
}

/// Return the lazily initialized immutable projection layout.
/// @return Shared complete layout used by all Myriahedral projections.
inline const projection_layout&
layout()
{
  static const projection_layout value = make_projection_layout();
  return value;
}

/// Normalize one raw planar point into the registered 16:9 unit canvas.
/// @param projection Measured planar layout containing the point.
/// @param raw Raw unfolded coordinate.
/// @return Screen-oriented coordinate in the unit square.
inline point_2d
normalize_planar_point(const projection_layout& projection,
                       const point_2d raw)
{
  if (!std::isfinite(raw.x) || !std::isfinite(raw.y)
      || !std::isfinite(projection.minimum_x)
      || !std::isfinite(projection.minimum_y)
      || !std::isfinite(projection.maximum_x)
      || !std::isfinite(projection.maximum_y))
    throw std::logic_error(
      "Myriahedral normalization received non-finite geometry");

  const long double extent_x
    = static_cast<long double>(projection.maximum_x)
      - projection.minimum_x;
  const long double extent_y
    = static_cast<long double>(projection.maximum_y)
      - projection.minimum_y;
  if (extent_x <= 0 || extent_y <= 0)
    throw std::logic_error("Myriahedral layout has invalid bounds");

  constexpr long double ratio = 16.0L / 9.0L;
  const long double scale = std::min(ratio / extent_x, 1.0L / extent_y);
  const long double left = (ratio - extent_x * scale) / 2;
  const long double bottom = (1 - extent_y * scale) / 2;
  const long double x
    = (left + (static_cast<long double>(raw.x) - projection.minimum_x)
              * scale) / ratio;
  const long double y
    = 1 - (bottom + (static_cast<long double>(raw.y)
                     - projection.minimum_y) * scale);
  constexpr long double tolerance
    = 128 * std::numeric_limits<double>::epsilon();
  if (!std::isfinite(x) || !std::isfinite(y)
      || x < -tolerance || x > 1 + tolerance
      || y < -tolerance || y > 1 + tolerance)
    throw std::logic_error(
      "Myriahedral projection lies outside its registered canvas");
  return {static_cast<double>(std::clamp(x, 0.0L, 1.0L)),
          static_cast<double>(std::clamp(y, 0.0L, 1.0L))};
}

/// Convert geographic degrees to a unit Cartesian vector.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Unit vector, with exact canonical vectors at both poles.
inline vector_3d
geographic_vector(const double latitude, const double longitude)
{
  if (latitude == 90)
    return {0, 0, 1};
  if (latitude == -90)
    return {0, 0, -1};
  const double phi = latitude * pi / 180;
  // Exact +180 and -180 identify one meridian. Canonicalize before both
  // face selection and projection so roundoff in sin(+/-pi) cannot select
  // different faces when the meridian lies on a cut.
  const double canonical_longitude = longitude == 180 ? -180 : longitude;
  const double lambda = canonical_longitude * pi / 180;
  const double cosine = std::cos(phi);
  return {cosine * std::cos(lambda),
          cosine * std::sin(lambda),
          std::sin(phi)};
}

/// Evaluate the oriented volume of three vectors with widened intermediates.
/// @param first First column of the determinant.
/// @param second Second column of the determinant.
/// @param third Third column of the determinant.
/// @return Scalar triple product `first dot (second cross third)`.
inline long double
triple_product(const vector_3d& first,
               const vector_3d& second,
               const vector_3d& third)
{
  const long double cross_x
    = static_cast<long double>(second.y) * third.z
      - static_cast<long double>(second.z) * third.y;
  const long double cross_y
    = static_cast<long double>(second.z) * third.x
      - static_cast<long double>(second.x) * third.z;
  const long double cross_z
    = static_cast<long double>(second.x) * third.y
      - static_cast<long double>(second.y) * third.x;
  return std::fma(static_cast<long double>(first.x), cross_x,
                  std::fma(static_cast<long double>(first.y), cross_y,
                           static_cast<long double>(first.z) * cross_z));
}

/// Central-projection barycentric coordinates within one spherical face.
struct barycentric_coordinates
{
  long double first;  ///< Weight of face vertex zero.
  long double second; ///< Weight of face vertex one.
  long double third;  ///< Weight of face vertex two.
};

/// Intersect a ray from the sphere center with one chord-face plane.
/// @param face Spherical chord triangle.
/// @param value Direction of the geographic point from the sphere center.
/// @return Barycentric coordinates whose sum is one.
/// @throws std::logic_error if the ray is parallel to the face plane.
inline barycentric_coordinates
gnomonic_barycentric(const spherical_face& face, const vector_3d& value)
{
  const long double first = triple_product(value, face[1], face[2]);
  const long double second = triple_product(value, face[2], face[0]);
  const long double third = triple_product(value, face[0], face[1]);
  const long double denominator = first + second + third;
  const long double magnitude
    = std::abs(first) + std::abs(second) + std::abs(third);
  const long double tolerance
    = 64 * std::numeric_limits<long double>::epsilon() * magnitude;
  if (!std::isfinite(first) || !std::isfinite(second)
      || !std::isfinite(third) || !std::isfinite(denominator)
      || magnitude == 0 || std::abs(denominator) <= tolerance)
    throw std::logic_error(
      "Myriahedral gnomonic ray is parallel to its face plane");
  return {first / denominator,
          second / denominator,
          third / denominator};
}

/// Project a direction centrally into a specific unfolded face.
/// @param source Spherical chord triangle.
/// @param target Matching unfolded planar triangle.
/// @param value Direction of the geographic point from the sphere center.
/// @return Gnomonic point in the unnormalized unfolded net.
inline point_2d
project_on_face(const spherical_face& source,
                const planar_face& target,
                const vector_3d& value)
{
  const barycentric_coordinates weights
    = gnomonic_barycentric(source, value);
  const long double x
    = std::fma(weights.first, static_cast<long double>(target[0].x),
               std::fma(weights.second,
                        static_cast<long double>(target[1].x),
                        weights.third * target[2].x));
  const long double y
    = std::fma(weights.first, static_cast<long double>(target[0].y),
               std::fma(weights.second,
                        static_cast<long double>(target[1].y),
                        weights.third * target[2].y));
  if (!std::isfinite(x) || !std::isfinite(y))
    throw std::logic_error(
      "Myriahedral gnomonic projection produced a non-finite point");
  return {static_cast<double>(x), static_cast<double>(y)};
}

/// Project a direction centrally into one indexed unfolded face.
/// @param projection Complete spherical and planar layout.
/// @param face_index Terminal face to use without classifying the point.
/// @param value Direction of the geographic point from the sphere center.
/// @return Gnomonic point in the unnormalized unfolded net.
/// @throws std::out_of_range if `face_index` is invalid.
inline point_2d
project_on_face(const projection_layout& projection,
                const std::size_t face_index,
                const vector_3d& value)
{
  if (face_index >= face_count)
    throw std::out_of_range("Myriahedral face index is out of range");
  return project_on_face(projection.spherical[face_index],
                         projection.planar[face_index], value);
}

/// Measure how far a point lies inside a spherical face's half-spaces.
/// Edge-plane normals are normalized so margins from differently shaped faces
/// are comparable.
/// @param face Candidate spherical triangle.
/// @param value Unit vector to test.
/// @return Minimum signed angular edge margin; larger values indicate fit.
inline long double
containment_margin_wide(const spherical_face& face,
                        const vector_3d& value)
{
  const long double orientation
    = triple_product(face[0], face[1], face[2]);
  if (!std::isfinite(orientation) || orientation == 0)
    throw std::logic_error("Myriahedral face has invalid orientation");
  const long double direction = orientation < 0 ? -1 : 1;
  const std::array<long double, 3> sides {
    direction * triple_product(value, face[1], face[2]),
    direction * triple_product(value, face[2], face[0]),
    direction * triple_product(value, face[0], face[1]),
  };
  const std::array<vector_3d, 3> normals {
    cross(face[1], face[2]),
    cross(face[2], face[0]),
    cross(face[0], face[1]),
  };
  long double result = std::numeric_limits<long double>::infinity();
  for (std::size_t edge = 0; edge < 3; ++edge)
    {
      const long double normal_length = std::sqrt(
        static_cast<long double>(dot(normals[edge], normals[edge])));
      if (!std::isfinite(normal_length) || normal_length <= 0)
        throw std::logic_error("Myriahedral face has an invalid edge plane");
      result = std::min(result, sides[edge] / normal_length);
    }
  return result;
}

/// Double-precision adapter for diagnostics and existing callers.
/// @param face Candidate spherical triangle.
/// @param value Unit vector to test.
/// @return Minimum normalized edge margin rounded to `double`.
inline double
containment_margin(const spherical_face& face, const vector_3d& value)
{ return static_cast<double>(containment_margin_wide(face, value)); }

/// Test spherical half-spaces with widened orientation predicates.
/// @param face Candidate spherical triangle.
/// @param value Unit vector to test.
/// @return `true` when the point is inside or at roundoff distance from it.
inline bool
contains(const spherical_face& face, const vector_3d& value)
{
  const long double orientation
    = triple_product(face[0], face[1], face[2]);
  if (!std::isfinite(orientation) || orientation == 0)
    throw std::logic_error("Myriahedral face has invalid orientation");
  const long double direction = orientation < 0 ? -1 : 1;
  constexpr long double tolerance
    = 64 * std::numeric_limits<long double>::epsilon();
  return direction * triple_product(value, face[1], face[2]) >= -tolerance
         && direction * triple_product(value, face[2], face[0]) >= -tolerance
         && direction * triple_product(value, face[0], face[1]) >= -tolerance;
}

/// Select a terminal face by hierarchical containment-first descent.
/// @param value Geographic unit vector.
/// @return Stable terminal face index in `[0, face_count)`.
inline std::size_t
containing_face(const vector_3d& value)
{
  const auto base = make_icosahedron();
  std::size_t selected = base.size();
  for (std::size_t index = 0; index < base.size(); ++index)
    if (contains(base[index], value))
      {
        selected = index;
        break;
      }
  if (selected == base.size())
    {
      selected = 0;
      long double best_margin = containment_margin_wide(base[0], value);
      for (std::size_t index = 1; index < base.size(); ++index)
        {
          const long double margin
            = containment_margin_wide(base[index], value);
          if (margin > best_margin)
            {
              selected = index;
              best_margin = margin;
            }
        }
    }

  spherical_face current = base[selected];
  for (std::size_t level = 0; level < subdivision_levels; ++level)
    {
      const auto children = subdivide(current);
      std::size_t child_index = children.size();
      for (std::size_t index = 0; index < children.size(); ++index)
        if (contains(children[index], value))
          {
            child_index = index;
            break;
          }
      if (child_index == children.size())
        {
          child_index = 0;
          long double best_margin
            = containment_margin_wide(children[0], value);
          for (std::size_t index = 1; index < children.size(); ++index)
            {
              const long double margin
                = containment_margin_wide(children[index], value);
              if (margin > best_margin)
                {
                  child_index = index;
                  best_margin = margin;
                }
            }
        }
      selected = selected * 4 + child_index;
      current = children[child_index];
    }
  return selected;
}

/// Map a geographic coordinate gnomonically into a supplied unfolded layout.
/// @param projection Complete layout to use.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Point in the unnormalized unfolded planar net.
inline point_2d
project_to_unfolded_net(const projection_layout& projection,
                        const double latitude, const double longitude)
{
  const vector_3d value = geographic_vector(latitude, longitude);
  const std::size_t index = containing_face(value);
  return project_on_face(projection, index, value);
}

/// Map a geographic coordinate into the reference unfolded layout.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Point in the unnormalized reference net.
inline point_2d
project_to_unfolded_net(const double latitude, const double longitude)
{ return project_to_unfolded_net(layout(), latitude, longitude); }

/// Normalize a supplied layout into the centered registered 16:9 canvas.
/// @param projection Complete layout to use.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Screen-oriented point, with roundoff-only canvas clamping.
inline point_2d
project_to_normalized_map(const projection_layout& projection,
                          const double latitude, const double longitude)
{
  return normalize_planar_point(
    projection,
    project_to_unfolded_net(projection, latitude, longitude));
}

/// Normalize the reference layout into its registered 16:9 canvas.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Screen-oriented point, with roundoff-only canvas clamping.
inline point_2d
project_to_normalized_map(const double latitude, const double longitude)
{ return project_to_normalized_map(layout(), latitude, longitude); }

} // namespace myriahedral_detail

/// Construct generic projection state for a supplied layout and 16:9 frame.
/// Only frame_area is retained; map placement remains cartography's job.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @param projection_layout Complete layout used by the projection.
/// @return Validated generic projection state with its origin initialized.
inline projection_base
make_myriahedral_projection_base(
  const frame& map_frame, string raster_name,
  const myriahedral_detail::projection_layout& projection_layout)
{
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_myriahedral_projection_base(
    {projection_frame, 0, 0, myriahedral, std::move(raster_name)});
  const auto zero = myriahedral_detail::project_to_normalized_map(
    projection_layout, 0, 0);
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/// Construct generic projection state for the reference layout.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @return Validated generic projection state with its origin initialized.
inline projection_base
make_myriahedral_projection_base(const frame& map_frame, string raster_name)
{
  return make_myriahedral_projection_base(
    map_frame, std::move(raster_name), myriahedral_detail::layout());
}

/**
   Variable-size depth-5 Myriahedral projection.

   The forward transform selects one of 5120 spherical triangles, maps the
   point centrally and gnomonically into a fixed land-aware spanning-tree net,
   and uniformly scales the net into a 16:9 frame.
*/
struct myriaproj : public projection_base, public projection_api
{
  /// Immutable tree layout selected for this projection instance.
  const myriahedral_detail::projection_layout* selected_layout;

  /// Construct from generic projection state.
  /// @param value State with a valid 16:9 frame.
  explicit myriaproj(const projection_base value)
  : projection_base(validate_myriahedral_projection_base(value)),
    selected_layout(&myriahedral_detail::layout())
  { }

  /// Construct generic state against an explicit immutable layout.
  /// @param value State with a valid 16:9 frame.
  /// @param projection_layout Layout whose lifetime exceeds this projection.
  myriaproj(const projection_base value,
            const myriahedral_detail::projection_layout& projection_layout)
  : projection_base(validate_myriahedral_projection_base(value)),
    selected_layout(&projection_layout)
  { }

  /// Make a projection for any valid 16:9 frame. Frame placement offsets are
  /// deliberately discarded; the projection owns only frame_area.
  /// @param variable_frame Ratio-correct output frame.
  /// @param raster_name Optional registered raster filename.
  explicit myriaproj(const frame& variable_frame, string raster_name = {})
  : myriaproj(make_myriahedral_projection_base(variable_frame,
                                                std::move(raster_name)))
  { }

  /// Make a projection for a valid frame and an explicit immutable layout.
  /// @param variable_frame Ratio-correct output frame.
  /// @param projection_layout Layout whose lifetime exceeds this projection.
  /// @param raster_name Optional registered raster filename.
  myriaproj(const frame& variable_frame,
            const myriahedral_detail::projection_layout& projection_layout,
            string raster_name = {})
  : myriaproj(
      make_myriahedral_projection_base(
        variable_frame, std::move(raster_name), projection_layout),
      projection_layout)
  { }

  /// Reject a temporary layout because the projection stores a pointer to it.
  myriaproj(const frame&,
            myriahedral_detail::projection_layout&&,
            string = {}) = delete;

  /// Copy a Myriahedral projection.
  /// @param other Projection to copy.
  myriaproj(const myriaproj& other) = default;

  /// Return the immutable tree layout used by this projection.
  /// @return Complete selected layout.
  const myriahedral_detail::projection_layout&
  layout() const
  { return *selected_layout; }

  /// Resolve the registered raster against the runtime data directory.
  /// @param mode Raster variant requested by the common API; unused here.
  /// @return Full runtime-resource path to the registered raster.
  string
  image_filename([[maybe_unused]] const raster_mode mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  /// Project a geographic coordinate into the configured 16:9 frame.
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
        "Myriahedral latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Myriahedral latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Myriahedral longitude must be in [-180, 180] degrees");

    const auto projected = myriahedral_detail::project_to_normalized_map(
      layout(), latitude, longitude);
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

/// Construct a variable-size Myriahedral projection.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @return Configured Myriahedral projection.
inline myriaproj
make_myriahedral_projection(const frame& map_frame, string raster_name = {})
{
  return myriaproj(map_frame, std::move(raster_name));
}

/// Construct a variable-size projection from an explicit immutable layout.
/// @param map_frame Ratio-correct output frame.
/// @param projection_layout Layout whose lifetime exceeds the result.
/// @param raster_name Optional registered raster filename.
/// @return Configured Myriahedral projection.
inline myriaproj
make_myriahedral_projection(
  const frame& map_frame,
  const myriahedral_detail::projection_layout& projection_layout,
  string raster_name = {})
{
  return myriaproj(
    map_frame, projection_layout, std::move(raster_name));
}

/// Reject a temporary layout because the result retains a layout pointer.
inline myriaproj
make_myriahedral_projection(
  const frame&, myriahedral_detail::projection_layout&&, string = {}) = delete;

/// Frame matching the checked-in black-and-white source raster.
inline const frame pmyriahedral_source {
  myriahedral_source_width, myriahedral_source_height
};

/// Registered projection preset for the checked-in Myriahedral raster.
inline const myriaproj myriahedral_source {
  pmyriahedral_source,
  "assets.static/myriahedral/black-white-downsampled.png"
};

} // namespace a60::carto

#endif
