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
inline constexpr std::uint32_t api_version = 3;

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
  std::optional<std::uint32_t> component;
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
    case projection_kind::cahill_keyes:
    case projection_kind::authagraph:
    case projection_kind::dymaxion:
    case projection_kind::myriahedral:
    case projection_kind::voronoi:
      return inverse_mode::face_qualified;
    case projection_kind::star_x:
      return inverse_mode::candidates;
    }
  return inverse_mode::none;
}

inline a60::carto::star_x_layout
runtime_star_x_layout(const projection_handle& projection)
{
  const starxproj& implementation
    = std::get<starxproj>(projection.projection);
  return {implementation.group_gap_ratio(),
          implementation.enlargement_factor()};
}

inline a60::carto::star_x_detail::antarctic_cap_registration
star_x_cap_registration(const projection_handle& projection)
{
  using namespace a60::carto;
  using namespace a60::carto::star_x_detail;
  static const frame unit_frame {star_x_width_to_height_ratio, 1};
  static const antarctic_cap_registration unit
    = make_antarctic_cap_registration(unit_frame);
  const double scale = projection.map_frame.height();
  return {
    unit.cutoff_latitude,
    unit.bearing_offset,
    unit.maximum_boundary_radius * scale,
    unit.boundary_local_bottom * scale,
    unit.bottom_clearance * scale,
    {unit.target_pole.x * scale, unit.target_pole.y * scale},
  };
}

/// Project one explicit longitude/latitude coordinate.
inline forward_result
forward(const projection_handle& projection,
        const geographic_coordinate point)
{
  const geographic_point internal {
    point.latitude_degrees, point.longitude_degrees,
  };
  if (projection.spec.kind == projection_kind::star_x
      && point.latitude_degrees
           <= a60::carto::star_x_antarctic_cutoff_latitude_degrees)
    {
      validate_geographic_point(internal);
      const auto registration = star_x_cap_registration(projection);
      const auto cap = a60::carto::star_x_detail::project_antarctic_fragment(
        point.latitude_degrees, point.longitude_degrees,
        projection.map_frame, registration.target_pole,
        registration.bearing_offset, runtime_star_x_layout(projection));
      return {{cap.x, cap.y}, static_cast<std::uint32_t>(
                projection_cell(projection, internal)), 1};
    }
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
  constexpr double geographic_tolerance = 1e-10;
  for (inverse_candidate& existing : result.candidates)
    if (existing.native_cell == candidate.native_cell
        && existing.component == candidate.component
        && std::abs(existing.point.latitude_degrees
                    - candidate.point.latitude_degrees)
             <= geographic_tolerance
        && std::abs(std::remainder(
             existing.point.longitude_degrees
               - candidate.point.longitude_degrees, 360.0))
             <= geographic_tolerance)
      {
        const bool boundary = existing.boundary || candidate.boundary;
        if (candidate.forward_residual < existing.forward_residual)
          existing = std::move(candidate);
        existing.boundary = boundary;
        return;
      }
  if (result.candidates.size() < options.maximum_candidates)
    result.candidates.push_back(std::move(candidate));
  else
    result.truncated = true;
}

inline void
inverse_cahill_keyes(const projection_handle& projection,
                     const projected_coordinate point,
                     const inverse_options& options,
                     inverse_result& result)
{
  const ckproj& implementation = std::get<ckproj>(projection.projection);
  const double native_x = point.x - implementation.longitude_zero_x;
  const double native_y = implementation.latitude_zero_y - point.y;
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));
  constexpr std::array<int, 8> assembly_octants {
    1, 2, 3, 4, 6, 7, 8, 5,
  };
  const std::size_t begin = options.native_cell
                              ? *options.native_cell : 0;
  const std::size_t end = options.native_cell
                            ? begin + 1 : assembly_octants.size();
  for (std::size_t cell = begin; cell < end; ++cell)
    {
      const auto solution = implementation.forward.inverse(
        native_x, native_y, assembly_octants[cell], acceptance);
      if (!solution)
        continue;
      const geographic_coordinate geographic {
        canonical_longitude(solution->registered_longitude - 1),
        solution->latitude,
      };
      if (!solution->boundary
          && cahill_keyes_cell(
               {geographic.latitude_degrees,
                geographic.longitude_degrees}) != cell)
        continue;
      append_candidate(
        result,
        {geographic, static_cast<std::uint32_t>(cell), 0,
         solution->forward_residual, solution->boundary},
        options);
    }
}

