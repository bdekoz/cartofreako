// Strict Network Groundstations profile and Starlink gateway ingestion.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_GROUNDSTATIONS_DATA_H
#define CART0FREAK0_NETWORK_GROUNDSTATIONS_DATA_H 1

#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::network_groundstations_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
network_groundstations_require(const bool condition,
                               const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline rj::Document
read_json_document(const fs::path& path)
{
  std::ifstream input {path};
  network_groundstations_require(input.good(),
    "failed to open " + path.string());
  const std::string content {std::istreambuf_iterator<char>(input),
                             std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(content.c_str());
  network_groundstations_require(!document.HasParseError(),
    path.string() + " is not valid JSON: "
      + rj::GetParseError_En(document.GetParseError()));
  return document;
}

inline const rj::Value&
required_member(const rj::Value& object, const char* name,
                const std::string& context)
{
  network_groundstations_require(object.IsObject()
                             && object.HasMember(name),
    context + " is missing required member " + name);
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  network_groundstations_require(value.IsString(),
    context + "." + name + " must be a string");
  return value.GetString();
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  network_groundstations_require(value.IsNumber(),
    context + "." + name + " must be a number");
  return value.GetDouble();
}

inline std::uint64_t
required_uint(const rj::Value& object, const char* name,
              const std::string& context)
{
  const double value = required_number(object, name, context);
  network_groundstations_require(value >= 0
                             && std::floor(value) == value,
    context + "." + name + " must be a non-negative integer");
  return static_cast<std::uint64_t>(value);
}

struct groundstation_link
{
  std::string name;
  double longitude = 0;
  double latitude = 0;
  std::vector<std::pair<double, double>> path;
};

struct groundstations_dataset
{
  std::string id;
  std::string datestamp;
  std::string source;
  std::string source_sha256;
  std::string schema;
  std::vector<groundstation_link> stations;
};

struct groundstations_profile
{
  fs::path path;
  std::string name;
  double marker_radius = 0.026;
  double minimum_nonzero_opacity = 0.18;
  std::uint64_t expected_features = 0;
  std::string source_repository;
  std::string source_commit;
  std::string source_license;
  std::string datestamp;
  std::string gateways_sha256;
};

inline groundstations_profile
parse_groundstations_profile(const rj::Document& document,
                             const fs::path& path)
{
  const std::string context = path.string();
  network_groundstations_require(document.IsObject(),
    context + " root must be an object");
  network_groundstations_require(
    required_uint(document, "schema_version", context) == 1,
    context + " uses an unsupported schema version");

  groundstations_profile result;
  result.path = path;
  result.name = required_string(document, "name", context);

  const rj::Value& clustering = required_member(document, "clustering",
                                                context);
  const std::string clustering_context = context + ".clustering";
  result.marker_radius = required_number(
    clustering, "marker_radius_inches", clustering_context);
  result.minimum_nonzero_opacity = required_number(
    clustering, "minimum_nonzero_opacity", clustering_context);

  const rj::Value& display = required_member(document, "display", context);
  result.expected_features = required_uint(
    display, "expected_features", context + ".display");

  const rj::Value& source = required_member(document, "source", context);
  const std::string source_context = context + ".source";
  result.source_repository = required_string(
    source, "repository", source_context);
  result.source_commit = required_string(source, "commit", source_context);
  result.source_license = required_string(source, "license", source_context);
  result.datestamp = required_string(source, "datestamp", source_context);
  result.gateways_sha256 = required_string(
    source, "gateways_sha256", source_context);

  network_groundstations_require(result.marker_radius > 0
                             && result.marker_radius <= 0.25,
    clustering_context + ".marker_radius_inches is invalid");
  network_groundstations_require(result.minimum_nonzero_opacity > 0
                             && result.minimum_nonzero_opacity < 1,
    clustering_context + ".minimum_nonzero_opacity is invalid");
  return result;
}

inline void
append_coordinate(std::vector<std::pair<double, double>>& path,
                  const rj::Value& coordinate, const std::string& context)
{
  network_groundstations_require(coordinate.IsArray()
                             && coordinate.Size() >= 2
                             && coordinate[0].IsNumber()
                             && coordinate[1].IsNumber(),
    context + " coordinate must begin with [lon, lat]");
  const double longitude = coordinate[0].GetDouble();
  const double latitude = coordinate[1].GetDouble();
  network_groundstations_require(std::isfinite(longitude)
                             && longitude >= -180 && longitude <= 180
                             && std::isfinite(latitude)
                             && latitude >= -90 && latitude <= 90,
    context + " has out-of-range coordinates");
  path.emplace_back(longitude, latitude);
}

inline groundstations_dataset
parse_groundstations_dataset(const rj::Document& document,
                             const fs::path& path,
                             const groundstations_profile& profile)
{
  const std::string context = path.string();
  network_groundstations_require(document.IsObject(),
    context + " root must be an object");
  network_groundstations_require(
    required_string(document, "type", context) == "FeatureCollection",
    context + " must be a GeoJSON FeatureCollection");

  groundstations_dataset result;
  result.id = required_string(document, "name", context);
  result.schema = document.HasMember("schema")
    ? required_string(document, "schema", context)
    : std::string("starlink-global-gateways-pops");
  result.datestamp = profile.datestamp;
  result.source = profile.source_repository;
  result.source_sha256 = profile.gateways_sha256;

  const rj::Value& features = required_member(document, "features", context);
  network_groundstations_require(features.IsArray(),
    context + ".features must be an array");
  network_groundstations_require(features.Size() == profile.expected_features,
    context + ".features count differs from profile.expected_features");

  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string feature_context
        = context + ".features[" + std::to_string(index) + "]";
      network_groundstations_require(feature.IsObject(),
        feature_context + " must be an object");
      const rj::Value& properties = required_member(feature, "properties",
                                                    feature_context);
      const rj::Value& geometry = required_member(feature, "geometry",
                                                  feature_context);
      const std::string name = required_string(properties, "Name",
                                               feature_context);
      const std::string type = required_string(geometry, "type",
                                               feature_context);
      const rj::Value& coordinates = required_member(geometry, "coordinates",
                                                     feature_context);

      groundstation_link station;
      station.name = name;
      if (type == "Point")
        {
          append_coordinate(station.path, coordinates, feature_context);
        }
      else if (type == "LineString")
        {
          network_groundstations_require(coordinates.IsArray()
                                     && coordinates.Size() >= 2,
            feature_context + " LineString must have at least two points");
          for (rj::SizeType point = 0; point < coordinates.Size(); ++point)
            append_coordinate(station.path, coordinates[point],
                              feature_context);
        }
      else
        network_groundstations_require(false,
          feature_context + " uses unsupported geometry type " + type);

      station.longitude = station.path.front().first;
      station.latitude = station.path.front().second;
      result.stations.push_back(std::move(station));
    }

  network_groundstations_require(!result.stations.empty(),
    context + " contains no groundstation features");
  return result;
}

inline groundstations_profile
load_groundstations_profile(const fs::path& path)
{
  return parse_groundstations_profile(read_json_document(path), path);
}

inline groundstations_dataset
load_groundstations_dataset(const fs::path& path,
                            const groundstations_profile& profile)
{
  return parse_groundstations_dataset(
    read_json_document(path), path, profile);
}

} // namespace cart0freak0::network_groundstations_generation

#endif
