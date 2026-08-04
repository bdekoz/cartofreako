// Generate two exact face-clipped Myriahedral water slices.
// -*- mode: C++ -*-

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

#include <cart0freak0-myriahedral-slicing.h>

namespace {

namespace slicing = a60::carto::myriahedral_slicing;
using a60::carto::frame;

void
generate(const std::filesystem::path& source,
         const std::filesystem::path& output_directory)
{
  const frame carrier {44, 24.75};
  const std::string source_fragment = source.stem().string();
  const auto slices = slicing::make_group_slices(carrier);
  for (const slicing::slice_descriptor& slice : slices)
    {
      const std::string basename = slicing::water_slice_basename(slice);
      const std::filesystem::path output
        = output_directory / (basename + ".svg");
      slicing::write_slice_svg(
        output, source, source_fragment, slice, carrier);
      slicing::verify_slice_svg(
        output, source, source_fragment, slice, carrier);
      std::cout << output.string() << ": "
                << slicing::format_number(slice.output_frame.width()) << " x "
                << slicing::format_number(slice.output_frame.height())
                << ", " << slice.selected_faces << " faces\n";
    }
  std::cout << "written: " << slices.size()
            << " complementary Myriahedral face-group slices\n";
}

} // namespace

int
main(const int argc, char** argv)
try
  {
    if (argc > 3)
      throw std::invalid_argument(
        "usage: generate-myriahedral-slices "
        "[source-water.svg [output-directory]]");
    const std::filesystem::path source
      = argc >= 2 ? argv[1] : "water-myriahedral-44-24.75.svg";
    const std::filesystem::path output_directory
      = argc >= 3 ? argv[2] : ".";
    generate(source, output_directory);
  }
catch (const std::exception& error)
  {
    std::cerr << "generate-myriahedral-slices: " << error.what() << '\n';
    return 1;
  }
