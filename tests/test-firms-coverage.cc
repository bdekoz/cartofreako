// Exercise the actual CSV ingestion and required-global coverage gate.
#define main particulate_preparation_application_main
#include "../src.generate/prepare-anthropocene-particulate.cc"
#undef main

#include <cassert>

int
main()
{
  const fs::path root = fs::temp_directory_path()
    / ("cartofreako-firms-" + std::to_string(
         std::chrono::steady_clock::now().time_since_epoch().count()));
  fs::create_directories(root / "cwfis");
  struct cleanup
  {
    fs::path root;
    ~cleanup() { fs::remove_all(root); }
  } remove {root};
  const auto csv = [&](const std::string& name, const int days,
                       const std::set<int>& missing, const bool all_regions) {
    const fs::path path = root / name;
    std::ofstream stream {path};
    stream << "latitude,longitude,acq_date\n";
    const std::vector<std::pair<int, int>> points {
      {40, -100}, {-10, -55}, {50, 10}, {-10, 20},
      {60, 100}, {35, 130}, {-25, 135},
    };
    const std::chrono::sys_days first {
      std::chrono::year {2026} / std::chrono::January / 1};
    for (int i = 0; i < days; ++i)
      {
        const int day = sys_day_key(first + std::chrono::days {i});
        if (missing.contains(day)) continue;
        for (std::size_t n = 0; n < (all_regions ? points.size() : 1); ++n)
          stream << points[n].first << ',' << points[n].second
                 << ',' << iso_day(day) << '\n';
      }
    return path;
  };
  configuration config;
  config.year = 2026;
  config.snapshot_date_key = 20260805;
  const std::set<int> outages {
    20260310, 20260311, 20260312, 20260428, 20260429, 20260430,
    20260601, 20260602, 20260711, 20260712, 20260713, 20260714,
    20260715, 20260716,
  };
  inputs paths;
  paths.cwfis_directory = root / "cwfis";
  paths.firms_csvs = {csv("suomi-outages.csv", 216, outages, true)};
  observations data;
  source_statistics failed;
  process_fire_sources(paths, config, data, failed);
  assert(failed.firms_unique_days == 202);
  assert(missing_firms_days(config, failed)
         == std::vector<int>(outages.begin(), outages.end()));
  try
    {
      validate_required_firms(config, failed);
      assert(false && "Incomplete source was accepted");
    }
  catch (const std::runtime_error& error)
    {
      const std::string message {error.what()};
      assert(message.find("202/216 snapshot days (93.5%; minimum 95%)")
             != std::string::npos);
      assert(message.find("2026-03-10") != std::string::npos);
      assert(message.find("VIIRS_NOAA20_SP VIIRS_NOAA20_NRT")
             != std::string::npos);
    }
  // A supported sensor covers the same dates. Repeated observations from
  // overlapping standard/NRT requests never multiply cell-day counts.
  paths.firms_csvs = {csv("noaa20-sp.csv", 216, {}, true),
                     csv("noaa20-nrt-overlap.csv", 216, {}, true)};
  source_statistics complete;
  data.clear();
  process_fire_sources(paths, config, data, complete);
  validate_required_firms(config, complete);
  assert(complete.firms_unique_days == 216);
  for (const auto& [cell, values] : data)
    {
      static_cast<void>(cell);
      assert(values[static_cast<std::size_t>(metric::active_fire_days)].size()
             == 216);
    }
  // Preserve the exact 95% boundary and the independent geographic audit.
  config.snapshot_date_key = 20260411; // 100 calendar days.
  const auto first = *make_day(2026, 1, 1);
  std::set<int> missing;
  for (int i = 95; i < 100; ++i)
    missing.insert(sys_day_key(first + std::chrono::days {i}));
  for (int eligible : {95, 94})
    {
      if (eligible == 94)
        missing.insert(sys_day_key(first + std::chrono::days {94}));
      paths.firms_csvs = {csv("boundary.csv", 100, missing, true)};
      source_statistics boundary;
      data.clear();
      process_fire_sources(paths, config, data, boundary);
      bool accepted = true;
      try { validate_required_firms(config, boundary); }
      catch (const std::runtime_error&) { accepted = false; }
      assert(accepted == (eligible == 95));
    }
  paths.firms_csvs = {csv("one-region.csv", 100, {}, false)};
  source_statistics regional;
  data.clear();
  process_fire_sources(paths, config, data, regional);
  bool rejected = false;
  try { validate_required_firms(config, regional); }
  catch (const std::runtime_error& error)
    { rejected = std::string(error.what()).find("global region audit")
                 != std::string::npos; }
  assert(rejected);
  std::cout << "FIRMS outage, coverage-boundary, overlap and region checks passed\n";
}
