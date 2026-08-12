#include <cassert>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

#include <rapidjson/document.h>
#include <rapidjson/istreamwrapper.h>

#include "cart0freak0-equal-earth.h"

namespace equal_earth = a60::carto::equal_earth;
namespace rj = rapidjson;

namespace {

double
longitude_distance(const double left, const double right)
{
  return std::abs(std::remainder(left - right, 360.0));
}

} // namespace

int
main(int argc, char** argv)
{
  if (argc != 2)
    throw std::runtime_error("usage: test-equal-earth-projection FIXTURE");
  std::ifstream stream(argv[1]);
  if (!stream)
    throw std::runtime_error(std::string("cannot read ") + argv[1]);
  rj::IStreamWrapper wrapper(stream);
  rj::Document document;
  document.ParseStream(wrapper);
  assert(!document.HasParseError() && document.IsObject());

  std::size_t count = 0;
  for (const rj::Value& layout : document["layouts"].GetArray())
    {
      const double central_meridian
        = layout["centralMeridianDegrees"].GetDouble();
      const equal_earth::projection projection(2054.5821300028537,
                                               central_meridian);
      assert(std::abs(projection.height() - 1000) < 1e-12);
      for (const rj::Value& fixture : layout["cases"].GetArray())
        {
          ++count;
          const rj::Value& source = fixture["geographic"];
          const equal_earth::geographic_coordinate geographic {
            source[0].GetDouble(), source[1].GetDouble(),
          };
          const equal_earth::point raw = equal_earth::forward_raw(
            equal_earth::relative_longitude_radians(
              geographic.longitude_degrees, central_meridian),
            geographic.latitude_degrees * equal_earth::radians_per_degree);
          const rj::Value& wanted_raw = fixture["expected"]["raw"];
          const double raw_tolerance
            = fixture["tolerances"]["raw"].GetDouble();
          assert(std::hypot(raw.x - wanted_raw[0].GetDouble(),
                            raw.y - wanted_raw[1].GetDouble())
                 <= raw_tolerance);

          const equal_earth::point page = projection.forward(geographic);
          const rj::Value& wanted_page
            = fixture["expected"]["normalizedPage"];
          const double page_tolerance
            = fixture["tolerances"]["normalized"].GetDouble();
          assert(std::hypot(page.x / projection.width()
                              - wanted_page[0].GetDouble(),
                            page.y / projection.height()
                              - wanted_page[1].GetDouble())
                 <= page_tolerance);

          const equal_earth::inverse_result reverse
            = projection.inverse(page);
          assert(reverse.status == equal_earth::inverse_status::unique);
          const double angular_tolerance
            = fixture["tolerances"]["angularDegrees"].GetDouble();
          assert(longitude_distance(reverse.coordinate.longitude_degrees,
                                    geographic.longitude_degrees)
                 <= angular_tolerance);
          assert(std::abs(reverse.coordinate.latitude_degrees
                          - geographic.latitude_degrees)
                 <= angular_tolerance);
          assert(reverse.forward_residual <= 1e-7);
        }
      assert(projection.inverse({-1, projection.height() / 2}).status
             == equal_earth::inverse_status::outside);
      assert(projection.inverse({projection.width() + 1,
                                  projection.height() / 2}).status
             == equal_earth::inverse_status::outside);
      assert(projection.inverse({0, 0}).status
             == equal_earth::inverse_status::outside);
      const equal_earth::inverse_result west
        = projection.inverse({0, projection.height() / 2});
      const equal_earth::inverse_result east
        = projection.inverse({projection.width(), projection.height() / 2});
      assert(west.status == equal_earth::inverse_status::unique);
      assert(east.status == equal_earth::inverse_status::unique);
      assert(longitude_distance(west.coordinate.longitude_degrees,
                                east.coordinate.longitude_degrees) < 1e-12);
      assert(west.forward_residual < 1e-7);
      assert(east.forward_residual < 1e-7);
    }
  assert(count == 30);
  std::cout << "C++ Equal Earth forward/reverse checks passed: "
            << count << " fixtures\n";
}
