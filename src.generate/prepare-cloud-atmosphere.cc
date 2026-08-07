// Aggregate JAXA COG and P-Tree NetCDF rasters into a deterministic H3 snapshot.
// -*- mode: C++ -*-

#include <algorithm>
#include <cmath>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <numbers>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include <cpl_string.h>
#include <gdal_priv.h>
#include <h3/h3api.h>
#include <rapidjson/document.h>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>

#include "cloud-atmosphere-data.h"

namespace atmosphere = cart0freak0::cloud_atmosphere_generation;
namespace fs = std::filesystem;
namespace rj = rapidjson;

namespace {

struct dataset_deleter
{
  void operator()(GDALDataset* dataset) const noexcept
  { GDALClose(dataset); }
};

using dataset_ptr = std::unique_ptr<GDALDataset, dataset_deleter>;

struct input_file
{
  fs::path path;
  std::string source_url;
  std::string sha256;
  std::optional<double> scale;
  std::optional<double> offset;
  std::optional<double> nodata;
};

struct input_observation
{
  std::string source_id;
  std::string collection;
  cart0freak0::generation_time::instant start;
  cart0freak0::generation_time::instant end;
  std::string fetched_at_utc;
  std::string source_url;
  std::string coverage;
  std::vector<input_file> files;
};

struct fetch_manifest
{
  cart0freak0::generation_time::instant process_start;
  std::string fetched_at_utc;
  std::vector<input_observation> observations;
};

struct raster_view
{
  dataset_ptr dataset;
  GDALRasterBand* band = nullptr;
};

struct accumulator
{
  std::uint64_t total_samples = 0;
  std::uint64_t valid_samples = 0;
  double sum = 0;
  std::map<std::int64_t, std::uint64_t> frequencies;
};

using layer_aggregates = std::unordered_map<H3Index, accumulator>;

std::optional<double>
optional_number(const rj::Value& object, const char* name,
                const std::string& context)
{
  if (!object.HasMember(name) || object[name].IsNull())
    return std::nullopt;
  atmosphere::atmosphere_require(object[name].IsNumber()
                                   && std::isfinite(object[name].GetDouble()),
                                 context + "." + name
                                   + " must be null or a finite number");
  return object[name].GetDouble();
}

fetch_manifest
load_manifest(const fs::path& path)
{
  const rj::Document document = atmosphere::read_json_document(path);
  atmosphere::atmosphere_require(
    atmosphere::required_string(document, "schema", path.string())
      == "cartofreako-cloud-atmosphere-fetch-v1",
    "unsupported cloud-atmosphere fetch manifest schema");
  atmosphere::atmosphere_require(
    atmosphere::required_string(document, "selection", path.string())
      == "latest-not-after",
    "fetch manifest must use latest-not-after selection");
  fetch_manifest result {
    cart0freak0::generation_time::parse_timestamp(
      atmosphere::required_string(document, "process_start_utc", path.string())),
    atmosphere::required_string(document, "fetched_at_utc", path.string()),
    {},
  };
  const rj::Value& observations = atmosphere::required_member(
    document, "observations", path.string());
  atmosphere::atmosphere_require(observations.IsArray()
                                   && !observations.Empty(),
                                 "fetch manifest observations must be nonempty");
  std::set<std::string> source_ids;
  for (const rj::Value& value : observations.GetArray())
    {
      const std::string context = "observations["
        + std::to_string(result.observations.size()) + "]";
      input_observation observation {
        atmosphere::required_string(value, "source", context),
        atmosphere::required_string(value, "collection", context),
        cart0freak0::generation_time::parse_timestamp(
          atmosphere::required_string(value, "start_utc", context)),
        cart0freak0::generation_time::parse_timestamp(
          atmosphere::required_string(value, "end_utc", context)),
        atmosphere::required_string(value, "fetched_at_utc", context),
        atmosphere::required_string(value, "source_url", context),
        atmosphere::required_string(value, "coverage", context),
        {},
      };
      atmosphere::atmosphere_require(
        source_ids.emplace(observation.source_id).second,
        "fetch manifest repeats source " + observation.source_id);
      atmosphere::atmosphere_require(
        observation.start.value <= observation.end.value
          && observation.end.value <= result.process_start.value,
        "fetch manifest source " + observation.source_id
          + " is not latest-not-after process start");
      const rj::Value& files = atmosphere::required_member(
        value, "files", context);
      atmosphere::atmosphere_require(files.IsArray() && !files.Empty(),
                                    context + ".files must be nonempty");
      for (const rj::Value& file : files.GetArray())
        {
          const std::string file_context = context + ".files["
            + std::to_string(observation.files.size()) + "]";
          input_file parsed {
            path.parent_path() / atmosphere::required_string(
              file, "path", file_context),
            atmosphere::required_string(file, "source_url", file_context),
            atmosphere::required_string(file, "sha256", file_context),
            optional_number(file, "scale", file_context),
            optional_number(file, "offset", file_context),
            optional_number(file, "nodata", file_context),
          };
          atmosphere::atmosphere_require(fs::is_regular_file(parsed.path),
                                        "missing fetched raster "
                                          + parsed.path.string());
          observation.files.push_back(std::move(parsed));
        }
      result.observations.push_back(std::move(observation));
    }
  return result;
}

const input_observation&
find_observation(const fetch_manifest& manifest,
                 const std::string_view source_id)
{
  const auto found = std::find_if(
    manifest.observations.begin(), manifest.observations.end(),
    [source_id](const input_observation& observation) {
      return observation.source_id == source_id;
    });
  atmosphere::atmosphere_require(found != manifest.observations.end(),
                                 "fetch manifest lacks source "
                                   + std::string(source_id));
  return *found;
}

std::string
lowercase(std::string value)
{
  std::transform(value.begin(), value.end(), value.begin(),
                 [](const unsigned char character) {
                   return static_cast<char>(std::tolower(character));
                 });
  return value;
}

bool
candidate_match(const std::string& text,
                const std::vector<std::string>& candidates)
{
  const std::string normalized = lowercase(text);
  return std::any_of(candidates.begin(), candidates.end(),
                     [&](const std::string& candidate) {
                       return normalized.find(lowercase(candidate))
                         != std::string::npos;
                     });
}

dataset_ptr
open_dataset(const std::string& name, const fs::path& display_path)
{
  dataset_ptr result(static_cast<GDALDataset*>(GDALOpenEx(
    name.c_str(), GDAL_OF_RASTER | GDAL_OF_READONLY, nullptr, nullptr,
    nullptr)));
  atmosphere::atmosphere_require(result != nullptr,
                                 "GDAL failed to open "
                                   + display_path.string());
  return result;
}

raster_view
open_raster(const fs::path& path,
            const std::vector<std::string>& candidates)
{
  dataset_ptr root = open_dataset(path.string(), path);
  if (root->GetRasterCount() > 0)
    {
      GDALRasterBand* selected = nullptr;
      for (int index = 1; index <= root->GetRasterCount(); ++index)
        {
          GDALRasterBand* candidate = root->GetRasterBand(index);
          const std::string description = candidate->GetDescription();
          if (candidate_match(description, candidates))
            {
              selected = candidate;
              break;
            }
        }
      // A one-band COG is unambiguous even when its band description is
      // empty. Never guess band one in a multi-band raster.
      if (selected == nullptr && root->GetRasterCount() == 1)
        selected = root->GetRasterBand(1);
      atmosphere::atmosphere_require(
        selected != nullptr,
        "none of the configured variables matches a band in "
          + path.string());
      return {std::move(root), selected};
    }

  char** subdatasets = root->GetMetadata("SUBDATASETS");
  atmosphere::atmosphere_require(subdatasets != nullptr,
                                 "raster has no bands or subdatasets: "
                                   + path.string());
  for (int index = 0; subdatasets[index] != nullptr; ++index)
    {
      const std::string entry = subdatasets[index];
      const std::size_t separator = entry.find('=');
      if (separator == std::string::npos
          || !entry.substr(0, separator).ends_with("_NAME"))
        continue;
      const std::string name = entry.substr(separator + 1);
      if (!candidate_match(name, candidates))
        continue;
      dataset_ptr selected = open_dataset(name, path);
      atmosphere::atmosphere_require(selected->GetRasterCount() > 0,
                                     "selected NetCDF variable has no raster band: "
                                       + name);
      GDALRasterBand* band = selected->GetRasterBand(1);
      return {std::move(selected), band};
    }
  std::string names;
  for (const std::string& candidate : candidates)
    names += (names.empty() ? "" : ", ") + candidate;
  throw std::runtime_error("none of the configured variables [" + names
                           + "] exists in " + path.string());
}

std::array<double, 6>
geotransform(GDALDataset& dataset)
{
  std::array<double, 6> transform {};
  if (dataset.GetGeoTransform(transform.data()) == CE_None)
    return transform;
  const int width = dataset.GetRasterXSize();
  const int height = dataset.GetRasterYSize();
  // P-Tree CLP 1.0 is an equidistant cylindrical 0.05-degree grid. Published
  // longitude/latitude coordinates identify pixel centers, whereas a GDAL
  // geotransform identifies the upper-left pixel corner. The historic
  // 2401-column product begins at 80E; a future-compatible expanded grid
  // begins at 70E. This fallback is used only when NetCDF lacks CF tags.
  if (height == 2401 && (width == 2401 || width == 2801))
    return {width == 2801 ? 69.975 : 79.975, 0.05, 0.0,
            60.025, 0.0, -0.05};
  throw std::runtime_error("raster lacks georeferencing and is not a known "
                           "P-Tree CLP grid");
}

std::vector<double>
read_resampled(GDALRasterBand& band, const int width, const int height)
{
  std::vector<double> values(static_cast<std::size_t>(width)
                             * static_cast<std::size_t>(height));
  atmosphere::atmosphere_require(
    band.RasterIO(GF_Read, 0, 0, band.GetXSize(), band.GetYSize(),
                  values.data(), width, height, GDT_Float64,
                  0, 0, nullptr) == CE_None,
    "GDAL failed to read/resample atmosphere raster band");
  return values;
}

bool
same_raw_value(const double left, const double right)
{
  const double tolerance = std::max(1.0, std::abs(right)) * 1e-10;
  return std::abs(left - right) <= tolerance;
}

bool
quality_accepts(const double raw, const atmosphere::quality_rule& rule)
{
  if (!std::isfinite(raw) || raw < 0
      || raw > std::numeric_limits<std::uint32_t>::max())
    return false;
  const auto bits = static_cast<std::uint32_t>(std::llround(raw));
  const std::uint32_t mask = (std::uint32_t {1} << rule.bit_width) - 1;
  const unsigned value = (bits >> rule.bit_offset) & mask;
  return std::find(rule.accepted_values.begin(), rule.accepted_values.end(),
                   value) != rule.accepted_values.end();
}

double
unit_multiplier(const atmosphere::layer_definition& layer,
                GDALRasterBand& band)
{
  const std::string unit = lowercase(band.GetUnitType());
  if (layer.unit == "km"
      && (unit == "m" || unit == "meter" || unit == "metre"))
    return 0.001;
  return 1;
}

void
sample_file(const atmosphere::atmosphere_profile& profile,
            const atmosphere::layer_definition& layer,
            const input_file& file, layer_aggregates& output)
{
  raster_view value = open_raster(file.path, layer.variable_candidates);
  std::optional<raster_view> quality;
  if (layer.quality.has_value()
      && layer.aggregation != atmosphere::aggregation_kind::cloud_fraction)
    quality = open_raster(file.path, layer.quality->variable_candidates);
  const int source_width = value.dataset->GetRasterXSize();
  const int source_height = value.dataset->GetRasterYSize();
  atmosphere::atmosphere_require(source_width > 0 && source_height > 0,
                                 "atmosphere raster is empty: "
                                   + file.path.string());
  const double reduction = std::max(
    1.0, static_cast<double>(std::max(source_width, source_height))
      / profile.maximum_samples_per_axis);
  const int width = std::max(1, static_cast<int>(
    std::ceil(source_width / reduction)));
  const int height = std::max(1, static_cast<int>(
    std::ceil(source_height / reduction)));
  const std::vector<double> values = read_resampled(*value.band, width, height);
  std::vector<double> quality_values;
  if (quality.has_value())
    {
      atmosphere::atmosphere_require(
        quality->dataset->GetRasterXSize() == source_width
          && quality->dataset->GetRasterYSize() == source_height,
        "quality and value rasters have different dimensions in "
          + file.path.string());
      quality_values = read_resampled(*quality->band, width, height);
    }
  const std::array<double, 6> transform = geotransform(*value.dataset);

  int has_scale = 0;
  int has_offset = 0;
  int has_nodata = 0;
  const double band_scale = value.band->GetScale(&has_scale);
  const double band_offset = value.band->GetOffset(&has_offset);
  const double band_nodata = value.band->GetNoDataValue(&has_nodata);
  const double scale = file.scale.value_or(has_scale ? band_scale : 1.0);
  const double offset = file.offset.value_or(has_offset ? band_offset : 0.0);
  const std::optional<double> nodata = file.nodata.has_value()
    ? file.nodata : (has_nodata ? std::optional<double> {band_nodata}
                                : std::nullopt);
  const double units = unit_multiplier(layer, *value.band);

  for (int row = 0; row < height; ++row)
    for (int column = 0; column < width; ++column)
      {
        const double pixel_x = (column + 0.5) * source_width / width;
        const double pixel_y = (row + 0.5) * source_height / height;
        double longitude = transform[0] + pixel_x * transform[1]
          + pixel_y * transform[2];
        const double latitude = transform[3] + pixel_x * transform[4]
          + pixel_y * transform[5];
        while (longitude > 180)
          longitude -= 360;
        while (longitude < -180)
          longitude += 360;
        if (!std::isfinite(latitude) || !std::isfinite(longitude)
            || latitude < -90 || latitude > 90)
          continue;
        const LatLng position {
          latitude * std::numbers::pi / 180.0,
          longitude * std::numbers::pi / 180.0,
        };
        H3Index cell = H3_NULL;
        atmosphere::atmosphere_require(
          latLngToCell(&position, static_cast<int>(profile.h3_resolution),
                       &cell) == E_SUCCESS && cell != H3_NULL,
          "failed to aggregate atmosphere sample to H3");
        accumulator& aggregate = output[cell];
        ++aggregate.total_samples;
        const std::size_t index = static_cast<std::size_t>(row) * width
          + static_cast<std::size_t>(column);
        const double raw = values[index];
        if (!std::isfinite(raw)
            || (nodata.has_value() && same_raw_value(raw, *nodata)))
          continue;

        if (layer.aggregation == atmosphere::aggregation_kind::cloud_fraction)
          {
            atmosphere::atmosphere_require(layer.quality.has_value(),
              "cloud-fraction aggregation requires a quality bit rule");
            aggregate.sum += quality_accepts(raw, *layer.quality) ? 1.0 : 0.0;
            ++aggregate.valid_samples;
            continue;
          }
        if (layer.quality.has_value()
            && !quality_accepts(quality_values[index], *layer.quality))
          continue;
        const double physical = (raw * scale + offset) * units;
        if (!std::isfinite(physical)
            || physical < layer.scale_min
            || physical > layer.scale_max * 10)
          continue;
        ++aggregate.valid_samples;
        if (layer.aggregation == atmosphere::aggregation_kind::mode)
          ++aggregate.frequencies[static_cast<std::int64_t>(
            std::llround(physical))];
        else
          aggregate.sum += physical;
      }
}

std::optional<double>
aggregate_value(const accumulator& aggregate,
                const atmosphere::layer_definition& layer,
                const atmosphere::atmosphere_profile& profile,
                double& valid_fraction)
{
  if (aggregate.total_samples == 0)
    return std::nullopt;
  valid_fraction = static_cast<double>(aggregate.valid_samples)
    / aggregate.total_samples;
  if (aggregate.valid_samples == 0
      || valid_fraction < profile.minimum_valid_fraction)
    return std::nullopt;
  if (layer.aggregation == atmosphere::aggregation_kind::mode)
    {
      atmosphere::atmosphere_require(!aggregate.frequencies.empty(),
                                     "mode aggregate has no frequencies");
      const auto found = std::max_element(
        aggregate.frequencies.begin(), aggregate.frequencies.end(),
        [](const auto& left, const auto& right) {
          return left.second < right.second
            || (left.second == right.second && left.first > right.first);
        });
      return static_cast<double>(found->first);
    }
  return aggregate.sum / aggregate.valid_samples;
}

std::string
observation_digest(const input_observation& observation)
{
  if (observation.files.size() == 1)
    return observation.files.front().sha256;
  std::string result = "mosaic:";
  for (const input_file& file : observation.files)
    result += (result == "mosaic:" ? "" : ",") + file.sha256;
  return result;
}

void
write_snapshot(const fs::path& output_path,
               const atmosphere::atmosphere_profile& profile,
               const fetch_manifest& manifest,
               const std::vector<layer_aggregates>& aggregates)
{
  std::set<H3Index> cells;
  for (const layer_aggregates& layer : aggregates)
    for (const auto& [cell, unused] : layer)
      {
        static_cast<void>(unused);
        cells.insert(cell);
      }
  atmosphere::atmosphere_require(!cells.empty(),
                                 "atmosphere preparation produced no H3 cells");
  fs::create_directories(output_path.parent_path());
  const fs::path temporary = output_path.string() + ".tmp";
  std::ofstream stream {temporary, std::ios::binary};
  atmosphere::atmosphere_require(stream.good(),
                                 "failed to open output " + temporary.string());
  rj::OStreamWrapper wrapper(stream);
  rj::Writer<rj::OStreamWrapper> writer(wrapper);
  writer.StartObject();
  writer.Key("type"); writer.String("FeatureCollection");
  writer.Key("metadata"); writer.StartObject();
  writer.Key("schema");
  writer.String("cartofreako-cloud-atmosphere-snapshot-v1");
  writer.Key("fixture"); writer.Bool(false);
  writer.Key("prepared_at_utc");
  writer.String(cart0freak0::generation_time::process_start_instant()
                  .iso_utc.c_str());
  writer.Key("source_selection_process_start_utc");
  writer.String(manifest.process_start.iso_utc.c_str());
  writer.Key("h3_resolution"); writer.Uint(profile.h3_resolution);
  writer.Key("missing_semantics"); writer.String("unobserved-not-zero");
  writer.Key("observations"); writer.StartArray();
  for (const input_observation& observation : manifest.observations)
    {
      writer.StartObject();
      writer.Key("source"); writer.String(observation.source_id.c_str());
      writer.Key("start_utc"); writer.String(observation.start.iso_utc.c_str());
      writer.Key("end_utc"); writer.String(observation.end.iso_utc.c_str());
      writer.Key("fetched_at_utc");
      writer.String(observation.fetched_at_utc.c_str());
      writer.Key("source_url"); writer.String(observation.source_url.c_str());
      writer.Key("sha256");
      const std::string digest = observation_digest(observation);
      writer.String(digest.c_str());
      writer.Key("coverage"); writer.String(observation.coverage.c_str());
      writer.Key("asset_count");
      writer.Uint64(static_cast<std::uint64_t>(observation.files.size()));
      writer.EndObject();
    }
  writer.EndArray();
  writer.EndObject();
  writer.Key("features"); writer.StartArray();
  std::size_t feature_count = 0;
  for (const H3Index cell : cells)
    {
      std::vector<std::optional<double>> values(profile.layers.size());
      std::vector<double> fractions(profile.layers.size());
      bool populated = false;
      for (std::size_t index = 0; index < profile.layers.size(); ++index)
        {
          const auto found = aggregates[index].find(cell);
          if (found == aggregates[index].end())
            continue;
          values[index] = aggregate_value(
            found->second, profile.layers[index], profile, fractions[index]);
          populated = populated || values[index].has_value();
        }
      if (!populated)
        continue;
      LatLng center {};
      atmosphere::atmosphere_require(cellToLatLng(cell, &center) == E_SUCCESS,
                                     "failed to calculate prepared H3 center");
      char h3_text[32] {};
      atmosphere::atmosphere_require(
        h3ToString(cell, h3_text, sizeof(h3_text)) == E_SUCCESS,
        "failed to serialize prepared H3 index");
      writer.StartObject();
      writer.Key("type"); writer.String("Feature");
      writer.Key("geometry"); writer.StartObject();
      writer.Key("type"); writer.String("Point");
      writer.Key("coordinates"); writer.StartArray();
      writer.Double(center.lng * 180.0 / std::numbers::pi);
      writer.Double(center.lat * 180.0 / std::numbers::pi);
      writer.EndArray(); writer.EndObject();
      writer.Key("properties"); writer.StartObject();
      writer.Key("h3"); writer.String(h3_text);
      writer.Key("values"); writer.StartObject();
      for (std::size_t index = 0; index < profile.layers.size(); ++index)
        if (values[index].has_value())
          {
            writer.Key(profile.layers[index].property.c_str());
            writer.Double(*values[index]);
          }
      writer.EndObject();
      writer.Key("valid_fraction"); writer.StartObject();
      for (std::size_t index = 0; index < profile.layers.size(); ++index)
        if (values[index].has_value())
          {
            writer.Key(profile.layers[index].property.c_str());
            writer.Double(fractions[index]);
          }
      writer.EndObject();
      writer.EndObject();
      writer.EndObject();
      ++feature_count;
    }
  writer.EndArray();
  writer.EndObject();
  stream << '\n';
  stream.close();
  atmosphere::atmosphere_require(stream.good(),
                                 "failed to write " + temporary.string());
  atmosphere::atmosphere_require(feature_count > 0,
                                 "prepared atmosphere snapshot is empty");
  fs::rename(temporary, output_path);
  std::cout << "prepared " << feature_count << " H3 r"
            << profile.h3_resolution << " cells in " << output_path << '\n';
}

int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: prepare-cloud-atmosphere PROFILE.json FETCH-MANIFEST.json OUTPUT.geojson");
  GDALAllRegister();
  const atmosphere::atmosphere_profile profile
    = atmosphere::load_atmosphere_profile(fs::absolute(argv[1]));
  const fs::path manifest_path = fs::absolute(argv[2]);
  const fetch_manifest manifest = load_manifest(manifest_path);
  std::vector<layer_aggregates> aggregates(profile.layers.size());
  for (std::size_t layer_index = 0; layer_index < profile.layers.size();
       ++layer_index)
    {
      const atmosphere::layer_definition& layer = profile.layers[layer_index];
      if (!layer.enabled)
        continue;
      const input_observation& observation = find_observation(
        manifest, layer.source_id);
      const double age = cart0freak0::generation_time::age_hours(
        manifest.process_start, observation.end);
      if (layer.freshness == atmosphere::freshness_policy::maximum_age)
        atmosphere::atmosphere_require(
          age <= layer.maximum_age_hours,
          "fetch source " + layer.source_id + " is stale for " + layer.id);
      for (const input_file& file : observation.files)
        sample_file(profile, layer, file, aggregates[layer_index]);
      std::cout << layer.id << ": " << aggregates[layer_index].size()
                << " sampled H3 cells\n";
    }
  write_snapshot(fs::absolute(argv[3]), profile, manifest, aggregates);
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
      std::cerr << "prepare-cloud-atmosphere: " << error.what() << '\n';
      return 1;
    }
}
