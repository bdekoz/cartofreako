// Strict Anthropocene profile and normalized H3 GeoJSON ingestion.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ANTHROPOCENE_DATA_H
#define CART0FREAK0_ANTHROPOCENE_DATA_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::anthropocene_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
anthropocene_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

struct rgb_color
{
  unsigned short red = 0;
  unsigned short green = 0;
  unsigned short blue = 0;
};

enum class marker_shape
{
  triangle_up,
  triangle_down,
  diamond,
  circle,
  hexagon,
  ring,
  square,
  star,
  cross_square,
};

struct metric_definition
{
  std::string id;
  std::string property;
  std::string family;
  std::string title;
  bool enabled = true;
  std::uint64_t scale_days = 1;
  rgb_color color;
  marker_shape shape = marker_shape::circle;
  std::vector<std::string> sources;
};

struct source_definition
{
  std::string id;
  std::string status;
  std::string coverage;
  std::optional<std::string> available_through;
  std::string url;
};

struct future_phase
{
  std::string id;
  std::string status;
  std::string reason;
};

struct anthropocene_profile
{
  fs::path path;
  std::string name;
  std::string description;
  int calendar_year = 2026;
  std::string snapshot_as_of_utc;
  bool partial_year = true;
  unsigned h3_resolution = 4;
  std::string count_mode;
  unsigned minimum_record_years = 30;
  unsigned minimum_valid_days_per_year = 183;
  double heavy_precipitation_minimum_mm = 10;
  double heavy_precipitation_percentile = 0.95;
  int baseline_start = 1991;
  int baseline_end = 2020;
  unsigned pm25_aqi_threshold_exclusive = 100;
  double marker_radius = 0.055;
  double minimum_nonzero_opacity = 0.35;
  bool show_legend = true;
  std::string geojson;
  std::string geojson_sha256;
  std::vector<metric_definition> metrics;
  std::vector<source_definition> sources;
  std::vector<future_phase> future_phases;
};

struct anthropocene_feature
{
  H3Index h3 = H3_NULL;
  double longitude = 0;
  double latitude = 0;
  std::vector<std::uint64_t> counts;
};

struct source_statistics
{
  std::uint64_t ghcn_stations = 0;
  std::uint64_t ghcn_eligible_temperature_stations = 0;
  std::uint64_t ghcn_eligible_precipitation_stations = 0;
  std::uint64_t epa_rows = 0;
  std::uint64_t epa_exceedance_site_days = 0;
  std::uint64_t hms_polygons = 0;
  std::uint64_t hms_centroid_fallbacks = 0;
  std::uint64_t storm_events = 0;
  std::uint64_t storm_events_with_locations = 0;
  std::uint64_t cwfis_files = 0;
  std::uint64_t cwfis_rows = 0;
  std::uint64_t firms_rows = 0;
  std::uint64_t firms_files = 0;
  std::uint64_t firms_unique_days = 0;
  std::uint64_t firms_north_america_rows = 0;
  std::uint64_t firms_south_america_rows = 0;
  std::uint64_t firms_europe_rows = 0;
  std::uint64_t firms_africa_rows = 0;
  std::uint64_t firms_northern_asia_rows = 0;
  std::uint64_t firms_east_asia_rows = 0;
  std::uint64_t firms_oceania_rows = 0;
};

