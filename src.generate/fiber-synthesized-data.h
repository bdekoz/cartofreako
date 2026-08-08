// Validated cleaned-union submarine-fiber data.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_FIBER_SYNTHESIZED_DATA_H
#define CART0FREAK0_FIBER_SYNTHESIZED_DATA_H 1

#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "network-infrastructure-data.h"

namespace cart0freak0::fiber_synthesized_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;
namespace generation = cart0freak0::generation;
namespace infrastructure
  = cart0freak0::network_infrastructure_generation;

inline constexpr std::string_view fiber_schema
  = "cartofreako-fiber-synthesized-v1";
inline constexpr std::string_view fiber_kind
  = "cleaned-union-with-source-separated-observations";

struct fiber_profile
{
  fs::path directory;
  std::string default_snapshot;
  std::string older_snapshot;
  std::string source_repository;
  std::string source_commit;
  std::string source_license;
  std::string routes_sha256;
  std::string landings_sha256;
  std::size_t comparison_systems = 0;
  std::size_t expected_routes = 0;
  std::size_t expected_landings = 0;
  std::size_t expected_route_observations = 0;
  std::size_t expected_landing_observations = 0;
  std::size_t stable_id_matches = 0;
  std::size_t normalized_name_matches = 0;
  std::size_t landing_set_matches = 0;
  std::size_t unmatched_systems = 0;
};

struct fiber_route
{
  std::string cable_id;
  std::string name;
  std::string feature_id;
  std::string comparison_id;
  std::string source_snapshot;
  std::string snapshot_membership;
  std::string temporal_class;
  bool planned = false;
  std::vector<std::vector<generation::geographic_point>> paths;
};

struct fiber_landing
{
  std::string id;
  std::string name;
  std::string source_snapshot;
  std::string snapshot_membership;
  bool tbd = false;
  generation::geographic_point point {};
};

struct fiber_dataset
{
  fiber_profile profile;
  std::vector<fiber_route> routes;
  std::vector<fiber_landing> landings;
  std::size_t current_routes = 0;
  std::size_t historical_routes = 0;
  std::size_t planned_routes = 0;
  std::size_t planned_to_active_routes = 0;
  std::size_t current_only_routes = 0;
  std::size_t current_landings = 0;
  std::size_t historical_landings = 0;
};

inline std::size_t
manifest_size(const rj::Value& summary, const char* name,
              const std::string& context)
{
  return infrastructure::required_size(summary, name, context);
}

inline fiber_profile
load_fiber_profile(const fs::path& directory)
{
  const fs::path path = directory / "manifest.json";
  const rj::Document document = infrastructure::read_json_document(path);
  const std::string context = path.string();
  infrastructure::infrastructure_require(document.IsObject(),
    context + " root must be an object");
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "schema", context)
      == fiber_schema,
    context + " has an unsupported schema");
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "kind", context)
      == fiber_kind,
    context + " is not the cleaned-union dataset");

  fiber_profile result;
  result.directory = directory;
  result.default_snapshot = infrastructure::required_string(
    document, "default_snapshot", context);
  result.source_repository = infrastructure::required_string(
    document, "source_repository", context);
  result.source_commit = infrastructure::required_string(
    document, "source_checkout_head", context);
  result.source_license = infrastructure::required_string(
    document, "license", context);
  infrastructure::infrastructure_require(
    infrastructure::lower_hex(result.source_commit, 40),
    context + ".source_checkout_head must be a lowercase SHA-1");
  infrastructure::infrastructure_require(
    result.source_license.find("CC BY-NC-SA 3.0") != std::string::npos,
    context + " must retain the TeleGeography CC BY-NC-SA 3.0 license");

  const rj::Value& sources = infrastructure::required_member(
    document, "sources", context);
  infrastructure::infrastructure_require(
    sources.IsArray() && sources.Size() == 2,
    context + ".sources must contain exactly two snapshots");
  bool found_default = false;
  for (const rj::Value& source : sources.GetArray())
    {
      const std::string snapshot = infrastructure::required_string(
        source, "snapshot", context + ".sources[]");
      if (snapshot == result.default_snapshot)
        found_default = true;
      else
        {
          infrastructure::infrastructure_require(result.older_snapshot.empty(),
            context + " contains more than one non-default snapshot");
          result.older_snapshot = snapshot;
        }
    }
  infrastructure::infrastructure_require(found_default
    && !result.older_snapshot.empty(),
    context + " does not identify one default and one older snapshot");

  const rj::Value& summary = infrastructure::required_member(
    document, "summary", context);
  result.comparison_systems = manifest_size(
    summary, "comparison_systems", context + ".summary");
  result.expected_routes = manifest_size(
    summary, "cleaned_union_route_features", context + ".summary");
  result.expected_landings = manifest_size(
    summary, "cleaned_union_landing_features", context + ".summary");
  result.expected_route_observations = manifest_size(
    summary, "source_observation_route_features", context + ".summary");
  result.expected_landing_observations = manifest_size(
    summary, "source_observation_landing_features", context + ".summary");
  const rj::Value& match_classes = infrastructure::required_member(
    summary, "match_classes", context + ".summary");
  result.stable_id_matches = manifest_size(
    match_classes, "stable-id", context + ".summary.match_classes");
  result.normalized_name_matches = manifest_size(
    match_classes, "unique-normalized-name",
    context + ".summary.match_classes");
  result.landing_set_matches = manifest_size(
    match_classes, "unique-exact-landing-set",
    context + ".summary.match_classes");
  result.unmatched_systems = manifest_size(
    match_classes, "unmatched", context + ".summary.match_classes");
  infrastructure::infrastructure_require(
    result.stable_id_matches + result.normalized_name_matches
      + result.landing_set_matches + result.unmatched_systems
      == result.comparison_systems,
    context + ".summary match classes do not cover every comparison system");

  const rj::Value& outputs = infrastructure::required_member(
    document, "outputs", context);
  const rj::Value& routes = infrastructure::required_member(
    outputs, "routes.geojson", context + ".outputs");
  const rj::Value& landings = infrastructure::required_member(
    outputs, "landings.geojson", context + ".outputs");
  result.routes_sha256 = infrastructure::required_string(
    routes, "sha256", context + ".outputs.routes.geojson");
  result.landings_sha256 = infrastructure::required_string(
    landings, "sha256", context + ".outputs.landings.geojson");
  infrastructure::infrastructure_require(
    infrastructure::lower_hex(result.routes_sha256, 64)
      && infrastructure::lower_hex(result.landings_sha256, 64),
    context + " contains an invalid output digest");
  return result;
}

