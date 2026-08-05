// Solar illumination, P-Tree cloud, and JAXA atmosphere generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "cloud-atmosphere-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::cloud_atmosphere_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-cloud-atmosphere: " << error.what() << '\n';
      return 1;
    }
}
