// Reuse Alpha60's cache ingestion, member colours and weighted-circle renderer.
// Only the geographic projection and map frame are selected here.
#define main alpha60_carto_geo_original_main
#include "a60-carto-geo.cc"
#undef main

int main(int argc, char** argv)
{
  if (argc != 4)
    {
      std::cerr << "usage: render-swarm-authagraph CACHE COLLECTION OUTPUT\n";
      return 2;
    }
  const a60::scoped_quiet_output quiet(true);
  const a60::string cache(argv[1]), key(argv[2]);
  a60::io::set_run_time_resources(cache, cache);
  const auto pointer = a60::collection_catalog().get_unique(key);
  if (!pointer)
    throw std::invalid_argument("Unknown collection: " + key);
  a60::collection collection(*pointer);
  collection.initialize_ids_and_members();
  a60::swarm_geos swarm = a60::coalesce_with_unique_btiha(collection, "cumulative");
  a60::weigh_unique_collection(swarm);
  constexpr double width = 44.0 * 96.0;
  const a60::carto::frame frame(svg::area<> {
    width, width / a60::carto::authagraph_width_to_height_ratio});
  const a60::carto::agproj projection(frame, "earth-authagraph-44-19.052559.svg");
  const a60::carto::cartography<a60::carto::agproj> cartography(frame, projection);
  const a60::string output = a60::io::end_path(argv[3]);
  a60::io::pre_check_output_directory(output);
  render_cumulative_maps(swarm, cartography, output, false);
  return 0;
}
