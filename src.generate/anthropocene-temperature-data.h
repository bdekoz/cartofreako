// Strict profile and normalized non-sparse CPC temperature-field loading.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ANTHROPOCENE_TEMPERATURE_DATA_H
#define CART0FREAK0_ANTHROPOCENE_TEMPERATURE_DATA_H 1

#include <algorithm>
#include <array>
#include <chrono>
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
#include <vector>

#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::anthropocene_temperature_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline void
temperature_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

struct temperature_profile
{
  fs::path path;
  std::string name;
  std::string description;
  int calendar_year = 0;
  bool partial_year = true;
  std::string snapshot_as_of_utc;
  std::string data_through;
  unsigned h3_resolution = 3;
  int baseline_start = 1979;
  int baseline_end = 0;
  unsigned minimum_history_years = 30;
  std::uint64_t high_scale_days = 8;
  std::uint64_t low_scale_days = 8;
  double minimum_nonzero_opacity = 0.34;
  double data_graphic_opacity = 0.30;
  bool show_legend = true;
  std::string geojson;
  std::string geojson_sha256;
  std::string source_manifest_sha256;
};

struct temperature_cell
{
  H3Index h3 = H3_NULL;
  double longitude = 0;
  double latitude = 0;
  std::uint64_t record_high_days = 0;
  std::uint64_t record_low_days = 0;
  std::uint64_t tmax_valid_days = 0;
  std::uint64_t tmin_valid_days = 0;
};

struct temperature_totals
{
  std::uint64_t record_high_days = 0;
  std::uint64_t record_low_days = 0;
  std::uint64_t tmax_valid_days = 0;
  std::uint64_t tmin_valid_days = 0;
};

struct temperature_dataset
{
  fs::path path;
  std::string schema;
  std::string evidence_class;
  std::string missing_semantics;
  std::string reporting_day;
  std::string source_grid_aggregation;
  int calendar_year = 0;
  bool partial_year = true;
  std::string snapshot_as_of_utc;
  std::string data_through;
  unsigned h3_resolution = 0;
  int baseline_start = 0;
  int baseline_end = 0;
  unsigned minimum_history_years = 0;
  std::string source_manifest_sha256;
  std::uint64_t covered_cell_count = 0;
  temperature_totals totals;
  std::vector<temperature_cell> cells;
};

inline void
reject_temperature_duplicates(const rj::Value& value,
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
          temperature_require(names.insert(name).second,
                              context + " contains duplicate member '"
                                + name + "'");
          reject_temperature_duplicates(member->value, context + "." + name);
        }
    }
  else if (value.IsArray())
    for (rj::SizeType index = 0; index < value.Size(); ++index)
      reject_temperature_duplicates(
        value[index], context + "[" + std::to_string(index) + "]");
}

