// Use the atlas's projection for the India detail viewport and diagnostic marks.
#include <iomanip>
#include <iostream>
#include "projection-generation-common.h"
int main() {
  namespace gen=cart0freak0::generation;
  const gen::projection_context context(gen::find_projection_spec("authagraph"),"stage-2-points");
  double latitude,longitude;
  std::cout<<std::setprecision(17);
  while(std::cin>>latitude>>longitude) {
    const auto [x,y]=gen::project_point(context,{latitude,longitude});
    std::cout<<x<<' '<<y<<'\n';
  }
}
