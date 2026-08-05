#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <string_view>

#include "astro-data.h"
#include "cloud-atmosphere-generation.h"

namespace atmosphere = cart0freak0::cloud_atmosphere_generation;
namespace astro = cart0freak0::astro_generation;
namespace generation = cart0freak0::generation;
namespace solar = cart0freak0::solar_geometry;
namespace time_model = cart0freak0::generation_time;

namespace {

bool
near(const double left, const double right, const double tolerance)
{ return std::abs(left - right) <= tolerance; }

const atmosphere::source_definition&
source(const atmosphere::atmosphere_profile& profile,
       const std::string_view id)
{
  const auto found = std::find_if(
    profile.sources.begin(), profile.sources.end(),
    [id](const auto& candidate) { return candidate.id == id; });
  assert(found != profile.sources.end());
  return *found;
}

} // namespace

int
main()
{
  const atmosphere::atmosphere_profile profile
    = atmosphere::load_atmosphere_profile(
      "assets.static/cloud-atmosphere/cloud-atmosphere-profile.json");
  assert(profile.time_policy == "process-start");
  assert(profile.source_selection == "latest-not-after");
  assert(profile.h3_resolution == 3);
  assert(near(profile.minimum_valid_fraction, 0.2, 1e-12));
  assert(profile.maximum_samples_per_axis == 720);
  assert(near(profile.solar_contour_step_degrees, 1.0, 1e-12));
  assert(profile.layers.size() == 7);
  assert(profile.sources.size() == 4);
  assert(source(profile, "jaxa-ptree-cloud").access
         == "credentialed-netrc");
  assert(source(profile, "jaxa-ptree-cloud").coverage.find("daytime")
         != std::string::npos);
  assert(source(profile, "jaxa-gcom-c-aod").coverage.find("not smoke")
         != std::string::npos);
  assert(source(profile, "jaxa-gsmap-precipitation").coverage.find(
           "not flood") != std::string::npos);

  const std::size_t cloud_fraction = atmosphere::layer_index(
    profile, "cloud_fraction");
  const std::size_t cloud_optical_thickness = atmosphere::layer_index(
    profile, "cloud_optical_thickness");
  const std::size_t aerosol = atmosphere::layer_index(
    profile, "aerosol_optical_depth_500nm");
  const std::size_t precipitation = atmosphere::layer_index(
    profile, "precipitation_rate_mm_h");
  assert(profile.layers[cloud_fraction].aggregation
         == atmosphere::aggregation_kind::cloud_fraction);
  assert(profile.layers[cloud_fraction].quality.has_value());
  assert(profile.layers[cloud_fraction].quality->bit_offset == 3);
  assert(profile.layers[cloud_fraction].quality->bit_width == 2);
  assert(profile.layers[cloud_optical_thickness].quality.has_value());
  assert(profile.layers[cloud_optical_thickness].variable_candidates.front()
         == "CLOT");
  assert(profile.layers[atmosphere::layer_index(
           profile, "cloud_top_height_km")].variable_candidates.front()
         == "CLTH");
  assert(profile.layers[atmosphere::layer_index(
           profile, "cloud_type_isccp")].variable_candidates.front()
         == "CLTYPE");
  assert(profile.layers[aerosol].source_id == "jaxa-gcom-c-aod");
  assert(profile.layers[precipitation].source_id
         == "jaxa-gsmap-precipitation");
  assert(profile.layers[precipitation].variable_candidates.front()
         == "PRECIP");

  const atmosphere::atmosphere_dataset dataset
    = atmosphere::load_atmosphere_dataset(
      "assets.static/cloud-atmosphere/fixtures/cloud-atmosphere-fixture.geojson",
      profile);
  assert(dataset.fixture);
  assert(dataset.h3_resolution == 3);
  assert(dataset.source_selection_process_start.iso_utc
         == "2026-08-05T04:00:00Z");
  assert(dataset.missing_semantics == "unobserved-not-zero");
  assert(dataset.observations.size() == 4);
  assert(dataset.cells.size() == 12);
  assert(std::count_if(dataset.cells.begin(), dataset.cells.end(),
    [cloud_fraction](const auto& cell) {
      return cell.values[cloud_fraction].has_value();
    }) == 9);
  assert(std::all_of(dataset.cells.begin(), dataset.cells.end(),
    [aerosol](const auto& cell) {
      return cell.values[aerosol].has_value();
    }));

  const time_model::instant process_start = time_model::parse_timestamp(
    "2026-08-05T04:00:00Z");
  atmosphere::validate_observation_times(profile, dataset, process_start);
  atmosphere::atmosphere_dataset future = dataset;
  future.observations.front().end = time_model::parse_timestamp(
    "2026-08-05T04:00:01Z");
  bool future_rejected = false;
  try
    {
      atmosphere::validate_observation_times(profile, future, process_start);
    }
  catch (const std::runtime_error& error)
    {
      future_rejected = std::string_view(error.what()).find("ends after")
        != std::string_view::npos;
    }
  assert(future_rejected);
  atmosphere::atmosphere_dataset future_selection = dataset;
  future_selection.source_selection_process_start
    = time_model::parse_timestamp("2026-08-05T04:00:01Z");
  bool future_selection_rejected = false;
  try
    {
      atmosphere::validate_observation_times(
        profile, future_selection, process_start);
    }
  catch (const std::runtime_error& error)
    {
      future_selection_rejected = std::string_view(error.what()).find(
        "source selection occurred after") != std::string_view::npos;
    }
  assert(future_selection_rejected);
  bool stale_rejected = false;
  try
    {
      atmosphere::validate_observation_times(
        profile, dataset, time_model::parse_timestamp("2026-08-06T04:00:00Z"));
    }
  catch (const std::runtime_error& error)
    {
      stale_rejected = std::string_view(error.what()).find("stale")
        != std::string_view::npos;
    }
  assert(stale_rejected);

  assert(setenv("SOURCE_DATE_EPOCH", "1785902400", 1) == 0);
  const time_model::instant injected = time_model::process_start_instant();
  assert(injected.iso_utc == "2026-08-05T04:00:00Z");
  assert(unsetenv("SOURCE_DATE_EPOCH") == 0);
  const solar::geographic_position subsolar = solar::subsolar_position(injected);
  assert(near(subsolar.latitude_deg, 17.077346, 1e-5));
  assert(near(subsolar.longitude_deg_east, 121.145915, 1e-5));
  assert(solar::classify_illumination(solar::solar_altitude_degrees(
           subsolar, subsolar.latitude_deg, subsolar.longitude_deg_east))
         == solar::illumination_zone::day);
  assert(solar::classify_illumination(-18.01)
         == solar::illumination_zone::night);
  const auto horizon = atmosphere::solar_altitude_contour(subsolar, 0.0, 1.0);
  assert(horizon.size() == 360);
  for (std::size_t index = 0; index < horizon.size(); index += 37)
    assert(near(solar::solar_altitude_degrees(
                  subsolar, horizon[index].latitude, horizon[index].longitude),
                0.0, 1e-9));

  // Astro and atmosphere use exactly one shared solar ephemeris.
  const astro::profile astro_profile = astro::load_profile(
    "assets.static/astronomy/astro-profile.json");
  const solar::equatorial_position shared_sun
    = solar::sun_equatorial_position(astro_profile.calculation_time.julian_date);
  const std::vector<astro::sky_object> solar_system
    = astro::make_solar_system(astro_profile);
  const auto sun = std::find_if(
    solar_system.begin(), solar_system.end(),
    [](const astro::sky_object& object) { return object.id == "sun"; });
  assert(sun != solar_system.end());
  assert(near(sun->ra_deg, shared_sun.right_ascension_deg, 1e-12));
  assert(near(sun->dec_deg, shared_sun.declination_deg, 1e-12));

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-cloud-atmosphere-" + std::string(name));
      const auto solar_segments = atmosphere::project_solar_contour(
        context, horizon);
      assert(!solar_segments.empty());
      for (const auto& segment : solar_segments)
        for (const auto& point : segment)
          {
            assert(std::isfinite(std::get<0>(point)));
            assert(std::isfinite(std::get<1>(point)));
          }
      for (const atmosphere::atmosphere_cell& cell : dataset.cells)
        {
          const std::vector<generation::geographic_point> boundary
            = atmosphere::h3_polygon(cell.h3);
          assert(boundary.size() >= 5);
          const auto projected = generation::project_path(
            context, boundary, true);
          assert(!projected.empty());
          for (const auto& segment : projected)
            for (const auto& point : segment)
              {
                assert(std::isfinite(std::get<0>(point)));
                assert(std::isfinite(std::get<1>(point)));
              }
        }
    }

  const generation::projection_spec& ck
    = generation::find_projection_spec("cahill-keyes");
  const std::string metadata = atmosphere::metadata_element(
    ck, profile, dataset, injected, subsolar);
  assert(metadata.find("data-process-start-utc=\"2026-08-05T04:00:00Z\"")
         != std::string::npos);
  assert(metadata.find(
           "data-source-selection-process-start-utc=\"2026-08-05T04:00:00Z\"")
         != std::string::npos);
  assert(metadata.find("data-aod-is-smoke=\"false\"")
         != std::string::npos);
  assert(metadata.find("data-precipitation-is-event-count=\"false\"")
         != std::string::npos);
  assert(metadata.find("celestial-reference") == std::string::npos);
}
