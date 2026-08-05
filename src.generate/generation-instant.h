// Shared UTC generation-instant parsing and reproducible process clocks.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_GENERATION_INSTANT_H
#define CART0FREAK0_GENERATION_INSTANT_H 1

#include <array>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <stdexcept>
#include <string>
#include <string_view>

namespace cart0freak0::generation_time {

inline constexpr double julian_unix_epoch = 2440587.5;
inline constexpr double julian_j2000 = 2451545.0;
inline constexpr double seconds_per_day = 86400.0;

struct instant
{
  std::chrono::sys_seconds value;
  std::string iso_utc;
  double julian_date;
};

inline void
instant_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline int
parse_decimal_component(const std::string_view text, const std::size_t offset,
                        const std::size_t count,
                        const std::string_view component)
{
  instant_require(offset + count <= text.size(),
                  "timestamp is missing " + std::string(component));
  int result = 0;
  for (std::size_t index = offset; index < offset + count; ++index)
    {
      instant_require(text[index] >= '0' && text[index] <= '9',
                      "timestamp has a nondecimal "
                        + std::string(component));
      result = result * 10 + (text[index] - '0');
    }
  return result;
}

inline std::string
format_utc(const std::chrono::sys_seconds value)
{
  const std::time_t time = std::chrono::system_clock::to_time_t(value);
  std::tm utc {};
  instant_require(gmtime_r(&time, &utc) != nullptr,
                  "failed to format generation timestamp");
  std::array<char, 32> buffer {};
  instant_require(std::strftime(buffer.data(), buffer.size(),
                                "%Y-%m-%dT%H:%M:%SZ", &utc) != 0,
                  "failed to serialize generation timestamp");
  return buffer.data();
}

inline instant
make_instant(const std::chrono::sys_seconds value)
{
  const double unix_seconds = static_cast<double>(
    value.time_since_epoch().count());
  return {value, format_utc(value),
          julian_unix_epoch + unix_seconds / seconds_per_day};
}

inline instant
parse_timestamp(const std::string_view timestamp)
{
  if (timestamp == "now" || timestamp == "process-start")
    return make_instant(std::chrono::floor<std::chrono::seconds>(
      std::chrono::system_clock::now()));

  instant_require(timestamp.size() == 20
                    && timestamp[4] == '-' && timestamp[7] == '-'
                    && timestamp[10] == 'T' && timestamp[13] == ':'
                    && timestamp[16] == ':' && timestamp[19] == 'Z',
                  "timestamp must be 'now', 'process-start', or "
                  "YYYY-MM-DDTHH:MM:SSZ");
  const int year = parse_decimal_component(timestamp, 0, 4, "year");
  const unsigned month = static_cast<unsigned>(
    parse_decimal_component(timestamp, 5, 2, "month"));
  const unsigned day = static_cast<unsigned>(
    parse_decimal_component(timestamp, 8, 2, "day"));
  const int hour = parse_decimal_component(timestamp, 11, 2, "hour");
  const int minute = parse_decimal_component(timestamp, 14, 2, "minute");
  const int second = parse_decimal_component(timestamp, 17, 2, "second");
  const std::chrono::year_month_day calendar {
    std::chrono::year {year}, std::chrono::month {month},
    std::chrono::day {day},
  };
  instant_require(calendar.ok(), "timestamp has an invalid calendar date");
  instant_require(hour >= 0 && hour <= 23
                    && minute >= 0 && minute <= 59
                    && second >= 0 && second <= 59,
                  "timestamp has an invalid clock time");
  return make_instant(
    std::chrono::sys_days {calendar} + std::chrono::hours {hour}
      + std::chrono::minutes {minute} + std::chrono::seconds {second});
}

inline instant
process_start_instant()
{
  if (const char* source_date_epoch = std::getenv("SOURCE_DATE_EPOCH");
      source_date_epoch != nullptr && source_date_epoch[0] != '\0')
    {
      const std::string_view text {source_date_epoch};
      std::int64_t seconds {};
      const auto [position, error] = std::from_chars(
        text.data(), text.data() + text.size(), seconds);
      instant_require(error == std::errc {}
                        && position == text.data() + text.size(),
                      "SOURCE_DATE_EPOCH must be an integer Unix timestamp");
      return make_instant(std::chrono::sys_seconds {
        std::chrono::seconds {seconds}});
    }
  return make_instant(std::chrono::floor<std::chrono::seconds>(
    std::chrono::system_clock::now()));
}

inline double
age_hours(const instant& reference, const instant& observation)
{
  return std::chrono::duration<double, std::ratio<3600>>(
    reference.value - observation.value).count();
}

} // namespace cart0freak0::generation_time

#endif // CART0FREAK0_GENERATION_INSTANT_H
