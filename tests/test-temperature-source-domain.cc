// Verify compact storage retains the exact existing statistical field and
// rejects a source-center domain containing an unrelated or missing H3 cell.
#include <cassert>
#include <fstream>
#include <unordered_set>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>
#include "anthropocene-temperature-data.h"

namespace temperature = cart0freak0::anthropocene_temperature_generation;
namespace fs = std::filesystem;

int main(int argc, char** argv)
{
  assert(argc == 2);
  const fs::path scratch = argv[1]; fs::create_directories(scratch);
  const fs::path source = "assets.static/anthropocene/anthropocene-temperature-2026.geojson";
  auto profile = temperature::load_temperature_profile(
    "assets.static/anthropocene/anthropocene-temperature-2026-profile.json");
  const auto original = temperature::load_temperature_dataset(source, profile);
  for (const int resolution : {3, 5, 8})
    {
      const auto grid = temperature::cpc_grid_h3(resolution);
      const auto domain = temperature::cpc_source_cell_domain(resolution);
      assert(grid.size() == 259200);
      assert(domain.size() <= grid.size() && std::is_sorted(domain.begin(), domain.end()));
      assert(std::adjacent_find(domain.begin(), domain.end()) == domain.end());
      for (const auto cell : grid)
        {
          assert(getResolution(cell) == resolution && isValidCell(cell));
          assert(std::binary_search(domain.begin(), domain.end(), cell));
        }
    }
  const auto domain = temperature::cpc_source_cell_domain(3);
  const std::unordered_set<H3Index> included(domain.begin(), domain.end());
  auto doc = temperature::read_temperature_json(source, 128U * 1024U * 1024U);
  auto& allocator = doc.GetAllocator();
  rapidjson::Value features(rapidjson::kArrayType);
  for (auto& feature : doc["features"].GetArray())
    {
      const auto cell = temperature::temperature_h3(feature["id"].GetString(), "fixture");
      if (included.contains(cell)) features.PushBack(feature, allocator);
      else
        {
          assert(feature["properties"]["cpc_tmax_valid_days"].GetUint64() == 0);
          assert(feature["properties"]["cpc_tmin_valid_days"].GetUint64() == 0);
        }
    }
  doc["features"] = std::move(features);
  doc["metadata"]["feature_count"].SetUint64(domain.size());
  doc["metadata"].AddMember("cell_domain", "source-grid-centers", allocator);
  doc["metadata"].AddMember("unstored_cell_semantics",
    "No source-grid center; unobserved, not zero. Source pixel footprints are not filled.", allocator);
  const auto target = scratch / source.filename();
  const auto save = [&] {
    std::ofstream stream(target); rapidjson::OStreamWrapper wrapper(stream);
    rapidjson::Writer<rapidjson::OStreamWrapper> writer(wrapper); doc.Accept(writer);
  };
  save();
  profile.cell_domain = "source-grid-centers";
  const auto compact = temperature::load_temperature_dataset(target, profile);
  assert(compact.cells.size() == domain.size());
  assert(compact.covered_cell_count == original.covered_cell_count);
  assert(compact.totals.record_high_days == original.totals.record_high_days);
  assert(compact.totals.record_low_days == original.totals.record_low_days);
  for (const auto& cell : compact.cells)
    {
      const auto found = std::lower_bound(original.cells.begin(), original.cells.end(), cell.h3,
        [](const auto& item, const H3Index key) { return item.h3 < key; });
      assert(found != original.cells.end() && found->h3 == cell.h3);
      assert(cell.record_high_days == found->record_high_days && cell.record_low_days == found->record_low_days);
      assert(cell.tmax_valid_days == found->tmax_valid_days && cell.tmin_valid_days == found->tmin_valid_days);
    }
  const auto rejects = [&] {
    try { static_cast<void>(temperature::load_temperature_dataset(target, profile)); }
    catch (const std::runtime_error&) { return true; }
    return false;
  };
  profile.cell_domain = "global";
  assert(rejects());
  profile.cell_domain = "source-grid-centers";
  doc["metadata"]["h3_resolution"].SetUint(8); save(); assert(rejects());
  doc["metadata"]["h3_resolution"].SetUint(3);
  doc["features"].PopBack(); doc["metadata"]["feature_count"].SetUint64(domain.size()-1);
  save(); assert(rejects());
  fs::remove(target);
}
