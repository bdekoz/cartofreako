// Network Groundstations generator: alpha60 Starlink gateway style.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_GROUNDSTATIONS_GENERATION_H
#define CART0FREAK0_NETWORK_GROUNDSTATIONS_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "network-groundstations-data.h"
#include "network-infrastructure-generation.h"
#include "projection-generation-common.h"

namespace cart0freak0::network_groundstations_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;
namespace infrastructure
  = cart0freak0::network_infrastructure_generation;

inline std::string
xml_escape(std::string value)
{
  constexpr std::array replacements {
    std::pair {std::string_view {"&"}, std::string_view {"&amp;"}},
    std::pair {std::string_view {"\""}, std::string_view {"&quot;"}},
    std::pair {std::string_view {"<"}, std::string_view {"&lt;"}},
    std::pair {std::string_view {">"}, std::string_view {"&gt;"}},
  };
  for (const auto& [source, replacement] : replacements)
    {
      std::size_t position = 0;
      while ((position = value.find(source, position)) != std::string_view::npos)
        {
          value.replace(position, source.size(), replacement);
          position += replacement.size();
        }
    }
  return value;
}

inline std::string
format_number(const double value, const int precision = 6)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline std::string
polygon_path(const svg::point_2t origin, const double radius,
             const unsigned points)
{
  const double angle = 360.0 / points;
  const double zero = svg::zero_angle_north_cw(angle);
  svg::vrange vertices;
  vertices.reserve(points + 1);
  for (unsigned index = 0; index < points; ++index)
    vertices.push_back(svg::get_circumference_point_d(
      zero + angle * index, radius, origin));
  vertices.push_back(vertices.front());
  return svg::make_path_data_from_points(vertices);
}

inline void
add_polygon(svg::group_element& layer, const svg::point_2t origin,
            const svg::style& style, const double radius,
            const unsigned points, const std::string& attributes = {})
{
  layer.add_element(svg::make_path(
    polygon_path(origin, radius, points), style, "", true, attributes));
}

