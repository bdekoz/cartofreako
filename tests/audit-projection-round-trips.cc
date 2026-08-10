#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "cart0freak0-projection-runtime.h"

namespace runtime = cart0freak0::projection_runtime;

namespace {

constexpr double pi = 3.141592653589793238462643383279502884;

struct audit_result
{
  std::string id;
  double frame_width = 0;
  double frame_height = 0;
  std::size_t samples = 0;
  std::size_t unique = 0;
  std::size_t cut = 0;
  std::size_t ambiguous = 0;
  std::size_t failures = 0;
  std::size_t boundary_candidates = 0;
  std::vector<double> angular_errors;
  std::vector<double> longitude_errors;
  std::vector<double> latitude_errors;
  std::vector<double> residuals;
  runtime::geographic_coordinate worst_source {0, 0};
  double worst_angular_error = -1;
};

double
longitude_error(const double left, const double right)
{ return std::abs(std::remainder(left - right, 360.0)); }

double
angular_error(const runtime::geographic_coordinate left,
              const runtime::geographic_coordinate right)
{
  const double left_latitude = left.latitude_degrees * pi / 180;
  const double right_latitude = right.latitude_degrees * pi / 180;
  const double delta_latitude = right_latitude - left_latitude;
  const double delta_longitude
    = std::remainder(right.longitude_degrees - left.longitude_degrees, 360.0)
        * pi / 180;
  const double haversine
    = std::sin(delta_latitude / 2) * std::sin(delta_latitude / 2)
      + std::cos(left_latitude) * std::cos(right_latitude)
          * std::sin(delta_longitude / 2) * std::sin(delta_longitude / 2);
  return 2 * std::asin(std::sqrt(std::clamp(haversine, 0.0, 1.0)))
         * 180 / pi;
}

double
percentile(std::vector<double> values, const double fraction)
{
  if (values.empty())
    return std::numeric_limits<double>::quiet_NaN();
  std::sort(values.begin(), values.end());
  const double position = fraction * static_cast<double>(values.size() - 1);
  const std::size_t below = static_cast<std::size_t>(std::floor(position));
  const std::size_t above = static_cast<std::size_t>(std::ceil(position));
  const double weight = position - static_cast<double>(below);
  return values[below] * (1 - weight) + values[above] * weight;
}

double
maximum(const std::vector<double>& values)
{
  return values.empty() ? std::numeric_limits<double>::quiet_NaN()
                        : *std::max_element(values.begin(), values.end());
}

audit_result
audit(const std::string_view id, const double width)
{
  const runtime::projection_spec& spec = runtime::find_projection_spec(id);
  const double height = width / (spec.width / spec.height);
  const runtime::projection_context projection(
    spec, a60::carto::frame {width, height});
  audit_result result;
  result.id = id;
  result.frame_width = width;
  result.frame_height = height;

  // Half-step offsets avoid making this ordinary-interior campaign a seam
  // campaign. Exact cuts, poles, faces, and vertices remain covered by the
  // focused forward/reverse acceptance test.
  for (double latitude = -87.5; latitude <= 87.5; latitude += 5)
    for (double longitude = -177.5; longitude <= 177.5; longitude += 5)
      {
        ++result.samples;
        const runtime::geographic_coordinate source {longitude, latitude};
        const runtime::forward_result forward = runtime::forward(projection, source);
        runtime::inverse_options options;
        options.native_cell = forward.native_cell;
        options.component = forward.component;
        const runtime::inverse_result inverse
          = runtime::inverse(projection, forward.point, options);
        if (inverse.status == runtime::inverse_status::unique)
          ++result.unique;
        else if (inverse.status == runtime::inverse_status::cut)
          ++result.cut;
        else if (inverse.status == runtime::inverse_status::ambiguous)
          ++result.ambiguous;

        if (inverse.candidates.size() != 1)
          {
            ++result.failures;
            continue;
          }
        const runtime::inverse_candidate& candidate = inverse.candidates.front();
        if (candidate.native_cell != forward.native_cell
            || candidate.component != forward.component)
          {
            ++result.failures;
            continue;
          }
        result.boundary_candidates += candidate.boundary ? 1 : 0;
        const double lon_error = longitude_error(
          candidate.point.longitude_degrees, source.longitude_degrees);
        const double lat_error = std::abs(
          candidate.point.latitude_degrees - source.latitude_degrees);
        const double sphere_error = angular_error(candidate.point, source);
        result.longitude_errors.push_back(lon_error);
        result.latitude_errors.push_back(lat_error);
        result.angular_errors.push_back(sphere_error);
        result.residuals.push_back(candidate.forward_residual);
        if (sphere_error > result.worst_angular_error)
          {
            result.worst_angular_error = sphere_error;
            result.worst_source = source;
          }
      }
  return result;
}

void
write_result(std::ostream& output, const audit_result& result)
{
  output << "    {\n"
         << "      \"projection\": \"" << result.id << "\",\n"
         << "      \"frame\": {\"width\": " << result.frame_width
         << ", \"height\": " << result.frame_height << "},\n"
         << "      \"samples\": " << result.samples << ",\n"
         << "      \"statusCounts\": {\"unique\": " << result.unique
         << ", \"cut\": " << result.cut
         << ", \"ambiguous\": " << result.ambiguous
         << ", \"failures\": " << result.failures << "},\n"
         << "      \"boundaryCandidates\": " << result.boundary_candidates << ",\n"
         << "      \"angularErrorDegrees\": {\"p50\": "
         << percentile(result.angular_errors, 0.50)
         << ", \"p95\": " << percentile(result.angular_errors, 0.95)
         << ", \"p99\": " << percentile(result.angular_errors, 0.99)
         << ", \"max\": " << maximum(result.angular_errors) << "},\n"
         << "      \"longitudeErrorDegreesMax\": "
         << maximum(result.longitude_errors) << ",\n"
         << "      \"latitudeErrorDegreesMax\": "
         << maximum(result.latitude_errors) << ",\n"
         << "      \"forwardResidualPixels\": {\"p50\": "
         << percentile(result.residuals, 0.50)
         << ", \"p95\": " << percentile(result.residuals, 0.95)
         << ", \"p99\": " << percentile(result.residuals, 0.99)
         << ", \"max\": " << maximum(result.residuals) << "},\n"
         << "      \"worstAngularSource\": {\"longitude\": "
         << result.worst_source.longitude_degrees
         << ", \"latitude\": " << result.worst_source.latitude_degrees << "}\n"
         << "    }";
}

} // namespace

