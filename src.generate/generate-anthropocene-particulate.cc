// Anthropocene particulate observation-atlas generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "anthropocene-particulate-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::anthropocene_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-anthropocene-particulate: " << error.what() << '\n';
      return 1;
    }
}
