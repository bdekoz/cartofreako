// Shared font configuration for text rendered into generated maps.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_GENERATION_TYPOGRAPHY_H
#define CART0FREAK0_GENERATION_TYPOGRAPHY_H 1

#include <algorithm>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <string_view>

#include <izzi-svg.h>

namespace cart0freak0::generation {

inline constexpr std::string_view default_label_font
  = "atkinson_hyperlegible";
inline constexpr std::string_view atkinson_hyperlegible_family
  = "Atkinson Hyperlegible";
inline constexpr const char* label_font_environment
  = "CARTOFREAKO_LABEL_FONT";

inline std::string
resolve_label_font_family(const std::string_view configured)
{
  if (configured == default_label_font
      || configured == atkinson_hyperlegible_family)
    return std::string(atkinson_hyperlegible_family);

  const bool only_whitespace = std::all_of(
    configured.begin(), configured.end(), [](const unsigned char character) {
      return character == ' ' || character == '\t';
    });
  if (configured.empty() || only_whitespace)
    throw std::invalid_argument("the configured label font is empty");

  for (const unsigned char character : configured)
    if (character < 0x20 || character == 0x7f || character == '"'
        || character == '&' || character == '<' || character == '>')
      throw std::invalid_argument(
        "the configured label font is not safe for an SVG attribute");
  return std::string(configured);
}

inline const std::string&
configured_label_font_family()
{
  static const std::string family = [] {
    const char* configured = std::getenv(label_font_environment);
    return resolve_label_font_family(
      configured == nullptr ? default_label_font
                            : std::string_view(configured));
  }();
  return family;
}

inline svg::typography
with_configured_label_font(svg::typography typography)
{
  typography._M_face = configured_label_font_family();
  return typography;
}

inline void
verify_configured_label_font(const std::string_view document,
                             const std::string_view product)
{
  const std::string attribute
    = "font-family=\"" + configured_label_font_family() + "\"";
  std::size_t position = 0;
  while ((position = document.find("<text ", position))
         != std::string_view::npos)
    {
      const std::size_t end = document.find('>', position);
      if (end == std::string_view::npos
          || document.substr(position, end - position).find(attribute)
               == std::string_view::npos)
        throw std::runtime_error(
          std::string(product) + " contains a text element without the "
          + configured_label_font_family() + " font");
      position = end + 1;
    }
}

} // namespace cart0freak0::generation

#endif
