// Normalize source observations into deterministic H3 cell-day counts.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <gdal_priv.h>
#include <ogrsf_frmts.h>
#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>

namespace fs = std::filesystem;
namespace rj = rapidjson;

namespace {

void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

enum class metric : std::size_t
{
  temperature_record_high_days,
  temperature_record_low_days,
  precipitation_record_days,
  heavy_precipitation_days,
  active_fire_days,
  observed_smoke_days,
  flood_event_days,
  extreme_weather_event_days,
  pm25_exceedance_days,
  count,
};

inline constexpr std::array<std::string_view,
                            static_cast<std::size_t>(metric::count)>
metric_properties {
  "temperature_record_high_days",
  "temperature_record_low_days",
  "precipitation_record_days",
  "heavy_precipitation_days",
  "active_fire_days",
  "observed_smoke_days",
  "flood_event_days",
  "extreme_weather_event_days",
  "pm25_exceedance_days",
};

struct configuration
{
  int year = 2026;
  int h3_resolution = 4;
  int minimum_record_years = 30;
  int minimum_valid_days_per_year = 183;
  double heavy_precipitation_minimum_mm = 10;
  double heavy_precipitation_percentile = 0.95;
  int baseline_start = 1991;
  int baseline_end = 2020;
  int pm25_aqi_threshold_exclusive = 100;
  std::string snapshot_as_of;
  int snapshot_date_key = 20260101;
};

struct inputs
{
  fs::path profile;
  fs::path output;
  fs::path ghcn_directory;
  fs::path station_inventory;
  fs::path epa_csv;
  fs::path hms_shapefile;
  fs::path storm_details_csv;
  fs::path storm_locations_csv;
  fs::path cwfis_directory;
  std::vector<fs::path> firms_csvs;
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
};

using metric_days = std::array<std::unordered_set<int>,
                               static_cast<std::size_t>(metric::count)>;
using observations = std::unordered_map<H3Index, metric_days>;

std::string
trim(std::string value)
{
  const auto whitespace = [](const unsigned char ch) {
    return std::isspace(ch) != 0;
  };
  value.erase(value.begin(),
              std::find_if_not(value.begin(), value.end(), whitespace));
  value.erase(std::find_if_not(value.rbegin(), value.rend(), whitespace).base(),
              value.end());
  return value;
}

std::vector<std::string>
parse_csv_line(const std::string_view line)
{
  std::vector<std::string> fields;
  std::string field;
  bool quoted = false;
  for (std::size_t index = 0; index < line.size(); ++index)
    {
      const char value = line[index];
      if (quoted)
        {
          if (value == '"')
            {
              if (index + 1 < line.size() && line[index + 1] == '"')
                {
                  field.push_back('"');
                  ++index;
                }
              else
                quoted = false;
            }
          else
            field.push_back(value);
        }
      else if (value == '"')
        quoted = true;
      else if (value == ',')
        {
          fields.push_back(std::move(field));
          field.clear();
        }
      else if (value != '\r')
        field.push_back(value);
    }
  require(!quoted, "unterminated quoted CSV field");
  fields.push_back(std::move(field));
  return fields;
}

using header_map = std::unordered_map<std::string, std::size_t>;

header_map
make_header_map(const std::vector<std::string>& fields)
{
  header_map result;
  for (std::size_t index = 0; index < fields.size(); ++index)
    {
      const std::string name = trim(fields[index]);
      require(!name.empty() && result.emplace(name, index).second,
              "CSV contains an empty or duplicate column name");
    }
  return result;
}

const std::string&
csv_field(const std::vector<std::string>& fields, const header_map& header,
          const std::string& name)
{
  const auto found = header.find(name);
  require(found != header.end(), "CSV is missing column '" + name + "'");
  require(found->second < fields.size(), "CSV row is short at column '" + name
                                          + "'");
  return fields[found->second];
}

template<typename Integer>
std::optional<Integer>
parse_integer(const std::string_view text)
{
  Integer result {};
  const char* first = text.data();
  const char* last = text.data() + text.size();
  const auto [position, error] = std::from_chars(first, last, result);
  if (error != std::errc {} || position != last)
    return std::nullopt;
  return result;
}

std::optional<double>
parse_number(const std::string& text)
{
  if (text.empty())
    return std::nullopt;
  std::size_t consumed = 0;
  try
    {
      const double result = std::stod(text, &consumed);
      if (consumed == text.size() && std::isfinite(result))
        return result;
    }
  catch (const std::exception&)
    { }
  return std::nullopt;
}

rj::Document
load_json(const fs::path& path)
{
  std::ifstream input {path, std::ios::binary};
  require(input.good(), "failed to open " + path.string());
  const std::string json {std::istreambuf_iterator<char>(input),
                          std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.data(), json.size());
  require(!document.HasParseError(),
          "failed to parse " + path.string() + ": "
            + rj::GetParseError_En(document.GetParseError()));
  require(document.IsObject(), path.string() + " root must be an object");
  return document;
}

const rj::Value&
member(const rj::Value& object, const char* name, const std::string& context)
{
  require(object.IsObject() && object.HasMember(name),
          context + " is missing '" + name + "'");
  return object[name];
}

std::optional<int>
iso_date_key(std::string_view value, int expected_year);

configuration
load_configuration(const fs::path& path)
{
  const rj::Document document = load_json(path);
  const std::string context = path.string();
  const rj::Value& duration = member(document, "duration", context);
  const rj::Value& aggregation = member(document, "aggregation", context);
  const rj::Value& thresholds = member(document, "thresholds", context);
  const rj::Value& snapshot = member(document, "snapshot", context);
  configuration result;
  require(member(duration, "year", "duration").IsInt(),
          "duration.year must be an integer");
  result.year = duration["year"].GetInt();
  require(member(aggregation, "h3_resolution", "aggregation").IsInt(),
          "aggregation.h3_resolution must be an integer");
  result.h3_resolution = aggregation["h3_resolution"].GetInt();
  require(member(thresholds, "minimum_record_years", "thresholds").IsInt(),
          "thresholds.minimum_record_years must be an integer");
  result.minimum_record_years = thresholds["minimum_record_years"].GetInt();
  require(member(thresholds, "minimum_valid_days_per_year", "thresholds")
            .IsInt(),
          "thresholds.minimum_valid_days_per_year must be an integer");
  result.minimum_valid_days_per_year
    = thresholds["minimum_valid_days_per_year"].GetInt();
  const char* minimum_name = thresholds.HasMember(
    "heavy_precipitation_minimum_mm")
    ? "heavy_precipitation_minimum_mm"
    : "heavy_precipitation_wet_day_mm";
  require(member(thresholds, minimum_name, "thresholds").IsNumber(),
          std::string("thresholds.") + minimum_name + " must be a number");
  result.heavy_precipitation_minimum_mm
    = thresholds[minimum_name].GetDouble();
  require(member(thresholds, "heavy_precipitation_percentile", "thresholds")
            .IsNumber(),
          "thresholds.heavy_precipitation_percentile must be a number");
  result.heavy_precipitation_percentile
    = thresholds["heavy_precipitation_percentile"].GetDouble();
  require(member(thresholds, "heavy_precipitation_baseline_start",
                 "thresholds").IsInt(),
          "thresholds.heavy_precipitation_baseline_start must be an integer");
  result.baseline_start
    = thresholds["heavy_precipitation_baseline_start"].GetInt();
  require(member(thresholds, "heavy_precipitation_baseline_end",
                 "thresholds").IsInt(),
          "thresholds.heavy_precipitation_baseline_end must be an integer");
  result.baseline_end
    = thresholds["heavy_precipitation_baseline_end"].GetInt();
  require(member(thresholds, "pm25_aqi_threshold_exclusive", "thresholds")
            .IsInt(),
          "thresholds.pm25_aqi_threshold_exclusive must be an integer");
  result.pm25_aqi_threshold_exclusive
    = thresholds["pm25_aqi_threshold_exclusive"].GetInt();
  require(member(snapshot, "as_of_utc", "snapshot").IsString(),
          "snapshot.as_of_utc must be a string");
  result.snapshot_as_of = snapshot["as_of_utc"].GetString();
  require(result.year >= 1800 && result.year <= 2500,
          "duration.year is outside the supported range");
  require(result.h3_resolution >= 0 && result.h3_resolution <= 15,
          "aggregation.h3_resolution is outside the H3 range");
  require(result.minimum_record_years > 0
            && result.minimum_valid_days_per_year > 0,
          "record-history thresholds must be positive");
  require(result.heavy_precipitation_percentile > 0
            && result.heavy_precipitation_percentile <= 1,
          "heavy-precipitation percentile must be in (0, 1]");
  require(result.baseline_start <= result.baseline_end,
          "heavy-precipitation baseline range is reversed");
  const auto snapshot_date = iso_date_key(result.snapshot_as_of, result.year);
  require(snapshot_date.has_value(),
          "snapshot.as_of_utc must begin with a valid duration-year date");
  result.snapshot_date_key = *snapshot_date;
  return result;
}

inputs
parse_arguments(const int argc, char** argv)
{
  if (argc < 3)
    throw std::invalid_argument(
      "usage: prepare-anthropocene PROFILE.json OUTPUT.geojson "
      "--ghcn-dir DIR --stations FILE --epa FILE --hms FILE "
      "--storm-details FILE --storm-locations FILE --cwfis-dir DIR "
      "[--firms FILE]...");
  inputs result;
  result.profile = argv[1];
  result.output = argv[2];
  for (int index = 3; index < argc; ++index)
    {
      const std::string option = argv[index];
      require(index + 1 < argc, "missing value after " + option);
      const fs::path value = argv[++index];
      if (option == "--ghcn-dir") result.ghcn_directory = value;
      else if (option == "--stations") result.station_inventory = value;
      else if (option == "--epa") result.epa_csv = value;
      else if (option == "--hms") result.hms_shapefile = value;
      else if (option == "--storm-details") result.storm_details_csv = value;
      else if (option == "--storm-locations") result.storm_locations_csv = value;
      else if (option == "--cwfis-dir") result.cwfis_directory = value;
      else if (option == "--firms") result.firms_csvs.push_back(value);
      else throw std::invalid_argument("unknown option " + option);
    }
  require(fs::is_directory(result.ghcn_directory),
          "--ghcn-dir is not a directory");
  require(fs::is_regular_file(result.station_inventory),
          "--stations is not a file");
  require(fs::is_regular_file(result.epa_csv), "--epa is not a file");
  require(fs::is_regular_file(result.hms_shapefile), "--hms is not a file");
  require(fs::is_regular_file(result.storm_details_csv),
          "--storm-details is not a file");
  require(fs::is_regular_file(result.storm_locations_csv),
          "--storm-locations is not a file");
  require(fs::is_directory(result.cwfis_directory),
          "--cwfis-dir is not a directory");
  for (const fs::path& path : result.firms_csvs)
    require(fs::is_regular_file(path), "--firms is not a file: " + path.string());
  return result;
}

int
date_key(const int year, const unsigned month, const unsigned day)
{
  const std::chrono::year_month_day date {
    std::chrono::year {year}, std::chrono::month {month},
    std::chrono::day {day}};
  require(date.ok(), "invalid calendar date");
  return year * 10000 + static_cast<int>(month) * 100
    + static_cast<int>(day);
}

std::optional<int>
iso_date_key(const std::string_view value, const int expected_year)
{
  if (value.size() < 10 || value[4] != '-' || value[7] != '-')
    return std::nullopt;
  const auto year = parse_integer<int>(value.substr(0, 4));
  const auto month = parse_integer<unsigned>(value.substr(5, 2));
  const auto day = parse_integer<unsigned>(value.substr(8, 2));
  if (!year || !month || !day || *year != expected_year)
    return std::nullopt;
  const std::chrono::year_month_day date {
    std::chrono::year {*year}, std::chrono::month {*month},
    std::chrono::day {*day}};
  if (!date.ok())
    return std::nullopt;
  return date_key(*year, *month, *day);
}

std::optional<std::chrono::sys_days>
make_day(const int year, const unsigned month, const unsigned day)
{
  const std::chrono::year_month_day date {
    std::chrono::year {year}, std::chrono::month {month},
    std::chrono::day {day}};
  if (!date.ok())
    return std::nullopt;
  return std::chrono::sys_days {date};
}

int
sys_day_key(const std::chrono::sys_days day)
{
  const std::chrono::year_month_day date {day};
  return date_key(static_cast<int>(date.year()),
                  static_cast<unsigned>(date.month()),
                  static_cast<unsigned>(date.day()));
}

std::optional<int>
ordinal_date_key(const int year, const int day_of_year)
{
  if (day_of_year < 1 || day_of_year > 366)
    return std::nullopt;
  const std::chrono::sys_days first {
    std::chrono::year {year} / std::chrono::January / 1};
  const std::chrono::sys_days candidate = first
    + std::chrono::days {day_of_year - 1};
  const std::chrono::year_month_day date {candidate};
  if (static_cast<int>(date.year()) != year)
    return std::nullopt;
  return sys_day_key(candidate);
}

H3Index
point_cell(const double latitude, const double longitude,
           const int resolution)
{
  require(std::isfinite(latitude) && std::isfinite(longitude)
            && latitude >= -90 && latitude <= 90
            && longitude >= -180 && longitude <= 180,
          "source coordinate is invalid");
  const LatLng point {degsToRads(latitude), degsToRads(longitude)};
  H3Index result = H3_NULL;
  require(latLngToCell(&point, resolution, &result) == E_SUCCESS
            && result != H3_NULL,
          "failed to convert source coordinate to H3");
  return result;
}

void
add_observation(observations& output, const H3Index cell,
                const metric field, const int day)
{
  output[cell][static_cast<std::size_t>(field)].insert(day);
}

void
add_point_observation(observations& output, const double latitude,
                      const double longitude, const int resolution,
                      const metric field, const int day)
{
  add_observation(output, point_cell(latitude, longitude, resolution),
                  field, day);
}

struct station_location
{
  double latitude;
  double longitude;
};

std::unordered_map<std::string, station_location>
load_station_inventory(const fs::path& path)
{
  std::ifstream input {path};
  require(input.good(), "failed to open " + path.string());
  std::unordered_map<std::string, station_location> result;
  std::string line;
  while (std::getline(input, line))
    {
      if (line.size() < 30)
        continue;
      const auto latitude = parse_number(trim(line.substr(12, 8)));
      const auto longitude = parse_number(trim(line.substr(21, 9)));
      if (latitude && longitude)
        result.emplace(line.substr(0, 11),
                       station_location {*latitude, *longitude});
    }
  return result;
}

struct current_value
{
  unsigned month;
  unsigned day;
  int value;
};

struct station_history
{
  std::array<int, 13 * 32> historical_tmax;
  std::array<int, 13 * 32> historical_tmin;
  std::array<int, 13 * 32> historical_prcp;
  std::array<std::vector<int>, 13> baseline_wet_prcp;
  std::map<int, int> tmax_valid_days;
  std::map<int, int> tmin_valid_days;
  std::map<int, int> prcp_valid_days;
  std::vector<current_value> current_tmax;
  std::vector<current_value> current_tmin;
  std::vector<current_value> current_prcp;