int
main(int argc, char** argv)
{
  if (argc > 2)
    throw std::invalid_argument(
      "usage: audit-projection-round-trips [OUTPUT.json]");
  std::ofstream file;
  std::ostream* output = &std::cout;
  if (argc == 2)
    {
      file.open(argv[1]);
      if (!file)
        throw std::runtime_error("could not open output file");
      output = &file;
    }

  constexpr std::array ids {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  constexpr std::array widths {44.0, 1920.0, 13200.0};
  std::vector<audit_result> results;
  for (const std::string_view id : ids)
    for (const double width : widths)
      results.push_back(audit(id, width));

  *output << std::setprecision(17)
          << "{\n"
          << "  \"schema\": \"cartofreako-projection-round-trip-audit-v1\",\n"
          << "  \"runtimeApi\": " << runtime::api_version << ",\n"
          << "  \"geometryAbi\": " << runtime::abi_version << ",\n"
          << "  \"method\": {\"longitudeStart\": -177.5, "
             "\"latitudeStart\": -87.5, \"stepDegrees\": 5, "
             "\"samplesPerProjectionFrame\": 2592, "
             "\"qualification\": \"forward nativeCell and component\"},\n"
          << "  \"results\": [\n";
  for (std::size_t index = 0; index < results.size(); ++index)
    {
      write_result(*output, results[index]);
      *output << (index + 1 == results.size() ? "\n" : ",\n");
    }
  *output << "  ]\n}\n";

  for (const audit_result& result : results)
    if (result.failures != 0 || result.angular_errors.size() != result.samples)
      return 1;
  return 0;
}
