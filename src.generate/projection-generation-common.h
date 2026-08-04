// Shared configuration and seam-safe path projection for SVG generators.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_TESTS_PROJECTION_GENERATION_COMMON_H
#define CART0FREAK0_TESTS_PROJECTION_GENERATION_COMMON_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <variant>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-authagraph.h"
#include "cart0freak0-cahill-keyes.h"
#include "cart0freak0-myriahedral.h"
#include "cart0freak0-star-x.h"
#include "cart0freak0-voronoi.h"
#include "myriahedral-perspective-generation.h"

namespace cart0freak0::generation {

using a60::carto::agproj;
using a60::carto::ckproj;
using a60::carto::frame;
using a60::carto::myriaproj;
using a60::carto::starxproj;
using a60::carto::voronoiproj;

/// Physical unit for print-oriented generated map documents. Projection and
/// viewBox coordinates remain unitless, with one coordinate unit per inch.
inline constexpr svg::unit projection_document_unit = svg::unit::inch;

/// Root SVG document whose frame dimensions are physical print dimensions.
struct projection_document : svg::svg_element
{
  projection_document(const std::string& name,
                      const std::string& description,
                      const frame::area& document_area,
                      const bool lifetime = true)
  : svg::svg_element(
      name, document_area, lifetime, projection_document_unit)
  {
    if (lifetime)
      add_desc(description);
  }
};

enum class projection_kind
{
  cahill_keyes,
  authagraph,
  myriahedral,
  star_x,
  voronoi,
};

struct projection_spec
{
  projection_kind kind;
  std::string_view argument;
  std::string_view title;
  std::string_view output_tag;
  double width;
  double height;
  myriahedral_generation::perspective myriahedral_perspective
    = myriahedral_generation::perspective::reference;
};

inline constexpr std::array projection_specs {
  projection_spec {
    projection_kind::cahill_keyes,
    "cahill-keyes", "Cahill-Keyes", "ck-44-22", 44, 22,
  },
  projection_spec {
    projection_kind::authagraph,
    "authagraph", "AuthaGraph", "authagraph-44-19.052559",
    44, 44 / a60::carto::authagraph_width_to_height_ratio,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral", "Myriahedral", "myriahedral-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-americas", "Myriahedral Americas perspective",
    "myriahedral-americas-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
    myriahedral_generation::perspective::americas,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-atlantic", "Myriahedral Atlantic perspective",
    "myriahedral-atlantic-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
    myriahedral_generation::perspective::atlantic,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-afro-eur-asia", "Myriahedral Afro Eur Asia perspective",
    "myriahedral-afro-eur-asia-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
    myriahedral_generation::perspective::afro_eur_asia,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-pacific", "Myriahedral Pacific perspective",
    "myriahedral-pacific-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
    myriahedral_generation::perspective::pacific,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-antarctic", "Myriahedral Antarctic perspective",
    "myriahedral-antarctic-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio,
    myriahedral_generation::perspective::antarctic,
  },
  projection_spec {
    projection_kind::star_x,
    "star-x", "Star-X", "star-x-34-44",
    44 * a60::carto::star_x_width_to_height_ratio, 44,
  },
  projection_spec {
    projection_kind::voronoi,
    "voronoi", "Voronoi", "voronoi-44-22.916667",
    44, 44 / a60::carto::voronoi_width_to_height_ratio,
  },
};

inline void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline const projection_spec&
find_projection_spec(const std::string_view argument)
{
  const std::string_view canonical = argument == "ck" ? "cahill-keyes"
                                     : argument == "starx" ? "star-x"
                                     : argument == "voroni" ? "voronoi"
                                     : argument;
  for (const projection_spec& spec : projection_specs)
    if (spec.argument == canonical)
      return spec;
  throw std::invalid_argument(
    "unknown projection '" + std::string(argument)
    + "' (use a configured projection argument)");
}

inline const projection_spec&
projection_from_arguments(const int argc, char** argv)
{
  if (argc == 1)
    return projection_specs.front();
  if (argc == 2)
    return find_projection_spec(argv[1]);
  throw std::invalid_argument(
    "generator accepts at most one projection argument");
}

inline frame
make_frame(const projection_spec& spec)
{ return {spec.width, spec.height}; }

inline bool
has_valid_frame(const projection_spec& spec, const frame& candidate)
{
  switch (spec.kind)
    {
    case projection_kind::cahill_keyes:
      return a60::carto::is_cahill_keyes_frame(candidate);
    case projection_kind::authagraph:
      return a60::carto::is_authagraph_frame(candidate);
    case projection_kind::myriahedral:
      return a60::carto::is_myriahedral_frame(candidate);
    case projection_kind::star_x:
      return a60::carto::is_star_x_frame(candidate);
    case projection_kind::voronoi:
      return a60::carto::is_voronoi_frame(candidate);
    }
  return false;
}

inline std::string
output_basename(const std::string_view artifact,
                const projection_spec& spec)
{
  return std::string(artifact) + "-" + std::string(spec.output_tag);
}

using projection_variant = std::variant<
  ckproj, agproj, myriaproj, starxproj, voronoiproj>;

inline projection_variant
make_projection(const projection_spec& spec, const frame& map_frame,
                const std::string& raster_name)
{
  switch (spec.kind)
    {
    case projection_kind::cahill_keyes:
      return a60::carto::make_cahill_keyes_projection(
        map_frame, raster_name);
    case projection_kind::authagraph:
      return a60::carto::make_authagraph_projection(map_frame, raster_name);
    case projection_kind::myriahedral:
      return a60::carto::make_myriahedral_projection(
        map_frame,
        myriahedral_generation::layout(spec.myriahedral_perspective),
        raster_name);
    case projection_kind::star_x:
      return a60::carto::make_star_x_projection(map_frame, raster_name);
    case projection_kind::voronoi:
      return a60::carto::make_voronoi_projection(map_frame, raster_name);
    }
  throw std::logic_error("unhandled projection kind");
}

struct projection_context
{
  const projection_spec& spec;
  frame map_frame;
  projection_variant projection;

