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
#include <span>
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
#include <izzi-svg.h>

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

/// Version of the headless forward/reverse runtime API.
inline constexpr std::uint32_t api_version = 2;

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

/// Reverse-projection capability advertised by one projection layout.
enum class inverse_mode
{
  none,
  face_qualified,
  candidates,
};

/// Outcome of one reverse-projection request.
enum class inverse_status : std::uint8_t
{
  unique,
  ambiguous,
  outside,
  cut,
  unsupported,
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

/// Public immutable runtime handle. The alias keeps the implementation's
/// established context name available to existing generators.
using projection_handle = projection_context;

/// Geographic coordinate in explicit GeoJSON order.
struct geographic_coordinate
{
  double longitude_degrees;
  double latitude_degrees;
};

/// Projected coordinate in output-frame pixels.
struct projected_coordinate
{
  double x;
  double y;
};

/// Structured result of one forward projection.
struct forward_result
{
  projected_coordinate point;
  std::uint32_t native_cell;
  std::uint32_t component;
};

/// One face-qualified geographic solution to a projected coordinate.
struct inverse_candidate
{
  geographic_coordinate point;
  std::uint32_t native_cell;
  std::uint32_t component;
  double forward_residual;
  bool boundary;
};

/// Controls candidate enumeration and numerical acceptance.
struct inverse_options
{
  double tolerance_pixels = 1e-7;
  std::optional<std::uint32_t> native_cell;
  std::size_t maximum_candidates = 32;
};

/// Structured result of one reverse projection.
struct inverse_result
{
  inverse_status status = inverse_status::outside;
  std::vector<inverse_candidate> candidates;
  double tolerance_pixels = 0;
  bool truncated = false;
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

/// Return the reverse capability implemented for one projection layout.
inline constexpr inverse_mode
inverse_mode_for(const projection_spec& spec)
{
  switch (spec.kind)
    {
    case projection_kind::myriahedral:
    case projection_kind::voronoi:
      return inverse_mode::face_qualified;
    case projection_kind::cahill_keyes:
    case projection_kind::authagraph:
    case projection_kind::dymaxion:
    case projection_kind::star_x:
      return inverse_mode::none;
    }
  return inverse_mode::none;
}

/// Project one explicit longitude/latitude coordinate.
inline forward_result
forward(const projection_handle& projection,
        const geographic_coordinate point)
{
  const geographic_point internal {
    point.latitude_degrees, point.longitude_degrees,
  };
  const auto [x, y] = project_point(projection, internal);
  return {{x, y}, static_cast<std::uint32_t>(
                    projection_cell(projection, internal)), 0};
}

/// Project a packed native batch without sentinel coordinates.
inline std::vector<forward_result>
forward_many(const projection_handle& projection,
             const std::span<const geographic_coordinate> points)
{
  std::vector<forward_result> result;
  result.reserve(points.size());
  for (const geographic_coordinate point : points)
    result.push_back(forward(projection, point));
  return result;
}

namespace inverse_detail {

inline constexpr double pi
  = 3.141592653589793238462643383279502884;

struct barycentric_result
{
  std::array<long double, 3> weights;
  bool boundary;
};

template<typename Triangle>
inline std::optional<barycentric_result>
planar_barycentric(const Triangle& triangle,
                   const double x, const double y,
                   const long double tolerance)
{
  const long double ax = triangle[0].x;
  const long double ay = triangle[0].y;
  const long double bx = triangle[1].x;
  const long double by = triangle[1].y;
  const long double cx = triangle[2].x;
  const long double cy = triangle[2].y;
  const long double px = x;
  const long double py = y;
  const long double divisor
    = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
  const long double scale = std::max({
    std::abs(bx - ax), std::abs(by - ay),
    std::abs(cx - ax), std::abs(cy - ay), 1.0L,
  });
  if (!std::isfinite(divisor)
      || std::abs(divisor)
           <= 64 * std::numeric_limits<long double>::epsilon()
                * scale * scale)
    throw std::logic_error("inverse candidate has a degenerate planar face");

  const long double second
    = ((px - ax) * (cy - ay) - (py - ay) * (cx - ax)) / divisor;
  const long double third
    = ((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / divisor;
  const long double first = 1 - second - third;
  if (!std::isfinite(first) || !std::isfinite(second)
      || !std::isfinite(third)
      || first < -tolerance || second < -tolerance
      || third < -tolerance
      || first > 1 + tolerance || second > 1 + tolerance
      || third > 1 + tolerance)
    return std::nullopt;

  std::array<long double, 3> weights {
    std::clamp(first, 0.0L, 1.0L),
    std::clamp(second, 0.0L, 1.0L),
    std::clamp(third, 0.0L, 1.0L),
  };
  const long double sum = weights[0] + weights[1] + weights[2];
  for (long double& weight : weights)
    weight /= sum;
  const bool boundary = weights[0] <= tolerance
                        || weights[1] <= tolerance
                        || weights[2] <= tolerance;
  return barycentric_result {weights, boundary};
}

inline double
canonical_longitude(double value)
{
  while (value >= 180)
    value -= 360;
  while (value < -180)
    value += 360;
  return value;
}

template<typename Vector>
inline geographic_coordinate
geographic_from_vector(const Vector& value,
                       const double input_rotation_degrees = 0)
{
  const double horizontal = std::hypot(value.x, value.y);
  const double latitude = std::asin(
    std::clamp(value.z, -1.0, 1.0)) * 180 / pi;
  if (horizontal <= 64 * std::numeric_limits<double>::epsilon())
    return {0, latitude};
  const double rotated_longitude = std::atan2(value.y, value.x) * 180 / pi;
  return {canonical_longitude(
            rotated_longitude - input_rotation_degrees),
          latitude};
}

inline long double
barycentric_tolerance(const projection_handle& projection,
                      const inverse_options& options)
{
  const double minimum_dimension = std::min(
    projection.map_frame.width(), projection.map_frame.height());
  return std::max(
    512 * std::numeric_limits<long double>::epsilon(),
    static_cast<long double>(8 * options.tolerance_pixels
                             / minimum_dimension));
}

inline double
residual_floor(const projection_handle& projection)
{
  return 256 * std::numeric_limits<double>::epsilon()
         * std::max(projection.map_frame.width(),
                    projection.map_frame.height());
}

inline void
append_candidate(inverse_result& result,
                 inverse_candidate candidate,
                 const inverse_options& options)
{
  if (result.candidates.size() < options.maximum_candidates)
    result.candidates.push_back(std::move(candidate));
  else
    result.truncated = true;
}

inline void
inverse_myriahedral(const projection_handle& projection,
                    const projected_coordinate point,
                    const inverse_options& options,
                    inverse_result& result)
{
  using namespace a60::carto::myriahedral_detail;
  const myriaproj& implementation
    = std::get<myriaproj>(projection.projection);
  const projection_layout& layout = implementation.layout();
  const long double extent_x
    = static_cast<long double>(layout.maximum_x) - layout.minimum_x;
  const long double extent_y
    = static_cast<long double>(layout.maximum_y) - layout.minimum_y;
  constexpr long double ratio = 16.0L / 9.0L;
  const long double scale = std::min(ratio / extent_x, 1.0L / extent_y);
  const long double left = (ratio - extent_x * scale) / 2;
  const long double bottom = (1 - extent_y * scale) / 2;
  const long double normalized_x
    = point.x / projection.map_frame.width();
  const long double normalized_y
    = point.y / projection.map_frame.height();
  const point_2d raw {
    static_cast<double>(layout.minimum_x
      + (normalized_x * ratio - left) / scale),
    static_cast<double>(layout.minimum_y
      + ((1 - normalized_y) - bottom) / scale),
  };
  const long double weight_tolerance
    = barycentric_tolerance(projection, options);
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));

  const std::size_t begin = options.native_cell
                              ? *options.native_cell : 0;
  const std::size_t end = options.native_cell
                            ? begin + 1 : face_count;
  for (std::size_t face = begin; face < end; ++face)
    {
      const auto weights = planar_barycentric(
        layout.planar[face], raw.x, raw.y, weight_tolerance);
      if (!weights)
        continue;
      const spherical_face& source = layout.spherical[face];
      vector_3d vector {
        static_cast<double>(weights->weights[0] * source[0].x
                            + weights->weights[1] * source[1].x
                            + weights->weights[2] * source[2].x),
        static_cast<double>(weights->weights[0] * source[0].y
                            + weights->weights[1] * source[1].y
                            + weights->weights[2] * source[2].y),
        static_cast<double>(weights->weights[0] * source[0].z
                            + weights->weights[1] * source[1].z
                            + weights->weights[2] * source[2].z),
      };
      vector = normalized(vector);
      const point_2d forced = normalize_planar_point(
        layout, project_on_face(layout, face, vector));
      const double residual = std::hypot(
        forced.x * projection.map_frame.width() - point.x,
        forced.y * projection.map_frame.height() - point.y);
      if (!std::isfinite(residual) || residual > acceptance)
        continue;
      append_candidate(
        result,
        {geographic_from_vector(vector), static_cast<std::uint32_t>(face),
         0, residual, weights->boundary},
        options);
    }
}

inline void
inverse_voronoi(const projection_handle& projection,
                const projected_coordinate point,
                const inverse_options& options,
                inverse_result& result)
{
  using namespace a60::carto::voronoi_detail;
  const double normalized_x = point.x / projection.map_frame.width();
  const double normalized_y = point.y / projection.map_frame.height();
  static const point_2d registration = project_to_unfolded_net(
    0, registration_longitude_degrees);
  const point_2d raw {
    registration.x
      + (normalized_x * a60::carto::voronoi_source_width - source_center_x)
          / source_scale,
    registration.y
      + (source_center_y - normalized_y * a60::carto::voronoi_source_height)
          / source_scale,
  };
  const layout_data& data = layout();
  const long double weight_tolerance
    = barycentric_tolerance(projection, options);
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));
  const std::size_t begin = options.native_cell
                              ? *options.native_cell : 0;
  const std::size_t end = options.native_cell
                            ? begin + 1 : face_count;
  for (std::size_t face = begin; face < end; ++face)
    {
      const face_geometry& geometry = data.faces[face];
      std::array<point_2d, 3> planar {};
      for (std::size_t vertex = 0; vertex < planar.size(); ++vertex)
        {
          const point_2d local = project_on_face(
            geometry, data.vertices[geometry.vertices[vertex]]);
          const point_2d unfolded = apply(geometry.transform, local);
          planar[vertex] = {unfolded.x, -unfolded.y};
        }
      const auto weights = planar_barycentric(
        planar, raw.x, raw.y, weight_tolerance);
      if (!weights)
        continue;
      vector_3d vector {
        static_cast<double>(
          weights->weights[0] * data.vertices[geometry.vertices[0]].x
          + weights->weights[1] * data.vertices[geometry.vertices[1]].x
          + weights->weights[2] * data.vertices[geometry.vertices[2]].x),
        static_cast<double>(
          weights->weights[0] * data.vertices[geometry.vertices[0]].y
          + weights->weights[1] * data.vertices[geometry.vertices[1]].y
          + weights->weights[2] * data.vertices[geometry.vertices[2]].y),
        static_cast<double>(
          weights->weights[0] * data.vertices[geometry.vertices[0]].z
          + weights->weights[1] * data.vertices[geometry.vertices[1]].z
          + weights->weights[2] * data.vertices[geometry.vertices[2]].z),
      };
      vector = normalized(vector);
      const point_2d local = project_on_face(geometry, vector);
      const point_2d unfolded = apply(geometry.transform, local);
      const point_2d forced_raw {unfolded.x, -unfolded.y};
      const double forced_x
        = (source_center_x
           + source_scale * (forced_raw.x - registration.x))
          / a60::carto::voronoi_source_width
          * projection.map_frame.width();
      const double forced_y
        = (source_center_y
           - source_scale * (forced_raw.y - registration.y))
          / a60::carto::voronoi_source_height
          * projection.map_frame.height();
      const double residual = std::hypot(
        forced_x - point.x, forced_y - point.y);
      if (!std::isfinite(residual) || residual > acceptance)
        continue;
      append_candidate(
        result,
        {geographic_from_vector(vector, input_rotation_degrees),
         static_cast<std::uint32_t>(face), 0, residual,
         weights->boundary},
        options);
    }
}

} // namespace inverse_detail

