// alpha60 cartography projection Voronoi -*- mode: C++ -*-

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

// The icosahedral geometry, face tree, and source-canvas registration are
// derived from d3-geo-polygon's geoIcosahedral and polyhedral Voronoi
// implementation:
//
// Copyright 2017 Mike Bostock
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

/**
 * @file cart0freak0-voronoi.h
 * @brief Icosahedral Voronoi forward projection and fixed face-tree layout.
 */

#ifndef cart0freak0_VORONOI_H
#define cart0freak0_VORONOI_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace a60::carto {

/// Width of d3-geo-polygon's registered default canvas, in pixels.
inline constexpr double voronoi_source_width = 960;
/// Height of d3-geo-polygon's registered default canvas, in pixels.
inline constexpr double voronoi_source_height = 500;
/// Required width-to-height ratio of the registered source canvas.
inline constexpr double voronoi_width_to_height_ratio = 48.0 / 25.0;

/// True when a frame has finite, positive dimensions in the registered
/// 960:500 source-canvas ratio. The tolerance admits roundoff only.
/// @param candidate Frame to validate.
/// @return `true` when the dimensions are finite, positive, and ratio-correct.
inline bool
is_voronoi_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = voronoi_width_to_height_ratio * height;
  if (!std::isfinite(expected_width))
    return false;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
                           * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

/// Validate generic projection state for use by the Voronoi projection.
/// @param value Projection state to validate and return.
/// @return The validated projection state.
/// @throws std::invalid_argument if its frame does not have a 48:25 ratio.
inline projection_base
validate_voronoi_projection_base(projection_base value)
{
  if (!is_voronoi_frame(value.pframe))
    throw std::invalid_argument(
      "Voronoi projection frame must have finite, positive dimensions "
      "with a 48:25 width-to-height ratio");
  return value;
}

