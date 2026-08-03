// Generate the Natural Earth physical overlay excluding ocean and land.
// -*- mode: C++ -*-

#include "natural-earth-generation.h"

int
main(const int argc, char** argv)
{
  using namespace cart0freak0::natural_earth_generation;
  return run(artifact_kind::water, argc, argv);
}