inline rj::Document
read_temperature_json(const fs::path& path,
                      const std::uintmax_t maximum_size)
{
  std::error_code error;
  const std::uintmax_t size = fs::file_size(path, error);
  temperature_require(!error && size > 0 && size <= maximum_size,
                      "temperature JSON has invalid size: " + path.string());
  std::ifstream input {path, std::ios::binary};
  temperature_require(input.good(), "failed to open " + path.string());
  const std::string json {std::istreambuf_iterator<char>(input),
                          std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  temperature_require(!document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  temperature_require(document.IsObject(),
                      path.string() + " root must be an object");
  reject_temperature_duplicates(document, path.string());
  return document;
}

inline const rj::Value&
temperature_member(const rj::Value& object, const char* name,
                   const std::string_view context)
{
  temperature_require(object.IsObject() && object.HasMember(name),
                      std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
temperature_string(const rj::Value& object, const char* name,
                   const std::string_view context)
{
  const rj::Value& value = temperature_member(object, name, context);
  temperature_require(value.IsString(), std::string(context) + "." + name
                                           + " must be a string");
  return {value.GetString(), value.GetStringLength()};
}

inline std::uint64_t
temperature_uint64(const rj::Value& object, const char* name,
                   const std::string_view context)
{
  const rj::Value& value = temperature_member(object, name, context);
  temperature_require(value.IsUint64(), std::string(context) + "." + name
                                           + " must be unsigned");
  return value.GetUint64();
}

inline unsigned
temperature_uint(const rj::Value& object, const char* name,
                 const std::string_view context)
{
  const std::uint64_t value = temperature_uint64(object, name, context);
  temperature_require(value <= std::numeric_limits<unsigned>::max(),
                      std::string(context) + "." + name + " is too large");
  return static_cast<unsigned>(value);
}

inline int
temperature_int(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = temperature_member(object, name, context);
  temperature_require(value.IsInt(), std::string(context) + "." + name
                                        + " must be an integer");
  return value.GetInt();
}

inline bool
temperature_bool(const rj::Value& object, const char* name,
                 const std::string_view context)
{
  const rj::Value& value = temperature_member(object, name, context);
  temperature_require(value.IsBool(), std::string(context) + "." + name
                                         + " must be Boolean");
  return value.GetBool();
}

inline double
temperature_number(const rj::Value& object, const char* name,
                   const std::string_view context)
{
  const rj::Value& value = temperature_member(object, name, context);
  temperature_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                      std::string(context) + "." + name
                        + " must be a finite number");
  return value.GetDouble();
}

inline bool
temperature_sha256(const std::string_view text)
{
  return text.size() == 64
    && std::all_of(text.begin(), text.end(), [](const char digit) {
         return (digit >= '0' && digit <= '9')
           || (digit >= 'a' && digit <= 'f');
       });
}

inline std::chrono::sys_days
temperature_date(const std::string_view text, const std::string& context)
{
  temperature_require(text.size() == 10 && text[4] == '-' && text[7] == '-',
                      context + " must use YYYY-MM-DD");
  const auto part = [&](const std::size_t offset, const std::size_t length) {
    int result = 0;
    for (std::size_t index = 0; index < length; ++index)
      {
        const char digit = text[offset + index];
        temperature_require(digit >= '0' && digit <= '9',
                            context + " must use YYYY-MM-DD");
        result = result * 10 + digit - '0';
      }
    return result;
  };
  const std::chrono::year_month_day date {
    std::chrono::year {part(0, 4)},
    std::chrono::month {static_cast<unsigned>(part(5, 2))},
    std::chrono::day {static_cast<unsigned>(part(8, 2))},
  };
  temperature_require(date.ok(), context + " is not a calendar date");
  return std::chrono::sys_days {date};
}

inline unsigned
temperature_included_days(const temperature_profile& profile)
{
  const std::chrono::sys_days first {
    std::chrono::year {profile.calendar_year} / std::chrono::January / 1};
  return static_cast<unsigned>(
    (temperature_date(profile.data_through, "snapshot.data_through")
      - first).count() + 1);
}

inline temperature_profile
load_temperature_profile(const fs::path& path)
{
  const rj::Document document = read_temperature_json(path, 1024U * 1024U);
  temperature_require(temperature_int(document, "schema_version", path.string())
                        == 1,
                      "unsupported Anthropocene temperature profile schema");
  temperature_require(temperature_string(document, "product", path.string())
                        == "anthropocene-temperature-field",
                      "profile product is not anthropocene-temperature-field");
  temperature_profile result;
  result.path = path;
  result.name = temperature_string(document, "name", path.string());
  result.description = temperature_string(
    document, "description", path.string());

  const rj::Value& duration = temperature_member(
    document, "duration", path.string());
  temperature_require(temperature_string(duration, "type", "duration")
                        == "calendar-year",
                      "duration.type must be calendar-year");
  result.calendar_year = temperature_int(duration, "year", "duration");

  const rj::Value& snapshot = temperature_member(
    document, "snapshot", path.string());
  result.snapshot_as_of_utc = temperature_string(
    snapshot, "as_of_utc", "snapshot");
  result.data_through = temperature_string(
    snapshot, "data_through", "snapshot");
  result.partial_year = temperature_bool(
    snapshot, "partial_year", "snapshot");

  const rj::Value& aggregation = temperature_member(
    document, "aggregation", path.string());
  temperature_require(temperature_string(
                        aggregation, "spatial_index", "aggregation") == "H3",
                      "aggregation.spatial_index must be H3");
  temperature_require(temperature_string(
      aggregation, "source_grid_aggregation", "aggregation")
        == "mean-of-valid-grid-cell-centers",
      "unsupported temperature source-grid aggregation");
  result.h3_resolution = temperature_uint(
    aggregation, "h3_resolution", "aggregation");

  const rj::Value& records = temperature_member(
    document, "records", path.string());
  result.baseline_start = temperature_int(
    records, "baseline_start", "records");
  result.baseline_end = temperature_int(
    records, "baseline_end", "records");
  result.minimum_history_years = temperature_uint(
    records, "minimum_history_years", "records");
  temperature_require(temperature_string(records, "comparison", "records")
                        == "strict",
                      "records.comparison must be strict");

  const rj::Value& display = temperature_member(
    document, "display", path.string());
  result.high_scale_days = temperature_uint64(
    display, "high_scale_days", "display");
  result.low_scale_days = temperature_uint64(
    display, "low_scale_days", "display");
  result.minimum_nonzero_opacity = temperature_number(
    display, "minimum_nonzero_opacity", "display");
  result.data_graphic_opacity = temperature_number(
    display, "data_graphic_opacity", "display");
  result.show_legend = temperature_bool(display, "show_legend", "display");

  const rj::Value& source = temperature_member(
    document, "source", path.string());
  temperature_require(temperature_string(source, "id", "source")
                        == "noaa-cpc-global-temperature",
                      "unexpected temperature source id");
  result.source_manifest_sha256 = temperature_string(
    source, "manifest_sha256", "source");

  const rj::Value& data = temperature_member(document, "data", path.string());
  result.geojson = temperature_string(data, "geojson", "data");
  result.geojson_sha256 = temperature_string(data, "sha256", "data");

  temperature_require(result.calendar_year >= 1979
                        && result.calendar_year <= 2500,
                      "duration.year is outside the supported range");
  temperature_require(result.h3_resolution <= 15,
                      "aggregation.h3_resolution exceeds H3's limit");
  temperature_require(result.baseline_start == 1979
                        && result.baseline_end == result.calendar_year - 1,
                      "temperature record baseline is inconsistent");
  temperature_require(result.minimum_history_years > 0,
                      "minimum_history_years must be positive");
  temperature_require(result.high_scale_days > 1 && result.low_scale_days > 1
                        && result.minimum_nonzero_opacity >= 0
                        && result.minimum_nonzero_opacity <= 1
                        && result.data_graphic_opacity > 0
                        && result.data_graphic_opacity <= 1,
                      "temperature display scaling is invalid");
  temperature_require(temperature_sha256(result.source_manifest_sha256)
                        && temperature_sha256(result.geojson_sha256),
                      "temperature profile contains an invalid SHA-256");
  const std::chrono::year_month_day through {
    temperature_date(result.data_through, "snapshot.data_through")};
  temperature_require(static_cast<int>(through.year()) == result.calendar_year,
                      "snapshot.data_through is outside duration.year");
  const bool ends_year = static_cast<unsigned>(through.month()) == 12
    && static_cast<unsigned>(through.day()) == 31;
  temperature_require(result.partial_year != ends_year,
                      "snapshot.partial_year disagrees with data_through");
  return result;
}

inline H3Index
temperature_h3(const std::string& value, const std::string& context)
{
  H3Index result = H3_NULL;
  temperature_require(stringToH3(value.c_str(), &result) == E_SUCCESS
                        && result != H3_NULL && isValidCell(result),
                      context + " has an invalid H3 index");
  return result;
}

inline temperature_dataset
load_temperature_dataset(const fs::path& path,
                         const temperature_profile& profile)
{
  const rj::Document document = read_temperature_json(
    path, 128U * 1024U * 1024U);
  temperature_require(temperature_string(document, "type", path.string())
                        == "FeatureCollection",
                      path.string() + " must be a FeatureCollection");
  temperature_dataset result;
  result.path = path;
  const rj::Value& metadata = temperature_member(
    document, "metadata", path.string());
  result.schema = temperature_string(metadata, "schema", "metadata");
  result.evidence_class = temperature_string(
    metadata, "evidence_class", "metadata");
  result.calendar_year = temperature_int(
    metadata, "calendar_year", "metadata");
  result.snapshot_as_of_utc = temperature_string(
    metadata, "snapshot_as_of_utc", "metadata");
  result.data_through = temperature_string(
    metadata, "data_through", "metadata");
  result.partial_year = temperature_bool(
    metadata, "partial_year", "metadata");
  result.h3_resolution = temperature_uint(
    metadata, "h3_resolution", "metadata");
  result.source_grid_aggregation = temperature_string(
    metadata, "source_grid_aggregation", "metadata");
  result.reporting_day = temperature_string(
    metadata, "reporting_day", "metadata");
  temperature_require(temperature_string(
                        metadata, "record_comparison", "metadata") == "strict",
                      "metadata.record_comparison must be strict");
  result.baseline_start = temperature_int(
    metadata, "baseline_start", "metadata");
  result.baseline_end = temperature_int(
    metadata, "baseline_end", "metadata");
  result.minimum_history_years = temperature_uint(
    metadata, "minimum_history_years", "metadata");
  result.source_manifest_sha256 = temperature_string(
    metadata, "source_manifest_sha256", "metadata");
  result.missing_semantics = temperature_string(
    metadata, "missing_semantics", "metadata");
  result.covered_cell_count = temperature_uint64(
    metadata, "covered_cell_count", "metadata");
  const std::uint64_t feature_count = temperature_uint64(
    metadata, "feature_count", "metadata");
  const rj::Value& totals = temperature_member(
    metadata, "metric_totals", "metadata");
  result.totals.record_high_days = temperature_uint64(
    totals, "cpc_temperature_record_high_days", "metadata.metric_totals");
  result.totals.record_low_days = temperature_uint64(
    totals, "cpc_temperature_record_low_days", "metadata.metric_totals");
  result.totals.tmax_valid_days = temperature_uint64(
    totals, "cpc_tmax_valid_days", "metadata.metric_totals");
  result.totals.tmin_valid_days = temperature_uint64(
    totals, "cpc_tmin_valid_days", "metadata.metric_totals");

  temperature_require(result.schema
                        == "cartofreako-anthropocene-temperature-fields-v1",
                      "unsupported Anthropocene temperature field schema");
  temperature_require(result.evidence_class
                        == "observation-interpolated-analysis-field",
                      "unexpected temperature evidence class");
  temperature_require(result.calendar_year == profile.calendar_year
                        && result.snapshot_as_of_utc
                             == profile.snapshot_as_of_utc
                        && result.data_through == profile.data_through
                        && result.partial_year == profile.partial_year
                        && result.h3_resolution == profile.h3_resolution
                        && result.baseline_start == profile.baseline_start
                        && result.baseline_end == profile.baseline_end
                        && result.minimum_history_years
                             == profile.minimum_history_years
                        && result.source_manifest_sha256
                             == profile.source_manifest_sha256,
                      "temperature profile and dataset metadata differ");
  temperature_require(result.reporting_day == "06Z-to-06Z"
                        && result.source_grid_aggregation
                             == "mean-of-valid-grid-cell-centers",
                      "temperature field has an unexpected temporal or spatial contract");
  temperature_require(path.filename() == fs::path(profile.geojson).filename(),
                      "temperature profile does not name input GeoJSON");

  const rj::Value& features = temperature_member(
    document, "features", path.string());
  temperature_require(features.IsArray()
                        && feature_count == features.Size(),
                      "temperature feature_count differs from features");
  int64_t expected_cells = 0;
  temperature_require(getNumCells(profile.h3_resolution, &expected_cells)
                        == E_SUCCESS
                        && feature_count
                             == static_cast<std::uint64_t>(expected_cells),
                      "temperature field is not globally non-sparse");
  result.cells.reserve(features.Size());
  H3Index previous = H3_NULL;
  std::uint64_t calculated_covered = 0;
  temperature_totals calculated;
  const unsigned included_days = temperature_included_days(profile);
  for (rj::SizeType index = 0; index < features.Size(); ++index)
    {
      const rj::Value& feature = features[index];
      const std::string context = "features[" + std::to_string(index) + "]";
      temperature_require(temperature_string(feature, "type", context)
                            == "Feature",
                          context + " is not a Feature");
      const std::string id = temperature_string(feature, "id", context);
      const rj::Value& geometry = temperature_member(
        feature, "geometry", context);
      temperature_require(temperature_string(
                            geometry, "type", context + ".geometry") == "Point",
                          context + " geometry is not a Point");
      const rj::Value& coordinates = temperature_member(
        geometry, "coordinates", context + ".geometry");
      temperature_require(coordinates.IsArray() && coordinates.Size() == 2
                            && coordinates[0].IsNumber()
                            && coordinates[1].IsNumber(),
                          context + " coordinates must be lon/lat");
      const rj::Value& properties = temperature_member(
        feature, "properties", context);
      temperature_require(temperature_string(
                            properties, "h3", context + ".properties") == id,
                          context + " id and properties.h3 differ");
      temperature_cell cell;
      cell.h3 = temperature_h3(id, context);
      cell.longitude = coordinates[0].GetDouble();
      cell.latitude = coordinates[1].GetDouble();
      cell.record_high_days = temperature_uint64(
        properties, "cpc_temperature_record_high_days",
        context + ".properties");
      cell.record_low_days = temperature_uint64(
        properties, "cpc_temperature_record_low_days",
        context + ".properties");
      cell.tmax_valid_days = temperature_uint64(
        properties, "cpc_tmax_valid_days", context + ".properties");
      cell.tmin_valid_days = temperature_uint64(
        properties, "cpc_tmin_valid_days", context + ".properties");
      temperature_require(getResolution(cell.h3)
                            == static_cast<int>(profile.h3_resolution),
                          context + " has the wrong H3 resolution");
      temperature_require(previous == H3_NULL || previous < cell.h3,
                          "temperature features are not sorted by H3");
      previous = cell.h3;
      LatLng center {};
      temperature_require(cellToLatLng(cell.h3, &center) == E_SUCCESS,
                          "failed to calculate H3 center");
      temperature_require(std::abs(cell.longitude - radsToDegs(center.lng))
                             < 1e-9
                            && std::abs(cell.latitude - radsToDegs(center.lat))
                                 < 1e-9,
                          context + " Point is not the H3 center");
      temperature_require(cell.tmax_valid_days <= included_days
                            && cell.tmin_valid_days <= included_days
                            && cell.record_high_days <= cell.tmax_valid_days
                            && cell.record_low_days <= cell.tmin_valid_days,
                          context + " has impossible day counts");
      if (cell.tmax_valid_days != 0 || cell.tmin_valid_days != 0)
        ++calculated_covered;
      calculated.record_high_days += cell.record_high_days;
      calculated.record_low_days += cell.record_low_days;
      calculated.tmax_valid_days += cell.tmax_valid_days;
      calculated.tmin_valid_days += cell.tmin_valid_days;
      result.cells.push_back(cell);
    }
  temperature_require(calculated_covered == result.covered_cell_count
                        && calculated.record_high_days
                             == result.totals.record_high_days
                        && calculated.record_low_days
                             == result.totals.record_low_days
                        && calculated.tmax_valid_days
                             == result.totals.tmax_valid_days
                        && calculated.tmin_valid_days
                             == result.totals.tmin_valid_days,
                      "temperature field metadata totals do not verify");
  return result;
}

inline std::string
temperature_h3_string(const H3Index cell)
{
  std::array<char, 17> buffer {};
  temperature_require(h3ToString(cell, buffer.data(), buffer.size())
                        == E_SUCCESS,
                      "failed to format H3 index");
  return buffer.data();
}

} // namespace cart0freak0::anthropocene_temperature_generation

#endif // CART0FREAK0_ANTHROPOCENE_TEMPERATURE_DATA_H
