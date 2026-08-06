// Anthropocene non-sparse temperature-field generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "anthropocene-temperature-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::anthropocene_temperature_generation::run_temperature(
        argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-anthropocene-temperature: "
                << error.what() << '\n';
      return 1;
    }
}