inline void
validate_union_document(const rj::Document& document,
                        const fiber_profile& profile,
                        const std::string& context)
{
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "type", context)
      == "FeatureCollection",
    context + ".type must be FeatureCollection");
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "schema", context)
      == fiber_schema,
    context + " has an unsupported schema");
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "kind", context)
      == "cleaned-union",
    context + " is not a cleaned union");
  infrastructure::infrastructure_require(
    infrastructure::required_string(document, "default_snapshot", context)
      == profile.default_snapshot,
    context + " disagrees with the manifest default snapshot");
}

inline std::vector<fiber_route>
load_fiber_routes(const fiber_profile& profile)
{
  const fs::path path = profile.directory / "routes.geojson";
  const rj::Document document = infrastructure::read_json_document(path);
  const std::string context = path.string();
  validate_union_document(document, profile, context);
  const rj::Value& features = infrastructure::required_member(
    document, "features", context);
  infrastructure::infrastructure_require(features.IsArray()
    && features.Size() == profile.expected_routes,
    context + " has the wrong feature count");

  std::set<std::pair<std::string, std::string>> keys;
  std::vector<fiber_route> result;
  result.reserve(features.Size());
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string item = context + ".features["
        + std::to_string(index) + "]";
      infrastructure::infrastructure_require(
        infrastructure::required_string(feature, "type", item) == "Feature",
        item + ".type must be Feature");
      const rj::Value& properties = infrastructure::required_member(
        feature, "properties", item);
      const rj::Value& geometry = infrastructure::required_member(
        feature, "geometry", item);
      fiber_route route;
      route.cable_id = infrastructure::required_string(
        properties, "source_system_id", item + ".properties");
      route.name = infrastructure::required_string(
        properties, "name", item + ".properties");
      route.feature_id = infrastructure::required_string(
        properties, "source_feature_id", item + ".properties");
      route.comparison_id = infrastructure::required_string(
        properties, "comparison_id", item + ".properties");
      route.source_snapshot = infrastructure::required_string(
        properties, "source_snapshot", item + ".properties");
      route.snapshot_membership = infrastructure::required_string(
        properties, "snapshot_membership", item + ".properties");
      route.temporal_class = infrastructure::required_string(
        properties, "temporal_class", item + ".properties");
      route.planned = infrastructure::required_bool(
        properties, "source_is_planned", item + ".properties");
      infrastructure::infrastructure_require(
        infrastructure::safe_identifier(route.cable_id)
          && infrastructure::safe_identifier(route.feature_id)
          && keys.emplace(route.source_snapshot, route.feature_id).second,
        item + " has an unsafe or duplicate source identity");
      const bool current = route.source_snapshot == profile.default_snapshot;
      infrastructure::infrastructure_require(current
        || (route.source_snapshot == profile.older_snapshot
            && route.snapshot_membership
               == profile.older_snapshot + "-only"),
        item + " violates cleaned-union selection");

      infrastructure::infrastructure_require(
        infrastructure::required_string(geometry, "type", item + ".geometry")
          == "MultiLineString",
        item + ".geometry must be MultiLineString");
      const rj::Value& lines = infrastructure::required_member(
        geometry, "coordinates", item + ".geometry");
      infrastructure::infrastructure_require(lines.IsArray()
        && !lines.Empty(), item + " has no route parts");
      for (rj::SizeType line_index = 0; line_index < lines.Size(); ++line_index)
        {
          const rj::Value& points = lines[line_index];
          infrastructure::infrastructure_require(points.IsArray()
            && points.Size() >= 2, item + " has a short route part");
          std::vector<generation::geographic_point> part;
          part.reserve(points.Size());
          for (rj::SizeType point = 0; point < points.Size(); ++point)
            part.push_back(infrastructure::parse_point_coordinates(
              points[point], item + ".geometry.coordinates"));
          route.paths.push_back(std::move(part));
        }
      result.push_back(std::move(route));
    }
  return result;
}

