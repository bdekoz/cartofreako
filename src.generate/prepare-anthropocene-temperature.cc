// Prepare non-sparse NOAA CPC daily-temperature record fields on H3.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <numbers>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include <gdal_priv.h>
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

struct target_configuration
{
  fs::path profile_path;
  fs::path output_path;
  int year = 0;
  bool partial_year = true;
  std::string snapshot_as_of_utc;
  std::string data_through;
  std::chrono::sys_days last_day;
  int h3_resolution = 3;
  int baseline_start = 1979;
  int baseline_end = 0;
  unsigned minimum_history_years = 30;
  std::string source_manifest_sha256;
};

struct target_values
{
  target_configuration configuration;
  std::vector<std::uint16_t> record_high_days;
  std::vector<std::uint16_t> record_low_days;
  std::vector<std::uint16_t> tmax_valid_days;
  std::vector<std::uint16_t> tmin_valid_days;
};

using dataset_ptr = std::unique_ptr<GDALDataset, decltype(&GDALClose)>;

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

int
integer_member(const rj::Value& object, const char* name,
               const std::string& context)
{
  const rj::Value& value = member(object, name, context);
  require(value.IsInt(), context + "." + name + " must be an integer");
  return value.GetInt();
}

unsigned
unsigned_member(const rj::Value& object, const char* name,
                const std::string& context)
{
  const rj::Value& value = member(object, name, context);
  require(value.IsUint(), context + "." + name
                            + " must be an unsigned integer");
  return value.GetUint();
}

std::string
string_member(const rj::Value& object, const char* name,
              const std::string& context)
{
  const rj::Value& value = member(object, name, context);
  require(value.IsString(), context + "." + name + " must be a string");
  return {value.GetString(), value.GetStringLength()};
}

bool
bool_member(const rj::Value& object, const char* name,
            const std::string& context)
{
  const rj::Value& value = member(object, name, context);
  require(value.IsBool(), context + "." + name + " must be Boolean");
  return value.GetBool();
}

bool
is_hex_digest(const std::string_view value)
{
  return value.size() == 64
    && std::all_of(value.begin(), value.end(), [](const char digit) {
         return (digit >= '0' && digit <= '9')
           || (digit >= 'a' && digit <= 'f');
       });
}

std::chrono::sys_days
parse_date(const std::string_view text, const std::string& context)
{
  require(text.size() == 10 && text[4] == '-' && text[7] == '-',
          context + " must use YYYY-MM-DD");
  const auto parse_part = [&](const std::size_t offset,
                              const std::size_t length) {
    int value = 0;
    for (std::size_t index = 0; index < length; ++index)
      {
        const char digit = text[offset + index];
        require(digit >= '0' && digit <= '9',
                context + " must use YYYY-MM-DD");
        value = value * 10 + digit - '0';
      }
    return value;
  };
  const std::chrono::year_month_day date {
    std::chrono::year {parse_part(0, 4)},
    std::chrono::month {static_cast<unsigned>(parse_part(5, 2))},
    std::chrono::day {static_cast<unsigned>(parse_part(8, 2))},
  };
  require(date.ok(), context + " is not a calendar date");
  return std::chrono::sys_days {date};
}

