// Projection-neutral runtime registry and seam-safe geometry core.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_PROJECTION_RUNTIME_H
#define CART0FREAK0_PROJECTION_RUNTIME_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <variant>
#include <vector>

#if __has_include(<a60-numeric.h>)
#include <a60-numeric.h>
#endif
#if __has_include(<a60-countries.h>)
#include <a60-countries.h>
#endif
#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto.h"
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-dymaxion.h"
#include "cart0freak0-authagraph.h"
#include "cart0freak0-cahill-keyes-functions.h"
#include "cart0freak0-cahill-keyes.h"
#include "cart0freak0-myriahedral-perspectives.h"
#include "cart0freak0-myriahedral.h"
#include "cart0freak0-star-x-functions.h"
#include "cart0freak0-star-x.h"
#include "cart0freak0-voronoi.h"

/**
 * @file cart0freak0-projection-runtime.h
 * Runtime projection selection and topology-aware path projection shared by
 * native generators and WebAssembly clients.
 *
 * The public JavaScript API selects projections by identifier, but C++ keeps
 * concrete projection types in a closed `std::variant`. This gives one
 * registry and one seam policy without virtual calls per source coordinate.
 */
namespace cart0freak0::projection_runtime {

using a60::carto::agproj;
using a60::carto::ckproj;
using a60::carto::dymaxionproj;
using a60::carto::frame;
using a60::carto::myriaproj;
using a60::carto::starxproj;
using a60::carto::voronoiproj;

/// Version of the projection descriptor and flat geometry protocol.
inline constexpr std::uint32_t abi_version = 1;

/// Stable identifiers for the six supported projection families.
enum class projection_kind
{
  cahill_keyes,
  authagraph,
  dymaxion,
  myriahedral,
  star_x,
  voronoi,
};

/// Carrier topology used to choose the runtime seam-splitting policy.
enum class topology_kind
{
  folded,
  periodic,
  polyhedral,
};

/// Registry record for one projection and layout.
struct projection_spec
{
  projection_kind kind;
  std::string_view argument;
  std::string_view title;
  std::string_view output_tag;
  double width;
  double height;
  std::size_t native_cell_count;
  topology_kind topology;
  myriahedral_generation::perspective myriahedral_perspective
    = myriahedral_generation::perspective::reference;
};

/// Six reference models plus the five checked Myriahedral layouts.
inline constexpr std::array projection_specs {
  projection_spec {
    projection_kind::cahill_keyes,
    "cahill-keyes", "Cahill-Keyes", "ck-44-22", 44, 22, 8,
    topology_kind::folded,
  },
  projection_spec {
    projection_kind::authagraph,
    "authagraph", "AuthaGraph", "authagraph-44-19.052559",
    44, 44 / a60::carto::authagraph_width_to_height_ratio, 24,
    topology_kind::periodic,
  },
  projection_spec {
    projection_kind::dymaxion,
    "dymaxion", "Dymaxion", "dymaxion-44-20.78461",
    44, 44 / a60::carto::dymaxion_width_to_height_ratio, 23,
    topology_kind::polyhedral,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral", "Myriahedral", "myriahedral-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-americas", "Myriahedral Americas perspective",
    "myriahedral-americas-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
    myriahedral_generation::perspective::americas,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-atlantic", "Myriahedral Atlantic perspective",
    "myriahedral-atlantic-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
    myriahedral_generation::perspective::atlantic,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-afro-eur-asia",
    "Myriahedral Afro Eur Asia perspective",
    "myriahedral-afro-eur-asia-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
    myriahedral_generation::perspective::afro_eur_asia,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-pacific", "Myriahedral Pacific perspective",
    "myriahedral-pacific-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
    myriahedral_generation::perspective::pacific,
  },
  projection_spec {
    projection_kind::myriahedral,
    "myriahedral-antarctic", "Myriahedral Antarctic perspective",
    "myriahedral-antarctic-44-24.75",
    44, 44 / a60::carto::myriahedral_width_to_height_ratio, 5120,
    topology_kind::polyhedral,
    myriahedral_generation::perspective::antarctic,
  },
  projection_spec {
    projection_kind::star_x,
    "star-x", "Star-X", "star-x-34-44",
    44 * a60::carto::star_x_width_to_height_ratio, 44, 8,
    topology_kind::folded,
  },
  projection_spec {
    projection_kind::voronoi,
    "voronoi", "Voronoi", "voronoi-44-22.916667",
    44, 44 / a60::carto::voronoi_width_to_height_ratio, 20,
    topology_kind::polyhedral,
  },
};

inline constexpr std::array<std::string_view, 6> reference_projection_ids {
  "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
  "voronoi",
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
    + "' (use cahill-keyes, authagraph, dymaxion, myriahedral, "
      "star-x, or voronoi)");
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
    case projection_kind::dymaxion:
      return a60::carto::is_dymaxion_frame(candidate);
    case projection_kind::myriahedral:
      return a60::carto::is_myriahedral_frame(candidate);
    case projection_kind::star_x:
      return a60::carto::is_star_x_frame(candidate);
    case projection_kind::voronoi:
      return a60::carto::is_voronoi_frame(candidate);
    }
  return false;
}

