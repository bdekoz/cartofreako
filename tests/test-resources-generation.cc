#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

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
  replace_once(
    json, "\"path\": \"countries-110m.geojson\"",
    "\"path\": \""
      + std::filesystem::absolute(
          "assets.static/resources/countries-110m.geojson").string()
      + "\"");
  replace_once(
    json, "\"path\": \"resources-values.json\"",
    "\"path\": \""
      + std::filesystem::absolute(
          "assets.static/resources/resources-values.json").string()
      + "\"");
  const std::filesystem::path path = std::filesystem::temp_directory_path()
    / ("cartofreako-invalid-resources-v2-" + std::to_string(++sequence)
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

const resources::metric_definition&
find_metric(const resources::resource_family& family,
            const std::string_view id)
{
  const auto metric = std::find_if(family.metrics.begin(), family.metrics.end(),
    [&](const resources::metric_definition& candidate) {
      return candidate.id == id;
    });
  assert(metric != family.metrics.end());
  return *metric;
}

} // namespace

int
main()
{
  const std::filesystem::path profile_path
    = "assets.static/resources/resources-profile.json";
  const resources::resources_profile profile
    = resources::load_resources_profile(profile_path);
  assert(profile.name == "Resources Stage 6b current-source atlas");
  assert(profile.snapshot_as_of == "2026-08-06");
  assert(profile.families.size() == 5);
  assert(profile.values.size() == 856);
  assert(profile.name.find("1960") == std::string::npos);
  assert(profile.description.find("World Game") == std::string::npos);
  assert(std::filesystem::is_regular_file(profile.country_geometry_path));
  assert(std::filesystem::is_regular_file(profile.values_path));

  const std::array expected_families {
    std::pair {std::string_view {"resources-energy"}, std::size_t {169}},
    std::pair {std::string_view {"resources-food"}, std::size_t {168}},
    std::pair {std::string_view {"resources-flora"}, std::size_t {169}},
    std::pair {std::string_view {"resources-mineral"}, std::size_t {12}},
    std::pair {std::string_view {"resources-human"}, std::size_t {169}},
  };
  for (std::size_t index = 0; index != expected_families.size(); ++index)
    {
      const resources::resource_family& family = profile.families[index];
      assert(family.id == expected_families[index].first);
      const resources::metric_definition& metric
        = resources::default_resource_metric(family);
      assert(metric.status == resources::metric_status::default_metric);
      assert(metric.coverage.has_value());
      assert(metric.coverage->passes_non_sparse);
      assert(metric.coverage->covered_countries
             == expected_families[index].second);
      assert(metric.coverage->mapped_countries == 176);
      const auto values = resources::resource_metric_values(
        profile, family, metric);
      assert(values.size() == expected_families[index].second);
      assert(std::all_of(values.begin(), values.end(),
        [](const resources::country_value* value) {
          return resources::is_iso3(value->iso3)
                 && std::isfinite(value->value) && value->value >= 0;
        }));
    }

  const resources::resource_family& energy
    = resources::find_resource_family(profile, "energy");
  assert(resources::default_resource_metric(energy).id == "solar-capacity");
  assert(find_metric(energy, "wind-capacity").status
         == resources::metric_status::planned);
  assert(find_metric(energy, "nuclear-operating-capacity").title
         .find("nuclear") != std::string::npos);
  assert(find_metric(energy, "unconventional-gas-production").status
         == resources::metric_status::supplemental);

  const resources::resource_family& food
    = resources::find_resource_family(profile, "resources_food");
  assert(find_metric(food, "capture-fisheries").unit == "tonnes");
  assert(find_metric(food, "livestock-production").notes.find("counts")
         != std::string::npos);

  const resources::resource_family& flora
    = resources::find_resource_family(profile, "ressources-flora");
  assert(flora.id == "resources-flora");
  assert(find_metric(flora, "plant-biodiversity").status
         == resources::metric_status::supplemental);

  const resources::resource_family& mineral
    = resources::find_resource_family(profile, "minerals");
  assert(mineral.metrics.size() >= 20);
  assert(find_metric(mineral, "rare-earth-mine-production").reference_period
         == "2025 estimate");
  assert(find_metric(mineral, "uranium").status
         == resources::metric_status::planned);
  const auto mineral_values = resources::resource_metric_values(
    profile, mineral, resources::default_resource_metric(mineral));
  const auto china = std::find_if(mineral_values.begin(), mineral_values.end(),
    [](const resources::country_value* value) { return value->iso3 == "CHN"; });
  assert(china != mineral_values.end() && (*china)->value == 270000);
  assert(resources::default_resource_metric(mineral).coverage->output_percent
         > 99.0);

  const resources::resource_family& human
    = resources::find_resource_family(profile, "human");
  assert(resources::default_resource_metric(human).id == "population-under-30");
  assert(find_metric(human, "population-over-60").status
         == resources::metric_status::available);
  assert(resources::resource_metric_values(
    profile, human, find_metric(human, "population-over-60")).size() == 169);
  assert(find_metric(human, "books-read-median").status
         == resources::metric_status::research_gap);
  assert(find_metric(human, "consensual-same-sex-activity-law").notes
         .find("never label") != std::string::npos);
  assert(find_metric(human, "drug-possession-penalty").notes
         .find("substance") != std::string::npos);

  assert(resources::canonical_resource_family("resources").has_value() == false);
  assert(resources::canonical_resource_family("world-game").has_value() == false);
  assert(resources::canonical_resource_family("ressources_flora")
         == std::optional<std::string> {"resources-flora"});

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      for (const resources::resource_family& family : profile.families)
        {
          const resources::metric_definition& metric
            = resources::default_resource_metric(family);
          const std::string basename
            = resources::resources_output_basename(spec, family, metric);
          assert(basename.starts_with(family.id + "-"));
          assert(basename.ends_with(spec.output_tag));
        }
    }

  const resources::metric_definition& energy_metric
    = resources::default_resource_metric(energy);
  const auto energy_values = resources::resource_metric_values(
    profile, energy, energy_metric);
  const std::string metadata = resources::resources_metadata_element(
    generation::find_projection_spec("cahill-keyes"), profile, energy,
    energy_metric, energy_values);
  const std::size_t metric_count = std::accumulate(
    profile.families.begin(), profile.families.end(), std::size_t {0},
    [](const std::size_t count, const resources::resource_family& family) {
      return count + family.metrics.size();
    });
  assert(resources::resources_token_count(
    metadata, "data-resource-value-record=\"true\"") == energy_values.size());
  assert(resources::resources_token_count(
    metadata, "data-resource-metric-catalog=\"true\"") == metric_count);
  assert(metadata.find("Resources Stage 6b") != std::string::npos);
  assert(metadata.find("data-missing-is-zero=\"false\"")
         != std::string::npos);
  assert(metadata.find("1960") == std::string::npos);

  const std::string valid_json = read_file(profile_path);
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"name\":", "\"name\": \"duplicate\", \"name\":");
    expect_invalid(std::move(invalid), "duplicate member 'name'");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "cartofreako-resources-profile-v2",
                 "cartofreako-resources-profile-v1");
    expect_invalid(std::move(invalid), "unsupported resources profile schema");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"passes_non_sparse\": true",
                 "\"passes_non_sparse\": false");
    expect_invalid(std::move(invalid),
                   "non-sparse result disagrees with its percentages");
  }
  {
    std::string invalid = valid_json;
    replace_once(invalid, "\"resources-energy\"",
                 "\"resources-entropy\"");
    expect_invalid(std::move(invalid), "unknown family id");
  }
}
