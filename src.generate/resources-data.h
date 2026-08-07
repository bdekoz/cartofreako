// Strict Stage 12 resources profile and normalized country/spatial ingestion.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_RESOURCES_DATA_H
#define CART0FREAK0_RESOURCES_DATA_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iterator>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::resources_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
resources_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline constexpr std::array<std::string_view, 6> resource_family_ids {
  "resources-energy", "resources-food", "resources-fauna", "resources-flora",
  "resources-mineral", "resources-human",
};

enum class metric_status
{
  default_metric,
  released,
  available,
  planned,
  supplemental,
  research_gap,
};

enum class metric_scale
{
  linear,
  log1p,
};

struct source_definition
{
  std::string id;
  std::string organization;
  std::string title;
  std::string release;
  std::string url;
  std::string retrieved_at;
  std::string license;
  std::string sha256;
};

struct coverage_definition
{
  std::size_t covered_countries = 0;
  std::size_t mapped_countries = 0;
  double country_percent = 0;
  std::optional<double> population_percent;
  std::optional<double> output_percent;
  bool passes_non_sparse = false;
};

struct spatial_definition
{
  fs::path path;
  std::string sha256;
  std::size_t source_features = 0;
  std::size_t source_polygons = 0;
  std::size_t mapped_features = 0;
  double resolution_degrees = 0;
  std::string class_property;
  bool passes_non_sparse = false;
};

struct metric_definition
{
  std::string id;
  std::string title;
  std::string unit;
  std::string reference_period;
  std::string evidence_class;
  std::vector<std::string> source_ids;
  metric_status status = metric_status::planned;
  metric_scale scale = metric_scale::linear;
  std::string output_tag;
  std::optional<coverage_definition> coverage;
  std::optional<spatial_definition> spatial;
  std::string notes;
};

struct resource_palette
{
  std::array<int, 3> low {};
  std::array<int, 3> high {};
  std::array<int, 3> missing {};
};

struct resource_family
{
  std::string id;
  std::string title;
  std::string default_metric;
  resource_palette palette;
  std::vector<metric_definition> metrics;
};

struct country_value
{
  std::string family;
  std::string metric;
  std::string iso3;
  unsigned year = 0;
  double value = 0;
  std::string state;
};

struct resources_profile
{
  fs::path path;
  std::string name;
  std::string description;
  std::string snapshot_as_of;
  std::string missing_semantics;
  fs::path country_geometry_path;
  std::string country_geometry_sha256;
  std::string country_geometry_source_id;
  fs::path values_path;
  std::string values_sha256;
  std::vector<source_definition> sources;
  std::vector<resource_family> families;
  std::vector<country_value> values;
};

inline bool
is_identifier(const std::string_view value)
{
  if (value.empty() || value.front() == '-' || value.back() == '-')
    return false;
  return std::all_of(value.begin(), value.end(), [](const unsigned char item) {
    return std::islower(item) || std::isdigit(item) || item == '-';
  });
}

inline bool
is_iso3(const std::string_view value)
{
  return value.size() == 3
         && std::all_of(value.begin(), value.end(), [](const unsigned char item) {
              return item >= 'A' && item <= 'Z';
            });
}

inline bool
is_hex_digest(const std::string_view value)
{
  return value.size() == 64
         && std::all_of(value.begin(), value.end(), [](const unsigned char item) {
              return std::isdigit(item) || (item >= 'a' && item <= 'f');
            });
}

inline void
reject_resource_duplicate_members(const rj::Value& value,
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
          resources_require(names.insert(name).second,
            context + " contains duplicate member '" + name + "'");
          reject_resource_duplicate_members(member->value,
                                             context + "." + name);
        }
    }
  else if (value.IsArray())
    for (rj::SizeType index = 0; index != value.Size(); ++index)
      reject_resource_duplicate_members(
        value[index], context + "[" + std::to_string(index) + "]");
}