inline void
inverse_star_x_carrier(const projection_handle& projection,
                       const projected_coordinate point,
                       const inverse_options& options,
                       inverse_result& result)
{
  using namespace a60::carto;
  using namespace a60::carto::star_x_detail;
  const starxproj& implementation
    = std::get<starxproj>(projection.projection);
  const star_x_layout layout = runtime_star_x_layout(projection);
  const double normalized_x = point.x / projection.map_frame.width();
  const double normalized_y = point.y / projection.map_frame.height();
  const point_2d assembled {
    0.5 + (normalized_x - 0.5) / layout.enlargement_factor,
    0.5 + (normalized_y - 0.5) / layout.enlargement_factor,
  };
  const double x_in_height_units
    = assembled.x * star_x_width_to_height_ratio;
  constexpr double group_side = 0.5;
  constexpr double side_margin = 3.0 / 22.0;
  const double half_gap = layout.group_gap_ratio / 2;
  static const ck_native::forward_projection source(0.25);
  constexpr std::array<int, 8> assembly_octants {
    1, 2, 3, 4, 6, 7, 8, 5,
  };
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));
  const double native_acceptance = acceptance
    / (layout.enlargement_factor * projection.map_frame.height());
  const std::size_t begin = options.native_cell
                              ? *options.native_cell : 0;
  const std::size_t end = options.native_cell
                            ? begin + 1 : assembly_octants.size();
  for (std::size_t cell = begin; cell < end; ++cell)
    {
      const bool second_group = cell % 4 >= 2;
      const double native_x = second_group
        ? side_margin + group_side - x_in_height_units
        : x_in_height_units - side_margin - group_side;
      const double native_y = second_group
        ? assembled.y - group_side / 2 + half_gap
        : 3 * group_side / 2 + half_gap - assembled.y;
      const auto solution = source.inverse(
        native_x, native_y, assembly_octants[cell], native_acceptance);
      if (!solution)
        continue;
      const geographic_coordinate geographic {
        canonical_longitude(solution->registered_longitude - 1),
        solution->latitude,
      };
      if (geographic.latitude_degrees
          <= star_x_antarctic_cutoff_latitude_degrees)
        continue;
      const geographic_point internal {
        geographic.latitude_degrees, geographic.longitude_degrees,
      };
      if (!solution->boundary
          && a60::carto::star_x_path_detail::path_cell(
               {internal.latitude, internal.longitude}) != cell)
        continue;
      const auto [forced_x, forced_y] = implementation.meridians_to_point_2d(
        geographic.latitude_degrees, geographic.longitude_degrees);
      const double residual = std::hypot(
        forced_x - point.x, forced_y - point.y);
      if (!std::isfinite(residual) || residual > acceptance)
        continue;
      append_candidate(
        result,
        {geographic, static_cast<std::uint32_t>(cell), 0,
         residual, solution->boundary},
        options);
    }
}

inline bool
star_x_cap_longitude_boundary(const double longitude,
                              const double tolerance_degrees)
{
  constexpr std::array seams {-111.0, -21.0, 69.0, 159.0};
  for (const double seam : seams)
    if (std::abs(std::remainder(longitude - seam, 360.0))
        <= tolerance_degrees)
      return true;
  return false;
}

inline double
snap_star_x_cap_longitude(const double longitude,
                          const double tolerance_degrees)
{
  constexpr std::array seams {-111.0, -21.0, 69.0, 159.0};
  for (const double seam : seams)
    if (std::abs(std::remainder(longitude - seam, 360.0))
        <= tolerance_degrees)
      return seam;
  return longitude;
}

