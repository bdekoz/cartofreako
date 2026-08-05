#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <string>
#include <string_view>

#include "astro-data.h"

namespace {

namespace astro = cart0freak0::astro_generation;

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
check_coordinates(const std::vector<astro::sky_object>& objects)
{
  for (const astro::sky_object& object : objects)
    {
      assert(std::isfinite(object.ra_deg));
      assert(std::isfinite(object.dec_deg));
      assert(object.ra_deg >= 0 && object.ra_deg < 360);
      assert(object.dec_deg >= -90 && object.dec_deg <= 90);
      assert(std::isfinite(object.altitude_deg));
      assert(object.altitude_deg >= -90 && object.altitude_deg <= 90);
    }
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
  assert(config.observer.name == "San Francisco, California, USA");
  assert(near(config.observer.latitude_deg, 37.7749, 1e-12));
  assert(near(config.observer.longitude_deg_east, -122.4194, 1e-12));
  assert(near(config.observer.elevation_m, 16, 1e-12));
  assert(config.sky_orientation.celestial_handedness);
  assert(near(config.sky_orientation.central_right_ascension_deg, 180, 1e-12));
  assert(config.instrument.mode == "multi-band");
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

  const double sidereal = astro::local_sidereal_time(config);
  assert(near(astro::altitude_degrees(
                sidereal, config.observer.latitude_deg,
                config.observer.latitude_deg, sidereal),
              90, 1e-9));
  for (const double azimuth : {0.0, 90.0, 180.0, 270.0})
    {
      const astro::right_ascension_declination horizon
        = astro::horizontal_to_equatorial(
          azimuth, 0, config.observer.latitude_deg, sidereal);
      assert(near(astro::altitude_degrees(
                    horizon.ra_deg, horizon.dec_deg,
                    config.observer.latitude_deg, sidereal),
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

  astro::calculate_altitudes(catalogs, config);
  check_coordinates(catalogs.stars);
  check_coordinates(catalogs.exoplanet_hosts);
  check_coordinates(catalogs.deep_sky);
  check_coordinates(catalogs.transients);
  check_coordinates(catalogs.solar_system);

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

  astro::profile shorter_window = config;
  shorter_window.event_lookback_days = 3;
  assert(astro::load_curated_catalog(shorter_window).events.size() == 4);

  astro::sky_object optical {
    "optical-test", "Optical test", "star", {"optical"},
    sidereal, config.observer.latitude_deg, 5.0,
    std::nullopt, std::nullopt, std::nullopt, "", "",
  };
  optical.altitude_deg = 90;
  assert(astro::object_visible_to_observer(optical, config, -19));
  assert(!astro::object_visible_to_observer(optical, config, -17));
  optical.magnitude = 6.0;
  assert(!astro::object_visible_to_observer(optical, config, -19));
  optical.bands = {"radio"};
  assert(astro::object_visible_to_observer(optical, config, 30));
  optical.altitude_deg = -0.001;
  assert(!astro::object_visible_to_observer(optical, config, -30));
}
