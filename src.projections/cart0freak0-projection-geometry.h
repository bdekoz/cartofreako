// Flat geometry protocol and topology-aware projection pipeline.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_PROJECTION_GEOMETRY_H
#define CART0FREAK0_PROJECTION_GEOMETRY_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "cart0freak0-projection-runtime.h"
#include "cart0freak0-projection-slicing.h"

namespace cart0freak0::projection_runtime {

enum class geometry_part_type : std::uint8_t
{
  point = 0,
  line = 1,
  ring = 2,
};

enum class ring_role : std::uint8_t
{
  none = 0,
  exterior = 1,
  hole = 2,
};

/// Renderer-neutral flattened input. Offsets count geographic points, not
/// doubles. `part_offsets` therefore ends at `coordinates.size()`.
struct geometry_input
{
  std::vector<geographic_point> coordinates;
  std::vector<std::uint32_t> part_offsets;
  std::vector<geometry_part_type> part_types;
  std::vector<std::uint32_t> feature_ids;
  std::vector<ring_role> ring_roles;
};

struct geometry_options
{
  double tolerance_pixels = 0.35;
  double maximum_angular_step = 5;
  std::uint32_t maximum_subdivision_depth = 16;
  std::optional<slice_descriptor> slice;
};

struct geometry_diagnostics
{
  std::uint32_t input_points = 0;
  std::uint32_t input_parts = 0;
  std::uint32_t output_vertices = 0;
  std::uint32_t output_parts = 0;
  std::uint32_t sampled_points = 0;
  std::uint32_t cell_transitions = 0;
  std::uint32_t cuts = 0;
  std::uint32_t periodic_wraps = 0;
  std::uint32_t fallback_splits = 0;
  std::uint32_t clipped_parts = 0;
  std::uint32_t dropped_parts = 0;
};

/// Output command buffer consumed without geometric reinterpretation by SVG,
/// Canvas, D3-stream replay, or WebGL adapters.
struct geometry_command_buffer
{
  std::vector<double> coordinates;
  std::vector<std::uint32_t> part_offsets {0};
  std::vector<geometry_part_type> part_types;
  std::vector<std::uint32_t> feature_ids;
  std::vector<std::uint32_t> native_cells;
  std::vector<std::uint32_t> component_ids;
  std::vector<ring_role> ring_roles;
  std::vector<std::uint8_t> closed;
  double origin_x = 0;
  double origin_y = 0;
  double width = 0;
  double height = 0;
  geometry_diagnostics diagnostics;
};

namespace geometry_detail {

inline constexpr double epsilon = 1e-10;

struct point
{
  double x;
  double y;
};

using polygon = std::vector<point>;

inline point
operator+(const point left, const point right)
{ return {left.x + right.x, left.y + right.y}; }

inline point
operator-(const point left, const point right)
{ return {left.x - right.x, left.y - right.y}; }

inline point
operator*(const point value, const double factor)
{ return {value.x * factor, value.y * factor}; }

inline double
cross(const point left, const point right)
{ return left.x * right.y - left.y * right.x; }

inline bool
same_point(const point left, const point right)
{
  return std::abs(left.x - right.x) <= epsilon
         && std::abs(left.y - right.y) <= epsilon;
}

inline void
append_unique(polygon& result, const point value)
{
  if (result.empty() || !same_point(result.back(), value))
    result.push_back(value);
}

inline double
signed_area(const polygon& value)
{
  double result = 0;
  for (std::size_t index = 0; index < value.size(); ++index)
    result += cross(value[index], value[(index + 1) % value.size()]);
  return result / 2;
}

inline polygon
clip_against_edge(const polygon& subject, const point edge_start,
                  const point edge_end, const double orientation)
{
  polygon result;
  if (subject.empty())
    return result;
  const point edge = edge_end - edge_start;
  const auto distance = [=](const point value) {
    return orientation * cross(edge, value - edge_start);
  };
  point previous = subject.back();
  double previous_distance = distance(previous);
  bool previous_inside = previous_distance >= -epsilon;
  for (const point current : subject)
    {
      const double current_distance = distance(current);
      const bool current_inside = current_distance >= -epsilon;
      if (current_inside != previous_inside)
        {
          const double denominator = previous_distance - current_distance;
          if (std::abs(denominator) > epsilon)
            append_unique(result,
                          previous + (current - previous)
                            * (previous_distance / denominator));
        }
      if (current_inside)
        append_unique(result, current);
      previous = current;
      previous_distance = current_distance;
      previous_inside = current_inside;
    }
  if (result.size() > 1 && same_point(result.front(), result.back()))
    result.pop_back();
  return result;
}

inline polygon
clip_to_convex_polygon(polygon subject, const polygon& clip)
{
  if (subject.size() < 3 || clip.size() < 3)
    return {};
  const double orientation = signed_area(clip) < 0 ? -1 : 1;
  for (std::size_t index = 0; index < clip.size(); ++index)
    {
      subject = clip_against_edge(
        subject, clip[index], clip[(index + 1) % clip.size()], orientation);
      if (subject.size() < 3)
        return {};
    }
  return subject;
}

inline polygon
rectangle(const double west, const double south,
          const double east, const double north)
{
  return {{west, south}, {east, south}, {east, north}, {west, north}};
}

inline polygon
clip_to_rectangle(const polygon& subject, const double west,
                  const double south, const double east,
                  const double north)
{
  return clip_to_convex_polygon(subject, rectangle(west, south, east, north));
}

inline polygon
densify(const polygon& value, const double maximum_step)
{
  polygon result;
  if (value.empty())
    return result;
  for (std::size_t index = 0; index < value.size(); ++index)
    {
      const point start = value[index];
      const point finish = value[(index + 1) % value.size()];
      append_unique(result, start);
      const double span = std::max(std::abs(finish.x - start.x),
                                   std::abs(finish.y - start.y));
      const int segments = std::max(
        1, static_cast<int>(std::ceil(span / maximum_step)));
      for (int segment = 1; segment < segments; ++segment)
        append_unique(result,
                      start + (finish - start)
                        * (static_cast<double>(segment) / segments));
    }
  return result;
}

inline polygon
to_polygon(const std::vector<geographic_point>& value)
{
  polygon result;
  result.reserve(value.size());
  for (const geographic_point item : value)
    append_unique(result, {item.longitude, item.latitude});
  if (result.size() > 1 && same_point(result.front(), result.back()))
    result.pop_back();
  return result;
}

inline projected_path
to_projected_path(const polygon& value)
{
  projected_path result;
  result.reserve(value.size());
  for (const point item : value)
    result.emplace_back(item.x, item.y);
  return result;
}

inline polygon
from_projected_path(const projected_path& value)
{
  polygon result;
  result.reserve(value.size());
  for (const auto [x, y] : value)
    result.push_back({x, y});
  return result;
}

inline double
point_to_segment_distance(const projected_point value,
                          const projected_point first,
                          const projected_point second)
{
  const double x = std::get<0>(value);
  const double y = std::get<1>(value);
  const double x1 = std::get<0>(first);
  const double y1 = std::get<1>(first);
  const double dx = std::get<0>(second) - x1;
  const double dy = std::get<1>(second) - y1;
  const double length_squared = dx * dx + dy * dy;
  if (length_squared <= std::numeric_limits<double>::epsilon())
    return std::hypot(x - x1, y - y1);
  const double factor = std::clamp(
    ((x - x1) * dx + (y - y1) * dy) / length_squared, 0.0, 1.0);
  return std::hypot(x - (x1 + factor * dx),
                    y - (y1 + factor * dy));
}

struct vector_3d
{
  double x;
  double y;
  double z;
};

inline vector_3d
geographic_vector(const geographic_point value)
{
  constexpr double radians = 3.14159265358979323846 / 180;
  const double latitude = value.latitude * radians;
  const double longitude = value.longitude * radians;
  const double cosine = std::cos(latitude);
  return {cosine * std::cos(longitude), cosine * std::sin(longitude),
          std::sin(latitude)};
}

inline geographic_point
great_circle_midpoint(const geographic_point first,
                      const geographic_point second)
{
  const vector_3d left = geographic_vector(first);
  const vector_3d right = geographic_vector(second);
  vector_3d middle {left.x + right.x, left.y + right.y, left.z + right.z};
  const double magnitude = std::hypot(std::hypot(middle.x, middle.y), middle.z);
  if (magnitude < 1e-12)
    return interpolate(first, second, 0.5);
  middle.x /= magnitude;
  middle.y /= magnitude;
  middle.z /= magnitude;
  constexpr double degrees = 180 / 3.14159265358979323846;
  return {std::asin(std::clamp(middle.z, -1.0, 1.0)) * degrees,
          std::atan2(middle.y, middle.x) * degrees};
}

inline double
angular_span(const geographic_point first, const geographic_point second)
{
  const vector_3d left = geographic_vector(first);
  const vector_3d right = geographic_vector(second);
  const double dot = std::clamp(
    left.x * right.x + left.y * right.y + left.z * right.z, -1.0, 1.0);
  return std::acos(dot) * 180 / 3.14159265358979323846;
}

inline void
sample_edge(const projection_context& context,
            const geographic_point first, const geographic_point second,
            const geometry_options& options, const std::uint32_t depth,
            std::vector<geographic_point>& result)
{
  const geographic_point middle = great_circle_midpoint(first, second);
  const projected_point p0 = project_point(context, first);
  const projected_point p1 = project_point(context, second);
  const projected_point pm = project_point(context, middle);
  const bool cell_change = projection_cell(context, first)
                           != projection_cell(context, second)
                           || projection_cell(context, first)
                                != projection_cell(context, middle);
  const bool subdivide
    = depth < options.maximum_subdivision_depth
      && (cell_change
          || angular_span(first, second) > options.maximum_angular_step
          || point_to_segment_distance(pm, p0, p1)
               > options.tolerance_pixels);
  if (subdivide)
    {
      sample_edge(context, first, middle, options, depth + 1, result);
      sample_edge(context, middle, second, options, depth + 1, result);
    }
  else
    result.push_back(second);
}

inline std::vector<geographic_point>
adaptive_sample(const projection_context& context,
                const std::vector<geographic_point>& source,
                const bool closed, const geometry_options& options)
{
  if (source.empty())
    return {};
  std::vector<geographic_point> result;
  result.reserve(source.size());
  result.push_back(source.front());
  const std::size_t edges = closed ? source.size() : source.size() - 1;
  for (std::size_t index = 0; index < edges; ++index)
    sample_edge(context, source[index], source[(index + 1) % source.size()],
                options, 0, result);
  if (closed && result.size() > 1
      && result.front().latitude == result.back().latitude
      && result.front().longitude == result.back().longitude)
    result.pop_back();
  return result;
}

inline bool
clip_line_segment(const point first, const point second,
                  const projected_view view, point& clipped_first,
                  point& clipped_second)
{
  const double dx = second.x - first.x;
  const double dy = second.y - first.y;
  const std::array p {-dx, dx, -dy, dy};
  const std::array q {first.x - view.x,
                      view.x + view.width - first.x,
                      first.y - view.y,
                      view.y + view.height - first.y};
  double begin = 0;
  double end = 1;
  for (std::size_t index = 0; index < p.size(); ++index)
    {
      if (std::abs(p[index]) <= epsilon)
        {
          if (q[index] < 0)
            return false;
          continue;
        }
      const double ratio = q[index] / p[index];
      if (p[index] < 0)
        begin = std::max(begin, ratio);
      else
        end = std::min(end, ratio);
      if (begin > end)
        return false;
    }
  clipped_first = {first.x + begin * dx, first.y + begin * dy};
  clipped_second = {first.x + end * dx, first.y + end * dy};
  return true;
}

inline std::vector<projected_path>
clip_polyline(const projected_path& source, const projected_view view)
{
  std::vector<projected_path> result;
  projected_path current;
  for (std::size_t index = 1; index < source.size(); ++index)
    {
      point first {};
      point second {};
      const point source_first {
        std::get<0>(source[index - 1]), std::get<1>(source[index - 1]),
      };
      const point source_second {
        std::get<0>(source[index]), std::get<1>(source[index]),
      };
      if (!clip_line_segment(source_first, source_second, view, first, second))
        {
          if (current.size() >= 2)
            result.push_back(std::move(current));
          current.clear();
          continue;
        }
      const projected_point first_tuple {first.x, first.y};
      const projected_point second_tuple {second.x, second.y};
      if (!current.empty() && current.back() != first_tuple)
        {
          if (current.size() >= 2)
            result.push_back(std::move(current));
          current.clear();
        }
      projection_runtime::append_unique(current, first_tuple);
      projection_runtime::append_unique(current, second_tuple);
    }
  if (current.size() >= 2)
    result.push_back(std::move(current));
  return result;
}

inline std::vector<std::vector<geographic_point>>
clip_geographic_line(const std::vector<geographic_point>& source,
                     const geographic_bounds bounds)
{
  projected_path as_planar;
  as_planar.reserve(source.size());
  for (const geographic_point item : source)
    as_planar.emplace_back(item.longitude, item.latitude);
  const projected_view view {bounds.west, bounds.south,
                             bounds.east - bounds.west,
                             bounds.north - bounds.south};
  std::vector<std::vector<geographic_point>> result;
  for (const projected_path& clipped : clip_polyline(as_planar, view))
    {
      std::vector<geographic_point> path;
      path.reserve(clipped.size());
      for (const auto [longitude, latitude] : clipped)
        path.push_back({latitude, longitude});
      result.push_back(std::move(path));
    }
  return result;
}

inline polygon
clip_geographic_ring(const polygon& source,
                     const geographic_bounds bounds)
{
  return clip_to_rectangle(source, bounds.west, bounds.south,
                           bounds.east, bounds.north);
}

inline std::array<point, 3>
native_face_triangle(const projection_context& context,
                     const std::size_t face_index)
{
  if (context.spec.kind == projection_kind::myriahedral)
    {
      const auto& triangle
        = std::get<myriaproj>(context.projection).layout().planar.at(face_index);
      return {{{triangle[0].x, triangle[0].y},
               {triangle[1].x, triangle[1].y},
               {triangle[2].x, triangle[2].y}}};
    }
  if (context.spec.kind == projection_kind::dymaxion)
    {
      constexpr auto planar = a60::carto::dymaxion_detail::planar_faces();
      const auto& triangle = planar.at(face_index);
      return {{{triangle[0].x, triangle[0].y},
               {triangle[1].x, triangle[1].y},
               {triangle[2].x, triangle[2].y}}};
    }
  if (context.spec.kind == projection_kind::voronoi)
    {
      using namespace a60::carto::voronoi_detail;
      const auto& data = layout();
      const face_geometry& face = data.faces.at(face_index);
      std::array<point, 3> result {};
      for (std::size_t index = 0; index < result.size(); ++index)
        {
          const point_2d local = project_on_face(
            face, data.vertices[face.vertices[index]]);
          const point_2d transformed = apply(face.transform, local);
          result[index] = {transformed.x, -transformed.y};
        }
      return result;
    }
  throw std::logic_error("native triangle requested for a non-triangle net");
}

inline point
project_on_native_face(const projection_context& context,
                       const std::size_t face_index,
                       const point geographic)
{
  if (context.spec.kind == projection_kind::myriahedral)
    {
      using namespace a60::carto::myriahedral_detail;
      const auto& layout = std::get<myriaproj>(context.projection).layout();
      const point_2d projected = project_on_face(
        layout, face_index,
        a60::carto::myriahedral_detail::geographic_vector(
          geographic.y, geographic.x));
      return {projected.x, projected.y};
    }
  if (context.spec.kind == projection_kind::dymaxion)
    {
      using namespace a60::carto::dymaxion_detail;
      const point_2d projected = project_on_face(
        face_index, a60::carto::dymaxion_detail::geographic_vector(
                      geographic.y, geographic.x));
      return {projected.x, projected.y};
    }
  if (context.spec.kind == projection_kind::voronoi)
    {
      using namespace a60::carto::voronoi_detail;
      const a60::carto::voronoi_detail::vector_3d value
        = a60::carto::voronoi_detail::geographic_vector(
            geographic.y, rotate_longitude(geographic.x));
      const face_geometry& face = layout().faces.at(face_index);
      const point_2d local = project_on_face(face, value);
      const point_2d transformed = apply(face.transform, local);
      return {transformed.x, -transformed.y};
    }
  throw std::logic_error("face-local projection requested for another net");
}

inline point
normalize_native_point(const projection_context& context, const point raw)
{
  if (context.spec.kind == projection_kind::myriahedral)
    {
      using namespace a60::carto::myriahedral_detail;
      const auto& layout = std::get<myriaproj>(context.projection).layout();
      const point_2d normalized = normalize_planar_point(layout, {raw.x, raw.y});
      return {normalized.x * context.map_frame.width(),
              normalized.y * context.map_frame.height()};
    }
  if (context.spec.kind == projection_kind::dymaxion)
    {
      const auto normalized
        = a60::carto::dymaxion_detail::normalize_planar_point({raw.x, raw.y});
      return {normalized.x * context.map_frame.width(),
              normalized.y * context.map_frame.height()};
    }
  if (context.spec.kind == projection_kind::voronoi)
    {
      using namespace a60::carto::voronoi_detail;
      static const point_2d registration = project_to_unfolded_net(
        0, registration_longitude_degrees);
      return {
        (source_center_x + source_scale * (raw.x - registration.x))
          / a60::carto::voronoi_source_width * context.map_frame.width(),
        (source_center_y - source_scale * (raw.y - registration.y))
          / a60::carto::voronoi_source_height * context.map_frame.height(),
      };
    }
  throw std::logic_error("native normalization requested for another net");
}

inline void
add_candidate_face(std::vector<std::size_t>& result,
                   const projection_context& context,
                   const point geographic)
{
  const std::size_t face = static_cast<std::size_t>(projection_cell(
    context, {geographic.y, geographic.x}));
  if (std::find(result.begin(), result.end(), face) == result.end())
    result.push_back(face);
}

inline std::vector<std::size_t>
candidate_faces(const polygon& geographic, const projection_context& context,
                const double west, const double south,
                const double cell_size)
{
  std::vector<std::size_t> result;
  for (const point value : geographic)
    add_candidate_face(result, context, value);
  const double sample_step = context.spec.kind == projection_kind::myriahedral
                               ? 0.5 : 1.0;
  const int samples = std::max(
    1, static_cast<int>(std::ceil(cell_size / sample_step)));
  for (int y = 0; y <= samples; ++y)
    for (int x = 0; x <= samples; ++x)
      add_candidate_face(
        result, context,
        {west + cell_size * static_cast<double>(x) / samples,
         south + cell_size * static_cast<double>(y) / samples});
  return result;
}

inline bool
is_triangle_net(const projection_context& context)
{
  return context.spec.kind == projection_kind::myriahedral
         || context.spec.kind == projection_kind::dymaxion
         || context.spec.kind == projection_kind::voronoi;
}

struct output_ring
{
  projected_path points;
  std::uint32_t native_cell;
};

inline std::vector<output_ring>
project_triangle_net_ring(const projection_context& context,
                          const polygon& source,
                          const slice_descriptor* slice)
{
  constexpr double cell_size = 5;
  const double sample_step
    = context.spec.kind == projection_kind::myriahedral ? 0.5 : 1.0;
  if (source.size() < 3)
    return {};
  double minimum_x = source.front().x;
  double maximum_x = source.front().x;
  double minimum_y = source.front().y;
  double maximum_y = source.front().y;
  for (const point value : source)
    {
      minimum_x = std::min(minimum_x, value.x);
      maximum_x = std::max(maximum_x, value.x);
      minimum_y = std::min(minimum_y, value.y);
      maximum_y = std::max(maximum_y, value.y);
    }
  const int first_x = std::max(
    -180, static_cast<int>(std::floor(minimum_x / cell_size))
            * static_cast<int>(cell_size));
  const int last_x = std::min(
    180, static_cast<int>(std::ceil(maximum_x / cell_size))
           * static_cast<int>(cell_size));
  const int first_y = std::max(
    -90, static_cast<int>(std::floor(minimum_y / cell_size))
           * static_cast<int>(cell_size));
  const int last_y = std::min(
    90, static_cast<int>(std::ceil(maximum_y / cell_size))
          * static_cast<int>(cell_size));
  std::vector<output_ring> result;
  for (int south = first_y; south < last_y;
       south += static_cast<int>(cell_size))
    for (int west = first_x; west < last_x;
         west += static_cast<int>(cell_size))
      {
        polygon cell = clip_to_rectangle(
          source, west, south, west + cell_size, south + cell_size);
        if (cell.size() < 3 || std::abs(signed_area(cell)) < 1e-14)
          continue;
        cell = densify(cell, sample_step);
        for (const std::size_t face
             : candidate_faces(cell, context, west, south, cell_size))
          {
            if (!slice_selects_cell(slice, static_cast<std::uint32_t>(face)))
              continue;
            polygon planar;
            planar.reserve(cell.size());
            bool finite = true;
            for (const point geographic : cell)
              {
                const point projected = project_on_native_face(
                  context, face, geographic);
                finite = finite && std::isfinite(projected.x)
                         && std::isfinite(projected.y);
                append_unique(planar, projected);
              }
            if (!finite)
              continue;
            const auto triangle_array = native_face_triangle(context, face);
            const polygon triangle {
              triangle_array[0], triangle_array[1], triangle_array[2],
            };
            polygon clipped = clip_to_convex_polygon(
              std::move(planar), triangle);
            if (clipped.size() < 3 || std::abs(signed_area(clipped)) < 1e-15)
              continue;
            polygon normalized;
            normalized.reserve(clipped.size());
            for (const point raw : clipped)
              append_unique(normalized, normalize_native_point(context, raw));
            if (normalized.size() >= 3)
              result.push_back({to_projected_path(normalized),
                                static_cast<std::uint32_t>(face)});
          }
      }
  return result;
}

inline std::vector<output_ring>
project_cahill_family_ring(const projection_context& context,
                           const polygon& source,
                           const slice_descriptor* slice)
{
  std::vector<output_ring> result;
  constexpr double seam_epsilon = 1e-7;
  for (const ck_sector sector : ck_sectors)
    for (const bool north : {true, false})
      {
        const std::uint32_t cell = north ? sector.north_cell
                                         : sector.south_cell;
        if (!slice_selects_cell(slice, cell))
          continue;
        polygon shifted = source;
        if (sector.west > 180 - 90)
          for (point& value : shifted)
            if (value.x < sector.west - 180)
              value.x += 360;
        const double south = north ? 0 : -90;
        const double north_bound = north ? 90 : 0;
        polygon clipped = clip_to_rectangle(
          shifted, sector.west + seam_epsilon, south,
          sector.east - seam_epsilon, north_bound);
        if (clipped.size() < 3 || std::abs(signed_area(clipped)) < 1e-14)
          continue;
        clipped = densify(clipped, 1);
        projected_path projected;
        projected.reserve(clipped.size());
        for (point value : clipped)
          {
            if (!north && std::abs(value.y) < seam_epsilon)
              value.y = -seam_epsilon;
            value.x = canonical_longitude(value.x);
            projection_runtime::append_unique(
              projected, project_point(context, {value.y, value.x}));
          }
        if (projected.size() >= 3)
          result.push_back({std::move(projected), cell});
      }
  return result;
}

inline polygon
unwrap_periodic_x(const projection_context& context, polygon value)
{
  if (value.empty())
    return value;
  const double width = context.map_frame.width();
  for (std::size_t index = 1; index < value.size(); ++index)
    {
      while (value[index].x - value[index - 1].x > width / 2)
        value[index].x -= width;
      while (value[index - 1].x - value[index].x > width / 2)
        value[index].x += width;
    }
  return value;
}

inline std::vector<output_ring>
project_authagraph_ring(const projection_context& context,
                        const polygon& source,
                        const slice_descriptor* slice)
{
  constexpr double cell_size = 5;
  std::vector<output_ring> result;
  if (source.size() < 3)
    return result;
  double minimum_x = source.front().x;
  double maximum_x = source.front().x;
  double minimum_y = source.front().y;
  double maximum_y = source.front().y;
  for (const point value : source)
    {
      minimum_x = std::min(minimum_x, value.x);
      maximum_x = std::max(maximum_x, value.x);
      minimum_y = std::min(minimum_y, value.y);
      maximum_y = std::max(maximum_y, value.y);
    }
  const int first_x = std::max(
    -180, static_cast<int>(std::floor(minimum_x / cell_size)) * 5);
  const int last_x = std::min(
    180, static_cast<int>(std::ceil(maximum_x / cell_size)) * 5);
  const int first_y = std::max(
    -90, static_cast<int>(std::floor(minimum_y / cell_size)) * 5);
  const int last_y = std::min(
    90, static_cast<int>(std::ceil(maximum_y / cell_size)) * 5);
  for (int south = first_y; south < last_y; south += 5)
    for (int west = first_x; west < last_x; west += 5)
      {
        polygon cell = clip_to_rectangle(
          source, west, south, west + cell_size, south + cell_size);
        if (cell.size() < 3 || std::abs(signed_area(cell)) < 1e-14)
          continue;
        cell = densify(cell, 0.5);
        polygon planar;
        planar.reserve(cell.size());
        for (const point geographic : cell)
          {
            const auto [x, y] = project_point(
              context, {geographic.y, geographic.x});
            append_unique(planar, {x, y});
          }
        planar = unwrap_periodic_x(context, std::move(planar));
        double center = 0;
        for (const point value : planar)
          center += value.x;
        center /= planar.size();
        const double base_shift = -std::round(
          center / context.map_frame.width()) * context.map_frame.width();
        for (const int copy : {-1, 0, 1})
          {
            polygon shifted = planar;
            const double shift = base_shift
                                 + copy * context.map_frame.width();
            for (point& value : shifted)
              value.x += shift;
            polygon clipped = clip_to_rectangle(
              shifted, 0, 0, context.map_frame.width(),
              context.map_frame.height());
            if (clipped.size() < 3
                || std::abs(signed_area(clipped)) < 1e-14)
              continue;
            const point geographic_center {
              west + cell_size / 2, south + cell_size / 2,
            };
            const std::uint32_t native_cell
              = static_cast<std::uint32_t>(projection_cell(
                  context, {geographic_center.y, geographic_center.x}));
            if (slice_selects_cell(slice, native_cell))
              result.push_back(
                {to_projected_path(clipped), native_cell});
          }
      }
  return result;
}

inline std::vector<output_ring>
project_ring(const projection_context& context, polygon source,
             const slice_descriptor* slice)
{
  if (slice != nullptr && slice->kind == slice_kind::geographic_preclip)
    source = clip_geographic_ring(source, *slice->geographic);
  if (source.size() < 3)
    return {};
  if (is_triangle_net(context))
    return project_triangle_net_ring(context, source, slice);
  if (context.spec.kind == projection_kind::cahill_keyes
      || context.spec.kind == projection_kind::star_x)
    return project_cahill_family_ring(context, source, slice);
  return project_authagraph_ring(context, source, slice);
}

inline void
add_diagnostics(geometry_diagnostics& destination,
                const path_diagnostics& source)
{
  destination.sampled_points += source.sampled_points;
  destination.cell_transitions += source.cell_transitions;
  destination.cuts += source.cuts;
  destination.periodic_wraps += source.periodic_wraps;
  destination.fallback_splits += source.fallback_splits;
}

inline projected_view
output_view(const projection_context& context,
            const slice_descriptor* slice)
{
  return slice == nullptr ? full_carrier_view(context) : slice->source_view;
}

inline bool
inside_view(const point value, const projected_view view)
{
  return value.x >= view.x - epsilon
         && value.x <= view.x + view.width + epsilon
         && value.y >= view.y - epsilon
         && value.y <= view.y + view.height + epsilon;
}

inline void
append_output_part(geometry_command_buffer& output,
                   const projected_path& source,
                   const geometry_part_type type,
                   const std::uint32_t feature_id,
                   const std::uint32_t native_cell,
                   const ring_role role, const bool closed,
                   const projected_view view)
{
  if ((type == geometry_part_type::point && source.empty())
      || (type == geometry_part_type::line && source.size() < 2)
      || (type == geometry_part_type::ring && source.size() < 3))
    return;
  for (const auto [x, y] : source)
    {
      output.coordinates.push_back(x - view.x);
      output.coordinates.push_back(y - view.y);
    }
  output.part_offsets.push_back(
    static_cast<std::uint32_t>(output.coordinates.size() / 2));
  output.part_types.push_back(type);
  output.feature_ids.push_back(feature_id);
  output.native_cells.push_back(native_cell);
  output.component_ids.push_back(
    static_cast<std::uint32_t>(output.component_ids.size()));
  output.ring_roles.push_back(role);
  output.closed.push_back(closed ? 1 : 0);
  output.diagnostics.output_vertices += static_cast<std::uint32_t>(source.size());
  ++output.diagnostics.output_parts;
}

inline void
append_planar_clipped_part(geometry_command_buffer& output,
                           const projected_path& source,
                           const geometry_part_type type,
                           const std::uint32_t feature_id,
                           const std::uint32_t native_cell,
                           const ring_role role, const bool closed,
                           const projected_view view)
{
  if (type == geometry_part_type::point)
    {
      projected_path retained;
      for (const auto [x, y] : source)
        if (inside_view({x, y}, view))
          retained.emplace_back(x, y);
      if (retained.size() != source.size())
        ++output.diagnostics.clipped_parts;
      append_output_part(output, retained, type, feature_id, native_cell,
                         role, false, view);
      return;
    }
  if (type == geometry_part_type::line)
    {
      const std::vector<projected_path> clipped = clip_polyline(source, view);
      if (clipped.size() != 1 || clipped.front() != source)
        ++output.diagnostics.clipped_parts;
      for (const projected_path& piece : clipped)
        append_output_part(output, piece, type, feature_id, native_cell,
                           role, false, view);
      return;
    }
  polygon clipped = clip_to_rectangle(
    from_projected_path(source), view.x, view.y,
    view.x + view.width, view.y + view.height);
  if (clipped.size() != source.size())
    ++output.diagnostics.clipped_parts;
  append_output_part(output, to_projected_path(clipped), type, feature_id,
                     native_cell, role, closed, view);
}

} // namespace geometry_detail

inline void
validate_geometry_input(const geometry_input& input)
{
  if (input.part_offsets.empty() || input.part_offsets.front() != 0
      || input.part_offsets.back() != input.coordinates.size())
    throw std::invalid_argument(
      "geometry part offsets must start at zero and end at point count");
  const std::size_t parts = input.part_offsets.size() - 1;
  if (input.part_types.size() != parts
      || (!input.feature_ids.empty() && input.feature_ids.size() != parts)
      || (!input.ring_roles.empty() && input.ring_roles.size() != parts))
    throw std::invalid_argument(
      "geometry metadata arrays must match the number of parts");
  for (std::size_t part = 0; part < parts; ++part)
    {
      if (input.part_offsets[part] > input.part_offsets[part + 1]
          || input.part_offsets[part + 1] > input.coordinates.size())
        throw std::invalid_argument("geometry part offsets are not ordered");
      const std::size_t points
        = input.part_offsets[part + 1] - input.part_offsets[part];
      if ((input.part_types[part] == geometry_part_type::point && points < 1)
          || (input.part_types[part] == geometry_part_type::line && points < 2)
          || (input.part_types[part] == geometry_part_type::ring && points < 3))
        throw std::invalid_argument(
          "geometry part does not contain enough coordinates");
    }
  for (const geographic_point point : input.coordinates)
    validate_geographic_point(point);
}

inline void
validate_geometry_options(const geometry_options& options)
{
  if (!std::isfinite(options.tolerance_pixels)
      || options.tolerance_pixels <= 0
      || !std::isfinite(options.maximum_angular_step)
      || options.maximum_angular_step <= 0
      || options.maximum_angular_step > 180
      || options.maximum_subdivision_depth == 0
      || options.maximum_subdivision_depth > 24)
    throw std::invalid_argument("invalid geometry sampling options");
}

inline geometry_command_buffer
project_geometry(const projection_context& context,
                 const geometry_input& input,
                 const geometry_options& options = {})
{
  using namespace geometry_detail;
  validate_geometry_input(input);
  validate_geometry_options(options);
  const slice_descriptor* slice
    = options.slice ? &*options.slice : nullptr;
  if (slice != nullptr && slice->projection != context.spec.argument
      && slice->projection != projection_kind_name(context.spec.kind))
    throw std::invalid_argument(
      "slice projection does not match the active carrier");
  const projected_view view = output_view(context, slice);
  if (!valid_view(context, view))
    throw std::invalid_argument("geometry output view is outside the carrier");

  geometry_command_buffer output;
  output.origin_x = view.x;
  output.origin_y = view.y;
  output.width = view.width;
  output.height = view.height;
  output.diagnostics.input_points
    = static_cast<std::uint32_t>(input.coordinates.size());
  output.diagnostics.input_parts
    = static_cast<std::uint32_t>(input.part_types.size());

  for (std::size_t part = 0; part < input.part_types.size(); ++part)
    {
      const auto begin = input.coordinates.begin() + input.part_offsets[part];
      const auto end = input.coordinates.begin() + input.part_offsets[part + 1];
      std::vector<geographic_point> source(begin, end);
      if (source.size() > 1
          && source.front().latitude == source.back().latitude
          && source.front().longitude == source.back().longitude)
        source.pop_back();
      const std::uint32_t feature_id = input.feature_ids.empty()
        ? static_cast<std::uint32_t>(part) : input.feature_ids[part];
      const ring_role role = input.ring_roles.empty()
        ? (input.part_types[part] == geometry_part_type::ring
             ? ring_role::exterior : ring_role::none)
        : input.ring_roles[part];

      if (input.part_types[part] == geometry_part_type::point)
        {
          projected_path points;
          std::uint32_t first_cell = std::numeric_limits<std::uint32_t>::max();
          for (const geographic_point geographic : source)
            {
              if (slice != nullptr
                  && slice->kind == slice_kind::geographic_preclip)
                {
                  const geographic_bounds bounds = *slice->geographic;
                  if (geographic.longitude < bounds.west
                      || geographic.longitude > bounds.east
                      || geographic.latitude < bounds.south
                      || geographic.latitude > bounds.north)
                    continue;
                }
              const std::uint32_t cell = static_cast<std::uint32_t>(
                projection_cell(context, geographic));
              if (!slice_selects_cell(slice, cell))
                continue;
              if (first_cell == std::numeric_limits<std::uint32_t>::max())
                first_cell = cell;
              projection_runtime::append_unique(
                points, project_point(context, geographic));
            }
          append_planar_clipped_part(
            output, points, geometry_part_type::point, feature_id,
            first_cell, ring_role::none, false, view);
          if (points.empty())
            ++output.diagnostics.dropped_parts;
          continue;
        }

      if (input.part_types[part] == geometry_part_type::line)
        {
          std::vector<std::vector<geographic_point>> geographic_pieces;
          if (slice != nullptr
              && slice->kind == slice_kind::geographic_preclip)
            geographic_pieces = clip_geographic_line(
              source, *slice->geographic);
          else
            geographic_pieces.push_back(std::move(source));
          const std::uint32_t before = output.diagnostics.output_parts;
          for (const std::vector<geographic_point>& geographic
               : geographic_pieces)
            {
              std::vector<geographic_point> sampled = adaptive_sample(
                context, geographic, false, options);
              projected_path_result projected = project_path_detailed(
                context, std::move(sampled), false,
                slice != nullptr
                  && slice->kind == slice_kind::native_cell_mask);
              add_diagnostics(output.diagnostics, projected.diagnostics);
              for (const projected_path_piece& piece : projected.pieces)
                if (slice_selects_cell(slice, piece.native_cell))
                  append_planar_clipped_part(
                    output, piece.points, geometry_part_type::line,
                    feature_id, piece.native_cell, ring_role::none,
                    false, view);
            }
          if (output.diagnostics.output_parts == before)
            ++output.diagnostics.dropped_parts;
          continue;
        }

      const std::uint32_t before = output.diagnostics.output_parts;
      for (const output_ring& ring
           : project_ring(context, to_polygon(source), slice))
        append_planar_clipped_part(
          output, ring.points, geometry_part_type::ring, feature_id,
          ring.native_cell, role, true, view);
      if (output.diagnostics.output_parts == before)
        ++output.diagnostics.dropped_parts;
    }
  return output;
}

/// Exact finite-carrier face geometry, primarily for an ocean/background
/// layer. It uses the same command protocol as arbitrary projected features.
inline geometry_command_buffer
carrier_geometry(const projection_context& context,
                 const std::optional<slice_descriptor>& selected_slice
                   = std::nullopt)
{
  using namespace geometry_detail;
  const slice_descriptor* slice
    = selected_slice ? &*selected_slice : nullptr;
  const projected_view view = output_view(context, slice);
  geometry_command_buffer output;
  output.origin_x = view.x;
  output.origin_y = view.y;
  output.width = view.width;
  output.height = view.height;

  if (is_triangle_net(context))
    {
      for (std::size_t cell = 0; cell < context.spec.native_cell_count; ++cell)
        {
          if (!slice_selects_cell(slice, static_cast<std::uint32_t>(cell)))
            continue;
          const auto raw = native_face_triangle(context, cell);
          projected_path triangle;
          triangle.reserve(3);
          for (const point value : raw)
            {
              const point normalized = normalize_native_point(context, value);
              triangle.emplace_back(normalized.x, normalized.y);
            }
          append_planar_clipped_part(
            output, triangle, geometry_part_type::ring, 0,
            static_cast<std::uint32_t>(cell), ring_role::exterior, true, view);
        }
    }
  else if (context.spec.kind == projection_kind::cahill_keyes
           || context.spec.kind == projection_kind::star_x)
    {
      for (const ck_sector sector : ck_sectors)
        for (const bool north : {true, false})
          {
            const std::uint32_t cell = north ? sector.north_cell
                                             : sector.south_cell;
            if (!slice_selects_cell(slice, cell))
              continue;
            const projected_path outline = make_ck_octant_outline(
              context, sector, north);
            append_planar_clipped_part(
              output, outline, geometry_part_type::ring, 0, cell,
              ring_role::exterior, true, view);
          }
    }
  else
    {
      const projected_path rectangle_path {
        {0, 0}, {context.map_frame.width(), 0},
        {context.map_frame.width(), context.map_frame.height()},
        {0, context.map_frame.height()},
      };
      append_planar_clipped_part(
        output, rectangle_path, geometry_part_type::ring, 0, 0,
        ring_role::exterior, true, view);
    }
  return output;
}

} // namespace cart0freak0::projection_runtime

#endif
