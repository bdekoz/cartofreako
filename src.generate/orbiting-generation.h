// Projection-aware Orbital Technosphere SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ORBITING_GENERATION_H
#define CART0FREAK0_ORBITING_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "orbiting-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::orbiting_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

enum class product_kind
{
  global,
  observer,
};

inline std::string_view
product_argument(const product_kind product)
{ return product == product_kind::global ? "global" : "observer"; }

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
      while ((position = value.find(source, position)) != std::string::npos)
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
join(const std::vector<std::string>& values,
     const std::string_view delimiter = ",")
{
  std::string result;
  for (std::size_t index = 0; index < values.size(); ++index)
    {
      if (index != 0)
        result += delimiter;
      result += values[index];
    }
  return result;
}

inline generation::geographic_point
projection_point(const propagated_object& object, const profile& config,
                 const product_kind product)
{
  if (product == product_kind::global)
    return {object.subpoint.latitude_deg,
            object.subpoint.longitude_deg_east};
  return {object.equatorial.declination_deg,
          normalize_signed_degrees(config.central_right_ascension_deg
            - object.equatorial.right_ascension_deg)};
}

inline std::vector<svg::vrange>
project_reference_path(const generation::projection_context& context,
                       std::vector<generation::geographic_point> source)
{
  std::vector<std::vector<generation::geographic_point>> pieces;
  for (const generation::geographic_point point : source)
    {
      if (pieces.empty())
        pieces.emplace_back();
      if (!pieces.back().empty()
          && std::abs(point.longitude - pieces.back().back().longitude) > 180)
        pieces.emplace_back();
      pieces.back().push_back(point);
    }
  std::vector<svg::vrange> result;
  for (auto& piece : pieces)
    {
      if (piece.size() < 2)
        continue;
      for (svg::vrange& segment
           : generation::project_path(context, piece, false))
        if (segment.size() >= 2)
          result.push_back(std::move(segment));
    }
  return result;
}

inline void
add_path_segments(svg::group_element& group,
                  const std::vector<svg::vrange>& segments,
                  const svg::style& style, const std::string& id)
{
  for (std::size_t index = 0; index < segments.size(); ++index)
    group.add_element(svg::make_path(
      svg::make_path_data_from_points(segments[index]), style,
      id + "-segment-" + std::to_string(index + 1)));
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context,
               const product_kind product)
{
  svg::group_element layer;
  layer.start_element(product == product_kind::global
                        ? "terrestrial-background" : "observer-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({
    product == product_kind::global ? svg::color_qi {242, 244, 243}
                                    : svg::color_qi {5, 12, 31},
    1, svg::color::none, 0, 0,
  });
  rectangle.add_raw(product == product_kind::global
                      ? "id=\"technosphere-ocean\""
                      : "id=\"technosphere-night-sky\"");
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

inline equatorial_position
horizontal_to_equatorial(const double azimuth_deg, const double altitude_deg,
                         const profile& config)
{
  const double azimuth = degrees_to_radians(azimuth_deg);
  const double altitude = degrees_to_radians(altitude_deg);
  const double latitude = degrees_to_radians(config.observer.latitude_deg);
  const double declination = std::asin(
    std::sin(altitude) * std::sin(latitude)
      + std::cos(altitude) * std::cos(latitude) * std::cos(azimuth));
  const double hour_angle = std::atan2(
    -std::sin(azimuth) * std::cos(altitude),
    std::sin(altitude) * std::cos(latitude)
      - std::cos(altitude) * std::sin(latitude) * std::cos(azimuth));
  const double local_sidereal = SGP4Funcs::gstime_SGP4(
    config.calculation_time.julian_date)
    + degrees_to_radians(config.observer.longitude_deg_east);
  return {normalize_degrees(radians_to_degrees(
            local_sidereal - hour_angle)),
          radians_to_degrees(declination)};
}