inline void
inverse_star_x_cap(const projection_handle& projection,
                   const projected_coordinate point,
                   const inverse_options& options,
                   inverse_result& result)
{
  using namespace a60::carto;
  using namespace a60::carto::star_x_detail;
  const star_x_layout layout = runtime_star_x_layout(projection);
  const antarctic_cap_registration registration
    = star_x_cap_registration(projection);
  const double delta_x = point.x - registration.target_pole.x;
  const double delta_y = point.y - registration.target_pole.y;
  const double requested_radius = std::hypot(delta_x, delta_y);
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));
  const double angular_tolerance = std::max(
    1e-10, acceptance / projection.map_frame.height() * 180);

  if (requested_radius <= acceptance)
    {
      constexpr std::array<double, 4> representative_longitudes {
        -156, -66, 24, 114,
      };
      const std::size_t begin = options.native_cell
                                  ? *options.native_cell : 4;
      const std::size_t end = options.native_cell
                                ? begin + 1 : 8;
      for (std::size_t cell = begin; cell < end; ++cell)
        {
          if (cell < 4)
            continue;
          const geographic_coordinate geographic {
            representative_longitudes[cell - 4], -90,
          };
          const point_2d forced = project_antarctic_fragment(
            geographic.latitude_degrees, geographic.longitude_degrees,
            projection.map_frame, registration.target_pole,
            registration.bearing_offset, layout);
          const double residual = std::hypot(
            forced.x - point.x, forced.y - point.y);
          if (residual <= acceptance)
            append_candidate(
              result,
              {geographic, static_cast<std::uint32_t>(cell), 1,
               residual, true},
              options);
        }
      return;
    }

  const double longitude = snap_star_x_cap_longitude(
    canonical_longitude(
      std::atan2(delta_x, -delta_y) * 180 / pi
        - registration.bearing_offset),
    angular_tolerance);
  const double boundary_radius = antarctic_source_radius(
    registration.cutoff_latitude, longitude,
    projection.map_frame, layout);
  if (!std::isfinite(boundary_radius)
      || requested_radius > boundary_radius + acceptance)
    return;

  double lower = -90;
  double upper = registration.cutoff_latitude;
  for (std::size_t iteration = 0; iteration != 80; ++iteration)
    {
      const double middle = (lower + upper) / 2;
      const double radius = antarctic_source_radius(
        middle, longitude, projection.map_frame, layout);
      if (radius < requested_radius)
        lower = middle;
      else
        upper = middle;
    }
  const double latitude = (lower + upper) / 2;
  const std::uint32_t cell
    = a60::carto::star_x_path_detail::path_cell({latitude, longitude});
  if (options.native_cell && *options.native_cell != cell)
    return;
  const point_2d forced = project_antarctic_fragment(
    latitude, longitude, projection.map_frame,
    registration.target_pole, registration.bearing_offset, layout);
  const double residual = std::hypot(
    forced.x - point.x, forced.y - point.y);
  if (!std::isfinite(residual) || residual > acceptance)
    return;
  const bool boundary
    = std::abs(requested_radius - boundary_radius) <= acceptance
      || star_x_cap_longitude_boundary(longitude, angular_tolerance);
  append_candidate(
    result,
    {{longitude, latitude}, cell, 1, residual, boundary}, options);
}

inline void
inverse_star_x(const projection_handle& projection,
               const projected_coordinate point,
               const inverse_options& options,
               inverse_result& result)
{
  if (!options.component || *options.component == 0)
    inverse_star_x_carrier(projection, point, options, result);
  if (!options.component || *options.component == 1)
    inverse_star_x_cap(projection, point, options, result);
}

