#include <algorithm>
#include <cassert>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "generation-profile.h"

namespace generation = cart0freak0::generation_profile;

namespace {

void
expect_invalid(const std::string_view json, const std::string_view message)
{
  bool rejected = false;
  try
    {
      static_cast<void>(generation::parse_json(json, "test profile"));
    }
  catch (const std::runtime_error& error)
    {
      rejected = true;
      assert(std::string_view(error.what()).find(message)
             != std::string_view::npos);
    }
  assert(rejected);
}

} // namespace

int
main()
{
  const generation::profile configured = generation::load(
    "generation-profile.json");
  assert(configured.schema_version == 1);
  assert(!configured.projections.empty());
  assert(!configured.passes.empty());
  const std::vector<std::string> configured_targets
    = generation::targets(configured);
  assert(configured_targets.size()
         == configured.projections.size() * configured.passes.size());
  for (const std::string& target : configured_targets)
    {
      assert(target.starts_with("generate-"));
      assert(target.find_first_of(" \t\r\n") == std::string::npos);
    }

  const generation::profile development = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["cahill_keyes"],
      "passes": ["earth", "ocean"]
    }
  )json");
  assert((development.projections == std::vector<std::string> {
                                       "cahill-keyes"}));
  assert((development.passes == std::vector<std::string> {"earth", "water"}));
  assert((generation::targets(development) == std::vector<std::string> {
            "generate-earth-cahill-keyes", "generate-water-cahill-keyes"}));

  const generation::profile everything = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["all"],
      "passes": ["all"]
    }
  )json");
  const std::vector<std::string> all_targets = generation::targets(everything);
  assert(everything.all_projections);
  assert(everything.all_passes);
  assert(all_targets.size() == 102);
  assert(all_targets.front() == "generate-geometry-cahill-keyes");
  assert(all_targets.back() == "generate-cloud-atmosphere-voronoi");
  std::vector<std::string> unique_targets = all_targets;
  std::sort(unique_targets.begin(), unique_targets.end());
  assert(std::adjacent_find(unique_targets.begin(), unique_targets.end())
         == unique_targets.end());

  const generation::profile aliases = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "description": "Alias coverage",
      "projections": ["STAR_X", "voroni", "ck"],
      "passes": ["graticule", "astro", "orbiting", "swarm",
                 "bathymetry_rolette", "infrastructure", "anthropocene",
                 "resources", "solar/cloud/atmosphere"]
    }
  )json");
  assert((aliases.projections == std::vector<std::string> {
                                   "star-x", "voronoi", "cahill-keyes"}));
  assert((aliases.passes == std::vector<std::string> {
                              "graticules", "astronomy",
                              "orbital-technosphere", "network-swarm",
                              "bathymetry-roulette",
                              "network-infrastructure", "anthropocene",
                              "resources-energy", "resources-food",
                              "resources-fauna", "resources-flora", "resources-mineral",
                              "resources-human", "cloud-atmosphere"}));
  const std::vector<std::string> alias_targets = generation::targets(aliases);
  assert(alias_targets.front() == "generate-graticules-star-x");
  assert(std::find(alias_targets.begin(), alias_targets.end(),
                   "generate-network-swarm-star-x")
         != alias_targets.end());
  assert(std::find(alias_targets.begin(), alias_targets.end(),
                   "generate-network-infrastructure-star-x")
         != alias_targets.end());
  assert(std::find(alias_targets.begin(), alias_targets.end(),
                   "generate-anthropocene-star-x")
         != alias_targets.end());
  assert(std::find(alias_targets.begin(), alias_targets.end(),
                   "generate-resources-energy-star-x")
         != alias_targets.end());
  assert(std::find(alias_targets.begin(), alias_targets.end(),
                   "generate-cloud-atmosphere-star-x")
         != alias_targets.end());

  const generation::profile atmosphere_aliases = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["ck"],
      "passes": ["clouds"]
    }
  )json");
  assert((atmosphere_aliases.passes == std::vector<std::string> {
                                           "cloud-atmosphere"}));
  assert((generation::targets(atmosphere_aliases)
          == std::vector<std::string> {
               "generate-cloud-atmosphere-cahill-keyes"}));

  const generation::profile resource_aliases = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["ck"],
      "passes": ["resouces"]
    }
  )json");
  assert((resource_aliases.passes == std::vector<std::string> {
                                           "resources-energy",
                                           "resources-food",
                                           "resources-fauna",
                                           "resources-flora",
                                           "resources-mineral",
                                           "resources-human"}));
  assert((generation::targets(resource_aliases)
          == std::vector<std::string> {
               "generate-resources-energy-cahill-keyes",
               "generate-resources-food-cahill-keyes",
               "generate-resources-fauna-cahill-keyes",
               "generate-resources-flora-cahill-keyes",
               "generate-resources-mineral-cahill-keyes",
               "generate-resources-human-cahill-keyes"}));

  const generation::profile resource_family_aliases
    = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["ck"],
      "passes": ["energy", "reefs", "ressources-flora", "minerals", "human"]
    }
  )json");
  assert((resource_family_aliases.passes == std::vector<std::string> {
                                                "resources-energy",
                                                "resources-fauna",
                                                "resources-flora",
                                                "resources-mineral",
                                                "resources-human"}));
  assert((generation::targets(resource_family_aliases)
          == std::vector<std::string> {
               "generate-resources-energy-cahill-keyes",
               "generate-resources-fauna-cahill-keyes",
               "generate-resources-flora-cahill-keyes",
               "generate-resources-mineral-cahill-keyes",
               "generate-resources-human-cahill-keyes"}));

  const generation::profile legacy_network = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["ck"],
      "passes": ["network"]
    }
  )json");
  assert((legacy_network.passes == std::vector<std::string> {
                                     "network-swarm"}));
  assert((generation::targets(legacy_network) == std::vector<std::string> {
            "generate-network-swarm-cahill-keyes"}));

  const generation::profile historical = generation::parse_json(R"json(
    {
      "schema_version": 1,
      "projections": ["ck"],
      "passes": ["art-agua-roulette"]
    }
  )json");
  assert((historical.passes == std::vector<std::string> {
                                  "bathymetry-roulette"}));
  assert((generation::targets(historical) == std::vector<std::string> {
            "generate-bathymetry-roulette-cahill-keyes"}));

  expect_invalid(R"json({
    "schema_version": 1,
    "projections": ["all", "voronoi"],
    "passes": ["earth"]
  })json", "sole value");
  expect_invalid(R"json({
    "schema_version": 1,
    "projections": ["cahill-keyes"],
    "passes": ["water", "ocean"]
  })json", "duplicate selection 'water'");
  expect_invalid(R"json({
    "schema_version": 1,
    "projections": ["mercator"],
    "passes": ["earth"]
  })json", "unknown value 'mercator'");
  expect_invalid(R"json({
    "schema_version": 1,
    "projections": [],
    "passes": ["earth"]
  })json", "must not be empty");
  expect_invalid(R"json({
    "schema_version": 2,
    "projections": ["all"],
    "passes": ["all"]
  })json", "unsupported generation profile schema");
  expect_invalid(R"json({
    "schema_version": 1,
    "projection": ["all"],
    "projections": ["all"],
    "passes": ["all"]
  })json", "unknown member 'projection'");
  expect_invalid(R"json({
    "schema_version": 1,
    "projections": ["cahill-keyes"],
    "projections": ["voronoi"],
    "passes": ["earth"]
  })json", "duplicate member 'projections'");
  expect_invalid(R"json({
    "schema_version": 1,
    "projections": ["cahill-keyes"],
    "passes": ["world-game"]
  })json", "unknown value 'world-game'");
}
