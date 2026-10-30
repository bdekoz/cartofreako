#include "projection-generation-common.h"
#include <iomanip>
#include <iostream>
int main() {
  using namespace cart0freak0::generation;
  const projection_context context(find_projection_spec("authagraph"));
  double lon, lat;
  std::cout << std::setprecision(12);
  while (std::cin >> lon >> lat) {
    const auto [x,y] = project_point(context, {lat,lon});
    std::cout << x << ' ' << y << '\n';
  }
}