/// Internal icosahedral geometry, face selection, and tree-unfolding helpers.
namespace voronoi_detail {

/// Pi in radians.
inline constexpr double pi = 3.141592653589793238462643383279502884;
/// Number of vertices in the base icosahedron.
inline constexpr std::size_t vertex_count = 12;
/// Number of triangular faces in the base icosahedron.
inline constexpr std::size_t face_count = 20;
/// Scale from the unfolded gnomonic net to source-canvas pixels.
inline constexpr double source_scale = 131.777;
/// Horizontal center of the registered source canvas.
inline constexpr double source_center_x = voronoi_source_width / 2;
/// Vertical center of the registered source canvas.
inline constexpr double source_center_y = voronoi_source_height / 2;
/// Longitude rotation applied before choosing an icosahedral face.
inline constexpr double input_rotation_degrees = 108;
/// Longitude used to register the unfolded net with the source canvas.
inline constexpr double registration_longitude_degrees = 162;

/// Cartesian point in the unfolded two-dimensional net.
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

/// Two-dimensional affine transform represented as a 2-by-3 matrix.
struct affine_transform
{
  double a; ///< Coefficient multiplying the input x coordinate for output x.
  double b; ///< Coefficient multiplying the input y coordinate for output x.
  double c; ///< Translation added to the output x coordinate.
  double d; ///< Coefficient multiplying the input x coordinate for output y.
  double e; ///< Coefficient multiplying the input y coordinate for output y.
  double f; ///< Translation added to the output y coordinate.
};

/// Subtract two planar points component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise difference.
inline constexpr point_2d
operator-(const point_2d& left, const point_2d& right)
{ return {left.x - right.x, left.y - right.y}; }

/// Add two three-dimensional vectors component-wise.
/// @param left Left operand.
/// @param right Right operand.
/// @return Component-wise sum.
inline constexpr vector_3d
operator+(const vector_3d& left, const vector_3d& right)
{ return {left.x + right.x, left.y + right.y, left.z + right.z}; }

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

/// Measure a three-dimensional vector.
/// @param value Vector to measure.
/// @return Euclidean magnitude.
inline double
length(const vector_3d& value)
{ return std::sqrt(dot(value, value)); }

/// Normalize a nonzero three-dimensional vector.
/// @param value Vector to normalize.
/// @return Unit vector in the same direction.
inline vector_3d
normalized(const vector_3d& value)
{
  const double magnitude = length(value);
  return {value.x / magnitude, value.y / magnitude, value.z / magnitude};
}

/// Convert angular degrees to radians.
/// @param value Angle in degrees.
/// @return The angle in radians.
inline constexpr double
degrees_to_radians(const double value)
{ return value * pi / 180; }

/// Convert geographic coordinates to a unit Cartesian vector.
/// @param latitude Latitude in degrees in `[-90, 90]`.
/// @param longitude Longitude in degrees in `[-180, 180]`.
/// @return Point on the unit sphere, with exact vectors at both poles.
inline vector_3d
geographic_vector(const double latitude, const double longitude)
{
  // Collapse the geographic poles exactly. d3-geo's great-circle distance
  // treats all longitudes there as one point and therefore keeps the first
  // face in a stable tie; residual cos(+/-pi/2) must not choose another face.
  if (latitude == 90)
    return {0, 0, 1};
  if (latitude == -90)
    return {0, 0, -1};
  const double phi = degrees_to_radians(latitude);
  const double lambda = degrees_to_radians(longitude);
  const double cosine = std::cos(phi);
  return {cosine * std::cos(lambda),
          cosine * std::sin(lambda),
          std::sin(phi)};
}

/// Construct the identity affine transform.
/// @return Transform that leaves every planar point unchanged.
inline constexpr affine_transform
identity_transform()
{ return {1, 0, 0, 0, 1, 0}; }

/// Apply an affine transform to a planar point.
/// @param transform Transform to apply.
/// @param point Input point.
/// @return Transformed point.
inline constexpr point_2d
apply(const affine_transform& transform, const point_2d& point)
{
  return {transform.a * point.x + transform.b * point.y + transform.c,
          transform.d * point.x + transform.e * point.y + transform.f};
}

/// Compose two affine transforms so the result applies right, then left.
/// @param left Transform applied second.
/// @param right Transform applied first.
/// @return Composite affine transform.
inline constexpr affine_transform
multiply(const affine_transform& left, const affine_transform& right)
{
  return {
    left.a * right.a + left.b * right.d,
    left.a * right.b + left.b * right.e,
    left.a * right.c + left.b * right.f + left.c,
    left.d * right.a + left.e * right.d,
    left.d * right.b + left.e * right.e,
    left.d * right.c + left.e * right.f + left.f,
  };
}

/// Similarity transform mapping source[0..1] onto target[0..1].
/// @param target Target edge endpoints.
/// @param source Source edge endpoints.
/// @return Scale, rotation, reflection convention, and translation mapping the
/// source edge to the target edge.
/// @throws std::logic_error if either edge has zero length.
inline affine_transform
edge_transform(const std::array<point_2d, 2>& target,
               const std::array<point_2d, 2>& source)
{
  const point_2d u = target[1] - target[0];
  const point_2d v = source[1] - source[0];
  const double source_length = std::hypot(v.x, v.y);
  const double target_length = std::hypot(u.x, u.y);
  if (source_length == 0 || target_length == 0)
    throw std::logic_error("Voronoi face tree contains a degenerate edge");

  const double angle = std::atan2(u.x * v.y - u.y * v.x,
                                  u.x * v.x + u.y * v.y);
  const double scale = target_length / source_length;
  const double cosine = std::cos(angle);
  const double sine = std::sin(angle);
  const double a = scale * cosine;
  const double b = scale * sine;
  const double d = -scale * sine;
  const double e = scale * cosine;
  return {a, b, target[0].x - a * source[0].x - b * source[0].y,
          d, e, target[0].y - d * source[0].x - e * source[0].y};
}

/// Three indices identifying the vertices of one icosahedral face.
using face_vertices = std::array<std::size_t, 3>;

/// Spherical and planar geometry associated with one icosahedral face.
struct face_geometry
{
  face_vertices vertices {}; ///< Indices of the face's spherical vertices.
  vector_3d site {}; ///< Unit vector through the face center.
  vector_3d east {}; ///< Local gnomonic east basis vector.
  vector_3d north {}; ///< Local gnomonic north basis vector.
  affine_transform transform {identity_transform()}; ///< Face-to-net transform.
};

/// Complete base icosahedron and its unfolded face transformations.
struct layout_data
{
  std::array<vector_3d, vertex_count> vertices {}; ///< Spherical vertices.
  std::array<face_geometry, face_count> faces {}; ///< Face geometry and layout.
};

/// Construct the twelve vertices of the registered icosahedron.
/// @return Spherical vertex vectors ordered for the face index table.
inline std::array<vector_3d, vertex_count>
make_vertices()
{
  std::array<vector_3d, vertex_count> result {};
  result[0] = geographic_vector(90, 0);
  result[1] = geographic_vector(-90, 0);
  const double ring_latitude = std::atan(0.5) * 180 / pi;
  for (std::size_t index = 0; index < 10; ++index)
    {
      const int phase = static_cast<int>(index) * 36;
      const int longitude = (phase + 180) % 360 - 180;
      const double latitude = index % 2 == 0
                                ? -ring_latitude : ring_latitude;
      result[index + 2] = geographic_vector(latitude, longitude);
    }
  return result;
}

/// Return the vertex indices of all twenty oriented faces.
/// @return Face-to-vertex lookup table.
inline constexpr std::array<face_vertices, face_count>
face_vertex_indices()
{
  return {{{0, 3, 11}, {0, 5, 3}, {0, 7, 5}, {0, 9, 7}, {0, 11, 9},
           {2, 11, 3}, {3, 4, 2}, {4, 3, 5}, {5, 6, 4}, {6, 5, 7},
           {7, 8, 6}, {8, 7, 9}, {9, 10, 8}, {10, 9, 11},
           {11, 2, 10},
           {1, 2, 4}, {1, 4, 6}, {1, 6, 8}, {1, 8, 10}, {1, 10, 2}}};
}

/// Return the parent of every face in the fixed unfolding tree.
/// @return Parent indices, with `-1` marking the root face.
inline constexpr std::array<int, face_count>
face_parents()
{
  return {{-1, 7, 9, 11, 13,
           0, 5, 6, 7, 8,
           9, 10, 11, 12, 13,
           6, 8, 10, 12, 14}};
}

/// Project a spherical direction into a face-centered gnomonic plane.
/// @param face Face basis and center used for the projection.
/// @param point Unit direction to project.
/// @return Coordinates in the face's local plane.
/// @throws std::logic_error if the direction lies behind the selected face.
inline point_2d
project_on_face(const face_geometry& face, const vector_3d& point)
{
  const double denominator = dot(point, face.site);
  if (denominator <= 0)
    throw std::logic_error(
      "Voronoi gnomonic projection selected a point behind its face");
  return {dot(point, face.east) / denominator,
          -dot(point, face.north) / denominator};
}

/// Map a child face's local plane across its shared edge into its parent.
/// @param data Icosahedral vertices and initialized face geometry.
/// @param child_index Index of the child face.
/// @param parent_index Index of the adjacent parent face.
/// @return Affine transform from child-local to parent-local coordinates.
/// @throws std::logic_error if the faces do not share exactly one edge.
inline affine_transform
shared_edge_transform(const layout_data& data,
                      const std::size_t child_index,
                      const std::size_t parent_index)
{
  const face_geometry& child = data.faces[child_index];
  const face_geometry& parent = data.faces[parent_index];
  std::array<std::size_t, 2> shared {};
  std::size_t shared_count = 0;
  for (const std::size_t child_vertex : child.vertices)
    for (const std::size_t parent_vertex : parent.vertices)
      if (child_vertex == parent_vertex)
        {
          if (shared_count >= shared.size())
            throw std::logic_error(
              "Voronoi face-tree neighbors share too many vertices");
          shared[shared_count++] = child_vertex;
        }
  if (shared_count != shared.size())
    throw std::logic_error(
      "Voronoi face-tree neighbors do not share an edge");

  std::array<point_2d, 2> parent_edge {};
  std::array<point_2d, 2> child_edge {};
  for (std::size_t index = 0; index < shared.size(); ++index)
    {
      const vector_3d& vertex = data.vertices[shared[index]];
      parent_edge[index] = project_on_face(parent, vertex);
      child_edge[index] = project_on_face(child, vertex);
    }
  return edge_transform(parent_edge, child_edge);
}

/// Build all spherical face bases and their transforms into the unfolded net.
/// @return Fully initialized immutable-layout value.
/// @throws std::logic_error if the fixed face tree is malformed.
inline layout_data
make_layout()
{
  layout_data result;
  result.vertices = make_vertices();
  const auto indices = face_vertex_indices();
  for (std::size_t index = 0; index < result.faces.size(); ++index)
    {
      face_geometry& face = result.faces[index];
      face.vertices = indices[index];
      face.site = normalized(result.vertices[face.vertices[0]]
                             + result.vertices[face.vertices[1]]
                             + result.vertices[face.vertices[2]]);
      face.east = normalized({-face.site.y, face.site.x, 0});
      face.north = cross(face.site, face.east);
    }

  const auto parents = face_parents();
  std::array<bool, face_count> built {};
  built[0] = true;
  std::size_t built_count = 1;
  while (built_count < face_count)
    {
      bool progressed = false;
      for (std::size_t child = 1; child < face_count; ++child)
        {
          if (built[child])
            continue;
          const int parent_value = parents[child];
          if (parent_value < 0)
            throw std::logic_error("Voronoi face tree has multiple roots");
          const std::size_t parent = static_cast<std::size_t>(parent_value);
          if (parent >= face_count)
            throw std::logic_error("Voronoi face tree has an invalid parent");
          if (!built[parent])
            continue;

          const affine_transform edge = shared_edge_transform(
            result, child, parent);
          result.faces[child].transform = multiply(
            result.faces[parent].transform, edge);
          built[child] = true;
          ++built_count;
          progressed = true;
        }
      if (!progressed)
        throw std::logic_error("Voronoi face tree is disconnected or cyclic");
    }
  return result;
}

/// Access the process-wide lazily initialized Voronoi layout.
/// @return Const reference to the complete layout data.
inline const layout_data&
layout()
{
  static const layout_data value = make_layout();
  return value;
}

/// Nearest spherical site; maximizing the dot product avoids an unnecessary
/// acos and has the same stable, lowest-index tie behavior as the source.
/// @param point Unit direction whose containing Voronoi cell is required.
/// @return Index of the nearest face-center site.
inline std::size_t
containing_face(const vector_3d& point)
{
  if (point.x == 0 && point.y == 0)
    return point.z < 0 ? 15 : 0;
  const auto& faces = layout().faces;
  std::size_t closest = 0;
  double closest_dot = dot(point, faces[0].site);
  for (std::size_t index = 1; index < faces.size(); ++index)
    {
      const double candidate = dot(point, faces[index].site);
      if (candidate > closest_dot)
        {
          closest = index;
          closest_dot = candidate;
        }
    }
  return closest;
}

/// Project geographic coordinates into the unregistered unfolded net.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Point in unfolded-net coordinates.
inline point_2d
project_to_unfolded_net(const double latitude, const double longitude)
{
  const vector_3d point = geographic_vector(latitude, longitude);
  const face_geometry& face = layout().faces[containing_face(point)];
  const point_2d local = project_on_face(face, point);
  const point_2d transformed = apply(face.transform, local);
  return {transformed.x, -transformed.y};
}

/// Apply the same spherical rotation convention as d3-geo. Keeping +180
/// rather than canonicalizing it to -180 preserves face ties at map cuts.
/// @param longitude Geographic longitude in degrees.
/// @return Longitude rotated by 108 degrees and wrapped to `[-180, 180]`.
inline double
rotate_longitude(const double longitude)
{
  double result = longitude + input_rotation_degrees;
  if (result > 180)
    result -= 360;
  else if (result < -180)
    result += 360;
  return result;
}

/// Project geographic coordinates into the registered source-canvas domain.
/// @param latitude Latitude in degrees.
/// @param longitude Longitude in degrees.
/// @return Normalized map point, where the source canvas spans `[0, 1]` on
/// each axis.
inline point_2d
project_to_normalized_map(const double latitude, const double longitude)
{
  const point_2d raw = project_to_unfolded_net(
    latitude, rotate_longitude(longitude));
  static const point_2d registration = project_to_unfolded_net(
    0, registration_longitude_degrees);
  return {(source_center_x + source_scale * (raw.x - registration.x))
            / voronoi_source_width,
          (source_center_y - source_scale * (raw.y - registration.y))
            / voronoi_source_height};
}

} // namespace voronoi_detail

