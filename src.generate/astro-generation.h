// Projection-aware SVG generation for celestial catalogs.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ASTRO_GENERATION_H
#define CART0FREAK0_ASTRO_GENERATION_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "astro-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::astro_generation {

namespace generation = cart0freak0::generation;

enum class product_kind
{
  all_sky,
  observer,
};

inline std::string_view
product_argument(const product_kind product)
{
  return product == product_kind::all_sky ? "all-sky" : "observer";
}

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
format_number(const double value, const int precision = 6)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline std::string
join(const std::vector<std::string>& values, const std::string_view delimiter)
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
projection_point(const sky_object& object, const profile& config)
{
  return {object.dec_deg,
          celestial_longitude(config.sky_orientation, object.ra_deg)};
}

inline generation::geographic_point
projection_point(const right_ascension_declination position,
                 const profile& config)
{
  return {position.dec_deg,
          celestial_longitude(config.sky_orientation, position.ra_deg)};
}

inline std::vector<svg::vrange>
project_celestial_path(const generation::projection_context& context,
                       const profile& config,
                       const std::vector<right_ascension_declination>& source)
{
  std::vector<std::vector<generation::geographic_point>> pieces;
  for (const right_ascension_declination position : source)
    {
      const generation::geographic_point point = projection_point(
        position, config);
      if (pieces.empty())
        pieces.emplace_back();
      if (!pieces.back().empty()
          && std::abs(point.longitude - pieces.back().back().longitude) > 180)
        pieces.emplace_back();
      pieces.back().push_back(point);
    }

  std::vector<svg::vrange> result;
  for (std::vector<generation::geographic_point>& piece : pieces)
    {
      if (piece.size() < 2)
        continue;
      std::vector<svg::vrange> projected = generation::project_path(
        context, std::move(piece), false);
      for (svg::vrange& segment : projected)
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

inline right_ascension_declination
equatorial_vector_to_coordinates(const vector_3d value)
{
  const double distance = length(value);
  astro_require(distance > 0, "celestial reference vector has zero length");
  return {
    normalize_degrees(radians_to_degrees(std::atan2(value.y, value.x))),
    radians_to_degrees(std::asin(std::clamp(value.z / distance, -1.0, 1.0))),
  };
}

inline std::vector<right_ascension_declination>
celestial_equator()
{
  std::vector<right_ascension_declination> result;
  for (int ra = 0; ra <= 360; ++ra)
    result.push_back({static_cast<double>(ra), 0});
  return result;
}

inline std::vector<right_ascension_declination>
ecliptic_line()
{
  std::vector<right_ascension_declination> result;
  for (int longitude = 0; longitude <= 360; ++longitude)
    {
      const double angle = degrees_to_radians(longitude);
      result.push_back(ecliptic_vector_to_equatorial(
        {std::cos(angle), std::sin(angle), 0}));
    }
  return result;
}

inline std::vector<right_ascension_declination>
galactic_equator()
{
  std::vector<right_ascension_declination> result;
  for (int longitude = 0; longitude <= 360; ++longitude)
    {
      const double angle = degrees_to_radians(longitude);
      const double x = std::cos(angle);
      const double y = std::sin(angle);
      result.push_back(equatorial_vector_to_coordinates({
        -0.0548755604 * x + 0.4941094279 * y,
        -0.8734370902 * x - 0.4448296300 * y,
        -0.4838350155 * x + 0.7469822445 * y,
      }));
    }
  return result;
}

inline std::vector<right_ascension_declination>
observer_horizon(const profile& config)
{
  const double sidereal = local_sidereal_time(config);
  std::vector<right_ascension_declination> result;
  for (int azimuth = 0; azimuth <= 360; ++azimuth)
    result.push_back(horizontal_to_equatorial(
      azimuth, config.instrument.minimum_altitude_deg,
      config.observer.latitude_deg, sidereal));
  return result;
}

inline void
add_reference_lines(generation::projection_document& document,
                    const generation::projection_context& context,
                    const profile& config, const product_kind product)
{
  svg::group_element reference;
  reference.start_element("celestial-reference");
  if (config.display.show_reference_lines)
    {
      const svg::style equator_style {
        svg::color::none, 0, svg::color::gray50, 0.45, 0.018,
      };
      const svg::style ecliptic_style {
        svg::color::none, 0, svg::color::gold, 0.65, 0.025,
      };
      const svg::style galactic_style {
        svg::color::none, 0, svg::color::mediumpurple, 0.55, 0.025,
      };
      const auto add_reference = [&](const std::string& id,
                                     const auto& source,
                                     const svg::style& style) {
        try
          {
            add_path_segments(reference,
              project_celestial_path(context, config, source), style, id);
          }
        catch (const std::exception& error)
          {
            throw std::runtime_error("failed to project " + id + ": "
                                     + error.what());
          }
      };
      add_reference("celestial-equator", celestial_equator(), equator_style);
      add_reference("ecliptic", ecliptic_line(), ecliptic_style);
      add_reference("galactic-equator", galactic_equator(), galactic_style);
    }
  if (product == product_kind::observer
      && config.display.show_below_horizon_reference)
    {
      const svg::style horizon_style {
        svg::color::none, 0, svg::color::asamaorange, 0.8, 0.035,
      };
      try
        {
          add_path_segments(reference,
            project_celestial_path(context, config, observer_horizon(config)),
            horizon_style, "observer-horizon");
        }
      catch (const std::exception& error)
        {
          throw std::runtime_error("failed to project observer horizon: "
                                   + std::string(error.what()));
        }
    }
  reference.finish_element();
  document.add_element(reference);
}

inline svg::style
star_style(const sky_object& object)
{
  svg::color color = svg::color::white;
  if (object.color_index.has_value())
    {
      if (*object.color_index < 0.15)
        color = svg::color::lightblue;
      else if (*object.color_index < 0.8)
        color = svg::color::white;
      else if (*object.color_index < 1.6)
        color = svg::color::lemonchiffon;
      else
        color = svg::color::orange;
    }
  return {color, 0.92, svg::color::none, 0, 0};
}

inline svg::style
object_style(const sky_object& object)
{
  if (object.kind == "star")
    return star_style(object);
  if (object.kind == "exoplanet-host")
    return {svg::color::none, 0, svg::color::aquamarine, 0.85, 0.022};
  if (object.kind == "sun")
    return {svg::color::gold, 1, svg::color::lemonchiffon, 1, 0.025};
  if (object.kind == "moon")
    return {svg::color::gray05, 1, svg::color::white, 1, 0.018};
  if (object.kind == "planet")
    return {svg::color::asamaorange, 0.95, svg::color::white, 0.75, 0.012};
  if (object.kind == "asteroid")
    return {svg::color::goldenrod, 0.9, svg::color::none, 0, 0};
  if (object.kind == "comet")
    return {svg::color::lightcyan, 0.9, svg::color::cyan, 0.9, 0.02};
  if (object.kind == "gamma-ray-burst"
      || object.kind == "magnetar-burst-candidate"
      || object.kind == "x-ray-transient")
    return {svg::color::none, 0, svg::color::redorange, 1, 0.045};
  if (object.kind == "black-hole")
    return {svg::color::black, 1, svg::color::magenta, 1, 0.035};
  return {svg::color::mediumpurple, 0.88,
          svg::color::lightcyan, 0.7, 0.012};
}

inline double
marker_radius(const sky_object& object)
{
  if (object.kind == "star")
    {
      const double magnitude = object.magnitude.value_or(5.5);
      return std::clamp(0.035 * std::pow(10.0, -0.08 * (magnitude - 3.0)),
                        0.013, 0.095);
    }
  if (object.kind == "sun")
    return 0.14;
  if (object.kind == "moon")
    return 0.11;
  if (object.kind == "planet")
    return 0.075;
  if (object.kind == "asteroid" || object.kind == "comet")
    return 0.052;
  if (object.kind == "exoplanet-host")
    return 0.043;
  if (object.observed_at.has_value())
    return 0.085;
  return 0.065;
}

inline std::string
object_attributes(const sky_object& object, const profile& config)
{
  std::string result;
  const auto attribute = [&](const std::string_view name,
                             const std::string& value) {
    result += " data-" + std::string(name) + "=\"" + xml_escape(value)
      + "\"";
  };
  attribute("name", object.name);
  attribute("kind", object.kind);
  attribute("bands", join(object.bands, ","));
  attribute("ra-deg", format_number(object.ra_deg));
  attribute("dec-deg", format_number(object.dec_deg));
  attribute("observer-altitude-deg", format_number(object.altitude_deg));
  attribute("source", object.source_url);
  if (!object.detail.empty())
    attribute("detail", object.detail);
  if (object.magnitude.has_value())
    attribute("magnitude", format_number(*object.magnitude, 3));
  if (object.uncertainty_deg.has_value())
    attribute("uncertainty-deg",
              format_number(*object.uncertainty_deg, 6));
  if (object.observed_at.has_value())
    {
      attribute("observed-at", object.observed_at->iso_utc);
      const double age_days = std::chrono::duration<double>(
        config.calculation_time.value - object.observed_at->value).count()
        / seconds_per_day;
      attribute("age-days", format_number(age_days, 3));
    }
  return result;
}

inline void
add_marker(svg::group_element& layer,
           const generation::projection_context& context,
           const profile& config, const sky_object& object)
{
  svg::point_2t point;
  try
    {
      point = generation::project_point(
        context, projection_point(object, config));
    }
  catch (const std::exception& error)
    {
      throw std::runtime_error("failed to project " + object.id + ": "
                               + error.what());
    }
  svg::circle_element marker;
  marker.start_element();
  marker.add_data({std::get<0>(point), std::get<1>(point),
                   marker_radius(object)});
  marker.add_style(object_style(object));
  marker.add_raw("id=\"" + xml_escape(object.id) + "\""
                 + object_attributes(object, config));
  marker.finish_element();
  layer.add_element(marker);
}

inline std::vector<right_ascension_declination>
uncertainty_circle(const sky_object& object)
{
  astro_require(object.uncertainty_deg.has_value(),
                "uncertainty circle requires an angular uncertainty");
  const double radius = degrees_to_radians(std::clamp(
    *object.uncertainty_deg, 0.08, 89.0));
  const double center_ra = degrees_to_radians(object.ra_deg);
  const double center_dec = degrees_to_radians(object.dec_deg);
  std::vector<right_ascension_declination> result;
  for (int bearing_deg = 0; bearing_deg <= 360; bearing_deg += 5)
    {
      const double bearing = degrees_to_radians(bearing_deg);
      const double dec = std::asin(
        std::sin(center_dec) * std::cos(radius)
          + std::cos(center_dec) * std::sin(radius) * std::cos(bearing));
      const double delta_ra = std::atan2(
        std::sin(bearing) * std::sin(radius) * std::cos(center_dec),
        std::cos(radius) - std::sin(center_dec) * std::sin(dec));
      result.push_back({normalize_degrees(radians_to_degrees(
                          center_ra + delta_ra)),
                        radians_to_degrees(dec)});
    }
  return result;
}

inline void
add_uncertainty(svg::group_element& layer,
                const generation::projection_context& context,
                const profile& config, const sky_object& object)
{
  if (!object.uncertainty_deg.has_value())
    return;
  const svg::style style {
    svg::color::none, 0, svg::color::redorange, 0.6, 0.022,
  };
  try
    {
      add_path_segments(layer,
        project_celestial_path(context, config, uncertainty_circle(object)),
        style, object.id + "-uncertainty");
    }
  catch (const std::exception& error)
    {
      // A few coordinates fall on numerical holes in the legacy
      // Cahill-Keyes parallel construction. Preserve the event and its error
      // metadata with a clearly marked planar fallback instead of dropping
      // the transient or aborting the complete atlas.
      const svg::point_2t center = generation::project_point(
        context, projection_point(object, config));
      const double planar_radius = std::clamp(
        *object.uncertainty_deg / 180.0
          * std::max(context.map_frame.width(), context.map_frame.height()),
        0.08, std::max(context.map_frame.width(), context.map_frame.height())
                / 3.0);
      svg::circle_element fallback;
      fallback.start_element();
      fallback.add_data({std::get<0>(center), std::get<1>(center),
                         planar_radius});
      fallback.add_style(style);
      fallback.add_raw("id=\"" + xml_escape(object.id)
                       + "-uncertainty-planar-fallback\""
                       + " data-projection-fallback=\""
                       + xml_escape(error.what()) + "\"");
      fallback.finish_element();
      layer.add_element(fallback);
    }
}

inline svg::typography
label_typography()
{
  svg::typography result = svg::k::smono_typo;
  result._M_size = 0.17;
  result._M_style = {
    svg::color::gray05, 0.95, svg::color::midnightblue, 0.75, 0.01,
  };
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline void
add_label(svg::group_element& labels,
          const generation::projection_context& context,
          const profile& config, const sky_object& object)
{
  svg::point_2t point;
  try
    {
      point = generation::project_point(
        context, projection_point(object, config));
    }
  catch (const std::exception& error)
    {
      throw std::runtime_error("failed to project label " + object.id + ": "
                               + error.what());
    }
  const svg::point_2t label_point {
    std::min(context.map_frame.width() - 0.05,
             std::get<0>(point) + marker_radius(object) + 0.04),
    std::get<1>(point),
  };
  svg::styled_text(labels, xml_escape(object.name), label_point,
                   label_typography());
}

inline bool
should_label(const sky_object&, const std::string_view layer,
             const std::size_t layer_index)
{
  if (layer == "solar-system" || layer == "deep-sky"
      || layer == "transients")
    return true;
  return layer == "exoplanet-hosts" && layer_index < 8;
}

inline std::size_t
add_object_layer(generation::projection_document& document,
                 svg::group_element& labels,
                 const generation::projection_context& context,
                 const profile& config, const product_kind product,
                 const std::string_view layer_name,
                 const std::vector<sky_object>& objects,
                 const double sun_altitude, std::size_t label_count)
{
  svg::group_element layer;
  layer.start_element(std::string(layer_name));
  std::size_t layer_index = 0;
  for (const sky_object& object : objects)
    {
      if (product == product_kind::observer
          && !object_visible_to_observer(object, config, sun_altitude))
        continue;
      if (layer_name == "transients")
        add_uncertainty(layer, context, config, object);
      add_marker(layer, context, config, object);
      if (label_count < config.display.maximum_labels
          && should_label(object, layer_name, layer_index))
        {
          add_label(labels, context, config, object);
          ++label_count;
        }
      ++layer_index;
    }
  layer.finish_element();
  document.add_element(layer);
  return label_count;
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("astronomy-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({
    svg::color::midnightblue, 1, svg::color::none, 0, 0,
  });
  rectangle.add_raw("id=\"night-sky-background\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const profile& config, const product_kind product,
                 const double sun_altitude)
{
  return "<metadata id=\"astro-metadata\""
    " data-profile=\"" + xml_escape(config.path.filename().string()) + "\""
    " data-product=\"" + std::string(product_argument(product)) + "\""
    " data-timestamp=\"" + config.calculation_time.iso_utc + "\""
    " data-reference-point=\"" + xml_escape(config.observer.name) + "\""
    " data-reference-latitude-deg=\""
      + format_number(config.observer.latitude_deg) + "\""
    " data-reference-longitude-deg-east=\""
      + format_number(config.observer.longitude_deg_east) + "\""
    " data-reference-elevation-m=\""
      + format_number(config.observer.elevation_m, 1) + "\""
    " data-handedness=\""
      + std::string(config.sky_orientation.celestial_handedness
                      ? "celestial" : "terrestrial") + "\""
    " data-central-ra-hours=\""
      + format_number(config.sky_orientation.central_right_ascension_deg
                        / degrees_per_hour, 3) + "\""
    " data-instrumentation=\"" + xml_escape(config.instrument.mode) + "\""
    " data-bands=\"" + xml_escape(join(config.instrument.bands, ",")) + "\""
    " data-transient-lookback-days=\""
      + format_number(config.event_lookback_days, 3) + "\""
    " data-sun-altitude-deg=\"" + format_number(sun_altitude) + "\""
    "></metadata>\n";
}

inline double
sun_altitude(const catalogs& data)
{
  const auto found = std::find_if(
    data.solar_system.begin(), data.solar_system.end(),
    [](const sky_object& object) { return object.id == "sun"; });
  astro_require(found != data.solar_system.end(),
                "Solar System catalog is missing the Sun");
  return found->altitude_deg;
}

inline std::string
output_basename(const product_kind product,
                const generation::projection_spec& spec)
{
  return generation::output_basename(
    product == product_kind::all_sky ? "astro-all-sky" : "astro-observer",
    spec);
}

inline void
generate(const generation::projection_spec& spec, const product_kind product,
         const profile& config)
{
  const std::string basename = output_basename(product, spec);
  const generation::projection_context context(spec, basename);
  catalogs data = load_catalogs(config);
  calculate_altitudes(data, config);
  const double solar_altitude = sun_altitude(data);

  generation::projection_document document(
    basename,
    std::string(spec.title) + " " + std::string(product_argument(product))
      + " multi-band celestial atlas at " + config.calculation_time.iso_utc,
    context.map_frame.frame_area);
  document.add_raw(metadata_element(config, product, solar_altitude));
  add_background(document, context);
  add_reference_lines(document, context, config, product);

  svg::group_element labels;
  labels.start_element("labels");
  std::size_t label_count = 0;
  label_count = add_object_layer(
    document, labels, context, config, product, "stars", data.stars,
    solar_altitude, label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, "exoplanet-hosts",
    data.exoplanet_hosts, solar_altitude, label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, "deep-sky", data.deep_sky,
    solar_altitude, label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, "solar-system",
    data.solar_system, solar_altitude, label_count);
  static_cast<void>(add_object_layer(
    document, labels, context, config, product, "transients",
    data.transients, solar_altitude, label_count));
  labels.finish_element();
  document.add_element(labels);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  astro_require(input.good(), "failed to open generated " + basename + ".svg");
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
  astro_require(generated.find(generation::view_box_fragment(context))
                  != std::string::npos,
                "generated astronomy SVG has the wrong viewBox");
  constexpr std::array layers {
    "astronomy-background", "celestial-reference", "stars",
    "exoplanet-hosts", "deep-sky", "solar-system", "transients", "labels",
  };
  for (const std::string_view layer : layers)
    astro_require(generated.find("<g id=\"" + std::string(layer) + "\">")
                    != std::string::npos,
                  "generated astronomy SVG is missing layer "
                    + std::string(layer));
  astro_require(generated.find("id=\"astro-metadata\"") != std::string::npos
                  && generated.find("data-timestamp=\""
                                      + config.calculation_time.iso_utc + "\"")
                       != std::string::npos,
                "generated astronomy SVG is missing profile metadata");
  astro_require(token_count(generated, "data-kind=\"star\"")
                    <= config.display.maximum_stars,
                "generated astronomy SVG exceeds the star budget");
  if (product == product_kind::all_sky)
    {
      astro_require(token_count(generated, "data-kind=\"star\"") >= 100,
                    "all-sky astronomy SVG contains too few Gaia stars");
      astro_require(token_count(generated, "data-kind=\"planet\"") >= 7,
                    "all-sky astronomy SVG omits major planets");
      astro_require(token_count(generated, "data-kind=\"asteroid\"") >= 1
                      && token_count(generated, "data-kind=\"comet\"") >= 1,
                    "all-sky astronomy SVG omits small-body classes");
      astro_require(generated.find("observer-horizon-segment-")
                      == std::string::npos,
                    "all-sky astronomy SVG unexpectedly has an observer "
                    "horizon");
    }
  else
    {
      astro_require(generated.find("observer-horizon-segment-")
                      != std::string::npos,
                    "observer astronomy SVG is missing its horizon");
      astro_require(generated.find("<g id=\"solar-system\">")
                      != std::string::npos,
                    "observer astronomy SVG is missing its Solar System "
                    "layer");
    }
  astro_require(generated.find(" nan") == std::string::npos
                  && generated.find(" -nan") == std::string::npos
                  && generated.find(" inf") == std::string::npos
                  && generated.find(" -inf") == std::string::npos,
                "generated astronomy SVG contains a non-finite coordinate");
}

inline product_kind
parse_product(const std::string_view argument)
{
  if (argument == "all-sky")
    return product_kind::all_sky;
  if (argument == "observer")
    return product_kind::observer;
  throw std::invalid_argument(
    "unknown astronomy product '" + std::string(argument)
      + "' (use all-sky or observer)");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-astro PROJECTION PRODUCT PROFILE.json");
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

} // namespace cart0freak0::astro_generation

#endif
