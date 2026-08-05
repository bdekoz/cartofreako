// Orbital Technosphere profile, OMM ingestion, and SGP4 state derivation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ORBITING_DATA_H
#define CART0FREAK0_ORBITING_DATA_H 1

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <numbers>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

#include "third_party/sgp4/SGP4.h"

namespace cart0freak0::orbiting_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline constexpr double julian_unix_epoch = 2440587.5;
inline constexpr double seconds_per_day = 86400.0;
inline constexpr double minutes_per_day = 1440.0;
inline constexpr double earth_equatorial_radius_km = 6378.137;
inline constexpr double earth_flattening = 1.0 / 298.257223563;
inline constexpr double earth_eccentricity_squared
  = earth_flattening * (2.0 - earth_flattening);

inline void
orbiting_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline double
degrees_to_radians(const double degrees)
{ return degrees * std::numbers::pi / 180.0; }

inline double
radians_to_degrees(const double radians)
{ return radians * 180.0 / std::numbers::pi; }

inline double
normalize_degrees(double degrees)
{
  degrees = std::fmod(degrees, 360.0);
  if (degrees < 0)
    degrees += 360.0;
  return degrees;
}

inline double
normalize_signed_degrees(const double degrees)
{
  double result = normalize_degrees(degrees);
  if (result > 180.0)
    result -= 360.0;
  return result;
}

inline int
decimal_component(const std::string_view text, const std::size_t offset,
                  const std::size_t count, const std::string_view name)
{
  orbiting_require(offset + count <= text.size(),
                   "timestamp is missing " + std::string(name));
  int result = 0;
  for (std::size_t index = offset; index < offset + count; ++index)
    {
      orbiting_require(text[index] >= '0' && text[index] <= '9',
                       "timestamp has a nondecimal " + std::string(name));
      result = result * 10 + text[index] - '0';
    }
  return result;
}

struct instant
{
  std::string iso_utc;
  double julian_date;
};

inline instant
parse_timestamp(const std::string_view timestamp,
                const bool require_utc_suffix = true)
{
  orbiting_require(timestamp.size() >= 19
                     && timestamp[4] == '-' && timestamp[7] == '-'
                     && timestamp[10] == 'T' && timestamp[13] == ':'
                     && timestamp[16] == ':',
                   "timestamp must begin YYYY-MM-DDTHH:MM:SS");
  if (require_utc_suffix)
    orbiting_require(timestamp.back() == 'Z',
                     "profile timestamp must have a Z UTC suffix");

  const int year = decimal_component(timestamp, 0, 4, "year");
  const unsigned month = static_cast<unsigned>(
    decimal_component(timestamp, 5, 2, "month"));
  const unsigned day = static_cast<unsigned>(
    decimal_component(timestamp, 8, 2, "day"));
  const int hour = decimal_component(timestamp, 11, 2, "hour");
  const int minute = decimal_component(timestamp, 14, 2, "minute");
  std::size_t seconds_end = timestamp.size();
  if (timestamp.back() == 'Z')
    --seconds_end;
  const std::string seconds_text(timestamp.substr(17, seconds_end - 17));
  std::size_t consumed = 0;
  const double second = std::stod(seconds_text, &consumed);
  orbiting_require(consumed == seconds_text.size(),
                   "timestamp has an invalid seconds field");

  const std::chrono::year_month_day calendar {
    std::chrono::year {year}, std::chrono::month {month},
    std::chrono::day {day},
  };
  orbiting_require(calendar.ok(), "timestamp has an invalid calendar date");
  orbiting_require(hour >= 0 && hour <= 23
                     && minute >= 0 && minute <= 59
                     && second >= 0 && second < 61,
                   "timestamp has an invalid clock time");
  const double unix_day = std::chrono::duration<double>(
    std::chrono::sys_days {calendar}.time_since_epoch()).count()
    / seconds_per_day;
  const double julian = julian_unix_epoch + unix_day
    + (hour * 3600.0 + minute * 60.0 + second) / seconds_per_day;
  return {std::string(timestamp), julian};
}

