// Resolve a JSON generation profile to safe top-level Make targets.
// -*- mode: C++ -*-

#include <exception>
#include <iostream>
#include <string_view>

#include "generation-profile.h"

namespace generation = cart0freak0::generation_profile;

int
main(const int argc, char** argv)
try
  {
    const bool describe = argc == 3 && std::string_view(argv[1]) == "--describe";
    if ((!describe && argc != 2) || (describe && argc != 3))
      {
        std::cerr << "usage: resolve-generation-profile [--describe] PROFILE.json\n";
        return 2;
      }

    const char* path = argv[describe ? 2 : 1];
    const generation::profile selection = generation::load(path);
    const std::vector<std::string> targets = generation::targets(selection);
    if (describe)
      {
        std::cout << "profile: " << path << '\n';
        if (!selection.description.empty())
          std::cout << "description: " << selection.description << '\n';
        std::cout << "projections: " << generation::join(selection.projections)
                  << '\n'
                  << "passes: " << generation::join(selection.passes) << '\n'
                  << "targets:\n";
        for (const std::string& target : targets)
          std::cout << "  " << target << '\n';
      }
    else
      for (const std::string& target : targets)
        std::cout << target << '\n';
    return 0;
  }
catch (const std::exception& error)
  {
    std::cerr << "resolve-generation-profile: " << error.what() << '\n';
    return 1;
  }
