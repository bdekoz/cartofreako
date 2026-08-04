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
/// Root face shared by the reconstructed and exploratory spanning trees.
inline constexpr std::size_t tree_root = 103;
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
  // Constants and face order are retained from myriaworld's SPHEmesh.cpp.
  constexpr double tau = 0.8506508084;
  constexpr double one = 0.5257311121;
  const vector_3d za {tau, one, 0};
  const vector_3d zb {-tau, one, 0};
  const vector_3d zc {-tau, -one, 0};
  const vector_3d zd {tau, -one, 0};
  const vector_3d ya {one, 0, tau};
  const vector_3d yb {one, 0, -tau};
  const vector_3d yc {-one, 0, -tau};
  const vector_3d yd {-one, 0, tau};
  const vector_3d xa {0, tau, one};
  const vector_3d xb {0, -tau, one};
  const vector_3d xc {0, -tau, -one};
  const vector_3d xd {0, tau, -one};
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
  for (std::size_t face = 0; face < face_count; ++face)
    {
      const std::size_t parent = tree_parent(encoded_tree, face);
      if (parent == face)
        continue;
      add(face, parent);
      add(parent, face);
      ++edges;
    }
  if (edges + 1 != face_count)
    throw std::logic_error("Myriahedral spanning tree has the wrong size");
  return result;
}

/// Decode the source-raster-compatible tree adjacency.
/// @return Adjacency and degree arrays for all terminal faces.
inline tree_adjacency
make_tree_adjacency()
{ return make_tree_adjacency(spanning_tree_parent_hex); }

/// Test whether two independently produced spherical vertices coincide.
/// @param left First vertex.
/// @param right Second vertex.
/// @return `true` when squared separation is below the fixed tolerance.
inline bool
same_vertex(const vector_3d& left, const vector_3d& right)
{
  const vector_3d difference = left - right;
  return dot(difference, difference) < 1e-20;
}

/// Embed a root spherical triangle in the plane while preserving edge lengths.
/// @param value Root spherical triangle.
/// @return Planar root triangle with its first edge on the x axis.
inline planar_face
initial_planar_face(const spherical_face& value)
{
  const vector_3d d0 = value[1] - value[0];
  const vector_3d d1 = value[2] - value[0];
  const double length0 = length(d0);
  const double length1 = length(d1);
  const double cosine = std::clamp(
    std::abs(dot(d0, d1) / (length0 * length1)), 0.0, 1.0);
  return {{{0, 0},
           {length0, 0},
           {cosine * length0,
            std::sqrt(std::max(0.0, 1 - cosine * cosine)) * length1}}};
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
  const double distance_a = length(
    child[child_third] - child[child_shared[0]]);
  const double distance_b = length(
    child[child_third] - child[child_shared[1]]);
  const double along = (distance_a * distance_a
                        - distance_b * distance_b
                        + edge_length * edge_length)
                       / (2 * edge_length);
  const double height = std::sqrt(std::max(
    0.0, distance_a * distance_a - along * along));
  const point_2d unit = edge * (1 / edge_length);
  const point_2d perpendicular {-unit.y, unit.x};
  const point_2d candidate0 = a + unit * along + perpendicular * height;
  const point_2d candidate1 = a + unit * along - perpendicular * height;
  const double parent_side = cross(
    edge, parent_planar[parent_third] - a);
  const double candidate_side = cross(edge, candidate0 - a);
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

  result.planar[0] = initial_planar_face(result.spherical[0]);
  positioned[0] = true;
  stack[stack_size++] = 0;
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

/// Build the source-raster-compatible projection layout.
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
  const double extent_x = projection.maximum_x - projection.minimum_x;
  const double extent_y = projection.maximum_y - projection.minimum_y;
  const double scale = std::min(myriahedral_width_to_height_ratio / extent_x,
                                1 / extent_y);
  const double left = (myriahedral_width_to_height_ratio
                       - extent_x * scale) / 2;
  const double bottom = (1 - extent_y * scale) / 2;
  const double x = (left + (raw.x - projection.minimum_x) * scale)
                   / myriahedral_width_to_height_ratio;
  const double y = 1 - (bottom + (raw.y - projection.minimum_y) * scale);
  return {std::clamp(x, 0.0, 1.0), std::clamp(y, 0.0, 1.0)};
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

/// Measure how far a point lies inside a spherical face's half-spaces.
/// @param face Candidate spherical triangle.
/// @param value Unit vector to test.
/// @return Minimum signed edge margin; larger values indicate better fit.
inline double
containment_margin(const spherical_face& face, const vector_3d& value)
{
  double margin = std::numeric_limits<double>::infinity();
  for (std::size_t edge = 0; edge < 3; ++edge)
    {
      const vector_3d normal = cross(face[edge], face[(edge + 1) % 3]);
      const double reference = dot(normal, face[(edge + 2) % 3]);
      const double side = reference < 0 ? -dot(normal, value)
                                        : dot(normal, value);
      margin = std::min(margin, side);
    }
  return margin;
}

/// Select a terminal face by hierarchical maximum-margin descent.
/// @param value Geographic unit vector.
/// @return Stable terminal face index in `[0, face_count)`.
inline std::size_t
containing_face(const vector_3d& value)
{
  const auto base = make_icosahedron();
  std::size_t selected = 0;
  double best_margin = containment_margin(base[0], value);
  for (std::size_t index = 1; index < base.size(); ++index)
    {
      const double margin = containment_margin(base[index], value);
      if (margin > best_margin)
        {
          selected = index;
          best_margin = margin;
        }
    }

  spherical_face current = base[selected];
  for (std::size_t level = 0; level < subdivision_levels; ++level)
    {
      const auto children = subdivide(current);
      std::size_t child_index = 0;
      best_margin = containment_margin(children[0], value);
      for (std::size_t index = 1; index < children.size(); ++index)
        {
          const double margin = containment_margin(children[index], value);
          if (margin > best_margin)
            {
              child_index = index;
              best_margin = margin;
            }
        }
      selected = selected * 4 + child_index;
      current = children[child_index];
    }
  return selected;
}

/// Map a geographic coordinate affinely into a supplied unfolded layout.
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
  const auto& source = projection.spherical[index];
  const auto& target = projection.planar[index];

  const vector_3d d0 = source[1] - source[0];
  const vector_3d d1 = source[2] - source[0];
  const vector_3d relative = value - source[0];
  const double a = dot(d0, d0);
  const double b = dot(d0, d1);
  const double c = dot(d1, d1);
  const double r0 = dot(relative, d0);
  const double r1 = dot(relative, d1);
  const double determinant = a * c - b * b;
  const double alpha = (r0 * c - r1 * b) / determinant;
  const double beta = (r1 * a - r0 * b) / determinant;
  return target[0] + (target[1] - target[0]) * alpha
                   + (target[2] - target[0]) * beta;
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
/// @return Screen-oriented point clamped to the unit square.
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
/// @return Screen-oriented point clamped to the unit square.
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
   point affinely into a fixed land-aware spanning-tree net, and uniformly
   scales the net into a 16:9 frame.
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
