// Projection-aware solar illumination and physical atmosphere rendering.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_CLOUD_ATMOSPHERE_GENERATION_H
#define CART0FREAK0_CLOUD_ATMOSPHERE_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <numbers>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>
#include <h3/h3api.h>

#include "cloud-atmosphere-data.h"
#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"
#include "solar-geometry.h"

namespace cart0freak0::cloud_atmosphere_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
xml_escape(std::string value)
{
  const std::array replacements {
    std::pair {std::string_view {"&"}, std::string_view {"&amp;"}},
    std::pair {std::string_view {"\""}, std::string_view {"&quot;"}},
    std::pair {std::string_view {"<"}, std::string_view {"&lt;"}},
    std::pair {std::string_view {">"}, std::string_view {"&gt;"}},
  };
  for (const auto& [source, replacement] : replacements)
    {
      std::size_t position = 0;
      while ((position = value.find(source, position)) != std::string::npos)
        {
          value.replace(position, source.size(), replacement);
          position += replacement.size();
        }
    }
  return value;
}

inline std::string
format_number(const double value, const int precision = 2)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline svg::color_qi
svg_color(const rgb_color color)
{
  using component = svg::color_qi::itype;
  return {static_cast<component>(color.red),
          static_cast<component>(color.green),
          static_cast<component>(color.blue)};
}

inline svg::typography
label_typography(const double size, const svg::color_qi color)
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 0.94, {241, 244, 245}, 0.88, 0.006};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline void
append_projected_polygon(std::string& path_data,
                         const generation::projection_context& context,
                         std::vector<generation::geographic_point> polygon)
{
  for (const svg::vrange& segment
       : generation::project_path(context, std::move(polygon), true))
    if (segment.size() >= 3)
      {
        path_data += svg::make_path_data_from_points(segment);
        path_data += "Z ";
      }
}