inline void
inverse_authagraph(const projection_handle& projection,
                   const projected_coordinate point,
                   const inverse_options& options,
                   inverse_result& result)
{
  using namespace a60::carto::authagraph_detail;
  const double normalized_x = point.x / projection.map_frame.width();
  const double unfolded_y
    = (1 - point.y / projection.map_frame.height()) * unfolded_height;
  const double acceptance = std::max(
    options.tolerance_pixels, residual_floor(projection));
  const double native_tolerance = acceptance
    / std::min(projection.map_frame.width(), projection.map_frame.height())
    * std::max(unfolded_width, unfolded_height);
  const double angular_tolerance = std::max(
    4096 * std::numeric_limits<double>::epsilon(),
    native_tolerance * 8);
  const double singular_tolerance = std::max(
    native_tolerance,
    64 * std::sqrt(std::numeric_limits<double>::epsilon()));
  const auto& vertices = tetrahedron_vertices();
  const std::size_t begin = options.native_cell
                              ? *options.native_cell : 0;
  const std::size_t end = options.native_cell
                            ? begin + 1 : cell_origins.size();

  for (std::size_t cell = begin; cell < end; ++cell)
    for (int periodic_copy = -2; periodic_copy <= 2; ++periodic_copy)
      {
        const double unfolded_x
          = (normalized_x - horizontal_shift + periodic_copy)
            * unfolded_width;
        const double origin_x = tetrahedron_scale
          * (cell_origins[cell][0] + cell_origins[cell][1] / 2.0);
        const double origin_y = tetrahedron_scale * cell_origins[cell][1]
          * sqrt_three / 2;
        const double angle = cell_rotation_sixths[cell] * pi / 6;
        const double cosine = std::cos(angle);
        const double sine = std::sin(angle);
        const double delta_x = unfolded_x - origin_x;
        const double delta_y = unfolded_y - origin_y;
        const point_2d canonical {
          cosine * delta_x + sine * delta_y,
          -sine * delta_x + cosine * delta_y,
        };

        double c = sqrt_two - sqrt_three * canonical.y;
        if (!std::isfinite(c) || c < -native_tolerance)
          continue;
        if (c < 0)
          c = 0;

        const std::size_t vertex_index = cell / 6;
        const int sector = static_cast<int>(cell % 6);
        double reduced_longitude = 0;
        const bool singular = c <= native_tolerance;
        bool boundary = c <= singular_tolerance;
        if (!singular)
          {
            const double equal_area_angle
              = canonical.x * pi / (2 * c);
            const double maximum_angle = pi / 6;
            if (!std::isfinite(equal_area_angle)
                || equal_area_angle < -maximum_angle - angular_tolerance
                || equal_area_angle > maximum_angle + angular_tolerance)
              continue;
            double lower = -pi / 3;
            double upper = pi / 3;
            for (std::size_t iteration = 0; iteration != 80; ++iteration)
              {
                const double middle = (lower + upper) / 2;
                const double value = middle - std::asin(std::clamp(
                  std::sin(middle) / sqrt_three, -1.0, 1.0));
                if (value < equal_area_angle)
                  lower = middle;
                else
                  upper = middle;
              }
            reduced_longitude = (lower + upper) / 2;
            const bool even_sector = sector % 2 == 0;
            const double sector_lower = even_sector ? -pi / 3 : 0;
            const double sector_upper = even_sector ? 0 : pi / 3;
            if (reduced_longitude < sector_lower - angular_tolerance
                || reduced_longitude > sector_upper + angular_tolerance)
              continue;
            boundary = boundary
              || std::abs(reduced_longitude - sector_lower)
                   <= angular_tolerance
              || std::abs(reduced_longitude - sector_upper)
                   <= angular_tolerance;
          }

        double local_longitude = reduced_longitude
          + static_cast<double>(sector / 2) * 2 * pi / 3;
        if (local_longitude > pi)
          local_longitude -= 2 * pi;
        const double local_latitude = singular
          ? pi / 2
          : std::atan((2 + std::cos(reduced_longitude)) / c - sqrt_two);
        const vector_3d pole = vertices[vertex_index];
        const vector_3d tangent = unit_tangent_toward(
          pole, vertices[(vertex_index + 1) % vertices.size()]);
        const vector_3d quarter_turn = cross(pole, tangent);
        const double latitude_cosine = std::cos(local_latitude);
        const vector_3d vector {
          latitude_cosine
              * (std::cos(local_longitude) * tangent.x
                 + std::sin(local_longitude) * quarter_turn.x)
            + std::sin(local_latitude) * pole.x,
          latitude_cosine
              * (std::cos(local_longitude) * tangent.y
                 + std::sin(local_longitude) * quarter_turn.y)
            + std::sin(local_latitude) * pole.y,
          latitude_cosine
              * (std::cos(local_longitude) * tangent.z
                 + std::sin(local_longitude) * quarter_turn.z)
            + std::sin(local_latitude) * pole.z,
        };

        double maximum_dot = dot(vector, vertices.front());
        for (std::size_t index = 1; index < vertices.size(); ++index)
          maximum_dot = std::max(maximum_dot, dot(vector, vertices[index]));
        const double expected_dot = dot(vector, pole);
        const double dot_tolerance = angular_tolerance * 4;
        if (expected_dot < maximum_dot - dot_tolerance)
          continue;
        boundary = boundary
          || (maximum_dot - expected_dot <= dot_tolerance
              && [&] {
               for (std::size_t index = 0; index < vertices.size(); ++index)
                 if (index != vertex_index
                     && std::abs(dot(vector, vertices[index]) - expected_dot)
                          <= dot_tolerance)
                   return true;
               return false;
              }());

        const geographic_coordinate geographic
          = geographic_from_vector(vector);
        const double forced_latitude_cosine = std::cos(local_latitude);
        const double forced_c
          = (2 + std::cos(reduced_longitude)) * forced_latitude_cosine
            / (sqrt_two * forced_latitude_cosine
               + std::sin(local_latitude));
        const double forced_equal_area_angle
          = reduced_longitude - std::asin(std::clamp(
              std::sin(reduced_longitude) / sqrt_three, -1.0, 1.0));
        const point_2d forced_canonical {
          2 / pi * forced_c * forced_equal_area_angle,
          (sqrt_two - forced_c) / sqrt_three,
        };
        const point_2d forced_unfolded
          = assemble_cell(cell, forced_canonical);
        const double forced_x = positive_modulo(
          forced_unfolded.x / unfolded_width + horizontal_shift, 1)
          * projection.map_frame.width();
        const double forced_y
          = (1 - forced_unfolded.y / unfolded_height)
            * projection.map_frame.height();
        double residual_x = std::fmod(
          std::abs(forced_x - point.x), projection.map_frame.width());
        residual_x = std::min(
          residual_x, projection.map_frame.width() - residual_x);
        const double residual = std::hypot(
          residual_x, forced_y - point.y);
        if (!std::isfinite(residual) || residual > acceptance)
          continue;
        append_candidate(
          result,
          {geographic, static_cast<std::uint32_t>(cell), 0,
           residual, boundary},
          options);
      }
}

