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

#include "anthropocene-generation.h"

namespace anthropocene = cart0freak0::anthropocene_generation;
namespace generation = cart0freak0::generation;

int
main()
{
  const anthropocene::anthropocene_profile profile
    = anthropocene::load_anthropocene_profile(
      "assets.static/anthropocene/anthropocene-profile.json");
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
  assert(source("purpleair").status == "excluded-from-default");

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
      "assets.static/anthropocene/anthropocene-2026.geojson", profile);
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
        spec, "test-anthropocene-" + std::string(name));
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