using projection_variant = std::variant<
  ckproj, agproj, dymaxionproj, myriaproj, starxproj, voronoiproj>;

inline projection_variant
make_projection(const projection_spec& spec, const frame& map_frame,
                const std::string& raster_name = {})
{
  switch (spec.kind)
    {
    case projection_kind::cahill_keyes:
      return a60::carto::make_cahill_keyes_projection(
        map_frame, raster_name);
    case projection_kind::authagraph:
      return a60::carto::make_authagraph_projection(map_frame, raster_name);
    case projection_kind::dymaxion:
      return a60::carto::make_dymaxion_projection(map_frame, raster_name);
    case projection_kind::myriahedral:
      return a60::carto::make_myriahedral_projection(
        map_frame, myriahedral_generation::layout(
          spec.myriahedral_perspective), raster_name);
    case projection_kind::star_x:
      return a60::carto::make_star_x_projection(map_frame, raster_name);
    case projection_kind::voronoi:
      return a60::carto::make_voronoi_projection(map_frame, raster_name);
    }
  throw std::logic_error("unhandled projection kind");
}

/// Complete runtime projection on a valid full carrier.
struct projection_context
{
  const projection_spec& spec;
  frame map_frame;
  projection_variant projection;

  projection_context(const projection_spec& value,
                     const std::string& raster_name = {})
  : projection_context(value, make_frame(value), raster_name)
  { }

  projection_context(const projection_spec& value, const frame& carrier,
                     const std::string& raster_name = {})
  : spec(value), map_frame(carrier),
    projection(make_projection(value, map_frame, raster_name))
  {
    if (!has_valid_frame(spec, map_frame))
      throw std::invalid_argument(
        std::string(spec.title)
        + " carrier has non-finite, non-positive, or incorrect-ratio "
          "dimensions");
  }
};

/// Geographic latitude/longitude pair in decimal degrees on WGS 84.
struct geographic_point
{
  double latitude;
  double longitude;
};

using projected_point = a60::point_2t;
using projected_path = std::vector<projected_point>;

inline void
validate_geographic_point(const geographic_point point)
{
  if (!std::isfinite(point.latitude) || point.latitude < -90
      || point.latitude > 90)
    throw std::invalid_argument("latitude must be finite and within [-90, 90]");
  if (!std::isfinite(point.longitude) || point.longitude < -180
      || point.longitude > 180)
    throw std::invalid_argument(
      "longitude must be finite and within [-180, 180]");
}

