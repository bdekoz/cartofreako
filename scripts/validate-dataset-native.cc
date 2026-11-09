// Validate candidate profiles with the same loaders used by the generators.
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <maxminddb.h>
#include "anthropocene-particulate-data.h"
#include "anthropocene-temperature-data.h"
#include "astro-data.h"
#include "astro-observer.h"
#include "cloud-atmosphere-data.h"
#include "orbiting-data.h"
#include "resources-data.h"

int main(int argc, char** argv)
{
  try
    {
      if (argc != 7)
        throw std::runtime_error("usage: validate-dataset-native ORBITAL_PROFILE ASTRO_DIR ANTHROPOCENE_DIR RESOURCES_PROFILE ATMOSPHERE_DIR MMDB");
      MMDB_s geolocation{};
      if (MMDB_open(argv[6], MMDB_MODE_MMAP, &geolocation) != MMDB_SUCCESS)
        throw std::runtime_error("Configured native swarm geolocation database is unreadable");
      MMDB_close(&geolocation);
      namespace orbital = cart0freak0::orbiting_generation;
      namespace astro = cart0freak0::astro_generation;
      namespace particulate = cart0freak0::anthropocene_generation;
      namespace temperature = cart0freak0::anthropocene_temperature_generation;
      namespace resources = cart0freak0::resources_generation;
      const auto orbit = orbital::load_profile(argv[1]);
      const auto population = orbital::propagate_catalog(orbital::load_catalogs(orbit), orbit);
      if (population.objects.empty() || population.failed_propagation != 0)
        throw std::runtime_error("Orbital candidate has no finite population or failed propagations");
      for (const auto filename : {"astro-profile.json", "astro-hubble-profile.json"})
        {
          const auto profile = astro::load_profile(std::filesystem::path(argv[2]) / filename);
          const auto catalog = astro::load_catalogs(profile);
          (void)astro::make_observer_state(profile);
          if (catalog.stars.empty())
            throw std::runtime_error("Astronomy candidate is empty");
        }
      for (const auto year : {"2025", "2026"})
        {
          const auto directory = std::filesystem::path(argv[3]);
          const std::string p = std::string("anthropocene-particulate-") + year;
          const auto pp = particulate::load_anthropocene_profile(directory / (p + "-profile.json"));
          const auto pd = particulate::load_anthropocene_dataset(directory / (p + ".geojson"), pp);
          const std::string t = std::string("anthropocene-land-temperature-") + year;
          const auto tp = temperature::load_temperature_profile(directory / (t + "-profile.json"));
          const auto td = temperature::load_temperature_dataset(directory / (t + ".geojson"), tp);
          if (pd.features.empty() || td.cells.empty())
            throw std::runtime_error("Normalized candidate has no source support");
        }
      if (resources::load_resources_profile(argv[4]).values.empty())
        throw std::runtime_error("Resource candidate is empty");
      namespace atmosphere = cart0freak0::cloud_atmosphere_generation;
      for (const auto stem : {"cloud-atmosphere", "cloud-atmosphere-atlas"})
        {
          const auto directory = std::filesystem::path(argv[5]);
          const auto profile = atmosphere::load_atmosphere_profile(directory / (std::string(stem) + "-profile.json"));
          const auto data = atmosphere::load_atmosphere_dataset(directory / profile.prepared_snapshot, profile);
          if (data.cells.empty())
            throw std::runtime_error("Atmosphere candidate has no observed source support");
        }
      std::cout << "Native dataset profiles, source support, finite states and metadata passed\n";
      return 0;
    }
  catch (const std::exception& error)
    {
      std::cerr << "dataset-native: " << error.what() << '\n';
      return 1;
    }
}
