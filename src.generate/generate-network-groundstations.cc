// Network Groundstations generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "network-groundstations-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::network_groundstations_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-network-groundstations: " << error.what()
                << '\n';
      return 1;
    }
}