inline void
add_line(svg::group_element& layer, const svg::point_2t start,
         const svg::point_2t finish, const svg::style& style,
         const std::string& attributes = {})
{
  svg::line_element line;
  line.start_element();
  line.add_data({std::get<0>(start), std::get<0>(finish),
                 std::get<1>(start), std::get<1>(finish)});
  line.add_style(style);
  if (!attributes.empty())
    line.add_raw(attributes);
  line.finish_element();
  layer.add_element(line);
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("network-groundstations-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{242, 244, 243}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"network-groundstations-ocean\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_subdued_land(generation::projection_document& document,
                 const generation::projection_context& context)
{
  const natural_earth::layer_spec land {
    "terrestrial-land", "Subdued Natural Earth 1:10m land",
    "ne_10m_land.shp", natural_earth::geometry_role::area,
    natural_earth::area_style({216, 221, 219}), 0.05, 0.82,
  };
  svg::group_element layer;
  layer.start_element(std::string(land.id));
  layer.add_title(std::string(land.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(context);
      static_cast<void>(natural_earth::render_star_x_source(
        layer, land, context, cap));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, land, context));
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
station_attributes(const groundstation_link& station)
{
  return "data-groundstation=\"true\" data-name=\""
    + xml_escape(station.name) + "\" data-latitude=\""
    + format_number(station.latitude, 6) + "\" data-longitude=\""
    + format_number(station.longitude, 6) + "\"";
}

inline void
add_gateway_links(generation::projection_document& document,
                  const generation::projection_context& context,
                  const groundstations_dataset& dataset)
{
  svg::group_element layer;
  layer.start_element("starlink-gateway-links");
  const svg::style link_style {
    svg::color::none, 0, {255, 29, 16}, 0.45, 0.006,
  };
  for (const groundstation_link& station : dataset.stations)
    {
      if (station.path.size() < 2)
        continue;
      std::vector<generation::geographic_point> geographic;
      geographic.reserve(station.path.size());
      for (const auto& [longitude, latitude] : station.path)
        geographic.push_back({latitude, longitude});
      const std::string path_data
        = infrastructure::project_open_path(context, geographic);
      if (!path_data.empty())
        layer.add_element(svg::make_path(
          path_data, link_style, "", true,
          "data-gateway-link=\"true\" data-name=\""
            + xml_escape(station.name) + "\""));
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_gateways(generation::projection_document& document,
             const generation::projection_context& context,
             const groundstations_dataset& dataset,
             const groundstations_profile& profile)
{
  svg::group_element layer;
  layer.start_element("starlink-gateways-20250902");
  const svg::style gateway_style {
    {255, 29, 16}, 0.33, {255, 29, 16}, 1.0, 0.010,
  };
  for (const groundstation_link& station : dataset.stations)
    {
      const generation::geographic_point geographic {
        station.latitude, station.longitude,
      };
      const svg::point_2t point
        = generation::project_point(context, geographic);
      add_polygon(layer, point, gateway_style, profile.marker_radius, 3,
                  station_attributes(station));
    }
  layer.finish_element();
  document.add_element(layer);
}

inline svg::typography
label_typography(const double size = 0.13,
                 const svg::color_qi color = {37, 48, 51})
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 1, {250, 251, 250}, 0.94, 0.012};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline void
add_legend(generation::projection_document& document,
           const generation::projection_context& context,
           const groundstations_dataset& dataset,
           const groundstations_profile& profile)
{
  svg::group_element layer;
  layer.start_element("network-groundstations-legend-and-provenance");
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, context.map_frame.width(), 0.82});
  band.add_style({{226, 230, 228}, 0.96, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = label_typography(0.44, {176, 23, 12});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer,
    xml_escape("NETWORK GROUNDSTATIONS / " + dataset.datestamp),
    {0.32, 0.27}, title);
  svg::styled_text(layer,
    xml_escape(std::to_string(dataset.stations.size())
      + " Starlink gateway/pop records  |  "
      + profile.source_repository),
    {0.32, 0.62}, label_typography(0.112, {55, 67, 72}));
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const generation::projection_spec& spec,
                 const groundstations_profile& profile,
                 const groundstations_dataset& dataset)
{
  return "<metadata id=\"network-groundstations-metadata\""
    " data-workflow=\"Network groundstations\""
    " data-profile=\"" + xml_escape(profile.path.filename().string()) + "\""
    " data-marker-radius-inches=\""
      + format_number(profile.marker_radius, 3)
      + "\" data-background-color=\"#f2f4f3\" data-title-scale=\"2\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-dataset-id=\"" + xml_escape(dataset.id) + "\""
    " data-datestamp=\"" + xml_escape(dataset.datestamp) + "\""
    " data-feature-count=\"" + std::to_string(dataset.stations.size()) + "\""
    " data-source-repository=\"" + xml_escape(profile.source_repository) + "\""
    " data-source-commit=\"" + xml_escape(profile.source_commit) + "\""
    " data-source-license=\"" + xml_escape(profile.source_license) + "\""
    " data-source-gateways-sha256=\""
      + xml_escape(profile.gateways_sha256) + "\""
    "></metadata>\n";
}

inline std::string
output_basename(const generation::projection_spec& spec)
{
  return generation::output_basename("network-groundstations", spec);
}

inline void
generate(const generation::projection_spec& spec,
         const groundstations_profile& profile,
         const groundstations_dataset& dataset)
{
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, std::string(spec.title) + " network groundstations for "
      + dataset.datestamp, context.map_frame.frame_area);
  document.add_raw(metadata_element(spec, profile, dataset));
  add_background(document, context);
  natural_earth::initialize_gdal();
  add_subdued_land(document, context);
  add_gateway_links(document, context, dataset);
  add_gateways(document, context, dataset, profile);
  add_legend(document, context, dataset, profile);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  network_groundstations_require(input.good(),
    "failed to open generated " + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
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

inline void
verify(const std::string& generated,
       const generation::projection_context& context,
       const groundstations_dataset& dataset)
{
  network_groundstations_require(
    generated.find(generation::view_box_fragment(context))
      != std::string::npos,
    "generated Network-groundstations SVG has the wrong viewBox");
  constexpr std::array layers {
    "network-groundstations-background", "terrestrial-land",
    "starlink-gateway-links", "starlink-gateways-20250902",
    "network-groundstations-legend-and-provenance",
  };
  for (const std::string_view layer : layers)
    network_groundstations_require(
      generated.find("<g id=\"" + std::string(layer) + "\">")
        != std::string::npos,
      "generated Network-groundstations SVG is missing layer "
        + std::string(layer));
  network_groundstations_require(
    generated.find("id=\"network-groundstations-metadata\"")
      != std::string::npos
      && generated.find("data-background-color=\"#f2f4f3\"")
           != std::string::npos
      && generated.find("data-source-gateways-sha256=\""
        + dataset.source_sha256 + "\"") != std::string::npos,
    "generated Network-groundstations SVG is missing provenance metadata");
  network_groundstations_require(
    token_count(generated, "data-groundstation=\"true\"")
      == dataset.stations.size(),
    "generated Network-groundstations SVG has the wrong feature count");
  network_groundstations_require(
    generated.find(" nan") == std::string::npos
      && generated.find(" -nan") == std::string::npos
      && generated.find(" inf") == std::string::npos
      && generated.find(" -inf") == std::string::npos,
    "generated Network-groundstations SVG has non-finite data");
  generation::verify_configured_label_font(
    generated, "Network-groundstations SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 3)
    throw std::invalid_argument(
      "usage: generate-network-groundstations PROJECTION DATA_DIRECTORY");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const fs::path data_dir = std::filesystem::absolute(argv[2]);
  const groundstations_profile profile = load_groundstations_profile(
    data_dir / "network-groundstations-profile.json");
  const groundstations_dataset dataset = load_groundstations_dataset(
    data_dir / "starlink-global-gateways-pops.20250902.json", profile);
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec, profile, dataset);
  verify(read_generated(basename), context, dataset);
  return 0;
}

} // namespace cart0freak0::network_groundstations_generation

#endif
