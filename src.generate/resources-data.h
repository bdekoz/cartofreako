// Strict World Game resources profile ingestion.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_RESOURCES_DATA_H
#define CART0FREAK0_RESOURCES_DATA_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iterator>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
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

enum class resource_category
{
  metals,
  industrial_materials,
  energy_feedstocks,
};

struct producer
{
  std::string historical_label;
  std::string modern_area;
  double longitude = 0;
  double latitude = 0;
  double share_percent = 0;
};

struct historical_resource
{
  unsigned index = 0;
  std::string id;
  std::string label;
  resource_category category = resource_category::metals;
  std::optional<std::uint64_t> world_total;
  std::string source_unit;
  unsigned header_pdf_page = 0;
  std::optional<unsigned> leader_pdf_page;
  std::optional<producer> leader;
};

struct modern_resource
{
  std::string id;
  std::string label;
  unsigned reference_year = 0;
  std::uint64_t world_total = 0;
  std::string unit;
  std::optional<producer> leader;
  std::string source_organization;
  std::string source_title;
  std::string source_url;
  std::string scope_note;
};

struct resources_profile
{
  fs::path path;
  std::string name;
  std::string description;
  double marker_radius = 0;
  double cluster_step = 0;
  bool show_legend = true;

  unsigned publication_year = 0;
  unsigned production_year = 0;
  std::string source_title;
  std::string source_authors;
  std::string source_publisher;
  std::string source_page_url;
  std::string source_pdf_url;
  std::string source_pdf_sha256;
  std::string source_pdf_pages;
  std::string historical_scope;
  std::string missing_semantics;
  std::string geography_semantics;
  std::vector<historical_resource> historical;

  std::string modern_separation;
  std::vector<modern_resource> modern;
};

inline std::string_view
category_name(const resource_category category)
{
  switch (category)
    {
    case resource_category::metals: return "metals";
    case resource_category::industrial_materials:
      return "industrial-materials";
    case resource_category::energy_feedstocks:
      return "energy-feedstocks";
    }
  throw std::logic_error("unhandled resource category");
}

inline resource_category
parse_category(const std::string_view value)
{
  if (value == "metals") return resource_category::metals;
  if (value == "industrial-materials")
    return resource_category::industrial_materials;
  if (value == "energy-feedstocks")
    return resource_category::energy_feedstocks;
  throw std::runtime_error("profile contains unknown resource category '"
                           + std::string(value) + "'");
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
          reject_resource_duplicate_members(
            member->value, context + "." + name);
        }
    }
  else if (value.IsArray())
    for (rj::SizeType index = 0; index < value.Size(); ++index)
      reject_resource_duplicate_members(
        value[index], context + "[" + std::to_string(index) + "]");
}

