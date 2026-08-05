// Validated user selection of projection generation passes.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_GENERATION_PROFILE_H
#define CART0FREAK0_GENERATION_PROFILE_H 1

#include <algorithm>
#include <array>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/error/en.h>

namespace cart0freak0::generation_profile {

namespace fs = std::filesystem;
namespace rj = rapidjson;

inline constexpr std::array<std::string_view, 6> supported_projections {
  "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
  "voronoi",
};

inline constexpr std::array<std::string_view, 12> supported_passes {
  "geometry", "graticules", "earth", "water", "astronomy",
  "orbital-technosphere", "network-swarm", "bathymetry-roulette",
  "network-infrastructure", "resources", "anthropocene",
  "cloud-atmosphere",
};

struct profile
{
  unsigned schema_version = 1;
  std::string description;
  bool all_projections = false;
  bool all_passes = false;
  std::vector<std::string> projections;
  std::vector<std::string> passes;
};

inline void
profile_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline std::string
normalize_token(const std::string_view input)
{
  std::string result;
  result.reserve(input.size());
  for (const unsigned char value : input)
    {
      if (value == '_')
        result.push_back('-');
      else
        result.push_back(static_cast<char>(std::tolower(value)));
    }
  return result;
}

inline std::optional<std::string>
canonical_projection(const std::string_view input)
{
  const std::string value = normalize_token(input);
  if (value == "cahill-keyes" || value == "cahillkeyes" || value == "ck")
    return "cahill-keyes";
  if (value == "authagraph" || value == "autha-graph")
    return "authagraph";
  if (value == "dymaxion")
    return "dymaxion";
  if (value == "myriahedral")
    return "myriahedral";
  if (value == "star-x" || value == "starx")
    return "star-x";
  if (value == "voronoi" || value == "voroni")
    return "voronoi";
  return std::nullopt;
}

inline std::optional<std::string>
canonical_pass(const std::string_view input)
{
  const std::string value = normalize_token(input);
  if (value == "geometry")
    return "geometry";
  if (value == "graticule" || value == "graticules")
    return "graticules";
  if (value == "earth")
    return "earth";
  if (value == "water" || value == "ocean")
    return "water";
  if (value == "astro" || value == "astronomy")
    return "astronomy";
  if (value == "orbiting" || value == "orbital-technosphere")
    return "orbital-technosphere";
  if (value == "network-swarm" || value == "network" || value == "swarm")
    return "network-swarm";
  if (value == "network-infrastructure" || value == "infrastructure")
    return "network-infrastructure";
  if (value == "bathymetry-roulette" || value == "bathymetry-rolette"
      || value == "art-agua-roulette")
    return "bathymetry-roulette";
  if (value == "anthropocene")
    return "anthropocene";
  if (value == "resources" || value == "resource" || value == "resouces"
      || value == "world-game" || value == "world-game-resources")
    return "resources";
  if (value == "cloud-atmosphere" || value == "clouds"
      || value == "atmosphere" || value == "solar-atmosphere"
      || value == "solar/cloud/atmosphere")
    return "cloud-atmosphere";
  return std::nullopt;
}

template<std::size_t Size>
inline std::string
allowed_values(const std::array<std::string_view, Size>& values)
{
  std::string result;
  for (const std::string_view value : values)
    {
      if (!result.empty())
        result += ", ";
      result += value;
    }
  return result;
}

using canonicalizer = std::optional<std::string> (*)(std::string_view);

template<std::size_t Size>
inline std::vector<std::string>
read_selector(const rj::Value& document, const char* member_name,
              const std::array<std::string_view, Size>& supported,
              const canonicalizer canonicalize, bool& selected_all,
              const std::string_view context)
{
  profile_require(document.HasMember(member_name),
                  std::string(context) + " is missing '" + member_name + "'");
  const rj::Value& selector = document[member_name];
  profile_require(selector.IsArray(), std::string(context) + "."
                                        + member_name + " must be an array");
  profile_require(!selector.Empty(), std::string(context) + "."
                                      + member_name + " must not be empty");

  std::vector<std::string> result;
  for (const rj::Value& item : selector.GetArray())
    {
      profile_require(item.IsString(), std::string(context) + "."
                                         + member_name
                                         + " must contain only strings");
      const std::string_view raw {item.GetString(), item.GetStringLength()};
      if (normalize_token(raw) == "all")
        {
          profile_require(selector.Size() == 1,
                          std::string(context) + "." + member_name
                            + " may use 'all' only as its sole value");
          selected_all = true;
          result.reserve(supported.size());
          for (const std::string_view value : supported)
            result.emplace_back(value);
          return result;
        }

      const std::optional<std::string> canonical = canonicalize(raw);
      profile_require(canonical.has_value(),
                      std::string(context) + "." + member_name
                        + " contains unknown value '" + std::string(raw)
                        + "'; choose all or one of: "
                        + allowed_values(supported));
      profile_require(std::find(result.begin(), result.end(), *canonical)
                        == result.end(),
                      std::string(context) + "." + member_name
                        + " contains duplicate selection '" + *canonical
                        + "'");
      result.push_back(*canonical);
    }
  return result;
}

inline profile
parse(const rj::Document& document, const std::string_view context)
{
  profile_require(document.IsObject(),
                  std::string(context) + " root must be an object");

  std::vector<std::string> member_names;
  for (auto member = document.MemberBegin(); member != document.MemberEnd();
       ++member)
    {
      const std::string_view name {
        member->name.GetString(), member->name.GetStringLength()};
      profile_require(std::find(member_names.begin(), member_names.end(), name)
                        == member_names.end(),
                      std::string(context) + " contains duplicate member '"
                        + std::string(name) + "'");
      member_names.emplace_back(name);
      profile_require(name == "schema_version" || name == "description"
                        || name == "projections" || name == "passes",
                      std::string(context) + " contains unknown member '"
                        + std::string(name) + "'");
    }

  profile_require(document.HasMember("schema_version"),
                  std::string(context) + " is missing 'schema_version'");
  profile_require(document["schema_version"].IsUint(),
                  std::string(context)
                    + ".schema_version must be a nonnegative integer");
  profile_require(document["schema_version"].GetUint() == 1,
                  std::string(context)
                    + " uses an unsupported generation profile schema");

  profile result;
  if (document.HasMember("description"))
    {
      profile_require(document["description"].IsString(),
                      std::string(context) + ".description must be a string");
      result.description = document["description"].GetString();
    }
  result.projections = read_selector(
    document, "projections", supported_projections, canonical_projection,
    result.all_projections, context);
  result.passes = read_selector(
    document, "passes", supported_passes, canonical_pass, result.all_passes,
    context);
  return result;
}

inline profile
parse_json(const std::string_view json,
           const std::string_view context = "generation profile")
{
  rj::Document document;
  document.Parse(json.data(), json.size());
  profile_require(
    !document.HasParseError(),
    std::string(context) + " is not valid JSON: "
      + rj::GetParseError_En(document.GetParseError()) + " at byte "
      + std::to_string(document.GetErrorOffset()));
  return parse(document, context);
}

inline profile
load(const fs::path& path)
{
  std::ifstream input {path};
  profile_require(input.good(),
                  "failed to open generation profile " + path.string());
  const std::string json {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  return parse_json(json, path.string());
}

inline std::string
target_name(const std::string_view projection, const std::string_view pass)
{
  if (pass == "astronomy")
    return "generate-astro-" + std::string(projection);
  if (pass == "orbital-technosphere")
    return "generate-orbiting-" + std::string(projection);
  if (pass == "network-swarm")
    return "generate-network-swarm-" + std::string(projection);
  profile_require(std::find(supported_passes.begin(), supported_passes.end(),
                            pass) != supported_passes.end(),
                  "internal error: unsupported canonical pass");
  return "generate-" + std::string(pass) + "-" + std::string(projection);
}

inline std::vector<std::string>
targets(const profile& selection)
{
  std::vector<std::string> result;
  result.reserve(selection.projections.size() * selection.passes.size());
  for (const std::string& projection : selection.projections)
    for (const std::string& pass : selection.passes)
      result.push_back(target_name(projection, pass));
  return result;
}

inline std::string
join(const std::vector<std::string>& values)
{
  std::string result;
  for (const std::string& value : values)
    {
      if (!result.empty())
        result += ", ";
      result += value;
    }
  return result;
}

} // namespace cart0freak0::generation_profile

#endif // CART0FREAK0_GENERATION_PROFILE_H
