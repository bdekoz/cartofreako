#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include <cart0freak0-myriahedral-slicing.h>

namespace {

bool
near(const double left, const double right, const double tolerance = 1e-9)
{ return std::abs(left - right) <= tolerance; }

} // namespace

int
main()
{
  namespace slicing = a60::carto::myriahedral_slicing;
  const a60::carto::frame carrier {44, 24.75};

  const auto groups = slicing::make_face_groups();
  std::array<std::size_t, 2> counts {};
  for (const std::uint8_t group : groups)
    {
      assert(group == 1 || group == 2);
      ++counts[group - 1];
    }
  assert(counts == slicing::expected_group_face_counts);
  assert(counts[0] + counts[1]
         == a60::carto::myriahedral_detail::face_count);

  // Every configured separator is a retained hinge whose endpoints receive
  // opposite group labels.
  const auto tree = a60::carto::myriahedral_detail::make_tree_adjacency();
  for (const slicing::hinge_cut edge : slicing::group_boundary_hinges)
    {
      assert(slicing::contains_edge(tree, edge));
      assert(groups[edge.first] != groups[edge.second]);
    }

  const auto slices = slicing::make_group_slices(carrier);
  assert(slices.size() == 2);
  for (std::size_t index = 0; index < slices.size(); ++index)
    {
      const slicing::slice_descriptor& slice = slices[index];
      assert(slice.number == static_cast<int>(index + 1));
      assert(slice.selected_faces == counts[index]);
      assert(slice.clip_triangles.size() == counts[index]);
      assert(near(slice.output_frame.width(), slice.source_view.width));
      assert(near(slice.output_frame.height(), slice.source_view.height));
      assert(near(slice.output_frame.moriginx, -slice.source_view.x));
      assert(near(slice.output_frame.moriginy, -slice.source_view.y));
      assert(slice.source_view.x >= 0);
      assert(slice.source_view.y >= 0);
      assert(slice.source_view.x + slice.source_view.width <= 44 + 1e-8);
      assert(slice.source_view.y + slice.source_view.height <= 24.75 + 1e-8);
      for (const svg::vrange& triangle : slice.clip_triangles)
        {
          assert(triangle.size() == 3);
          for (const auto [x, y] : triangle)
            {
              assert(x >= slice.source_view.x - 1e-9);
              assert(x <= slice.source_view.x
                          + slice.source_view.width + 1e-9);
              assert(y >= slice.source_view.y - 1e-9);
              assert(y <= slice.source_view.y
                          + slice.source_view.height + 1e-9);
            }
        }
    }

  // These bounds register the reference topology, 335-degree rotation,
  // 16:9 normalization, and five-hinge partition together.
  assert(near(slices[0].source_view.x, 4.62928339117, 1e-8));
  assert(near(slices[0].source_view.y, 0, 1e-8));
  assert(near(slices[0].source_view.width, 22.5313244677, 1e-8));
  assert(near(slices[0].source_view.height, 24.75, 1e-8));
  assert(near(slices[1].source_view.x, 8.17447516357, 1e-8));
  assert(near(slices[1].source_view.y, 4.93044675727, 1e-8));
  assert(near(slices[1].source_view.width, 31.1962414453, 1e-8));
  assert(near(slices[1].source_view.height, 16.1085708816, 1e-8));

  bool rejected = false;
  try
    {
      static_cast<void>(
        slicing::make_group_slices(a60::carto::frame {44, 22}));
    }
  catch (const std::invalid_argument&)
    { rejected = true; }
  assert(rejected);
}
