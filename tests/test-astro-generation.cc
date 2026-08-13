#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <string>
#include <string_view>

#include "astro-generation.h"

namespace {

namespace astro = cart0freak0::astro_generation;
namespace generation = cart0freak0::generation;

bool
near(const double left, const double right, const double tolerance)
{ return std::abs(left - right) <= tolerance; }

const astro::sky_object&
find_object(const std::vector<astro::sky_object>& objects,
            const std::string_view id)
{
  const auto found = std::find_if(
    objects.begin(), objects.end(),
    [id](const astro::sky_object& object) { return object.id == id; });
  assert(found != objects.end());
  return *found;
}

void
check_ground_coordinates(const std::vector<astro::sky_object>& objects)
{
  for (const astro::sky_object& object : objects)
    {
      assert(std::isfinite(object.ra_deg));
      assert(std::isfinite(object.dec_deg));
      assert(object.ra_deg >= 0 && object.ra_deg < 360);
      assert(object.dec_deg >= -90 && object.dec_deg <= 90);
      assert(std::isfinite(object.observer_angle_deg));
      assert(object.observer_angle_deg >= -90
             && object.observer_angle_deg <= 90);
    }
}

void
check_hubble_coordinates(const std::vector<astro::sky_object>& objects)
{
  for (const astro::sky_object& object : objects)
    {
      assert(std::isfinite(object.observer_angle_deg));
      assert(object.observer_angle_deg >= -90
             && object.observer_angle_deg <= 180);
      assert(std::isfinite(object.sun_separation_deg));
      assert(object.sun_separation_deg >= 0
             && object.sun_separation_deg <= 180);
    }
}

double
maximum_segment(const std::vector<svg::vrange>& paths)
{
  double result = 0;
  for (const svg::vrange& path : paths)
    for (std::size_t index = 1; index < path.size(); ++index)
      result = std::max(
        result,
        generation::point_distance(path[index - 1], path[index]));
  return result;
}

} // namespace