inline std::optional<a60::carto::dymaxion_detail::vector_3d>
inverse_fuller_triangle(
  const a60::carto::dymaxion_detail::point_2d canonical,
  const a60::carto::dymaxion_detail::face_basis& basis)
{
  using namespace a60::carto::dymaxion_detail;
  const double square_root_three = std::sqrt(3.0);
  const double square_root_five = std::sqrt(5.0);
  const double spherical_edge_arc
    = 2 * std::asin(std::sqrt(5 - square_root_five) / std::sqrt(10.0));
  const double half_edge_arc = spherical_edge_arc / 2;
  const double vertex_to_edge
    = std::sqrt(3 + square_root_five) / std::sqrt(5 + square_root_five);
  const double chord_edge
    = std::sqrt(8.0) / std::sqrt(5 + square_root_five);
  const double gnomonic_scale
    = std::sqrt(5 + 2 * square_root_five) / std::sqrt(15.0);

  const double vertical = square_root_three * spherical_edge_arc
                          * canonical.y;
  const double horizontal = spherical_edge_arc * canonical.x;
  const std::array offsets {
    2 * vertical / 3,
    -vertical / 3 + horizontal,
    -vertical / 3 - horizontal,
  };
  double lower = 0;
  double upper = spherical_edge_arc;
  for (const double offset : offsets)
    {
      lower = std::max(lower, -offset);
      upper = std::min(upper, spherical_edge_arc - offset);
    }
  constexpr double angle_tolerance
    = 512 * std::numeric_limits<double>::epsilon();
  if (lower > upper + angle_tolerance)
    return std::nullopt;
  lower = std::clamp(lower, 0.0, spherical_edge_arc);
  upper = std::clamp(upper, 0.0, spherical_edge_arc);

  const auto distance_sum = [&](const double mean) {
    double sum = 3 * chord_edge / 2;
    for (const double offset : offsets)
      sum += vertex_to_edge
             * std::tan(mean + offset - half_edge_arc);
    return sum - chord_edge;
  };
  const double lower_value = distance_sum(lower);
  const double upper_value = distance_sum(upper);
  const double equation_tolerance
    = 4096 * std::numeric_limits<double>::epsilon();
  if (lower_value > equation_tolerance
      || upper_value < -equation_tolerance)
    return std::nullopt;
  for (std::size_t iteration = 0; iteration != 96; ++iteration)
    {
      const double middle = (lower + upper) / 2;
      const double value = distance_sum(middle);
      if (value > 0)
        upper = middle;
      else
        lower = middle;
    }
  const double mean = (lower + upper) / 2;
  std::array<double, 3> edge_coordinates {};
  for (std::size_t index = 0; index != edge_coordinates.size(); ++index)
    edge_coordinates[index]
      = chord_edge / 2
        + vertex_to_edge
            * std::tan(mean + offsets[index] - half_edge_arc);
  const double projected_x
    = (edge_coordinates[1] - edge_coordinates[2]) / 2;
  const double projected_y
    = (edge_coordinates[0]
       - (edge_coordinates[1] + edge_coordinates[2]) / 2)
      / square_root_three;
  vector_3d local = normalized({
    projected_x / gnomonic_scale,
    projected_y / gnomonic_scale,
    1,
  });
  return normalized(
    basis.x * local.x + basis.y * local.y + basis.z * local.z);
}