target_configuration
load_configuration(const fs::path& profile_path, const fs::path& output_path)
{
  const rj::Document document = load_json(profile_path);
  const std::string context = profile_path.string();
  require(integer_member(document, "schema_version", context) == 1,
          "unsupported Anthropocene temperature profile schema");
  require(string_member(document, "product", context)
            == "anthropocene-temperature-field",
          context + ".product must be 'anthropocene-temperature-field'");

  target_configuration result;
  result.profile_path = profile_path;
  result.output_path = output_path;
  const rj::Value& duration = member(document, "duration", context);
  require(string_member(duration, "type", "duration") == "calendar-year",
          "duration.type must be 'calendar-year'");
  result.year = integer_member(duration, "year", "duration");

  const rj::Value& snapshot = member(document, "snapshot", context);
  result.snapshot_as_of_utc = string_member(
    snapshot, "as_of_utc", "snapshot");
  result.data_through = string_member(snapshot, "data_through", "snapshot");
  result.partial_year = bool_member(snapshot, "partial_year", "snapshot");
  result.last_day = parse_date(result.data_through, "snapshot.data_through");

  const rj::Value& aggregation = member(document, "aggregation", context);
  require(string_member(aggregation, "spatial_index", "aggregation") == "H3",
          "aggregation.spatial_index must be 'H3'");
  require(string_member(aggregation, "source_grid_aggregation", "aggregation")
            == "mean-of-valid-grid-cell-centers",
          "unsupported aggregation.source_grid_aggregation");
  result.h3_resolution = integer_member(
    aggregation, "h3_resolution", "aggregation");

  const rj::Value& records = member(document, "records", context);
  result.baseline_start = integer_member(
    records, "baseline_start", "records");
  result.baseline_end = integer_member(records, "baseline_end", "records");
  result.minimum_history_years = unsigned_member(
    records, "minimum_history_years", "records");
  require(string_member(records, "comparison", "records") == "strict",
          "records.comparison must be 'strict'");

  const rj::Value& source = member(document, "source", context);
  require(string_member(source, "id", "source")
            == "noaa-cpc-global-temperature",
          "source.id must be noaa-cpc-global-temperature");
  result.source_manifest_sha256 = string_member(
    source, "manifest_sha256", "source");
  require(is_hex_digest(result.source_manifest_sha256),
          "source.manifest_sha256 must be a lowercase SHA-256");

  const rj::Value& data = member(document, "data", context);
  require(fs::path(string_member(data, "geojson", "data")).filename()
            == output_path.filename(),
          "profile data.geojson does not name the requested output");
  require(result.year >= 1979 && result.year <= 2500,
          "duration.year is outside the supported CPC range");
  require(result.h3_resolution >= 0 && result.h3_resolution <= 15,
          "aggregation.h3_resolution is outside H3's range");
  require(result.baseline_start == 1979,
          "CPC V1.0 record baseline must begin in 1979");
  require(result.baseline_end == result.year - 1,
          "records.baseline_end must be the year before duration.year");
  require(result.minimum_history_years > 0
            && result.minimum_history_years
                 <= static_cast<unsigned>(result.baseline_end
                                            - result.baseline_start + 1),
          "records.minimum_history_years is invalid");
  const std::chrono::year_month_day last {result.last_day};
  require(static_cast<int>(last.year()) == result.year,
          "snapshot.data_through must be inside duration.year");
  const bool ends_year = static_cast<unsigned>(last.month()) == 12
    && static_cast<unsigned>(last.day()) == 31;
  require(result.partial_year != ends_year,
          "snapshot.partial_year disagrees with snapshot.data_through");
  return result;
}

std::vector<H3Index>
global_cells(const int resolution)
{
  std::vector<H3Index> roots(static_cast<std::size_t>(res0CellCount()));
  require(getRes0Cells(roots.data()) == E_SUCCESS,
          "failed to enumerate H3 resolution-zero cells");
  std::vector<H3Index> result;
  for (const H3Index root : roots)
    {
      int64_t size = 0;
      require(cellToChildrenSize(root, resolution, &size) == E_SUCCESS
                && size > 0,
              "failed to size H3 descendants");
      std::vector<H3Index> children(static_cast<std::size_t>(size));
      require(cellToChildren(root, resolution, children.data()) == E_SUCCESS,
              "failed to enumerate H3 descendants");
      for (const H3Index child : children)
        if (child != H3_NULL)
          result.push_back(child);
    }
  std::sort(result.begin(), result.end());
  result.erase(std::unique(result.begin(), result.end()), result.end());
  int64_t expected = 0;
  require(getNumCells(resolution, &expected) == E_SUCCESS
            && result.size() == static_cast<std::size_t>(expected),
          "H3 global-cell enumeration has the wrong size");
  return result;
}

dataset_ptr
open_cpc(const fs::path& path, const std::string& variable)
{
  require(fs::is_regular_file(path), "missing CPC input " + path.string());
  const std::string name = "NETCDF:\"" + fs::absolute(path).string()
    + "\":" + variable;
  dataset_ptr result(static_cast<GDALDataset*>(GDALOpenEx(
    name.c_str(), GDAL_OF_RASTER | GDAL_OF_READONLY, nullptr, nullptr,
    nullptr)), &GDALClose);
  require(result != nullptr, "GDAL failed to open " + path.string());
  require(result->GetRasterXSize() == 720 && result->GetRasterYSize() == 360,
          path.string() + " is not the CPC 0.5-degree global grid");
  std::array<double, 6> transform {};
  require(result->GetGeoTransform(transform.data()) == CE_None,
          path.string() + " lacks a geotransform");
  constexpr std::array expected {0.0, 0.5, 0.0, 90.0, 0.0, -0.5};
  for (std::size_t index = 0; index < transform.size(); ++index)
    require(std::abs(transform[index] - expected[index]) < 1e-12,
            path.string() + " has an unexpected geotransform");
  return result;
}