struct anthropocene_dataset
{
  fs::path path;
  std::string schema;
  int calendar_year = 0;
  std::string snapshot_as_of_utc;
  bool partial_year = true;
  unsigned h3_resolution = 0;
  std::string count_mode;
  std::string missing_semantics;
  std::vector<std::uint64_t> reported_metric_totals;
  std::vector<std::uint64_t> reported_metric_feature_counts;
  source_statistics statistics;
  std::vector<anthropocene_feature> features;
};

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
          anthropocene_require(names.insert(name).second,
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
                   const std::uintmax_t maximum_size = 32U * 1024U * 1024U)
{
  std::error_code error;
  const std::uintmax_t size = fs::file_size(path, error);
  anthropocene_require(!error, "failed to stat JSON file " + path.string());
  anthropocene_require(size > 0 && size <= maximum_size,
    "JSON file has an invalid or excessive size: " + path.string());
  std::ifstream input {path, std::ios::binary};
  anthropocene_require(input.good(), "failed to open JSON file " + path.string());
  const std::string json {std::istreambuf_iterator<char>(input),
                          std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  anthropocene_require(!document.HasParseError(),
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
  anthropocene_require(object.IsObject() && object.HasMember(name),
    std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsString(), std::string(context) + "." + name
                                           + " must be a string");
  return {value.GetString(), value.GetStringLength()};
}

inline std::uint64_t
required_uint64(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsUint64(), std::string(context) + "." + name
                                           + " must be an unsigned integer");
  return value.GetUint64();
}

inline unsigned
required_uint(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const std::uint64_t value = required_uint64(object, name, context);
  anthropocene_require(value <= std::numeric_limits<unsigned>::max(),
                       std::string(context) + "." + name + " is too large");
  return static_cast<unsigned>(value);
}

inline int
required_int(const rj::Value& object, const char* name,
             const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsInt(), std::string(context) + "." + name
                                         + " must be an integer");
  return value.GetInt();
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                       std::string(context) + "." + name
                         + " must be a finite number");
  return value.GetDouble();
}

inline bool
required_bool(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsBool(), std::string(context) + "." + name
                                          + " must be a Boolean");
  return value.GetBool();
}

inline std::vector<std::string>
required_string_array(const rj::Value& object, const char* name,
                      const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  anthropocene_require(value.IsArray() && !value.Empty(),
                       std::string(context) + "." + name
                         + " must be a nonempty array");
  std::vector<std::string> result;
  for (const rj::Value& entry : value.GetArray())
    {
      anthropocene_require(entry.IsString(), std::string(context) + "." + name
                                              + " must contain strings");
      const std::string item(entry.GetString(), entry.GetStringLength());
      anthropocene_require(std::find(result.begin(), result.end(), item)
                             == result.end(),
                           std::string(context) + "." + name
                             + " contains duplicate '" + item + "'");
      result.push_back(item);
    }
  return result;
}

inline unsigned
hex_digit(const char value)
{
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'a' && value <= 'f') return 10 + value - 'a';
  if (value >= 'A' && value <= 'F') return 10 + value - 'A';
  throw std::runtime_error("profile color contains a non-hex digit");
}

inline rgb_color
parse_color(const std::string& value)
{
  anthropocene_require(value.size() == 7 && value[0] == '#',
                       "profile color must use #rrggbb");
  const auto channel = [&](const std::size_t offset) {
    return static_cast<unsigned short>(hex_digit(value[offset]) * 16
                                       + hex_digit(value[offset + 1]));
  };
  return {channel(1), channel(3), channel(5)};
}

inline marker_shape
parse_shape(const std::string_view value)
{
  if (value == "triangle-up") return marker_shape::triangle_up;
  if (value == "triangle-down") return marker_shape::triangle_down;
  if (value == "diamond") return marker_shape::diamond;
  if (value == "circle") return marker_shape::circle;
  if (value == "hexagon") return marker_shape::hexagon;
  if (value == "ring") return marker_shape::ring;
  if (value == "square") return marker_shape::square;
  if (value == "star") return marker_shape::star;
  if (value == "cross-square") return marker_shape::cross_square;
  throw std::runtime_error("profile contains unknown marker shape '"
                           + std::string(value) + "'");
}

inline source_definition
parse_source(const rj::Value& value, const std::size_t index)
{
  const std::string context = "sources[" + std::to_string(index) + "]";
  source_definition result;
  result.id = required_string(value, "id", context);
  result.status = required_string(value, "status", context);
  result.coverage = required_string(value, "coverage", context);
  const rj::Value& available = required_member(
    value, "available_through", context);
  anthropocene_require(available.IsNull() || available.IsString(),
                       context + ".available_through must be null or a string");
  if (available.IsString())
    result.available_through = std::string(
      available.GetString(), available.GetStringLength());
  result.url = required_string(value, "url", context);
  return result;
}

