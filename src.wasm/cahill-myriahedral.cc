#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <emscripten/bind.h>
#include <emscripten/val.h>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-myriahedral.h"

namespace {

namespace myria = a60::carto::myriahedral_detail;

// Match the native Natural Earth renderer's five-degree area grid. Half-
// degree segmentation keeps each projected edge shorter than a terminal
// Myriahedral face while avoiding tens of thousands of one-degree subpaths.
constexpr double geographic_cell_size = 5.0;
constexpr double candidate_sample_step = 0.5;
constexpr double clipping_epsilon = 1e-12;

struct projected_point
{
  double x;
  double y;
};

using polygon = std::vector<projected_point>;

projected_point
operator+(const projected_point left, const projected_point right)
{ return {left.x + right.x, left.y + right.y}; }

projected_point
operator-(const projected_point left, const projected_point right)
{ return {left.x - right.x, left.y - right.y}; }

projected_point
operator*(const projected_point value, const double factor)
{ return {value.x * factor, value.y * factor}; }

double
cross(const projected_point left, const projected_point right)
{ return left.x * right.y - left.y * right.x; }

double
signed_area(const polygon& value)
{
  double result = 0;
  for (std::size_t index = 0; index < value.size(); ++index)
    result += cross(value[index], value[(index + 1) % value.size()]);
  return result / 2;
}

bool
same_point(const projected_point left, const projected_point right)
{
  return std::abs(left.x - right.x) <= clipping_epsilon
         && std::abs(left.y - right.y) <= clipping_epsilon;
}

void
append_unique(polygon& result, const projected_point value)
{
  if (result.empty() || !same_point(result.back(), value))
    result.push_back(value);
}

polygon
clip_against_edge(const polygon& subject,
                  const projected_point edge_start,
                  const projected_point edge_end,
                  const double orientation)
{
  polygon result;
  if (subject.empty())
    return result;

  const projected_point edge = edge_end - edge_start;
  const auto distance = [=](const projected_point value) {
    return orientation * cross(edge, value - edge_start);
  };

  projected_point previous = subject.back();
  double previous_distance = distance(previous);
  bool previous_inside = previous_distance >= -clipping_epsilon;
  for (const projected_point current : subject)
    {
      const double current_distance = distance(current);
      const bool current_inside = current_distance >= -clipping_epsilon;
      if (current_inside != previous_inside)
        {
          const double denominator = previous_distance - current_distance;
          if (std::abs(denominator) > clipping_epsilon)
            append_unique(
              result,
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

polygon
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

polygon
clip_to_geographic_cell(const polygon& subject,
                        const double west, const double south)
{
  const double east = west + geographic_cell_size;
  const double north = south + geographic_cell_size;
  return clip_to_convex_polygon(
    subject,
    {{west, south}, {east, south}, {east, north}, {west, north}});
}

polygon
densify(const polygon& value)
{
  polygon result;
  for (std::size_t index = 0; index < value.size(); ++index)
    {
      const projected_point start = value[index];
      const projected_point finish = value[(index + 1) % value.size()];
      append_unique(result, start);
      const double span = std::max(std::abs(finish.x - start.x),
                                   std::abs(finish.y - start.y));
      const int segments = std::max(
        1, static_cast<int>(std::ceil(span / candidate_sample_step)));
      for (int segment = 1; segment < segments; ++segment)
        append_unique(result,
                      start + (finish - start)
                                * (static_cast<double>(segment) / segments));
    }
  return result;
}

void
add_candidate_face(std::vector<std::size_t>& result,
                   const double longitude, const double latitude)
{
  const std::size_t face = myria::containing_face(
    myria::geographic_vector(latitude, longitude));
  if (std::find(result.begin(), result.end(), face) == result.end())
    result.push_back(face);
}

std::vector<std::size_t>
candidate_faces(const polygon& value,
                const double west, const double south)
{
  std::vector<std::size_t> result;
  for (const projected_point point : value)
    add_candidate_face(result, point.x, point.y);

  constexpr int samples
    = static_cast<int>(geographic_cell_size / candidate_sample_step);
  for (int y = 0; y <= samples; ++y)
    for (int x = 0; x <= samples; ++x)
      add_candidate_face(
        result,
        west + geographic_cell_size * static_cast<double>(x) / samples,
        south + geographic_cell_size * static_cast<double>(y) / samples);
  return result;
}

class face_projection
{
  myria::vector_3d source_origin;
  myria::vector_3d source_edge_0;
  myria::vector_3d source_edge_1;
  myria::point_2d target_origin;
  myria::point_2d target_edge_0;
  myria::point_2d target_edge_1;
  double coefficient_a;
  double coefficient_b;
  double coefficient_c;
  double determinant;

public:
  face_projection(const myria::projection_layout& layout,
                  const std::size_t face)
  : source_origin(layout.spherical[face][0]),
    source_edge_0(layout.spherical[face][1] - source_origin),
    source_edge_1(layout.spherical[face][2] - source_origin),
    target_origin(layout.planar[face][0]),
    target_edge_0(layout.planar[face][1] - target_origin),
    target_edge_1(layout.planar[face][2] - target_origin),
    coefficient_a(myria::dot(source_edge_0, source_edge_0)),
    coefficient_b(myria::dot(source_edge_0, source_edge_1)),
    coefficient_c(myria::dot(source_edge_1, source_edge_1)),
    determinant(coefficient_a * coefficient_c
                - coefficient_b * coefficient_b)
  { }

  projected_point
  operator()(const double longitude, const double latitude) const
  {
    const myria::vector_3d relative
      = myria::geographic_vector(latitude, longitude) - source_origin;
    const double r0 = myria::dot(relative, source_edge_0);
    const double r1 = myria::dot(relative, source_edge_1);
    const double alpha
      = (r0 * coefficient_c - r1 * coefficient_b) / determinant;
    const double beta
      = (r1 * coefficient_a - r0 * coefficient_b) / determinant;
    const myria::point_2d value
      = target_origin + target_edge_0 * alpha + target_edge_1 * beta;
    return {value.x, value.y};
  }
};

class cahill_myriahedral_web_projection
{
  a60::carto::frame map_frame;
  a60::carto::myriaproj projection;

  projected_point
  normalize(const projected_point value) const
  {
    const myria::point_2d normalized = myria::normalize_planar_point(
      projection.layout(), {value.x, value.y});
    return {normalized.x * map_frame.width(),
            normalized.y * map_frame.height()};
  }

  void
  append_svg_polygon(std::ostringstream& output,
                     const polygon& raw) const
  {
    if (raw.size() < 3 || std::abs(signed_area(raw)) < 1e-15)
      return;
    for (std::size_t index = 0; index < raw.size(); ++index)
      {
        const projected_point point = normalize(raw[index]);
        output << (index == 0 ? 'M' : 'L')
               << point.x << ' ' << point.y << ' ';
      }
    output << "Z ";
  }

  void
  append_face_clipped_cell(std::ostringstream& output,
                           const polygon& geographic,
                           const double west, const double south) const
  {
    const polygon sampled = densify(geographic);
    for (const std::size_t face
         : candidate_faces(sampled, west, south))
      {
        const face_projection project_on_face(projection.layout(), face);
        polygon planar;
        planar.reserve(sampled.size());
        for (const projected_point point : sampled)
          append_unique(planar, project_on_face(point.x, point.y));

        const auto& face_triangle = projection.layout().planar[face];
        const polygon triangle {
          {face_triangle[0].x, face_triangle[0].y},
          {face_triangle[1].x, face_triangle[1].y},
          {face_triangle[2].x, face_triangle[2].y},
        };
        append_svg_polygon(
          output, clip_to_convex_polygon(std::move(planar), triangle));
      }
  }

  void
  append_ring(std::ostringstream& output,
              const emscripten::val& ring) const
  {
    polygon geographic;
    const unsigned point_count = ring["length"].as<unsigned>();
    geographic.reserve(point_count);
    for (unsigned index = 0; index < point_count; ++index)
      {
        const emscripten::val coordinate = ring[index];
        const projected_point point {
          coordinate[0].as<double>(), coordinate[1].as<double>()
        };
        if (!std::isfinite(point.x) || point.x < -180 || point.x > 180
            || !std::isfinite(point.y) || point.y < -90 || point.y > 90)
          throw std::invalid_argument(
            "Myriahedral web land coordinates must be finite WGS 84 "
            "longitude/latitude values");
        append_unique(geographic, point);
      }
    if (geographic.size() > 1
        && same_point(geographic.front(), geographic.back()))
      geographic.pop_back();
    if (geographic.size() < 3)
      return;

    double minimum_x = geographic.front().x;
    double maximum_x = geographic.front().x;
    double minimum_y = geographic.front().y;
    double maximum_y = geographic.front().y;
    for (const projected_point point : geographic)
      {
        minimum_x = std::min(minimum_x, point.x);
        maximum_x = std::max(maximum_x, point.x);
        minimum_y = std::min(minimum_y, point.y);
        maximum_y = std::max(maximum_y, point.y);
      }

    constexpr int cell_size = static_cast<int>(geographic_cell_size);
    const int first_x = std::max(
      -180, static_cast<int>(std::floor(minimum_x / cell_size)) * cell_size);
    const int last_x = std::min(
      180, static_cast<int>(std::ceil(maximum_x / cell_size)) * cell_size);
    const int first_y = std::max(
      -90, static_cast<int>(std::floor(minimum_y / cell_size)) * cell_size);
    const int last_y = std::min(
      90, static_cast<int>(std::ceil(maximum_y / cell_size)) * cell_size);
    for (int south = first_y; south < last_y; south += cell_size)
      for (int west = first_x; west < last_x; west += cell_size)
        {
          polygon clipped = clip_to_geographic_cell(
            geographic, west, south);
          if (clipped.size() >= 3
              && std::abs(signed_area(clipped)) > 1e-14)
            append_face_clipped_cell(output, clipped, west, south);
        }
  }

  void
  append_polygon_coordinates(std::ostringstream& output,
                             const emscripten::val& coordinates) const
  {
    const unsigned ring_count = coordinates["length"].as<unsigned>();
    for (unsigned index = 0; index < ring_count; ++index)
      append_ring(output, coordinates[index]);
  }

  void
  append_geometry(std::ostringstream& output,
                  const emscripten::val& geometry) const
  {
    const std::string type = geometry["type"].as<std::string>();
    if (type == "GeometryCollection")
      {
        const emscripten::val geometries = geometry["geometries"];
        const unsigned count = geometries["length"].as<unsigned>();
        for (unsigned index = 0; index < count; ++index)
          append_geometry(output, geometries[index]);
      }
    else if (type == "Polygon")
      append_polygon_coordinates(output, geometry["coordinates"]);
    else if (type == "MultiPolygon")
      {
        const emscripten::val polygons = geometry["coordinates"];
        const unsigned count = polygons["length"].as<unsigned>();
        for (unsigned index = 0; index < count; ++index)
          append_polygon_coordinates(output, polygons[index]);
      }
    else if (type == "LineString")
      {
        // GDAL's Cahill-Keyes seam preparation left one zero-area boundary
        // remnant in the shared land input. It cannot contribute to a filled
        // land layer and is intentionally ignored by both WASM adapters.
      }
    else
      throw std::invalid_argument(
        "Myriahedral web land data must contain only polygon geometry");
  }

  void
  append_ocean(std::ostringstream& output) const
  {
    output << "<g id=\"ocean\"><path id=\"myriahedral-ocean\" d=\"";
    for (const auto& face : projection.layout().planar)
      append_svg_polygon(output,
                         {{face[0].x, face[0].y},
                          {face[1].x, face[1].y},
                          {face[2].x, face[2].y}});
    output << "\" fill=\"#e8f2f5\" stroke=\"#e8f2f5\" stroke-width=\""
           << map_frame.width() / 2500
           << "\" stroke-linejoin=\"round\" fill-rule=\"evenodd\"/></g>";
  }

  void
  append_land(std::ostringstream& output,
              const emscripten::val& geojson) const
  {
    if (geojson["type"].as<std::string>() != "FeatureCollection")
      throw std::invalid_argument(
        "Myriahedral web land data must be a GeoJSON FeatureCollection");

    output << "<g id=\"land\"><path id=\"natural-earth-land\" d=\"";
    const emscripten::val features = geojson["features"];
    const unsigned count = features["length"].as<unsigned>();
    for (unsigned index = 0; index < count; ++index)
      append_geometry(output, features[index]["geometry"]);
    output << "\" fill=\"#deddd4\" stroke=\"#deddd4\" stroke-width=\""
           << map_frame.width() / 2500
           << "\" stroke-linejoin=\"round\" fill-rule=\"evenodd\"/></g>";
  }

public:
  cahill_myriahedral_web_projection(const double width, const double height)
  : map_frame(width, height),
    projection(a60::carto::make_myriahedral_projection(map_frame))
  { }

  projected_point
  project(const double latitude, const double longitude) const
  {
    const auto [x, y]
      = projection.meridians_to_point_2d(latitude, longitude);
    return {x, y};
  }

  double
  width() const
  { return map_frame.width(); }

  double
  height() const
  { return map_frame.height(); }

  std::string
  generate_base_map_svg(const emscripten::val& land_geojson) const
  {
    std::ostringstream output;
    output << std::fixed << std::setprecision(3);
    output
      << "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 "
      << map_frame.width() << ' ' << map_frame.height()
      << "\" width=\"" << map_frame.width() << "\" height=\""
      << map_frame.height()
      << "\" role=\"img\" data-generator=\"cartofreako-cahill-"
         "myriahedral-wasm\" data-layers=\"ocean land\">"
         "<title>Cartofreako Myriahedral world map</title>"
         "<desc>Generated at runtime by the cartofreako C++20 "
         "Myriahedral projection compiled to WebAssembly. The base map "
         "contains only ocean and Natural Earth 1:110m land layers.</desc>";
    append_ocean(output);
    append_land(output, land_geojson);
    output << "</svg>";
    return output.str();
  }
};

std::string
implementation_name()
{ return "cartofreako C++20 Myriahedral/WebAssembly"; }

} // namespace

EMSCRIPTEN_BINDINGS(cartofreako_cahill_myriahedral)
{
  emscripten::value_object<projected_point>("MyriahedralProjectedPoint")
    .field("x", &projected_point::x)
    .field("y", &projected_point::y);

  emscripten::class_<cahill_myriahedral_web_projection>(
    "MyriahedralProjection")
    .constructor<double, double>()
    .function("project", &cahill_myriahedral_web_projection::project)
    .function("width", &cahill_myriahedral_web_projection::width)
    .function("height", &cahill_myriahedral_web_projection::height)
    .function("generateBaseMapSvg",
              &cahill_myriahedral_web_projection::generate_base_map_svg);

  emscripten::function("implementationName", &implementation_name);
}