inline rj::Document
read_json(const fs::path& path)
{
  std::ifstream input {path};
  orbiting_require(input.good(), "failed to open JSON file " + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.c_str());
  orbiting_require(
    !document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  return document;
}

inline const rj::Value&
required_member(const rj::Value& object, const char* name,
                const std::string_view context)
{
  orbiting_require(object.IsObject() && object.HasMember(name),
                   std::string(context) + " is missing '" + name + "'");
  return object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  orbiting_require(value.IsString(), std::string(context) + "." + name
                                      + " must be a string");
  return value.GetString();
}

inline double
required_number(const rj::Value& object, const char* name,
                const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  orbiting_require(value.IsNumber(), std::string(context) + "." + name
                                      + " must be a number");
  return value.GetDouble();
}

inline std::size_t
required_size(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  orbiting_require(value.IsUint64(), std::string(context) + "." + name
                                      + " must be a nonnegative integer");
  return static_cast<std::size_t>(value.GetUint64());
}

inline bool
required_bool(const rj::Value& object, const char* name,
              const std::string_view context)
{
  const rj::Value& value = required_member(object, name, context);
  orbiting_require(value.IsBool(), std::string(context) + "." + name
                                    + " must be a boolean");
  return value.GetBool();
}

struct reference_point
{
  std::string name;
  double latitude_deg;
  double longitude_deg_east;
  double elevation_m;
  std::string capture_method;
};

struct group_configuration
{
  std::string id;
  std::string role;
  fs::path file;
  std::string source_url;
};

struct propagation_configuration
{
  double maximum_element_age_days;
  double maximum_future_epoch_hours;
};

struct visibility_configuration
{
  double minimum_elevation_deg;
  bool require_sunlit;
  double maximum_solar_altitude_deg;
};

struct display_configuration
{
  std::size_t maximum_active_objects;
  std::size_t maximum_debris_per_group;
  std::size_t maximum_labels;
  std::size_t maximum_tracks_per_group;
  int track_minutes_each_side;
  int track_step_minutes;
  bool show_reference_lines;
};

struct profile
{
  fs::path path;
  std::string name;
  instant calculation_time;
  reference_point observer;
  double central_right_ascension_deg;
  propagation_configuration propagation;
  visibility_configuration visibility;
  display_configuration display;
  group_configuration primary;
  std::vector<group_configuration> groups;
  fs::path nasa_reference;
  std::string nasa_query_url;
  fs::path checksum_file;
};

inline group_configuration
load_group_configuration(const rj::Value& value, const fs::path& directory,
                         const std::string_view context)
{
  return {
    required_string(value, "id", context),
    required_string(value, "role", context),
    directory / required_string(value, "file", context),
    required_string(value, "source_url", context),
  };
}

inline profile
load_profile(const fs::path& path)
{
  const rj::Document document = read_json(path);
  orbiting_require(document.IsObject(),
                   "profile JSON root must be an object in " + path.string());
  orbiting_require(required_size(document, "schema_version", "profile") == 1,
                   "unsupported Orbital Technosphere profile schema");
  const rj::Value& products = required_member(document, "products", "profile");
  orbiting_require(products.IsArray(), "profile.products must be an array");
  bool global = false;
  bool observer = false;
  for (const rj::Value& value : products.GetArray())
    {
      orbiting_require(value.IsString(),
                       "profile.products must contain strings");
      global = global || std::string_view(value.GetString()) == "global";
      observer = observer || std::string_view(value.GetString()) == "observer";
    }
  orbiting_require(global && observer,
                   "profile.products must enable global and observer");

  const fs::path absolute_path = fs::absolute(path);
  const fs::path directory = absolute_path.parent_path();
  const rj::Value& point = required_member(
    document, "reference_point", "profile");
  reference_point reference {
    required_string(point, "name", "profile.reference_point"),
    required_number(point, "latitude_deg", "profile.reference_point"),
    required_number(point, "longitude_deg_east", "profile.reference_point"),
    required_number(point, "elevation_m", "profile.reference_point"),
    required_string(point, "capture_method", "profile.reference_point"),
  };
  orbiting_require(reference.latitude_deg >= -90
                     && reference.latitude_deg <= 90,
                   "reference latitude must be in [-90, 90]");
  orbiting_require(reference.longitude_deg_east >= -180
                     && reference.longitude_deg_east <= 180,
                   "reference longitude must be in [-180, 180]");

  const rj::Value& orientation = required_member(
    document, "orientation", "profile");
  orbiting_require(required_string(
                     orientation, "observer_handedness",
                     "profile.orientation") == "celestial",
                   "observer orientation must use celestial handedness");
  const double central_ra_hours = required_number(
    orientation, "central_right_ascension_hours", "profile.orientation");
  orbiting_require(central_ra_hours >= 0 && central_ra_hours < 24,
                   "central right ascension must be in [0, 24) hours");

  const rj::Value& propagation = required_member(
    document, "propagation", "profile");
  orbiting_require(required_string(propagation, "model",
                                   "profile.propagation") == "SGP4",
                   "propagation model must be SGP4");
  orbiting_require(required_string(propagation, "gravity_model",
                                   "profile.propagation") == "WGS72",
                   "propagation gravity model must be WGS72");
  orbiting_require(required_string(propagation, "operation_mode",
                                   "profile.propagation") == "AFSPC",
                   "propagation operation mode must be AFSPC");
  propagation_configuration propagation_config {
    required_number(propagation, "maximum_element_age_days",
                    "profile.propagation"),
    required_number(propagation, "maximum_future_epoch_hours",
                    "profile.propagation"),
  };
  orbiting_require(propagation_config.maximum_element_age_days > 0
                     && propagation_config.maximum_future_epoch_hours >= 0,
                   "profile propagation epoch limits are invalid");

  const rj::Value& visibility = required_member(
    document, "visibility", "profile");
  visibility_configuration visibility_config {
    required_number(visibility, "minimum_elevation_deg", "profile.visibility"),
    required_bool(visibility, "require_sunlit_for_optical_candidate",
                  "profile.visibility"),
    required_number(visibility, "maximum_solar_altitude_deg",
                    "profile.visibility"),
  };
  orbiting_require(visibility_config.minimum_elevation_deg >= -90
                     && visibility_config.minimum_elevation_deg <= 90,
                   "minimum elevation must be in [-90, 90]");

  const rj::Value& display = required_member(document, "display", "profile");
  display_configuration display_config {
    required_size(display, "maximum_active_objects", "profile.display"),
    required_size(display, "maximum_debris_per_group", "profile.display"),
    required_size(display, "maximum_labels", "profile.display"),
    required_size(display, "maximum_tracks_per_group", "profile.display"),
    static_cast<int>(required_size(display, "track_minutes_each_side",
                                   "profile.display")),
    static_cast<int>(required_size(display, "track_step_minutes",
                                   "profile.display")),
    required_bool(display, "show_reference_lines", "profile.display"),
  };
  orbiting_require(display_config.maximum_active_objects > 0
                     && display_config.track_step_minutes > 0,
                   "profile display limits are invalid");

  const rj::Value& catalogs = required_member(document, "catalogs", "profile");
  const group_configuration primary = load_group_configuration(
    required_member(catalogs, "primary", "profile.catalogs"), directory,
    "profile.catalogs.primary");
  orbiting_require(primary.id == "active" && primary.role == "active",
                   "primary catalog must be the active catalog");
  const rj::Value& groups_value = required_member(
    catalogs, "groups", "profile.catalogs");
  orbiting_require(groups_value.IsArray() && !groups_value.Empty(),
                   "profile.catalogs.groups must be a nonempty array");
  std::vector<group_configuration> groups;
  std::unordered_set<std::string> group_ids;
  for (rapidjson::SizeType index = 0; index < groups_value.Size(); ++index)
    {
      const std::string context = "profile.catalogs.groups["
        + std::to_string(index) + "]";
      group_configuration group = load_group_configuration(
        groups_value[index], directory, context);
      orbiting_require(group_ids.insert(group.id).second,
                       "duplicate catalog group id " + group.id);
      groups.push_back(std::move(group));
    }
  const rj::Value& nasa = required_member(
    catalogs, "nasa_ssc_reference", "profile.catalogs");
  const rj::Value& snapshot = required_member(document, "snapshot", "profile");

  return {
    absolute_path,
    required_string(document, "name", "profile"),
    parse_timestamp(required_string(document, "timestamp", "profile")),
    std::move(reference),
    central_ra_hours * 15.0,
    propagation_config,
    visibility_config,
    display_config,
    primary,
    std::move(groups),
    directory / required_string(nasa, "file",
                                "profile.catalogs.nasa_ssc_reference"),
    required_string(nasa, "query_url",
                    "profile.catalogs.nasa_ssc_reference"),
    directory / required_string(snapshot, "checksum_file", "profile.snapshot"),
  };
}

inline std::vector<std::string>
parse_csv_row(const std::string_view line)
{
  std::vector<std::string> fields;
  std::string field;
  bool quoted = false;
  for (std::size_t index = 0; index < line.size(); ++index)
    {
      const char value = line[index];
      if (value == '"')
        {
          if (quoted && index + 1 < line.size() && line[index + 1] == '"')
            {
              field.push_back('"');
              ++index;
            }
          else
            quoted = !quoted;
        }
      else if (value == ',' && !quoted)
        {
          fields.push_back(std::move(field));
          field.clear();
        }
      else if (value != '\r')
        field.push_back(value);
    }
  orbiting_require(!quoted, "CSV row has an unterminated quoted field");
  fields.push_back(std::move(field));
  return fields;
}

inline double
parse_csv_number(const std::string& value, const std::string& field,
                 const fs::path& path, const std::size_t line)
{
  try
    {
      std::size_t consumed = 0;
      const double result = std::stod(value, &consumed);
      orbiting_require(consumed == value.size() && std::isfinite(result),
                       "invalid numeric value");
      return result;
    }
  catch (const std::exception&)
    {
      throw std::runtime_error(path.string() + ":" + std::to_string(line)
                               + " has invalid " + field + " value '"
                               + value + "'");
    }
}

struct orbital_object
{
  std::string name;
  std::string international_designator;
  instant epoch;
  double mean_motion_rev_per_day;
  double eccentricity;
  double inclination_deg;
  double right_ascension_node_deg;
  double argument_pericenter_deg;
  double mean_anomaly_deg;
  std::string classification;
  std::string norad_id;
  long element_set_number;
  long revolution_at_epoch;
  double bstar;
  double mean_motion_dot;
  double mean_motion_ddot;
  std::vector<std::string> group_ids;
  std::vector<std::string> roles;
  std::string source_url;
};

inline std::vector<orbital_object>
load_omm_catalog(const fs::path& path, const std::string& source_url)
{
  std::ifstream input {path};
  orbiting_require(input.good(), "failed to open OMM CSV " + path.string());
  std::string line;
  orbiting_require(static_cast<bool>(std::getline(input, line)),
                   "OMM CSV is empty: " + path.string());
  const std::vector<std::string> header = parse_csv_row(line);
  std::unordered_map<std::string, std::size_t> columns;
  for (std::size_t index = 0; index < header.size(); ++index)
    columns.emplace(header[index], index);
  constexpr std::array required_columns {
    "OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", "ECCENTRICITY",
    "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY",
    "CLASSIFICATION_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO",
    "REV_AT_EPOCH", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT",
  };
  for (const std::string_view name : required_columns)
    orbiting_require(columns.contains(std::string(name)),
                     "OMM CSV " + path.string() + " is missing column "
                       + std::string(name));

  std::vector<orbital_object> result;
  std::size_t line_number = 1;
  while (std::getline(input, line))
    {
      ++line_number;
      if (line.empty() || line == "\r")
        continue;
      const std::vector<std::string> fields = parse_csv_row(line);
      orbiting_require(fields.size() == header.size(),
                       path.string() + ":" + std::to_string(line_number)
                         + " has the wrong field count");
      const auto value = [&](const std::string_view name) -> const std::string& {
        return fields.at(columns.at(std::string(name)));
      };
      const auto number = [&](const std::string_view name) {
        return parse_csv_number(value(name), std::string(name), path,
                                line_number);
      };
      orbital_object object {
        value("OBJECT_NAME"),
        value("OBJECT_ID"),
        parse_timestamp(value("EPOCH"), false),
        number("MEAN_MOTION"),
        number("ECCENTRICITY"),
        number("INCLINATION"),
        number("RA_OF_ASC_NODE"),
        number("ARG_OF_PERICENTER"),
        number("MEAN_ANOMALY"),
        value("CLASSIFICATION_TYPE"),
        value("NORAD_CAT_ID"),
        static_cast<long>(number("ELEMENT_SET_NO")),
        static_cast<long>(number("REV_AT_EPOCH")),
        number("BSTAR"),
        number("MEAN_MOTION_DOT"),
        number("MEAN_MOTION_DDOT"),
        {}, {}, source_url,
      };
      orbiting_require(!object.name.empty() && !object.norad_id.empty(),
                       path.string() + ":" + std::to_string(line_number)
                         + " has an empty object name or catalog id");
      orbiting_require(object.mean_motion_rev_per_day > 0
                         && object.eccentricity >= 0
                         && object.eccentricity < 1,
                       path.string() + ":" + std::to_string(line_number)
                         + " has invalid orbital elements");
      result.push_back(std::move(object));
    }
  orbiting_require(!result.empty(), "OMM CSV has no records: " + path.string());
  return result;
}

inline void
append_unique(std::vector<std::string>& values, const std::string& value)
{
  if (std::find(values.begin(), values.end(), value) == values.end())
    values.push_back(value);
}

inline bool
catalog_id_less(const std::string& left, const std::string& right)
{
  if (left.size() != right.size())
    return left.size() < right.size();
  return left < right;
}

struct catalog_bundle
{
  std::vector<orbital_object> objects;
  std::size_t active_records = 0;
  std::size_t debris_records = 0;
};

inline catalog_bundle
load_catalogs(const profile& config)
{
  std::vector<orbital_object> active = load_omm_catalog(
    config.primary.file, config.primary.source_url);
  if (active.size() > config.display.maximum_active_objects)
    active.resize(config.display.maximum_active_objects);
  std::unordered_map<std::string, std::size_t> active_indices;
  active_indices.reserve(active.size());
  for (std::size_t index = 0; index < active.size(); ++index)
    active_indices.emplace(active[index].norad_id, index);

  std::vector<orbital_object> debris;
  for (const group_configuration& group : config.groups)
    {
      std::vector<orbital_object> members = load_omm_catalog(
        group.file, group.source_url);
      if (group.role == "debris")
        {
          std::sort(members.begin(), members.end(),
            [](const orbital_object& left, const orbital_object& right) {
              return catalog_id_less(left.norad_id, right.norad_id);
            });
          if (members.size() > config.display.maximum_debris_per_group)
            members.resize(config.display.maximum_debris_per_group);
          for (orbital_object& member : members)
            {
              if (active_indices.contains(member.norad_id))
                continue;
              append_unique(member.group_ids, group.id);
              append_unique(member.roles, group.role);
              debris.push_back(std::move(member));
            }
          continue;
        }
      for (const orbital_object& member : members)
        {
          const auto found = active_indices.find(member.norad_id);
          if (found == active_indices.end())
            continue;
          orbital_object& target = active[found->second];
          append_unique(target.group_ids, group.id);
          append_unique(target.roles, group.role);
        }
    }
  for (orbital_object& object : active)
    if (object.roles.empty())
      object.roles.push_back("other-active");

  catalog_bundle result;
  result.active_records = active.size();
  result.debris_records = debris.size();
  result.objects.reserve(active.size() + debris.size());
  std::move(active.begin(), active.end(), std::back_inserter(result.objects));
  std::move(debris.begin(), debris.end(), std::back_inserter(result.objects));
  return result;
}

struct vector_3d
{
  double x;
  double y;
  double z;
};

inline vector_3d
operator-(const vector_3d left, const vector_3d right)
{ return {left.x - right.x, left.y - right.y, left.z - right.z}; }

inline double
dot(const vector_3d left, const vector_3d right)
{ return left.x * right.x + left.y * right.y + left.z * right.z; }

inline double
length(const vector_3d value)
{ return std::sqrt(dot(value, value)); }

inline vector_3d
unit(const vector_3d value)
{
  const double magnitude = length(value);
  orbiting_require(magnitude > 0, "cannot normalize a zero vector");
  return {value.x / magnitude, value.y / magnitude, value.z / magnitude};
}

inline elsetrec
initialize_sgp4(const orbital_object& object)
{
  elsetrec satellite {};
  const double scale = 2.0 * std::numbers::pi / minutes_per_day;
  const double mean_motion = object.mean_motion_rev_per_day * scale;
  const double mean_motion_dot = object.mean_motion_dot * scale
    / minutes_per_day;
  const double mean_motion_ddot = object.mean_motion_ddot * scale
    / (minutes_per_day * minutes_per_day);
  // Upstream still stores only five catalog characters internally. The real
  // OMM catalog id remains in orbital_object; this harmless placeholder keeps
  // six- and nine-digit ids from overflowing an upstream bookkeeping field.
  constexpr char sgp4_placeholder_id[9] = "00000";
  const bool initialized = SGP4Funcs::sgp4init(
    wgs72, 'a', sgp4_placeholder_id,
    object.epoch.julian_date - 2433281.5,
    object.bstar, mean_motion_dot, mean_motion_ddot, object.eccentricity,
    degrees_to_radians(object.argument_pericenter_deg),
    degrees_to_radians(object.inclination_deg),
    degrees_to_radians(object.mean_anomaly_deg), mean_motion,
    degrees_to_radians(object.right_ascension_node_deg), satellite);
  orbiting_require(initialized && satellite.error == 0,
                   "SGP4 initialization failed for NORAD " + object.norad_id);
  return satellite;
}

struct teme_state
{
  vector_3d position_km;
  vector_3d velocity_km_s;
};

inline teme_state
propagate_teme(const orbital_object& object, const double julian_date)
{
  elsetrec satellite = initialize_sgp4(object);
  double position[3] {};
  double velocity[3] {};
  const double minutes_since_epoch = (julian_date - object.epoch.julian_date)
    * minutes_per_day;
  const bool propagated = SGP4Funcs::sgp4(
    satellite, minutes_since_epoch, position, velocity);
  orbiting_require(propagated && satellite.error == 0,
                   "SGP4 propagation failed for NORAD " + object.norad_id
                     + " with error " + std::to_string(satellite.error));
  return {{position[0], position[1], position[2]},
          {velocity[0], velocity[1], velocity[2]}};
}

inline vector_3d
teme_to_ecef(const vector_3d teme, const double julian_date)
{
  const double sidereal = SGP4Funcs::gstime_SGP4(julian_date);
  const double cosine = std::cos(sidereal);
  const double sine = std::sin(sidereal);
  return {cosine * teme.x + sine * teme.y,
          -sine * teme.x + cosine * teme.y,
          teme.z};
}

inline vector_3d
ecef_to_teme(const vector_3d ecef, const double julian_date)
{
  const double sidereal = SGP4Funcs::gstime_SGP4(julian_date);
  const double cosine = std::cos(sidereal);
  const double sine = std::sin(sidereal);
  return {cosine * ecef.x - sine * ecef.y,
          sine * ecef.x + cosine * ecef.y,
          ecef.z};
}

struct geodetic_position
{
  double latitude_deg;
  double longitude_deg_east;
  double altitude_km;
};

inline geodetic_position
ecef_to_geodetic(const vector_3d ecef)
{
  const double longitude = std::atan2(ecef.y, ecef.x);
  const double horizontal = std::hypot(ecef.x, ecef.y);
  double latitude = std::atan2(
    ecef.z, horizontal * (1.0 - earth_eccentricity_squared));
  double altitude = 0;
  for (int iteration = 0; iteration < 8; ++iteration)
    {
      const double sine = std::sin(latitude);
      const double radius = earth_equatorial_radius_km
        / std::sqrt(1.0 - earth_eccentricity_squared * sine * sine);
      if (horizontal < 1e-9)
        altitude = std::abs(ecef.z)
          - radius * (1.0 - earth_eccentricity_squared);
      else
        altitude = horizontal / std::cos(latitude) - radius;
      latitude = std::atan2(
        ecef.z,
        horizontal * (1.0 - earth_eccentricity_squared * radius
                                  / (radius + altitude)));
    }
  return {radians_to_degrees(latitude),
          normalize_signed_degrees(radians_to_degrees(longitude)), altitude};
}

inline vector_3d
observer_ecef(const reference_point& observer)
{
  const double latitude = degrees_to_radians(observer.latitude_deg);
  const double longitude = degrees_to_radians(observer.longitude_deg_east);
  const double sine = std::sin(latitude);
  const double prime_vertical = earth_equatorial_radius_km
    / std::sqrt(1.0 - earth_eccentricity_squared * sine * sine);
  const double elevation_km = observer.elevation_m / 1000.0;
  return {(prime_vertical + elevation_km) * std::cos(latitude)
            * std::cos(longitude),
          (prime_vertical + elevation_km) * std::cos(latitude)
            * std::sin(longitude),
          (prime_vertical * (1.0 - earth_eccentricity_squared)
             + elevation_km) * sine};
}

struct horizontal_position
{
  double azimuth_deg;
  double elevation_deg;
  double range_km;
};

inline horizontal_position
topocentric_horizontal(const vector_3d satellite_ecef,
                       const reference_point& observer)
{
  const vector_3d delta = satellite_ecef - observer_ecef(observer);
  const double latitude = degrees_to_radians(observer.latitude_deg);
  const double longitude = degrees_to_radians(observer.longitude_deg_east);
  const double east = -std::sin(longitude) * delta.x
    + std::cos(longitude) * delta.y;
  const double north = -std::sin(latitude) * std::cos(longitude) * delta.x
    - std::sin(latitude) * std::sin(longitude) * delta.y
    + std::cos(latitude) * delta.z;
  const double up = std::cos(latitude) * std::cos(longitude) * delta.x
    + std::cos(latitude) * std::sin(longitude) * delta.y
    + std::sin(latitude) * delta.z;
  const double range = std::sqrt(east * east + north * north + up * up);
  return {normalize_degrees(radians_to_degrees(std::atan2(east, north))),
          radians_to_degrees(std::asin(std::clamp(up / range, -1.0, 1.0))),
          range};
}

struct equatorial_position
{
  double right_ascension_deg;
  double declination_deg;
};

inline equatorial_position
topocentric_equatorial(const vector_3d satellite_teme,
                       const reference_point& observer,
                       const double julian_date)
{
  const vector_3d topocentric = satellite_teme
    - ecef_to_teme(observer_ecef(observer), julian_date);
  const double distance = length(topocentric);
  return {normalize_degrees(radians_to_degrees(
            std::atan2(topocentric.y, topocentric.x))),
          radians_to_degrees(std::asin(std::clamp(
            topocentric.z / distance, -1.0, 1.0)))};
}

inline vector_3d
solar_unit_vector(const double julian_date)
{
  const double days = julian_date - 2451545.0;
  const double mean_longitude = degrees_to_radians(normalize_degrees(
    280.460 + 0.9856474 * days));
  const double mean_anomaly = degrees_to_radians(normalize_degrees(
    357.528 + 0.9856003 * days));
  const double ecliptic_longitude = mean_longitude
    + degrees_to_radians(1.915) * std::sin(mean_anomaly)
    + degrees_to_radians(0.020) * std::sin(2.0 * mean_anomaly);
  const double obliquity = degrees_to_radians(23.439 - 0.0000004 * days);
  return unit({std::cos(ecliptic_longitude),
               std::cos(obliquity) * std::sin(ecliptic_longitude),
               std::sin(obliquity) * std::sin(ecliptic_longitude)});
}

inline bool
is_sunlit(const vector_3d satellite_teme, const double julian_date)
{
  const vector_3d sun = solar_unit_vector(julian_date);
  const double along_sun = dot(satellite_teme, sun);
  if (along_sun >= 0)
    return true;
  const vector_3d perpendicular {
    satellite_teme.x - along_sun * sun.x,
    satellite_teme.y - along_sun * sun.y,
    satellite_teme.z - along_sun * sun.z,
  };
  return length(perpendicular) >= earth_equatorial_radius_km;
}

inline double
solar_altitude_deg(const profile& config, const double julian_date)
{
  const vector_3d sun = solar_unit_vector(julian_date);
  const double right_ascension = std::atan2(sun.y, sun.x);
  const double declination = std::asin(sun.z);
  const double local_sidereal = SGP4Funcs::gstime_SGP4(julian_date)
    + degrees_to_radians(config.observer.longitude_deg_east);
  const double hour_angle = local_sidereal - right_ascension;
  const double latitude = degrees_to_radians(config.observer.latitude_deg);
  return radians_to_degrees(std::asin(
    std::sin(latitude) * std::sin(declination)
      + std::cos(latitude) * std::cos(declination) * std::cos(hour_angle)));
}

inline bool
epoch_is_admissible(const orbital_object& object, const profile& config)
{
  const double age_days = config.calculation_time.julian_date
    - object.epoch.julian_date;
  return age_days <= config.propagation.maximum_element_age_days
    && age_days * -24.0 <= config.propagation.maximum_future_epoch_hours;
}

inline std::string
display_role(const orbital_object& object)
{
  constexpr std::array priorities {
    "debris", "megaconstellation", "navigation", "communications",
    "earth-observation", "human-presence", "science", "other-active",
  };
  for (const std::string_view role : priorities)
    if (std::find(object.roles.begin(), object.roles.end(), role)
          != object.roles.end())
      return std::string(role);
  return "other-active";
}

struct propagated_object
{
  orbital_object source;
  teme_state teme;
  geodetic_position subpoint;
  horizontal_position horizontal;
  equatorial_position equatorial;
  std::string role;
  double element_age_days;
  bool sunlit;
  bool optical_candidate;
};

struct propagated_catalog
{
  std::vector<propagated_object> objects;
  std::size_t skipped_stale = 0;
  std::size_t failed_propagation = 0;
};

inline propagated_object
propagate_object(const orbital_object& object, const profile& config,
                 const double julian_date, const double sun_altitude)
{
  const teme_state state = propagate_teme(object, julian_date);
  const vector_3d ecef = teme_to_ecef(state.position_km, julian_date);
  const horizontal_position horizontal = topocentric_horizontal(
    ecef, config.observer);
  const bool sunlight = is_sunlit(state.position_km, julian_date);
  const bool optical = horizontal.elevation_deg
      >= config.visibility.minimum_elevation_deg
    && sun_altitude <= config.visibility.maximum_solar_altitude_deg
    && (!config.visibility.require_sunlit || sunlight);
  return {object, state, ecef_to_geodetic(ecef), horizontal,
          topocentric_equatorial(state.position_km, config.observer,
                                 julian_date),
          display_role(object),
          config.calculation_time.julian_date - object.epoch.julian_date,
          sunlight, optical};
}

inline propagated_catalog
propagate_catalog(const catalog_bundle& input, const profile& config)
{
  propagated_catalog result;
  result.objects.reserve(input.objects.size());
  const double sun_altitude = solar_altitude_deg(
    config, config.calculation_time.julian_date);
  for (const orbital_object& object : input.objects)
    {
      if (!epoch_is_admissible(object, config))
        {
          ++result.skipped_stale;
          continue;
        }
      try
        {
          result.objects.push_back(propagate_object(
            object, config, config.calculation_time.julian_date,
            sun_altitude));
        }
      catch (const std::exception&)
        {
          ++result.failed_propagation;
        }
    }
  orbiting_require(!result.objects.empty(),
                   "no orbital objects survived profile propagation");
  return result;
}

} // namespace cart0freak0::orbiting_generation

#endif