/// Construct generic projection state from a variable-size 48:25 frame.
/// Only frame_area is retained; map placement remains cartography's job.
/// @param map_frame Frame whose area determines the projection dimensions.
/// @param raster_name Optional backing-raster filename.
/// @return Validated generic Voronoi projection state.
/// @throws std::invalid_argument if the resulting frame is not 48:25.
inline projection_base
make_voronoi_projection_base(const frame& map_frame, string raster_name)
{
  const frame projection_frame {map_frame.frame_area};
  projection_base value = validate_voronoi_projection_base(
    {projection_frame, 0, 0, voronoi, std::move(raster_name)});
  const auto zero = voronoi_detail::project_to_normalized_map(0, 0);
  value.longitude_zero_x = zero.x * projection_frame.width();
  value.latitude_zero_y = zero.y * projection_frame.height();
  return value;
}

/**
   Variable-size icosahedral Voronoi projection.

   The forward transform selects the nearest of twenty spherical face sites,
   applies a face-centered gnomonic projection, unfolds the faces through a
   fixed shared-edge tree, and scales the registered net to a 48:25 frame.

   The face layout is the d3-geo-polygon default Icosahedral map implemented
   by Jason Davies, Enrico Spinielli, and Philippe Riviere.
*/
struct voronoiproj : public projection_base, public projection_api
{
  /// Construct from validated generic projection state.
  /// @param value Generic projection state with a 48:25 frame.
  /// @throws std::invalid_argument if the frame is invalid.
  explicit voronoiproj(const projection_base value)
  : projection_base(validate_voronoi_projection_base(value))
  { }

