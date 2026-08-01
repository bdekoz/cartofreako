// Generate layered Cahill-Keyes face geometry.  -*- mode: C++ -*-

#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

namespace {

using a60::carto::ckproj;
using a60::carto::frame;

constexpr std::string_view output_basename = "geometry-ck-44-22";
constexpr std::string_view output_filename = "geometry-ck-44-22.svg";

// The public projection applies the one-degree registration adjustment used by
// the Visionscarto base map.  These are therefore the public longitudes of the
// four M-shaped map seams, expressed monotonically around the globe.
struct longitude_sector
{
  double west;
  double east;
  int north_octant;
  int south_octant;
};

constexpr std::array sectors {
  longitude_sector {159, 249, 1, 6},
  longitude_sector {-111, -21, 2, 7},
  longitude_sector {-21, 69, 3, 8},
  longitude_sector {69, 159, 4, 5},
};

constexpr double seam_epsilon = 1e-7;
constexpr double sample_step = 2.5;

struct named_path
{
  std::string id;
  svg::vrange points;
};

void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

double
canonical_longitude(double longitude)
{
  while (longitude > 180)
    longitude -= 360;
  while (longitude < -180)
    longitude += 360;
  return longitude;
}

void
append_projected(svg::vrange& points, const ckproj& projection,
                 const frame& map_frame, const double latitude,
                 const double longitude)
{
  const auto [x, y] = projection.meridians_to_point_2d(
    latitude, canonical_longitude(longitude));
  constexpr double tolerance = 1e-8;
  require(std::isfinite(x) && std::isfinite(y),
          "Cahill-Keyes geometry contains a non-finite point");
  require(x >= -tolerance && x <= map_frame.width() + tolerance
          && y >= -tolerance && y <= map_frame.height() + tolerance,
          "Cahill-Keyes geometry point lies outside its frame");

  const svg::point_2t point {x, y};
  if (points.empty() || points.back() != point)
    points.push_back(point);
}

void
append_parallel(svg::vrange& points, const ckproj& projection,
                const frame& map_frame, const double latitude,
                const double longitude_begin, const double longitude_end)
{
  const double direction = longitude_end >= longitude_begin ? 1 : -1;
  for (double longitude = longitude_begin;
       direction * (longitude_end - longitude) > 0;
       longitude += direction * sample_step)
    append_projected(points, projection, map_frame, latitude, longitude);
  append_projected(points, projection, map_frame, latitude, longitude_end);
}

void
append_meridian(svg::vrange& points, const ckproj& projection,
                const frame& map_frame, const double longitude,
                const double latitude_begin, const double latitude_end)
{
  const double direction = latitude_end >= latitude_begin ? 1 : -1;
  for (double latitude = latitude_begin;
       direction * (latitude_end - latitude) > 0;
       latitude += direction * sample_step)
    append_projected(points, projection, map_frame, latitude, longitude);
  append_projected(points, projection, map_frame, latitude_end, longitude);
}

double
sector_center(const longitude_sector& sector)
{ return (sector.west + sector.east) / 2; }

svg::vrange
make_octant_outline(const ckproj& projection, const frame& map_frame,
                    const longitude_sector& sector,
                    const double hemisphere)
{
  const double west = sector.west + seam_epsilon;
  const double east = sector.east - seam_epsilon;
  const double center = sector_center(sector);
  const double pole = hemisphere * 90;
  const double near_pole = hemisphere * (90 - seam_epsilon);

  svg::vrange points;
  append_parallel(points, projection, map_frame, 0, west, east);
  append_meridian(points, projection, map_frame, east, 0, near_pole);
  append_projected(points, projection, map_frame, pole, center);
  append_meridian(points, projection, map_frame, west, near_pole, 0);
  return points;
}

svg::vrange
make_half_octant_outline(const ckproj& projection, const frame& map_frame,
                         const longitude_sector& sector,
                         const double hemisphere, const bool eastern_half)
{
  const double west = sector.west + seam_epsilon;
  const double east = sector.east - seam_epsilon;
  const double center = sector_center(sector);
  const double pole = hemisphere * 90;
  const double near_pole = hemisphere * (90 - seam_epsilon);

  svg::vrange points;
  if (eastern_half)
    {
      append_parallel(points, projection, map_frame, 0, center, east);
      append_meridian(points, projection, map_frame, east, 0, near_pole);
      append_projected(points, projection, map_frame, pole, center);
      append_meridian(points, projection, map_frame, center, near_pole, 0);
    }
  else
    {
      append_parallel(points, projection, map_frame, 0, west, center);
      append_meridian(points, projection, map_frame, center, 0, near_pole);
      append_projected(points, projection, map_frame, pole, center);
      append_meridian(points, projection, map_frame, west, near_pole, 0);
    }
  return points;
}

std::vector<named_path>
make_quadrants(const frame& map_frame)
{
  std::vector<named_path> paths;
  const double quadrant_width = map_frame.width() / 4;
  for (int quadrant = 0; quadrant != 4; ++quadrant)
    {
      const double x0 = quadrant * quadrant_width;
      const double x1 = (quadrant + 1) * quadrant_width;
      paths.push_back({
        "quadrant-" + std::to_string(quadrant + 1),
        {{x0, 0}, {x1, 0}, {x1, map_frame.height()},
         {x0, map_frame.height()}},
      });
    }
  return paths;
}

void
add_path_layer(svg::svg_element& document, const std::string& layer_id,
               const std::vector<named_path>& paths, const svg::style& style)
{
  svg::group_element layer;
  layer.start_element(layer_id);
  for (const auto& path : paths)
    {
      require(path.points.size() >= 3,
              "Cahill-Keyes geometry path has too few points");
      std::string path_data = svg::make_path_data_from_points(path.points);
      path_data += "Z";
      layer.add_element(svg::make_path(path_data, style, path.id));
    }
  layer.finish_element();
  document.add_element(layer);
}

std::size_t
layer_path_count(const std::string& document, const std::string& layer_id)
{
  const std::string opening = "<g id=\"" + layer_id + "\">";
  const std::size_t begin = document.find(opening);
  require(begin != std::string::npos, "generated SVG is missing layer " + layer_id);
  const std::size_t end = document.find("</g>", begin);
  require(end != std::string::npos,
          "generated SVG has an unterminated layer " + layer_id);

  std::size_t count = 0;
  std::size_t position = begin;
  while ((position = document.find("<path ", position)) != std::string::npos
         && position < end)
    {
      ++count;
      ++position;
    }
  return count;
}

} // namespace

