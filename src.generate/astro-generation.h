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
#include <izzi-svg.h>

#include "astro-observer.h"
#include "generation-typography.h"
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
angular_circle(const right_ascension_declination center,
               const double radius_deg)
{
  const double radius = degrees_to_radians(radius_deg);
  const double center_ra = degrees_to_radians(center.ra_deg);
  const double center_dec = degrees_to_radians(center.dec_deg);
  std::vector<right_ascension_declination> result;
  for (int bearing_deg = 0; bearing_deg <= 360; bearing_deg += 2)
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

inline std::vector<right_ascension_declination>
observer_horizon(const profile& config)
{
  astro_require(config.observer.terrestrial.has_value()
                  && config.instrument.minimum_altitude_deg.has_value(),
                "ground horizon requires terrestrial observer limits");
  const double sidereal = local_sidereal_time(config);
  std::vector<right_ascension_declination> result;
  for (int azimuth = 0; azimuth <= 360; ++azimuth)
    result.push_back(horizontal_to_equatorial(
      azimuth, *config.instrument.minimum_altitude_deg,
      config.observer.terrestrial->latitude_deg, sidereal));
  return result;
}

inline void
add_reference_lines(generation::projection_document& document,
                    const generation::projection_context& context,
                    const profile& config, const product_kind product,
                    const observer_state& state)
{
  svg::group_element reference;
  reference.start_element("celestial-reference");
  if (config.display.show_reference_lines)
    {
      const svg::style equator_style {
        svg::color::none, 0, svg::color::white, 0.45, 0.023,
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
      try
        {
          if (config.observer.kind == observer_kind::terrestrial)
            {
              const svg::style horizon_style {
                svg::color::none, 0, svg::color::asamaorange, 0.8, 0.035,
              };
              add_path_segments(reference,
                project_celestial_path(
                  context, config, observer_horizon(config)),
                horizon_style, "ground-observer-horizon");
            }
          else
            {
              astro_require(state.orbiting.has_value()
                              && config.observer.orbiting.has_value(),
                            "HST reference state is missing");
              const orbiting_observer_state& orbit = *state.orbiting;
              const orbiting_observer& observer = *config.observer.orbiting;
              const svg::style earth_style {
                svg::color::none, 0, svg::color::asamaorange, 0.9, 0.04,
              };
              const svg::style earth_avoidance_style {
                svg::color::none, 0, svg::color::orange, 0.65, 0.025,
              };
              const svg::style sun_avoidance_style {
                svg::color::none, 0, svg::color::gold, 0.75, 0.03,
              };
              add_path_segments(reference,
                project_celestial_path(context, config,
                  angular_circle(orbit.earth_center,
                                 orbit.earth_angular_radius_deg)),
                earth_style, "hubble-earth-limb");
              add_path_segments(reference,
                project_celestial_path(context, config,
                  angular_circle(orbit.earth_center,
                    orbit.earth_angular_radius_deg
                      + observer.earth_limb_avoidance_deg)),
                earth_avoidance_style, "hubble-earth-avoidance");
              const solar_geometry::equatorial_position sun
                = solar_geometry::sun_equatorial_position(
                  config.calculation_time.julian_date);
              add_path_segments(reference,
                project_celestial_path(context, config,
                  angular_circle({sun.right_ascension_deg, sun.declination_deg},
                                 observer.sun_avoidance_deg)),
                sun_avoidance_style, "hubble-sun-avoidance");
            }
        }
      catch (const std::exception& error)
        {
          throw std::runtime_error("failed to project observer limits: "
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
    return {svg::color::black, 1, svg::color::white, 1, 0.07};
  return {svg::color::mediumpurple, 0.88,
          svg::color::lightcyan, 0.7, 0.012};
}

inline double
marker_radius(const sky_object& object)
{
  constexpr double planet_base_display_radius = 0.075;
  constexpr double planet_display_scale = 2.0;
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
    return planet_base_display_radius * planet_display_scale;
  if (object.kind == "asteroid" || object.kind == "comet")
    return 0.052;
  if (object.kind == "exoplanet-host")
    return 0.043;
  if (object.observed_at.has_value())
    return 0.085;
  return 0.065;
}

inline std::string
object_attributes(const sky_object& object, const profile& config,
                  const observer_state& state)
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
  if (state.kind == observer_kind::terrestrial)
    attribute("observer-altitude-deg",
              format_number(object.observer_angle_deg));
  else
    {
      attribute("earth-limb-clearance-deg",
                format_number(object.observer_angle_deg));
      attribute("sun-separation-deg",
                format_number(object.sun_separation_deg));
    }
  attribute("source", object.source_url);
  if (!object.detail.empty())
    attribute("detail", object.detail);
  if (object.magnitude.has_value())
    attribute("magnitude", format_number(*object.magnitude, 3));
  if (object.apparent_angular_radius_deg.has_value())
    {
      attribute("apparent-angular-radius-deg",
                format_number(*object.apparent_angular_radius_deg, 9));
      attribute("apparent-angular-diameter-arcsec",
                format_number(*object.apparent_angular_radius_deg * 7200, 3));
      attribute("display-radius-inches",
                format_number(marker_radius(object), 3));
      attribute("display-radius-scale", "2");
    }
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
make_stationary_rays(svg::group_element& layer, const svg::point_2t origin,
                     const sky_object& object)
{
  // Deterministic ten-ray ornament for fixed catalog points. Equivalent to
  // Izzi make_line_rays(n=10) but with fixed angles so regenerated plates
  // remain checksum-stable.
  constexpr std::size_t nrays = 10;
  constexpr double tau = 6.2831853071795864769;
  const double radius = 3.0 * marker_radius(object);
  const svg::style style {svg::color::none, 0, svg::color::white, 0.6, 0.02};
  svg::group_element rays;
  rays.start_element("stationary-rays-" + xml_escape(object.id));
  for (std::size_t index = 0; index < nrays; ++index)
    {
      const double angle = tau * static_cast<double>(index) / nrays;
      const double end_x = std::get<0>(origin) + radius * std::cos(angle);
      const double end_y = std::get<1>(origin) + radius * std::sin(angle);
      rays.add_element(svg::make_line(origin, {end_x, end_y}, style));
    }
  rays.finish_element();
  layer.add_element(rays);
}

inline void
add_marker(svg::group_element& layer,
           const generation::projection_context& context,
           const profile& config, const observer_state& state,
           const sky_object& object, const std::string_view layer_name)
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
  // Objects at the projection seam (3C 273 on the AuthaGraph left edge)
  // must stay fully inside the frame.
  point = {
    std::max(std::get<0>(point), marker_radius(object)),
    std::get<1>(point),
  };
  svg::circle_element marker;
  marker.start_element();
  marker.add_data({std::get<0>(point), std::get<1>(point),
                   marker_radius(object)});
  marker.add_style(object_style(object));
  marker.add_raw("id=\"" + xml_escape(object.id) + "\""
                 + object_attributes(object, config, state));
  marker.finish_element();
  layer.add_element(marker);

  if (object.kind == "planet")
    {
      astro_require(object.apparent_angular_radius_deg.has_value()
                      && *object.apparent_angular_radius_deg > 0,
                    "planet is missing its apparent angular radius");
      const svg::style true_size_style {
        svg::color::none, 0, svg::color::white, 1, 0.002,
      };
      const auto segments = project_celestial_path(
        context, config,
        angular_circle({object.ra_deg, object.dec_deg},
                       *object.apparent_angular_radius_deg));
      astro_require(!segments.empty(),
                    "planet true-angular-size outline did not project");
      for (std::size_t index = 0; index < segments.size(); ++index)
        layer.add_element(svg::make_path(
          svg::make_path_data_from_points(segments[index]), true_size_style,
          xml_escape(object.id) + "-true-angular-size-segment-"
            + std::to_string(index + 1),
          true,
          "data-planet-true-angular-size=\"true\""
          " data-apparent-angular-radius-deg=\""
            + format_number(*object.apparent_angular_radius_deg, 9)
            + "\" stroke-dasharray=\"0.001 0.001\""
              " stroke-linecap=\"round\""));
    }
  if (layer_name == "deep-sky" || layer_name == "transients"
      || (layer_name == "solar-system"
          && (object.kind == "asteroid" || object.kind == "comet")))
    make_stationary_rays(layer, point, object);
}

inline std::vector<right_ascension_declination>
uncertainty_circle(const sky_object& object)
{
  astro_require(object.uncertainty_deg.has_value(),
                "uncertainty circle requires an angular uncertainty");
  return angular_circle(
    {object.ra_deg, object.dec_deg},
    std::clamp(*object.uncertainty_deg, 0.08, 89.0));
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
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = 0.17;
  result._M_style = {
    svg::color::gray05, 0.95, svg::color::white, 0.0, 0.05,
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
  constexpr double left_inset = 0.15;
  const svg::point_2t label_point {
    std::min(context.map_frame.width() - 0.05,
             std::max(left_inset,
                      std::get<0>(point) + marker_radius(object) + 0.04)),
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
                 const observer_state& state,
                 const std::string_view layer_name,
                 const std::vector<sky_object>& objects,
                 std::size_t label_count)
{
  svg::group_element layer;
  layer.start_element(std::string(layer_name));
  std::size_t layer_index = 0;
  for (const sky_object& object : objects)
    {
      if (product == product_kind::observer
          && !object_visible_to_platform(object, config, state))
        continue;
      if (layer_name == "transients")
        add_uncertainty(layer, context, config, object);
      add_marker(layer, context, config, state, object, layer_name);
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
               const generation::projection_context& context,
               const profile& config, const product_kind product)
{
  svg::color_qi background = {0, 1, 108};
  if (product == product_kind::observer)
    background = config.observer.kind == observer_kind::terrestrial
      ? svg::color_qi {0, 1, 139}
      : svg::color_qi {116, 0, 89};
  svg::group_element layer;
  layer.start_element("astronomy-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({background, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"night-sky-background\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const profile& config, const product_kind product,
                 const observer_state& state)
{
  std::string result = "<metadata id=\"astro-metadata\""
    " data-profile=\"" + xml_escape(config.path.filename().string()) + "\""
    " data-product=\"" + std::string(product_argument(product)) + "\""
    " data-timestamp=\"" + config.calculation_time.iso_utc + "\""
    " data-observer-id=\"" + xml_escape(config.observer.id) + "\""
    " data-observer-name=\"" + xml_escape(config.observer.name) + "\""
    " data-observer-kind=\""
      + std::string(config.observer.kind == observer_kind::terrestrial
                      ? "terrestrial" : "orbiting") + "\""
    " data-handedness=\""
      + std::string(config.sky_orientation.celestial_handedness
                      ? "celestial" : "terrestrial") + "\""
    " data-central-ra-hours=\""
      + format_number(config.sky_orientation.central_right_ascension_deg
                        / degrees_per_hour, 3) + "\""
    " data-instrument-id=\"" + xml_escape(config.instrument.id) + "\""
    " data-instrument-name=\"" + xml_escape(config.instrument.name) + "\""
    " data-planet-display-radius-inches=\"0.15\""
    " data-planet-display-scale=\"2\""
    " data-planet-size-encoding=\"fixed-glyph-plus-true-angular-outline\""
    " data-instrumentation=\"" + xml_escape(config.instrument.mode) + "\""
    " data-bands=\"" + xml_escape(join(config.instrument.bands, ",")) + "\""
    " data-transient-lookback-days=\""
      + format_number(config.event_lookback_days, 3) + "\"";
  if (config.observer.kind == observer_kind::terrestrial)
    {
      astro_require(config.observer.terrestrial.has_value(),
                    "ground observer metadata is missing");
      const reference_point& point = *config.observer.terrestrial;
      result += " data-reference-point=\"" + xml_escape(config.observer.name)
        + "\" data-reference-latitude-deg=\""
        + format_number(point.latitude_deg)
        + "\" data-reference-longitude-deg-east=\""
        + format_number(point.longitude_deg_east)
        + "\" data-reference-elevation-m=\""
        + format_number(point.elevation_m, 1)
        + "\" data-sun-altitude-deg=\""
        + format_number(state.ground_sun_altitude_deg) + "\"";
    }
  else
    {
      astro_require(state.orbiting.has_value()
                      && config.observer.orbiting.has_value(),
                    "orbiting observer metadata is missing");
      const orbiting_observer_state& orbit = *state.orbiting;
      const orbiting_observer& observer = *config.observer.orbiting;
      result += " data-observer-norad-id=\"" + xml_escape(observer.norad_id)
        + "\" data-orbit-element-epoch=\""
        + xml_escape(orbit.element_epoch_utc)
        + "\" data-orbit-element-age-days=\""
        + format_number(orbit.element_age_days, 6)
        + "\" data-orbit-source=\"" + xml_escape(orbit.source_url)
        + "\" data-observer-subpoint-latitude-deg=\""
        + format_number(orbit.subpoint.latitude_deg)
        + "\" data-observer-subpoint-longitude-deg-east=\""
        + format_number(orbit.subpoint.longitude_deg_east)
        + "\" data-observer-altitude-km=\""
        + format_number(orbit.subpoint.altitude_km, 3)
        + "\" data-earth-angular-radius-deg=\""
        + format_number(orbit.earth_angular_radius_deg)
        + "\" data-earth-limb-avoidance-deg=\""
        + format_number(observer.earth_limb_avoidance_deg, 1)
        + "\" data-sun-avoidance-deg=\""
        + format_number(observer.sun_avoidance_deg, 1) + "\"";
    }
  return result + "></metadata>\n";
}

inline std::string
output_basename(const product_kind product,
                const generation::projection_spec& spec,
                const profile& config)
{
  return generation::output_basename(
    product == product_kind::all_sky
      ? std::string {"astro-all-sky"}
      : std::string {"astro-observer-"} + config.observer.id,
    spec);
}

inline void
generate(const generation::projection_spec& spec, const product_kind product,
         const profile& config)
{
  astro_require(product == product_kind::all_sky
                  ? config.all_sky_enabled : config.observer_enabled,
                "requested astronomy product is disabled by its profile");
  const std::string basename = output_basename(product, spec, config);
  const generation::projection_context context(spec, basename);
  catalogs data = load_catalogs(config);
  observer_state state = make_observer_state(config);
  calculate_observer_metrics(data, config, state);

  generation::projection_document document(
    basename,
    std::string(spec.title) + " " + std::string(product_argument(product))
      + " celestial atlas for " + config.observer.name + " / "
      + config.instrument.name + " at " + config.calculation_time.iso_utc,
    context.map_frame.frame_area);
  document.add_raw(metadata_element(config, product, state));
  add_background(document, context, config, product);
  add_reference_lines(document, context, config, product, state);

  svg::group_element labels;
  labels.start_element("labels");
  std::size_t label_count = 0;
  label_count = add_object_layer(
    document, labels, context, config, product, state, "stars", data.stars,
    label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, state, "exoplanet-hosts",
    data.exoplanet_hosts, label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, state, "deep-sky",
    data.deep_sky, label_count);
  label_count = add_object_layer(
    document, labels, context, config, product, state, "solar-system",
    data.solar_system, label_count);
  static_cast<void>(add_object_layer(
    document, labels, context, config, product, state, "transients",
    data.transients, label_count));
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
    astro_require(generated.find("<g id=\"" + std::string(layer) + "\"")
                    != std::string::npos,
                  "generated astronomy SVG is missing layer "
                    + std::string(layer));
  astro_require(generated.find("id=\"astro-metadata\"") != std::string::npos
                  && generated.find("data-timestamp=\""
                                      + config.calculation_time.iso_utc + "\"")
                       != std::string::npos
                  && generated.find("data-observer-id=\""
                                      + config.observer.id + "\"")
                       != std::string::npos
                  && generated.find("data-instrument-id=\""
                                      + config.instrument.id + "\"")
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
      astro_require(token_count(
                      generated, "data-planet-true-angular-size=\"true\"")
                      >= 7,
                    "all-sky astronomy SVG omits true planet-size outlines");
      astro_require(token_count(generated, "data-kind=\"asteroid\"") >= 1
                      && token_count(generated, "data-kind=\"comet\"") >= 1,
                    "all-sky astronomy SVG omits small-body classes");
      astro_require(generated.find("ground-observer-horizon-segment-")
                      == std::string::npos
                      && generated.find("hubble-earth-limb-segment-")
                           == std::string::npos,
                    "all-sky astronomy SVG unexpectedly has an observer "
                    "horizon");
    }
  else if (config.observer.kind == observer_kind::terrestrial)
    {
      astro_require(generated.find("ground-observer-horizon-segment-")
                      != std::string::npos,
                    "ground-observer astronomy SVG is missing its horizon");
      astro_require(generated.find("data-observer-kind=\"terrestrial\"")
                      != std::string::npos,
                    "ground-observer SVG is missing its platform kind");
    }
  else
    {
      astro_require(generated.find("hubble-earth-limb-segment-")
                      != std::string::npos
                      && generated.find("hubble-earth-avoidance-segment-")
                           != std::string::npos
                      && generated.find("hubble-sun-avoidance-segment-")
                           != std::string::npos,
                    "Hubble observer SVG is missing pointing limits");
      astro_require(generated.find("data-observer-norad-id=\"20580\"")
                      != std::string::npos
                      && generated.find("data-orbit-element-epoch=\"")
                           != std::string::npos,
                    "Hubble observer SVG is missing orbit provenance");
    }
  if (product == product_kind::observer)
    {
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
  generation::verify_configured_label_font(generated, "astronomy SVG");
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
  const std::string basename = output_basename(product, spec, config);
  const generation::projection_context context(spec, basename);
  generate(spec, product, config);
  verify(read_generated(basename), context, product, config);
  return 0;
}

} // namespace cart0freak0::astro_generation

#endif