  station_history()
  {
    historical_tmax.fill(std::numeric_limits<int>::min());
    historical_tmin.fill(std::numeric_limits<int>::max());
    historical_prcp.fill(std::numeric_limits<int>::min());
  }
};

unsigned
days_in_month(const int year, const unsigned month)
{
  const std::chrono::year_month_day_last last {
    std::chrono::year {year},
    std::chrono::month_day_last {std::chrono::month {month}}};
  return static_cast<unsigned>(last.day());
}

int
eligible_years(const std::map<int, int>& counts, const configuration& config)
{
  return static_cast<int>(std::count_if(
    counts.begin(), counts.end(), [&](const auto& entry) {
      return entry.first < config.year
        && entry.second >= config.minimum_valid_days_per_year;
    }));
}

double
nearest_rank_percentile(std::vector<int> values, const double percentile)
{
  require(!values.empty(), "cannot calculate percentile of an empty sample");
  std::sort(values.begin(), values.end());
  const std::size_t index = std::min(
    values.size() - 1,
    static_cast<std::size_t>(std::ceil(percentile * values.size()) - 1));
  return values[index] / 10.0;
}

station_history
read_station_history(const fs::path& path, const configuration& config)
{
  std::ifstream input {path};
  require(input.good(), "failed to open " + path.string());
  station_history result;
  std::string line;
  while (std::getline(input, line))
    {
      if (line.size() < 21)
        continue;
      const auto year = parse_integer<int>(line.substr(11, 4));
      const auto month = parse_integer<unsigned>(line.substr(15, 2));
      const std::string element = line.substr(17, 4);
      if (!year || !month || *month < 1 || *month > 12
          || (element != "TMAX" && element != "TMIN" && element != "PRCP"))
        continue;
      const unsigned month_days = days_in_month(*year, *month);
      for (unsigned day = 1; day <= month_days; ++day)
        {
          const std::size_t offset = 21 + (day - 1) * 8;
          if (offset + 7 >= line.size())
            break;
          const auto value = parse_integer<int>(trim(line.substr(offset, 5)));
          const char quality_flag = line[offset + 6];
          if (!value || *value == -9999 || quality_flag != ' ')
            continue;
          const std::size_t key = *month * 32 + day;
          std::map<int, int>* counts = nullptr;
          std::vector<current_value>* current = nullptr;
          if (element == "TMAX")
            {
              counts = &result.tmax_valid_days;
              current = &result.current_tmax;
              if (*year < config.year)
                result.historical_tmax[key]
                  = std::max(result.historical_tmax[key], *value);
            }
          else if (element == "TMIN")
            {
              counts = &result.tmin_valid_days;
              current = &result.current_tmin;
              if (*year < config.year)
                result.historical_tmin[key]
                  = std::min(result.historical_tmin[key], *value);
            }
          else
            {
              counts = &result.prcp_valid_days;
              current = &result.current_prcp;
              if (*year < config.year)
                result.historical_prcp[key]
                  = std::max(result.historical_prcp[key], *value);
              if (*year >= config.baseline_start
                  && *year <= config.baseline_end && *value >= 10)
                result.baseline_wet_prcp[*month].push_back(*value);
            }
          ++(*counts)[*year];
          if (*year == config.year
              && date_key(*year, *month, day) < config.snapshot_date_key)
            current->push_back({*month, day, *value});
        }
    }
  return result;
}

void
process_ghcn(const inputs& paths, const configuration& config,
             observations& output, source_statistics& statistics)
{
  const auto stations = load_station_inventory(paths.station_inventory);
  std::vector<fs::path> files;
  for (const fs::directory_entry& entry
       : fs::directory_iterator(paths.ghcn_directory))
    if (entry.is_regular_file() && entry.path().extension() == ".dly")
      files.push_back(entry.path());
  std::sort(files.begin(), files.end());
  for (const fs::path& path : files)
    {
      ++statistics.ghcn_stations;
      const std::string station_id = path.stem().string();
      const auto location = stations.find(station_id);
      if (location == stations.end())
        continue;
      const station_history history = read_station_history(path, config);
      const bool temperature_high_eligible
        = eligible_years(history.tmax_valid_days, config)
          >= config.minimum_record_years;
      const bool temperature_low_eligible
        = eligible_years(history.tmin_valid_days, config)
          >= config.minimum_record_years;
      const bool precipitation_eligible
        = eligible_years(history.prcp_valid_days, config)
          >= config.minimum_record_years;
      if (temperature_high_eligible || temperature_low_eligible)
        ++statistics.ghcn_eligible_temperature_stations;
      if (precipitation_eligible)
        ++statistics.ghcn_eligible_precipitation_stations;
      if (temperature_high_eligible)
        for (const current_value& value : history.current_tmax)
          {
            const std::size_t key = value.month * 32 + value.day;
            if (history.historical_tmax[key] != std::numeric_limits<int>::min()
                && value.value > history.historical_tmax[key])
              add_point_observation(
                output, location->second.latitude, location->second.longitude,
                config.h3_resolution, metric::temperature_record_high_days,
                date_key(config.year, value.month, value.day));
          }
      if (temperature_low_eligible)
        for (const current_value& value : history.current_tmin)
          {
            const std::size_t key = value.month * 32 + value.day;
            if (history.historical_tmin[key] != std::numeric_limits<int>::max()
                && value.value < history.historical_tmin[key])
              add_point_observation(
                output, location->second.latitude, location->second.longitude,
                config.h3_resolution, metric::temperature_record_low_days,
                date_key(config.year, value.month, value.day));
          }
      if (precipitation_eligible)
        {
          std::array<std::optional<double>, 13> monthly_p95;
          for (unsigned month = 1; month <= 12; ++month)
            if (!history.baseline_wet_prcp[month].empty())
              monthly_p95[month] = nearest_rank_percentile(
                history.baseline_wet_prcp[month],
                config.heavy_precipitation_percentile);
          for (const current_value& value : history.current_prcp)
            {
              const std::size_t key = value.month * 32 + value.day;
              const int day = date_key(config.year, value.month, value.day);
              if (history.historical_prcp[key]
                    != std::numeric_limits<int>::min()
                  && value.value > history.historical_prcp[key])
                add_point_observation(
                  output, location->second.latitude,
                  location->second.longitude, config.h3_resolution,
                  metric::precipitation_record_days, day);
              const double millimetres = value.value / 10.0;
              if (monthly_p95[value.month]
                  && millimetres >= config.heavy_precipitation_minimum_mm
                  && millimetres > *monthly_p95[value.month])
                add_point_observation(
                  output, location->second.latitude,
                  location->second.longitude, config.h3_resolution,
                  metric::heavy_precipitation_days, day);
            }
        }
    }
}

void
process_epa(const fs::path& path, const configuration& config,
            observations& output, source_statistics& statistics)
{
  std::ifstream input {path};
  require(input.good(), "failed to open " + path.string());
  std::string line;
  require(static_cast<bool>(std::getline(input, line)), "EPA CSV is empty");
  const header_map header = make_header_map(parse_csv_line(line));
  std::unordered_set<std::string> unique_site_days;
  while (std::getline(input, line))
    {
      ++statistics.epa_rows;
      const std::vector<std::string> fields = parse_csv_line(line);
      const auto aqi = parse_integer<int>(csv_field(fields, header, "AQI"));
      if (!aqi || *aqi <= config.pm25_aqi_threshold_exclusive)
        continue;
      const auto day = iso_date_key(csv_field(fields, header, "Date Local"),
                                    config.year);
      const auto latitude = parse_number(csv_field(fields, header, "Latitude"));
      const auto longitude = parse_number(csv_field(fields, header, "Longitude"));
      if (!day || *day >= config.snapshot_date_key
          || !latitude || !longitude)
        continue;
      const std::string site = csv_field(fields, header, "State Code") + "-"
        + csv_field(fields, header, "County Code") + "-"
        + csv_field(fields, header, "Site Num") + "-"
        + std::to_string(*day);
      if (!unique_site_days.insert(site).second)
        continue;
      ++statistics.epa_exceedance_site_days;
      add_point_observation(output, *latitude, *longitude,
                            config.h3_resolution,
                            metric::pm25_exceedance_days, *day);
    }
}

std::vector<LatLng>
h3_loop(const OGRLinearRing& ring)
{
  int count = ring.getNumPoints();
  if (count > 1 && ring.getX(0) == ring.getX(count - 1)
      && ring.getY(0) == ring.getY(count - 1))
    --count;
  std::vector<LatLng> result;
  result.reserve(static_cast<std::size_t>(std::max(count, 0)));
  for (int index = 0; index < count; ++index)
    result.push_back({degsToRads(ring.getY(index)),
                      degsToRads(ring.getX(index))});
  return result;
}

std::vector<H3Index>
polygon_cells(const OGRPolygon& polygon, const int resolution)
{
  const OGRLinearRing* exterior = polygon.getExteriorRing();
  if (exterior == nullptr)
    return {};
  std::vector<LatLng> exterior_points = h3_loop(*exterior);
  if (exterior_points.size() < 3)
    return {};
  std::vector<std::vector<LatLng>> hole_points;
  std::vector<GeoLoop> holes;
  hole_points.reserve(static_cast<std::size_t>(polygon.getNumInteriorRings()));
  for (int index = 0; index < polygon.getNumInteriorRings(); ++index)
    {
      std::vector<LatLng> points = h3_loop(*polygon.getInteriorRing(index));
      if (points.size() >= 3)
        hole_points.push_back(std::move(points));
    }
  holes.reserve(hole_points.size());
  for (std::vector<LatLng>& points : hole_points)
    holes.push_back({static_cast<int>(points.size()), points.data()});
  GeoPolygon source {
    {static_cast<int>(exterior_points.size()), exterior_points.data()},
    static_cast<int>(holes.size()), holes.data(),
  };
  int64_t maximum_size = 0;
  if (maxPolygonToCellsSize(&source, resolution, 0, &maximum_size) != E_SUCCESS
      || maximum_size <= 0 || maximum_size > 2000000)
    return {};
  std::vector<H3Index> result(static_cast<std::size_t>(maximum_size), H3_NULL);
  if (polygonToCells(&source, resolution, 0, result.data()) != E_SUCCESS)
    return {};
  result.erase(std::remove(result.begin(), result.end(), H3_NULL), result.end());
  return result;
}

std::vector<const OGRPolygon*>
geometry_polygons(const OGRGeometry& geometry)
{
  std::vector<const OGRPolygon*> result;
  const OGRwkbGeometryType type = wkbFlatten(geometry.getGeometryType());
  if (type == wkbPolygon)
    result.push_back(geometry.toPolygon());
  else if (type == wkbMultiPolygon)
    {
      const OGRMultiPolygon* multi = geometry.toMultiPolygon();
      for (const auto* child : *multi)
        if (wkbFlatten(child->getGeometryType()) == wkbPolygon)
          result.push_back(static_cast<const OGRPolygon*>(child));
    }
  return result;
}

std::vector<int>
hms_days(const std::string& start, const std::string& end,
         const int expected_year)
{
  if (start.size() < 7 || end.size() < 7)
    return {};
  const auto start_year = parse_integer<int>(std::string_view(start).substr(0, 4));
  const auto start_doy = parse_integer<int>(std::string_view(start).substr(4, 3));
  const auto end_year = parse_integer<int>(std::string_view(end).substr(0, 4));
  const auto end_doy = parse_integer<int>(std::string_view(end).substr(4, 3));
  if (!start_year || !start_doy || !end_year || !end_doy
      || *start_year != expected_year || *end_year != expected_year)
    return {};
  const auto first_key = ordinal_date_key(*start_year, *start_doy);
  const auto last_key = ordinal_date_key(*end_year, *end_doy);
  if (!first_key || !last_key)
    return {};
  const std::chrono::sys_days first = std::chrono::sys_days {
    std::chrono::year {*start_year} / std::chrono::January / 1}
    + std::chrono::days {*start_doy - 1};
  const std::chrono::sys_days last = std::chrono::sys_days {
    std::chrono::year {*end_year} / std::chrono::January / 1}
    + std::chrono::days {*end_doy - 1};
  if (last < first || last - first > std::chrono::days {7})
    return {};
  std::vector<int> result;
  for (std::chrono::sys_days day = first; day <= last;
       day += std::chrono::days {1})
    result.push_back(sys_day_key(day));
  return result;
}

void
process_hms(const fs::path& path, const configuration& config,
            observations& output, source_statistics& statistics)
{
  GDALAllRegister();
  std::unique_ptr<GDALDataset, decltype(&GDALClose)> dataset(
    static_cast<GDALDataset*>(GDALOpenEx(
      path.string().c_str(), GDAL_OF_VECTOR | GDAL_OF_READONLY,
      nullptr, nullptr, nullptr)), &GDALClose);
  require(dataset != nullptr, "failed to open HMS shapefile " + path.string());
  OGRLayer* layer = dataset->GetLayer(0);
  require(layer != nullptr, "HMS shapefile has no layer");
  layer->ResetReading();
  while (OGRFeature* raw = layer->GetNextFeature())
    {
      std::unique_ptr<OGRFeature, decltype(&OGRFeature::DestroyFeature)>
        feature(raw, &OGRFeature::DestroyFeature);
      ++statistics.hms_polygons;
      std::vector<int> days = hms_days(
        feature->GetFieldAsString("Start"),
        feature->GetFieldAsString("End"), config.year);
      days.erase(std::remove_if(days.begin(), days.end(), [&](const int day) {
                   return day >= config.snapshot_date_key;
                 }),
                 days.end());
      OGRGeometry* geometry = feature->GetGeometryRef();
      if (days.empty() || geometry == nullptr)
        continue;
      bool filled = false;
      for (const OGRPolygon* polygon : geometry_polygons(*geometry))
        {
          const std::vector<H3Index> cells = polygon_cells(
            *polygon, config.h3_resolution);
          for (const H3Index cell : cells)
            for (const int day : days)
              add_observation(output, cell, metric::observed_smoke_days, day);
          filled = filled || !cells.empty();
        }
      if (!filled)
        {
          OGRPoint centroid;
          if (geometry->Centroid(&centroid) == OGRERR_NONE
              && std::isfinite(centroid.getX())
              && std::isfinite(centroid.getY()))
            {
              ++statistics.hms_centroid_fallbacks;
              for (const int day : days)
                add_point_observation(
                  output, centroid.getY(), centroid.getX(),
                  config.h3_resolution, metric::observed_smoke_days, day);
            }
        }
    }
}

using event_locations
  = std::unordered_map<std::string, std::vector<station_location>>;

event_locations
load_storm_locations(const fs::path& path)
{
  std::ifstream input {path};
  require(input.good(), "failed to open " + path.string());
  std::string line;
  require(static_cast<bool>(std::getline(input, line)),
          "Storm Events locations CSV is empty");
  const header_map header = make_header_map(parse_csv_line(line));
  event_locations result;
  while (std::getline(input, line))
    {
      const std::vector<std::string> fields = parse_csv_line(line);
      const auto latitude = parse_number(csv_field(fields, header, "LATITUDE"));
      const auto longitude = parse_number(csv_field(fields, header, "LONGITUDE"));
      if (latitude && longitude)
        result[csv_field(fields, header, "EVENT_ID")].push_back(
          {*latitude, *longitude});
    }
  return result;
}

bool
is_flood_event(std::string value)
{
  std::transform(value.begin(), value.end(), value.begin(),
                 [](const unsigned char ch) {
                   return static_cast<char>(std::tolower(ch));
                 });
  return value.find("flood") != std::string::npos
    || value.find("heavy rain") != std::string::npos
    || value.find("excessive rainfall") != std::string::npos;
}

void
process_storm_events(const inputs& paths, const configuration& config,
                     observations& output, source_statistics& statistics)
{
  const event_locations indexed_locations
    = load_storm_locations(paths.storm_locations_csv);
  std::ifstream input {paths.storm_details_csv};
  require(input.good(), "failed to open " + paths.storm_details_csv.string());
  std::string line;
  require(static_cast<bool>(std::getline(input, line)),
          "Storm Events details CSV is empty");
  const header_map header = make_header_map(parse_csv_line(line));
  while (std::getline(input, line))
    {
      ++statistics.storm_events;
      const std::vector<std::string> fields = parse_csv_line(line);
      const auto begin_year_month = parse_integer<int>(
        csv_field(fields, header, "BEGIN_YEARMONTH"));
      const auto end_year_month = parse_integer<int>(
        csv_field(fields, header, "END_YEARMONTH"));
      const auto begin_day = parse_integer<unsigned>(
        csv_field(fields, header, "BEGIN_DAY"));
      const auto end_day = parse_integer<unsigned>(
        csv_field(fields, header, "END_DAY"));
      if (!begin_year_month || !end_year_month || !begin_day || !end_day)
        continue;
      const int begin_year = *begin_year_month / 100;
      const unsigned begin_month = static_cast<unsigned>(*begin_year_month % 100);
      const int end_year = *end_year_month / 100;
      const unsigned end_month = static_cast<unsigned>(*end_year_month % 100);
      const auto first = make_day(begin_year, begin_month, *begin_day);
      const auto last = make_day(end_year, end_month, *end_day);
      if (!first || !last || *last < *first
          || *last - *first > std::chrono::days {366})
        continue;
      std::vector<station_location> locations;
      const std::string event_id = csv_field(fields, header, "EVENT_ID");
      const auto indexed = indexed_locations.find(event_id);
      if (indexed != indexed_locations.end())
        locations = indexed->second;
      const auto begin_latitude = parse_number(
        csv_field(fields, header, "BEGIN_LAT"));
      const auto begin_longitude = parse_number(
        csv_field(fields, header, "BEGIN_LON"));
      if (begin_latitude && begin_longitude)
        locations.push_back({*begin_latitude, *begin_longitude});
      const auto end_latitude = parse_number(csv_field(fields, header, "END_LAT"));
      const auto end_longitude = parse_number(csv_field(fields, header, "END_LON"));
      if (end_latitude && end_longitude)
        locations.push_back({*end_latitude, *end_longitude});
      if (locations.empty())
        continue;
      ++statistics.storm_events_with_locations;
      const bool flood = is_flood_event(csv_field(fields, header, "EVENT_TYPE"));
      for (std::chrono::sys_days day = *first; day <= *last;
           day += std::chrono::days {1})
        {
          const std::chrono::year_month_day calendar {day};
          if (static_cast<int>(calendar.year()) != config.year)
            continue;
          const int key = sys_day_key(day);
          if (key >= config.snapshot_date_key)
            continue;
          for (const station_location& location : locations)
            {
              add_point_observation(
                output, location.latitude, location.longitude,
                config.h3_resolution, metric::extreme_weather_event_days, key);
              if (flood)
                add_point_observation(
                  output, location.latitude, location.longitude,
                  config.h3_resolution, metric::flood_event_days, key);
            }
        }
    }
}

void
process_fire_csv(const fs::path& path, const configuration& config,
                 observations& output, std::uint64_t& row_count)
{
  std::ifstream input {path};
  require(input.good(), "failed to open " + path.string());
  std::string line;
  require(static_cast<bool>(std::getline(input, line)),
          "fire CSV is empty: " + path.string());
  const header_map header = make_header_map(parse_csv_line(line));
  const std::string latitude_name = header.contains("latitude")
    ? "latitude" : "lat";
  const std::string longitude_name = header.contains("longitude")
    ? "longitude" : "lon";
  const std::string date_name = header.contains("acq_date")
    ? "acq_date" : "rep_date";
  while (std::getline(input, line))
    {
      ++row_count;
      const std::vector<std::string> fields = parse_csv_line(line);
      const auto latitude = parse_number(
        trim(csv_field(fields, header, latitude_name)));
      const auto longitude = parse_number(
        trim(csv_field(fields, header, longitude_name)));
      const auto day = iso_date_key(
        trim(csv_field(fields, header, date_name)), config.year);
      if (latitude && longitude && day
          && *day < config.snapshot_date_key)
        add_point_observation(output, *latitude, *longitude,
                              config.h3_resolution,
                              metric::active_fire_days, *day);
    }
}

void
process_fire_sources(const inputs& paths, const configuration& config,
                     observations& output, source_statistics& statistics)
{
  std::vector<fs::path> cwfis_files;
  for (const fs::directory_entry& entry
       : fs::directory_iterator(paths.cwfis_directory))
    if (entry.is_regular_file() && entry.path().extension() == ".csv")
      cwfis_files.push_back(entry.path());
  std::sort(cwfis_files.begin(), cwfis_files.end());
  statistics.cwfis_files = cwfis_files.size();
  for (const fs::path& path : cwfis_files)
    process_fire_csv(path, config, output, statistics.cwfis_rows);
  for (const fs::path& path : paths.firms_csvs)
    process_fire_csv(path, config, output, statistics.firms_rows);
}

std::string
h3_string(const H3Index cell)
{
  std::array<char, 17> buffer {};
  require(h3ToString(cell, buffer.data(), buffer.size()) == E_SUCCESS,
          "failed to format H3 index");
  return buffer.data();
}

template<typename Writer>
void
write_statistics(Writer& writer,
                 const source_statistics& statistics)
{
  writer.Key("source_statistics");
  writer.StartObject();
  const auto value = [&](const char* name, const std::uint64_t number) {
    writer.Key(name);
    writer.Uint64(number);
  };
  value("ghcn_stations", statistics.ghcn_stations);
  value("ghcn_eligible_temperature_stations",
        statistics.ghcn_eligible_temperature_stations);
  value("ghcn_eligible_precipitation_stations",
        statistics.ghcn_eligible_precipitation_stations);
  value("epa_rows", statistics.epa_rows);
  value("epa_exceedance_site_days", statistics.epa_exceedance_site_days);
  value("hms_polygons", statistics.hms_polygons);
  value("hms_centroid_fallbacks", statistics.hms_centroid_fallbacks);
  value("storm_events", statistics.storm_events);
  value("storm_events_with_locations", statistics.storm_events_with_locations);
  value("cwfis_files", statistics.cwfis_files);
  value("cwfis_rows", statistics.cwfis_rows);
  value("firms_rows", statistics.firms_rows);
  writer.EndObject();
}

void
write_geojson(const fs::path& path, const configuration& config,
              const observations& data, const source_statistics& statistics)
{
  std::vector<H3Index> cells;
  cells.reserve(data.size());
  for (const auto& [cell, unused] : data)
    {
      static_cast<void>(unused);
      cells.push_back(cell);
    }
  std::sort(cells.begin(), cells.end());
  std::array<std::uint64_t, static_cast<std::size_t>(metric::count)> totals {};
  std::array<std::uint64_t, static_cast<std::size_t>(metric::count)>
    feature_counts {};
  for (const H3Index cell : cells)
    for (std::size_t index = 0; index < totals.size(); ++index)
      {
        totals[index] += data.at(cell)[index].size();
        if (!data.at(cell)[index].empty())
          ++feature_counts[index];
      }

  std::ofstream output {path, std::ios::binary};
  require(output.good(), "failed to open output " + path.string());
  rj::OStreamWrapper stream(output);
  rj::Writer<rj::OStreamWrapper> writer(stream);
  writer.StartObject();
  writer.Key("type");
  writer.String("FeatureCollection");
  writer.Key("metadata");
  writer.StartObject();
  writer.Key("schema");
  writer.String("cartofreako-anthropocene-observations-v1");
  writer.Key("calendar_year");
  writer.Int(config.year);
  writer.Key("snapshot_as_of_utc");
  writer.String(config.snapshot_as_of.c_str());
  writer.Key("partial_year");
  writer.Bool(true);
  writer.Key("h3_resolution");
  writer.Int(config.h3_resolution);
  writer.Key("count_mode");
  writer.String("unique-source-reporting-days-per-H3-cell");
  writer.Key("missing_semantics");
  writer.String("An absent metric is unobserved or unavailable, never an asserted zero.");
  writer.Key("feature_count");
  writer.Uint64(cells.size());
  writer.Key("metric_cell_day_totals");
  writer.StartObject();
  for (std::size_t index = 0; index < totals.size(); ++index)
    {
      writer.Key(metric_properties[index].data());
      writer.Uint64(totals[index]);
    }
  writer.EndObject();
  writer.Key("metric_feature_counts");
  writer.StartObject();
  for (std::size_t index = 0; index < feature_counts.size(); ++index)
    {
      writer.Key(metric_properties[index].data());
      writer.Uint64(feature_counts[index]);
    }
  writer.EndObject();
  write_statistics(writer, statistics);
  writer.EndObject();
  writer.Key("features");
  writer.StartArray();
  for (const H3Index cell : cells)
    {
      LatLng center {};
      require(cellToLatLng(cell, &center) == E_SUCCESS,
              "failed to calculate H3 center");
      const metric_days& values = data.at(cell);
      writer.StartObject();
      writer.Key("type");
      writer.String("Feature");
      writer.Key("id");
      const std::string id = h3_string(cell);
      writer.String(id.c_str());
      writer.Key("geometry");
      writer.StartObject();
      writer.Key("type");
      writer.String("Point");
      writer.Key("coordinates");
      writer.StartArray();
      writer.Double(radsToDegs(center.lng));
      writer.Double(radsToDegs(center.lat));
      writer.EndArray();
      writer.EndObject();
      writer.Key("properties");
      writer.StartObject();
      writer.Key("h3");
      writer.String(id.c_str());
      for (std::size_t index = 0; index < values.size(); ++index)
        if (!values[index].empty())
          {
            writer.Key(metric_properties[index].data());
            writer.Uint64(values[index].size());
          }
      writer.EndObject();
      writer.EndObject();
    }
  writer.EndArray();
  writer.EndObject();
  output << '\n';
  require(output.good(), "failed while writing " + path.string());
}

int
run(const int argc, char** argv)
{
  const inputs paths = parse_arguments(argc, argv);
  const configuration config = load_configuration(paths.profile);
  observations data;
  source_statistics statistics;
  std::cerr << "preparing GHCN/GSN records\n";
  process_ghcn(paths, config, data, statistics);
  std::cerr << "preparing EPA PM2.5 exceedances\n";
  process_epa(paths.epa_csv, config, data, statistics);
  std::cerr << "preparing NOAA HMS smoke polygons\n";
  process_hms(paths.hms_shapefile, config, data, statistics);
  std::cerr << "preparing NOAA Storm Events\n";
  process_storm_events(paths, config, data, statistics);
  std::cerr << "preparing active-fire feeds\n";
  process_fire_sources(paths, config, data, statistics);
  std::cerr << "writing " << data.size() << " H3 cells\n";
  write_geojson(paths.output, config, data, statistics);
  return 0;
}

} // namespace

int
main(const int argc, char** argv)
{
  try
    {
      return run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "prepare-anthropocene: " << error.what() << '\n';
      return 1;
    }
}