inline void
inverse_dymaxion(const projection_handle& projection,
                 const projected_coordinate point,
                 const inverse_options& options,
                 inverse_result& result)
{
  using namespace a60::carto::dymaxion_detail;
  const point_2d raw {
    point.x / projection.map_frame.width()
      * a60::carto::dymaxion_source_width,
    (1 - point.y / projection.map_frame.height())
      * a60::carto::dymaxion_source_height,
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
      const auto weights = planar_barycentric(
        geometry.planar, raw.x, raw.y, weight_tolerance);
      if (!weights)
        continue;
      const point_2d canonical {
        static_cast<double>(
          weights->weights[0] * geometry.canonical[0].x
          + weights->weights[1] * geometry.canonical[1].x
          + weights->weights[2] * geometry.canonical[2].x),
        static_cast<double>(
          weights->weights[0] * geometry.canonical[0].y
          + weights->weights[1] * geometry.canonical[1].y
          + weights->weights[2] * geometry.canonical[2].y),
      };
      const auto vector = inverse_fuller_triangle(
        canonical, geometry.basis);
      if (!vector)
        continue;
      if (!weights->boundary && containing_face(*vector) != face)
        continue;
      const point_2d forced = project_on_face(face, *vector);
      const double forced_x
        = forced.x / a60::carto::dymaxion_source_width
          * projection.map_frame.width();
      const double forced_y
        = (1 - forced.y / a60::carto::dymaxion_source_height)
          * projection.map_frame.height();
      const double residual = std::hypot(
        forced_x - point.x, forced_y - point.y);
      if (!std::isfinite(residual) || residual > acceptance)
        continue;
      append_candidate(
        result,
        {geographic_from_vector(*vector),
         static_cast<std::uint32_t>(face), 0, residual,
         weights->boundary},
        options);
    }
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
  if (options.component)
    {
      const std::uint32_t component_count
        = projection.spec.kind == projection_kind::star_x ? 2 : 1;
      if (*options.component >= component_count)
        throw std::invalid_argument("inverse component is out of range");
    }

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
    case projection_kind::cahill_keyes:
      inverse_detail::inverse_cahill_keyes(
        projection, point, options, result);
      break;
    case projection_kind::authagraph:
      inverse_detail::inverse_authagraph(
        projection, point, options, result);
      break;
    case projection_kind::dymaxion:
      inverse_detail::inverse_dymaxion(
        projection, point, options, result);
      break;
    case projection_kind::myriahedral:
      inverse_detail::inverse_myriahedral(
        projection, point, options, result);
      break;
    case projection_kind::voronoi:
      inverse_detail::inverse_voronoi(
        projection, point, options, result);
      break;
    case projection_kind::star_x:
      inverse_detail::inverse_star_x(
        projection, point, options, result);
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
      const double maximum_dimension = std::max(
        context.map_frame.width(), context.map_frame.height());

      if (context.spec.topology == topology_kind::periodic
          && point_distance(projected_left, projected_right)
               > maximum_dimension / 3)
        {
          const projected_transition transition
            = find_coordinate_wrap(context, left, right);
          append_unique(current, transition.left);
          append_piece(result, current, current_cell);
          append_unique(current, transition.right);
          ++result.diagnostics.periodic_wraps;
          current_cell = transition.right_cell;
          append_unique(current, projected_right);
          continue;
        }

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

  if (!closed)
    {
      const double maximum_dimension = std::max(
        context.map_frame.width(), context.map_frame.height());
      projected_path_result sanitized;
      sanitized.diagnostics = result.diagnostics;
      sanitized.pieces.reserve(result.pieces.size() * 2);
      for (const projected_path_piece& piece : result.pieces)
        {
          projected_path current;
          for (const projected_point point : piece.points)
            {
              if (!current.empty()
                  && point_distance(current.back(), point)
                       > maximum_dimension / 3)
                append_piece(sanitized, current, piece.native_cell);
              append_unique(current, point);
            }
          append_piece(sanitized, current, piece.native_cell, false);
        }
      result = std::move(sanitized);
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
