// CPC sample-center domains without allocating the full global H3 grid.
#ifndef CARTOFREAKO_TEMPERATURE_SOURCE_GRID_H
#define CARTOFREAKO_TEMPERATURE_SOURCE_GRID_H

#include <algorithm>
#include <stdexcept>
#include <vector>
#include <h3/h3api.h>

namespace cart0freak0::anthropocene_temperature_generation {

inline std::vector<H3Index>
cpc_grid_h3(const int resolution)
{
  std::vector<H3Index> result;
  result.reserve(720U * 360U);
  for (int row = 0; row < 360; ++row)
    for (int column = 0; column < 720; ++column)
      {
        double longitude = 0.25 + column * 0.5;
        if (longitude > 180) longitude -= 360;
        const LatLng position {degsToRads(89.75 - row * 0.5), degsToRads(longitude)};
        H3Index cell = H3_NULL;
        if (latLngToCell(&position, resolution, &cell) != E_SUCCESS || cell == H3_NULL)
          throw std::runtime_error("Cannot index CPC source-grid center");
        result.push_back(cell);
      }
  return result;
}

inline std::vector<H3Index>
cpc_source_cell_domain(const int resolution)
{
  auto result = cpc_grid_h3(resolution);
  std::sort(result.begin(), result.end());
  result.erase(std::unique(result.begin(), result.end()), result.end());
  return result;
}

} // namespace cart0freak0::anthropocene_temperature_generation
#endif
