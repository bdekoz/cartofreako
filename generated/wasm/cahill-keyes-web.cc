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

#include <emscripten/bind.h>
#include <emscripten/val.h>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

namespace {

constexpr double sample_step = 2.0;
constexpr double seam_epsilon = 1e-7;

struct projected_point
{
  double x;
  double y;
};

struct longitude_sector
{
  double west;
  double east;
};

constexpr std::array cahill_keyes_sectors {
  longitude_sector {159, 249},
  longitude_sector {-111, -21},
  longitude_sector {-21, 69},
  longitude_sector {69, 159},
};

double
canonical_longitude(double longitude)
{
  if (!std::isfinite(longitude))
    throw std::invalid_argument(
      "Cahill-Keyes longitude must be finite");
  while (longitude > 180)
    longitude -= 360;
  while (longitude < -180)
    longitude += 360;
  return longitude;
}

class cahill_keyes_web_projection
{
  a60::carto::frame map_frame;
  a60::carto::ckproj projection;

  projected_point
  project_unchecked(const double latitude, const double longitude) const
  {
    const auto [x, y] = projection.meridians_to_point_2d(
      latitude, canonical_longitude(longitude));
    return {x, y};
  }

  void
  append_point(std::ostringstream& output, const projected_point point,
               const bool move) const
  {
    output << (move ? 'M' : 'L') << point.x << ' ' << point.y << ' ';
  }

  void
  append_face(std::ostringstream& output, const longitude_sector sector,
              const bool north) const
  {
    const double west = sector.west + seam_epsilon;
    const double east = sector.east - seam_epsilon;
    append_point(output, project_unchecked(0, west), true);
    for (double longitude = west + sample_step; longitude < east;
         longitude += sample_step)
      append_point(output, project_unchecked(0, longitude), false);
    append_point(output, project_unchecked(0, east), false);

    const double pole = north ? 90 : -90;
    const double latitude_step = north ? sample_step : -sample_step;
    for (double latitude = latitude_step;
         north ? latitude < pole : latitude > pole;
         latitude += latitude_step)
      append_point(output, project_unchecked(latitude, east), false);
    append_point(output, project_unchecked(pole, east), false);

    for (double latitude = pole - latitude_step;
         north ? latitude > 0 : latitude < 0;
         latitude -= latitude_step)
      append_point(output, project_unchecked(latitude, west), false);
    append_point(output, project_unchecked(0, west), false);
    output << "Z ";
  }

  void
  append_parallel(std::ostringstream& output, const double latitude,
                  const longitude_sector sector) const
  {
    const double west = sector.west + seam_epsilon;
    const double east = sector.east - seam_epsilon;
    append_point(output, project_unchecked(latitude, west), true);
    for (double longitude = west + sample_step; longitude < east;
         longitude += sample_step)
      append_point(output, project_unchecked(latitude, longitude), false);
    append_point(output, project_unchecked(latitude, east), false);
  }

  void
  append_meridian(std::ostringstream& output, const double longitude,
                  const double south, const double north) const
  {
    append_point(output, project_unchecked(south, longitude), true);
    for (double latitude = south + sample_step; latitude < north;
         latitude += sample_step)
      append_point(output, project_unchecked(latitude, longitude), false);
    append_point(output, project_unchecked(north, longitude), false);
  }

  void
  append_polygon_coordinates(std::ostringstream& output,
                             const emscripten::val& polygon) const
  {
    const unsigned ring_count = polygon["length"].as<unsigned>();
    for (unsigned ring_index = 0; ring_index < ring_count; ++ring_index)
      {
        const emscripten::val ring = polygon[ring_index];
        const unsigned point_count = ring["length"].as<unsigned>();
        if (point_count < 3)
          continue;

        for (unsigned point_index = 0; point_index < point_count;
             ++point_index)
          {
            const emscripten::val coordinate = ring[point_index];
            const double longitude = coordinate[0].as<double>();
            const double latitude = coordinate[1].as<double>();
            append_point(output, project_unchecked(latitude, longitude),
                         point_index == 0);
          }
        output << "Z ";
      }
  }

  void
  append_geometry(std::ostringstream& output,
                  const emscripten::val& geometry) const
  {
    const std::string type = geometry["type"].as<std::string>();
    if (type == "GeometryCollection")
      {
        const emscripten::val geometries = geometry["geometries"];
        const unsigned geometry_count = geometries["length"].as<unsigned>();
        for (unsigned index = 0; index < geometry_count; ++index)
          append_geometry(output, geometries[index]);
      }
    else if (type == "Polygon")
      append_polygon_coordinates(output, geometry["coordinates"]);
    else if (type == "MultiPolygon")
      {
        const emscripten::val coordinates = geometry["coordinates"];
        const unsigned polygon_count = coordinates["length"].as<unsigned>();
        for (unsigned index = 0; index < polygon_count; ++index)
          append_polygon_coordinates(output, coordinates[index]);
      }
    else if (type != "LineString")
      throw std::invalid_argument(
        "Cahill-Keyes web land data must contain polygons");
  }