inline void
add_reference_lines(generation::projection_document& document,
                    const generation::projection_context& context,
                    const profile& config, const product_kind product)
{
  svg::group_element layer;
  layer.start_element(product == product_kind::global
                        ? "terrestrial-reference" : "observer-reference");
  if (config.display.show_reference_lines)
    {
      const svg::style reference_style {
        svg::color::none, 0,
        product == product_kind::global ? svg::color_qi {75, 75, 75}
                                        : svg::color::white,
        product == product_kind::global ? 0.34 : 0.40,
        product == product_kind::global ? 0.014 : 0.028,
      };
      if (product == product_kind::global)
        {
          for (int latitude = -60; latitude <= 60; latitude += 30)
            {
              std::vector<generation::geographic_point> path;
              for (int longitude = -180; longitude <= 180; ++longitude)
                path.push_back({static_cast<double>(latitude),
                                static_cast<double>(longitude)});
              add_path_segments(layer, project_reference_path(context, path),
                                reference_style,
                                "latitude-" + std::to_string(latitude));
            }
          for (int longitude = -150; longitude <= 180; longitude += 30)
            {
              std::vector<generation::geographic_point> path;
              for (int latitude = -90; latitude <= 90; ++latitude)
                path.push_back({static_cast<double>(latitude),
                                static_cast<double>(longitude)});
              add_path_segments(layer, project_reference_path(context, path),
                                reference_style,
                                "longitude-" + std::to_string(longitude));
            }
        }
      else
        {
          std::vector<generation::geographic_point> equator;
          for (int longitude = -180; longitude <= 180; ++longitude)
            equator.push_back({0, static_cast<double>(longitude)});
          add_path_segments(layer, project_reference_path(context, equator),
                            reference_style, "celestial-equator");
          std::vector<generation::geographic_point> horizon;
          for (int azimuth = 0; azimuth <= 360; ++azimuth)
            {
              const equatorial_position point = horizontal_to_equatorial(
                azimuth, config.visibility.minimum_elevation_deg, config);
              horizon.push_back({point.declination_deg,
                normalize_signed_degrees(config.central_right_ascension_deg
                  - point.right_ascension_deg)});
            }
          const svg::style horizon_style {
            svg::color::none, 0, svg::color::asamaorange, 0.82, 0.032,
          };
          add_path_segments(layer, project_reference_path(context, horizon),
                            horizon_style, "observer-horizon");
        }
    }
  layer.finish_element();
  document.add_element(layer);
}

inline svg::style
marker_style(const propagated_object& object)
{
  svg::color_qi color = svg::color::gray75;
  if (object.role == "megaconstellation")
    color = svg::color::cyan;
  else if (object.role == "navigation")
    color = svg::color::gold;
  else if (object.role == "communications")
    color = svg::color::mediumpurple;
  else if (object.role == "earth-observation")
    color = svg::color::aquamarine;
  else if (object.role == "human-presence")
    color = svg::color::redorange;
  else if (object.role == "science")
    color = svg::color::lightblue;
  else if (object.role == "debris")
    color = svg::color::orange;
  return {color, object.sunlit ? 0.88 : 0.36,
          object.optical_candidate ? svg::color::white : svg::color::none,
          object.optical_candidate ? 0.9 : 0, 0.018};
}

inline double
marker_radius(const propagated_object& object)
{
  if (object.role == "human-presence")
    return 0.066;
  if (object.role == "navigation" || object.role == "earth-observation"
      || object.role == "science")
    return 0.038;
  if (object.role == "communications")
    return 0.032;
  if (object.role == "megaconstellation")
    return 0.024;
  if (object.role == "debris")
    return 0.014;
  return 0.019;
}

inline std::string
object_attributes(const propagated_object& object)
{
  std::string result;
  const auto attribute = [&](const std::string_view name,
                             const std::string& value) {
    result += " data-" + std::string(name) + "=\"" + xml_escape(value)
      + "\"";
  };
  attribute("norad-id", object.source.norad_id);
  attribute("name", object.source.name);
  attribute("cospar-id", object.source.international_designator);
  attribute("role", object.role);
  attribute("groups", join(object.source.group_ids));
  attribute("element-epoch", object.source.epoch.iso_utc);
  attribute("element-age-days", format_number(object.element_age_days, 4));
  attribute("subpoint-latitude-deg",
            format_number(object.subpoint.latitude_deg));
  attribute("subpoint-longitude-deg-east",
            format_number(object.subpoint.longitude_deg_east));
  attribute("altitude-km", format_number(object.subpoint.altitude_km, 3));
  attribute("observer-range-km",
            format_number(object.horizontal.range_km, 3));
  attribute("observer-azimuth-deg",
            format_number(object.horizontal.azimuth_deg));
  attribute("observer-elevation-deg",
            format_number(object.horizontal.elevation_deg));
  attribute("topocentric-ra-deg",
            format_number(object.equatorial.right_ascension_deg));
  attribute("topocentric-dec-deg",
            format_number(object.equatorial.declination_deg));
  attribute("sunlit", object.sunlit ? "true" : "false");
  attribute("optical-candidate",
            object.optical_candidate ? "true" : "false");
  attribute("source", object.source.source_url);
  return result;
}