/// Reverse one projected coordinate into zero or more face-qualified
/// geographic candidates. Unsupported projections return a structured status.
inline inverse_result
inverse(const projection_handle& projection,
        const projected_coordinate point,
        const inverse_options& options = {})
{
  if (!std::isfinite(point.x) || !std::isfinite(point.y))
    throw std::invalid_argument("inverse point must be finite");
  if (!std::isfinite(options.tolerance_pixels)
      || options.tolerance_pixels <= 0)
    throw std::invalid_argument(
      "inverse tolerance must be finite and positive");
  if (options.maximum_candidates == 0)
    throw std::invalid_argument(
      "inverse maximum candidate count must be positive");
  if (options.native_cell
      && *options.native_cell >= projection.spec.native_cell_count)
    throw std::invalid_argument("inverse native cell is out of range");

  inverse_result result;
  result.tolerance_pixels = options.tolerance_pixels;
  if (inverse_mode_for(projection.spec) == inverse_mode::none)
    {
      result.status = inverse_status::unsupported;
      return result;
    }
  const double tolerance = options.tolerance_pixels;
  if (point.x < -tolerance
      || point.x > projection.map_frame.width() + tolerance
      || point.y < -tolerance
      || point.y > projection.map_frame.height() + tolerance)
    {
      result.status = inverse_status::outside;
      return result;
    }
  switch (projection.spec.kind)
    {
    case projection_kind::myriahedral:
      inverse_detail::inverse_myriahedral(
        projection, point, options, result);
      break;
    case projection_kind::voronoi:
      inverse_detail::inverse_voronoi(
        projection, point, options, result);
      break;
    case projection_kind::cahill_keyes:
    case projection_kind::authagraph:
    case projection_kind::dymaxion:
    case projection_kind::star_x:
      break;
    }
  if (result.candidates.empty())
    result.status = inverse_status::outside;
  else if (result.candidates.size() > 1 || result.truncated)
    result.status = inverse_status::ambiguous;
  else if (result.candidates.front().boundary)
    result.status = inverse_status::cut;
  else
    result.status = inverse_status::unique;
  return result;
}

/// Reverse a native batch, preserving one structured result per input point.
inline std::vector<inverse_result>
inverse_many(const projection_handle& projection,
             const std::span<const projected_coordinate> points,
             const inverse_options& options = {})
{
  std::vector<inverse_result> result;
  result.reserve(points.size());
  for (const projected_coordinate point : points)
    result.push_back(inverse(projection, point, options));
  return result;
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

inline constexpr std::string_view
inverse_mode_name(const inverse_mode mode)
{
  switch (mode)
    {
    case inverse_mode::none: return "none";
    case inverse_mode::face_qualified: return "face-qualified";
    case inverse_mode::candidates: return "candidates";
    }
  return "unknown";
}

inline constexpr std::string_view
inverse_status_name(const inverse_status status)
{
  switch (status)
    {
    case inverse_status::unique: return "unique";
    case inverse_status::ambiguous: return "ambiguous";
    case inverse_status::outside: return "outside";
    case inverse_status::cut: return "cut";
    case inverse_status::unsupported: return "unsupported";
    }
  return "unknown";
}

} // namespace cart0freak0::projection_runtime

#endif
