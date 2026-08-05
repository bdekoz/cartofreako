// Strict network profile and cumulative swarm GeoJSON ingestion.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_DATA_H
#define CART0FREAK0_NETWORK_DATA_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::network_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
network_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

struct downloader_counts
{
  std::uint64_t size = 0;
  std::uint64_t mobile = 0;
  std::uint64_t satellite = 0;
  std::uint64_t tor = 0;
  std::uint64_t tor_exit_nodes = 0;
  std::uint64_t vpn = 0;
  std::uint64_t relay = 0;
  std::uint64_t proxy = 0;
  std::uint64_t hosting = 0;
  std::uint64_t service = 0;
};

enum class downloader_metric
{
  size,
  mobile,
  satellite,
  tor,
  tor_exit_nodes,
  vpn,
  relay,
  proxy,
  hosting,
  service,
};

struct metric_descriptor
{
  downloader_metric metric;
  std::string_view field;
  std::string_view layer;
};

inline constexpr std::array metric_descriptors {
  metric_descriptor {downloader_metric::size, "size", "downloaders-total"},
  metric_descriptor {downloader_metric::mobile, "mobile",
                     "downloaders-mobile"},
  metric_descriptor {downloader_metric::satellite, "satellite",
                     "downloaders-satellite"},
  metric_descriptor {downloader_metric::tor, "tor", "downloaders-tor"},
  metric_descriptor {downloader_metric::tor_exit_nodes, "tor_exit_nodes",
                     "downloaders-tor-exit-nodes"},
  metric_descriptor {downloader_metric::vpn, "vpn", "downloaders-vpn"},
  metric_descriptor {downloader_metric::relay, "relay",
                     "downloaders-relay"},
  metric_descriptor {downloader_metric::proxy, "proxy",
                     "downloaders-proxy"},
  metric_descriptor {downloader_metric::hosting, "hosting",
                     "downloaders-hosting"},
  metric_descriptor {downloader_metric::service, "service",
                     "downloaders-service"},
};

inline std::uint64_t
metric_value(const downloader_counts& counts, const downloader_metric metric)
{
  switch (metric)
    {
    case downloader_metric::size: return counts.size;
    case downloader_metric::mobile: return counts.mobile;
    case downloader_metric::satellite: return counts.satellite;
    case downloader_metric::tor: return counts.tor;
    case downloader_metric::tor_exit_nodes: return counts.tor_exit_nodes;
    case downloader_metric::vpn: return counts.vpn;
    case downloader_metric::relay: return counts.relay;
    case downloader_metric::proxy: return counts.proxy;
    case downloader_metric::hosting: return counts.hosting;
    case downloader_metric::service: return counts.service;
    }
  throw std::logic_error("unhandled downloader metric");
}

inline std::uint64_t&
metric_value(downloader_counts& counts, const downloader_metric metric)
{
  switch (metric)
    {
    case downloader_metric::size: return counts.size;
    case downloader_metric::mobile: return counts.mobile;
    case downloader_metric::satellite: return counts.satellite;
    case downloader_metric::tor: return counts.tor;
    case downloader_metric::tor_exit_nodes: return counts.tor_exit_nodes;
    case downloader_metric::vpn: return counts.vpn;
    case downloader_metric::relay: return counts.relay;
    case downloader_metric::proxy: return counts.proxy;
    case downloader_metric::hosting: return counts.hosting;
    case downloader_metric::service: return counts.service;
    }
  throw std::logic_error("unhandled downloader metric");
}

struct swarm_feature
{
  std::string country_code;
  std::string city;
  std::string geoname_id;
  H3Index h3 = 0;
  double longitude = 0;
  double latitude = 0;
  downloader_counts downloaders;
};

struct swarm_dataset
{
  std::string id;
  std::string datestamp;
  std::string duration_type;
  std::string data_version;
  std::string partition_by;
  unsigned duration_index = 0;
  unsigned h3_resolution = 0;
  std::uint64_t minimum_size = 0;
  std::uint64_t reported_swarm_features_size = 0;
  std::uint64_t btiha_size = 0;
  std::vector<swarm_feature> features;
};

