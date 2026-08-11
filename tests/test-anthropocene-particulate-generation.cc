#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <string>
#include <string_view>
#include <vector>

#include "anthropocene-particulate-generation.h"

namespace anthropocene = cart0freak0::anthropocene_generation;
namespace generation = cart0freak0::generation;

int
main()
{
  const anthropocene::anthropocene_profile profile_2025
    = anthropocene::load_anthropocene_profile(
      "assets.static/anthropocene/anthropocene-particulate-2025-profile.json");
  const anthropocene::anthropocene_profile profile
    = anthropocene::load_anthropocene_profile(
      "assets.static/anthropocene/anthropocene-particulate-2026-profile.json");
  assert(profile_2025.calendar_year == 2025);
  assert(!profile_2025.partial_year);
  assert(profile_2025.snapshot_as_of_utc == "2026-08-10T00:00:00Z");
  assert(profile_2025.geojson_sha256
         == "ecd4b11bab4faa9895522dbfe75436ef66820f53620bf0c5f6fc7404e9f5426b");
  assert(profile.calendar_year == 2026);
  assert(profile.partial_year);
  assert(profile.snapshot_as_of_utc == "2026-08-05T00:00:00Z");
  assert(profile.h3_resolution == 4);
  assert(profile.minimum_record_years == 30);
  assert(profile.minimum_valid_days_per_year == 183);
  assert(profile.baseline_start == 1991);
  assert(profile.baseline_end == 2020);
  assert(profile.pm25_aqi_threshold_exclusive == 100);
  assert(profile.metrics.size() == 9);
  assert(profile.geojson_sha256
         == "a3b2fcb3a809710d278ce88aef52ea938fa67e8b900313cf2e5c2ed9c6ddde42");

  const std::size_t pm25 = anthropocene::metric_index(
    profile, "air-quality-exposure:pm25-exceedance-days");
  const std::size_t smoke = anthropocene::metric_index(
    profile, "atmosphere:observed-smoke-days");
  assert(pm25 != smoke);
  assert(profile.metrics[pm25].enabled);
  assert(profile.metrics[pm25].family == "air-quality-exposure");
  assert(profile.metrics[pm25].property == "pm25_exceedance_days");
  assert(profile.metrics[pm25].shape == anthropocene::marker_shape::cross_square);
  assert((profile.metrics[pm25].sources
          == std::vector<std::string> {"epa-airdata-pm25"}));
  assert(profile.metrics[smoke].family == "atmosphere");
  assert(profile.metrics[smoke].shape == anthropocene::marker_shape::ring);
  assert((profile.metrics[smoke].sources
          == std::vector<std::string> {"noaa-hms-smoke"}));

  const auto source = [&](const std::string_view id)
    -> const anthropocene::source_definition& {
    const auto found = std::find_if(
      profile.sources.begin(), profile.sources.end(), [&](const auto& item) {
        return item.id == id;
      });
    assert(found != profile.sources.end());
    return *found;
  };
  assert(source("cwfis-hotspots").status == "included");
  assert(source("nasa-firms").status == "configured-optional");
  assert(source("copernicus-sentinel-3-frp").status == "validation-only");
  assert(source("rosleskhoz-operational-reports").status == "validation-only");
  assert(source("purpleair").status == "excluded-from-standard");

  assert(profile.future_phases.size() == 1);
  assert(profile.future_phases.front().id
         == "ocean-heat:coral-bleaching-stress-days");
  assert(profile.future_phases.front().status == "separate-phase");
  assert(std::none_of(profile.metrics.begin(), profile.metrics.end(),
                      [](const auto& item) {
                        return item.id.find("coral") != std::string::npos;
                      }));

  const anthropocene::anthropocene_dataset dataset
    = anthropocene::load_anthropocene_dataset(
      "assets.static/anthropocene/anthropocene-particulate-2026.geojson", profile);
  const anthropocene::anthropocene_dataset dataset_2025
    = anthropocene::load_anthropocene_dataset(
      "assets.static/anthropocene/anthropocene-particulate-2025.geojson",
      profile_2025);
  assert(dataset_2025.calendar_year == 2025);
  assert(!dataset_2025.partial_year);
  assert(dataset_2025.features.size() == 49470);
  assert(dataset_2025.statistics.ghcn_stations == 996);
  assert(dataset_2025.statistics.ghcn_eligible_temperature_stations == 760);
  assert(dataset_2025.statistics.ghcn_eligible_precipitation_stations == 649);
  assert(dataset_2025.statistics.epa_rows == 758834);
  assert(dataset_2025.statistics.hms_polygons == 24238);
  assert(dataset_2025.statistics.storm_events == 72360);
  assert(dataset_2025.statistics.cwfis_files == 1);
  assert(dataset_2025.statistics.cwfis_rows == 2616235);
  assert(dataset_2025.statistics.firms_rows == 0);
  assert(dataset_2025.reported_metric_totals[anthropocene::metric_index(
    profile_2025, "climate-records:temperature-record-high-days")] == 4129);
  assert(dataset_2025.reported_metric_totals[anthropocene::metric_index(
    profile_2025, "atmosphere:observed-smoke-days")] == 1794158);
  assert(dataset_2025.reported_metric_totals[anthropocene::metric_index(
    profile_2025, "fire:active-fire-days")] == 127392);
  assert(dataset.schema == "cartofreako-anthropocene-observations-v1");
  assert(dataset.calendar_year == 2026);
  assert(dataset.partial_year);
  assert(dataset.h3_resolution == 4);
  assert(dataset.features.size() == 43895);
  assert(dataset.statistics.ghcn_stations == 996);
  assert(dataset.statistics.ghcn_eligible_temperature_stations == 768);
  assert(dataset.statistics.ghcn_eligible_precipitation_stations == 652);
  assert(dataset.statistics.epa_rows == 177365);
  assert(dataset.statistics.epa_exceedance_site_days == 164);
  assert(dataset.statistics.hms_polygons == 29813);
  assert(dataset.statistics.storm_events == 23255);
  assert(dataset.statistics.cwfis_files == 167);
  assert(dataset.statistics.firms_rows == 0);
  assert(dataset.reported_metric_totals[pm25] == 129);
  assert(dataset.reported_metric_feature_counts[pm25] == 67);
  assert(dataset.reported_metric_totals[smoke] == 1088261);
  assert(dataset.reported_metric_feature_counts[smoke] == 43690);
  assert(dataset.reported_metric_totals[anthropocene::metric_index(
    profile, "climate-records:temperature-record-high-days")] == 1567);
  assert(dataset.reported_metric_totals[anthropocene::metric_index(
    profile, "fire:active-fire-days")] == 35940);

  std::vector<std::uint64_t> totals(profile.metrics.size());
  for (const anthropocene::anthropocene_feature& feature : dataset.features)
    {
      assert(feature.counts.size() == profile.metrics.size());
      for (std::size_t index = 0; index < feature.counts.size(); ++index)
        totals[index] += feature.counts[index];
    }
  assert(totals == dataset.reported_metric_totals);

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-anthropocene-particulate-" + std::string(name));
      assert(anthropocene::output_basename(spec, profile_2025).find(
        "anthropocene-particulate-2025-") == 0);
      assert(anthropocene::output_basename(spec, profile).find(
        "anthropocene-particulate-2026-") == 0);
      for (std::size_t index = 0; index < dataset.features.size(); index += 97)
        {
          const anthropocene::anthropocene_feature& feature
            = dataset.features[index];
          const auto [x, y] = generation::project_point(
            context, {feature.latitude, feature.longitude});
          assert(std::isfinite(x) && std::isfinite(y));
          assert(x >= 0 && x <= context.map_frame.width());
          assert(y >= 0 && y <= context.map_frame.height());
        }
    }

  assert(anthropocene::scaled_opacity(0, profile.metrics[pm25], profile) == 0);
  assert(anthropocene::scaled_opacity(1, profile.metrics[pm25], profile)
         > profile.minimum_nonzero_opacity);
  assert(anthropocene::scaled_opacity(1000, profile.metrics[pm25], profile)
         == 1);
}