inline std::vector<generation::geographic_point>
h3_polygon(const H3Index cell)
{
  CellBoundary boundary {};
  atmosphere_require(cellToBoundary(cell, &boundary) == E_SUCCESS,
                     "failed to calculate H3 atmosphere-cell boundary");
  std::vector<generation::geographic_point> result;
  result.reserve(static_cast<std::size_t>(boundary.numVerts));
  for (int index = 0; index < boundary.numVerts; ++index)
    result.push_back({
      boundary.verts[index].lat * 180.0 / std::numbers::pi,
      boundary.verts[index].lng * 180.0 / std::numbers::pi,
    });
  return result;
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("cloud-atmosphere-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{17, 26, 38}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"cloud-atmosphere-ground\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline svg::style
solar_contour_style(const double altitude_deg)
{
  if (altitude_deg >= 60)
    return {svg::color::none, 0, {255, 224, 125}, 0.74, 0.020};
  if (altitude_deg >= 30)
    return {svg::color::none, 0, {238, 190, 79}, 0.62, 0.016};
  if (altitude_deg >= 0)
    return {svg::color::none, 0, {213, 139, 78}, 0.72, 0.022};
  if (altitude_deg >= -6)
    return {svg::color::none, 0, {172, 101, 96}, 0.72, 0.019};
  if (altitude_deg >= -12)
    return {svg::color::none, 0, {112, 88, 135}, 0.74, 0.017};
  return {svg::color::none, 0, {72, 72, 118}, 0.78, 0.015};
}

inline std::vector<generation::geographic_point>
solar_altitude_contour(
  const solar_geometry::geographic_position subsolar,
  const double altitude_deg, const double step_deg)
{
  const double center_latitude = solar_geometry::degrees_to_radians(
    subsolar.latitude_deg);
  const double center_longitude = solar_geometry::degrees_to_radians(
    subsolar.longitude_deg_east);
  const double angular_distance = solar_geometry::degrees_to_radians(
    90.0 - altitude_deg);
  const double sin_center = std::sin(center_latitude);
  const double cos_center = std::cos(center_latitude);
  const double sin_distance = std::sin(angular_distance);
  const double cos_distance = std::cos(angular_distance);
  std::vector<generation::geographic_point> result;
  result.reserve(static_cast<std::size_t>(std::ceil(360.0 / step_deg)));
  for (double bearing_deg = 0; bearing_deg < 360; bearing_deg += step_deg)
    {
      const double bearing = solar_geometry::degrees_to_radians(bearing_deg);
      const double latitude = std::asin(std::clamp(
        sin_center * cos_distance
          + cos_center * sin_distance * std::cos(bearing),
        -1.0, 1.0));
      const double longitude = center_longitude + std::atan2(
        std::sin(bearing) * sin_distance * cos_center,
        cos_distance - sin_center * std::sin(latitude));
      result.push_back({solar_geometry::radians_to_degrees(latitude),
                        solar_geometry::normalize_signed_degrees(
                          solar_geometry::radians_to_degrees(longitude))});
    }
  return result;
}

inline std::string_view
solar_contour_id(const double altitude_deg)
{
  if (altitude_deg == 60) return "solar-altitude-60";
  if (altitude_deg == 30) return "solar-altitude-30";
  if (altitude_deg == 0) return "solar-day-boundary";
  if (altitude_deg == -6) return "solar-civil-boundary";
  if (altitude_deg == -12) return "solar-nautical-boundary";
  return "solar-astronomical-boundary";
}

inline std::vector<svg::vrange>
project_solar_contour(
  const generation::projection_context& context,
  std::vector<generation::geographic_point> source)
{
  std::vector<std::vector<generation::geographic_point>> pieces(1);
  source.push_back(source.front());
  for (const generation::geographic_point point : source)
    {
      if (!pieces.back().empty())
        {
          const generation::geographic_point previous = pieces.back().back();
          if (std::abs(point.longitude - previous.longitude) > 180)
            {
              const bool eastward = previous.longitude > 0;
              const double unwrapped = point.longitude
                + (eastward ? 360.0 : -360.0);
              const double boundary = eastward ? 180.0 : -180.0;
              const double fraction = (boundary - previous.longitude)
                / (unwrapped - previous.longitude);
              const double latitude = previous.latitude
                + fraction * (point.latitude - previous.latitude);
              pieces.back().push_back({latitude, boundary});
              pieces.push_back({{latitude, -boundary}});
            }
        }
      pieces.back().push_back(point);
    }

  std::vector<svg::vrange> result;
  for (auto& piece : pieces)
    if (piece.size() >= 2)
      for (svg::vrange& segment
           : generation::project_path(context, std::move(piece), false))
        if (segment.size() >= 2)
          result.push_back(std::move(segment));
  return result;
}

inline void
add_solar_illumination(generation::projection_document& document,
                       const generation::projection_context& context,
                       const atmosphere_profile& profile,
                       const solar_geometry::geographic_position subsolar)
{
  svg::group_element layer;
  layer.start_element("solar-illumination");
  layer.add_title("Process-instant solar-altitude and twilight contours");
  constexpr std::array altitudes {60.0, 30.0, 0.0, -6.0, -12.0, -18.0};
  for (const double altitude : altitudes)
    {
      std::vector<svg::vrange> segments = project_solar_contour(
        context, solar_altitude_contour(
          subsolar, altitude, profile.solar_contour_step_degrees));
      for (std::size_t index = 0; index < segments.size(); ++index)
        if (segments[index].size() >= 2)
          layer.add_element(svg::make_path(
            svg::make_path_data_from_points(segments[index]),
            solar_contour_style(altitude),
            std::string(solar_contour_id(altitude)) + "-segment-"
              + std::to_string(index + 1), true,
            "data-calculated=\"true\" data-solar-altitude-deg=\""
              + format_number(altitude, 0) + "\""));
    }
  const svg::point_2t point = generation::project_point(
    context, {subsolar.latitude_deg, subsolar.longitude_deg_east});
  svg::circle_element marker;
  marker.start_element();
  marker.add_data({std::get<0>(point), std::get<1>(point), 0.11});
  marker.add_style({svg::color::gold, 0.95, svg::color::lemonchiffon,
                    1, 0.018});
  marker.add_raw("id=\"subsolar-point\" data-calculated=\"true\"");
  marker.finish_element();
  layer.add_element(marker);
  layer.finish_element();
  document.add_element(layer);
}

inline bool
outline_layer(const std::string_view property)
{
  return property == "aerosol_optical_depth_500nm"
    || property == "cloud_top_height_km"
    || property == "cloud_type_isccp";
}

inline unsigned
value_bin(const double value, const layer_definition& layer)
{
  constexpr unsigned bin_count = 6;
  const double scaled = std::clamp(
    (value - layer.scale_min) / (layer.scale_max - layer.scale_min),
    0.0, 1.0);
  return std::min(bin_count - 1,
                  static_cast<unsigned>(scaled * bin_count));
}

inline std::size_t
add_observation_layer(generation::projection_document& document,
                      const generation::projection_context& context,
                      const atmosphere_profile& profile,
                      const atmosphere_dataset& dataset,
                      const std::size_t layer_number)
{
  constexpr std::size_t bin_count = 6;
  const layer_definition& definition = profile.layers[layer_number];
  svg::group_element layer;
  layer.start_element(definition.id);
  layer.add_title(definition.title + " [" + definition.unit + "]");
  std::array<std::string, bin_count> paths;
  std::array<std::size_t, bin_count> counts {};
  for (const atmosphere_cell& cell : dataset.cells)
    if (cell.values[layer_number].has_value())
      {
        const unsigned bin = value_bin(*cell.values[layer_number], definition);
        append_projected_polygon(paths[bin], context, h3_polygon(cell.h3));
        ++counts[bin];
      }

  std::size_t rendered = 0;
  for (std::size_t bin = 0; bin < bin_count; ++bin)
    if (!paths[bin].empty())
      {
        const double fraction = (bin + 1.0) / bin_count;
        const svg::color_qi color = svg_color(definition.color);
        svg::style style;
        if (outline_layer(definition.property))
          style = {svg::color::none, 0, color,
                   std::min(1.0, definition.opacity * (0.35 + 0.65 * fraction)),
                   0.008 + 0.018 * fraction};
        else
          style = {color, definition.opacity * (0.18 + 0.82 * fraction),
                   color, std::min(1.0, definition.opacity + 0.12), 0.0025};
        std::string attributes = "data-atmosphere-observation=\"true\""
          " data-property=\"" + definition.property + "\""
          " data-source=\"" + definition.source_id + "\""
          " data-bin=\"" + std::to_string(bin + 1) + "\""
          " data-cell-count=\"" + std::to_string(counts[bin]) + "\"";
        layer.add_element(svg::make_path(
          paths[bin], style,
          definition.id + "-bin-" + std::to_string(bin + 1), true,
          attributes));
        rendered += counts[bin];
      }
  layer.finish_element();
  document.add_element(layer);
  return rendered;
}

inline void
add_coastline(generation::projection_document& document,
              const generation::projection_context& context)
{
  const natural_earth::layer_spec coastline {
    "terrestrial-coastline", "Natural Earth 1:10m coastline",
    "ne_10m_coastline.shp", natural_earth::geometry_role::line,
    natural_earth::line_style({198, 211, 219}, 0.018, 0.72), 0.03, 0.82,
  };
  svg::group_element layer;
  layer.start_element(std::string(coastline.id));
  layer.add_title(std::string(coastline.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(
          context, natural_earth::land_spec);
      static_cast<void>(natural_earth::render_star_x_source(
        layer, coastline, context, cap));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, coastline, context));
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
short_layer_title(const layer_definition& layer)
{
  if (layer.property == "shortwave_radiation_w_m2")
    return "surface SWR";
  if (layer.property == "aerosol_optical_depth_500nm")
    return "AOD 500 nm";
  if (layer.property == "precipitation_rate_mm_h")
    return "precipitation";
  if (layer.property == "cloud_optical_thickness")
    return "cloud optical thickness";
  if (layer.property == "cloud_top_height_km")
    return "cloud-top height";
  if (layer.property == "cloud_type_isccp")
    return "ISCCP cloud type";
  return layer.title;
}

inline void
add_legend(generation::projection_document& document,
           const generation::projection_context& context,
           const atmosphere_profile& profile,
           const atmosphere_dataset& dataset,
           const generation_time::instant& process_start,
           const solar_geometry::geographic_position subsolar)
{
  if (!profile.show_legend)
    return;
  svg::group_element layer;
  layer.start_element("legend-and-provenance");
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, context.map_frame.width(), 1.05});
  band.add_style({{241, 244, 245}, 0.94, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = label_typography(0.20, {28, 38, 46});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer,
    "SOLAR / CLOUD / ATMOSPHERE" + std::string(dataset.fixture ? " — FIXTURE" : ""),
    {0.30, 0.20}, title);
  svg::styled_text(layer,
    xml_escape(process_start.iso_utc + " process start  |  subsolar "
      + format_number(subsolar.latitude_deg) + "°, "
      + format_number(subsolar.longitude_deg_east) + "°E  |  missing is unobserved"),
    {0.30, 0.41}, label_typography(0.102, {67, 74, 79}));

  const std::size_t columns = 4;
  const double column_width = (context.map_frame.width() - 0.6) / columns;
  std::size_t position = 0;
  for (const layer_definition& definition : profile.layers)
    if (definition.enabled
        && (profile.show_cloud_type
              || definition.property != "cloud_type_isccp"))
      {
        const std::size_t row = position / columns;
        const std::size_t column = position % columns;
        const double x = 0.32 + column * column_width;
        const double y = 0.65 + row * 0.20;
        svg::circle_element marker;
        marker.start_element();
        marker.add_data({x, y, 0.035});
        marker.add_style({svg_color(definition.color), 0.78,
                          svg_color(definition.color), 1, 0.006});
        marker.finish_element();
        layer.add_element(marker);
        const observation_metadata& observation = observation_for(
          dataset, definition.source_id);
        const double age = generation_time::age_hours(
          process_start, observation.end);
        svg::styled_text(layer,
          xml_escape(short_layer_title(definition) + " (" + format_number(age, 1)
            + " h)"), {x + 0.07, y},
          label_typography(0.097, {45, 52, 57}));
        ++position;
      }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_coverage_note(generation::projection_document& document,
                  const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("coverage-note");
  svg::typography text = label_typography(0.090, {207, 218, 225});
  text._M_anchor = svg::typography::anchor::middle;
  text._M_align = svg::typography::align::center;
  svg::styled_text(layer,
    "Data: JAXA/EORC P-Tree, GCOM-C, GSMaP, and JASMES (MODIS source: NASA). P-Tree clouds are regional/daytime; AOD is not smoke or PM2.5.",
    {context.map_frame.width() / 2, context.map_frame.height() - 0.18}, text);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const generation::projection_spec& spec,
                 const atmosphere_profile& profile,
                 const atmosphere_dataset& dataset,
                 const generation_time::instant& process_start,
                 const solar_geometry::geographic_position subsolar)
{
  std::string result = "<metadata id=\"cloud-atmosphere-metadata\""
    " data-workflow=\"JAXA physical atmosphere snapshot\""
    " data-profile=\"" + xml_escape(profile.path.filename().string()) + "\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-process-start-utc=\"" + process_start.iso_utc + "\""
    " data-time-policy=\"process-start\""
    " data-source-selection=\"latest-not-after\""
    " data-source-selection-process-start-utc=\""
      + dataset.source_selection_process_start.iso_utc + "\""
    " data-subsolar-latitude-deg=\"" + format_number(subsolar.latitude_deg, 6) + "\""
    " data-subsolar-longitude-deg-east=\"" + format_number(subsolar.longitude_deg_east, 6) + "\""
    " data-h3-resolution=\"" + std::to_string(profile.h3_resolution) + "\""
    " data-feature-count=\"" + std::to_string(dataset.cells.size()) + "\""
    " data-fixture=\"" + std::string(dataset.fixture ? "true" : "false") + "\""
    " data-credit=\"JAXA/EORC; JASMES MODIS source NASA\""
    " data-missing-semantics=\"unobserved-not-zero\""
    " data-aod-is-smoke=\"false\""
    " data-precipitation-is-event-count=\"false\"";
  for (const observation_metadata& observation : dataset.observations)
    result += " data-observation-" + observation.source_id + "-end=\""
      + observation.end.iso_utc + "\"";
  return result + "></metadata>\n";
}

inline std::string
output_basename(const generation::projection_spec& spec)
{ return generation::output_basename("cloud-atmosphere", spec); }

inline void
generate(const generation::projection_spec& spec,
         const atmosphere_profile& profile,
         const atmosphere_dataset& dataset,
         const generation_time::instant& process_start)
{
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  const solar_geometry::geographic_position subsolar
    = solar_geometry::subsolar_position(process_start);
  generation::projection_document document(
    basename, std::string(spec.title)
      + " solar illumination, cloud, and atmosphere snapshot",
    context.map_frame.frame_area);
  document.add_raw(metadata_element(
    spec, profile, dataset, process_start, subsolar));
  add_background(document, context);
  add_solar_illumination(document, context, profile, subsolar);
  for (std::size_t index = 0; index < profile.layers.size(); ++index)
    if (profile.layers[index].enabled
        && (profile.show_cloud_type
              || profile.layers[index].property != "cloud_type_isccp"))
      static_cast<void>(add_observation_layer(
        document, context, profile, dataset, index));
  natural_earth::initialize_gdal();
  add_coastline(document, context);
  add_legend(document, context, profile, dataset, process_start, subsolar);
  add_coverage_note(document, context);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  atmosphere_require(input.good(),
                     "failed to open generated " + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline void
verify(const std::string& generated,
       const generation::projection_context& context,
       const atmosphere_profile& profile,
       const atmosphere_dataset& dataset,
       const generation_time::instant& process_start)
{
  atmosphere_require(generated.find(generation::view_box_fragment(context))
                       != std::string::npos,
                     "generated cloud-atmosphere SVG has the wrong viewBox");
  constexpr std::array required_layers {
    std::string_view {"cloud-atmosphere-background"},
    std::string_view {"solar-illumination"},
    std::string_view {"terrestrial-coastline"},
    std::string_view {"legend-and-provenance"},
    std::string_view {"coverage-note"},
  };
  for (const std::string_view layer : required_layers)
    atmosphere_require(generated.find("<g id=\"" + std::string(layer) + "\">")
                         != std::string::npos,
                       "generated cloud-atmosphere SVG is missing layer "
                         + std::string(layer));
  constexpr std::array required_solar_contours {
    std::string_view {"solar-altitude-60-segment-"},
    std::string_view {"solar-altitude-30-segment-"},
    std::string_view {"solar-day-boundary-segment-"},
    std::string_view {"solar-civil-boundary-segment-"},
    std::string_view {"solar-nautical-boundary-segment-"},
    std::string_view {"solar-astronomical-boundary-segment-"},
  };
  for (const std::string_view contour : required_solar_contours)
    atmosphere_require(generated.find("id=\"" + std::string(contour))
                         != std::string::npos,
                       "generated cloud-atmosphere SVG is missing "
                         + std::string(contour));
  for (const layer_definition& layer : profile.layers)
    if (layer.enabled
        && (profile.show_cloud_type || layer.property != "cloud_type_isccp"))
      atmosphere_require(generated.find("<g id=\"" + layer.id + "\">")
                           != std::string::npos,
                         "generated cloud-atmosphere SVG is missing " + layer.id);
  atmosphere_require(generated.find("id=\"cloud-atmosphere-metadata\"")
                       != std::string::npos
                       && generated.find("data-process-start-utc=\""
                         + process_start.iso_utc + "\"") != std::string::npos
                       && generated.find("data-source-selection=\"latest-not-after\"")
                            != std::string::npos
                       && generated.find("data-missing-semantics=\"unobserved-not-zero\"")
                            != std::string::npos,
                     "generated cloud-atmosphere SVG lacks time/provenance metadata");
  atmosphere_require(generated.find("celestial-reference") == std::string::npos
                       && generated.find("observer-horizon") == std::string::npos,
                     "cloud-atmosphere SVG duplicates astronomy layers");
  atmosphere_require(generated.find("data-aod-is-smoke=\"false\"")
                       != std::string::npos
                       && generated.find("data-precipitation-is-event-count=\"false\"")
                            != std::string::npos,
                     "cloud-atmosphere SVG lacks semantic separation metadata");
  atmosphere_require(generated.find(" nan") == std::string::npos
                       && generated.find(" -nan") == std::string::npos
                       && generated.find(" inf") == std::string::npos
                       && generated.find(" -inf") == std::string::npos,
                     "generated cloud-atmosphere SVG has non-finite data");
  if (dataset.fixture)
    atmosphere_require(generated.find("data-fixture=\"true\"")
                         != std::string::npos,
                       "fixture output is not visibly identified in metadata");
  generation::verify_configured_label_font(
    generated, "cloud-atmosphere SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-cloud-atmosphere PROJECTION PROFILE.json INPUT.geojson");
  // Deliberately sampled once: every calculated solar property and every
  // latest-not-after source check shares this process-start instant.
  const generation_time::instant process_start
    = generation_time::process_start_instant();
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const atmosphere_profile profile = load_atmosphere_profile(
    std::filesystem::absolute(argv[2]));
  const atmosphere_dataset dataset = load_atmosphere_dataset(
    std::filesystem::absolute(argv[3]), profile);
  validate_observation_times(profile, dataset, process_start);
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec, profile, dataset, process_start);
  verify(read_generated(basename), context, profile, dataset, process_start);
  return 0;
}

} // namespace cart0freak0::cloud_atmosphere_generation

#endif // CART0FREAK0_CLOUD_ATMOSPHERE_GENERATION_H
