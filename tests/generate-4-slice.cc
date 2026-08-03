// Generate four unscaled Cahill-Keyes whole-Earth strip slices.
// -*- mode: C++ -*-

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

#include <cart0freak0-cahill-keyes-slicing.h>

namespace {

namespace slicing = a60::carto::ck_slicing;
using a60::carto::frame;

void
generate(const std::filesystem::path& source,
         const std::filesystem::path& output_directory)
{
  const frame carrier {44, 22};
  const std::string source_fragment = source.stem().string();
  const auto slices = slicing::make_four_slices(carrier);
  if (slices.size() != 4)
    throw std::runtime_error("four-slice generator created the wrong count");

  for (const slicing::slice_descriptor& slice : slices)
    {
      const std::string basename = slicing::earth_slice_basename(slice);
      const std::filesystem::path output
        = output_directory / (basename + ".svg");
      slicing::write_slice_svg(
        output, source, source_fragment, slice, carrier);
      slicing::verify_slice_svg(
        output, source, source_fragment, slice);
      std::cout << output.string() << ": "
                << slicing::format_number(slice.output_frame.width()) << " x "
                << slicing::format_number(slice.output_frame.height())
                << ", octants " << slicing::octant_names(slice) << '\n';
    }
  std::cout << "written: " << slices.size() << " four-strip slices\n";
}

} // namespace

int
main(const int argc, char** argv)
try
  {
    if (argc > 3)
      throw std::invalid_argument(
        "usage: generate-4-slice [source-earth.svg [output-directory]]");
    const std::filesystem::path source
      = argc >= 2 ? argv[1] : "earth-ck-44-22.svg";
    const std::filesystem::path output_directory
      = argc >= 3 ? argv[2] : ".";
    generate(source, output_directory);
  }
catch (const std::exception& error)
  {
    std::cerr << "generate-4-slice: " << error.what() << '\n';
    return 1;
  }
