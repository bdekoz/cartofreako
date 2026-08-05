#include <cassert>
#include <stdexcept>
#include <string>

#include "generation-typography.h"

namespace generation = cart0freak0::generation;

int
main()
{
  assert(generation::resolve_label_font_family("atkinson_hyperlegible")
         == "Atkinson Hyperlegible");
  assert(generation::resolve_label_font_family("Atkinson Hyperlegible")
         == "Atkinson Hyperlegible");
  assert(generation::resolve_label_font_family("Example Sans")
         == "Example Sans");

  const std::string configured_family
    = generation::configured_label_font_family();
  const svg::typography typography
    = generation::with_configured_label_font(svg::k::smono_typo);
  assert(typography._M_face == configured_family);

  generation::verify_configured_label_font(
    "<svg><text font-family=\"" + configured_family
      + "\">A</text></svg>",
    "test SVG");

  for (const std::string configured : {"", "   ", "Unsafe\"Face", "A&B"})
    {
      bool threw = false;
      try
        {
          static_cast<void>(
            generation::resolve_label_font_family(configured));
        }
      catch (const std::invalid_argument&)
        {
          threw = true;
        }
      assert(threw);
    }

  bool threw = false;
  try
    {
      generation::verify_configured_label_font(
        "<svg><text font-family=\"Definitely Not The Configured Font\">"
        "A</text></svg>",
        "test SVG");
    }
  catch (const std::runtime_error&)
    {
      threw = true;
    }
  assert(threw);
}