std::vector<std::uint32_t>
pixel_cells(const std::vector<H3Index>& cells, const int resolution)
{
  std::unordered_map<H3Index, std::uint32_t> indices;
  indices.reserve(cells.size());
  for (std::size_t index = 0; index < cells.size(); ++index)
    indices.emplace(cells[index], static_cast<std::uint32_t>(index));

  std::vector<std::uint32_t> result(720U * 360U);
  for (int row = 0; row < 360; ++row)
    for (int column = 0; column < 720; ++column)
      {
        const double latitude = 89.75 - row * 0.5;
        double longitude = 0.25 + column * 0.5;
        if (longitude > 180)
          longitude -= 360;
        const LatLng point {degsToRads(latitude), degsToRads(longitude)};
        H3Index cell = H3_NULL;
        require(latLngToCell(&point, resolution, &cell) == E_SUCCESS
                  && cell != H3_NULL,
                "failed to map a CPC grid point to H3");
        const auto found = indices.find(cell);
        require(found != indices.end(), "CPC grid point mapped outside H3");
        result[static_cast<std::size_t>(row) * 720U
               + static_cast<std::size_t>(column)] = found->second;
      }
  return result;
}

unsigned
days_in_year(const int year)
{
  const std::chrono::sys_days first {
    std::chrono::year {year} / std::chrono::January / 1};
  const std::chrono::sys_days next {
    std::chrono::year {year + 1} / std::chrono::January / 1};
  return static_cast<unsigned>((next - first).count());
}

unsigned
day_slot(const std::chrono::year_month_day date)
{
  return static_cast<unsigned>(date.month()) * 32U
    + static_cast<unsigned>(date.day());
}

std::optional<std::size_t>
target_for_year(const std::vector<target_values>& targets, const int year)
{
  for (std::size_t index = 0; index < targets.size(); ++index)
    if (targets[index].configuration.year == year)
      return index;
  return std::nullopt;
}

void
process_variable(const fs::path& input_directory,
                 const std::string& variable, const bool maximum,
                 const std::vector<H3Index>& cells,
                 const std::vector<std::uint32_t>& grid_cells,
                 std::vector<target_values>& targets)
{
  constexpr std::size_t slots_per_cell = 13U * 32U;
  const int first_year = targets.front().configuration.baseline_start;
  const int final_year = targets.back().configuration.year;
  const unsigned minimum_history
    = targets.front().configuration.minimum_history_years;
  const float initial = maximum
    ? -std::numeric_limits<float>::infinity()
    : std::numeric_limits<float>::infinity();
  std::vector<float> records(cells.size() * slots_per_cell, initial);
  std::vector<std::uint8_t> history_years(
    cells.size() * slots_per_cell, 0);
  std::vector<float> raster(720U * 360U);
  std::vector<double> sums(cells.size(), 0);
  std::vector<std::uint16_t> samples(cells.size(), 0);
  std::vector<std::uint32_t> touched;
  touched.reserve(cells.size());

  for (int year = first_year; year <= final_year; ++year)
    {
      const fs::path path = input_directory
        / (variable + "." + std::to_string(year) + ".nc");
      dataset_ptr dataset = open_cpc(path, variable);
      const int bands = dataset->GetRasterCount();
      require(bands > 0 && bands <= static_cast<int>(days_in_year(year)),
              path.string() + " has an invalid daily-band count");
      const std::optional<std::size_t> target_index
        = target_for_year(targets, year);
      unsigned included_days = static_cast<unsigned>(bands);
      if (target_index)
        {
          const std::chrono::sys_days first {
            std::chrono::year {year} / std::chrono::January / 1};
          included_days = static_cast<unsigned>(
            (targets[*target_index].configuration.last_day - first).count()
            + 1);
          require(included_days <= static_cast<unsigned>(bands),
                  path.string() + " does not reach profile data_through");
        }
      else
        require(bands == static_cast<int>(days_in_year(year)),
                path.string() + " is incomplete inside the record baseline");

      std::cerr << "CPC " << variable << ' ' << year << ": "
                << included_days << " days\n";
      const std::chrono::sys_days first {
        std::chrono::year {year} / std::chrono::January / 1};
      for (unsigned day_index = 0; day_index < included_days; ++day_index)
        {
          GDALRasterBand* band = dataset->GetRasterBand(
            static_cast<int>(day_index + 1));
          require(band != nullptr
                    && band->RasterIO(
                      GF_Read, 0, 0, 720, 360, raster.data(), 720, 360,
                      GDT_Float32, 0, 0, nullptr) == CE_None,
                  "GDAL failed to read " + path.string() + " band "
                    + std::to_string(day_index + 1));
          touched.clear();
          for (std::size_t pixel = 0; pixel < raster.size(); ++pixel)
            {
              const float value = raster[pixel];
              if (!std::isfinite(value) || value <= -100 || value >= 100)
                continue;
              const std::uint32_t cell = grid_cells[pixel];
              if (samples[cell] == 0)
                touched.push_back(cell);
              sums[cell] += value;
              ++samples[cell];
            }

          const std::chrono::year_month_day date {
            first + std::chrono::days {day_index}};
          const unsigned slot = day_slot(date);
          for (const std::uint32_t cell : touched)
            {
              const float value = static_cast<float>(
                sums[cell] / samples[cell]);
              const std::size_t history_index
                = static_cast<std::size_t>(cell) * slots_per_cell + slot;
              if (target_index)
                {
                  target_values& target = targets[*target_index];
                  std::vector<std::uint16_t>& valid = maximum
                    ? target.tmax_valid_days : target.tmin_valid_days;
                  std::vector<std::uint16_t>& record_days = maximum
                    ? target.record_high_days : target.record_low_days;
                  ++valid[cell];
                  if (history_years[history_index] >= minimum_history
                      && (maximum ? value > records[history_index]
                                  : value < records[history_index]))
                    ++record_days[cell];
                }

              if (history_years[history_index]
                    < std::numeric_limits<std::uint8_t>::max())
                ++history_years[history_index];
              if (maximum)
                records[history_index] = std::max(
                  records[history_index], value);
              else
                records[history_index] = std::min(
                  records[history_index], value);
              sums[cell] = 0;
              samples[cell] = 0;
            }
        }
    }
}

