// Generate a labeled Cahill-Keyes graticule.  -*- mode: C++ -*-

#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

namespace {

using a60::carto::ckproj;
using a60::carto::frame;

constexpr std::string_view output_basename = "graticules-ck-44-22";
constexpr std::string_view output_filename = "graticules-ck-44-22.svg";

// Match the conventional ten-degree graticule in the checked-in
// Visionscarto reference. A 2.5-degree sampling step follows its curves while
// keeping the diagnostic SVG compact.
constexpr int graticule_step = 10;
constexpr double sample_step = 2.5;
constexpr double seam_epsilon = 1e-7;

// Public seam longitudes include ckproj's one-degree raster-registration
// adjustment. The first sector is deliberately unwrapped past 180 degrees.
struct longitude_sector
{
  double west;
  double east;
};

constexpr std::array sectors {
  longitude_sector {159, 249},
  longitude_sector {-111, -21},
  longitude_sector {-21, 69},
  longitude_sector {69, 159},
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

svg::point_2t
project_point(const ckproj& projection, const frame& map_frame,
              const double latitude, const double longitude)
{
  const auto [x, y] = projection.meridians_to_point_2d(
    latitude, canonical_longitude(longitude));
  constexpr double tolerance = 1e-8;
  require(std::isfinite(x) && std::isfinite(y),
          "Cahill-Keyes graticule contains a non-finite point");
  require(x >= -tolerance && x <= map_frame.width() + tolerance
          && y >= -tolerance && y <= map_frame.height() + tolerance,
          "Cahill-Keyes graticule point lies outside its frame");
  return {x, y};
}

void
append_projected(svg::vrange& points, const ckproj& projection,
                 const frame& map_frame, const double latitude,
                 const double longitude)
{
  const svg::point_2t point = project_point(
    projection, map_frame, latitude, longitude);
  if (points.empty() || points.back() != point)
    points.push_back(point);
}

void
append_parallel(svg::vrange& points, const ckproj& projection,
                const frame& map_frame, const double latitude,
                const double longitude_begin, const double longitude_end)
{
  for (double longitude = longitude_begin; longitude < longitude_end;
       longitude += sample_step)
    append_projected(points, projection, map_frame, latitude, longitude);
  append_projected(
    points, projection, map_frame, latitude, longitude_end);
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
  append_projected(
    points, projection, map_frame, latitude_end, longitude);
}

std::vector<svg::vrange>
make_parallel_segments(const ckproj& projection, const frame& map_frame,
                       const double latitude)
{
  std::vector<svg::vrange> segments;
  for (const longitude_sector& sector : sectors)
    {
      svg::vrange points;
      append_parallel(points, projection, map_frame, latitude,
                      sector.west + seam_epsilon,
                      sector.east - seam_epsilon);
      segments.push_back(std::move(points));
    }
  return segments;
}

std::vector<svg::vrange>
make_meridian_segments(const ckproj& projection, const frame& map_frame,
                       const double longitude)
{
  // Keep the two hemispheres as separate paths. They meet at the equator but
  // belong to different octahedral faces in the unfolded M-shaped net.
  svg::vrange southern;
  append_meridian(
    southern, projection, map_frame, longitude, -90, 0);
  svg::vrange northern;
  append_meridian(
    northern, projection, map_frame, longitude, 0, 90);
  return {std::move(southern), std::move(northern)};
}

std::string
coordinate_id(const std::string_view kind, const int coordinate,
              const std::string_view negative,
              const std::string_view positive)
{
  std::string id(kind);
  id += '-';
  id += std::to_string(std::abs(coordinate));
  if (coordinate < 0)
    {
      id += '-';
      id += negative;
    }
  else if (coordinate > 0)
    {
      id += '-';
      id += positive;
    }
  return id;
}

std::string
coordinate_label(const int coordinate, const std::string_view negative,
                 const std::string_view positive,
                 const bool unsigned_antimeridian = false)
{
  std::string label = std::to_string(std::abs(coordinate));
  label += "\u00b0";
  if (unsigned_antimeridian && std::abs(coordinate) == 180)
    return label;
  if (coordinate < 0)
    label += negative;
  else if (coordinate > 0)
    label += positive;
  return label;
}

svg::typography
make_label_typography(const svg::color color)
{
  svg::typography typography = svg::k::smono_typo;
  typography._M_size = 0.25;
  typography._M_style = {
    color, 0.95, svg::color::white, 0, 0,
  };
  typography._M_anchor = svg::typography::anchor::middle;
  typography._M_align = svg::typography::align::center;
  typography._M_baseline = svg::typography::baseline::central;
  return typography;
}

void
add_labeled_line(svg::group_element& layer, const std::string& id,
                 const std::string& label,
                 const std::vector<svg::vrange>& segments,
                 const svg::point_2t label_point, const svg::style& style,
                 const svg::typography& typography)
{
  svg::group_element line;
  line.start_element(id);
  line.add_title(label);
  for (std::size_t index = 0; index != segments.size(); ++index)
    {
      require(segments[index].size() >= 2,
              "Cahill-Keyes graticule path has too few points");
      const std::string path_data
        = svg::make_path_data_from_points(segments[index]);
      const std::string path_id
        = id + "-segment-" + std::to_string(index + 1);
      line.add_element(svg::make_path(path_data, style, path_id));
    }
  svg::styled_text(line, label, label_point, typography);
  line.finish_element();
  layer.add_element(line);
}

std::string_view
layer_section(const std::string& document, const std::string& layer_id,
              const std::string& next_marker)
{
  const std::string opening = "<g id=\"" + layer_id + "\">";
  const std::size_t begin = document.find(opening);
  require(begin != std::string::npos,
          "generated SVG is missing layer " + layer_id);
  const std::size_t end = document.find(next_marker, begin + opening.size());
  require(end != std::string::npos,
          "generated SVG has an unterminated layer " + layer_id);
  return std::string_view(document).substr(begin, end - begin);
}

std::size_t
token_count(const std::string_view text, const std::string_view token)
{
  std::size_t count = 0;
  std::size_t position = 0;
  while ((position = text.find(token, position)) != std::string_view::npos)
    {
      ++count;
      position += token.size();
    }
  return count;
}

} // namespace

void
test_ck_graticules(const frame size)
{
  require(a60::carto::is_cahill_keyes_frame(size),
          "test_ck_graticules requires a finite, positive 2:1 frame");
  require(size.width() == 44 && size.height() == 22,
          "this generator writes the 44 by 22 Cahill-Keyes fixture");

  const ckproj projection = a60::carto::make_cahill_keyes_projection(
    size, std::string(output_basename));
  const svg::style latitude_style {
    svg::color::none, 0, svg::color::steelblue, 0.55, 0.025,
  };
  const svg::style latitude_major_style {
    svg::color::none, 0, svg::color::blue, 0.80, 0.045,
  };
  const svg::style longitude_style {
    svg::color::none, 0, svg::color::asamaorange, 0.50, 0.025,
  };
  const svg::style longitude_major_style {
    svg::color::none, 0, svg::color::red, 0.75, 0.045,
  };
  const svg::typography latitude_typography
    = make_label_typography(svg::color::blue);
  const svg::typography longitude_typography
    = make_label_typography(svg::color::red);

  svg::svg_element document(
    std::string(output_basename),
    "Labeled ten-degree latitude and longitude graticules for the 44 by 22 "
    "Cahill-Keyes projection",
    size.frame_area);

  svg::group_element latitude_layer;
  latitude_layer.start_element("latitudes");
  for (int latitude = -80; latitude <= 80; latitude += graticule_step)
    {
      const std::string id = coordinate_id(
        "latitude", latitude, "south", "north");
      const std::string label = coordinate_label(latitude, "S", "N");
      auto [label_x, label_y] = project_point(
        projection, size, latitude, -156);
      label_x += 0.22;
      label_y -= 0.06;
      const bool major = latitude % 30 == 0;
      add_labeled_line(
        latitude_layer, id, label,
        make_parallel_segments(projection, size, latitude),
        {label_x, label_y},
        major ? latitude_major_style : latitude_style,
        latitude_typography);
    }
  latitude_layer.finish_element();
  document.add_element(latitude_layer);

  svg::group_element longitude_layer;
  longitude_layer.start_element("longitudes");
  int longitude_index = 0;
  for (int longitude = -180; longitude < 180;
       longitude += graticule_step, ++longitude_index)
    {
      const std::string id = coordinate_id(
        "longitude", longitude, "west", "east");
      const std::string label = coordinate_label(
        longitude, "W", "E", true);
      const double label_latitude = longitude_index % 2 == 0 ? -3.5 : 3.5;
      auto [label_x, label_y] = project_point(
        projection, size, label_latitude, longitude);
      label_x += 0.05;
      const bool major = longitude % 30 == 0;
      add_labeled_line(
        longitude_layer, id, label,
        make_meridian_segments(projection, size, longitude),
        {label_x, label_y},
        major ? longitude_major_style : longitude_style,
        longitude_typography);
    }
  longitude_layer.finish_element();
  document.add_element(longitude_layer);
}

int
main()
{
  test_ck_graticules(frame {44, 22});

  std::ifstream input {std::string(output_filename)};
  require(input.good(), "failed to open generated Cahill-Keyes graticule SVG");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find("viewBox=\"0 0 44.000000 22.000000\"")
            != std::string::npos,
          "generated SVG does not use the requested 44 by 22 viewBox");

  const std::string_view latitudes = layer_section(
    generated, "latitudes", "<g id=\"longitudes\">");
  const std::string_view longitudes = layer_section(
    generated, "longitudes", "</svg>");
  require(token_count(latitudes, "<g id=\"latitude-") == 17,
          "latitudes layer must contain seventeen labeled line groups");
  require(token_count(latitudes, "<path ") == 68,
          "each latitude must contain four seam-safe paths");
  require(token_count(latitudes, "<text ") == 17,
          "each latitude must contain one visible label");
  require(token_count(longitudes, "<g id=\"longitude-") == 36,
          "longitudes layer must contain thirty-six labeled line groups");
  require(token_count(longitudes, "<path ") == 72,
          "each longitude must contain two hemisphere paths");
  require(token_count(longitudes, "<text ") == 36,
          "each longitude must contain one visible label");
  require(token_count(generated, "\u00b0") >= 53,
          "every graticule line must have a degree label");
  require(generated.find(" nan") == std::string::npos
          && generated.find(" -nan") == std::string::npos
          && generated.find(" inf") == std::string::npos
          && generated.find(" -inf") == std::string::npos,
          "generated SVG contains a non-finite coordinate");
}