inline rj::Document
read_resources_document(const fs::path& path,
                        const std::uintmax_t maximum_size)
{
  std::error_code error;
  const std::uintmax_t size = fs::file_size(path, error);
  resources_require(!error, "failed to stat resources data " + path.string());
  resources_require(size > 0 && size <= maximum_size,
                    "resources data has an invalid or excessive size: "
                      + path.string());
  std::ifstream input {path, std::ios::binary};
  resources_require(input.good(), "failed to open resources data "
                                     + path.string());
  const std::string json {std::istreambuf_iterator<char>(input),
                          std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  resources_require(!document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  reject_resource_duplicate_members(document, path.string());
  return document;
}

inline bool
contains_name(const std::initializer_list<std::string_view> values,
              const std::string_view candidate)
{
  return std::find(values.begin(), values.end(), candidate) != values.end();
}

inline void
require_members(const rj::Value& object,
                const std::initializer_list<std::string_view> required,
                const std::initializer_list<std::string_view> optional,
                const std::string_view context)
{
  resources_require(object.IsObject(), std::string(context)
                                        + " must be an object");
  for (auto member = object.MemberBegin(); member != object.MemberEnd();
       ++member)
    {
      const std::string_view name {
        member->name.GetString(), member->name.GetStringLength()};
      resources_require(contains_name(required, name)
                          || contains_name(optional, name),
                        std::string(context) + " contains unknown member '"
                          + std::string(name) + "'");
    }
  for (const std::string_view name : required)
    resources_require(object.HasMember(std::string(name).c_str()),
                      std::string(context) + " is missing '"
                        + std::string(name) + "'");
}

inline const rj::Value&
required_member(const rj::Value& object, const char* name,
                const std::string_view context)
{
  resources_require(object.HasMember(name), std::string(context)
                                           + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  resources_require(value.IsString(), std::string(context) + "." + name
                                        + " must be a string");
  const std::string result(value.GetString(), value.GetStringLength());
  resources_require(!result.empty(), std::string(context) + "." + name
                                       + " must not be empty");
  return result;
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  resources_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                    std::string(context) + "." + name
                      + " must be a finite number");
  return value.GetDouble();
}

inline std::size_t
required_size(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  resources_require(value.IsUint64(), std::string(context) + "." + name
                                         + " must be an unsigned integer");
  return static_cast<std::size_t>(value.GetUint64());
}

inline std::optional<double>
optional_nullable_number(const rj::Value& object, const char* name,
                         const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  if (value.IsNull())
    return std::nullopt;
  resources_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                    std::string(context) + "." + name
                      + " must be null or a finite number");
  return value.GetDouble();
}

inline metric_status
parse_metric_status(const std::string_view value)
{
  if (value == "default") return metric_status::default_metric;
  if (value == "released") return metric_status::released;
  if (value == "available") return metric_status::available;
  if (value == "planned") return metric_status::planned;
  if (value == "supplemental") return metric_status::supplemental;
  if (value == "research-gap") return metric_status::research_gap;
  throw std::runtime_error("unknown resources metric status '"
                           + std::string(value) + "'");
}

inline std::string_view
metric_status_name(const metric_status value)
{
  switch (value)
    {
    case metric_status::default_metric: return "default";
    case metric_status::released: return "released";
    case metric_status::available: return "available";
    case metric_status::planned: return "planned";
    case metric_status::supplemental: return "supplemental";
    case metric_status::research_gap: return "research-gap";
    }
  throw std::logic_error("unhandled resources metric status");
}

inline metric_scale
parse_metric_scale(const std::string_view value)
{
  if (value == "linear") return metric_scale::linear;
  if (value == "log1p") return metric_scale::log1p;
  throw std::runtime_error("unknown resources metric scale '"
                           + std::string(value) + "'");
}

inline std::array<int, 3>
parse_color(const rj::Value& value, const std::string_view context)
{
  resources_require(value.IsArray() && value.Size() == 3,
                    std::string(context) + " must be an RGB triplet");
  std::array<int, 3> result {};
  for (rj::SizeType index = 0; index != value.Size(); ++index)
    {
      resources_require(value[index].IsInt()
                          && value[index].GetInt() >= 0
                          && value[index].GetInt() <= 255,
                        std::string(context) + " components must be in [0,255]");
      result[index] = value[index].GetInt();
    }
  return result;
}

inline coverage_definition
parse_coverage(const rj::Value& value, const std::string_view context)
{
  require_members(value,
    {"covered_countries", "mapped_countries", "country_percent",
     "population_percent", "output_percent", "passes_non_sparse"}, {},
    context);
  coverage_definition result;
  result.covered_countries = required_size(value, "covered_countries", context);
  result.mapped_countries = required_size(value, "mapped_countries", context);
  result.country_percent = required_number(value, "country_percent", context);
  result.population_percent = optional_nullable_number(
    value, "population_percent", context);
  result.output_percent = optional_nullable_number(value, "output_percent", context);
  const rj::Value& passes = required_member(value, "passes_non_sparse", context);
  resources_require(passes.IsBool(), std::string(context)
                                      + ".passes_non_sparse must be boolean");
  result.passes_non_sparse = passes.GetBool();
  resources_require(result.mapped_countries != 0
                      && result.covered_countries <= result.mapped_countries,
                    std::string(context) + " has invalid country counts");
  const double calculated = 100.0 * result.covered_countries
    / result.mapped_countries;
  resources_require(std::abs(calculated - result.country_percent) <= 0.0015,
                    std::string(context) + " country percentage disagrees with counts");
  for (const std::optional<double> percentage
       : {std::optional<double> {result.country_percent},
          result.population_percent, result.output_percent})
    if (percentage.has_value())
      resources_require(*percentage >= 0 && *percentage <= 100.001,
                        std::string(context) + " percentage is outside [0,100]");
  const bool calculated_gate = result.output_percent.has_value()
    ? *result.output_percent >= 90.0
    : result.population_percent.has_value()
      && result.country_percent >= 80.0
      && *result.population_percent >= 90.0;
  resources_require(result.passes_non_sparse == calculated_gate,
                    std::string(context)
                      + " non-sparse result disagrees with its percentages");
  return result;
}

inline spatial_definition
parse_spatial(const rj::Value& value, const fs::path& profile_directory,
              const std::string_view context)
{
  require_members(value,
    {"path", "sha256", "source_features", "source_polygons",
     "mapped_features", "resolution_degrees", "class_property",
     "passes_non_sparse"}, {}, context);
  spatial_definition result;
  result.path = profile_directory / required_string(value, "path", context);
  result.sha256 = required_string(value, "sha256", context);
  result.source_features = required_size(value, "source_features", context);
  result.source_polygons = required_size(value, "source_polygons", context);
  result.mapped_features = required_size(value, "mapped_features", context);
  result.resolution_degrees = required_number(
    value, "resolution_degrees", context);
  result.class_property = required_string(value, "class_property", context);
  const rj::Value& passes = required_member(
    value, "passes_non_sparse", context);
  resources_require(passes.IsBool(), std::string(context)
                                      + ".passes_non_sparse must be boolean");
  result.passes_non_sparse = passes.GetBool();
  resources_require(is_hex_digest(result.sha256),
                    std::string(context) + " has an invalid SHA-256");
  resources_require(result.source_features != 0
                      && result.source_polygons != 0
                      && result.mapped_features != 0
                      && result.resolution_degrees > 0
                      && result.resolution_degrees <= 5,
                    std::string(context) + " has invalid spatial statistics");
  resources_require(fs::is_regular_file(result.path),
                    "missing resources spatial data " + result.path.string());
  return result;
}

inline resources_profile
load_resources_profile(const fs::path& configured_path)
{
  const fs::path path = fs::absolute(configured_path);
  rj::Document document = read_resources_document(path, 2U * 1024U * 1024U);
  require_members(document,
    {"schema", "name", "description", "snapshot_as_of", "missing_semantics",
     "country_geometry", "values", "sources", "families"}, {}, path.string());
  resources_require(required_string(document, "schema", path.string())
                      == "cartofreako-resources-profile-v3",
                    "unsupported resources profile schema");

  resources_profile result;
  result.path = path;
  result.name = required_string(document, "name", path.string());
  result.description = required_string(document, "description", path.string());
  result.snapshot_as_of = required_string(document, "snapshot_as_of", path.string());
  result.missing_semantics = required_string(document, "missing_semantics", path.string());

  const rj::Value& geometry = document["country_geometry"];
  require_members(geometry, {"path", "sha256", "source_id"}, {},
                  "resources.country_geometry");
  result.country_geometry_path = path.parent_path()
    / required_string(geometry, "path", "resources.country_geometry");
  result.country_geometry_sha256 = required_string(
    geometry, "sha256", "resources.country_geometry");
  result.country_geometry_source_id = required_string(
    geometry, "source_id", "resources.country_geometry");
  resources_require(is_hex_digest(result.country_geometry_sha256),
                    "resources country geometry has an invalid SHA-256");
  resources_require(fs::is_regular_file(result.country_geometry_path),
                    "missing resources country geometry "
                      + result.country_geometry_path.string());

  const rj::Value& values = document["values"];
  require_members(values, {"path", "sha256"}, {}, "resources.values");
  result.values_path = path.parent_path()
    / required_string(values, "path", "resources.values");
  result.values_sha256 = required_string(values, "sha256", "resources.values");
  resources_require(is_hex_digest(result.values_sha256),
                    "resources values have an invalid SHA-256");

  const rj::Value& sources = document["sources"];
  resources_require(sources.IsArray() && !sources.Empty(),
                    "resources.sources must be a nonempty array");
  std::unordered_set<std::string> source_ids;
  for (rj::SizeType index = 0; index != sources.Size(); ++index)
    {
      const std::string context = "resources.sources["
        + std::to_string(index) + "]";
      const rj::Value& source = sources[index];
      require_members(source,
        {"id", "organization", "title", "release", "url", "retrieved_at",
         "license", "sha256"}, {}, context);
      source_definition parsed {
        required_string(source, "id", context),
        required_string(source, "organization", context),
        required_string(source, "title", context),
        required_string(source, "release", context),
        required_string(source, "url", context),
        required_string(source, "retrieved_at", context),
        required_string(source, "license", context),
        required_string(source, "sha256", context),
      };
      resources_require(is_identifier(parsed.id), context + " has invalid id");
      resources_require(is_hex_digest(parsed.sha256)
                          || parsed.sha256 == "not-yet-ingested",
                        context + " has invalid SHA-256/status");
      resources_require(source_ids.insert(parsed.id).second,
                        "duplicate resources source id '" + parsed.id + "'");
      result.sources.push_back(std::move(parsed));
    }
  resources_require(source_ids.contains(result.country_geometry_source_id),
                    "resources geometry references an unknown source");

  const rj::Value& families = document["families"];
  resources_require(families.IsArray()
                      && families.Size() == resource_family_ids.size(),
                    "resources.families must contain exactly six families");
  std::unordered_set<std::string> family_ids;
  for (rj::SizeType family_index = 0;
       family_index != families.Size(); ++family_index)
    {
      const std::string context = "resources.families["
        + std::to_string(family_index) + "]";
      const rj::Value& family = families[family_index];
      require_members(family,
        {"id", "title", "default_metric", "palette", "metrics"}, {}, context);
      resource_family parsed;
      parsed.id = required_string(family, "id", context);
      parsed.title = required_string(family, "title", context);
      parsed.default_metric = required_string(family, "default_metric", context);
      resources_require(std::find(resource_family_ids.begin(),
                                  resource_family_ids.end(), parsed.id)
                          != resource_family_ids.end(),
                        context + " has unknown family id '" + parsed.id + "'");
      resources_require(family_ids.insert(parsed.id).second,
                        "duplicate resources family id '" + parsed.id + "'");

      const rj::Value& palette = family["palette"];
      require_members(palette, {"low", "high", "missing"}, {},
                      context + ".palette");
      parsed.palette.low = parse_color(palette["low"], context + ".palette.low");
      parsed.palette.high = parse_color(palette["high"], context + ".palette.high");
      parsed.palette.missing = parse_color(
        palette["missing"], context + ".palette.missing");

      const rj::Value& metrics = family["metrics"];
      resources_require(metrics.IsArray() && !metrics.Empty(),
                        context + ".metrics must be a nonempty array");
      std::unordered_set<std::string> metric_ids;
      std::size_t default_count = 0;
      for (rj::SizeType metric_index = 0;
           metric_index != metrics.Size(); ++metric_index)
        {
          const std::string metric_context = context + ".metrics["
            + std::to_string(metric_index) + "]";
          const rj::Value& item = metrics[metric_index];
          require_members(item,
            {"id", "title", "unit", "reference_period", "evidence_class",
             "source_ids", "status", "scale", "output_tag", "coverage",
             "spatial", "notes"}, {}, metric_context);
          metric_definition parsed_metric;
          parsed_metric.id = required_string(item, "id", metric_context);
          parsed_metric.title = required_string(item, "title", metric_context);
          parsed_metric.unit = required_string(item, "unit", metric_context);
          parsed_metric.reference_period = required_string(
            item, "reference_period", metric_context);
          parsed_metric.evidence_class = required_string(
            item, "evidence_class", metric_context);
          parsed_metric.status = parse_metric_status(
            required_string(item, "status", metric_context));
          parsed_metric.scale = parse_metric_scale(
            required_string(item, "scale", metric_context));
          const rj::Value& output_tag = item["output_tag"];
          resources_require(output_tag.IsString(), metric_context
                                                    + ".output_tag must be a string");
          parsed_metric.output_tag.assign(output_tag.GetString(),
                                          output_tag.GetStringLength());
          parsed_metric.notes = required_string(item, "notes", metric_context);
          resources_require(is_identifier(parsed_metric.id),
                            metric_context + " has invalid metric id");
          resources_require(metric_ids.insert(parsed_metric.id).second,
                            "duplicate metric id '" + parsed_metric.id
                              + "' in " + parsed.id);

          const rj::Value& metric_sources = item["source_ids"];
          resources_require(metric_sources.IsArray(), metric_context
                                                        + ".source_ids must be an array");
          for (const rj::Value& source_id : metric_sources.GetArray())
            {
              resources_require(source_id.IsString(), metric_context
                                 + ".source_ids must contain strings");
              std::string id(source_id.GetString(), source_id.GetStringLength());
              resources_require(source_ids.contains(id), metric_context
                                 + " references unknown source '" + id + "'");
              resources_require(std::find(parsed_metric.source_ids.begin(),
                                          parsed_metric.source_ids.end(), id)
                                  == parsed_metric.source_ids.end(),
                                metric_context + " repeats source '" + id + "'");
              parsed_metric.source_ids.push_back(std::move(id));
            }

          if (item["coverage"].IsNull())
            parsed_metric.coverage = std::nullopt;
          else
            parsed_metric.coverage = parse_coverage(
              item["coverage"], metric_context + ".coverage");
          if (item["spatial"].IsNull())
            parsed_metric.spatial = std::nullopt;
          else
            parsed_metric.spatial = parse_spatial(
              item["spatial"], path.parent_path(),
              metric_context + ".spatial");
          if (parsed_metric.status == metric_status::default_metric)
            {
              ++default_count;
              resources_require(parsed_metric.id == parsed.default_metric,
                                context + " default status/id mismatch");
            }
          const bool released
            = parsed_metric.status == metric_status::default_metric
              || parsed_metric.status == metric_status::released;
          if (released)
            {
              resources_require(!parsed_metric.output_tag.empty()
                                  && is_identifier(parsed_metric.output_tag),
                                metric_context + " needs a valid output_tag");
              resources_require(parsed_metric.coverage.has_value()
                                  != parsed_metric.spatial.has_value(),
                                metric_context
                                  + " needs exactly one release definition");
              resources_require(
                (parsed_metric.coverage.has_value()
                   && parsed_metric.coverage->passes_non_sparse)
                  || (parsed_metric.spatial.has_value()
                      && parsed_metric.spatial->passes_non_sparse),
                metric_context + " must pass the non-sparse release gate");
              resources_require(!parsed_metric.source_ids.empty(),
                                metric_context + " needs a source");
            }
          else
            {
              resources_require(parsed_metric.output_tag.empty(), metric_context
                               + " unreleased metric must not select an output_tag");
              resources_require(!parsed_metric.coverage.has_value()
                                  && !parsed_metric.spatial.has_value(),
                                metric_context
                                  + " unreleased metric has release metadata");
            }
          parsed.metrics.push_back(std::move(parsed_metric));
        }
      resources_require(default_count == 1,
                        context + " must have exactly one default metric");
      result.families.push_back(std::move(parsed));
    }
  for (const std::string_view expected : resource_family_ids)
    resources_require(family_ids.contains(std::string(expected)),
                      "resources profile is missing family '"
                        + std::string(expected) + "'");

  rj::Document values_document = read_resources_document(
    result.values_path, 8U * 1024U * 1024U);
  require_members(values_document, {"schema", "snapshot_as_of", "records"}, {},
                  result.values_path.string());
  resources_require(required_string(values_document, "schema",
                                     result.values_path.string())
                      == "cartofreako-resources-values-v3",
                    "unsupported resources values schema");
  resources_require(required_string(values_document, "snapshot_as_of",
                                     result.values_path.string())
                      == result.snapshot_as_of,
                    "resources profile and values snapshot dates differ");
  const rj::Value& records = values_document["records"];
  resources_require(records.IsArray() && !records.Empty(),
                    "resources values records must be a nonempty array");
  std::unordered_set<std::string> keys;
  for (rj::SizeType index = 0; index != records.Size(); ++index)
    {
      const std::string context = "resources.values.records["
        + std::to_string(index) + "]";
      const rj::Value& item = records[index];
      require_members(item, {"family", "metric", "iso3", "year", "value", "state"},
                      {}, context);
      country_value parsed {
        required_string(item, "family", context),
        required_string(item, "metric", context),
        required_string(item, "iso3", context),
        0,
        required_number(item, "value", context),
        required_string(item, "state", context),
      };
      const rj::Value& year = item["year"];
      resources_require(year.IsUint() && year.GetUint() >= 1900
                          && year.GetUint() <= 2026,
                        context + ".year is outside the accepted range");
      parsed.year = year.GetUint();
      resources_require(is_iso3(parsed.iso3), context + " has invalid ISO3 code");
      const auto family = std::find_if(result.families.begin(), result.families.end(),
        [&](const resource_family& candidate) { return candidate.id == parsed.family; });
      resources_require(family != result.families.end(),
                        context + " references unknown family '" + parsed.family + "'");
      const auto metric = std::find_if(family->metrics.begin(), family->metrics.end(),
        [&](const metric_definition& candidate) { return candidate.id == parsed.metric; });
      resources_require(metric != family->metrics.end(),
                        context + " references unknown metric '" + parsed.metric + "'");
      resources_require(metric->status == metric_status::default_metric
                          || metric->status == metric_status::released
                          || metric->status == metric_status::available,
                        context + " supplies values for an unreleased metric");
      resources_require(parsed.value >= 0,
                        context + ".value must be nonnegative");
      resources_require(parsed.state == "reported-or-estimated"
                          || parsed.state == "estimated"
                          || parsed.state == "derived",
                        context + " has unknown observation state");
      const std::string key = parsed.family + "/" + parsed.metric + "/" + parsed.iso3;
      resources_require(keys.insert(key).second,
                        "duplicate resources country value '" + key + "'");
      result.values.push_back(std::move(parsed));
    }

  for (const resource_family& family : result.families)
    for (const metric_definition& metric : family.metrics)
      if (metric.status == metric_status::default_metric
          || metric.status == metric_status::released)
        {
          const std::size_t actual = static_cast<std::size_t>(std::count_if(
            result.values.begin(), result.values.end(),
            [&](const country_value& value) {
              return value.family == family.id && value.metric == metric.id;
            }));
          if (metric.coverage.has_value())
            resources_require(actual == metric.coverage->covered_countries,
                              family.id + "/" + metric.id
                                + " value count disagrees with coverage");
          else
            resources_require(actual == 0 && metric.spatial.has_value(),
                              family.id + "/" + metric.id
                                + " spatial metric has country values");
        }
  return result;
}

inline std::optional<std::string>
canonical_resource_family(const std::string_view input)
{
  std::string value;
  value.reserve(input.size());
  for (const unsigned char character : input)
    value.push_back(character == '_'
                      ? '-' : static_cast<char>(std::tolower(character)));
  if (value == "energy" || value == "resources-energy")
    return "resources-energy";
  if (value == "food" || value == "resources-food")
    return "resources-food";
  if (value == "fauna" || value == "resources-fauna"
      || value == "fisheries" || value == "reefs")
    return "resources-fauna";
  if (value == "flora" || value == "resources-flora"
      || value == "ressources-flora")
    return "resources-flora";
  if (value == "mineral" || value == "minerals"
      || value == "resources-mineral")
    return "resources-mineral";
  if (value == "human" || value == "resources-human")
    return "resources-human";
  return std::nullopt;
}

inline const resource_family&
find_resource_family(const resources_profile& profile,
                     const std::string_view input)
{
  const std::optional<std::string> canonical = canonical_resource_family(input);
  resources_require(canonical.has_value(), "unknown resources family '"
                                             + std::string(input) + "'");
  const auto family = std::find_if(profile.families.begin(), profile.families.end(),
    [&](const resource_family& candidate) { return candidate.id == *canonical; });
  resources_require(family != profile.families.end(),
                    "resources profile omits family '" + *canonical + "'");
  return *family;
}

inline const metric_definition&
default_resource_metric(const resource_family& family)
{
  const auto metric = std::find_if(family.metrics.begin(), family.metrics.end(),
    [&](const metric_definition& candidate) {
      return candidate.id == family.default_metric;
    });
  resources_require(metric != family.metrics.end(),
                    family.id + " omits its default metric");
  return *metric;
}

inline const metric_definition&
find_resource_metric(const resource_family& family,
                     const std::string_view metric_id)
{
  const auto metric = std::find_if(
    family.metrics.begin(), family.metrics.end(),
    [&](const metric_definition& candidate) {
      return candidate.id == metric_id;
    });
  resources_require(metric != family.metrics.end(),
                    family.id + " has no metric '"
                      + std::string(metric_id) + "'");
  resources_require(metric->status == metric_status::default_metric
                      || metric->status == metric_status::released,
                    family.id + "/" + metric->id + " is not released");
  return *metric;
}

inline std::vector<const country_value*>
resource_metric_values(const resources_profile& profile,
                       const resource_family& family,
                       const metric_definition& metric)
{
  std::vector<const country_value*> result;
  for (const country_value& value : profile.values)
    if (value.family == family.id && value.metric == metric.id)
      result.push_back(&value);
  return result;
}

} // namespace cart0freak0::resources_generation

#endif // CART0FREAK0_RESOURCES_DATA_H
