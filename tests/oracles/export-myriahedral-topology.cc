#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/prettywriter.h>

#include "cart0freak0-projection-runtime.h"

namespace fs = std::filesystem;
namespace runtime = cart0freak0::projection_runtime;
namespace rj = rapidjson;

int
main(const int argc, char** argv)
{
  if (argc != 2)
    {
      std::cerr << "usage: export-myriahedral-topology OUTPUT\n";
      return 2;
    }
  std::ofstream stream(argv[1]);
  if (!stream)
    throw std::runtime_error("cannot write topology file");
  rj::OStreamWrapper wrapper(stream);
  rj::PrettyWriter<rj::OStreamWrapper> writer(wrapper);
  writer.SetMaxDecimalPlaces(17);
  writer.StartObject();
  writer.Key("schemaVersion");
  writer.String("cartofreako-declared-myriahedral-topology-v1");
  writer.Key("normativeRole");
  writer.String("shared topology only; no reverse results");
  writer.Key("layouts");
  writer.StartArray();
  constexpr std::array offsets {0U, 85U, 170U, 255U};
  for (const runtime::projection_spec& spec : runtime::projection_specs)
    if (spec.kind == runtime::projection_kind::myriahedral)
      {
        const runtime::projection_context projection(spec);
        const auto& layout
          = std::get<a60::carto::myriaproj>(projection.projection).layout();
        writer.StartObject();
        writer.Key("layoutId"); writer.String(spec.argument.data());
        writer.Key("faces"); writer.StartArray();
        for (std::uint32_t base = 0; base < 20; ++base)
          for (const std::uint32_t offset : offsets)
            {
              const std::uint32_t face = base * 256 + offset;
              writer.StartObject();
              writer.Key("nativeFace"); writer.Uint(face);
              writer.Key("sphericalVertices"); writer.StartArray();
              for (const auto vertex : layout.spherical[face])
                {
                  writer.StartArray();
                  writer.Double(vertex.x); writer.Double(vertex.y);
                  writer.Double(vertex.z);
                  writer.EndArray();
                }
              writer.EndArray();
              writer.EndObject();
            }
        writer.EndArray();
        writer.EndObject();
      }
  writer.EndArray();
  writer.EndObject();
  stream << '\n';
  std::cout << "exported declared Myriahedral topology to " << argv[1]
            << '\n';
}
