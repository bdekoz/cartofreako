// Cloud/CDN site atlas and opt-in network topology generator entry point.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>

#include "network-infrastructure-generation.h"

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::network_infrastructure_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-network-infrastructure: " << error.what() << '\n';
      return 1;
    }
}
