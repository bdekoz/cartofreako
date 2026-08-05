#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>

#include "resources-generation.h"

namespace resources = cart0freak0::resources_generation;
namespace generation = cart0freak0::generation;

namespace {

std::string
read_file(const std::filesystem::path& path)
{
  std::ifstream input {path, std::ios::binary};
  assert(input.good());
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void
replace_once(std::string& value, const std::string_view before,
             const std::string_view after)
{
  const std::size_t position = value.find(before);
  assert(position != std::string::npos);
  value.replace(position, before.size(), after);
}

void
expect_invalid(std::string json, const std::string_view message)
{
  static unsigned sequence = 0;
  const std::filesystem::path path = std::filesystem::temp_directory_path()
    / ("cartofreako-invalid-resources-" + std::to_string(++sequence)
       + ".json");
  {
    std::ofstream output {path, std::ios::binary};
    assert(output.good());
    output << json;
  }
  bool rejected = false;
  try
    {
      static_cast<void>(resources::load_resources_profile(path));
    }
  catch (const std::runtime_error& error)
    {
      rejected = true;
      assert(std::string_view(error.what()).find(message)
             != std::string_view::npos);
    }
  std::filesystem::remove(path);
  assert(rejected);
}

} // namespace

int
main()
{
  const std::filesystem::path profile_path
    = "assets.static/resources/resources-profile.json";
  const resources::resources_profile profile
    = resources::load_resources_profile(profile_path);
  assert(profile.name == "World Game resources / 1960 production leaders");
  assert(profile.publication_year == 1963);
  assert(profile.production_year == 1960);
  assert(profile.historical.size() == 40);
  assert(profile.modern.size() == 4);
  assert(profile.source_pdf_sha256
         == "11f0a4f7617a34b58bf620bba62ddbfe01a6389dffc348e95142b86db964f816");
  assert(profile.historical.front().id == "aluminum");
  assert(profile.historical.front().world_total == 6080000);
  assert(profile.historical.front().leader.has_value());
  assert(std::abs(profile.historical.front().leader->share_percent - 38.035)
         < 1e-12);
  assert(profile.historical.back().id == "zinc");
  const resources::historical_resource& thorium = profile.historical[33];
  assert(thorium.id == "thorium");
  assert(!thorium.world_total.has_value());
  assert(!thorium.leader.has_value());
  assert(!thorium.leader_pdf_page.has_value());
  assert(thorium.source_unit == "N.A.");
  assert(profile.modern.front().id == "capture-fisheries");
  assert(!profile.modern.front().leader.has_value());
  assert(profile.modern.back().id == "installed-solar-capacity");
  assert(profile.modern.back().reference_year == 2025);
  assert(profile.modern.back().world_total == 2391584);
  assert(profile.modern.back().leader.has_value());
  assert(std::abs(profile.modern.back().leader->share_percent - 50.267)
         < 1e-12);

  assert(std::count_if(profile.historical.begin(), profile.historical.end(),
    [](const auto& record) { return record.leader.has_value(); }) == 39);
  assert(std::count_if(profile.modern.begin(), profile.modern.end(),
    [](const auto& record) { return record.leader.has_value(); }) == 2);
  for (const resources::resource_category category : {
         resources::resource_category::metals,
         resources::resource_category::industrial_materials,
         resources::resource_category::energy_feedstocks})
    assert(std::any_of(profile.historical.begin(), profile.historical.end(),
      [category](const auto& record) { return record.category == category; }));

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-resources-" + std::string(name));
      const resources::resources_layout layout
        = resources::layout_resource_points(context, profile);
      assert(layout.historical.size() == profile.historical.size());
      assert(layout.modern.size() == profile.modern.size());
      assert(std::count_if(layout.historical.begin(), layout.historical.end(),
        [](const auto& point) { return point.has_value(); }) == 39);
      assert(std::count_if(layout.modern.begin(), layout.modern.end(),
        [](const auto& point) { return point.has_value(); }) == 2);
      const auto check_point = [&](const auto& optional_point) {
        if (!optional_point.has_value())
          return;
        const auto [x, y] = optional_point->display;
        assert(std::isfinite(x) && std::isfinite(y));
        assert(x >= 0 && x <= context.map_frame.width());
        assert(y >= 0 && y <= context.map_frame.height());
      };
      std::for_each(layout.historical.begin(), layout.historical.end(),
                    check_point);
      std::for_each(layout.modern.begin(), layout.modern.end(), check_point);
      assert(resources::resources_output_basename(spec).starts_with(
        "resources-"));
      const std::string metadata
        = resources::resources_metadata_element(spec, profile);
      assert(resources::resources_token_count(
        metadata, "data-resource-catalog-record=\"true\"") == 40);
      assert(resources::resources_token_count(
        metadata, "data-modern-context-catalog-record=\"true\"") == 4);
    }

  const std::string valid_json = read_file(profile_path);
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"name\":", "\"name\": \"duplicate\", \"name\":");
    expect_invalid(std::move(invalid), "duplicate member 'name'");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"marker_radius\": 0.115",
                 "\"marker_radius\": 0.115, \"unknown\": true");
    expect_invalid(std::move(invalid), "unknown member 'unknown'");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"record_count\": 40", "\"record_count\": 39");
    expect_invalid(std::move(invalid), "required 40 records");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"share_percent\": 38.035",
                 "\"share_percent\": 0.0");
    expect_invalid(std::move(invalid), "must be in (0, 100]");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"world_total\": null, \"source_unit\": \"N.A.\"",
                 "\"world_total\": 1, \"source_unit\": \"N.A.\"");
    expect_invalid(std::move(invalid), "world_total and leader availability differ");
  }
}