inline void
add_marker(svg::group_element& layer,
           const generation::projection_context& context,
           const profile& config, const product_kind product,
           const propagated_object& object)
{
  const svg::point_2t point = generation::project_point(
    context, projection_point(object, config, product));
  svg::circle_element marker;
  marker.start_element();
  marker.add_data({std::get<0>(point), std::get<1>(point),
                   marker_radius(object)});
  marker.add_style(marker_style(object));
  marker.add_raw("id=\"norad-" + xml_escape(object.source.norad_id) + "\""
                 + object_attributes(object));
  marker.finish_element();
  layer.add_element(marker);
}

inline svg::typography
label_typography(const product_kind product)
{
  svg::typography typography = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  typography._M_size = 0.15;
  typography._M_style = product == product_kind::global
    ? svg::style {{40, 42, 46}, 0.92, svg::color::none, 0, 0}
    : svg::style {svg::color::gray05, 0.92, svg::color::white, 0.8, 0.02};
  typography._M_anchor = svg::typography::anchor::start;
  typography._M_align = svg::typography::align::left;
  typography._M_baseline = svg::typography::baseline::central;
  return typography;
}

inline void
add_label(svg::group_element& labels,
          const generation::projection_context& context,
          const profile& config, const product_kind product,
          const propagated_object& object)
{
  const svg::point_2t point = generation::project_point(
    context, projection_point(object, config, product));
  const svg::point_2t label_point {
    std::min(context.map_frame.width() - 0.05,
             std::get<0>(point) + marker_radius(object) + 0.035),
    std::get<1>(point),
  };
  svg::styled_text(labels, xml_escape(object.source.name), label_point,
                   label_typography(product));
}

inline bool
visible_in_product(const propagated_object& object,
                   const profile& config, const product_kind product)
{
  return product == product_kind::global
    || object.horizontal.elevation_deg
         >= config.visibility.minimum_elevation_deg;
}

inline void
add_tracks(generation::projection_document& document,
           const generation::projection_context& context,
           const profile& config, const catalog_bundle& catalogs,
           const product_kind product)
{
  svg::group_element tracks;
  tracks.start_element("representative-ground-tracks");
  if (product == product_kind::global
      && config.display.maximum_tracks_per_group != 0)
    {
      std::unordered_map<std::string, std::size_t> counts;
      const svg::style track_style {
        svg::color::none, 0, svg::color_qi {90, 90, 90}, 0.42, 0.012,
      };
      for (const orbital_object& object : catalogs.objects)
        for (const std::string& group : object.group_ids)
          {
            if (counts[group] >= config.display.maximum_tracks_per_group
                || !epoch_is_admissible(object, config))
              continue;
            std::vector<generation::geographic_point> path;
            try
              {
                for (int offset = -config.display.track_minutes_each_side;
                     offset <= config.display.track_minutes_each_side;
                     offset += config.display.track_step_minutes)
                  {
                    const double time = config.calculation_time.julian_date
                      + offset / minutes_per_day;
                    const teme_state state = propagate_teme(object, time);
                    const geodetic_position subpoint = ecef_to_geodetic(
                      teme_to_ecef(state.position_km, time));
                    path.push_back({subpoint.latitude_deg,
                                    subpoint.longitude_deg_east});
                  }
                add_path_segments(tracks,
                  project_reference_path(context, std::move(path)),
                  track_style, "track-" + group + "-norad-"
                    + object.norad_id);
                ++counts[group];
              }
            catch (const std::exception&)
              {
                // A failed optional track never removes the object's marker.
              }
          }
    }
  tracks.finish_element();
  document.add_element(tracks);
}

