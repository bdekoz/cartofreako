// Render actual H3 cell boundaries into bounded, transparent data-layer tiles.
// Source sampling, data classification and AuthaGraph geometry use atlas code.
#include <cairo.h>
#include <map>
#include <memory>
#include <set>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>
#include "cloud-atmosphere-generation.h"
#include "anthropocene-temperature-generation.h"

namespace atm = cart0freak0::cloud_atmosphere_generation;
namespace temp = cart0freak0::anthropocene_temperature_generation;
namespace gen = cart0freak0::generation;
namespace rj = rapidjson;
namespace fs = std::filesystem;

struct tile
{
  std::string id;
  double x, y, width, height, ppu;
  cairo_surface_t* surface;
  cairo_t* cr;
  std::uint64_t visible_cells = 0;
  tile(const rj::Value& settings)
  : id(settings["id"].GetString()), x(settings["bounds"][0].GetDouble()),
    y(settings["bounds"][1].GetDouble()), width(settings["bounds"][2].GetDouble()),
    height(settings["bounds"][3].GetDouble()), ppu(settings["pixels_per_unit"].GetDouble())
  {
    atm::atmosphere_require(width > 0 && height > 0 && ppu > 0 && ppu <= 2000,
                            "Invalid data tile extent or resolution");
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32,
      static_cast<int>(std::ceil(width * ppu)), static_cast<int>(std::ceil(height * ppu)));
    cr = cairo_create(surface);
    atm::atmosphere_require(cairo_status(cr) == CAIRO_STATUS_SUCCESS, "Cannot allocate data tile");
    cairo_scale(cr, cairo_image_surface_get_width(surface) / width,
                    cairo_image_surface_get_height(surface) / height);
    cairo_translate(cr, -x, -y);
  }
  ~tile() { cairo_destroy(cr); cairo_surface_destroy(surface); }
  tile(const tile&) = delete;
  bool add(const svg::vrange& points, const double margin)
  {
    if (points.size() < 3) return false;
    double left = INFINITY, right = -INFINITY, top = INFINITY, bottom = -INFINITY;
    for (const auto& [px, py] : points)
      {
        atm::atmosphere_require(std::isfinite(px) && std::isfinite(py), "Nonfinite projected H3 vertex");
        left = std::min(left, px); right = std::max(right, px);
        top = std::min(top, py); bottom = std::max(bottom, py);
      }
    if (right + margin < x || left - margin > x + width
        || bottom + margin < y || top - margin > y + height) return false;
    cairo_move_to(cr, std::get<0>(points[0]), std::get<1>(points[0]));
    for (std::size_t i = 1; i < points.size(); ++i)
      cairo_line_to(cr, std::get<0>(points[i]), std::get<1>(points[i]));
    cairo_close_path(cr);
    return true;
  }
  void paint(const rj::Value& style, const double radiation_opacity = -1)
  {
    const auto& fill = style["fill"];
    const auto& stroke = style["stroke"];
    if (fill[3].GetDouble() > 0)
      {
        cairo_set_source_rgba(cr, fill[0].GetDouble(), fill[1].GetDouble(),
                             fill[2].GetDouble(), fill[3].GetDouble());
        cairo_fill_preserve(cr);
      }
    const double alpha = radiation_opacity < 0 ? stroke[3].GetDouble() : radiation_opacity;
    if (alpha > 0)
      {
        cairo_set_source_rgba(cr, stroke[0].GetDouble(), stroke[1].GetDouble(), stroke[2].GetDouble(), alpha);
        cairo_set_line_width(cr, style["width"].GetDouble());
        cairo_stroke(cr);
      }
    else cairo_new_path(cr);
    atm::atmosphere_require(cairo_status(cr) == CAIRO_STATUS_SUCCESS, "Cannot paint H3 tile");
  }
};

struct render_cell
{
  H3Index h3;
  double value;
  unsigned bin;
};

