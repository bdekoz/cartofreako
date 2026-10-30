// Projection coordinates and vector context for the shared Python renderers.
#include "natural-earth-generation.h"
#include <iomanip>
#include <iostream>

int main(int argc, char** argv)
{
  try {
    if (argc < 3) throw std::runtime_error("usage: generation-context info|points|basemap PROJECTION [OUTPUT-BASENAME]");
    namespace g = cart0freak0::generation;
    namespace ne = cart0freak0::natural_earth_generation;
    const auto& spec = g::find_projection_spec(argv[2]);
    const g::projection_context context(spec);
    const std::string mode(argv[1]);
    std::cout << std::setprecision(12);
    if (mode == "info")
      std::cout << "{\"projection\":\"" << spec.argument << "\",\"title\":\"" << spec.title
        << "\",\"suffix\":\"-" << spec.output_tag << "\",\"width\":" << spec.width
        << ",\"height\":" << spec.height << "}\n";
    else if (mode == "points") {
      double lon, lat;
      while (std::cin >> lon >> lat) {
        const auto [x,y] = g::project_point(context, {lat,lon});
        std::cout << x << ' ' << y << '\n';
      }
    } else if (mode == "basemap" && argc == 4) {
      ne::initialize_gdal();
      g::projection_document doc(argv[3], "Vector geographic context", context.map_frame.frame_area);
      const std::array<ne::layer_spec,2> specs {{
        {"land", "Natural Earth land", "ne_10m_land.shp", ne::geometry_role::area,
         ne::area_style({242,242,242}), .05, .82},
        {"terrestrial-coastline", "Natural Earth coastlines", "ne_10m_coastline.shp", ne::geometry_role::line,
         ne::line_style({85,85,85}, cart0freak0::generation_style::coastline_atmosphere_width_pt/72,
                        cart0freak0::generation_style::coastline_atmosphere_opacity), .03, .82}
      }};
      for (const auto& layer : specs) {
        svg::group_element group; group.start_element(std::string(layer.id));
        if (spec.kind == g::projection_kind::star_x)
          static_cast<void>(ne::render_star_x_source(group,layer,context,ne::make_antarctic_cap(context)));
        else static_cast<void>(ne::render_source(group,layer,context));
        group.finish_element(); doc.add_element(group);
      }
    } else throw std::runtime_error("invalid generation-context command");
    return 0;
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
