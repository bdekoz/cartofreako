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

#ifndef a60_CARTOGRAPHY_PROJECTION_MYRIAHEDRAL_H
#define a60_CARTOGRAPHY_PROJECTION_MYRIAHEDRAL_H 1

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

/// Dimensions and ratio of the checked-in black-and-white source raster.
inline constexpr double myriahedral_source_width = 4480;
inline constexpr double myriahedral_source_height = 2520;
inline constexpr double myriahedral_width_to_height_ratio = 16.0 / 9.0;

/// True when a frame has finite, positive dimensions in the source raster's
/// 16:9 aspect ratio. The tolerance admits floating-point roundoff only.
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

inline projection_base
validate_myriahedral_projection_base(projection_base value)
{
  if (!is_myriahedral_frame(value.pframe))
    throw std::invalid_argument(
      "Myriahedral projection frame must have finite, positive dimensions "
      "with a 16:9 width-to-height ratio");
  return value;
}

namespace myriahedral_detail {

inline constexpr double pi = 3.141592653589793238462643383279502884;
inline constexpr std::size_t base_face_count = 20;
inline constexpr std::size_t subdivision_levels = 4;
inline constexpr std::size_t face_count = 5120;
inline constexpr double layout_rotation_degrees = 335;

struct point_2d
{
  double x;
  double y;
};

struct vector_3d
{
  double x;
  double y;
  double z;
};

using spherical_face = std::array<vector_3d, 3>;
using planar_face = std::array<point_2d, 3>;

inline constexpr vector_3d
operator+(const vector_3d& left, const vector_3d& right)
{ return {left.x + right.x, left.y + right.y, left.z + right.z}; }

inline constexpr vector_3d
operator-(const vector_3d& left, const vector_3d& right)
{ return {left.x - right.x, left.y - right.y, left.z - right.z}; }

inline constexpr vector_3d
operator*(const vector_3d& value, const double factor)
{ return {value.x * factor, value.y * factor, value.z * factor}; }

inline constexpr point_2d
operator+(const point_2d& left, const point_2d& right)
{ return {left.x + right.x, left.y + right.y}; }

inline constexpr point_2d
operator-(const point_2d& left, const point_2d& right)
{ return {left.x - right.x, left.y - right.y}; }

inline constexpr point_2d
operator*(const point_2d& value, const double factor)
{ return {value.x * factor, value.y * factor}; }

inline constexpr double
dot(const vector_3d& left, const vector_3d& right)
{ return left.x * right.x + left.y * right.y + left.z * right.z; }

inline constexpr vector_3d
cross(const vector_3d& left, const vector_3d& right)
{
  return {left.y * right.z - left.z * right.y,
          left.z * right.x - left.x * right.z,
          left.x * right.y - left.y * right.x};
}

inline constexpr double
cross(const point_2d& left, const point_2d& right)
{ return left.x * right.y - left.y * right.x; }

inline double
length(const vector_3d& value)
{ return std::sqrt(dot(value, value)); }

inline double
length(const point_2d& value)
{ return std::hypot(value.x, value.y); }

inline vector_3d
normalized(const vector_3d& value)
{
  const double magnitude = length(value);
  return {value.x / magnitude, value.y / magnitude, value.z / magnitude};
}

inline vector_3d
spherical_midpoint(const vector_3d& left, const vector_3d& right)
{ return normalized((left + right) * 0.5); }

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
inline constexpr char spanning_tree_parent_hex[] =
#include "a60-carto-projection-myriahedral-tree.inc"
  ;

static_assert(sizeof(spanning_tree_parent_hex) - 1 == face_count * 4);

inline constexpr std::uint16_t
hex_digit(const char value)
{
  return value >= '0' && value <= '9'
           ? static_cast<std::uint16_t>(value - '0')
           : static_cast<std::uint16_t>(value - 'a' + 10);
}

inline constexpr std::uint16_t
tree_parent(const std::size_t face)
{
  const std::size_t offset = face * 4;
  return static_cast<std::uint16_t>(
    (hex_digit(spanning_tree_parent_hex[offset]) << 12)
    | (hex_digit(spanning_tree_parent_hex[offset + 1]) << 8)
    | (hex_digit(spanning_tree_parent_hex[offset + 2]) << 4)
    | hex_digit(spanning_tree_parent_hex[offset + 3]));
}

struct tree_adjacency
{
  std::array<std::array<std::uint16_t, 3>, face_count> neighbors {};
  std::array<std::uint8_t, face_count> degree {};
};

inline tree_adjacency
make_tree_adjacency()
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
      const std::size_t parent = tree_parent(face);
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

inline bool
same_vertex(const vector_3d& left, const vector_3d& right)
{
  const vector_3d difference = left - right;
  return dot(difference, difference) < 1e-20;
}

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

struct projection_layout
{
  std::array<spherical_face, face_count> spherical;
  std::array<planar_face, face_count> planar;
  double minimum_x;
  double minimum_y;
  double maximum_x;
  double maximum_y;
};

inline projection_layout
make_projection_layout()
{
  projection_layout result {make_spherical_faces(), {}, 0, 0, 0, 0};
  const tree_adjacency tree = make_tree_adjacency();
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

  const double angle = layout_rotation_degrees * pi / 180;
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

inline const projection_layout&
layout()
{
  static const projection_layout value = make_projection_layout();
  return value;
}

inline vector_3d
geographic_vector(const double latitude, const double longitude)
{
  if (latitude == 90)
    return {0, 0, 1};
  if (latitude == -90)
    return {0, 0, -1};
  const double phi = latitude * pi / 180;
  const double lambda = longitude * pi / 180;
  const double cosine = std::cos(phi);
  return {cosine * std::cos(lambda),
          cosine * std::sin(lambda),
          std::sin(phi)};
}

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

inline point_2d
project_to_unfolded_net(const double latitude, const double longitude)
{
  const vector_3d value = geographic_vector(
    latitude, longitude == 180 ? -180 : longitude);
  const auto& projection = layout();
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

inline point_2d
project_to_normalized_map(const double latitude, const double longitude)
{
  const point_2d raw = project_to_unfolded_net(latitude, longitude);
  const auto& projection = layout();
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

} // namespace myriahedral_detail

/// Construct generic projection state from a variable-size 16:9 frame.
/// Only frame_area is retained; map placement remains cartography's job.
inline projection_base
make_myriahedral_projection_base(const frame& map_frame, string raster_name)
{
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_myriahedral_projection_base(
    {projection_frame, 0, 0, myriahedral, std::move(raster_name)});
  const auto zero = myriahedral_detail::project_to_normalized_map(0, 0);
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/**
   Variable-size depth-5 Myriahedral projection.

   The forward transform selects one of 5120 spherical triangles, maps the
   point affinely into a fixed land-aware spanning-tree net, and uniformly
   scales the net into a 16:9 frame.
*/
struct myriaproj : public projection_base, public projection_api
{
  explicit myriaproj(const projection_base value)
  : projection_base(validate_myriahedral_projection_base(value))
  { }

  /// Make a projection for any valid 16:9 frame. Frame placement offsets are
  /// deliberately discarded; the projection owns only frame_area.
  explicit myriaproj(const frame& variable_frame, string raster_name = {})
  : myriaproj(make_myriahedral_projection_base(variable_frame,
                                                std::move(raster_name)))
  { }

  myriaproj(const myriaproj&) = default;

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
        "Myriahedral latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Myriahedral latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Myriahedral longitude must be in [-180, 180] degrees");

    const auto projected = myriahedral_detail::project_to_normalized_map(
      latitude, longitude);
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

inline myriaproj
make_myriahedral_projection(const frame& map_frame, string raster_name = {})
{
  return myriaproj(map_frame, std::move(raster_name));
}

inline const frame pmyriahedral_source {
  myriahedral_source_width, myriahedral_source_height
};

inline const myriaproj myriahedral_source {
  pmyriahedral_source,
  "assets/myriahedral/black-white-downsampled.png"
};

} // namespace a60::carto

#endif