template<typename Writer>
void render_layer(const std::string& id, const std::vector<render_cell>& cells,
                  const rj::Document& settings, const fs::path& output,
                  const gen::projection_context& context, Writer& writer)
{
  std::vector<std::unique_ptr<tile>> tiles;
  for (const auto& view : settings["views"].GetArray()) tiles.push_back(std::make_unique<tile>(view));
  const bool radiation = id == "surface-shortwave-radiation";
  std::map<std::pair<unsigned, unsigned>, std::vector<H3Index>> buckets;
  std::map<unsigned, std::uint64_t> band_counts;
  double minimum = INFINITY, maximum = -INFINITY;
  for (const auto& cell : cells)
    {
      minimum = std::min(minimum, cell.value); maximum = std::max(maximum, cell.value);
      const unsigned band = radiation
        ? static_cast<unsigned>(std::floor(std::clamp(cell.value / 400.0, 0.0, 1.0) * 99 + 0.5)) : cell.bin;
      ++band_counts[band];
      // Match the source's deliberate omission of observed zero rain/cloud fraction.
      if ((id == "precipitation-rate" || id == "cloud-fraction") && cell.value <= 0) continue;
      buckets[{band, cell.bin}].push_back(cell.h3);
    }
  const auto& styles = settings["styles"][id.c_str()];
  std::uint64_t drawn = 0;
  for (const auto& [key, indices] : buckets)
    {
      const auto [band, bin] = key;
      const auto& style = styles[std::to_string(bin).c_str()];
      for (const auto cell : indices)
        {
          std::vector<bool> visible(tiles.size(), false);
          for (auto polygon : atm::h3_polygons(cell))
            for (const auto& segment : gen::project_path(context, std::move(polygon), true))
              for (std::size_t i = 0; i < tiles.size(); ++i)
                visible[i] = tiles[i]->add(segment, style["width"].GetDouble() * 2) || visible[i];
          for (std::size_t i = 0; i < tiles.size(); ++i)
            if (visible[i]) ++tiles[i]->visible_cells;
          ++drawn;
        }
      // One compound path per source bin/opacity band preserves the SVG paint
      // order and avoids repeatedly accumulating alpha on shared cell edges.
      for (auto& target : tiles) target->paint(style, radiation ? band / 99.0 : -1);
    }
  writer.StartObject();
  writer.Key("id"); writer.String(id.c_str());
  writer.Key("observed_cells"); writer.Uint64(cells.size());
  writer.Key("drawn_cells"); writer.Uint64(drawn);
  writer.Key("value_range"); writer.StartArray();
  if (!cells.empty()) { writer.Double(minimum); writer.Double(maximum); }
  writer.EndArray();
  writer.Key("band_counts"); writer.StartObject();
  for (auto [band, count] : band_counts) { writer.Key(std::to_string(band).c_str()); writer.Uint64(count); }
  writer.EndObject();
  writer.Key("tiles"); writer.StartArray();
  for (auto& target : tiles)
    {
      const auto file = target->id + "-" + id + ".png";
      atm::atmosphere_require(cairo_surface_write_to_png(target->surface, (output / file).c_str())
                              == CAIRO_STATUS_SUCCESS, "Cannot write H3 data tile");
      writer.StartObject();
      writer.Key("scope"); writer.String(target->id.c_str());
      writer.Key("file"); writer.String(file.c_str());
      writer.Key("visible_cells"); writer.Uint64(target->visible_cells);
      writer.Key("width_px"); writer.Int(cairo_image_surface_get_width(target->surface));
      writer.Key("height_px"); writer.Int(cairo_image_surface_get_height(target->surface));
      writer.EndObject();
    }
  writer.EndArray(); writer.EndObject();
  std::cout << "Rendered " << id << ": " << cells.size() << " observations\n" << std::flush;
}

