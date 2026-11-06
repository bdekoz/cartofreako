// Export original projected cell paths for value-driven Setouchi web styling.
#include <exception>
#include <fstream>
#include <iostream>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>

#include "cloud-atmosphere-generation.h"

int main(const int argc, char** argv)
{
  namespace atmosphere = cart0freak0::cloud_atmosphere_generation;
  namespace generation = cart0freak0::generation;
  try
    {
      if (argc != 4)
        throw std::invalid_argument("usage: export-atmosphere-cells PROFILE SNAPSHOT OUTPUT.json");
      const auto profile = atmosphere::load_atmosphere_profile(argv[1]);
      const auto dataset = atmosphere::load_atmosphere_dataset(argv[2], profile);
      const auto index = atmosphere::layer_index(profile, "shortwave_radiation_w_m2");
      const auto& definition = profile.layers[index];
      const auto& observation = atmosphere::observation_for(dataset, definition.source_id);
      const generation::projection_context context(
        generation::find_projection_spec("authagraph"), "setouchi-radiation-cells");
      std::ofstream output(argv[3]);
      atmosphere::atmosphere_require(output.good(), "Cannot open projected-cell output");
      rapidjson::OStreamWrapper stream(output);
      rapidjson::Writer<rapidjson::OStreamWrapper> writer(stream);
      writer.StartObject();
      writer.Key("schema"); writer.String("cartofreako-atmosphere-cell-paths-v1");
      writer.Key("projection"); writer.String("authagraph");
      writer.Key("property"); writer.String(definition.property.c_str());
      writer.Key("observation_end_utc"); writer.String(observation.end.iso_utc.c_str());
      writer.Key("feature_count"); writer.Uint64(dataset.cells.size());
      writer.Key("h3_resolution"); writer.Uint(dataset.h3_resolution);
      writer.Key("missing_semantics"); writer.String(dataset.missing_semantics.c_str());
      writer.Key("cells"); writer.StartArray();
      std::size_t count = 0;
      for (const auto& cell : dataset.cells)
        if (cell.values[index].has_value())
          {
            std::string path;
            for (auto polygon : atmosphere::h3_polygons(cell.h3))
              atmosphere::append_projected_polygon(path, context, std::move(polygon));
            char h3[17] {};
            atmosphere::atmosphere_require(h3ToString(cell.h3, h3, sizeof(h3)) == E_SUCCESS,
                                           "Cannot format H3 cell identifier");
            writer.StartObject();
            writer.Key("h3"); writer.String(h3);
            writer.Key("value"); writer.Double(*cell.values[index]);
            writer.Key("valid_fraction"); writer.Double(cell.valid_fractions[index]);
            writer.Key("source_bin"); writer.Uint(atmosphere::value_bin(*cell.values[index], definition) + 1);
            writer.Key("path"); writer.String(path.c_str());
            writer.EndObject();
            ++count;
          }
      writer.EndArray(); writer.EndObject();
      output << '\n';
      atmosphere::atmosphere_require(output.good(), "Cannot finish projected-cell output");
      std::cout << "Exported " << count << " shortwave-radiation cell paths\n";
      return 0;
    }
  catch (const std::exception& error)
    {
      std::cerr << "export-atmosphere-cells: " << error.what() << '\n';
      return 1;
    }
}
