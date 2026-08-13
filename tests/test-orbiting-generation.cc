// Orbital Technosphere profile, OMM, SGP4, and reference checks.

#include <cassert>
#include <cmath>
#include <filesystem>
#include <string_view>

#include "orbiting-data.h"

namespace orbital = cart0freak0::orbiting_generation;

namespace {

bool
near(const double value, const double expected, const double tolerance)
{ return std::abs(value - expected) <= tolerance; }

const orbital::orbital_object&
find_norad(const orbital::catalog_bundle& catalog, const std::string_view id)
{
  const auto found = std::find_if(
    catalog.objects.begin(), catalog.objects.end(),
    [&](const orbital::orbital_object& object) { return object.norad_id == id; });
  assert(found != catalog.objects.end());
  return *found;
}

double
distance(const orbital::vector_3d left, const orbital::vector_3d right)
{ return orbital::length(left - right); }

} // namespace

int
main()
{
  assert(near(orbital::parse_timestamp(
                "2000-01-01T12:00:00Z").julian_date,
              2451545.0, 1e-9));
  assert(near(orbital::parse_timestamp(
                "2000-01-01T12:00:00.500000", false).julian_date,
              2451545.0 + 0.5 / orbital::seconds_per_day, 1e-9));

  // First verification case from Vallado et al., AIAA 2006-6753. The OMM
  // adapter must reproduce the upstream TEME vector at its element epoch.
  const orbital::orbital_object vanguard {
    "VANGUARD 1", "1958-002B",
    orbital::parse_timestamp("2000-06-27T18:50:19.733568", false),
    10.82419157, 0.1859667, 34.2682, 348.7242, 331.7664, 19.3264,
    "U", "00005", 475, 41366, 0.28098e-4, 0.00000023, 0,
    {}, {}, "https://celestrak.org/publications/AIAA/2006-6753/",
  };
  const orbital::teme_state vanguard_state = orbital::propagate_teme(
    vanguard, vanguard.epoch.julian_date);
  assert(near(vanguard_state.position_km.x, 7022.46529266, 1e-6));
  assert(near(vanguard_state.position_km.y, -1400.08296755, 1e-6));
  assert(near(vanguard_state.position_km.z, 0.03995155, 1e-6));
  assert(near(vanguard_state.velocity_km_s.x, 1.893841015, 1e-9));
  assert(near(vanguard_state.velocity_km_s.y, 6.405893759, 1e-9));
  assert(near(vanguard_state.velocity_km_s.z, 4.534807250, 1e-9));

  const std::filesystem::path profile_path
    = "assets.static/orbital-technosphere/orbital-technosphere-profile.json";
  const orbital::profile config = orbital::load_profile(profile_path);
  assert(config.name == "San Francisco Orbital Technosphere");
  assert(config.calculation_time.iso_utc == "2026-08-13T15:36:00Z");
  assert(config.observer.name == "San Francisco, California, USA");
  assert(near(config.observer.latitude_deg, 37.7749, 1e-12));
  assert(config.groups.size() == 15);
  assert(config.propagation.maximum_element_age_days == 7);

  const orbital::vector_3d site_ecef = orbital::observer_ecef(config.observer);
  const orbital::geodetic_position site_round_trip
    = orbital::ecef_to_geodetic(site_ecef);
  assert(near(site_round_trip.latitude_deg,
              config.observer.latitude_deg, 1e-9));
  assert(near(site_round_trip.longitude_deg_east,
              config.observer.longitude_deg_east, 1e-9));
  assert(near(site_round_trip.altitude_km,
              config.observer.elevation_m / 1000.0, 1e-8));
  assert(near(orbital::length(orbital::solar_unit_vector(
                config.calculation_time.julian_date)), 1, 1e-12));
  assert(std::isfinite(orbital::solar_altitude_deg(
    config, config.calculation_time.julian_date)));

  const orbital::catalog_bundle catalogs = orbital::load_catalogs(config);
  assert(catalogs.active_records > 10000);
  assert(catalogs.debris_records > 100);
  assert(catalogs.objects.size()
           == catalogs.active_records + catalogs.debris_records);
  assert(std::any_of(catalogs.objects.begin(), catalogs.objects.end(),
    [](const orbital::orbital_object& object) {
      return object.norad_id.size() >= 6;
    }));

  const orbital::orbital_object& iss = find_norad(catalogs, "25544");
  assert(std::find(iss.roles.begin(), iss.roles.end(), "human-presence")
           != iss.roles.end());
  const orbital::orbital_object& starlink = *std::find_if(
    catalogs.objects.begin(), catalogs.objects.end(),
    [](const orbital::orbital_object& object) {
      return std::find(object.roles.begin(), object.roles.end(),
                       "megaconstellation") != object.roles.end();
    });
  assert(!starlink.norad_id.empty());

  // NASA SSCWeb GEO positions at 2026-08-13T15:36:00Z. Public OMM/SGP4
  // states are expected to agree at visualization scale, not operational
  // orbit-determination precision.
  const double nasa_time = orbital::parse_timestamp(
    "2026-08-13T15:36:00Z").julian_date;
  const orbital::vector_3d iss_ecef = orbital::teme_to_ecef(
    orbital::propagate_teme(iss, nasa_time).position_km, nasa_time);
  assert(distance(iss_ecef,
                  {-888.7007162486722, 4192.760987163541,
                   -5284.562706947327}) < 100);
  const orbital::orbital_object& goes19 = find_norad(catalogs, "60133");
  const orbital::vector_3d goes19_ecef = orbital::teme_to_ecef(
    orbital::propagate_teme(goes19, nasa_time).position_km, nasa_time);
  assert(distance(goes19_ecef,
                  {10778.09601978017, -40764.78455148575,
                   17.692609690129757}) < 150);

  const rapidjson::Document nasa = orbital::read_json(config.nasa_reference);
  assert(nasa.IsArray() && nasa.Size() == 2);
  assert(nasa[1].IsObject() && nasa[1].HasMember("Result"));
  assert(nasa[1]["Result"].IsArray());
  assert(nasa[1]["Result"][1]["StatusCode"].GetString()
           == std::string_view("SUCCESS"));

  const orbital::propagated_catalog propagated
    = orbital::propagate_catalog(catalogs, config);
  assert(propagated.objects.size() > 10000);
  assert(propagated.failed_propagation < 10);
  for (const orbital::propagated_object& object : propagated.objects)
    {
      assert(std::isfinite(object.subpoint.latitude_deg));
      assert(object.subpoint.latitude_deg >= -90
               && object.subpoint.latitude_deg <= 90);
      assert(object.subpoint.longitude_deg_east >= -180
               && object.subpoint.longitude_deg_east <= 180);
      assert(std::isfinite(object.horizontal.elevation_deg));
    }
}