  void
  append_land(std::ostringstream& output,
              const emscripten::val& geojson) const
  {
    if (geojson["type"].as<std::string>() != "FeatureCollection")
      throw std::invalid_argument(
        "Cahill-Keyes web land data must be a GeoJSON FeatureCollection");

    output << "<g id=\"land\"><path id=\"natural-earth-land\" d=\"";
    const emscripten::val features = geojson["features"];
    const unsigned feature_count = features["length"].as<unsigned>();
    for (unsigned index = 0; index < feature_count; ++index)
      append_geometry(output, features[index]["geometry"]);
    output << "\" fill=\"#deddd4\" fill-rule=\"evenodd\" "
              "stroke=\"#747b78\" stroke-width=\""
           << map_frame.width() / 5200
           << "\" stroke-linejoin=\"round\"/></g>";
  }

public:
  cahill_keyes_web_projection(const double width, const double height)
  : map_frame(width, height),
    projection(a60::carto::make_cahill_keyes_projection(map_frame))
  { }

  projected_point
  project(const double latitude, const double longitude) const
  {
    if (!std::isfinite(latitude) || latitude < -90 || latitude > 90)
      throw std::invalid_argument(
        "Cahill-Keyes latitude must be within [-90, 90]");
    if (!std::isfinite(longitude) || longitude < -180 || longitude > 180)
      throw std::invalid_argument(
        "Cahill-Keyes longitude must be within [-180, 180]");
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
      << "<svg xmlns=\"http://www.w3.org/2000/svg\" "
         "viewBox=\"0 0 " << map_frame.width() << ' ' << map_frame.height()
      << "\" width=\"" << map_frame.width() << "\" height=\""
      << map_frame.height()
      << "\" role=\"img\" data-generator=\"cartofreako-cahill-keyes-wasm\">"
         "<title>Cartofreako Cahill-Keyes world map</title>"
         "<desc>Generated at runtime by the cartofreako C++20 "
         "Cahill-Keyes projection compiled to WebAssembly. The forward "
         "construction derives from work by Mary Jo Graca and Gene Keyes; "
         "land geometry is Natural Earth 1:110m.</desc>"
         "<rect width=\"100%\" height=\"100%\" fill=\"#fafaf7\"/>"
         "<g id=\"ocean-faces\" fill=\"#e8f2f5\" stroke=\"#72848c\" "
         "stroke-width=\"" << map_frame.width() / 4200 << "\">";
    for (const longitude_sector sector : cahill_keyes_sectors)
      {
        output << "<path d=\"";
        append_face(output, sector, true);
        output << "\"/><path d=\"";
        append_face(output, sector, false);
        output << "\"/>";
      }
    output << "</g>";

    output << "<g id=\"graticules\" fill=\"none\" stroke=\"#91a4aa\" "
              "stroke-opacity=\"0.55\" stroke-width=\""
           << map_frame.width() / 9000 << "\">";
    for (int latitude = -80; latitude <= 80; latitude += 10)
      {
        output << "<path data-latitude=\"" << latitude << "\" d=\"";
        for (const longitude_sector sector : cahill_keyes_sectors)
          append_parallel(output, latitude, sector);
        output << "\"/>";
      }
    for (int longitude = -180; longitude < 180; longitude += 10)
      {
        output << "<path data-longitude=\"" << longitude << "\" d=\"";
        append_meridian(output, longitude, -90, 0);
        append_meridian(output, longitude, 0, 90);
        output << "\"/>";
      }
    output << "</g>";

    append_land(output, land_geojson);
    output << "</svg>";
    return output.str();
  }
};

std::string
implementation_name()
{ return "cartofreako C++20 Cahill-Keyes/WebAssembly"; }

} // namespace

EMSCRIPTEN_BINDINGS(cartofreako_cahill_keyes_web)
{
  emscripten::value_object<projected_point>("ProjectedPoint")
    .field("x", &projected_point::x)
    .field("y", &projected_point::y);

  emscripten::class_<cahill_keyes_web_projection>("CahillKeyesProjection")
    .constructor<double, double>()
    .function("project", &cahill_keyes_web_projection::project)
    .function("width", &cahill_keyes_web_projection::width)
    .function("height", &cahill_keyes_web_projection::height)
    .function("generateBaseMapSvg",
              &cahill_keyes_web_projection::generate_base_map_svg);

  emscripten::function("implementationName", &implementation_name);
}
