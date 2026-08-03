#include <array>
#include <cassert>
#include <cmath>
#include <stdexcept>
#include <string>

#include <cart0freak0-cahill-keyes-slicing.h>

#include "projection-generation-common.h"

namespace {

bool
near(const double left, const double right, const double tolerance = 1e-9)
{ return std::abs(left - right) <= tolerance; }

} // namespace

int
main()
{
  namespace slicing = a60::carto::ck_slicing;
  const a60::carto::frame carrier {44, 22};

  // The projection coordinate system stays 44 by 22, but the outer document
  // must declare those dimensions as physical inches rather than CSS pixels.
  {
    cart0freak0::generation::projection_document document(
      "physical-document-test", "physical size test",
      carrier.frame_area, false);
    document.start("physical size test");
    const std::string markup = document.str();
    assert(markup.find(
      "width=\"44.000000in\" height=\"22.000000in\"")
      != std::string::npos);
    assert(markup.find(
      "viewBox=\"0 0 44.000000 22.000000\"")
      != std::string::npos);
    assert(markup.find("44.000000px") == std::string::npos);
    document.finish(false);
  }

  const auto four = slicing::make_four_slices(carrier);
  assert(four.size() == 4);
  constexpr std::array expected_octants {
    std::array {1, 6}, std::array {2, 7},
    std::array {3, 8}, std::array {4, 5},
  };
  for (std::size_t index = 0; index < four.size(); ++index)
    {
      const auto& slice = four[index];
      assert(slice.number == static_cast<int>(index + 1));
      assert(slice.octants == expected_octants[index]);
      assert(slice.octant_count == 2);
      assert(near(slice.source_view.x, 11 * index));
      assert(near(slice.source_view.y, 0));
      assert(near(slice.output_frame.width(), 11));
      assert(near(slice.output_frame.height(), 22));
      assert(near(slice.output_frame.moriginx,
                  -11 * static_cast<double>(index)));
      assert(near(slice.output_frame.moriginy, 0));
      assert(slice.clip_outline.empty());
      assert(slice.latitudes.has_value());
    }

  const auto eight = slicing::make_eight_slices(carrier);
  assert(eight.size() == 8);
  for (std::size_t index = 0; index < eight.size(); ++index)
    {
      const auto& slice = eight[index];
      assert(slice.number == static_cast<int>(index + 1));
      assert(slice.octant_count == 1);
      assert(slice.octants[0] == slice.number);
      assert(slice.clip_outline.size() > 100);
      assert(near(slice.output_frame.width(), slice.source_view.width));
      assert(near(slice.output_frame.height(), slice.source_view.height));
      assert(slice.source_view.x >= 0);
      assert(slice.source_view.y >= 0);
      assert(slice.source_view.x + slice.source_view.width <= 44 + 1e-8);
      assert(slice.source_view.y + slice.source_view.height <= 22 + 1e-8);
      for (const auto [x, y] : slice.clip_outline)
        {
          assert(x >= slice.source_view.x - 1e-9);
          assert(x <= slice.source_view.x + slice.source_view.width + 1e-9);
          assert(y >= slice.source_view.y - 1e-9);
          assert(y <= slice.source_view.y + slice.source_view.height + 1e-9);
        }
    }

  // All northern faces share one natural size; all southern faces share the
  // other. Their carrier rectangles overlap vertically, proving that a 4x2
  // rectangular page grid cannot also isolate the semantic octants.
  for (std::size_t index = 1; index < 4; ++index)
    {
      assert(near(eight[index].source_view.width,
                  eight.front().source_view.width));
      assert(near(eight[index].source_view.height,
                  eight.front().source_view.height));
    }
  for (std::size_t index = 5; index < 8; ++index)
    {
      assert(near(eight[index].source_view.width, eight[4].source_view.width));
      assert(near(eight[index].source_view.height,
                  eight[4].source_view.height));
    }
  assert(eight[0].source_view.y + eight[0].source_view.height
         > eight[5].source_view.y);

  bool rejected = false;
  try
    {
      static_cast<void>(
        slicing::make_four_slices(a60::carto::frame {11, 22}));
    }
  catch (const std::invalid_argument&)
    { rejected = true; }
  assert(rejected);
}
