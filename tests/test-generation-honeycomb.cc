#include "generation-honeycomb.h"
#include <cassert>
#include <set>

namespace honeycomb = cart0freak0::generation_honeycomb;

int main()
{
  for (std::size_t common : {0, 1, 20, 60, 61, 100, 10000})
    for (std::size_t rare : {0, 1, 2, 100})
      {
        const std::array<std::size_t, 4> counts {common, rare, 0, 1};
        const auto result = honeycomb::allocation(counts, 61);
        const auto total = std::accumulate(counts.begin(), counts.end(), std::size_t{});
        assert(std::accumulate(result.begin(), result.end(), std::size_t{}) == std::min(total, std::size_t{61}));
        for (std::size_t i = 0; i < counts.size(); ++i)
          assert((result[i] > 0) == (counts[i] > 0));
        if (total <= 61) assert(result == counts);
      }
  bool rejected = false;
  try { static_cast<void>(honeycomb::allocation({100, 1, 1, 1}, 3)); }
  catch (const std::invalid_argument&) { rejected = true; }
  assert(rejected);
  const auto offsets = honeycomb::offsets(61, .0175);
  const std::set<std::pair<double, double>> unique(offsets.begin(), offsets.end());
  assert(unique.size() == 61 && offsets.front() == std::make_pair(0.0, 0.0));
  for (int q = -8; q <= 8; ++q)
    for (int r = -8; r <= 8; ++r)
      assert(honeycomb::cell(1.5*.16*q, std::sqrt(3.0)*.16*(r+q/2.0), .16) == std::make_pair(q,r));
}