inline anthropocene_profile
load_anthropocene_profile(const fs::path& path)
{
  const rj::Document document = read_json_document(path, 1024U * 1024U);
  anthropocene_require(document.IsObject(), path.string() + " root must be an object");
  anthropocene_require(required_uint(document, "schema_version", path.string())
                         == 1,
                       "unsupported Anthropocene profile schema");
  anthropocene_profile result;
  result.path = path;
  result.name = required_string(document, "name", path.string());
  result.description = required_string(document, "description", path.string());

  const rj::Value& duration = required_member(document, "duration", path.string());
  anthropocene_require(required_string(duration, "type", "duration")
                         == "calendar-year",
                       "duration.type must be 'calendar-year'");
  result.calendar_year = required_int(duration, "year", "duration");
  anthropocene_require(result.calendar_year >= 1800
                         && result.calendar_year <= 2500,
                       "duration.year is outside the supported range");

  const rj::Value& snapshot = required_member(document, "snapshot", path.string());
  result.snapshot_as_of_utc = required_string(snapshot, "as_of_utc", "snapshot");
  result.partial_year = required_bool(snapshot, "partial_year", "snapshot");

  const rj::Value& aggregation = required_member(
    document, "aggregation", path.string());
  anthropocene_require(required_string(
                         aggregation, "spatial_index", "aggregation") == "H3",
                       "aggregation.spatial_index must be 'H3'");
  result.h3_resolution = required_uint(
    aggregation, "h3_resolution", "aggregation");
  anthropocene_require(result.h3_resolution <= 15,
                       "aggregation.h3_resolution exceeds H3's limit");
  result.count_mode = required_string(aggregation, "count_mode", "aggregation");

  const rj::Value& thresholds = required_member(
    document, "thresholds", path.string());
  result.minimum_record_years = required_uint(
    thresholds, "minimum_record_years", "thresholds");
  result.minimum_valid_days_per_year = required_uint(
    thresholds, "minimum_valid_days_per_year", "thresholds");
  result.heavy_precipitation_minimum_mm = required_number(
    thresholds, "heavy_precipitation_minimum_mm", "thresholds");
  result.heavy_precipitation_percentile = required_number(
    thresholds, "heavy_precipitation_percentile", "thresholds");
  result.baseline_start = required_int(
    thresholds, "heavy_precipitation_baseline_start", "thresholds");
  result.baseline_end = required_int(
    thresholds, "heavy_precipitation_baseline_end", "thresholds");
  result.pm25_aqi_threshold_exclusive = required_uint(
    thresholds, "pm25_aqi_threshold_exclusive", "thresholds");
  anthropocene_require(result.minimum_record_years > 0
                         && result.minimum_valid_days_per_year > 0,
                       "record-history thresholds must be positive");
  anthropocene_require(result.heavy_precipitation_minimum_mm >= 0
                         && result.heavy_precipitation_percentile > 0
                         && result.heavy_precipitation_percentile <= 1,
                       "heavy-precipitation thresholds are invalid");
  anthropocene_require(result.baseline_start <= result.baseline_end,
                       "heavy-precipitation baseline is reversed");

  const rj::Value& display = required_member(document, "display", path.string());
  result.marker_radius = required_number(display, "marker_radius", "display");
  result.minimum_nonzero_opacity = required_number(
    display, "minimum_nonzero_opacity", "display");
  result.show_legend = required_bool(display, "show_legend", "display");
  anthropocene_require(result.marker_radius > 0
                         && result.minimum_nonzero_opacity >= 0
                         && result.minimum_nonzero_opacity <= 1,
                       "display marker radius or opacity is invalid");

  const rj::Value& data = required_member(document, "data", path.string());
  result.geojson = required_string(data, "geojson", "data");
  result.geojson_sha256 = required_string(data, "sha256", "data");
  anthropocene_require(result.geojson_sha256.size() == 64,
                       "data.sha256 must contain 64 hexadecimal digits");
  for (const char digit : result.geojson_sha256)
    static_cast<void>(hex_digit(digit));

  const rj::Value& metrics = required_member(document, "metrics", path.string());
  anthropocene_require(metrics.IsArray() && !metrics.Empty()
                         && metrics.Size() <= 32,
                       "metrics must be a nonempty array of at most 32 entries");
  std::unordered_set<std::string> metric_ids;
  std::unordered_set<std::string> metric_properties;
  for (rj::SizeType index = 0; index < metrics.Size(); ++index)
    {
      const rj::Value& value = metrics[index];
      const std::string context = "metrics[" + std::to_string(index) + "]";
      metric_definition metric;
      metric.id = required_string(value, "id", context);
      metric.property = required_string(value, "property", context);
      metric.family = required_string(value, "family", context);
      metric.title = required_string(value, "title", context);
      metric.enabled = required_bool(value, "enabled", context);
      metric.scale_days = required_uint64(value, "scale_days", context);
      metric.color = parse_color(required_string(value, "color", context));
      metric.shape = parse_shape(required_string(value, "shape", context));
      metric.sources = required_string_array(value, "sources", context);
      anthropocene_require(metric_ids.insert(metric.id).second,
                           "duplicate metric id '" + metric.id + "'");
      anthropocene_require(metric_properties.insert(metric.property).second,
                           "duplicate metric property '" + metric.property + "'");
      anthropocene_require(metric.scale_days > 0,
                           context + ".scale_days must be positive");
      result.metrics.push_back(std::move(metric));
    }

  const rj::Value& sources = required_member(document, "sources", path.string());
  anthropocene_require(sources.IsArray() && !sources.Empty(),
                       "sources must be a nonempty array");
  std::unordered_set<std::string> source_ids;
  for (rj::SizeType index = 0; index < sources.Size(); ++index)
    {
      source_definition source = parse_source(sources[index], index);
      anthropocene_require(source_ids.insert(source.id).second,
                           "duplicate source id '" + source.id + "'");
      result.sources.push_back(std::move(source));
    }
  for (const metric_definition& metric : result.metrics)
    for (const std::string& source : metric.sources)
      anthropocene_require(source_ids.contains(source),
                           "metric '" + metric.id
                             + "' references unknown source '" + source + "'");

  const rj::Value& phases = required_member(
    document, "future_phases", path.string());
  anthropocene_require(phases.IsArray(), "future_phases must be an array");
  for (rj::SizeType index = 0; index < phases.Size(); ++index)
    {
      const std::string context = "future_phases[" + std::to_string(index) + "]";
      result.future_phases.push_back({
        required_string(phases[index], "id", context),
        required_string(phases[index], "status", context),
        required_string(phases[index], "reason", context),
      });
    }
  return result;
}

