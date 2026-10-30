// Reuse Alpha60's cache ingestion, member colours and weighted-circle renderer.
// Only the geographic projection and map frame are selected here.
#define main alpha60_carto_geo_original_main
#include "a60-carto-geo.cc"
#undef main
#include "projection-generation-common.h"
#include <type_traits>

int main(int argc, char** argv)
{
  if (argc != 5)
    {
      std::cerr << "usage: generate-native-swarm PROJECTION CACHE COLLECTION OUTPUT\n";
      return 2;
    }
  const a60::scoped_quiet_output quiet(true);
  const a60::string cache(argv[2]), key(argv[3]);
  a60::io::set_run_time_resources(cache, cache);
  const auto pointer = a60::collection_catalog().get_unique(key);
  if (!pointer)
    throw std::invalid_argument("Unknown collection: " + key);
  a60::collection collection(*pointer);
  collection.initialize_ids_and_members();
  a60::swarm_geos swarm = a60::coalesce_with_unique_btiha(collection, "cumulative");
  a60::weigh_unique_collection(swarm);
  namespace generation = cart0freak0::generation;
  const auto& spec = generation::find_projection_spec(argv[1]);
  const a60::carto::frame frame(svg::area<> {spec.width * 96, spec.height * 96});
  const auto projection = generation::make_projection(spec, frame,
    "earth-" + std::string(spec.output_tag) + ".svg");
  const a60::string output = a60::io::end_path(argv[4]);
  a60::io::pre_check_output_directory(output);
  static_assert(cart0freak0::generation_style::swarm_fill_opacity == 0.05,
                "Alpha60 cumulative rendering currently uses 5% fill opacity");
  std::visit([&](const auto& concrete) {
    using Projection = std::decay_t<decltype(concrete)>;
    const a60::carto::cartography<Projection> cartography(frame, concrete);
    render_cumulative_maps(swarm, cartography, output, false);
  }, projection);
  return 0;
}