int
main()
{
  const astro::profile config = astro::load_profile(
    "assets.static/astronomy/astro-profile.json");

  // The profile, rather than the host clock or an inferred machine location,
  // is the sole authority for the calculation instant and point of reference.
  assert(config.calculation_time.iso_utc == "2026-08-05T01:59:44Z");
  assert(config.all_sky_enabled && config.observer_enabled);
  assert(config.observer.id == "ground-multiband");
  assert(config.observer.name == "San Francisco, California, USA");
  assert(config.observer.kind == astro::observer_kind::terrestrial);
  assert(config.observer.terrestrial.has_value());
  assert(near(config.observer.terrestrial->latitude_deg, 37.7749, 1e-12));
  assert(near(config.observer.terrestrial->longitude_deg_east,
              -122.4194, 1e-12));
  assert(near(config.observer.terrestrial->elevation_m, 16, 1e-12));
  assert(config.sky_orientation.celestial_handedness);
  assert(near(config.sky_orientation.central_right_ascension_deg, 180, 1e-12));
  assert(config.instrument.id == "generic-ground-multiband");
  assert(config.instrument.mode == "ground-multi-band");
  assert(config.instrument.optical_limiting_magnitude.has_value());
  assert(near(config.event_lookback_days, 7, 1e-12));

  const astro::instant j2000 = astro::parse_timestamp(
    "2000-01-01T12:00:00Z");
  assert(near(j2000.julian_date, astro::julian_j2000, 1e-12));
  assert(near(astro::greenwich_mean_sidereal_time(j2000.julian_date),
              280.46061837, 1e-10));

  assert(near(astro::celestial_longitude(config.sky_orientation, 180), 0,
              1e-12));
  assert(near(astro::celestial_longitude(config.sky_orientation, 90), 90,
              1e-12));
  assert(near(astro::celestial_longitude(config.sky_orientation, 270), -90,
              1e-12));
  const astro::orientation terrestrial {false, 180};
  assert(near(astro::celestial_longitude(terrestrial, 90), -90, 1e-12));

  const generation::projection_context cahill_keyes_context(
    generation::find_projection_spec("cahill-keyes"), "");
  const auto celestial_equator = astro::project_celestial_path(
    cahill_keyes_context, config, astro::celestial_equator());
  assert(celestial_equator.size() >= 2);
  bool found_frame_fold = false;
  for (std::size_t index = 1; index < celestial_equator.size(); ++index)
    {
      const svg::point_2t exit = celestial_equator[index - 1].back();
      const svg::point_2t entry = celestial_equator[index].front();
      if (near(std::get<0>(exit), 0, 1e-12)
          && near(std::get<0>(entry),
                  cahill_keyes_context.map_frame.width(), 1e-12)
          && near(std::get<1>(exit), std::get<1>(entry), 1e-12))
        found_frame_fold = true;
    }
  assert(found_frame_fold);
  assert(maximum_segment(celestial_equator)
         < cahill_keyes_context.map_frame.width() / 4);
  for (const auto& reference : {
         astro::project_celestial_path(
           cahill_keyes_context, config, astro::ecliptic_line()),
         astro::project_celestial_path(
           cahill_keyes_context, config, astro::galactic_equator()),
       })
    assert(maximum_segment(reference)
           < cahill_keyes_context.map_frame.width() / 2);

  const generation::projection_context star_x_context(
    generation::find_projection_spec("star-x"), "");
  const auto star_x_equator = astro::project_celestial_path(
    star_x_context, config, astro::celestial_equator());
  assert(star_x_equator.size() == 5);
  assert(maximum_segment(star_x_equator)
         < star_x_context.map_frame.width() / 4);
  bool found_star_x_group_fold = false;
  for (std::size_t index = 1; index < star_x_equator.size(); ++index)
    {
      const svg::point_2t exit = star_x_equator[index - 1].back();
      const svg::point_2t entry = star_x_equator[index].front();
      if (near(std::get<0>(exit), std::get<0>(entry), 1e-12)
          && std::abs(std::get<1>(exit) - std::get<1>(entry))
               > star_x_context.map_frame.height() / 4)
        found_star_x_group_fold = true;
    }
  assert(found_star_x_group_fold);
  for (const auto& reference : {
         astro::project_celestial_path(
           star_x_context, config, astro::ecliptic_line()),
         astro::project_celestial_path(
           star_x_context, config, astro::galactic_equator()),
       })
    assert(maximum_segment(reference)
           < star_x_context.map_frame.width() / 4);

  const double sidereal = astro::local_sidereal_time(config);
  assert(near(astro::altitude_degrees(
                sidereal, config.observer.terrestrial->latitude_deg,
                config.observer.terrestrial->latitude_deg, sidereal),
              90, 1e-9));
  for (const double azimuth : {0.0, 90.0, 180.0, 270.0})
    {
      const astro::right_ascension_declination horizon
        = astro::horizontal_to_equatorial(
          azimuth, 0, config.observer.terrestrial->latitude_deg, sidereal);
      assert(near(astro::altitude_degrees(
                    horizon.ra_deg, horizon.dec_deg,
                    config.observer.terrestrial->latitude_deg, sidereal),
                  0, 1e-10));
    }

  astro::catalogs catalogs = astro::load_catalogs(config);
  assert(catalogs.stars.size() == 500);
  assert(catalogs.exoplanet_hosts.size() == 247);
  assert(catalogs.deep_sky.size() == 11);
  assert(catalogs.transients.size() == 6);
  assert(catalogs.solar_system.size() == 16);
  assert(std::count_if(
           catalogs.solar_system.begin(), catalogs.solar_system.end(),
           [](const astro::sky_object& object) {
             return object.kind == "planet";
           }) == 7);
  for (const astro::sky_object& object : catalogs.solar_system)
    if (object.kind == "planet")
      {
        assert(object.apparent_angular_radius_deg.has_value());
        assert(*object.apparent_angular_radius_deg > 0
               && *object.apparent_angular_radius_deg < 0.1);
        assert(astro::marker_radius(object) == 0.15);
      }
  assert(std::count_if(
           catalogs.solar_system.begin(), catalogs.solar_system.end(),
           [](const astro::sky_object& object) {
             return object.kind == "asteroid";
           }) == 4);
  assert(std::count_if(
           catalogs.solar_system.begin(), catalogs.solar_system.end(),
           [](const astro::sky_object& object) {
             return object.kind == "comet";
           }) == 3);

  astro::observer_state ground_state = astro::make_observer_state(config);
  astro::calculate_observer_metrics(catalogs, config, ground_state);
  assert(near(ground_state.ground_sun_altitude_deg, 13.18, 0.02));
  check_ground_coordinates(catalogs.stars);
  check_ground_coordinates(catalogs.exoplanet_hosts);
  check_ground_coordinates(catalogs.deep_sky);
  check_ground_coordinates(catalogs.transients);
  check_ground_coordinates(catalogs.solar_system);

  // Pinned topocentric ICRF references from JPL Horizons at the profile's SF
  // site and timestamp. The implementation is intentionally approximate and
  // geocentric, but remains comfortably within visualization-scale accuracy.
  const astro::sky_object& sun = find_object(catalogs.solar_system, "sun");
  assert(near(sun.ra_deg, 134.7884167, 0.05));
  assert(near(sun.dec_deg, 17.0988611, 0.05));
  const astro::sky_object& jupiter = find_object(
    catalogs.solar_system, "jupiter");
  assert(near(jupiter.ra_deg, 130.0326667, 0.05));
  assert(near(jupiter.dec_deg, 18.8608611, 0.05));
  assert(jupiter.apparent_angular_radius_deg.has_value());
  assert(*jupiter.apparent_angular_radius_deg > 0.003
         && *jupiter.apparent_angular_radius_deg < 0.01);
  const std::string jupiter_attributes = astro::object_attributes(
    jupiter, config, ground_state);
  assert(jupiter_attributes.find("data-display-radius-scale=\"2\"")
         != std::string::npos);
  assert(jupiter_attributes.find("data-apparent-angular-diameter-arcsec=")
         != std::string::npos);

  astro::profile shorter_window = config;
  shorter_window.event_lookback_days = 3;
  assert(astro::load_curated_catalog(shorter_window).events.size() == 4);

  astro::sky_object optical {
    "optical-test", "Optical test", "star", {"optical"},
    sidereal, config.observer.terrestrial->latitude_deg, 5.0,
    std::nullopt, std::nullopt, std::nullopt, "", "",
  };
  optical.observer_angle_deg = 90;
  assert(astro::object_visible_to_observer(optical, config, -19));
  assert(!astro::object_visible_to_observer(optical, config, -17));
  optical.magnitude = 6.0;
  assert(!astro::object_visible_to_observer(optical, config, -19));
  optical.bands = {"radio"};
  assert(astro::object_visible_to_observer(optical, config, 30));
  optical.observer_angle_deg = -0.001;
  assert(!astro::object_visible_to_observer(optical, config, -30));

  const astro::profile hubble = astro::load_profile(
    "assets.static/astronomy/astro-hubble-profile.json");
  assert(!hubble.all_sky_enabled && hubble.observer_enabled);
  assert(hubble.observer.id == "hubble");
  assert(hubble.observer.name == "Hubble Space Telescope");
  assert(hubble.observer.kind == astro::observer_kind::orbiting);
  assert(hubble.observer.orbiting.has_value());
  assert(hubble.observer.orbiting->norad_id == "20580");
  assert(near(hubble.observer.orbiting->earth_limb_avoidance_deg,
              20, 1e-12));
  assert(near(hubble.observer.orbiting->sun_avoidance_deg, 60.3, 1e-12));
  assert(hubble.instrument.id == "hst-composite");
  assert(hubble.instrument.mode == "hst-composite");
  assert(!hubble.instrument.optical_limiting_magnitude.has_value());
  assert(hubble.instrument.night_required_bands.empty());

  astro::observer_state hubble_state = astro::make_observer_state(hubble);
  assert(hubble_state.orbiting.has_value());
  assert(hubble_state.orbiting->element_epoch_utc
         == "2026-08-12T22:01:03.125856Z");
  assert(hubble_state.orbiting->element_age_days > 0.7
         && hubble_state.orbiting->element_age_days < 0.8);
  assert(hubble_state.orbiting->subpoint.altitude_km > 450
         && hubble_state.orbiting->subpoint.altitude_km < 650);
  assert(hubble_state.orbiting->earth_angular_radius_deg > 65
         && hubble_state.orbiting->earth_angular_radius_deg < 70);

  astro::catalogs hubble_catalogs = astro::load_catalogs(hubble);
  astro::calculate_observer_metrics(hubble_catalogs, hubble, hubble_state);
  check_hubble_coordinates(hubble_catalogs.stars);
  check_hubble_coordinates(hubble_catalogs.exoplanet_hosts);
  check_hubble_coordinates(hubble_catalogs.deep_sky);
  check_hubble_coordinates(hubble_catalogs.transients);
  check_hubble_coordinates(hubble_catalogs.solar_system);
  const astro::sky_object& hubble_sun = find_object(
    hubble_catalogs.solar_system, "sun");
  assert(near(hubble_sun.sun_separation_deg, 0, 1e-9));
  assert(!astro::object_visible_to_platform(
    hubble_sun, hubble, hubble_state));
  assert(std::count_if(
           hubble_catalogs.stars.begin(), hubble_catalogs.stars.end(),
           [&](const astro::sky_object& object) {
             return astro::object_visible_to_platform(
               object, hubble, hubble_state);
           }) > 25);

  const astro::right_ascension_declination earth_center
    = hubble_state.orbiting->earth_center;
  for (const std::string_view name : {
         "cahill-keyes", "authagraph", "dymaxion", "myriahedral",
         "star-x", "voronoi",
       })
    {
      const generation::projection_context context(
        generation::find_projection_spec(name), "");
      assert(!astro::project_celestial_path(
        context, hubble, astro::angular_circle(
          earth_center, hubble_state.orbiting->earth_angular_radius_deg))
                   .empty());
    }

  const std::string hubble_metadata = astro::metadata_element(
    hubble, astro::product_kind::observer, hubble_state);
  assert(hubble_metadata.find("data-observer-id=\"hubble\"")
         != std::string::npos);
  assert(hubble_metadata.find("data-instrument-id=\"hst-composite\"")
         != std::string::npos);
  assert(hubble_metadata.find(
           "data-orbit-element-epoch=\"2026-08-12T22:01:03.125856Z\"")
         != std::string::npos);
  assert(astro::output_basename(
           astro::product_kind::observer,
           generation::find_projection_spec("cahill-keyes"), hubble)
         == "astro-observer-hubble-ck-44-22");
  assert(astro::output_basename(
           astro::product_kind::observer,
           generation::find_projection_spec("cahill-keyes"), config)
         == "astro-observer-ground-multiband-ck-44-22");
}
