// Stage 6b resources generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "resources-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::resources_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-resources: " << error.what() << '\n';
      return 1;
    }
}
