// Ground and orbiting observer state for astronomy generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ASTRO_OBSERVER_H
#define CART0FREAK0_ASTRO_OBSERVER_H 1

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <string>
#include <vector>

#include "astro-data.h"
#include "orbiting-data.h"

namespace cart0freak0::astro_generation {

namespace orbital = cart0freak0::orbiting_generation;

struct orbiting_observer_state
{
  orbital::vector_3d position_teme_km;
  orbital::geodetic_position subpoint;
  right_ascension_declination earth_center;
  double earth_angular_radius_deg;
  std::string element_epoch_utc;
  double element_age_days;
  std::string source_url;
};

struct observer_state
{
  observer_kind kind;
  double ground_sun_altitude_deg
    = std::numeric_limits<double>::quiet_NaN();
  std::optional<orbiting_observer_state> orbiting;
};

inline vector_3d
equatorial_unit_vector(const double ra_deg, const double dec_deg)
{
  const double ra = degrees_to_radians(ra_deg);
  const double dec = degrees_to_radians(dec_deg);
  return {std::cos(dec) * std::cos(ra),
          std::cos(dec) * std::sin(ra), std::sin(dec)};
}

inline right_ascension_declination
equatorial_coordinates(const orbital::vector_3d value)
{
  const double magnitude = orbital::length(value);
  astro_require(magnitude > 0 && std::isfinite(magnitude),
                "observer vector must be finite and nonzero");
  return {
    normalize_degrees(radians_to_degrees(std::atan2(value.y, value.x))),
    radians_to_degrees(std::asin(std::clamp(
      value.z / magnitude, -1.0, 1.0))),
  };
}

inline double
angular_separation_degrees(const vector_3d left, const vector_3d right)
{
  const double cosine = left.x * right.x + left.y * right.y
    + left.z * right.z;
  return radians_to_degrees(std::acos(std::clamp(cosine, -1.0, 1.0)));
}

inline observer_state
make_observer_state(const profile& config)
{
  observer_state result {
    config.observer.kind,
    std::numeric_limits<double>::quiet_NaN(),
    std::nullopt,
  };
  if (config.observer.kind == observer_kind::terrestrial)
    return result;

  astro_require(config.observer.orbiting.has_value(),
                "orbiting observer configuration is missing");
  const orbiting_observer& observer = *config.observer.orbiting;
  const std::vector<orbital::orbital_object> catalog
    = orbital::load_omm_catalog(observer.omm_catalog, observer.source_url);
  const auto found = std::find_if(
    catalog.begin(), catalog.end(), [&](const orbital::orbital_object& object) {
      return object.norad_id == observer.norad_id;
    });
  astro_require(found != catalog.end(),
                "OMM catalog lacks orbiting observer NORAD "
                  + observer.norad_id);
  const double element_age_days = config.calculation_time.julian_date
    - found->epoch.julian_date;
  astro_require(element_age_days >= 0,
                "orbiting observer element epoch is after profile time");
  astro_require(element_age_days <= observer.maximum_element_age_days,
                "orbiting observer element epoch exceeds maximum age");

  const orbital::teme_state propagated = orbital::propagate_teme(
    *found, config.calculation_time.julian_date);
  const double distance = orbital::length(propagated.position_km);
  astro_require(distance > orbital::earth_equatorial_radius_km,
                "orbiting observer propagated inside Earth");
  const orbital::vector_3d earthward {
    -propagated.position_km.x,
    -propagated.position_km.y,
    -propagated.position_km.z,
  };
  std::string epoch = found->epoch.iso_utc;
  if (epoch.empty() || epoch.back() != 'Z')
    epoch += 'Z';
  result.orbiting = orbiting_observer_state {
    propagated.position_km,
    orbital::ecef_to_geodetic(orbital::teme_to_ecef(
      propagated.position_km, config.calculation_time.julian_date)),
    equatorial_coordinates(earthward),
    radians_to_degrees(std::asin(
      orbital::earth_equatorial_radius_km / distance)),
    std::move(epoch),
    element_age_days,
    found->source_url,
  };
  return result;
}

inline const sky_object&
sun_object(const catalogs& data)
{
  const auto found = std::find_if(
    data.solar_system.begin(), data.solar_system.end(),
    [](const sky_object& object) { return object.id == "sun"; });
  astro_require(found != data.solar_system.end(),
                "Solar System catalog is missing the Sun");
  return *found;
}

template<typename Function>
inline void
for_each_sky_object(catalogs& data, Function function)
{
  for (std::vector<sky_object>* objects : {
         &data.stars, &data.exoplanet_hosts, &data.deep_sky,
         &data.solar_system, &data.transients,
       })
    for (sky_object& object : *objects)
      function(object);
}

inline void
calculate_observer_metrics(catalogs& data, const profile& config,
                           observer_state& state)
{
  if (config.observer.kind == observer_kind::terrestrial)
    {
      calculate_ground_altitudes(data, config);
      state.ground_sun_altitude_deg = sun_object(data).observer_angle_deg;
      return;
    }

  astro_require(state.orbiting.has_value()
                  && config.observer.orbiting.has_value(),
                "HST observer state is missing");
  const orbiting_observer_state& orbit = *state.orbiting;
  const vector_3d earth = equatorial_unit_vector(
    orbit.earth_center.ra_deg, orbit.earth_center.dec_deg);
  const sky_object& sun = sun_object(data);
  const vector_3d sun_direction = equatorial_unit_vector(
    sun.ra_deg, sun.dec_deg);
  for_each_sky_object(data, [&](sky_object& object) {
    const vector_3d direction = equatorial_unit_vector(
      object.ra_deg, object.dec_deg);
    object.observer_angle_deg = angular_separation_degrees(
      direction, earth) - orbit.earth_angular_radius_deg;
    object.sun_separation_deg = angular_separation_degrees(
      direction, sun_direction);
  });
}

inline bool
object_visible_to_platform(const sky_object& object, const profile& config,
                           const observer_state& state)
{
  if (config.observer.kind == observer_kind::terrestrial)
    return object_visible_to_observer(
      object, config, state.ground_sun_altitude_deg);
  astro_require(config.observer.orbiting.has_value(),
                "orbiting observer configuration is missing");
  return object.observer_angle_deg
           >= config.observer.orbiting->earth_limb_avoidance_deg
    && object.sun_separation_deg
         >= config.observer.orbiting->sun_avoidance_deg
    && object_matches_instrument(object, config,
                                 state.ground_sun_altitude_deg);
}

} // namespace cart0freak0::astro_generation

#endif