  projection_context(const projection_spec& value,
                     const std::string& raster_name)
  : spec(value), map_frame(make_frame(value)),
    projection(make_projection(value, map_frame, raster_name))
  {
    require(has_valid_frame(spec, map_frame),
            std::string(spec.title) + " generator frame has the wrong ratio");
    constexpr double tolerance = 1e-12;
    require(map_frame.width() <= 44 + tolerance
            && map_frame.height() <= 44 + tolerance
            && (std::abs(map_frame.width() - 44) <= tolerance
                || std::abs(map_frame.height() - 44) <= tolerance),
            std::string(spec.title)
              + " generator frame must have a largest dimension of 44");
  }
};

struct geographic_point
{
  double latitude;
  double longitude;
};

inline svg::point_2t
project_point(const projection_context& context,
              const geographic_point point)
{
  const double latitude = std::clamp(point.latitude, -90.0, 90.0);
  const double longitude = std::clamp(point.longitude, -180.0, 180.0);
  const auto [x, y] = std::visit(
    [latitude, longitude](const auto& projection) {
      return projection.meridians_to_point_2d(latitude, longitude);
    }, context.projection);
  constexpr double tolerance = 1e-7;
  require(std::isfinite(x) && std::isfinite(y),
          std::string(context.spec.title)
            + " projection produced a non-finite point");
  require(x >= -tolerance
          && x <= context.map_frame.width() + tolerance
          && y >= -tolerance
          && y <= context.map_frame.height() + tolerance,
          std::string(context.spec.title)
            + " projection produced a point outside its frame");
  return {std::clamp(x, 0.0, context.map_frame.width()),
          std::clamp(y, 0.0, context.map_frame.height())};
}

inline double
point_distance(const svg::point_2t left, const svg::point_2t right)
{
  const double dx = std::get<0>(right) - std::get<0>(left);
  const double dy = std::get<1>(right) - std::get<1>(left);
  return std::hypot(dx, dy);
}

inline geographic_point
interpolate(const geographic_point left, const geographic_point right,
            const double fraction)
{
  return {left.latitude + fraction * (right.latitude - left.latitude),
          left.longitude + fraction * (right.longitude - left.longitude)};
}

inline std::uint64_t
authagraph_cell(const geographic_point point)
{
  using namespace a60::carto::authagraph_detail;
  const vector_3d geographic = longitude_latitude_to_vector(
    degrees_to_radians(point.longitude),
    degrees_to_radians(point.latitude));
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
  const point_2d local = local_longitude_latitude(
    geographic, vertices[closest], vertices[(closest + 1) % vertices.size()]);
  const triangle_projection triangle = project_spherical_triangle(local);
  return closest * 6 + static_cast<std::size_t>(triangle.sector);
}

inline std::uint64_t
cahill_keyes_cell(const geographic_point point)
{
  double longitude = point.longitude;
  while (longitude < 159)
    longitude += 360;
  while (longitude >= 519)
    longitude -= 360;
  const auto sector = static_cast<std::uint64_t>(
    std::clamp(static_cast<int>((longitude - 159) / 90), 0, 3));
  return sector + (point.latitude < 0 ? 4 : 0);
}

inline std::uint64_t
projection_cell(const projection_context& context,
                const geographic_point point)
{
  switch (context.spec.kind)
    {
    case projection_kind::cahill_keyes:
    case projection_kind::star_x:
      return cahill_keyes_cell(point);
    case projection_kind::authagraph:
      return authagraph_cell(point);
    case projection_kind::myriahedral:
      return a60::carto::myriahedral_detail::containing_face(
        a60::carto::myriahedral_detail::geographic_vector(
          point.latitude, point.longitude));
    case projection_kind::voronoi:
      {
        const double longitude
          = a60::carto::voronoi_detail::rotate_longitude(point.longitude);
        return a60::carto::voronoi_detail::containing_face(
          a60::carto::voronoi_detail::geographic_vector(
            point.latitude, longitude));
      }
    }
  throw std::logic_error("unhandled projection kind");
}

struct projected_transition
{
  svg::point_2t left;
  svg::point_2t right;
  geographic_point geographic_right;
  bool is_cut;
};

inline projected_transition
find_cell_transition(const projection_context& context,
                     geographic_point left, geographic_point right,
                     const std::uint64_t left_cell)
{
  // Locate the first boundary after the left endpoint. The remaining interval
  // can contain more transitions; project_path resumes from geographic_right
  // until it reaches the endpoint cell. The limiting points eliminate a
  // visible sampling gap at a retained hinge and expose a true unfolded cut.
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      if (projection_cell(context, middle) == left_cell)
        left = middle;
      else
        right = middle;
    }
  const svg::point_2t projected_left = project_point(context, left);
  const svg::point_2t projected_right = project_point(context, right);
  const double maximum_dimension = std::max(
    context.map_frame.width(), context.map_frame.height());
  return {projected_left, projected_right, right,
          point_distance(projected_left, projected_right)
            > maximum_dimension * 1e-5};
}