  /// Make a projection for any valid 48:25 frame. Frame placement offsets are
  /// deliberately discarded; the projection owns only frame_area.
  /// @param variable_frame Frame whose area supplies the projection size.
  /// @param raster_name Optional backing-raster filename.
  /// @throws std::invalid_argument if the resulting frame is invalid.
  explicit voronoiproj(const frame& variable_frame, string raster_name = {})
  : voronoiproj(make_voronoi_projection_base(variable_frame,
                                              std::move(raster_name)))
  { }

  /// Copy an existing Voronoi projection.
  /// @param other Projection to copy.
  voronoiproj(const voronoiproj& other) = default;

  /// Resolve the backing raster against the run-time data directory.
  /// @param mode Raster variant requested by the generic API; unused here.
  /// @return Full raster filename.
  string
  image_filename([[maybe_unused]] const raster_mode mode) const override
  {
    auto& resources = io::get_run_time_resources();
    return io::end_path(resources.data) + name;
  }

  /// Project one geographic coordinate into the configured frame.
  /// @param latitude Latitude in degrees in `[-90, 90]`.
  /// @param longitude Longitude in degrees in `[-180, 180]`.
  /// @return Projected `(x, y)` frame coordinates.
  /// @throws std::invalid_argument if either coordinate is non-finite or
  /// outside its supported range.
  a60::point_2t
  meridians_to_point_2d(const double latitude,
                        const double longitude) const override
  {
    if (!std::isfinite(latitude) || !std::isfinite(longitude))
      throw std::invalid_argument(
        "Voronoi latitude and longitude must be finite");
    if (latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Voronoi latitude must be in [-90, 90] degrees");
    if (longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Voronoi longitude must be in [-180, 180] degrees");

    const auto projected = voronoi_detail::project_to_normalized_map(
      latitude, longitude);
    return std::make_tuple(projected.x * pframe.width(),
                           projected.y * pframe.height());
  }
};

/// Construct a variable-size Voronoi projection.
/// @param map_frame Frame whose area supplies the projection size.
/// @param raster_name Optional backing-raster filename.
/// @return Configured Voronoi projection.
/// @throws std::invalid_argument if the frame is invalid.
inline voronoiproj
make_voronoi_projection(const frame& map_frame, string raster_name = {})
{
  return voronoiproj(map_frame, std::move(raster_name));
}

/// Registered 960-by-500 source frame for the canonical projection.
inline const frame pvoronoi_source {
  voronoi_source_width, voronoi_source_height
};

/// Canonical Voronoi projection using the registered source frame.
inline const voronoiproj voronoi_source {pvoronoi_source};

} // namespace a60::carto

#endif