inline void
add_objects(generation::projection_document& document,
            const generation::projection_context& context,
            const profile& config, const product_kind product,
            const propagated_catalog& catalog)
{
  constexpr std::array roles {
    "debris", "other-active", "communications", "navigation",
    "earth-observation", "science", "megaconstellation", "human-presence",
  };
  svg::group_element labels;
  labels.start_element("labels");
  std::size_t label_count = 0;
  std::unordered_set<std::string> labelled_groups;
  for (const std::string_view role : roles)
    {
      svg::group_element layer;
      layer.start_element("objects-" + std::string(role));
      for (const propagated_object& object : catalog.objects)
        {
          if (object.role != role
              || !visible_in_product(object, config, product))
            continue;
          add_marker(layer, context, config, product, object);
          bool priority_label = false;
          for (const std::string& group : object.source.group_ids)
            if (!labelled_groups.contains(group))
              {
                priority_label = true;
                labelled_groups.insert(group);
                break;
              }
          if (priority_label && label_count < config.display.maximum_labels)
            {
              add_label(labels, context, config, product, object);
              ++label_count;
            }
        }
      layer.finish_element();
      document.add_element(layer);
    }
  labels.finish_element();
  document.add_element(labels);
}

inline void
add_observer_site(generation::projection_document& document,
                  const generation::projection_context& context,
                  const profile& config, const product_kind product)
{
  svg::group_element layer;
  layer.start_element("reference-site");
  if (product == product_kind::global)
    {
      const svg::point_2t point = generation::project_point(
        context, {config.observer.latitude_deg,
                  config.observer.longitude_deg_east});
      svg::circle_element marker;
      marker.start_element();
      marker.add_data({std::get<0>(point), std::get<1>(point), 0.075});
      marker.add_style({
        svg::color::redorange, 1, svg::color::white, 0.9, 0.018,
      });
      marker.add_raw("id=\"observer-site\" data-name=\""
                     + xml_escape(config.observer.name) + "\"");
      marker.finish_element();
      layer.add_element(marker);
    }
  layer.finish_element();
  document.add_element(layer);
}

inline std::size_t
visible_count(const propagated_catalog& catalog, const profile& config,
              const product_kind product)
{
  return static_cast<std::size_t>(std::count_if(
    catalog.objects.begin(), catalog.objects.end(),
    [&](const propagated_object& object) {
      return visible_in_product(object, config, product);
    }));
}

inline std::string
metadata_element(const profile& config, const product_kind product,
                 const catalog_bundle& loaded,
                 const propagated_catalog& propagated)
{
  return "<metadata id=\"orbital-technosphere-metadata\""
    " data-profile=\"" + xml_escape(config.path.filename().string()) + "\""
    " data-workflow=\"Orbital Technosphere\""
    " data-product=\"" + std::string(product_argument(product)) + "\""
    " data-timestamp=\"" + config.calculation_time.iso_utc + "\""
    " data-reference-point=\"" + xml_escape(config.observer.name) + "\""
    " data-reference-latitude-deg=\""
      + format_number(config.observer.latitude_deg) + "\""
    " data-reference-longitude-deg-east=\""
      + format_number(config.observer.longitude_deg_east) + "\""
    " data-reference-elevation-m=\""
      + format_number(config.observer.elevation_m, 1) + "\""
    " data-reference-capture-method=\""
      + xml_escape(config.observer.capture_method) + "\""
    " data-propagator=\"SGP4/WGS72/AFSPC\""
    " data-nasa-ssc-reference=\""
      + xml_escape(config.nasa_reference.filename().string()) + "\""
    " data-nasa-ssc-query=\"" + xml_escape(config.nasa_query_url) + "\""
    " data-input-checksums=\""
      + xml_escape(config.checksum_file.filename().string()) + "\""
    " data-primary-records=\"" + std::to_string(loaded.active_records) + "\""
    " data-debris-records=\"" + std::to_string(loaded.debris_records) + "\""
    " data-propagated-records=\""
      + std::to_string(propagated.objects.size()) + "\""
    " data-visible-records=\""
      + std::to_string(visible_count(propagated, config, product)) + "\""
    " data-skipped-stale=\"" + std::to_string(propagated.skipped_stale) + "\""
    " data-failed-propagation=\""
      + std::to_string(propagated.failed_propagation) + "\""
    " data-solar-altitude-deg=\""
      + format_number(solar_altitude_deg(
          config, config.calculation_time.julian_date)) + "\""
    "></metadata>\n";
}

inline std::string
output_basename(const product_kind product,
                const generation::projection_spec& spec)
{
  return generation::output_basename(
    product == product_kind::global ? "orbital-technosphere-global"
                                    : "orbital-technosphere-observer",
    spec);
}