int main(int argc, char** argv)
{
  try
    {
      if (argc != 6) throw std::invalid_argument("usage: render-setouchi-h3-cells atmosphere|temperature|ocean PROFILE DATA SETTINGS OUTPUT-DIR");
      const std::string subject = argv[1];
      const auto settings = atm::read_json_document(argv[4]);
      const fs::path output = argv[5]; fs::create_directories(output);
      const gen::projection_context context(gen::find_projection_spec("authagraph"), "setouchi-h3-trials");
      std::ofstream stream(output / "render.json");
      rj::OStreamWrapper wrapper(stream); rj::Writer<rj::OStreamWrapper> writer(wrapper);
      writer.StartObject(); writer.Key("subject"); writer.String(subject.c_str());
      writer.Key("projection"); writer.String("authagraph");
      writer.Key("h3_resolution");
      if (subject == "atmosphere")
        {
          const auto profile = atm::load_atmosphere_profile(argv[2]);
          const auto dataset = atm::load_atmosphere_dataset(argv[3], profile);
          writer.Uint(dataset.h3_resolution);
          writer.Key("feature_count"); writer.Uint64(dataset.cells.size());
          writer.Key("layers"); writer.StartArray();
          for (std::size_t i = 0; i < profile.layers.size(); ++i)
            {
              if (!profile.layers[i].enabled) continue;
              std::vector<render_cell> cells;
              for (const auto& cell : dataset.cells)
                if (cell.values[i]) cells.push_back({cell.h3, *cell.values[i], atm::value_bin(*cell.values[i], profile.layers[i]) + 1});
              render_layer(profile.layers[i].id, cells, settings, output, context, writer);
            }
          writer.EndArray();
        }
      else if (subject == "temperature")
        {
          const auto profile = temp::load_temperature_profile(argv[2]);
          const auto dataset = temp::load_temperature_dataset(argv[3], profile);
          writer.Uint(dataset.h3_resolution);
          writer.Key("feature_count"); writer.Uint64(dataset.cells.size());
          writer.Key("covered_cell_count"); writer.Uint64(dataset.covered_cell_count);
          writer.Key("layers"); writer.StartArray();
          for (int layer = 0; layer < 3; ++layer)
            {
              std::vector<render_cell> cells;
              const std::string id = layer == 0 ? "cpc-temperature-coverage"
                : layer == 1 ? "cpc-temperature-record-high-days" : "cpc-temperature-record-low-days";
              for (const auto& cell : dataset.cells)
                {
                  const auto value = layer == 0 ? (cell.tmax_valid_days || cell.tmin_valid_days)
                    : layer == 1 ? cell.record_high_days : cell.record_low_days;
                  if (value) cells.push_back({cell.h3, static_cast<double>(value), layer == 0 ? 0U
                    : layer == 1 ? temp::temperature_high_bin(value) + 1
                    : temp::temperature_bin(value, profile.low_scale_days) + 1});
                }
              render_layer(id, cells, settings, output, context, writer);
            }
          writer.EndArray();
        }
      else if (subject == "ocean")
        {
          const auto data = atm::read_json_document(argv[3]);
          atm::atmosphere_require(data["schema"].IsString()
            && std::string(data["schema"].GetString()) == "cartofreako-ocean-render-v1",
            "Invalid ocean render schema");
          writer.Uint(5);
          writer.Key("layers"); writer.StartArray();
          for (const auto& layer : data["layers"].GetArray())
            {
              const std::string id = layer["id"].GetString();
              atm::atmosphere_require(settings["styles"].HasMember(id.c_str()), "Missing ocean layer style");
              std::vector<render_cell> cells;
              std::set<H3Index> seen;
              for (const auto& item : layer["cells"].GetArray())
                {
                  const auto h3 = std::stoull(item[0].GetString(), nullptr, 16);
                  const auto value = item[1].GetDouble();
                  const auto bin = item[2].GetUint();
                  atm::atmosphere_require(isValidCell(h3) && getResolution(h3) == 5
                    && std::isfinite(value) && seen.insert(h3).second,
                    "Invalid or duplicate ocean cell");
                  atm::atmosphere_require(settings["styles"][id.c_str()].HasMember(std::to_string(bin).c_str()), "Missing ocean bin style");
                  cells.push_back({h3, value, bin});
                }
              render_layer(id, cells, settings, output, context, writer);
            }
          writer.EndArray();
        }
      else throw std::invalid_argument("Unsupported trial subject");
      writer.EndObject(); stream << '\n';
      atm::atmosphere_require(stream.good(), "Cannot finish render receipt");
      return 0;
    }
  catch (const std::exception& error)
    { std::cerr << "render-setouchi-h3-cells: " << error.what() << '\n'; return 1; }
}
