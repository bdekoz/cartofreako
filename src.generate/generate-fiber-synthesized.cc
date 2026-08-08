// Cleaned-union submarine-fiber generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "fiber-synthesized-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::fiber_synthesized_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-fiber-synthesized: " << error.what() << '\n';
      return 1;
    }
}