inline std::uint64_t
optional_count(const rj::Value& object, const std::string& name,
               const std::string& context)
{
  if (!object.HasMember(name.c_str()))
    return 0;
  const rj::Value& value = object[name.c_str()];
  anthropocene_require(value.IsUint64(), context + "." + name
                                          + " must be an unsigned integer");
  return value.GetUint64();
}

inline source_statistics
parse_source_statistics(const rj::Value& value)
{
  source_statistics result;
  result.ghcn_stations = required_uint64(value, "ghcn_stations", "source_statistics");
  result.ghcn_eligible_temperature_stations = required_uint64(
    value, "ghcn_eligible_temperature_stations", "source_statistics");
  result.ghcn_eligible_precipitation_stations = required_uint64(
    value, "ghcn_eligible_precipitation_stations", "source_statistics");
  result.epa_rows = required_uint64(value, "epa_rows", "source_statistics");
  result.epa_exceedance_site_days = required_uint64(
    value, "epa_exceedance_site_days", "source_statistics");
  result.hms_polygons = required_uint64(value, "hms_polygons", "source_statistics");
  result.hms_centroid_fallbacks = required_uint64(
    value, "hms_centroid_fallbacks", "source_statistics");
  result.storm_events = required_uint64(value, "storm_events", "source_statistics");
  result.storm_events_with_locations = required_uint64(
    value, "storm_events_with_locations", "source_statistics");
  result.cwfis_files = required_uint64(value, "cwfis_files", "source_statistics");
  result.cwfis_rows = required_uint64(value, "cwfis_rows", "source_statistics");
  result.firms_rows = required_uint64(value, "firms_rows", "source_statistics");
  result.firms_files = optional_count(
    value, "firms_files", "source_statistics");
  result.firms_unique_days = optional_count(
    value, "firms_unique_days", "source_statistics");
  result.firms_north_america_rows = optional_count(
    value, "firms_north_america_rows", "source_statistics");
  result.firms_south_america_rows = optional_count(
    value, "firms_south_america_rows", "source_statistics");
  result.firms_europe_rows = optional_count(
    value, "firms_europe_rows", "source_statistics");
  result.firms_africa_rows = optional_count(
    value, "firms_africa_rows", "source_statistics");
  result.firms_northern_asia_rows = optional_count(
    value, "firms_northern_asia_rows", "source_statistics");
  result.firms_east_asia_rows = optional_count(
    value, "firms_east_asia_rows", "source_statistics");
  result.firms_oceania_rows = optional_count(
    value, "firms_oceania_rows", "source_statistics");
  return result;
}