inline rj::Document
read_resources_document(const fs::path& path)
{
  std::error_code error;
  const std::uintmax_t size = fs::file_size(path, error);
  resources_require(!error, "failed to stat resources profile "
                              + path.string());
  resources_require(size > 0 && size <= 1024U * 1024U,
                    "resources profile has an invalid or excessive size: "
                      + path.string());
  std::ifstream input {path, std::ios::binary};
  resources_require(input.good(), "failed to open resources profile "
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

inline void
require_resource_members(
  const rj::Value& object,
  const std::initializer_list<std::string_view> allowed,
  const std::string_view context)
{
  resources_require(object.IsObject(), std::string(context)
                                        + " must be an object");
  for (auto member = object.MemberBegin(); member != object.MemberEnd();
       ++member)
    {
      const std::string_view name {
        member->name.GetString(), member->name.GetStringLength()};
      resources_require(std::find(allowed.begin(), allowed.end(), name)
                          != allowed.end(),
                        std::string(context) + " contains unknown member '"
                          + std::string(name) + "'");
    }
  for (const std::string_view expected : allowed)
    {
      bool found = false;
      for (auto member = object.MemberBegin(); member != object.MemberEnd();
           ++member)
        if (expected == std::string_view(
              member->name.GetString(), member->name.GetStringLength()))
          {
            found = true;
            break;
          }
      resources_require(found, std::string(context) + " is missing '"
                                 + std::string(expected) + "'");
    }
}

inline const rj::Value&
required_resource_member(const rj::Value& object, const char* name,
                         const std::string_view context)
{
  resources_require(object.IsObject() && object.HasMember(name),
                    std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_resource_string(const rj::Value& object, const char* name,
                         const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  resources_require(value.IsString(), std::string(context) + "." + name
                                         + " must be a string");
  const std::string result(value.GetString(), value.GetStringLength());
  resources_require(!result.empty() && result.size() <= 4096,
                    std::string(context) + "." + name
                      + " must be a nonempty bounded string");
  return result;
}

inline std::uint64_t
required_resource_uint64(const rj::Value& object, const char* name,
                         const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  resources_require(value.IsUint64(), std::string(context) + "." + name
                                         + " must be an unsigned integer");
  return value.GetUint64();
}

inline unsigned
required_resource_uint(const rj::Value& object, const char* name,
                       const std::string_view context)
{
  const std::uint64_t value = required_resource_uint64(
    object, name, context);
  resources_require(value <= std::numeric_limits<unsigned>::max(),
                    std::string(context) + "." + name + " is too large");
  return static_cast<unsigned>(value);
}

inline double
required_resource_number(const rj::Value& object, const char* name,
                         const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  resources_require(value.IsNumber() && std::isfinite(value.GetDouble()),
                    std::string(context) + "." + name
                      + " must be a finite number");
  return value.GetDouble();
}

inline bool
required_resource_bool(const rj::Value& object, const char* name,
                       const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  resources_require(value.IsBool(), std::string(context) + "." + name
                                       + " must be a Boolean");
  return value.GetBool();
}

inline bool
valid_resource_id(const std::string_view value)
{
  if (value.empty() || value.front() < 'a' || value.front() > 'z')
    return false;
  return std::all_of(value.begin(), value.end(), [](const unsigned char item) {
    return (item >= 'a' && item <= 'z') || (item >= '0' && item <= '9')
           || item == '-';
  });
}

inline void
require_https_url(const std::string& value, const std::string_view context)
{
  resources_require(value.starts_with("https://"),
                    std::string(context) + " must be an HTTPS URL");
}

inline bool
hexadecimal_digit(const char value)
{
  return (value >= '0' && value <= '9') || (value >= 'a' && value <= 'f')
         || (value >= 'A' && value <= 'F');
}

inline producer
parse_producer(const rj::Value& value, const std::string_view context)
{
  require_resource_members(value,
    {"historical_label", "modern_area", "longitude", "latitude",
     "share_percent"}, context);
  producer result;
  result.historical_label = required_resource_string(
    value, "historical_label", context);
  result.modern_area = required_resource_string(value, "modern_area", context);
  result.longitude = required_resource_number(value, "longitude", context);
  result.latitude = required_resource_number(value, "latitude", context);
  result.share_percent = required_resource_number(
    value, "share_percent", context);
  resources_require(result.longitude >= -180 && result.longitude <= 180
                      && result.latitude >= -90 && result.latitude <= 90,
                    std::string(context) + " has an invalid representative "
                      "coordinate");
  resources_require(result.share_percent > 0 && result.share_percent <= 100,
                    std::string(context)
                      + ".share_percent must be in (0, 100]");
  return result;
}

inline std::optional<producer>
parse_optional_producer(const rj::Value& object, const char* name,
                        const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  if (value.IsNull())
    return std::nullopt;
  return parse_producer(value, std::string(context) + "." + name);
}

inline std::optional<std::uint64_t>
parse_optional_resource_uint64(const rj::Value& object, const char* name,
                               const std::string_view context)
{
  const rj::Value& value = required_resource_member(object, name, context);
  resources_require(value.IsNull() || value.IsUint64(),
                    std::string(context) + "." + name
                      + " must be null or an unsigned integer");
  if (value.IsNull())
    return std::nullopt;
  return value.GetUint64();
}

inline std::optional<unsigned>
parse_optional_resource_uint(const rj::Value& object, const char* name,
                             const std::string_view context)
{
  const std::optional<std::uint64_t> value = parse_optional_resource_uint64(
    object, name, context);
  resources_require(!value.has_value()
                      || *value <= std::numeric_limits<unsigned>::max(),
                    std::string(context) + "." + name + " is too large");
  return value.has_value()
    ? std::optional<unsigned>(static_cast<unsigned>(*value)) : std::nullopt;
}

inline historical_resource
parse_historical_resource(const rj::Value& value, const std::size_t position)
{
  const std::string context = "historical.records["
    + std::to_string(position) + "]";
  require_resource_members(value,
    {"index", "id", "label", "category", "world_total", "source_unit",
     "header_pdf_page", "leader_pdf_page", "leader"}, context);
  historical_resource result;
  result.index = required_resource_uint(value, "index", context);
  result.id = required_resource_string(value, "id", context);
  result.label = required_resource_string(value, "label", context);
  result.category = parse_category(required_resource_string(
    value, "category", context));
  result.world_total = parse_optional_resource_uint64(
    value, "world_total", context);
  result.source_unit = required_resource_string(value, "source_unit", context);
  result.header_pdf_page = required_resource_uint(
    value, "header_pdf_page", context);
  result.leader_pdf_page = parse_optional_resource_uint(
    value, "leader_pdf_page", context);
  result.leader = parse_optional_producer(value, "leader", context);

  resources_require(result.index == position + 1,
                    context + ".index must preserve source column order");
  resources_require(valid_resource_id(result.id),
                    context + ".id is not lower-case kebab-case");
  resources_require(result.header_pdf_page >= 62
                      && result.header_pdf_page <= 65,
                    context + ".header_pdf_page is outside the table header");
  resources_require(!result.leader_pdf_page.has_value()
                      || (*result.leader_pdf_page >= 62
                          && *result.leader_pdf_page <= 73),
                    context + ".leader_pdf_page is outside the table");
  resources_require(result.leader.has_value()
                      == result.leader_pdf_page.has_value(),
                    context + " leader and leader_pdf_page must both be null "
                      "or both be reported");
  resources_require(result.world_total.has_value() == result.leader.has_value(),
                    context + " world_total and leader availability differ");
  if (result.world_total.has_value())
    resources_require(*result.world_total > 0
                        && result.source_unit != "N.A.",
                      context + " reports an invalid total or source unit");
  else
    resources_require(result.source_unit == "N.A.",
                      context + " unavailable data must use source unit N.A.");
  return result;
}

inline modern_resource
parse_modern_resource(const rj::Value& value, const std::size_t position)
{
  const std::string context = "modern_context.records["
    + std::to_string(position) + "]";
  require_resource_members(value,
    {"id", "label", "reference_year", "world_total", "unit", "leader",
     "source_organization", "source_title", "source_url", "scope_note"},
    context);
  modern_resource result;
  result.id = required_resource_string(value, "id", context);
  result.label = required_resource_string(value, "label", context);
  result.reference_year = required_resource_uint(
    value, "reference_year", context);
  result.world_total = required_resource_uint64(value, "world_total", context);
  result.unit = required_resource_string(value, "unit", context);
  result.leader = parse_optional_producer(value, "leader", context);
  result.source_organization = required_resource_string(
    value, "source_organization", context);
  result.source_title = required_resource_string(
    value, "source_title", context);
  result.source_url = required_resource_string(value, "source_url", context);
  result.scope_note = required_resource_string(value, "scope_note", context);
  resources_require(valid_resource_id(result.id),
                    context + ".id is not lower-case kebab-case");
  resources_require(result.reference_year >= 1961
                      && result.reference_year <= 2500,
                    context + ".reference_year is outside the supported range");
  resources_require(result.world_total > 0,
                    context + ".world_total must be positive");
  require_https_url(result.source_url, context + ".source_url");
  return result;
}

inline resources_profile
load_resources_profile(const fs::path& path)
{
  const rj::Document document = read_resources_document(path);
  require_resource_members(document,
    {"schema", "name", "description", "display", "historical",
     "modern_context"}, path.string());
  resources_require(required_resource_string(document, "schema", path.string())
                      == "cartofreako-resources-profile-v1",
                    "unsupported resources profile schema");

  resources_profile result;
  result.path = path;
  result.name = required_resource_string(document, "name", path.string());
  result.description = required_resource_string(
    document, "description", path.string());

  const rj::Value& display = required_resource_member(
    document, "display", path.string());
  require_resource_members(display,
    {"marker_radius", "cluster_step", "show_legend"}, "display");
  result.marker_radius = required_resource_number(
    display, "marker_radius", "display");
  result.cluster_step = required_resource_number(
    display, "cluster_step", "display");
  result.show_legend = required_resource_bool(
    display, "show_legend", "display");
  resources_require(result.marker_radius > 0 && result.marker_radius <= 0.5
                      && result.cluster_step >= 2 * result.marker_radius
                      && result.cluster_step <= 2,
                    "display marker radius or cluster step is invalid");

  const rj::Value& historical = required_resource_member(
    document, "historical", path.string());
  require_resource_members(historical,
    {"publication_year", "production_year", "record_count", "source_title",
     "source_authors", "source_publisher", "source_page_url",
     "source_pdf_url", "source_pdf_sha256", "source_pdf_pages", "scope",
     "missing_semantics", "geography_semantics", "records"}, "historical");
  result.publication_year = required_resource_uint(
    historical, "publication_year", "historical");
  result.production_year = required_resource_uint(
    historical, "production_year", "historical");
  resources_require(result.publication_year == 1963
                      && result.production_year == 1960,
                    "historical source years must be publication 1963 and "
                      "production 1960");
  result.source_title = required_resource_string(
    historical, "source_title", "historical");
  result.source_authors = required_resource_string(
    historical, "source_authors", "historical");
  result.source_publisher = required_resource_string(
    historical, "source_publisher", "historical");
  result.source_page_url = required_resource_string(
    historical, "source_page_url", "historical");
  result.source_pdf_url = required_resource_string(
    historical, "source_pdf_url", "historical");
  result.source_pdf_sha256 = required_resource_string(
    historical, "source_pdf_sha256", "historical");
  result.source_pdf_pages = required_resource_string(
    historical, "source_pdf_pages", "historical");
  result.historical_scope = required_resource_string(
    historical, "scope", "historical");
  result.missing_semantics = required_resource_string(
    historical, "missing_semantics", "historical");
  result.geography_semantics = required_resource_string(
    historical, "geography_semantics", "historical");
  require_https_url(result.source_page_url, "historical.source_page_url");
  require_https_url(result.source_pdf_url, "historical.source_pdf_url");
  resources_require(result.source_pdf_sha256.size() == 64
                      && std::all_of(result.source_pdf_sha256.begin(),
                                     result.source_pdf_sha256.end(),
                                     hexadecimal_digit),
                    "historical.source_pdf_sha256 must contain 64 "
                      "hexadecimal digits");

  const rj::Value& records = required_resource_member(
    historical, "records", "historical");
  resources_require(records.IsArray(),
                    "historical.records must be an array");
  const std::uint64_t declared_count = required_resource_uint64(
    historical, "record_count", "historical");
  resources_require(declared_count == records.Size()
                      && records.Size() == 40,
                    "historical.record_count and the required 40 records "
                      "must agree");
  std::unordered_set<std::string> ids;
  std::array<unsigned, 3> category_counts {};
  std::size_t unavailable_count = 0;
  for (rj::SizeType index = 0; index < records.Size(); ++index)
    {
      historical_resource record = parse_historical_resource(
        records[index], index);
      resources_require(ids.insert(record.id).second,
                        "duplicate resource id '" + record.id + "'");
      ++category_counts[static_cast<std::size_t>(record.category)];
      if (!record.leader.has_value())
        {
          ++unavailable_count;
          resources_require(record.id == "thorium",
                            "the v1 unavailable historical row must be thorium");
        }
      result.historical.push_back(std::move(record));
    }
  resources_require(std::all_of(category_counts.begin(), category_counts.end(),
                                [](const unsigned count) { return count > 0; }),
                    "historical records must include every category");
  resources_require(unavailable_count == 1,
                    "historical records must preserve the single N.A. row");

  const rj::Value& modern = required_resource_member(
    document, "modern_context", path.string());
  require_resource_members(modern, {"separation", "records"},
                           "modern_context");
  result.modern_separation = required_resource_string(
    modern, "separation", "modern_context");
  const rj::Value& modern_records = required_resource_member(
    modern, "records", "modern_context");
  resources_require(modern_records.IsArray() && !modern_records.Empty()
                      && modern_records.Size() <= 32,
                    "modern_context.records must contain 1 to 32 records");
  for (rj::SizeType index = 0; index < modern_records.Size(); ++index)
    {
      modern_resource record = parse_modern_resource(
        modern_records[index], index);
      resources_require(ids.insert(record.id).second,
                        "duplicate resource id '" + record.id + "'");
      result.modern.push_back(std::move(record));
    }
  return result;
}

} // namespace cart0freak0::resources_generation

#endif // CART0FREAK0_RESOURCES_DATA_H
