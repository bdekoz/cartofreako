// Profile and prepared H3 snapshot loading for cloud-atmosphere generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_CLOUD_ATMOSPHERE_DATA_H
#define CART0FREAK0_CLOUD_ATMOSPHERE_DATA_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <numbers>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

#include "generation-instant.h"

namespace cart0freak0::cloud_atmosphere_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
atmosphere_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

struct rgb_color
{
  unsigned red;
  unsigned green;
  unsigned blue;
};

enum class aggregation_kind
{
  mean,
  mode,
  cloud_fraction,
};

enum class freshness_policy
{
  maximum_age,
  latest_available,
};

struct quality_rule
{
  std::vector<std::string> variable_candidates;
  unsigned bit_offset = 0;
  unsigned bit_width = 0;
  std::vector<unsigned> accepted_values;
};

struct layer_definition
{
  std::string id;
  std::string property;
  std::string title;
  std::string unit;
  std::string source_id;
  bool enabled;
  aggregation_kind aggregation;
  std::vector<std::string> variable_candidates;
  std::optional<quality_rule> quality;
  double scale_min;
  double scale_max;
  double maximum_age_hours;
  freshness_policy freshness;
  double opacity;
  rgb_color color;
};

struct source_definition
{
  std::string id;
  std::string title;
  std::string access;
  std::string status;
  std::string coverage;
  std::string url;
  std::string collection;
  std::string license_url;
};

struct atmosphere_profile
{
  fs::path path;
  std::string name;
  std::string description;
  std::string time_policy;
  std::string source_selection;
  unsigned h3_resolution;
  double minimum_valid_fraction;
  unsigned maximum_samples_per_axis;
  double solar_contour_step_degrees;
  bool show_legend;
  bool show_cloud_type;
  std::string prepared_snapshot;
  std::vector<layer_definition> layers;
  std::vector<source_definition> sources;
};

struct observation_metadata
{
  std::string source_id;
  generation_time::instant start;
  generation_time::instant end;
  std::string fetched_at_utc;
  std::string source_url;
  std::string sha256;
  std::string coverage;
};

struct atmosphere_cell
{
  H3Index h3 = H3_NULL;
  double latitude = 0;
  double longitude = 0;
  std::vector<std::optional<double>> values;
  std::vector<double> valid_fractions;
};

struct atmosphere_dataset
{
  fs::path path;
  std::string schema;
  bool fixture = false;
  std::string prepared_at_utc;
  generation_time::instant source_selection_process_start {};
  unsigned h3_resolution = 0;
  std::string missing_semantics;
  std::vector<observation_metadata> observations;
  std::vector<atmosphere_cell> cells;
};