inline projected_point
project_point(const projection_context& context,
              const geographic_point point)
{
  validate_geographic_point(point);
  const auto [x, y] = std::visit(
    [point](const auto& projection) {
      return projection.meridians_to_point_2d(
        point.latitude, point.longitude);
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
point_distance(const projected_point left, const projected_point right)
{
  return std::hypot(std::get<0>(right) - std::get<0>(left),
                    std::get<1>(right) - std::get<1>(left));
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
  const int octant = a60::carto::cahill_keyes_registered_octant(
    point.longitude);
  const auto sector = static_cast<std::uint64_t>(octant - 1);
  return sector + (point.latitude < 0 ? 4 : 0);
}

inline std::uint64_t
projection_cell(const projection_context& context,
                const geographic_point point)
{
  validate_geographic_point(point);
  switch (context.spec.kind)
    {
    case projection_kind::cahill_keyes:
      return cahill_keyes_cell(point);
    case projection_kind::star_x:
      return a60::carto::star_x_path_detail::path_cell(
        {point.latitude, point.longitude});
    case projection_kind::authagraph:
      return authagraph_cell(point);
    case projection_kind::dymaxion:
      return a60::carto::dymaxion_detail::containing_face(
        a60::carto::dymaxion_detail::geographic_vector(
          point.latitude, point.longitude));
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

/// Counters describing adaptive sampling and seam decisions for one path.
struct path_diagnostics
{
  std::uint32_t input_points = 0;
  std::uint32_t sampled_points = 0;
  std::uint32_t cell_transitions = 0;
  std::uint32_t cuts = 0;
  std::uint32_t periodic_wraps = 0;
  std::uint32_t fallback_splits = 0;
};

/// One continuous projected segment associated with a native carrier cell.
struct projected_path_piece
{
  projected_path points;
  std::uint32_t native_cell = 0;
  bool closed = false;
};

/// Seam-safe path pieces together with their construction diagnostics.
struct projected_path_result
{
  std::vector<projected_path_piece> pieces;
  path_diagnostics diagnostics;
};

/// Refined left/right samples bracketing a native-cell transition.
struct projected_transition
{
  projected_point left;
  projected_point right;
  geographic_point geographic_right;
  std::uint64_t right_cell;
  bool is_cut;
};

inline projected_transition
find_cell_transition(const projection_context& context,
                     geographic_point left, geographic_point right,
                     const std::uint64_t left_cell)
{
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      if (projection_cell(context, middle) == left_cell)
        left = middle;
      else
        right = middle;
    }
  const projected_point projected_left = project_point(context, left);
  const projected_point projected_right = project_point(context, right);
  const double maximum_dimension = std::max(
    context.map_frame.width(), context.map_frame.height());
  return {projected_left, projected_right, right,
          projection_cell(context, right),
          point_distance(projected_left, projected_right)
            > maximum_dimension * 1e-5};
}

inline projected_transition
find_coordinate_wrap(const projection_context& context,
                     geographic_point left, geographic_point right)
{
  projected_point projected_left = project_point(context, left);
  projected_point projected_right = project_point(context, right);
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      const projected_point projected_middle = project_point(context, middle);
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
  return {projected_left, projected_right, right,
          projection_cell(context, right), true};
}

inline void
append_unique(projected_path& points, const projected_point point)
{
  if (points.empty() || points.back() != point)
    points.push_back(point);
}

inline void
append_piece(projected_path_result& result, projected_path& current,
             const std::uint64_t native_cell, const bool closed = false)
{
  if (current.size() >= (closed ? 3U : 2U))
    result.pieces.push_back(
      {std::move(current), static_cast<std::uint32_t>(native_cell), closed});
  current.clear();
}

/// Project an already sampled line or ring and expose every topology event.
/// Native-cell transitions can optionally split at retained hinges; this is
/// required when a native-cell slice filters the output.
inline projected_path_result
project_path_detailed(const projection_context& context,
                      std::vector<geographic_point> source,
                      const bool closed,
                      const bool split_at_every_cell = false)
{
  projected_path_result result;
  result.diagnostics.input_points = static_cast<std::uint32_t>(source.size());
  if (source.empty())
    return result;
  for (const geographic_point point : source)
    validate_geographic_point(point);
  if (source.size() > 1
      && source.front().latitude == source.back().latitude
      && source.front().longitude == source.back().longitude)
    source.pop_back();
  if (source.empty())
    return result;
  result.diagnostics.sampled_points
    = static_cast<std::uint32_t>(source.size());

  std::optional<a60::carto::cartography<ckproj>> cahill_keyes_cartography;
  if (context.spec.kind == projection_kind::cahill_keyes)
    cahill_keyes_cartography.emplace(
      context.map_frame, std::get<ckproj>(context.projection));

  std::uint64_t current_cell = projection_cell(context, source.front());
  projected_path current;
  append_unique(current, project_point(context, source.front()));
  const std::size_t edge_count = closed ? source.size() : source.size() - 1;
  for (std::size_t index = 0; index < edge_count; ++index)
    {
      geographic_point left = source[index];
      const geographic_point right = source[(index + 1) % source.size()];
      const projected_point projected_left = project_point(context, left);
      const projected_point projected_right = project_point(context, right);

      if (cahill_keyes_cartography
          && a60::carto::cahill_keyes_path_detail::first_edge_transition(
            *cahill_keyes_cartography, projected_left, projected_right))
        {
          const a60::vvranges folded = a60::carto::fold_path_edges(
            *cahill_keyes_cartography,
            a60::vrange {projected_left, projected_right});
          require(folded.size() > 1,
                  "Cahill-Keyes edge transition did not produce a fold");
          ++result.diagnostics.cell_transitions;
          ++result.diagnostics.cuts;
          for (std::size_t folded_index = 0;
               folded_index < folded.size(); ++folded_index)
            {
              if (folded_index != 0)
                append_piece(result, current, current_cell);
              for (const projected_point point : folded[folded_index])
                append_unique(current, point);
            }
          current_cell = projection_cell(context, right);
          continue;
        }

      if (context.spec.kind == projection_kind::star_x)
        {
          const auto& star_x_projection
            = std::get<starxproj>(context.projection);
          a60::carto::star_x_path_detail::geographic_coordinate star_x_left {
            left.latitude, left.longitude,
          };
          const a60::carto::star_x_path_detail::geographic_coordinate
            star_x_right {right.latitude, right.longitude};
          constexpr std::size_t maximum_transitions_per_edge = 64;
          std::size_t transition_count = 0;
          while (const auto transition
                 = a60::carto::star_x_path_detail::first_edge_transition(
                   star_x_projection, star_x_left, star_x_right))
            {
              require(++transition_count <= maximum_transitions_per_edge,
                      "Star-X path edge crosses too many topology cells");
              ++result.diagnostics.cell_transitions;
              append_unique(current, transition->exit);
              if (transition->is_fold() || split_at_every_cell)
                {
                  if (transition->is_fold())
                    ++result.diagnostics.cuts;
                  append_piece(result, current, current_cell);
                }
              append_unique(current, transition->entry);
              star_x_left = transition->geographic_entry;
              current_cell = a60::carto::star_x_path_detail::path_cell(
                star_x_left);
            }
          append_unique(current, projected_right);
          current_cell = projection_cell(context, right);
          continue;
        }

      std::uint64_t left_cell = projection_cell(context, left);
      const std::uint64_t right_cell = projection_cell(context, right);
      constexpr std::size_t maximum_transitions_per_edge = 64;
      std::size_t transition_count = 0;
      while (left_cell != right_cell)
        {
          require(++transition_count <= maximum_transitions_per_edge,
                  std::string(context.spec.title)
                    + " path edge crosses too many native cells");
          const projected_transition transition = find_cell_transition(
            context, left, right, left_cell);
          ++result.diagnostics.cell_transitions;
          append_unique(current, transition.left);
          if (transition.is_cut || split_at_every_cell)
            {
              if (transition.is_cut)
                ++result.diagnostics.cuts;
              append_piece(result, current, left_cell);
            }
          append_unique(current, transition.right);
          left = transition.geographic_right;
          require(transition.right_cell != left_cell,
                  std::string(context.spec.title)
                    + " path transition did not enter a new native cell");
          left_cell = transition.right_cell;
          current_cell = left_cell;
        }

      const double maximum_dimension = std::max(
        context.map_frame.width(), context.map_frame.height());
      if (!current.empty()
          && point_distance(current.back(), projected_right)
               > maximum_dimension / 3)
        {
          const projected_transition transition
            = find_coordinate_wrap(context, left, right);
          append_unique(current, transition.left);
          append_piece(result, current, current_cell);
          append_unique(current, transition.right);
          ++result.diagnostics.periodic_wraps;
          current_cell = transition.right_cell;
        }
      append_unique(current, projected_right);
      current_cell = right_cell;
    }

  append_piece(result, current, current_cell,
               closed && result.pieces.empty());

  // Join only an uncut closed ring split at its arbitrary source start.
  if (closed && !split_at_every_cell && result.pieces.size() > 1
      && !result.pieces.front().points.empty()
      && !result.pieces.back().points.empty()
      && result.pieces.back().points.back()
           == result.pieces.front().points.front())
    {
      projected_path merged = std::move(result.pieces.back().points);
      const std::uint32_t cell = result.pieces.back().native_cell;
      result.pieces.pop_back();
      for (std::size_t point = 1;
           point < result.pieces.front().points.size(); ++point)
        append_unique(merged, result.pieces.front().points[point]);
      result.pieces.front()
        = {std::move(merged), cell, result.pieces.size() == 1};
    }
  return result;
}

/// Compatibility form used by the native SVG generators.
inline std::vector<projected_path>
project_path(const projection_context& context,
             std::vector<geographic_point> source, const bool closed)
{
  projected_path_result detailed = project_path_detailed(
    context, std::move(source), closed);
  std::vector<projected_path> result;
  result.reserve(detailed.pieces.size());
  for (projected_path_piece& piece : detailed.pieces)
    {
      if (piece.closed && piece.points.size() > 1
          && piece.points.front() == piece.points.back())
        piece.points.pop_back();
      result.push_back(std::move(piece.points));
    }
  return result;
}

inline constexpr std::string_view
projection_kind_name(const projection_kind kind)
{
  switch (kind)
    {
    case projection_kind::cahill_keyes: return "cahill-keyes";
    case projection_kind::authagraph: return "authagraph";
    case projection_kind::dymaxion: return "dymaxion";
    case projection_kind::myriahedral: return "myriahedral";
    case projection_kind::star_x: return "star-x";
    case projection_kind::voronoi: return "voronoi";
    }
  return "unknown";
}

inline constexpr std::string_view
topology_kind_name(const topology_kind kind)
{
  switch (kind)
    {
    case topology_kind::folded: return "folded";
    case topology_kind::periodic: return "periodic";
    case topology_kind::polyhedral: return "polyhedral";
    }
  return "unknown";
}

} // namespace cart0freak0::projection_runtime

#endif