inline void
generate(const generation::projection_spec& spec, const product_kind product,
         const profile& config)
{
  const std::string basename = output_basename(product, spec);
  const generation::projection_context context(spec, basename);
  const catalog_bundle loaded = load_catalogs(config);
  const propagated_catalog propagated = propagate_catalog(loaded, config);

  generation::projection_document document(
    basename,
    std::string(spec.title) + " " + std::string(product_argument(product))
      + " Orbital Technosphere at " + config.calculation_time.iso_utc,
    context.map_frame.frame_area);
  document.add_raw(metadata_element(config, product, loaded, propagated));
  add_background(document, context, product);
  if (product == product_kind::global)
    {
      natural_earth::initialize_gdal();
      add_subdued_land(document, context);
    }
  add_reference_lines(document, context, config, product);
  add_tracks(document, context, config, loaded, product);
  add_objects(document, context, config, product, propagated);
  add_observer_site(document, context, config, product);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  orbiting_require(input.good(), "failed to open generated " + basename
                                  + ".svg");
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
       const product_kind product, const profile& config)
{
  orbiting_require(generated.find(generation::view_box_fragment(context))
                      != std::string::npos,
                   "generated Orbital Technosphere SVG has the wrong viewBox");
  constexpr std::array object_layers {
    "objects-debris", "objects-other-active", "objects-communications",
    "objects-navigation", "objects-earth-observation", "objects-science",
    "objects-megaconstellation", "objects-human-presence",
  };
  for (const std::string_view layer : object_layers)
    orbiting_require(generated.find("<g id=\"" + std::string(layer) + "\"")
                        != std::string::npos,
                     "generated Orbital Technosphere SVG is missing layer "
                       + std::string(layer));
  constexpr std::array common_layers {
    "representative-ground-tracks", "labels", "reference-site",
  };
  for (const std::string_view layer : common_layers)
    orbiting_require(generated.find("<g id=\"" + std::string(layer) + "\"")
                        != std::string::npos,
                     "generated Orbital Technosphere SVG is missing layer "
                       + std::string(layer));
  orbiting_require(generated.find("id=\"orbital-technosphere-metadata\"")
                      != std::string::npos
                     && generated.find("data-timestamp=\""
                         + config.calculation_time.iso_utc + "\"")
                          != std::string::npos
                     && generated.find("data-nasa-ssc-reference=\""
                         + config.nasa_reference.filename().string() + "\"")
                          != std::string::npos,
                   "generated Orbital Technosphere SVG is missing metadata");
  orbiting_require(token_count(generated, "data-norad-id=") > 100,
                   "generated Orbital Technosphere SVG has too few objects");
  if (product == product_kind::global)
    orbiting_require(generated.find("<g id=\"terrestrial-land\">")
                        != std::string::npos
                       && generated.find("id=\"observer-site\"")
                            != std::string::npos,
                     "global Orbital Technosphere SVG lacks terrestrial base");
  else
    orbiting_require(generated.find("observer-horizon-segment-")
                        != std::string::npos
                       && generated.find("<g id=\"observer-background\">")
                            != std::string::npos,
                     "observer Orbital Technosphere SVG lacks horizon");
  orbiting_require(generated.find(" nan") == std::string::npos
                     && generated.find(" -nan") == std::string::npos
                     && generated.find(" inf") == std::string::npos
                     && generated.find(" -inf") == std::string::npos,
                   "generated Orbital Technosphere SVG has non-finite data");
  generation::verify_configured_label_font(
    generated, "Orbital Technosphere SVG");
}

inline product_kind
parse_product(const std::string_view argument)
{
  if (argument == "global")
    return product_kind::global;
  if (argument == "observer")
    return product_kind::observer;
  throw std::invalid_argument(
    "unknown Orbital Technosphere product '" + std::string(argument)
      + "' (use global or observer)");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-orbiting PROJECTION PRODUCT PROFILE.json");
  const generation::projection_spec& spec = generation::find_projection_spec(
    argv[1]);
  const product_kind product = parse_product(argv[2]);
  const profile config = load_profile(std::filesystem::absolute(argv[3]));
  const std::string basename = output_basename(product, spec);
  const generation::projection_context context(spec, basename);
  generate(spec, product, config);
  verify(read_generated(basename), context, product, config);
  return 0;
}

} // namespace cart0freak0::orbiting_generation

#endif
