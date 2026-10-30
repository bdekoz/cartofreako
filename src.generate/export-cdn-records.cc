// Source adaptation uses Alpha60's validated canonical-record loader unchanged.
// SPDX-License-Identifier: GPL-3.0-or-later
#include <a60-cdn-records.h>
#include <iostream>
using namespace a60::cdn;
int main(int argc, char** argv) {
  if (argc != 3) return 2;
  try {
    const auto config = read_json(argv[1]);
    const auto data = load_dataset(argv[1], config);
    fs::create_directories(argv[2]);
    std::ofstream out(fs::path(argv[2]) / "records.jsonl");
    for (const auto& r : data.records) {
      json::StringBuffer b; json::Writer<json::StringBuffer> w(b);
      w.StartObject();
      auto s=[&](const char* k,const std::string& v){w.Key(k);w.String(v.c_str(),v.size());};
      s("record_id",r.id);s("source_layer",r.source_layer);s("source_snapshot",r.snapshot);
      s("provider_label",r.provider);s("vendor_id",r.vendor_id);s("service",r.service);
      s("entity_type",r.entity_type);s("source_scope",r.source_scope);s("parent_record_id",r.parent_id);
      s("lifecycle_status",r.lifecycle);s("country_iso2",r.country_iso2);s("country_iso3",r.country_iso3);
      s("city",r.city);s("metro",r.metro);s("coordinate_method",r.coordinate_method);
      s("location_precision",r.precision);s("source_url",r.source_url);s("observation_date",r.observation_date);
      s("source_published_at",r.published_at);s("retrieved_at",r.retrieved_at);s("disposition",r.disposition);s("reason",r.reason);
      s("reference_basis",r.reference_basis);
      s("display_name",r.approximate?reference_name(r.reference):(r.city.empty()?r.metro:r.city));
      s("display_precision",r.approximate?r.reference.precision:r.precision);
      w.Key("approximate");w.Bool(r.approximate);w.Key("display_coordinates");
      if(r.plotted()){w.StartArray();w.Double(r.point.longitude);w.Double(r.point.latitude);w.EndArray();}else w.Null();
      w.Key("source_feature");w.RawValue(r.original_feature.data(),r.original_feature.size(),json::kObjectType);
      w.EndObject();out << b.GetString() << '\n';
    }
    std::ofstream refs(fs::path(argv[2]) / "locality-references.jsonl");
    for (const auto& r : data.references) {
      json::StringBuffer b; json::Writer<json::StringBuffer> w(b);w.StartObject();
      auto s=[&](const char* k,const std::string& v){w.Key(k);w.String(v.c_str(),v.size());};
      s("footprint_id",r.id);s("vendor_id",r.vendor_id);s("source_layer",r.source_layer);
      s("display_name",reference_name(r.reference));s("precision",r.precision);
      w.Key("independent_mark");w.Bool(r.draw);w.Key("display_coordinates");
      w.StartArray();w.Double(r.reference.point.longitude);w.Double(r.reference.point.latitude);w.EndArray();
      w.Key("canonical_reconciliation");w.RawValue(r.reconciliation.data(),r.reconciliation.size(),json::kObjectType);
      w.Key("source_feature");w.RawValue(r.original_feature.data(),r.original_feature.size(),json::kObjectType);
      w.EndObject();refs << b.GetString() << '\n';
    }
    if (!out || !refs) throw std::runtime_error("failed writing CDN ledgers");
    std::ofstream audit(fs::path(argv[2]) / "loader-audit.json");
    audit << "{\"canonical_records\":" << data.records.size() << ",\"source_coordinates\":" << data.sourced
      << ",\"derived_references\":" << data.derived << ",\"unplotted\":" << data.unplotted
      << ",\"locality_references\":" << data.references.size() << "}\n";
    std::cout << data.records.size() << " records; " << data.sourced << " source points; " << data.derived
      << " reference positions; " << data.unplotted << " unplotted\n";
  } catch (const std::exception& e) { std::cerr << e.what() << '\n';return 1; }
}