inline std::vector<fiber_landing>
load_fiber_landings(const fiber_profile& profile)
{
  const fs::path path = profile.directory / "landings.geojson";
  const rj::Document document = infrastructure::read_json_document(path);
  const std::string context = path.string();
  validate_union_document(document, profile, context);
  const rj::Value& features = infrastructure::required_member(
    document, "features", context);
  infrastructure::infrastructure_require(features.IsArray()
    && features.Size() == profile.expected_landings,
    context + " has the wrong feature count");
  std::set<std::pair<std::string, std::string>> keys;
  std::vector<fiber_landing> result;
  result.reserve(features.Size());
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string item = context + ".features["
        + std::to_string(index) + "]";
      const rj::Value& properties = infrastructure::required_member(
        feature, "properties", item);
      const rj::Value& geometry = infrastructure::required_member(
        feature, "geometry", item);
      fiber_landing landing;
      landing.id = infrastructure::required_string(
        properties, "source_landing_id", item + ".properties");
      landing.name = infrastructure::required_string(
        properties, "name", item + ".properties");
      landing.source_snapshot = infrastructure::required_string(
        properties, "source_snapshot", item + ".properties");
      landing.snapshot_membership = infrastructure::required_string(
        properties, "snapshot_membership", item + ".properties");
      landing.tbd = infrastructure::required_bool(
        properties, "is_tbd", item + ".properties");
      infrastructure::infrastructure_require(
        infrastructure::safe_identifier(landing.id)
          && keys.emplace(landing.source_snapshot, landing.id).second,
        item + " has an unsafe or duplicate source identity");
      const bool current = landing.source_snapshot == profile.default_snapshot;
      infrastructure::infrastructure_require(current
        || (landing.source_snapshot == profile.older_snapshot
            && landing.snapshot_membership
               == profile.older_snapshot + "-only"),
        item + " violates cleaned-union selection");
      infrastructure::infrastructure_require(
        infrastructure::required_string(geometry, "type", item + ".geometry")
          == "Point", item + ".geometry must be Point");
      landing.point = infrastructure::parse_point_coordinates(
        infrastructure::required_member(
          geometry, "coordinates", item + ".geometry"),
        item + ".geometry.coordinates");
      result.push_back(std::move(landing));
    }
  return result;
}

inline fiber_dataset
load_fiber_dataset(const fs::path& directory)
{
  fiber_dataset result;
  result.profile = load_fiber_profile(directory);
  result.routes = load_fiber_routes(result.profile);
  result.landings = load_fiber_landings(result.profile);
  for (const fiber_route& route : result.routes)
    {
      const bool current
        = route.source_snapshot == result.profile.default_snapshot;
      result.current_routes += current;
      result.historical_routes += !current;
      result.planned_routes += current && route.planned;
      result.planned_to_active_routes
        += current && route.temporal_class == "planned-to-active";
      result.current_only_routes += current
        && route.snapshot_membership
           == result.profile.default_snapshot + "-only";
    }
  for (const fiber_landing& landing : result.landings)
    {
      const bool current
        = landing.source_snapshot == result.profile.default_snapshot;
      result.current_landings += current;
      result.historical_landings += !current;
    }
  infrastructure::infrastructure_require(
    result.current_routes + result.historical_routes == result.routes.size()
      && result.current_landings + result.historical_landings
           == result.landings.size(),
    "fiber-synthesized classification is incomplete");
  return result;
}

} // namespace cart0freak0::fiber_synthesized_generation

#endif