std::string
h3_string(const H3Index cell)
{
  std::array<char, 17> buffer {};
  require(h3ToString(cell, buffer.data(), buffer.size()) == E_SUCCESS,
          "failed to format H3 index");
  return buffer.data();
}

void
write_geojson(const target_values& target,
              const std::vector<H3Index>& cells)
{
  const auto total = [](const std::vector<std::uint16_t>& values) {
    std::uint64_t result = 0;
    for (const std::uint16_t value : values)
      result += value;
    return result;
  };
  const auto covered = [&](const std::size_t index) {
    return target.tmax_valid_days[index] != 0
      || target.tmin_valid_days[index] != 0;
  };
  std::uint64_t covered_cells = 0;
  for (std::size_t index = 0; index < cells.size(); ++index)
    if (covered(index))
      ++covered_cells;

  std::ofstream output {target.configuration.output_path, std::ios::binary};
  require(output.good(), "failed to open "
                           + target.configuration.output_path.string());
  rj::OStreamWrapper stream(output);
  rj::Writer<rj::OStreamWrapper> writer(stream);
  writer.StartObject();
  writer.Key("type");
  writer.String("FeatureCollection");
  writer.Key("metadata");
  writer.StartObject();
  writer.Key("schema");
  writer.String("cartofreako-anthropocene-temperature-fields-v1");
  writer.Key("evidence_class");
  writer.String("observation-interpolated-analysis-field");
  writer.Key("calendar_year");
  writer.Int(target.configuration.year);
  writer.Key("snapshot_as_of_utc");
  writer.String(target.configuration.snapshot_as_of_utc.c_str());
  writer.Key("data_through");
  writer.String(target.configuration.data_through.c_str());
  writer.Key("partial_year");
  writer.Bool(target.configuration.partial_year);
  writer.Key("h3_resolution");
  writer.Int(target.configuration.h3_resolution);
  writer.Key("source_grid_aggregation");
  writer.String("mean-of-valid-grid-cell-centers");
  writer.Key("reporting_day");
  writer.String("06Z-to-06Z");
  writer.Key("record_comparison");
  writer.String("strict");
  writer.Key("baseline_start");
  writer.Int(target.configuration.baseline_start);
  writer.Key("baseline_end");
  writer.Int(target.configuration.baseline_end);
  writer.Key("minimum_history_years");
  writer.Uint(target.configuration.minimum_history_years);
  writer.Key("source_manifest_sha256");
  writer.String(target.configuration.source_manifest_sha256.c_str());
  writer.Key("missing_semantics");
  writer.String("A zero with positive valid_days is analyzed zero; zero valid_days is missing.");
  writer.Key("feature_count");
  writer.Uint64(cells.size());
  writer.Key("covered_cell_count");
  writer.Uint64(covered_cells);
  writer.Key("metric_totals");
  writer.StartObject();
  writer.Key("cpc_temperature_record_high_days");
  writer.Uint64(total(target.record_high_days));
  writer.Key("cpc_temperature_record_low_days");
  writer.Uint64(total(target.record_low_days));
  writer.Key("cpc_tmax_valid_days");
  writer.Uint64(total(target.tmax_valid_days));
  writer.Key("cpc_tmin_valid_days");
  writer.Uint64(total(target.tmin_valid_days));
  writer.EndObject();
  writer.EndObject();
  writer.Key("features");
  writer.StartArray();
  for (std::size_t index = 0; index < cells.size(); ++index)
    {
      const H3Index cell = cells[index];
      LatLng center {};
      require(cellToLatLng(cell, &center) == E_SUCCESS,
              "failed to calculate H3 center");
      const std::string id = h3_string(cell);
      writer.StartObject();
      writer.Key("type");
      writer.String("Feature");
      writer.Key("id");
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
      writer.Key("cpc_temperature_record_high_days");
      writer.Uint(target.record_high_days[index]);
      writer.Key("cpc_temperature_record_low_days");
      writer.Uint(target.record_low_days[index]);
      writer.Key("cpc_tmax_valid_days");
      writer.Uint(target.tmax_valid_days[index]);
      writer.Key("cpc_tmin_valid_days");
      writer.Uint(target.tmin_valid_days[index]);
      writer.EndObject();
      writer.EndObject();
    }
  writer.EndArray();
  writer.EndObject();
  output << '\n';
  require(output.good(), "failed while writing "
                           + target.configuration.output_path.string());
}

