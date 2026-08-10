#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

#include "anthropocene-temperature-generation.h"

namespace temperature
  = cart0freak0::anthropocene_temperature_generation;
namespace generation = cart0freak0::generation;

namespace {

struct region
{
  std::string_view name;
  double minimum_longitude;
  double maximum_longitude;
  double minimum_latitude;
  double maximum_latitude;
};

std::size_t
covered_in(const temperature::temperature_dataset& dataset,
           const region& bounds)
{
  std::size_t result = 0;
  for (const temperature::temperature_cell& cell : dataset.cells)
    if (cell.longitude >= bounds.minimum_longitude
        && cell.longitude <= bounds.maximum_longitude
        && cell.latitude >= bounds.minimum_latitude
        && cell.latitude <= bounds.maximum_latitude
        && (cell.tmax_valid_days != 0 || cell.tmin_valid_days != 0))
      ++result;
  return result;
}

} // namespace

int
main()
{
  const temperature::temperature_profile profile_2025
    = temperature::load_temperature_profile(
      "assets.static/anthropocene/anthropocene-temperature-2025-profile.json");
  const temperature::temperature_profile profile_2026
    = temperature::load_temperature_profile(
      "assets.static/anthropocene/anthropocene-temperature-2026-profile.json");
  assert(profile_2025.calendar_year == 2025);
  assert(!profile_2025.partial_year);
  assert(profile_2025.data_through == "2025-12-31");
  assert(profile_2025.baseline_start == 1979);
  assert(profile_2025.baseline_end == 2024);
  assert(profile_2026.calendar_year == 2026);
  assert(profile_2026.partial_year);
  assert(profile_2026.data_through == "2026-08-04");
  assert(profile_2026.baseline_start == 1979);
  assert(profile_2026.baseline_end == 2025);
  assert(profile_2025.h3_resolution == 3);
  assert(profile_2026.h3_resolution == 3);
  assert(profile_2025.high_scale_days == 32);
  assert(profile_2025.low_scale_days == 16);
  assert(profile_2026.high_scale_days == 32);
  assert(profile_2026.low_scale_days == 16);
  assert(profile_2025.data_graphic_opacity == 0.60);
  assert(profile_2026.data_graphic_opacity == 0.60);
  assert(profile_2025.source_manifest_sha256
         == profile_2026.source_manifest_sha256);

  const temperature::temperature_dataset dataset_2025
    = temperature::load_temperature_dataset(
      "assets.static/anthropocene/anthropocene-temperature-2025.geojson",
      profile_2025);
  const temperature::temperature_dataset dataset_2026
    = temperature::load_temperature_dataset(
      "assets.static/anthropocene/anthropocene-temperature-2026.geojson",
      profile_2026);
  assert(dataset_2025.cells.size() == 41162);
  assert(dataset_2026.cells.size() == 41162);
  assert(dataset_2025.covered_cell_count > 10000);
  assert(dataset_2026.covered_cell_count > 10000);
  assert(dataset_2025.totals.tmax_valid_days > 0);
  assert(dataset_2025.totals.tmin_valid_days > 0);
  assert(dataset_2026.totals.tmax_valid_days > 0);
  assert(dataset_2026.totals.tmin_valid_days > 0);
  assert(dataset_2025.totals.record_high_days > 0);
  assert(dataset_2025.totals.record_low_days > 0);
  assert(dataset_2026.totals.record_high_days > 0);
  assert(dataset_2026.totals.record_low_days > 0);

  bool found_covered_zero = false;
  bool found_missing = false;
  bool found_complete_2025 = false;
  bool found_complete_2026 = false;
  for (const temperature::temperature_cell& cell : dataset_2025.cells)
    {
      assert(cell.record_high_days <= cell.tmax_valid_days);
      assert(cell.record_low_days <= cell.tmin_valid_days);
      found_covered_zero = found_covered_zero
        || ((cell.tmax_valid_days != 0 || cell.tmin_valid_days != 0)
            && cell.record_high_days == 0 && cell.record_low_days == 0);
      found_missing = found_missing
        || (cell.tmax_valid_days == 0 && cell.tmin_valid_days == 0);
      found_complete_2025 = found_complete_2025
        || (cell.tmax_valid_days == 365 && cell.tmin_valid_days == 365);
    }
  for (const temperature::temperature_cell& cell : dataset_2026.cells)
    {
      assert(cell.record_high_days <= cell.tmax_valid_days);
      assert(cell.record_low_days <= cell.tmin_valid_days);
      found_complete_2026 = found_complete_2026
        || (cell.tmax_valid_days == 216 && cell.tmin_valid_days == 216);
    }
  assert(found_covered_zero);
  assert(found_missing);
  assert(found_complete_2025);
  assert(found_complete_2026);

  constexpr std::array regions {
    region {"Europe", -10, 40, 35, 70},
    region {"Siberia", 60, 180, 50, 75},
    region {"China and Japan", 100, 150, 20, 50},
    region {"Australia", 110, 155, -45, -10},
    region {"Africa", -20, 55, -35, 37},
    region {"South America", -82, -35, -56, 13},
  };
  for (const region& bounds : regions)
    {
      static_cast<void>(bounds.name);
      assert(covered_in(dataset_2025, bounds) > 100);
      assert(covered_in(dataset_2026, bounds) > 100);
    }

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  const H3Index antimeridian_cell = temperature::temperature_h3(
    "830d86fffffffff", "antimeridian test cell");
  const auto antimeridian_polygons
    = temperature::temperature_h3_polygons(antimeridian_cell);
  assert(antimeridian_polygons.size() == 2);
  for (const auto& polygon : antimeridian_polygons)
    for (const generation::geographic_point point : polygon)
      assert(point.longitude >= -180 && point.longitude <= 180);
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-anthropocene-temperature-" + std::string(name));
      for (std::size_t index = 0; index < dataset_2025.cells.size();
           index += 193)
        {
          const temperature::temperature_cell& cell
            = dataset_2025.cells[index];
          const auto [x, y] = generation::project_point(
            context, {cell.latitude, cell.longitude});
          assert(std::isfinite(x) && std::isfinite(y));
          assert(x >= 0 && x <= context.map_frame.width());
          assert(y >= 0 && y <= context.map_frame.height());
        }
      std::string antimeridian_path;
      temperature::append_temperature_polygon(
        antimeridian_path, context, antimeridian_cell);
      assert(!antimeridian_path.empty());
    }

  assert(temperature::temperature_bin(1, 32) == 0);
  assert(temperature::temperature_bin(32, 32) == 5);
  assert(temperature::temperature_bin(1000, 32) == 5);
}
