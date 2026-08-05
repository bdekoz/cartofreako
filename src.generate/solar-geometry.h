// Shared low-precision solar geometry for celestial and terrestrial passes.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_SOLAR_GEOMETRY_H
#define CART0FREAK0_SOLAR_GEOMETRY_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <numbers>
#include <string_view>

#include "generation-instant.h"

namespace cart0freak0::solar_geometry {

using generation_time::instant;
using generation_time::julian_j2000;

inline double
degrees_to_radians(const double degrees)
{ return degrees * std::numbers::pi / 180.0; }

inline double
radians_to_degrees(const double radians)
{ return radians * 180.0 / std::numbers::pi; }

inline double
normalize_degrees(double degrees)
{
  degrees = std::fmod(degrees, 360.0);
  if (degrees < 0)
    degrees += 360.0;
  return degrees;
}

inline double
normalize_signed_degrees(const double degrees)
{
  double result = normalize_degrees(degrees);
  if (result > 180.0)
    result -= 360.0;
  return result;
}

struct equatorial_position
{
  double right_ascension_deg;
  double declination_deg;
};

struct geographic_position
{
  double latitude_deg;
  double longitude_deg_east;
};

struct cartesian_vector
{
  double x;
  double y;
  double z;
};

inline double
solve_eccentric_anomaly(const double mean_anomaly, const double eccentricity)
{
  double eccentric_anomaly = mean_anomaly
    + eccentricity * std::sin(mean_anomaly);
  for (int iteration = 0; iteration < 32; ++iteration)
    {
      const double correction
        = (mean_anomaly - (eccentric_anomaly
                           - eccentricity * std::sin(eccentric_anomaly)))
          / (1 - eccentricity * std::cos(eccentric_anomaly));
      eccentric_anomaly += correction;
      if (std::abs(correction) < 1e-13)
        break;
    }
  return eccentric_anomaly;
}

inline cartesian_vector
orbital_vector(const double semi_major_axis, const double eccentricity,
               const double inclination_deg, const double mean_anomaly_deg,
               const double longitude_perihelion_deg,
               const double longitude_node_deg)
{
  const double mean_anomaly = degrees_to_radians(
    normalize_signed_degrees(mean_anomaly_deg));
  const double eccentric_anomaly = solve_eccentric_anomaly(
    mean_anomaly, eccentricity);
  const double x_orbit = semi_major_axis
    * (std::cos(eccentric_anomaly) - eccentricity);
  const double y_orbit = semi_major_axis
    * std::sqrt(1 - eccentricity * eccentricity)
    * std::sin(eccentric_anomaly);
  const double inclination = degrees_to_radians(inclination_deg);
  const double node = degrees_to_radians(longitude_node_deg);
  const double argument_perihelion = degrees_to_radians(
    longitude_perihelion_deg - longitude_node_deg);
  const double cos_w = std::cos(argument_perihelion);
  const double sin_w = std::sin(argument_perihelion);
  const double cos_node = std::cos(node);
  const double sin_node = std::sin(node);
  const double cos_i = std::cos(inclination);
  const double sin_i = std::sin(inclination);
  return {
    (cos_w * cos_node - sin_w * sin_node * cos_i) * x_orbit
      + (-sin_w * cos_node - cos_w * sin_node * cos_i) * y_orbit,
    (cos_w * sin_node + sin_w * cos_node * cos_i) * x_orbit
      + (-sin_w * sin_node + cos_w * cos_node * cos_i) * y_orbit,
    sin_w * sin_i * x_orbit + cos_w * sin_i * y_orbit,
  };
}

// Visualization-grade geocentric solar coordinates using the same JPL
// approximate Earth elements as the astronomy pass. Sharing this function is
// more important here than mixing independent solar approximations.
inline equatorial_position
sun_equatorial_position(const double julian_date)
{
  constexpr std::array base {
    1.00000261, 0.01671123, -0.00001531, 100.46457166,
    102.93768193, 0.0,
  };
  constexpr std::array rate {
    0.00000562, -0.00004392, -0.01294668, 35999.37244981,
    0.32327364, 0.0,
  };
  const double centuries = (julian_date - julian_j2000) / 36525.0;
  std::array<double, 6> element {};
  for (std::size_t index = 0; index < element.size(); ++index)
    element[index] = base[index] + rate[index] * centuries;
  const cartesian_vector earth = orbital_vector(
    element[0], element[1], element[2], element[3] - element[4],
    element[4], element[5]);
  const cartesian_vector geocentric {-earth.x, -earth.y, -earth.z};
  constexpr double obliquity_deg = 23.43928;
  const double obliquity = degrees_to_radians(obliquity_deg);
  const cartesian_vector equatorial {
    geocentric.x,
    std::cos(obliquity) * geocentric.y
      - std::sin(obliquity) * geocentric.z,
    std::sin(obliquity) * geocentric.y
      + std::cos(obliquity) * geocentric.z,
  };
  const double distance = std::hypot(
    std::hypot(equatorial.x, equatorial.y), equatorial.z);
  return {
    normalize_degrees(radians_to_degrees(std::atan2(
      equatorial.y, equatorial.x))),
    radians_to_degrees(std::asin(
      std::clamp(equatorial.z / distance, -1.0, 1.0))),
  };
}

inline double
greenwich_mean_sidereal_time(const double julian_date)
{
  const double days = julian_date - julian_j2000;
  const double centuries = days / 36525.0;
  return normalize_degrees(
    280.46061837 + 360.98564736629 * days
      + 0.000387933 * centuries * centuries
      - centuries * centuries * centuries / 38710000.0);
}

inline geographic_position
subsolar_position(const instant& calculation_time)
{
  const equatorial_position sun = sun_equatorial_position(
    calculation_time.julian_date);
  return {
    sun.declination_deg,
    normalize_signed_degrees(sun.right_ascension_deg
      - greenwich_mean_sidereal_time(calculation_time.julian_date)),
  };
}

inline double
solar_altitude_degrees(const geographic_position subsolar,
                       const double latitude_deg,
                       const double longitude_deg_east)
{
  const double latitude = degrees_to_radians(latitude_deg);
  const double declination = degrees_to_radians(subsolar.latitude_deg);
  const double hour_angle = degrees_to_radians(normalize_signed_degrees(
    longitude_deg_east - subsolar.longitude_deg_east));
  const double sine_altitude
    = std::sin(latitude) * std::sin(declination)
      + std::cos(latitude) * std::cos(declination)
          * std::cos(hour_angle);
  return radians_to_degrees(std::asin(
    std::clamp(sine_altitude, -1.0, 1.0)));
}

enum class illumination_zone
{
  day,
  civil_twilight,
  nautical_twilight,
  astronomical_twilight,
  night,
};

inline illumination_zone
classify_illumination(const double solar_altitude_deg)
{
  if (solar_altitude_deg >= 0)
    return illumination_zone::day;
  if (solar_altitude_deg >= -6)
    return illumination_zone::civil_twilight;
  if (solar_altitude_deg >= -12)
    return illumination_zone::nautical_twilight;
  if (solar_altitude_deg >= -18)
    return illumination_zone::astronomical_twilight;
  return illumination_zone::night;
}

inline std::string_view
zone_name(const illumination_zone zone)
{
  switch (zone)
    {
    case illumination_zone::day: return "day";
    case illumination_zone::civil_twilight: return "civil-twilight";
    case illumination_zone::nautical_twilight: return "nautical-twilight";
    case illumination_zone::astronomical_twilight:
      return "astronomical-twilight";
    case illumination_zone::night: return "night";
    }
  return "unknown";
}

} // namespace cart0freak0::solar_geometry

#endif // CART0FREAK0_SOLAR_GEOMETRY_H