inline H3Index
parse_h3(const std::string& value, const std::string& context)
{
  H3Index result = H3_NULL;
  anthropocene_require(stringToH3(value.c_str(), &result) == E_SUCCESS
                         && result != H3_NULL && isValidCell(result),
                       context + " contains an invalid H3 index");
  return result;
}

inline anthropocene_dataset
load_anthropocene_dataset(const fs::path& path,
                          const anthropocene_profile& profile)
{
  const rj::Document document = read_json_document(path);
  anthropocene_require(document.IsObject()
                         && required_string(document, "type", path.string())
                              == "FeatureCollection",
                       path.string() + " must be a GeoJSON FeatureCollection");
  anthropocene_dataset result;
  result.path = path;
  const rj::Value& metadata = required_member(document, "metadata", path.string());
  result.schema = required_string(metadata, "schema", "metadata");
  anthropocene_require(result.schema
                         == "cartofreako-anthropocene-observations-v1",
                       "GeoJSON uses an unsupported Anthropocene schema");
  result.calendar_year = required_int(metadata, "calendar_year", "metadata");
  result.snapshot_as_of_utc = required_string(
    metadata, "snapshot_as_of_utc", "metadata");
  result.partial_year = required_bool(metadata, "partial_year", "metadata");
  result.h3_resolution = required_uint(metadata, "h3_resolution", "metadata");
  result.count_mode = required_string(metadata, "count_mode", "metadata");
  result.missing_semantics = required_string(
    metadata, "missing_semantics", "metadata");
  anthropocene_require(result.calendar_year == profile.calendar_year
                         && result.snapshot_as_of_utc
                              == profile.snapshot_as_of_utc
                         && result.partial_year == profile.partial_year
                         && result.h3_resolution == profile.h3_resolution,
                       "profile and GeoJSON duration/snapshot/aggregation differ");
  anthropocene_require(path.filename() == fs::path(profile.geojson).filename(),
                       "profile data.geojson does not name the input GeoJSON");

  const rj::Value& totals = required_member(
    metadata, "metric_cell_day_totals", "metadata");
  const rj::Value& feature_counts = required_member(
    metadata, "metric_feature_counts", "metadata");
  for (const metric_definition& metric : profile.metrics)
    {
      result.reported_metric_totals.push_back(
        required_uint64(totals, metric.property.c_str(),
                        "metadata.metric_cell_day_totals"));
      result.reported_metric_feature_counts.push_back(
        required_uint64(feature_counts, metric.property.c_str(),
                        "metadata.metric_feature_counts"));
    }
  result.statistics = parse_source_statistics(
    required_member(metadata, "source_statistics", "metadata"));

  const rj::Value& features = required_member(document, "features", path.string());
  anthropocene_require(features.IsArray() && !features.Empty(),
                       "GeoJSON features must be a nonempty array");
  anthropocene_require(required_uint64(metadata, "feature_count", "metadata")
                         == features.Size(),
                       "metadata feature_count differs from features array");
  result.features.reserve(features.Size());
  std::unordered_set<H3Index> unique_cells;
  std::vector<std::uint64_t> calculated_totals(profile.metrics.size());
  std::vector<std::uint64_t> calculated_feature_counts(profile.metrics.size());
  H3Index previous = H3_NULL;
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string context = "features[" + std::to_string(index) + "]";
      anthropocene_require(required_string(feature, "type", context) == "Feature",
                           context + " must be a Feature");
      const std::string id = required_string(feature, "id", context);
      const rj::Value& geometry = required_member(feature, "geometry", context);
      anthropocene_require(required_string(geometry, "type", context + ".geometry")
                             == "Point",
                           context + ".geometry must be a Point");
      const rj::Value& coordinates = required_member(
        geometry, "coordinates", context + ".geometry");
      anthropocene_require(coordinates.IsArray() && coordinates.Size() == 2
                             && coordinates[0].IsNumber()
                             && coordinates[1].IsNumber(),
                           context + ".geometry.coordinates must contain lon/lat");
      anthropocene_feature parsed;
      parsed.longitude = coordinates[0].GetDouble();
      parsed.latitude = coordinates[1].GetDouble();
      anthropocene_require(std::isfinite(parsed.longitude)
                             && std::isfinite(parsed.latitude)
                             && parsed.longitude >= -180
                             && parsed.longitude <= 180
                             && parsed.latitude >= -90
                             && parsed.latitude <= 90,
                           context + " coordinate is invalid");
      const rj::Value& properties = required_member(feature, "properties", context);
      const std::string property_h3 = required_string(
        properties, "h3", context + ".properties");
      anthropocene_require(id == property_h3,
                           context + " id and properties.h3 differ");
      parsed.h3 = parse_h3(id, context);
      anthropocene_require(getResolution(parsed.h3)
                             == static_cast<int>(profile.h3_resolution),
                           context + " has the wrong H3 resolution");
      anthropocene_require(unique_cells.insert(parsed.h3).second,
                           "GeoJSON contains duplicate H3 cell " + id);
      anthropocene_require(previous == H3_NULL || previous < parsed.h3,
                           "GeoJSON features are not sorted by H3 index");
      previous = parsed.h3;
      LatLng center {};
      anthropocene_require(cellToLatLng(parsed.h3, &center) == E_SUCCESS,
                           "failed to calculate center for " + id);
      anthropocene_require(std::abs(parsed.longitude - radsToDegs(center.lng))
                             < 1e-9
                             && std::abs(parsed.latitude - radsToDegs(center.lat))
                                  < 1e-9,
                           context + " Point is not the H3 cell center");
      parsed.counts.reserve(profile.metrics.size());
      bool nonzero = false;
      for (std::size_t metric_index = 0;
           metric_index < profile.metrics.size(); ++metric_index)
        {
          const std::uint64_t count = optional_count(
            properties, profile.metrics[metric_index].property,
            context + ".properties");
          parsed.counts.push_back(count);
          calculated_totals[metric_index] += count;
          if (count != 0)
            {
              ++calculated_feature_counts[metric_index];
              nonzero = true;
            }
        }
      anthropocene_require(nonzero, context + " has no observations");
      result.features.push_back(std::move(parsed));
    }
  anthropocene_require(calculated_totals == result.reported_metric_totals,
                       "GeoJSON metric cell-day totals do not verify");
  anthropocene_require(calculated_feature_counts
                         == result.reported_metric_feature_counts,
                       "GeoJSON metric feature counts do not verify");
  return result;
}

inline std::string
h3_string(const H3Index cell)
{
  std::array<char, 17> buffer {};
  anthropocene_require(h3ToString(cell, buffer.data(), buffer.size()) == E_SUCCESS,
                       "failed to format H3 index");
  return buffer.data();
}

inline std::size_t
metric_index(const anthropocene_profile& profile, const std::string_view id)
{
  for (std::size_t index = 0; index < profile.metrics.size(); ++index)
    if (profile.metrics[index].id == id)
      return index;
  throw std::runtime_error("profile is missing metric '" + std::string(id) + "'");
}

} // namespace cart0freak0::anthropocene_generation

#endif // CART0FREAK0_ANTHROPOCENE_DATA_H