inline projected_transition
find_coordinate_wrap(const projection_context& context,
                     geographic_point left, geographic_point right)
{
  svg::point_2t projected_left = project_point(context, left);
  svg::point_2t projected_right = project_point(context, right);
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      const svg::point_2t projected_middle = project_point(context, middle);
      if (point_distance(projected_left, projected_middle)
          > point_distance(projected_middle, projected_right))
        {
          right = middle;
          projected_right = projected_middle;
        }
      else
        {
          left = middle;
          projected_left = projected_middle;
        }
    }
  return {projected_left, projected_right, right, true};
}

inline void
append_unique(svg::vrange& points, const svg::point_2t point)
{
  if (points.empty() || points.back() != point)
    points.push_back(point);
}

inline std::vector<svg::vrange>
project_path(const projection_context& context,
             std::vector<geographic_point> source, const bool closed)
{
  std::vector<svg::vrange> result;
  if (source.empty())
    return result;
  if (source.size() > 1
      && source.front().latitude == source.back().latitude
      && source.front().longitude == source.back().longitude)
    source.pop_back();
  if (source.empty())
    return result;

  svg::vrange current;
  append_unique(current, project_point(context, source.front()));
  const std::size_t edge_count = closed ? source.size() : source.size() - 1;
  for (std::size_t index = 0; index < edge_count; ++index)
    {
      geographic_point left = source[index];
      const geographic_point right = source[(index + 1) % source.size()];
      const svg::point_2t projected_right = project_point(context, right);
      std::uint64_t left_cell = projection_cell(context, left);
      const std::uint64_t right_cell = projection_cell(context, right);

      // Densification normally leaves at most one native-cell boundary per
      // source edge, but an edge passing close to a mesh vertex can cross two
      // or more tiny faces. Consume the first transition repeatedly instead
      // of joining the first neighbor directly to the endpoint face.
      constexpr std::size_t maximum_transitions_per_edge = 64;
      std::size_t transition_count = 0;
      while (left_cell != right_cell)
        {
          require(++transition_count <= maximum_transitions_per_edge,
                  std::string(context.spec.title)
                    + " path edge crosses too many native cells");
          const projected_transition transition = find_cell_transition(
            context, left, right, left_cell);
          append_unique(current, transition.left);
          if (transition.is_cut)
            {
              if (current.size() >= 2)
                result.push_back(std::move(current));
              current.clear();
            }
          append_unique(current, transition.right);

          left = transition.geographic_right;
          const std::uint64_t next_cell = projection_cell(context, left);
          require(next_cell != left_cell,
                  std::string(context.spec.title)
                    + " path transition did not enter a new native cell");
          left_cell = next_cell;
        }

      const double maximum_dimension = std::max(
        context.map_frame.width(), context.map_frame.height());
      if (point_distance(current.back(), projected_right)
          > maximum_dimension / 3)
        {
          const projected_transition transition
            = find_coordinate_wrap(context, left, right);
          append_unique(current, transition.left);
          if (current.size() >= 2)
            result.push_back(std::move(current));
          current.clear();
          append_unique(current, transition.right);
        }
      append_unique(current, projected_right);
    }

  if (!current.empty())
    result.push_back(std::move(current));

  // A closed ring can begin in the middle of one projected fragment. Merge
  // the tail and head created solely by choosing that geographic start point.
  if (closed && result.size() > 1
      && !result.front().empty() && !result.back().empty()
      && result.back().back() == result.front().front())
    {
      svg::vrange merged = std::move(result.back());
      result.pop_back();
      for (std::size_t index = 1; index < result.front().size(); ++index)
        append_unique(merged, result.front()[index]);
      result.front() = std::move(merged);
    }

  for (svg::vrange& points : result)
    if (closed && points.size() > 1 && points.front() == points.back())
      points.pop_back();
  return result;
}

inline std::string
view_box_fragment(const projection_context& context)
{
  char buffer[128] {};
  const int written = std::snprintf(
    buffer, sizeof(buffer), "viewBox=\"0 0 %.6f %.6f\"",
    context.map_frame.width(), context.map_frame.height());
  require(written > 0 && static_cast<std::size_t>(written) < sizeof(buffer),
          "could not format SVG viewBox");
  return buffer;
}

} // namespace cart0freak0::generation

#endif