void
test_ck_grids(const frame size)
{
  require(a60::carto::is_cahill_keyes_frame(size),
          "test_ck_grids requires a finite, positive 2:1 frame");
  require(size.width() == 44 && size.height() == 22,
          "this generator writes the 44 by 22 Cahill-Keyes fixture");

  const ckproj projection = a60::carto::make_cahill_keyes_projection(
    size, std::string(output_basename));

  std::vector<named_path> triangular_faces;
  std::vector<named_path> octants;
  std::vector<named_path> half_octants;
  for (const auto& sector : sectors)
    {
      for (const auto [hemisphere, octant]
           : std::array<std::pair<double, int>, 2> {
               std::pair {1.0, sector.north_octant},
               std::pair {-1.0, sector.south_octant},
             })
        {
          const std::string number = std::to_string(octant);
          svg::vrange outline = make_octant_outline(
            projection, size, sector, hemisphere);
          triangular_faces.push_back({"triangular-face-" + number, outline});
          octants.push_back({"octant-" + number, std::move(outline)});
          half_octants.push_back({
            "half-octant-" + number + "-west",
            make_half_octant_outline(
              projection, size, sector, hemisphere, false),
          });
          half_octants.push_back({
            "half-octant-" + number + "-east",
            make_half_octant_outline(
              projection, size, sector, hemisphere, true),
          });
        }
    }

  require(triangular_faces.size() == 8, "expected eight triangular faces");
  require(octants.size() == 8, "expected eight octants");
  require(half_octants.size() == 16, "expected sixteen half-octants");

  // Quadrants match cartography::point_to_x_quadrant: four equal-width map
  // regions.  The other layers are sampled in geographic space and projected.
  const std::vector<named_path> quadrants = make_quadrants(size);
  const svg::style face_style {
    svg::color::gray05, 0.55, svg::color::gray50, 0.60, 0.04,
  };
  const svg::style quadrant_style {
    svg::color::none, 0, svg::color::blue, 0.65, 0.08,
  };
  const svg::style octant_style {
    svg::color::none, 0, svg::color::black, 0.90, 0.12,
  };
  const svg::style half_octant_style {
    svg::color::none, 0, svg::color::red, 0.70, 0.055,
  };

  svg::svg_element document(
    std::string(output_basename),
    "Cahill-Keyes triangular faces, map quadrants, octants, and half-octants",
    size.frame_area);
  add_path_layer(document, "triangular-faces", triangular_faces, face_style);
  add_path_layer(document, "quadrants", quadrants, quadrant_style);
  add_path_layer(document, "octants", octants, octant_style);
  add_path_layer(document, "half-octants", half_octants, half_octant_style);
}

int
main()
{
  test_ck_grids(frame {44, 22});

  std::ifstream input {std::string(output_filename)};
  require(input.good(), "failed to open generated Cahill-Keyes SVG");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find("viewBox=\"0 0 44.000000 22.000000\"")
            != std::string::npos,
          "generated SVG does not use the requested 44 by 22 viewBox");
  require(layer_path_count(generated, "triangular-faces") == 8,
          "triangular-faces layer must contain eight paths");
  require(layer_path_count(generated, "quadrants") == 4,
          "quadrants layer must contain four paths");
  require(layer_path_count(generated, "octants") == 8,
          "octants layer must contain eight paths");
  require(layer_path_count(generated, "half-octants") == 16,
          "half-octants layer must contain sixteen paths");
  require(generated.find("nan") == std::string::npos
          && generated.find("inf") == std::string::npos,
          "generated SVG contains a non-finite coordinate");
}
