// Generate the Natural Earth ocean-and-land base map.
// -*- mode: C++ -*-

#include "natural-earth-generation.h"

int
main(const int argc, char** argv)
{
  using namespace cart0freak0::natural_earth_generation;
  return run(artifact_kind::earth, argc, argv);
}
