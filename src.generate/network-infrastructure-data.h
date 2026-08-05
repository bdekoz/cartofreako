// Validated cloud/CDN, submarine-cable, and Internet-exchange source data.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_INFRASTRUCTURE_DATA_H
#define CART0FREAK0_NETWORK_INFRASTRUCTURE_DATA_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

#include "projection-generation-common.h"

namespace cart0freak0::network_infrastructure_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;
namespace generation = cart0freak0::generation;

inline void
infrastructure_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline void
reject_duplicate_members(const rj::Value& value, const std::string& context)
{
  if (value.IsObject())
    {
      std::unordered_set<std::string> names;
      for (auto member = value.MemberBegin(); member != value.MemberEnd();
           ++member)
        {
          const std::string name(member->name.GetString(),
                                 member->name.GetStringLength());
          infrastructure_require(names.insert(name).second,
            context + " contains duplicate member '" + name + "'");
          reject_duplicate_members(member->value, context + "." + name);
        }
    }
  else if (value.IsArray())
    for (rj::SizeType index = 0; index < value.Size(); ++index)
      reject_duplicate_members(value[index], context + "["
        + std::to_string(index) + "]");
}

inline rj::Document
read_json_document(const fs::path& path,
                   const std::uintmax_t maximum_size = 64U * 1024U * 1024U)
{
  std::error_code error;
  const std::uintmax_t size = fs::file_size(path, error);
  infrastructure_require(!error, "failed to stat JSON file " + path.string());
  infrastructure_require(size != 0 && size <= maximum_size,
    "JSON file has an invalid or excessive size: " + path.string());
  std::ifstream input {path, std::ios::binary};
  infrastructure_require(input.good(), "failed to open JSON file "
                                      + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  infrastructure_require(!document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  reject_duplicate_members(document, path.string());
  return document;
}

inline const rj::Value&
required_member(const rj::Value& object, const char* name,
                const std::string_view context)
{
  infrastructure_require(object.IsObject() && object.HasMember(name),
    std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  infrastructure_require(value.IsString(), std::string(context) + "." + name
                                             + " must be a string");
  return {value.GetString(), value.GetStringLength()};
}

inline std::string
optional_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  infrastructure_require(value.IsNull() || value.IsString(),
    std::string(context) + "." + name + " must be a string or null");
  return value.IsNull()
    ? std::string {}
    : std::string(value.GetString(), value.GetStringLength());
}

inline std::size_t
required_size(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  infrastructure_require(value.IsUint64(), std::string(context) + "." + name
                                             + " must be an unsigned integer");
  infrastructure_require(value.GetUint64()
                           <= std::numeric_limits<std::size_t>::max(),
                         std::string(context) + "." + name + " is too large");
  return static_cast<std::size_t>(value.GetUint64());
}

inline unsigned
required_uint(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const std::size_t value = required_size(object, name, context);
  infrastructure_require(value <= std::numeric_limits<unsigned>::max(),
                         std::string(context) + "." + name + " is too large");
  return static_cast<unsigned>(value);
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  infrastructure_require(value.IsNumber() && std::isfinite(value.GetDouble()),
    std::string(context) + "." + name + " must be a finite number");
  return value.GetDouble();
}

inline bool
required_bool(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  infrastructure_require(value.IsBool(), std::string(context) + "." + name
                                           + " must be a boolean");
  return value.GetBool();
}

inline bool
lower_hex(const std::string_view value, const std::size_t size)
{
  return value.size() == size
    && std::all_of(value.begin(), value.end(), [](const char character) {
         return (character >= '0' && character <= '9')
           || (character >= 'a' && character <= 'f');
       });
}

inline bool
safe_relative_path(const fs::path& path)
{
  if (path.empty() || path.is_absolute())
    return false;
  for (const fs::path& component : path)
    if (component == "..")
      return false;
  return true;
}

inline generation::geographic_point
parse_point_coordinates(const rj::Value& coordinates,
                        const std::string& context)
{
  infrastructure_require(coordinates.IsArray() && coordinates.Size() >= 2
                           && coordinates[0].IsNumber()
                           && coordinates[1].IsNumber(),
                         context + " must begin with [longitude, latitude]");
  const double longitude = coordinates[0].GetDouble();
  const double latitude = coordinates[1].GetDouble();
  infrastructure_require(std::isfinite(longitude) && longitude >= -180
                           && longitude <= 180 && std::isfinite(latitude)
                           && latitude >= -90 && latitude <= 90,
                         context + " contains out-of-range coordinates");
  return {latitude, longitude};
}

enum class infrastructure_product
{
  sites,
  topology,
};

struct cloud_source_pin
{
  std::string repository;
  std::string commit;
  std::string license;
  std::string snapshot;
  fs::path manifest;
  std::string manifest_sha256;
  std::size_t expected_layers = 0;
  std::size_t expected_records = 0;
  std::size_t expected_located = 0;
};

struct cable_source_pin
{
  std::string repository;
  std::string commit;
  std::string license;
  std::string snapshot;
  fs::path routes;
  std::string routes_sha256;
  fs::path landings;
  std::string landings_sha256;
  fs::path detail_directory;
  std::size_t expected_systems = 0;
  std::size_t expected_route_features = 0;
  std::size_t expected_landings = 0;
};

struct exchange_source_pin
{
  std::string repository;
  std::string commit;
  std::string license;
  std::string snapshot;
  fs::path buildings;
  std::string buildings_sha256;
  std::size_t expected_buildings = 0;
  std::size_t expected_exchanges = 0;
  std::size_t expected_memberships = 0;
};

struct infrastructure_profile
{
  fs::path path;
  std::string name;
  infrastructure_product product = infrastructure_product::sites;
  double marker_radius = 0.032;
  double collision_cell = 0.18;
  double minimum_tether = 0.045;
  std::size_t maximum_labels = 48;
  std::size_t maximum_cable_labels = 16;
  bool show_tethers = true;
  bool include_observed_cloud = false;
  bool include_cloud_sites = true;
  bool include_submarine_cables = false;
  bool include_landing_points = false;
  bool include_exchange_buildings = false;
  bool include_exchange_membership = false;
  bool topology_opt_in = false;
  std::string generated_artifact_license;
  cloud_source_pin cloud;
  cable_source_pin cables;
  exchange_source_pin exchanges;
};

inline infrastructure_profile
parse_infrastructure_profile(const rj::Document& document,
                             const fs::path& path)
{
  const std::string context = path.string();
  infrastructure_require(document.IsObject(), context + " root must be an object");
  infrastructure_require(required_uint(document, "schema_version", context) == 1,
    context + " uses an unsupported schema version");

  infrastructure_profile result;
  result.path = path;
  result.name = required_string(document, "name", context);
  const std::string product = required_string(document, "product", context);
  infrastructure_require(product == "sites" || product == "topology",
                         context + ".product must be sites or topology");
  result.product = product == "sites" ? infrastructure_product::sites
                                      : infrastructure_product::topology;

  const rj::Value& display = required_member(document, "display", context);
  const std::string display_context = context + ".display";
  result.marker_radius = required_number(
    display, "marker_radius_inches", display_context);
  result.collision_cell = required_number(
    display, "collision_cell_inches", display_context);
  result.minimum_tether = required_number(
    display, "minimum_tether_inches", display_context);
  result.maximum_labels = required_size(
    display, "maximum_labels", display_context);
  result.maximum_cable_labels = required_size(
    display, "maximum_cable_labels", display_context);
  result.show_tethers = required_bool(display, "show_tethers", display_context);
  result.include_observed_cloud = required_bool(
    display, "include_observed_cloud", display_context);
  infrastructure_require(result.marker_radius > 0 && result.marker_radius <= 0.2,
                         display_context + ".marker_radius_inches is invalid");
  infrastructure_require(result.collision_cell >= result.marker_radius * 2
                           && result.collision_cell <= 2,
                         display_context + ".collision_cell_inches is invalid");
  infrastructure_require(result.minimum_tether >= 0 && result.minimum_tether <= 2,
                         display_context + ".minimum_tether_inches is invalid");
  infrastructure_require(result.maximum_labels <= 500
                           && result.maximum_cable_labels <= 200,
                         display_context + " requests too many labels");

  const rj::Value& layers = required_member(document, "layers", context);
  const std::string layers_context = context + ".layers";
  result.include_cloud_sites = required_bool(
    layers, "cloud_cdn_sites", layers_context);
  result.include_submarine_cables = required_bool(
    layers, "submarine_cables", layers_context);
  result.include_landing_points = required_bool(
    layers, "landing_points", layers_context);
  result.include_exchange_buildings = required_bool(
    layers, "internet_exchange_buildings", layers_context);
  result.include_exchange_membership = required_bool(
    layers, "internet_exchange_membership", layers_context);

  const rj::Value& licensing = required_member(document, "licensing", context);
  const std::string licensing_context = context + ".licensing";
  result.topology_opt_in = required_bool(
    licensing, "tele_geography_opt_in", licensing_context);
  result.generated_artifact_license = required_string(
    licensing, "generated_artifact_license", licensing_context);

  const rj::Value& sources = required_member(document, "sources", context);
  const std::string sources_context = context + ".sources";
  const rj::Value& cloud = required_member(sources, "cloud_cdn", sources_context);
  const std::string cloud_context = sources_context + ".cloud_cdn";
  result.cloud.repository = required_string(cloud, "repository", cloud_context);
  result.cloud.commit = required_string(cloud, "commit", cloud_context);
  result.cloud.license = required_string(cloud, "license", cloud_context);
  result.cloud.snapshot = required_string(cloud, "snapshot", cloud_context);
  result.cloud.manifest = required_string(cloud, "manifest", cloud_context);
  result.cloud.manifest_sha256 = required_string(
    cloud, "manifest_sha256", cloud_context);
  result.cloud.expected_layers = required_size(
    cloud, "expected_layers", cloud_context);
  result.cloud.expected_records = required_size(
    cloud, "expected_records", cloud_context);
  result.cloud.expected_located = required_size(
    cloud, "expected_located", cloud_context);

  const rj::Value& cables = required_member(
    sources, "submarine_cables", sources_context);
  const std::string cables_context = sources_context + ".submarine_cables";
  result.cables.repository = required_string(
    cables, "repository", cables_context);
  result.cables.commit = required_string(cables, "commit", cables_context);
  result.cables.license = required_string(cables, "license", cables_context);
  result.cables.snapshot = required_string(cables, "snapshot", cables_context);
  result.cables.routes = required_string(cables, "routes", cables_context);
  result.cables.routes_sha256 = required_string(
    cables, "routes_sha256", cables_context);
  result.cables.landings = required_string(cables, "landings", cables_context);
  result.cables.landings_sha256 = required_string(
    cables, "landings_sha256", cables_context);
  result.cables.detail_directory = required_string(
    cables, "detail_directory", cables_context);
  result.cables.expected_systems = required_size(
    cables, "expected_systems", cables_context);
  result.cables.expected_route_features = required_size(
    cables, "expected_route_features", cables_context);
  result.cables.expected_landings = required_size(
    cables, "expected_landings", cables_context);

  const rj::Value& exchanges = required_member(
    sources, "internet_exchanges", sources_context);
  const std::string exchanges_context = sources_context + ".internet_exchanges";
  result.exchanges.repository = required_string(
    exchanges, "repository", exchanges_context);
  result.exchanges.commit = required_string(
    exchanges, "commit", exchanges_context);
  result.exchanges.license = required_string(
    exchanges, "license", exchanges_context);
  result.exchanges.snapshot = required_string(
    exchanges, "snapshot", exchanges_context);
  result.exchanges.buildings = required_string(
    exchanges, "buildings", exchanges_context);
  result.exchanges.buildings_sha256 = required_string(
    exchanges, "buildings_sha256", exchanges_context);
  result.exchanges.expected_buildings = required_size(
    exchanges, "expected_buildings", exchanges_context);
  result.exchanges.expected_exchanges = required_size(
    exchanges, "expected_exchanges", exchanges_context);
  result.exchanges.expected_memberships = required_size(
    exchanges, "expected_memberships", exchanges_context);

  const auto check_pin = [&](const std::string& pin_context,
                             const std::string& commit,
                             const std::string& digest) {
    infrastructure_require(lower_hex(commit, 40),
                           pin_context + ".commit must be lowercase SHA-1");
    infrastructure_require(lower_hex(digest, 64),
                           pin_context + " digest must be lowercase SHA-256");
  };
  check_pin(cloud_context, result.cloud.commit,
            result.cloud.manifest_sha256);
  check_pin(cables_context, result.cables.commit,
            result.cables.routes_sha256);
  infrastructure_require(lower_hex(result.cables.landings_sha256, 64),
    cables_context + ".landings_sha256 must be lowercase SHA-256");
  check_pin(exchanges_context, result.exchanges.commit,
            result.exchanges.buildings_sha256);
  infrastructure_require(safe_relative_path(result.cloud.manifest)
                           && safe_relative_path(result.cables.routes)
                           && safe_relative_path(result.cables.landings)
                           && safe_relative_path(result.cables.detail_directory)
                           && safe_relative_path(result.exchanges.buildings),
                         context + " contains an unsafe source path");

  const bool any_topology = result.include_submarine_cables
    || result.include_landing_points || result.include_exchange_buildings
    || result.include_exchange_membership;
  infrastructure_require(result.include_cloud_sites,
                         layers_context + ".cloud_cdn_sites must be enabled");
  if (result.product == infrastructure_product::sites)
    infrastructure_require(!any_topology && !result.topology_opt_in,
      context + " sites product cannot enable licensed topology");
  else
    infrastructure_require(any_topology && result.topology_opt_in
      && result.generated_artifact_license.find("CC BY-NC-SA 3.0")
           != std::string::npos,
      context + " topology product must explicitly opt in to CC BY-NC-SA 3.0");
  return result;
}

inline infrastructure_profile
load_infrastructure_profile(const fs::path& path)
{
  return parse_infrastructure_profile(read_json_document(path), path);
}

struct cloud_site
{
  std::string id;
  std::string provider;
  std::string service;
  std::string entity_type;
  std::string name;
  std::string city;
  std::string country;
  std::string source_scope;
  std::string lifecycle_status;
  std::string location_precision;
  generation::geographic_point point {};
};

struct cloud_dataset
{
  std::string snapshot;
  std::string schema_version;
  std::size_t layer_count = 0;
  std::size_t record_count = 0;
  std::size_t null_geometry_count = 0;
  std::vector<cloud_site> sites;
};

inline cloud_dataset
load_cloud_dataset(const fs::path& root,
                   const infrastructure_profile& profile)
{
  const fs::path manifest_path = root / profile.cloud.manifest;
  const rj::Document manifest = read_json_document(manifest_path);
  const std::string context = manifest_path.string();
  infrastructure_require(manifest.IsObject(), context + " root must be an object");
  cloud_dataset result;
  result.snapshot = required_string(
    manifest, "generated_from_retained_snapshots_at", context);
  result.layer_count = required_size(manifest, "layer_count", context);
  result.record_count = required_size(manifest, "record_count", context);
  const rj::Value& schema = required_member(manifest, "schema", context);
  result.schema_version = required_string(schema, "version", context + ".schema");
  const rj::Value& layers = required_member(manifest, "layers", context);
  infrastructure_require(layers.IsArray() && layers.Size() == result.layer_count,
                         context + ".layers does not match layer_count");
  std::unordered_set<std::string> seen_ids;
  std::size_t parsed_records = 0;
  for (rj::SizeType layer_index = 0; layer_index < layers.Size(); ++layer_index)
    {
      const rj::Value& layer = layers[layer_index];
      const std::string layer_context = context + ".layers["
        + std::to_string(layer_index) + "]";
      const std::string layer_name = required_string(
        layer, "layer", layer_context);
      const std::size_t layer_records = required_size(
        layer, "record_count", layer_context);
      const std::size_t expected_null = required_size(
        layer, "geometry_null", layer_context);
      const rj::Value& files = required_member(layer, "files", layer_context);
      const rj::Value& geojson = required_member(
        files, "geojson", layer_context + ".files");
      const fs::path relative = required_string(
        geojson, "path", layer_context + ".files.geojson");
      infrastructure_require(safe_relative_path(relative),
                             layer_context + " has an unsafe GeoJSON path");
      const fs::path geojson_path = root / relative;
      const rj::Document document = read_json_document(geojson_path);
      const std::string geo_context = geojson_path.string();
      infrastructure_require(required_string(document, "type", geo_context)
                               == "FeatureCollection",
                             geo_context + ".type must be FeatureCollection");
      const rj::Value& features = required_member(
        document, "features", geo_context);
      infrastructure_require(features.IsArray()
                               && features.Size() == layer_records,
                             geo_context + ".features has the wrong count");
      std::size_t null_count = 0;
      for (rj::SizeType index = 0; index < features.Size(); ++index)
        {
          const rj::Value& feature = features[index];
          const std::string feature_context = geo_context + ".features["
            + std::to_string(index) + "]";
          infrastructure_require(required_string(feature, "type", feature_context)
                                   == "Feature",
                                 feature_context + ".type must be Feature");
          const rj::Value& properties = required_member(
            feature, "properties", feature_context);
          const std::string id = required_string(
            properties, "record_id", feature_context + ".properties");
          infrastructure_require(seen_ids.insert(id).second,
                                 "cloud manifest repeats record_id " + id);
          const rj::Value& geometry = required_member(
            feature, "geometry", feature_context);
          if (geometry.IsNull())
            {
              ++null_count;
              continue;
            }
          infrastructure_require(geometry.IsObject()
            && required_string(geometry, "type", feature_context + ".geometry")
                 == "Point",
            feature_context + ".geometry must be Point or null");
          cloud_site site;
          site.id = id;
          site.provider = required_string(
            properties, "provider", feature_context + ".properties");
          site.service = required_string(
            properties, "service", feature_context + ".properties");
          site.entity_type = required_string(
            properties, "entity_type", feature_context + ".properties");
          site.name = required_string(
            properties, "name", feature_context + ".properties");
          site.city = optional_string(
            properties, "city", feature_context + ".properties");
          site.country = optional_string(
            properties, "country", feature_context + ".properties");
          site.source_scope = required_string(
            properties, "source_scope", feature_context + ".properties");
          site.lifecycle_status = required_string(
            properties, "lifecycle_status", feature_context + ".properties");
          site.location_precision = required_string(
            properties, "location_precision", feature_context + ".properties");
          site.point = parse_point_coordinates(
            required_member(geometry, "coordinates", feature_context + ".geometry"),
            feature_context + ".geometry.coordinates");
          if (profile.include_observed_cloud || site.source_scope != "observed")
            result.sites.push_back(std::move(site));
        }
      infrastructure_require(null_count == expected_null,
                             layer_context + " geometry_null is inconsistent");
      result.null_geometry_count += null_count;
      parsed_records += layer_records;
      static_cast<void>(layer_name);
    }
  infrastructure_require(parsed_records == result.record_count,
                         context + " canonical record_count is inconsistent");
  infrastructure_require(result.layer_count == profile.cloud.expected_layers
                           && result.record_count == profile.cloud.expected_records
                           && result.sites.size() == profile.cloud.expected_located,
                         context + " does not match the pinned cloud snapshot");
  return result;
}

struct cable_system
{
  std::string id;
  std::string name;
  bool planned = false;
  std::optional<unsigned> rfs_year;
  std::vector<std::string> landing_ids;
};

struct cable_route
{
  std::string cable_id;
  std::string name;
  std::string feature_id;
  std::string source_color;
  bool planned = false;
  std::vector<std::vector<generation::geographic_point>> paths;
};

struct landing_point
{
  std::string id;
  std::string name;
  bool tbd = false;
  std::size_t cable_count = 0;
  generation::geographic_point point {};
};

struct cable_dataset
{
  std::vector<cable_system> systems;
  std::vector<cable_route> routes;
  std::vector<landing_point> landings;
  std::size_t planned_systems = 0;
  std::size_t route_parts = 0;
  std::size_t route_vertices = 0;
};

inline bool
safe_identifier(const std::string_view value)
{
  return !value.empty()
    && std::all_of(value.begin(), value.end(), [](const unsigned char c) {
         return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
           || c == '-';
       });
}

inline cable_dataset
load_cable_dataset(const fs::path& root,
                   const infrastructure_profile& profile)
{
  cable_dataset result;
  const fs::path routes_path = root / profile.cables.routes;
  const rj::Document routes_document = read_json_document(routes_path);
  const std::string routes_context = routes_path.string();
  infrastructure_require(required_string(
    routes_document, "type", routes_context) == "FeatureCollection",
    routes_context + ".type must be FeatureCollection");
  const rj::Value& route_features = required_member(
    routes_document, "features", routes_context);
  infrastructure_require(route_features.IsArray() && !route_features.Empty(),
                         routes_context + ".features must be nonempty");

  std::set<std::string> cable_ids;
  for (const rj::Value& feature : route_features.GetArray())
    {
      const rj::Value& properties = required_member(
        feature, "properties", routes_context + ".feature");
      const std::string id = required_string(
        properties, "id", routes_context + ".feature.properties");
      infrastructure_require(safe_identifier(id),
                             routes_context + " contains an unsafe cable id");
      cable_ids.insert(id);
    }

  std::map<std::string, std::size_t> system_index;
  for (const std::string& id : cable_ids)
    {
      const fs::path detail_path
        = root / profile.cables.detail_directory / (id + ".json");
      const rj::Document detail = read_json_document(detail_path);
      const std::string detail_context = detail_path.string();
      cable_system system;
      system.id = required_string(detail, "id", detail_context);
      system.name = required_string(detail, "name", detail_context);
      system.planned = required_bool(detail, "is_planned", detail_context);
      infrastructure_require(system.id == id,
                             detail_context + " id does not match its filename");
      const rj::Value& rfs_year = required_member(
        detail, "rfs_year", detail_context);
      infrastructure_require(rfs_year.IsNull() || rfs_year.IsUint(),
                             detail_context + ".rfs_year is invalid");
      if (rfs_year.IsUint())
        system.rfs_year = rfs_year.GetUint();
      const rj::Value& landing_points = required_member(
        detail, "landing_points", detail_context);
      infrastructure_require(landing_points.IsArray(),
                             detail_context + ".landing_points must be an array");
      std::set<std::string> unique_landings;
      for (const rj::Value& landing : landing_points.GetArray())
        {
          const std::string landing_id = required_string(
            landing, "id", detail_context + ".landing_points[]");
          infrastructure_require(safe_identifier(landing_id),
                                 detail_context + " has an unsafe landing id");
          infrastructure_require(unique_landings.insert(landing_id).second,
                                 detail_context + " repeats landing " + landing_id);
          system.landing_ids.push_back(landing_id);
        }
      if (system.planned)
        ++result.planned_systems;
      system_index.emplace(system.id, result.systems.size());
      result.systems.push_back(std::move(system));
    }

  result.routes.reserve(route_features.Size());
  std::set<std::string> feature_ids;
  for (rj::SizeType index = 0; index < route_features.Size(); ++index)
    {
      const rj::Value& feature = route_features[index];
      const std::string feature_context = routes_context + ".features["
        + std::to_string(index) + "]";
      const rj::Value& properties = required_member(
        feature, "properties", feature_context);
      const rj::Value& geometry = required_member(
        feature, "geometry", feature_context);
      cable_route route;
      route.cable_id = required_string(
        properties, "id", feature_context + ".properties");
      route.name = required_string(
        properties, "name", feature_context + ".properties");
      route.feature_id = required_string(
        properties, "feature_id", feature_context + ".properties");
      route.source_color = required_string(
        properties, "color", feature_context + ".properties");
      infrastructure_require(feature_ids.insert(route.feature_id).second,
                             feature_context + " repeats feature_id "
                               + route.feature_id);
      const auto system = system_index.find(route.cable_id);
      infrastructure_require(system != system_index.end(),
                             feature_context + " has no cable detail record");
      route.planned = result.systems[system->second].planned;
      infrastructure_require(required_string(
        geometry, "type", feature_context + ".geometry") == "MultiLineString",
        feature_context + ".geometry.type must be MultiLineString");
      const rj::Value& lines = required_member(
        geometry, "coordinates", feature_context + ".geometry");
      infrastructure_require(lines.IsArray() && !lines.Empty(),
                             feature_context + " has no route parts");
      for (rj::SizeType line_index = 0; line_index < lines.Size(); ++line_index)
        {
          const rj::Value& points = lines[line_index];
          infrastructure_require(points.IsArray() && points.Size() >= 2,
                                 feature_context + " route part is too short");
          std::vector<generation::geographic_point> path;
          path.reserve(points.Size());
          for (rj::SizeType point_index = 0; point_index < points.Size();
               ++point_index)
            path.push_back(parse_point_coordinates(points[point_index],
              feature_context + ".geometry.coordinates["
                + std::to_string(line_index) + "]["
                + std::to_string(point_index) + "]"));
          result.route_vertices += path.size();
          ++result.route_parts;
          route.paths.push_back(std::move(path));
        }
      result.routes.push_back(std::move(route));
    }

  const fs::path landings_path = root / profile.cables.landings;
  const rj::Document landings_document = read_json_document(landings_path);
  const std::string landings_context = landings_path.string();
  infrastructure_require(required_string(
    landings_document, "type", landings_context) == "FeatureCollection",
    landings_context + ".type must be FeatureCollection");
  const rj::Value& landing_features = required_member(
    landings_document, "features", landings_context);
  infrastructure_require(landing_features.IsArray() && !landing_features.Empty(),
                         landings_context + ".features must be nonempty");
  std::map<std::string, std::size_t> landing_index;
  result.landings.reserve(landing_features.Size());
  for (rj::SizeType index = 0; index < landing_features.Size(); ++index)
    {
      const rj::Value& feature = landing_features[index];
      const std::string feature_context = landings_context + ".features["
        + std::to_string(index) + "]";
      const rj::Value& properties = required_member(
        feature, "properties", feature_context);
      const rj::Value& geometry = required_member(
        feature, "geometry", feature_context);
      landing_point landing;
      landing.id = required_string(
        properties, "id", feature_context + ".properties");
      landing.name = required_string(
        properties, "name", feature_context + ".properties");
      landing.tbd = required_bool(
        properties, "is_tbd", feature_context + ".properties");
      infrastructure_require(required_string(
        geometry, "type", feature_context + ".geometry") == "Point",
        feature_context + ".geometry.type must be Point");
      landing.point = parse_point_coordinates(required_member(
        geometry, "coordinates", feature_context + ".geometry"),
        feature_context + ".geometry.coordinates");
      infrastructure_require(landing_index.emplace(
        landing.id, result.landings.size()).second,
        feature_context + " repeats landing id " + landing.id);
      result.landings.push_back(std::move(landing));
    }
  for (const cable_system& system : result.systems)
    for (const std::string& id : system.landing_ids)
      {
        const auto landing = landing_index.find(id);
        infrastructure_require(landing != landing_index.end(),
          "cable " + system.id + " references unknown landing " + id);
        ++result.landings[landing->second].cable_count;
      }
  infrastructure_require(result.systems.size() == profile.cables.expected_systems
    && result.routes.size() == profile.cables.expected_route_features
    && result.landings.size() == profile.cables.expected_landings,
    routes_context + " does not match the pinned cable snapshot");
  return result;
}

struct exchange_membership
{
  std::string slug;
  std::string name;
};

struct exchange_building
{
  std::string id;
  std::string slug;
  std::string name;
  std::string country;
  std::string metro_area;
  generation::geographic_point point {};
  std::vector<exchange_membership> exchanges;
};

struct internet_exchange
{
  std::string slug;
  std::string name;
  std::vector<std::size_t> building_indices;
};

struct exchange_dataset
{
  std::vector<exchange_building> buildings;
  std::vector<internet_exchange> exchanges;
  std::size_t membership_count = 0;
  std::size_t duplicate_membership_count = 0;
};

inline std::string
first_array_string(const rj::Value& object, const char* name,
                   const std::string& context)
{
  const rj::Value& values = required_member(object, name, context);
  infrastructure_require(values.IsArray() && !values.Empty()
                           && values[0].IsString(),
                         context + "." + name
                           + " must be a nonempty string array");
  return {values[0].GetString(), values[0].GetStringLength()};
}

inline exchange_dataset
load_exchange_dataset(const fs::path& root,
                      const infrastructure_profile& profile)
{
  exchange_dataset result;
  const fs::path buildings_path = root / profile.exchanges.buildings;
  const rj::Document document = read_json_document(buildings_path);
  const std::string context = buildings_path.string();
  infrastructure_require(required_string(document, "type", context)
                           == "FeatureCollection",
                         context + ".type must be FeatureCollection");
  const rj::Value& features = required_member(document, "features", context);
  infrastructure_require(features.IsArray() && !features.Empty(),
                         context + ".features must be nonempty");
  std::set<std::string> building_ids;
  std::map<std::string, internet_exchange> exchanges;
  result.buildings.reserve(features.Size());
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string feature_context = context + ".features["
        + std::to_string(index) + "]";
      const rj::Value& properties = required_member(
        feature, "properties", feature_context);
      const rj::Value& geometry = required_member(
        feature, "geometry", feature_context);
      exchange_building building;
      const rj::Value& building_id = required_member(
        properties, "building_id", feature_context + ".properties");
      infrastructure_require(building_id.IsInt64() || building_id.IsUint64(),
                             feature_context + ".properties.building_id is invalid");
      building.id = building_id.IsInt64()
        ? std::to_string(building_id.GetInt64())
        : std::to_string(building_id.GetUint64());
      infrastructure_require(building_ids.insert(building.id).second,
                             feature_context + " repeats building id "
                               + building.id);
      building.slug = required_string(
        properties, "slug", feature_context + ".properties");
      building.name = first_array_string(
        properties, "address", feature_context + ".properties");
      building.country = required_string(
        properties, "country", feature_context + ".properties");
      building.metro_area = required_string(
        properties, "metro_area", feature_context + ".properties");
      infrastructure_require(required_string(
        geometry, "type", feature_context + ".geometry") == "Point",
        feature_context + ".geometry.type must be Point");
      building.point = parse_point_coordinates(required_member(
        geometry, "coordinates", feature_context + ".geometry"),
        feature_context + ".geometry.coordinates");
      const rj::Value& memberships = required_member(
        properties, "exchanges", feature_context + ".properties");
      infrastructure_require(memberships.IsArray() && !memberships.Empty(),
                             feature_context + ".properties.exchanges is empty");
      std::set<std::string> unique_memberships;
      for (const rj::Value& membership : memberships.GetArray())
        {
          exchange_membership parsed;
          parsed.slug = required_string(
            membership, "slug", feature_context + ".properties.exchanges[]");
          parsed.name = first_array_string(
            membership, "address", feature_context + ".properties.exchanges[]");
          ++result.membership_count;
          if (!unique_memberships.insert(parsed.slug).second)
            {
              ++result.duplicate_membership_count;
              continue;
            }
          auto [exchange, inserted] = exchanges.try_emplace(
            parsed.slug, internet_exchange {parsed.slug, parsed.name, {}});
          if (!inserted)
            infrastructure_require(exchange->second.name == parsed.name,
              "exchange " + parsed.slug + " has inconsistent names");
          exchange->second.building_indices.push_back(result.buildings.size());
          building.exchanges.push_back(std::move(parsed));
        }
      result.buildings.push_back(std::move(building));
    }
  result.exchanges.reserve(exchanges.size());
  for (auto& [slug, exchange] : exchanges)
    {
      static_cast<void>(slug);
      std::sort(exchange.building_indices.begin(),
                exchange.building_indices.end());
      result.exchanges.push_back(std::move(exchange));
    }
  infrastructure_require(result.buildings.size()
                           == profile.exchanges.expected_buildings
    && result.exchanges.size() == profile.exchanges.expected_exchanges
    && result.membership_count == profile.exchanges.expected_memberships,
    context + " does not match the pinned Internet-exchange snapshot");
  return result;
}

struct infrastructure_dataset
{
  cloud_dataset cloud;
  cable_dataset cables;
  exchange_dataset exchanges;
};

inline infrastructure_dataset
load_infrastructure_dataset(const infrastructure_profile& profile,
                            const fs::path& cloud_root,
                            const std::optional<fs::path>& cable_root,
                            const std::optional<fs::path>& exchange_root)
{
  infrastructure_dataset result;
  result.cloud = load_cloud_dataset(cloud_root, profile);
  if (profile.product == infrastructure_product::topology)
    {
      infrastructure_require(cable_root.has_value()
                               && exchange_root.has_value(),
                             "topology generation requires both TeleGeography roots");
      result.cables = load_cable_dataset(*cable_root, profile);
      result.exchanges = load_exchange_dataset(*exchange_root, profile);
    }
  return result;
}

} // namespace cart0freak0::network_infrastructure_generation

#endif
