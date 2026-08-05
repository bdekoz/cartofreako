// Astronomy profile, catalog loading, and visualization-grade astrometry.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ASTRO_DATA_H
#define CART0FREAK0_ASTRO_DATA_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
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

#include "generation-instant.h"
#include "solar-geometry.h"

namespace cart0freak0::astro_generation {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline constexpr double degrees_per_hour = 15.0;
inline constexpr double julian_gaia_dr3_epoch = 2457388.5;
inline constexpr double days_per_julian_year = 365.25;

using generation_time::instant;
using generation_time::julian_j2000;
using generation_time::make_instant;
using generation_time::parse_timestamp;
using generation_time::seconds_per_day;
using solar_geometry::degrees_to_radians;
using solar_geometry::greenwich_mean_sidereal_time;
using solar_geometry::normalize_degrees;
using solar_geometry::normalize_signed_degrees;
using solar_geometry::radians_to_degrees;

inline void
astro_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline rj::Document
read_json(const fs::path& path)
{
  std::ifstream input {path};
  astro_require(input.good(), "failed to open JSON file " + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  rj::Document document;
  document.Parse(json.c_str());
  astro_require(
    !document.HasParseError(),
    "failed to parse " + path.string() + ": "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  astro_require(document.IsObject(),
                "JSON root must be an object in " + path.string());
  return document;
}

inline const rj::Value*
required_member(const rj::Value& object, const char* name,
                std::string context)
{
  astro_require(object.IsObject() && object.HasMember(name),
                context + " is missing '" + name + "'");
  return &object[name];
}

inline std::string
required_string(const rj::Value& object, const char* name,
                std::string context)
{
  const rj::Value& value = *required_member(object, name, context);
  astro_require(value.IsString(), context + "." + name
                                    + " must be a string");
  return value.GetString();
}

inline double
required_number(const rj::Value& object, const char* name,
                std::string context)
{
  const rj::Value& value = *required_member(object, name, context);
  astro_require(value.IsNumber(), context + "." + name
                                    + " must be a number");
  return value.GetDouble();
}

inline std::size_t
required_size(const rj::Value& object, const char* name,
              std::string context)
{
  const rj::Value& value = *required_member(object, name, context);
  astro_require(value.IsUint64(), context + "." + name
                                    + " must be a nonnegative integer");
  return static_cast<std::size_t>(value.GetUint64());
}

inline bool
required_bool(const rj::Value& object, const char* name,
              std::string context)
{
  const rj::Value& value = *required_member(object, name, context);
  astro_require(value.IsBool(), context + "." + name
                                  + " must be a boolean");
  return value.GetBool();
}

inline std::vector<std::string>
required_strings(const rj::Value& object, const char* name,
                 std::string context)
{
  const rj::Value& value = *required_member(object, name, context);
  astro_require(value.IsArray(), context + "." + name
                                   + " must be an array");
  std::vector<std::string> result;
  result.reserve(value.Size());
  for (const rj::Value& element : value.GetArray())
    {
      astro_require(element.IsString(), context + "." + name
                                          + " must contain strings");
      result.emplace_back(element.GetString());
    }
  return result;
}

struct reference_point
{
  std::string name;
  double latitude_deg;
  double longitude_deg_east;
  double elevation_m;
};

struct orientation
{
  bool celestial_handedness;
  double central_right_ascension_deg;
};

struct instrumentation
{
  std::string mode;
  std::vector<std::string> bands;
  std::vector<std::string> night_required_bands;
  double optical_limiting_magnitude;
  double minimum_altitude_deg;
  double twilight_sun_altitude_deg;
};

struct display_configuration
{
  std::size_t maximum_stars;
  std::size_t maximum_exoplanet_hosts;
  std::size_t maximum_labels;
  bool show_reference_lines;
  bool show_below_horizon_reference;
};

struct profile
{
  fs::path path;
  std::string name;
  instant calculation_time;
  reference_point observer;
  orientation sky_orientation;
  instrumentation instrument;
  double event_lookback_days;
  display_configuration display;
  fs::path gaia_catalog;
  fs::path exoplanet_catalog;
  fs::path curated_catalog;
  std::vector<fs::path> small_body_catalogs;
};

inline profile
load_profile(const fs::path& path)
{
  const rj::Document document = read_json(path);
  astro_require(required_size(document, "schema_version", "profile") == 1,
                "unsupported astronomy profile schema");
  const rj::Value& products = *required_member(document, "products", "profile");
  astro_require(products.IsArray(), "profile.products must be an array");
  bool all_sky = false;
  bool observer = false;
  for (const rj::Value& value : products.GetArray())
    {
      astro_require(value.IsString(),
                    "profile.products must contain strings");
      all_sky = all_sky || std::string_view(value.GetString()) == "all-sky";
      observer = observer || std::string_view(value.GetString()) == "observer";
    }
  astro_require(all_sky && observer,
                "profile.products must enable all-sky and observer");

  const rj::Value& point = *required_member(
    document, "reference_point", "profile");
  reference_point reference {
    required_string(point, "name", "profile.reference_point"),
    required_number(point, "latitude_deg", "profile.reference_point"),
    required_number(point, "longitude_deg_east", "profile.reference_point"),
    required_number(point, "elevation_m", "profile.reference_point"),
  };
  astro_require(reference.latitude_deg >= -90
                  && reference.latitude_deg <= 90,
                "reference latitude must be in [-90, 90]");
  astro_require(reference.longitude_deg_east >= -180
                  && reference.longitude_deg_east <= 180,
                "reference longitude must be in [-180, 180]");

  const rj::Value& orientation_value = *required_member(
    document, "orientation", "profile");
  const std::string handedness = required_string(
    orientation_value, "handedness", "profile.orientation");
  astro_require(handedness == "celestial" || handedness == "terrestrial",
                "orientation handedness must be celestial or terrestrial");
  const double central_ra_hours = required_number(
    orientation_value, "central_right_ascension_hours",
    "profile.orientation");
  astro_require(central_ra_hours >= 0 && central_ra_hours < 24,
                "central right ascension must be in [0, 24) hours");

  const rj::Value& instrument_value = *required_member(
    document, "instrumentation", "profile");
  instrumentation instrument {
    required_string(instrument_value, "mode", "profile.instrumentation"),
    required_strings(instrument_value, "bands", "profile.instrumentation"),
    required_strings(instrument_value, "night_required_bands",
                     "profile.instrumentation"),
    required_number(instrument_value, "optical_limiting_magnitude",
                    "profile.instrumentation"),
    required_number(instrument_value, "minimum_altitude_deg",
                    "profile.instrumentation"),
    required_number(instrument_value,
                    "astronomical_twilight_sun_altitude_deg",
                    "profile.instrumentation"),
  };
  astro_require(instrument.mode == "multi-band",
                "the astronomy MVP requires multi-band instrumentation");
  astro_require(!instrument.bands.empty(),
                "instrumentation must enable at least one band");
  astro_require(instrument.minimum_altitude_deg >= -90
                  && instrument.minimum_altitude_deg <= 90,
                "minimum altitude must be in [-90, 90]");

  const rj::Value& dynamic = *required_member(
    document, "dynamic_events", "profile");
  const double lookback_days = required_number(
    dynamic, "lookback_days", "profile.dynamic_events");
  astro_require(lookback_days >= 0,
                "dynamic event lookback must be nonnegative");

  const rj::Value& display = *required_member(document, "display", "profile");
  display_configuration display_config {
    required_size(display, "maximum_stars", "profile.display"),
    required_size(display, "maximum_exoplanet_hosts", "profile.display"),
    required_size(display, "maximum_labels", "profile.display"),
    required_bool(display, "show_reference_lines", "profile.display"),
    required_bool(display, "show_below_horizon_reference", "profile.display"),
  };

  const rj::Value& catalogs = *required_member(document, "catalogs", "profile");
  const fs::path base = path.parent_path();
  std::vector<fs::path> small_body_paths;
  for (const std::string& filename : required_strings(
         catalogs, "small_bodies", "profile.catalogs"))
    small_body_paths.push_back(base / filename);

  return {
    path,
    required_string(document, "name", "profile"),
    parse_timestamp(required_string(document, "timestamp", "profile")),
    std::move(reference),
    {handedness == "celestial", central_ra_hours * degrees_per_hour},
    std::move(instrument),
    lookback_days,
    display_config,
    base / required_string(catalogs, "gaia_dr3", "profile.catalogs"),
    base / required_string(
      catalogs, "nasa_exoplanets", "profile.catalogs"),
    base / required_string(catalogs, "curated_sky", "profile.catalogs"),
    std::move(small_body_paths),
  };
}

struct sky_object
{
  std::string id;
  std::string name;
  std::string kind;
  std::vector<std::string> bands;
  double ra_deg;
  double dec_deg;
  std::optional<double> magnitude;
  std::optional<double> color_index;
  std::optional<double> uncertainty_deg;
  std::optional<instant> observed_at;
  std::string source_url;
  std::string detail;
  double altitude_deg = std::numeric_limits<double>::quiet_NaN();
};

inline std::vector<std::string>
parse_csv_line(const std::string_view line)
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
  astro_require(!quoted, "unterminated quoted CSV field");
  fields.push_back(std::move(field));
  return fields;
}

struct csv_table
{
  std::unordered_map<std::string, std::size_t> columns;
  std::vector<std::vector<std::string>> rows;
};

inline csv_table
read_csv(const fs::path& path)
{
  std::ifstream input {path};
  astro_require(input.good(), "failed to open CSV file " + path.string());
  std::string line;
  astro_require(static_cast<bool>(std::getline(input, line)),
                "CSV file is empty: " + path.string());
  csv_table result;
  const std::vector<std::string> header = parse_csv_line(line);
  for (std::size_t index = 0; index < header.size(); ++index)
    result.columns.emplace(header[index], index);
  while (std::getline(input, line))
    {
      if (line.empty())
        continue;
      std::vector<std::string> row = parse_csv_line(line);
      astro_require(row.size() == header.size(),
                    "CSV row has the wrong field count in " + path.string());
      result.rows.push_back(std::move(row));
    }
  return result;
}

inline const std::string&
csv_field(const csv_table& table, const std::vector<std::string>& row,
          std::string name)
{
  const auto found = table.columns.find(name);
  astro_require(found != table.columns.end(),
                "CSV catalog is missing column " + name);
  return row[found->second];
}

inline std::optional<double>
optional_number(const std::string& value)
{
  if (value.empty())
    return std::nullopt;
  std::size_t parsed = 0;
  const double result = std::stod(value, &parsed);
  astro_require(parsed == value.size() && std::isfinite(result),
                "catalog contains an invalid number: " + value);
  return result;
}

inline double
required_csv_number(const csv_table& table,
                    const std::vector<std::string>& row,
                    const std::string& name)
{
  const std::optional<double> result = optional_number(
    csv_field(table, row, name));
  astro_require(result.has_value(), "CSV field " + name + " is empty");
  return *result;
}

inline std::vector<sky_object>
load_gaia_stars(const profile& config)
{
  const csv_table table = read_csv(config.gaia_catalog);
  std::vector<sky_object> result;
  result.reserve(std::min(config.display.maximum_stars, table.rows.size()));
  const double years = (config.calculation_time.julian_date
                        - julian_gaia_dr3_epoch) / days_per_julian_year;
  for (const std::vector<std::string>& row : table.rows)
    {
      if (result.size() >= config.display.maximum_stars)
        break;
      double ra = required_csv_number(table, row, "ra");
      double dec = required_csv_number(table, row, "dec");
      const std::optional<double> pmra = optional_number(
        csv_field(table, row, "pmra"));
      const std::optional<double> pmdec = optional_number(
        csv_field(table, row, "pmdec"));
      if (pmra.has_value() && std::abs(std::cos(degrees_to_radians(dec))) > 1e-8)
        ra += *pmra * years
              / (3.6e6 * std::cos(degrees_to_radians(dec)));
      if (pmdec.has_value())
        dec += *pmdec * years / 3.6e6;
      const std::string source_id = csv_field(table, row, "source_id");
      result.push_back({
        "gaia-" + source_id,
        "Gaia DR3 " + source_id,
        "star",
        {"infrared", "optical"},
        normalize_degrees(ra),
        std::clamp(dec, -90.0, 90.0),
        optional_number(csv_field(table, row, "phot_g_mean_mag")),
        optional_number(csv_field(table, row, "bp_rp")),
        std::nullopt,
        std::nullopt,
        "https://gea.esac.esa.int/archive/",
        "Gaia DR3 astrometry at J2016.0 propagated by catalog proper motion",
      });
    }
  return result;
}

inline std::vector<sky_object>
load_exoplanet_hosts(const profile& config)
{
  const csv_table table = read_csv(config.exoplanet_catalog);
  std::vector<sky_object> result;
  std::unordered_set<std::string> hosts;
  for (const std::vector<std::string>& row : table.rows)
    {
      if (result.size() >= config.display.maximum_exoplanet_hosts)
        break;
      const std::string hostname = csv_field(table, row, "hostname");
      if (!hosts.insert(hostname).second)
        continue;
      const std::string planet = csv_field(table, row, "pl_name");
      const std::string method = csv_field(table, row, "discoverymethod");
      const std::string distance = csv_field(table, row, "sy_dist");
      result.push_back({
        "exoplanet-host-" + std::to_string(result.size() + 1),
        hostname + " system",
        "exoplanet-host",
        {"infrared", "optical"},
        required_csv_number(table, row, "ra"),
        required_csv_number(table, row, "dec"),
        optional_number(csv_field(table, row, "sy_vmag")),
        std::nullopt,
        std::nullopt,
        std::nullopt,
        "https://exoplanetarchive.ipac.caltech.edu/",
        planet + "; " + method + "; distance " + distance + " pc",
      });
    }
  return result;
}

inline sky_object
parse_curated_object(const rj::Value& value, const bool event)
{
  const std::string context = event ? "curated event" : "curated object";
  sky_object result {
    required_string(value, "id", context),
    required_string(value, "name", context),
    required_string(value, "kind", context),
    required_strings(value, "bands", context),
    required_number(value, "ra_deg", context),
    required_number(value, "dec_deg", context),
    std::nullopt,
    std::nullopt,
    std::nullopt,
    std::nullopt,
    required_string(value, "source_url", context),
    {},
  };
  if (value.HasMember("magnitude"))
    {
      astro_require(value["magnitude"].IsNumber(),
                    context + ".magnitude must be a number");
      result.magnitude = value["magnitude"].GetDouble();
    }
  if (event)
    {
      result.observed_at = parse_timestamp(
        required_string(value, "observed_at", context));
      result.uncertainty_deg = required_number(
        value, "uncertainty_deg", context);
    }
  astro_require(result.ra_deg >= 0 && result.ra_deg < 360
                  && result.dec_deg >= -90 && result.dec_deg <= 90,
                context + " has coordinates outside the celestial sphere");
  return result;
}

struct curated_catalog
{
  std::vector<sky_object> objects;
  std::vector<sky_object> events;
};

inline curated_catalog
load_curated_catalog(const profile& config)
{
  const rj::Document document = read_json(config.curated_catalog);
  astro_require(required_size(document, "schema_version", "curated catalog")
                  == 1,
                "unsupported curated sky schema");
  curated_catalog result;
  const rj::Value& objects = *required_member(
    document, "objects", "curated catalog");
  const rj::Value& events = *required_member(
    document, "events", "curated catalog");
  astro_require(objects.IsArray() && events.IsArray(),
                "curated objects and events must be arrays");
  for (const rj::Value& value : objects.GetArray())
    result.objects.push_back(parse_curated_object(value, false));
  const auto lookback = std::chrono::duration<double>(
    config.event_lookback_days * seconds_per_day);
  for (const rj::Value& value : events.GetArray())
    {
      sky_object event = parse_curated_object(value, true);
      const auto age = config.calculation_time.value
                       - event.observed_at->value;
      if (age >= std::chrono::seconds::zero() && age <= lookback)
        result.events.push_back(std::move(event));
    }
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

inline vector_3d
operator-(const vector_3d value)
{ return {-value.x, -value.y, -value.z}; }

inline double
length(const vector_3d value)
{ return std::hypot(std::hypot(value.x, value.y), value.z); }

struct right_ascension_declination
{
  double ra_deg;
  double dec_deg;
};

inline right_ascension_declination
ecliptic_vector_to_equatorial(const vector_3d ecliptic)
{
  constexpr double obliquity_deg = 23.43928;
  const double obliquity = degrees_to_radians(obliquity_deg);
  const vector_3d equatorial {
    ecliptic.x,
    std::cos(obliquity) * ecliptic.y - std::sin(obliquity) * ecliptic.z,
    std::sin(obliquity) * ecliptic.y + std::cos(obliquity) * ecliptic.z,
  };
  const double distance = length(equatorial);
  astro_require(distance > 0 && std::isfinite(distance),
                "ephemeris produced a zero or non-finite vector");
  return {
    normalize_degrees(radians_to_degrees(
      std::atan2(equatorial.y, equatorial.x))),
    radians_to_degrees(std::asin(
      std::clamp(equatorial.z / distance, -1.0, 1.0))),
  };
}

struct planet_model
{
  std::string_view id;
  std::string_view name;
  std::array<double, 6> base;
  std::array<double, 6> rate;
  double nominal_magnitude;
};

inline constexpr planet_model earth_model {
  "earth", "Earth/Moon barycenter",
  {1.00000261, 0.01671123, -0.00001531, 100.46457166,
   102.93768193, 0.0},
  {0.00000562, -0.00004392, -0.01294668, 35999.37244981,
   0.32327364, 0.0},
  -3.99,
};

inline constexpr std::array planet_models {
  planet_model {
    "mercury", "Mercury",
    {0.38709927, 0.20563593, 7.00497902, 252.25032350,
     77.45779628, 48.33076593},
    {0.00000037, 0.00001906, -0.00594749, 149472.67411175,
     0.16047689, -0.12534081},
    -0.4,
  },
  planet_model {
    "venus", "Venus",
    {0.72333566, 0.00677672, 3.39467605, 181.97909950,
     131.60246718, 76.67984255},
    {0.00000390, -0.00004107, -0.00078890, 58517.81538729,
     0.00268329, -0.27769418},
    -4.1,
  },
  planet_model {
    "mars", "Mars",
    {1.52371034, 0.09339410, 1.84969142, -4.55343205,
     -23.94362959, 49.55953891},
    {0.00001847, 0.00007882, -0.00813131, 19140.30268499,
     0.44441088, -0.29257343},
    -1.5,
  },
  planet_model {
    "jupiter", "Jupiter",
    {5.20288700, 0.04838624, 1.30439695, 34.39644051,
     14.72847983, 100.47390909},
    {-0.00011607, -0.00013253, -0.00183714, 3034.74612775,
     0.21252668, 0.20469106},
    -2.2,
  },
  planet_model {
    "saturn", "Saturn",
    {9.53667594, 0.05386179, 2.48599187, 49.95424423,
     92.59887831, 113.66242448},
    {-0.00125060, -0.00050991, 0.00193609, 1222.49362201,
     -0.41897216, -0.28867794},
    0.5,
  },
  planet_model {
    "uranus", "Uranus",
    {19.18916464, 0.04725744, 0.77263783, 313.23810451,
     170.95427630, 74.01692503},
    {-0.00196176, -0.00004397, -0.00242939, 428.48202785,
     0.40805281, 0.04240589},
    5.7,
  },
  planet_model {
    "neptune", "Neptune",
    {30.06992276, 0.00859048, 1.77004347, -55.12002969,
     44.96476227, 131.78422574},
    {0.00026291, 0.00005105, 0.00035372, 218.45945325,
     -0.32241464, -0.00508664},
    7.8,
  },
};

inline double
solve_eccentric_anomaly(const double mean_anomaly, const double eccentricity)
{
  double eccentric_anomaly = mean_anomaly
    + eccentricity * std::sin(mean_anomaly);
  for (int iteration = 0; iteration < 32; ++iteration)
    {
      const double correction
        = (mean_anomaly - (eccentric_anomaly
                           - eccentricity * std::sin(eccentric_anomaly)))
          / (1 - eccentricity * std::cos(eccentric_anomaly));
      eccentric_anomaly += correction;
      if (std::abs(correction) < 1e-13)
        break;
    }
  return eccentric_anomaly;
}

inline vector_3d
orbital_vector(const double semi_major_axis, const double eccentricity,
               const double inclination_deg, const double mean_anomaly_deg,
               const double longitude_perihelion_deg,
               const double longitude_node_deg)
{
  astro_require(semi_major_axis > 0 && eccentricity >= 0 && eccentricity < 1,
                "only bounded elliptic ephemerides are supported");
  const double mean_anomaly = degrees_to_radians(
    normalize_signed_degrees(mean_anomaly_deg));
  const double eccentric_anomaly = solve_eccentric_anomaly(
    mean_anomaly, eccentricity);
  const double x_orbit = semi_major_axis
    * (std::cos(eccentric_anomaly) - eccentricity);
  const double y_orbit = semi_major_axis * std::sqrt(1 - eccentricity * eccentricity)
    * std::sin(eccentric_anomaly);
  const double inclination = degrees_to_radians(inclination_deg);
  const double node = degrees_to_radians(longitude_node_deg);
  const double argument_perihelion = degrees_to_radians(
    longitude_perihelion_deg - longitude_node_deg);
  const double cos_w = std::cos(argument_perihelion);
  const double sin_w = std::sin(argument_perihelion);
  const double cos_node = std::cos(node);
  const double sin_node = std::sin(node);
  const double cos_i = std::cos(inclination);
  const double sin_i = std::sin(inclination);
  return {
    (cos_w * cos_node - sin_w * sin_node * cos_i) * x_orbit
      + (-sin_w * cos_node - cos_w * sin_node * cos_i) * y_orbit,
    (cos_w * sin_node + sin_w * cos_node * cos_i) * x_orbit
      + (-sin_w * sin_node + cos_w * cos_node * cos_i) * y_orbit,
    sin_w * sin_i * x_orbit + cos_w * sin_i * y_orbit,
  };
}

inline vector_3d
planet_heliocentric_vector(const planet_model& model,
                           const double julian_date)
{
  const double centuries = (julian_date - julian_j2000) / 36525.0;
  astro_require(centuries >= -2.0 && centuries <= 0.51,
                "JPL approximate planet elements are valid only from 1800 "
                "through 2050");
  std::array<double, 6> element {};
  for (std::size_t index = 0; index < element.size(); ++index)
    element[index] = model.base[index] + model.rate[index] * centuries;
  return orbital_vector(element[0], element[1], element[2],
                        element[3] - element[4], element[4], element[5]);
}

inline sky_object
object_from_vector(const std::string& id, const std::string& name,
                   const std::string& kind,
                   std::vector<std::string> bands,
                   const vector_3d geocentric,
                   const std::optional<double> magnitude,
                   const std::string& source_url,
                   const std::string& detail)
{
  const right_ascension_declination position
    = ecliptic_vector_to_equatorial(geocentric);
  return {id, name, kind, std::move(bands), position.ra_deg, position.dec_deg,
          magnitude, std::nullopt, std::nullopt, std::nullopt,
          source_url, detail};
}

inline sky_object
approximate_moon(const double julian_date)
{
  const double days = julian_date - 2451543.5;
  const double node = normalize_degrees(125.1228 - 0.0529538083 * days);
  constexpr double inclination = 5.1454;
  const double argument_perihelion
    = normalize_degrees(318.0634 + 0.1643573223 * days);
  constexpr double semi_major_axis = 60.2666;
  constexpr double eccentricity = 0.054900;
  const double mean_anomaly
    = normalize_degrees(115.3654 + 13.0649929509 * days);
  const vector_3d moon = orbital_vector(
    semi_major_axis, eccentricity, inclination, mean_anomaly,
    argument_perihelion + node, node);
  return object_from_vector(
    "moon", "Moon", "moon", {"infrared", "optical", "radio"},
    moon, -12.7, "https://ssd.jpl.nasa.gov/horizons/",
    "Low-precision geocentric lunar orbit for visualization");
}

inline std::optional<double>
sbdb_element(const rj::Document& document, const std::string_view name)
{
  const rj::Value& orbit = *required_member(document, "orbit", "SBDB record");
  const rj::Value& elements = *required_member(orbit, "elements", "SBDB orbit");
  astro_require(elements.IsArray(), "SBDB orbit.elements must be an array");
  for (const rj::Value& element : elements.GetArray())
    if (required_string(element, "name", "SBDB element") == name)
      {
        const std::string value = required_string(
          element, "value", "SBDB element");
        return optional_number(value);
      }
  return std::nullopt;
}

inline double
required_sbdb_element(const rj::Document& document,
                      const std::string_view name)
{
  const std::optional<double> value = sbdb_element(document, name);
  astro_require(value.has_value(),
                "SBDB orbit is missing numeric element "
                  + std::string(name));
  return *value;
}

inline std::optional<double>
sbdb_physical_parameter(const rj::Document& document,
                        const std::string_view name)
{
  if (!document.HasMember("phys_par") || !document["phys_par"].IsArray())
    return std::nullopt;
  for (const rj::Value& parameter : document["phys_par"].GetArray())
    if (required_string(parameter, "name", "SBDB physical parameter") == name)
      return optional_number(required_string(
        parameter, "value", "SBDB physical parameter"));
  return std::nullopt;
}

inline sky_object
load_small_body(const fs::path& path, const double julian_date,
                const vector_3d earth)
{
  const rj::Document document = read_json(path);
  const rj::Value& object = *required_member(document, "object", "SBDB record");
  const rj::Value& orbit = *required_member(document, "orbit", "SBDB record");
  const std::string name = required_string(object, "fullname", "SBDB object");
  const std::string code = required_string(object, "kind", "SBDB object");
  const std::string kind = code == "cn" ? "comet" : "asteroid";
  const std::optional<double> epoch_value = optional_number(
    required_string(orbit, "epoch", "SBDB orbit"));
  astro_require(epoch_value.has_value(), "SBDB orbit has an invalid epoch");
  const double epoch = *epoch_value;
  const double eccentricity = required_sbdb_element(document, "e");
  const double semi_major_axis = required_sbdb_element(document, "a");
  const double inclination = required_sbdb_element(document, "i");
  const double node = required_sbdb_element(document, "om");
  const double argument_perihelion = required_sbdb_element(document, "w");
  const double mean_anomaly_epoch = required_sbdb_element(document, "ma");
  const double mean_motion = required_sbdb_element(document, "n");
  const double mean_anomaly = mean_anomaly_epoch
    + mean_motion * (julian_date - epoch);
  const vector_3d heliocentric = orbital_vector(
    semi_major_axis, eccentricity, inclination, mean_anomaly,
    argument_perihelion + node, node);
  const vector_3d geocentric = heliocentric - earth;
  std::optional<double> magnitude;
  if (const std::optional<double> absolute = sbdb_physical_parameter(
        document, "H"))
    magnitude = *absolute
      + 5 * std::log10(length(heliocentric) * length(geocentric));
  std::vector<std::string> bands = kind == "comet"
    ? std::vector<std::string> {"infrared", "optical", "radio", "ultraviolet"}
    : std::vector<std::string> {"infrared", "optical", "radio"};
  return object_from_vector(
    "sbdb-" + path.stem().string().substr(5), name, kind,
    std::move(bands), geocentric, magnitude,
    "https://ssd-api.jpl.nasa.gov/doc/sbdb.html",
    "Two-body propagation of JPL SBDB osculating elements at JD "
      + std::to_string(epoch));
}

inline std::vector<sky_object>
make_solar_system(const profile& config)
{
  const double julian_date = config.calculation_time.julian_date;
  const vector_3d earth = planet_heliocentric_vector(
    earth_model, julian_date);
  std::vector<sky_object> result;
  const solar_geometry::equatorial_position sun
    = solar_geometry::sun_equatorial_position(julian_date);
  result.push_back({
    "sun", "Sun", "sun",
    {"radio", "infrared", "optical", "ultraviolet", "x-ray", "gamma-ray"},
    sun.right_ascension_deg, sun.declination_deg, -26.74,
    std::nullopt, std::nullopt, std::nullopt,
    "https://ssd.jpl.nasa.gov/planets/approx_pos.html",
    "Shared low-precision geocentric solar position",
  });
  result.push_back(approximate_moon(julian_date));
  for (const planet_model& model : planet_models)
    {
      const vector_3d geocentric = planet_heliocentric_vector(
        model, julian_date) - earth;
      result.push_back(object_from_vector(
        std::string(model.id), std::string(model.name), "planet",
        {"infrared", "optical", "radio"}, geocentric,
        model.nominal_magnitude,
        "https://ssd.jpl.nasa.gov/planets/approx_pos.html",
        "JPL approximate Keplerian planet position; nominal display magnitude"));
    }
  for (const fs::path& path : config.small_body_catalogs)
    result.push_back(load_small_body(path, julian_date, earth));
  return result;
}

struct catalogs
{
  std::vector<sky_object> stars;
  std::vector<sky_object> exoplanet_hosts;
  std::vector<sky_object> deep_sky;
  std::vector<sky_object> transients;
  std::vector<sky_object> solar_system;
};

inline catalogs
load_catalogs(const profile& config)
{
  curated_catalog curated = load_curated_catalog(config);
  return {
    load_gaia_stars(config),
    load_exoplanet_hosts(config),
    std::move(curated.objects),
    std::move(curated.events),
    make_solar_system(config),
  };
}

inline double
local_sidereal_time(const profile& config)
{
  return normalize_degrees(greenwich_mean_sidereal_time(
    config.calculation_time.julian_date)
    + config.observer.longitude_deg_east);
}

inline double
altitude_degrees(const double ra_deg, const double dec_deg,
                 const double observer_latitude_deg,
                 const double local_sidereal_deg)
{
  const double latitude = degrees_to_radians(observer_latitude_deg);
  const double declination = degrees_to_radians(dec_deg);
  const double hour_angle = degrees_to_radians(normalize_signed_degrees(
    local_sidereal_deg - ra_deg));
  const double sine_altitude
    = std::sin(latitude) * std::sin(declination)
      + std::cos(latitude) * std::cos(declination) * std::cos(hour_angle);
  return radians_to_degrees(std::asin(
    std::clamp(sine_altitude, -1.0, 1.0)));
}

inline right_ascension_declination
horizontal_to_equatorial(const double azimuth_deg, const double altitude_deg,
                         const double observer_latitude_deg,
                         const double local_sidereal_deg)
{
  const double azimuth = degrees_to_radians(azimuth_deg);
  const double altitude = degrees_to_radians(altitude_deg);
  const double latitude = degrees_to_radians(observer_latitude_deg);
  const double sine_declination
    = std::sin(altitude) * std::sin(latitude)
      + std::cos(altitude) * std::cos(latitude) * std::cos(azimuth);
  const double declination = std::asin(
    std::clamp(sine_declination, -1.0, 1.0));
  const double hour_angle = std::atan2(
    -std::sin(azimuth) * std::cos(altitude),
    std::sin(altitude) * std::cos(latitude)
      - std::cos(altitude) * std::sin(latitude) * std::cos(azimuth));
  return {
    normalize_degrees(local_sidereal_deg - radians_to_degrees(hour_angle)),
    radians_to_degrees(declination),
  };
}

inline void
calculate_altitudes(catalogs& data, const profile& config)
{
  const double sidereal = local_sidereal_time(config);
  auto calculate = [&](std::vector<sky_object>& objects) {
    for (sky_object& object : objects)
      object.altitude_deg = altitude_degrees(
        object.ra_deg, object.dec_deg, config.observer.latitude_deg,
        sidereal);
  };
  calculate(data.stars);
  calculate(data.exoplanet_hosts);
  calculate(data.deep_sky);
  calculate(data.transients);
  calculate(data.solar_system);
}

inline bool
contains(const std::vector<std::string>& values, const std::string& value)
{ return std::find(values.begin(), values.end(), value) != values.end(); }

inline bool
object_matches_instrument(const sky_object& object,
                          const profile& config,
                          const double sun_altitude_deg)
{
  for (const std::string& band : object.bands)
    if (contains(config.instrument.bands, band))
      {
        if (band == "optical" && object.magnitude.has_value()
            && *object.magnitude
                 > config.instrument.optical_limiting_magnitude)
          continue;
        if (!contains(config.instrument.night_required_bands, band)
            || sun_altitude_deg
                 <= config.instrument.twilight_sun_altitude_deg)
          return true;
      }
  return false;
}

inline bool
object_visible_to_observer(const sky_object& object,
                           const profile& config,
                           const double sun_altitude_deg)
{
  return object.altitude_deg >= config.instrument.minimum_altitude_deg
    && object_matches_instrument(object, config, sun_altitude_deg);
}

inline double
celestial_longitude(const orientation& orientation_value,
                    const double right_ascension_deg)
{
  const double offset = right_ascension_deg
    - orientation_value.central_right_ascension_deg;
  return normalize_signed_degrees(
    orientation_value.celestial_handedness ? -offset : offset);
}

} // namespace cart0freak0::astro_generation

#endif