struct network_profile
{
  fs::path path;
  std::string name;
  unsigned source_h3_resolution = 5;
  unsigned parent_h3_resolution = 3;
  double marker_radius = 0.026;
  double minimum_tether = 0.035;
  std::size_t maximum_labels = 40;
  double minimum_nonzero_opacity = 0.18;
  bool show_tethers = true;
  downloader_counts scale_reference;
  std::string archive;
  std::string archive_sha256;
  std::string geojson_member;
  std::string geojson_sha256;
  std::string source_repository;
  std::string source_commit;
  std::string license;
};

inline void
reject_duplicate_members(const rj::Value& value,
                         const std::string& context)
{
  if (value.IsObject())
    {
      std::unordered_set<std::string> names;
      for (auto member = value.MemberBegin(); member != value.MemberEnd();
           ++member)
        {
          const std::string name(member->name.GetString(),
                                 member->name.GetStringLength());
          network_require(names.insert(name).second,
                          context + " contains duplicate member '" + name
                            + "'");
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
  network_require(!error, "failed to stat JSON file " + path.string());
  network_require(size != 0 && size <= maximum_size,
                  "JSON file has an invalid or excessive size: "
                    + path.string());
  std::ifstream input {path, std::ios::binary};
  network_require(input.good(), "failed to open JSON file " + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  network_require(
    !document.HasParseError(),
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
  network_require(object.IsObject() && object.HasMember(name),
                  std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  network_require(value.IsString(), std::string(context) + "." + name
                                      + " must be a string");
  return {value.GetString(), value.GetStringLength()};
}

inline std::uint64_t
required_uint64(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  network_require(value.IsUint64(), std::string(context) + "." + name
                                      + " must be an unsigned integer");
  return value.GetUint64();
}

inline unsigned
required_uint(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const std::uint64_t value = required_uint64(object, name, context);
  network_require(value <= std::numeric_limits<unsigned>::max(),
                  std::string(context) + "." + name + " is too large");
  return static_cast<unsigned>(value);
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  network_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                  std::string(context) + "." + name
                    + " must be a finite number");
  return value.GetDouble();
}

inline bool
required_bool(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  network_require(value.IsBool(), std::string(context) + "." + name
                                    + " must be a boolean");
  return value.GetBool();
}

inline downloader_counts
parse_counts(const rj::Value& value, const std::string& context)
{
  network_require(value.IsObject(), context + " must be an object");
  downloader_counts result;
  for (const metric_descriptor descriptor : metric_descriptors)
    metric_value(result, descriptor.metric) = required_uint64(
      value, descriptor.field.data(), context);
  return result;
}

inline std::string
h3_string(const H3Index cell)
{
  std::array<char, 32> buffer {};
  network_require(h3ToString(cell, buffer.data(), buffer.size()) == E_SUCCESS,
                  "failed to format H3 cell");
  return buffer.data();
}

inline H3Index
h3_parent(const H3Index cell, const int resolution)
{
  H3Index parent = 0;
  network_require(cellToParent(cell, resolution, &parent) == E_SUCCESS,
                  "failed to compute H3 parent for " + h3_string(cell));
  return parent;
}

inline swarm_dataset
parse_swarm_dataset(const rj::Document& document,
                    const std::string_view context = "swarm GeoJSON")
{
  network_require(document.IsObject(),
                  std::string(context) + " root must be an object");
  network_require(required_string(document, "type", context)
                    == "FeatureCollection",
                  std::string(context) + ".type must be FeatureCollection");

  swarm_dataset result;
  result.id = required_string(document, "id", context);
  result.datestamp = required_string(document, "datestamp", context);
  result.duration_type = required_string(document, "duration_type", context);
  result.data_version = required_string(document, "data_version", context);
  result.partition_by = required_string(
    document, "swarm_geo_partition_by", context);
  result.duration_index = required_uint(document, "duration_index", context);
  result.h3_resolution = required_uint(
    document, "swarm_hexagon_resolution", context);
  result.minimum_size = required_uint64(document, "swarm_size_min", context);
  result.reported_swarm_features_size = required_uint64(
    document, "swarm_features_size", context);
  result.btiha_size = required_uint64(document, "btiha_size", context);
  network_require(result.partition_by == "hexagon",
                  std::string(context)
                    + ".swarm_geo_partition_by must be hexagon");
  network_require(result.duration_type == "cumulative",
                  std::string(context)
                    + ".duration_type must be cumulative");
  network_require(result.h3_resolution <= 15,
                  std::string(context) + " has an invalid H3 resolution");

  const rj::Value& features = required_member(document, "features", context);
  network_require(features.IsArray() && !features.Empty(),
                  std::string(context) + ".features must be a nonempty array");
  result.features.reserve(features.Size());
  std::unordered_set<H3Index> seen_cells;
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& source = features[index];
      const std::string feature_context = std::string(context) + ".features["
        + std::to_string(index) + "]";
      network_require(source.IsObject(), feature_context + " must be an object");
      network_require(required_string(source, "type", feature_context)
                        == "Feature",
                      feature_context + ".type must be Feature");
      const rj::Value& properties = required_member(
        source, "properties", feature_context);
      const rj::Value& geometry = required_member(
        source, "geometry", feature_context);
      network_require(properties.IsObject(),
                      feature_context + ".properties must be an object");
      network_require(geometry.IsObject(),
                      feature_context + ".geometry must be an object");
      network_require(required_string(geometry, "type", feature_context
                                      + ".geometry") == "Point",
                      feature_context + ".geometry.type must be Point");
      const rj::Value& coordinates = required_member(
        geometry, "coordinates", feature_context + ".geometry");
      network_require(coordinates.IsArray() && coordinates.Size() >= 2
                        && coordinates[0].IsNumber()
                        && coordinates[1].IsNumber(),
                      feature_context
                        + ".geometry.coordinates must begin with [lon, lat]");

      swarm_feature feature;
      feature.country_code = required_string(
        properties, "country_code", feature_context + ".properties");
      feature.city = required_string(
        properties, "city", feature_context + ".properties");
      feature.geoname_id = required_string(
        properties, "geoname_id", feature_context + ".properties");
      feature.h3 = required_uint64(
        properties, "h3_hexagon", feature_context + ".properties");
      feature.longitude = coordinates[0].GetDouble();
      feature.latitude = coordinates[1].GetDouble();
      feature.downloaders = parse_counts(
        required_member(properties, "downloaders",
                        feature_context + ".properties"),
        feature_context + ".properties.downloaders");

      network_require(std::isfinite(feature.longitude)
                        && feature.longitude >= -180
                        && feature.longitude <= 180
                        && std::isfinite(feature.latitude)
                        && feature.latitude >= -90
                        && feature.latitude <= 90,
                      feature_context + " has out-of-range coordinates");
      network_require(isValidCell(feature.h3) != 0,
                      feature_context + " has an invalid H3 cell");
      network_require(getResolution(feature.h3)
                        == static_cast<int>(result.h3_resolution),
                      feature_context + " has the wrong H3 resolution");
      network_require(seen_cells.insert(feature.h3).second,
                      feature_context + " repeats H3 cell "
                        + h3_string(feature.h3));
      network_require(feature.downloaders.size >= result.minimum_size,
                      feature_context
                        + " has fewer downloaders than swarm_size_min");
      result.features.push_back(std::move(feature));
    }
  return result;
}

inline swarm_dataset
load_swarm_dataset(const fs::path& path)
{ return parse_swarm_dataset(read_json_document(path), path.string()); }

inline network_profile
parse_network_profile(const rj::Document& document, const fs::path& path)
{
  const std::string context = path.string();
  network_require(document.IsObject(), context + " root must be an object");
  network_require(required_uint(document, "schema_version", context) == 1,
                  context + " uses an unsupported schema version");

  network_profile result;
  result.path = path;
  result.name = required_string(document, "name", context);
  const rj::Value& clustering = required_member(
    document, "clustering", context);
  const std::string clustering_context = context + ".clustering";
  result.source_h3_resolution = required_uint(
    clustering, "source_h3_resolution", clustering_context);
  result.parent_h3_resolution = required_uint(
    clustering, "parent_h3_resolution", clustering_context);
  result.marker_radius = required_number(
    clustering, "marker_radius_inches", clustering_context);
  result.minimum_tether = required_number(
    clustering, "minimum_tether_inches", clustering_context);

  const rj::Value& display = required_member(document, "display", context);
  const std::string display_context = context + ".display";
  result.maximum_labels = required_uint(
    display, "maximum_labels", display_context);
  result.minimum_nonzero_opacity = required_number(
    display, "minimum_nonzero_opacity", display_context);
  result.show_tethers = required_bool(display, "show_tethers", display_context);

  result.scale_reference = parse_counts(
    required_member(document, "scale_reference_p99", context),
    context + ".scale_reference_p99");

  const rj::Value& snapshot = required_member(document, "snapshot", context);
  const std::string snapshot_context = context + ".snapshot";
  result.archive = required_string(snapshot, "archive", snapshot_context);
  result.archive_sha256 = required_string(
    snapshot, "archive_sha256", snapshot_context);
  result.geojson_member = required_string(
    snapshot, "geojson_member", snapshot_context);
  result.geojson_sha256 = required_string(
    snapshot, "geojson_sha256", snapshot_context);
  result.source_repository = required_string(
    snapshot, "source_repository", snapshot_context);
  result.source_commit = required_string(
    snapshot, "source_commit", snapshot_context);
  result.license = required_string(snapshot, "license", snapshot_context);

  network_require(result.source_h3_resolution <= 15
                    && result.parent_h3_resolution
                         < result.source_h3_resolution,
                  clustering_context
                    + " must use a coarser valid parent H3 resolution");
  network_require(result.marker_radius > 0
                    && result.marker_radius <= 0.25,
                  clustering_context + ".marker_radius_inches is invalid");
  network_require(result.minimum_tether >= 0
                    && result.minimum_tether <= 2,
                  clustering_context + ".minimum_tether_inches is invalid");
  network_require(result.maximum_labels <= 500,
                  display_context + ".maximum_labels is excessive");
  network_require(result.minimum_nonzero_opacity > 0
                    && result.minimum_nonzero_opacity < 1,
                  display_context + ".minimum_nonzero_opacity is invalid");
  for (const metric_descriptor descriptor : metric_descriptors)
    network_require(metric_value(result.scale_reference, descriptor.metric) > 0,
                    context + ".scale_reference_p99."
                      + std::string(descriptor.field) + " must be positive");
  const auto lower_hex = [](const std::string_view value,
                            const std::size_t size) {
    return value.size() == size
      && std::all_of(value.begin(), value.end(), [](const char character) {
           return (character >= '0' && character <= '9')
             || (character >= 'a' && character <= 'f');
         });
  };
  network_require(lower_hex(result.archive_sha256, 64),
                  snapshot_context + ".archive_sha256 must be 64 lowercase hexadecimal characters");
  network_require(lower_hex(result.geojson_sha256, 64),
                  snapshot_context + ".geojson_sha256 must be 64 lowercase hexadecimal characters");
  network_require(lower_hex(result.source_commit, 40),
                  snapshot_context + ".source_commit must be a 40-character lowercase hexadecimal commit");
  network_require(!result.archive.empty() && !result.geojson_member.empty()
                    && !result.source_repository.empty()
                    && !result.license.empty(),
                  snapshot_context + " contains an empty provenance field");
  return result;
}

inline network_profile
load_network_profile(const fs::path& path)
{ return parse_network_profile(read_json_document(path), path); }

inline double
scaled_log_opacity(const std::uint64_t value, const std::uint64_t reference,
                   const double minimum_nonzero)
{
  if (value == 0)
    return 0;
  const double normalized = std::clamp(
    std::log1p(static_cast<double>(value))
      / std::log1p(static_cast<double>(reference)),
    0.0, 1.0);
  return minimum_nonzero + (1 - minimum_nonzero) * normalized;
}

} // namespace cart0freak0::network_generation

#endif