inline rj::Document
read_json_document(const fs::path& path)
{
  std::ifstream input {path, std::ios::binary};
  atmosphere_require(input.good(), "failed to open JSON file " + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  atmosphere_require(
    !document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  atmosphere_require(document.IsObject(),
                     path.string() + " JSON root must be an object");
  return document;
}

inline const rj::Value&
required_member(const rj::Value& object, const char* name,
                const std::string_view context)
{
  atmosphere_require(object.IsObject() && object.HasMember(name),
                     std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  atmosphere_require(value.IsString(),
                     context + "." + name + " must be a string");
  return value.GetString();
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  atmosphere_require(value.IsNumber(),
                     context + "." + name + " must be a number");
  atmosphere_require(std::isfinite(value.GetDouble()),
                     context + "." + name + " must be finite");
  return value.GetDouble();
}

inline unsigned
required_uint(const rj::Value& object, const char* name,
              const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  atmosphere_require(value.IsUint(),
                     context + "." + name + " must be an unsigned integer");
  return value.GetUint();
}

inline bool
required_bool(const rj::Value& object, const char* name,
              const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  atmosphere_require(value.IsBool(),
                     context + "." + name + " must be a boolean");
  return value.GetBool();
}

inline std::vector<std::string>
required_strings(const rj::Value& object, const char* name,
                 const std::string& context)
{
  const rj::Value& value = required_member(object, name, context);
  atmosphere_require(value.IsArray() && !value.Empty(),
                     context + "." + name
                       + " must be a nonempty string array");
  std::vector<std::string> result;
  result.reserve(value.Size());
  for (const rj::Value& element : value.GetArray())
    {
      atmosphere_require(element.IsString(),
                         context + "." + name + " must contain strings");
      result.emplace_back(element.GetString());
    }
  return result;
}

inline rgb_color
parse_color(const std::string& text, const std::string& context)
{
  atmosphere_require(text.size() == 7 && text.front() == '#',
                     context + " must be #RRGGBB");
  const auto nibble = [&](const char value) -> unsigned {
    if (value >= '0' && value <= '9')
      return static_cast<unsigned>(value - '0');
    if (value >= 'a' && value <= 'f')
      return static_cast<unsigned>(value - 'a' + 10);
    if (value >= 'A' && value <= 'F')
      return static_cast<unsigned>(value - 'A' + 10);
    atmosphere_require(false, context + " contains a non-hex digit");
    return 0;
  };
  const auto component = [&](const std::size_t offset) {
    return 16 * nibble(text[offset]) + nibble(text[offset + 1]);
  };
  return {component(1), component(3), component(5)};
}

inline aggregation_kind
parse_aggregation(const std::string_view value, const std::string& context)
{
  if (value == "mean")
    return aggregation_kind::mean;
  if (value == "mode")
    return aggregation_kind::mode;
  if (value == "cloud-fraction")
    return aggregation_kind::cloud_fraction;
  throw std::runtime_error(context + " has unsupported aggregation '"
                           + std::string(value) + "'");
}

inline freshness_policy
parse_freshness_policy(const rj::Value& value, const std::string& context)
{
  if (!value.HasMember("freshness_policy"))
    return freshness_policy::maximum_age;
  const std::string policy = required_string(
    value, "freshness_policy", context);
  if (policy == "maximum-age")
    return freshness_policy::maximum_age;
  if (policy == "latest-available")
    return freshness_policy::latest_available;
  throw std::runtime_error(context + " has unsupported freshness policy '"
                           + policy + "'");
}

inline quality_rule
parse_quality_rule(const rj::Value& value, const std::string& context)
{
  quality_rule result;
  result.variable_candidates = required_strings(
    value, "variable_candidates", context);
  result.bit_offset = required_uint(value, "bit_offset", context);
  result.bit_width = required_uint(value, "bit_width", context);
  atmosphere_require(result.bit_width > 0 && result.bit_width <= 16
                       && result.bit_offset + result.bit_width <= 32,
                     context + " has an invalid bit range");
  const rj::Value& accepted = required_member(value, "accepted_values", context);
  atmosphere_require(accepted.IsArray() && !accepted.Empty(),
                     context + ".accepted_values must be a nonempty array");
  const std::uint64_t maximum = (std::uint64_t {1} << result.bit_width) - 1;
  for (const rj::Value& item : accepted.GetArray())
    {
      atmosphere_require(item.IsUint64() && item.GetUint64() <= maximum,
                         context + ".accepted_values exceeds the bit range");
      result.accepted_values.push_back(static_cast<unsigned>(item.GetUint64()));
    }
  return result;
}

inline layer_definition
parse_layer(const rj::Value& value, const std::string& context)
{
  layer_definition result {
    required_string(value, "id", context),
    required_string(value, "property", context),
    required_string(value, "title", context),
    required_string(value, "unit", context),
    required_string(value, "source", context),
    required_bool(value, "enabled", context),
    parse_aggregation(required_string(value, "aggregation", context), context),
    required_strings(value, "variable_candidates", context),
    std::nullopt,
    required_number(value, "scale_min", context),
    required_number(value, "scale_max", context),
    required_number(value, "maximum_age_hours", context),
    parse_freshness_policy(value, context),
    required_number(value, "opacity", context),
    parse_color(required_string(value, "color", context), context + ".color"),
  };
  if (value.HasMember("quality"))
    result.quality = parse_quality_rule(value["quality"], context + ".quality");
  atmosphere_require(!result.id.empty() && !result.property.empty(),
                     context + " id/property must not be empty");
  atmosphere_require(result.scale_max > result.scale_min,
                     context + " scale_max must exceed scale_min");
  atmosphere_require(result.maximum_age_hours > 0,
                     context + " maximum_age_hours must be positive");
  atmosphere_require(result.opacity >= 0 && result.opacity <= 1,
                     context + " opacity must be in [0, 1]");
  return result;
}

inline source_definition
parse_source(const rj::Value& value, const std::string& context)
{
  return {
    required_string(value, "id", context),
    required_string(value, "title", context),
    required_string(value, "access", context),
    required_string(value, "status", context),
    required_string(value, "coverage", context),
    required_string(value, "url", context),
    required_string(value, "collection", context),
    required_string(value, "license_url", context),
  };
}

inline atmosphere_profile
load_atmosphere_profile(const fs::path& path)
{
  const rj::Document document = read_json_document(path);
  atmosphere_require(required_uint(document, "schema_version", "profile") == 1,
                     "unsupported cloud-atmosphere profile schema");
  const rj::Value& time = required_member(document, "time", "profile");
  const rj::Value& aggregation = required_member(
    document, "aggregation", "profile");
  const rj::Value& display = required_member(document, "display", "profile");
  const rj::Value& data = required_member(document, "data", "profile");
  atmosphere_profile result {
    path,
    required_string(document, "name", "profile"),
    required_string(document, "description", "profile"),
    required_string(time, "calculation", "profile.time"),
    required_string(time, "source_selection", "profile.time"),
    required_uint(aggregation, "h3_resolution", "profile.aggregation"),
    required_number(aggregation, "minimum_valid_fraction",
                    "profile.aggregation"),
    required_uint(aggregation, "maximum_samples_per_axis",
                  "profile.aggregation"),
    required_number(display, "solar_contour_step_degrees", "profile.display"),
    required_bool(display, "show_legend", "profile.display"),
    required_bool(display, "show_cloud_type", "profile.display"),
    required_string(data, "prepared_snapshot", "profile.data"),
    {}, {},
  };
  atmosphere_require(result.time_policy == "process-start",
                     "profile.time.calculation must be process-start");
  atmosphere_require(result.source_selection == "latest-not-after",
                     "profile.time.source_selection must be latest-not-after");
  atmosphere_require(result.h3_resolution <= 15,
                     "profile H3 resolution is invalid");
  atmosphere_require(result.minimum_valid_fraction > 0
                       && result.minimum_valid_fraction <= 1,
                     "minimum_valid_fraction must be in (0, 1]");
  atmosphere_require(result.maximum_samples_per_axis >= 32,
                     "maximum_samples_per_axis must be at least 32");
  atmosphere_require(result.solar_contour_step_degrees >= 0.25
                       && result.solar_contour_step_degrees <= 10,
                     "solar_contour_step_degrees must be in [0.25, 10]");

  const rj::Value& sources = required_member(document, "sources", "profile");
  atmosphere_require(sources.IsArray() && !sources.Empty(),
                     "profile.sources must be a nonempty array");
  std::unordered_set<std::string> source_ids;
  for (const rj::Value& source : sources.GetArray())
    {
      source_definition parsed = parse_source(
        source, "profile.sources[" + std::to_string(result.sources.size()) + "]");
      atmosphere_require(source_ids.emplace(parsed.id).second,
                         "profile contains duplicate source " + parsed.id);
      result.sources.push_back(std::move(parsed));
    }

  const rj::Value& layers = required_member(document, "layers", "profile");
  atmosphere_require(layers.IsArray() && !layers.Empty(),
                     "profile.layers must be a nonempty array");
  std::unordered_set<std::string> layer_ids;
  std::unordered_set<std::string> properties;
  for (const rj::Value& layer : layers.GetArray())
    {
      layer_definition parsed = parse_layer(
        layer, "profile.layers[" + std::to_string(result.layers.size()) + "]");
      atmosphere_require(source_ids.contains(parsed.source_id),
                         "layer " + parsed.id + " names an unknown source");
      atmosphere_require(layer_ids.emplace(parsed.id).second,
                         "profile contains duplicate layer " + parsed.id);
      atmosphere_require(properties.emplace(parsed.property).second,
                         "profile contains duplicate property " + parsed.property);
      result.layers.push_back(std::move(parsed));
    }
  return result;
}

inline H3Index
parse_h3(const std::string& text, const std::string& context)
{
  H3Index result = H3_NULL;
  atmosphere_require(stringToH3(text.c_str(), &result) == E_SUCCESS
                       && result != H3_NULL && isValidCell(result),
                     context + " contains an invalid H3 index");
  return result;
}

inline std::size_t
layer_index(const atmosphere_profile& profile, const std::string_view property)
{
  const auto found = std::find_if(
    profile.layers.begin(), profile.layers.end(),
    [property](const layer_definition& layer) {
      return layer.property == property;
    });
  atmosphere_require(found != profile.layers.end(),
                     "unknown atmosphere property " + std::string(property));
  return static_cast<std::size_t>(found - profile.layers.begin());
}

inline atmosphere_dataset
load_atmosphere_dataset(const fs::path& path,
                        const atmosphere_profile& profile)
{
  const rj::Document document = read_json_document(path);
  atmosphere_require(required_string(document, "type", path.string())
                       == "FeatureCollection",
                     path.string() + " must be a GeoJSON FeatureCollection");
  const rj::Value& metadata = required_member(document, "metadata", path.string());
  atmosphere_dataset result;
  result.path = path;
  result.schema = required_string(metadata, "schema", "metadata");
  atmosphere_require(result.schema
                       == "cartofreako-cloud-atmosphere-snapshot-v1",
                     "unsupported cloud-atmosphere snapshot schema");
  result.fixture = required_bool(metadata, "fixture", "metadata");
  result.prepared_at_utc = required_string(
    metadata, "prepared_at_utc", "metadata");
  static_cast<void>(generation_time::parse_timestamp(result.prepared_at_utc));
  result.source_selection_process_start = generation_time::parse_timestamp(
    required_string(metadata, "source_selection_process_start_utc",
                    "metadata"));
  result.h3_resolution = required_uint(metadata, "h3_resolution", "metadata");
  result.missing_semantics = required_string(
    metadata, "missing_semantics", "metadata");
  atmosphere_require(result.h3_resolution == profile.h3_resolution,
                     "profile and snapshot H3 resolutions differ");
  atmosphere_require(result.missing_semantics == "unobserved-not-zero",
                     "snapshot missing semantics must be unobserved-not-zero");

  const rj::Value& observations = required_member(
    metadata, "observations", "metadata");
  atmosphere_require(observations.IsArray() && !observations.Empty(),
                     "metadata.observations must be a nonempty array");
  std::unordered_set<std::string> observed_sources;
  for (const rj::Value& observation : observations.GetArray())
    {
      const std::string context = "metadata.observations["
        + std::to_string(result.observations.size()) + "]";
      observation_metadata parsed {
        required_string(observation, "source", context),
        generation_time::parse_timestamp(required_string(
          observation, "start_utc", context)),
        generation_time::parse_timestamp(required_string(
          observation, "end_utc", context)),
        required_string(observation, "fetched_at_utc", context),
        required_string(observation, "source_url", context),
        required_string(observation, "sha256", context),
        required_string(observation, "coverage", context),
      };
      atmosphere_require(parsed.end.value >= parsed.start.value,
                         context + " ends before it starts");
      atmosphere_require(observed_sources.emplace(parsed.source_id).second,
                         "snapshot repeats observation source "
                           + parsed.source_id);
      result.observations.push_back(std::move(parsed));
    }

  const rj::Value& features = required_member(document, "features", path.string());
  atmosphere_require(features.IsArray() && !features.Empty(),
                     "snapshot features must be a nonempty array");
  std::unordered_set<H3Index> seen;
  result.cells.reserve(features.Size());
  for (const rj::Value& feature : features.GetArray())
    {
      const std::string context = "features["
        + std::to_string(result.cells.size()) + "]";
      atmosphere_require(required_string(feature, "type", context) == "Feature",
                         context + " must be a GeoJSON Feature");
      const rj::Value& geometry = required_member(feature, "geometry", context);
      atmosphere_require(required_string(geometry, "type", context + ".geometry")
                           == "Point",
                         context + " geometry must be Point");
      const rj::Value& coordinates = required_member(
        geometry, "coordinates", context + ".geometry");
      atmosphere_require(coordinates.IsArray() && coordinates.Size() == 2
                           && coordinates[0].IsNumber()
                           && coordinates[1].IsNumber(),
                         context + " coordinates must be [longitude, latitude]");
      const rj::Value& properties_value = required_member(
        feature, "properties", context);
      atmosphere_cell cell;
      cell.h3 = parse_h3(required_string(
        properties_value, "h3", context + ".properties"), context);
      atmosphere_require(getResolution(cell.h3)
                           == static_cast<int>(profile.h3_resolution),
                         context + " H3 resolution differs from profile");
      atmosphere_require(seen.emplace(cell.h3).second,
                         context + " repeats an H3 cell");
      cell.longitude = coordinates[0].GetDouble();
      cell.latitude = coordinates[1].GetDouble();
      atmosphere_require(std::isfinite(cell.longitude)
                           && std::isfinite(cell.latitude)
                           && cell.longitude >= -180 && cell.longitude <= 180
                           && cell.latitude >= -90 && cell.latitude <= 90,
                         context + " coordinates are invalid");
      LatLng center {};
      atmosphere_require(cellToLatLng(cell.h3, &center) == E_SUCCESS,
                         context + " H3 center conversion failed");
      const double h3_latitude = center.lat * 180.0 / std::numbers::pi;
      const double h3_longitude = center.lng * 180.0 / std::numbers::pi;
      atmosphere_require(std::abs(cell.latitude - h3_latitude) < 1e-5
                           && std::abs(cell.longitude - h3_longitude) < 1e-5,
                         context + " coordinates are not the H3 center");

      const rj::Value& values = required_member(
        properties_value, "values", context + ".properties");
      const rj::Value& valid = required_member(
        properties_value, "valid_fraction", context + ".properties");
      atmosphere_require(values.IsObject() && valid.IsObject(),
                         context + " values/valid_fraction must be objects");
      cell.values.resize(profile.layers.size());
      cell.valid_fractions.resize(profile.layers.size());
      bool any_value = false;
      for (std::size_t index = 0; index < profile.layers.size(); ++index)
        {
          const layer_definition& layer = profile.layers[index];
          if (!values.HasMember(layer.property.c_str()))
            continue;
          const rj::Value& value = values[layer.property.c_str()];
          atmosphere_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                             context + " has invalid " + layer.property);
          atmosphere_require(valid.HasMember(layer.property.c_str())
                               && valid[layer.property.c_str()].IsNumber(),
                             context + " lacks valid fraction for "
                               + layer.property);
          const double fraction = valid[layer.property.c_str()].GetDouble();
          atmosphere_require(fraction >= profile.minimum_valid_fraction
                               && fraction <= 1,
                             context + " has invalid fraction for "
                               + layer.property);
          cell.values[index] = value.GetDouble();
          cell.valid_fractions[index] = fraction;
          any_value = true;
        }
      atmosphere_require(any_value, context + " contains no observations");
      result.cells.push_back(std::move(cell));
    }
  std::sort(result.cells.begin(), result.cells.end(),
            [](const atmosphere_cell& left, const atmosphere_cell& right) {
              return left.h3 < right.h3;
            });
  return result;
}

inline const observation_metadata&
observation_for(const atmosphere_dataset& dataset,
                const std::string_view source_id)
{
  const auto found = std::find_if(
    dataset.observations.begin(), dataset.observations.end(),
    [source_id](const observation_metadata& observation) {
      return observation.source_id == source_id;
    });
  atmosphere_require(found != dataset.observations.end(),
                     "snapshot has no observation for source "
                       + std::string(source_id));
  return *found;
}

inline void
validate_observation_times(const atmosphere_profile& profile,
                           const atmosphere_dataset& dataset,
                           const generation_time::instant& process_start,
                           const bool enforce_freshness = true)
{
  atmosphere_require(dataset.source_selection_process_start.value
                       <= process_start.value,
                     "snapshot source selection occurred after the generation "
                     "process instant");
  for (const layer_definition& layer : profile.layers)
    {
      if (!layer.enabled)
        continue;
      const observation_metadata& observation = observation_for(
        dataset, layer.source_id);
      atmosphere_require(
        observation.end.value
          <= dataset.source_selection_process_start.value,
        "source " + layer.source_id
          + " ends after the snapshot source-selection instant");
      atmosphere_require(observation.end.value <= process_start.value,
                         "source " + layer.source_id
                           + " ends after the generation process instant");
      const double age = generation_time::age_hours(
        process_start, observation.end);
      if (enforce_freshness
          && layer.freshness == freshness_policy::maximum_age)
        atmosphere_require(age <= layer.maximum_age_hours,
                           "source " + layer.source_id + " is stale for layer "
                             + layer.id + " (" + std::to_string(age)
                             + " hours old; maximum "
                             + std::to_string(layer.maximum_age_hours) + ")");
    }
}

} // namespace cart0freak0::cloud_atmosphere_generation

#endif // CART0FREAK0_CLOUD_ATMOSPHERE_DATA_H
