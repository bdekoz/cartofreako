// Fuller cross-repository integration. SPDX-License-Identifier: GPL-3.0-or-later
#ifndef CARTOFREAKO_FULLER_SWARM_ANALYSIS_H
#define CARTOFREAKO_FULLER_SWARM_ANALYSIS_H 1
#include "cart0freak0-projection-runtime.h"
#include "izzi-swarm-paired.h"
#include <h3/h3api.h>
#include <charconv>
#include <map>

namespace cart0freak0::fuller {
inline H3Index cell(const std::string& id)
{
  H3Index value=0;
  const bool decimal=id.find_first_not_of("0123456789")==std::string::npos;
  const auto parsed=std::from_chars(id.data(),id.data()+id.size(),value,decimal?10:16);
  if(parsed.ec!=std::errc{} || parsed.ptr!=id.data()+id.size() || !isValidCell(value))
    throw std::invalid_argument("invalid H3: "+id);
  return value;
}
struct parent_summary
{
  std::string id;
  std::vector<std::string> members;
  std::array<std::vector<std::uint64_t>,2> known, coverage;
};
inline std::vector<parent_summary> aggregate(const svg::paired_swarm_dataset& data, int resolution)
{
  std::map<H3Index,parent_summary> groups;
  for(const auto& record:data.records)
    {
      H3Index parent=0;
      const auto h=cell(record.id);
      if(std::to_string(getResolution(h))!=data.resolution
         || cellToParent(h,resolution,&parent)!=E_SUCCESS)
        throw std::invalid_argument("incompatible H3 aggregation resolution");
      auto& g=groups[parent];
      if(g.id.empty())
        {
          g.id=std::to_string(parent);
          for(int r=0;r<2;++r) {g.known[r].resize(data.metrics.size());g.coverage[r].resize(data.metrics.size());}
        }
      g.members.push_back(record.id);
      for(int r=0;r<2;++r) for(std::size_t m=0;m<data.metrics.size();++m)
        if(const auto v=record.roles[r].counts[m])
          {
            if(*v>std::numeric_limits<std::uint64_t>::max()-g.known[r][m])
              throw std::overflow_error("aggregate count overflow");
            g.known[r][m]+=*v; ++g.coverage[r][m];
          }
    }
  std::vector<parent_summary> out;
  for(auto& [id,g]:groups) {std::sort(g.members.begin(),g.members.end());out.push_back(std::move(g));}
  return out;
}

struct service_result { long double demand_gb, capacity_gb, delivered_gb, loss_gb, shortfall_gb; };
/// Hypothetical global digital provision, not inferred physical network topology.
inline service_result service_scenario(long double demand, long double days,
                                      long double gb_per_day, long double loss_fraction)
{
  if(!std::isfinite(demand)||!std::isfinite(days)||!std::isfinite(gb_per_day)
     ||!std::isfinite(loss_fraction)||demand<0||days<=0||gb_per_day<0
     ||loss_fraction<0||loss_fraction>=1)
    throw std::invalid_argument("invalid service scenario units/parameters");
  const auto capacity=days*gb_per_day;
  if(!std::isfinite(capacity)) throw std::overflow_error("scenario capacity overflow");
  const auto sent=std::min(capacity,demand/(1-loss_fraction));
  const auto loss=sent*loss_fraction, delivered=sent-loss;
  return {demand,capacity,delivered,loss,std::max(0.0L,demand-delivered)};
}
} // namespace cart0freak0::fuller
#endif