int
run(const int argc, char** argv)
{
  if (argc < 4 || argc % 2 != 0)
    throw std::invalid_argument(
      "usage: prepare-anthropocene-temperature CPC-DIR "
      "PROFILE.json OUTPUT.geojson [PROFILE.json OUTPUT.geojson]...");
  const fs::path input_directory = fs::absolute(argv[1]);
  require(fs::is_directory(input_directory), "CPC-DIR is not a directory");
  std::vector<target_values> targets;
  for (int index = 2; index < argc; index += 2)
    {
      target_values target;
      target.configuration = load_configuration(
        fs::absolute(argv[index]), fs::absolute(argv[index + 1]));
      targets.push_back(std::move(target));
    }
  std::sort(targets.begin(), targets.end(), [](const auto& left,
                                                const auto& right) {
    return left.configuration.year < right.configuration.year;
  });
  require(std::adjacent_find(
            targets.begin(), targets.end(), [](const auto& left,
                                                const auto& right) {
              return left.configuration.year == right.configuration.year;
            }) == targets.end(),
          "target profiles contain a duplicate year");
  for (const target_values& target : targets)
    require(target.configuration.h3_resolution
              == targets.front().configuration.h3_resolution
              && target.configuration.baseline_start
                   == targets.front().configuration.baseline_start
              && target.configuration.minimum_history_years
                   == targets.front().configuration.minimum_history_years
              && target.configuration.source_manifest_sha256
                   == targets.front().configuration.source_manifest_sha256,
            "target profiles disagree on CPC processing contract");

  GDALAllRegister();
  const std::vector<H3Index> cells = global_cells(
    targets.front().configuration.h3_resolution);
  const std::vector<std::uint32_t> grid_cells = pixel_cells(
    cells, targets.front().configuration.h3_resolution);
  for (target_values& target : targets)
    {
      target.record_high_days.resize(cells.size());
      target.record_low_days.resize(cells.size());
      target.tmax_valid_days.resize(cells.size());
      target.tmin_valid_days.resize(cells.size());
    }
  process_variable(input_directory, "tmax", true,
                   cells, grid_cells, targets);
  process_variable(input_directory, "tmin", false,
                   cells, grid_cells, targets);
  for (const target_values& target : targets)
    {
      write_geojson(target, cells);
      std::cout << "wrote " << target.configuration.output_path << " with "
                << cells.size() << " explicit H3 cells\n";
    }
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
      std::cerr << "prepare-anthropocene-temperature: "
                << error.what() << '\n';
      return 1;
    }
}
