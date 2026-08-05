// Cumulative network swarm generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "network-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::network_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-network: " << error.what() << '\n';
      return 1;
    }
}
