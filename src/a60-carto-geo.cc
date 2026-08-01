// alpha60 torrent carto geographic checks -*- mode: C++ -*-

// alpha60
// bittorrent x scrape x data + analytics

// Copyright (c) 2016-2025, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#include "a60.h"
#include "a60-svg-carto-geo.h"
#include "a60-btiha-geojson.h"


using namespace a60;


string
usage()
{
  string s("usage: a60-carto-geo.exe arg1 arg2");
  s += a60::k::newline;
  return s;
}

void
print_geo_peer(geo::geo_peer& p)
{
  std::cout << "lat: " << std::get<geo::latitude>(p) << std::endl;
  std::cout << "long: " << std::get<geo::longitude>(p) << std::endl;
  std::cout << "country: " << std::get<geo::country>(p) << std::endl;
  std::cout << "region: " << std::get<geo::region>(p) << std::endl;
  std::cout << "city: " << std::get<geo::city>(p) << std::endl;
  std::cout << std::endl;
}


bool
pre_check_geoip_install()
{
  bool ret(false);

  if constexpr (a60::k::geolocation_state != geo::iplocation_mode::none)
    {
      // Emtpy meta peer representing Google DNS ip address only.
      string sgdns("8.8.8.8");
      geo::geo_peer pgoogle = geo::make_geo_peer(sgdns);
      geo::vgeo_peers peerstest;
      peerstest.push_back(pgoogle);

      // test 1
      geo::geo_peer pmmp1 = geo::make_geo_peer(sgdns);
      print_geo_peer(pmmp1);

      geo::geo_peer pmmp2 = geo::make_geo_peer(sgdns, false, true);
      print_geo_peer(pmmp2);

      /*
	ip: 114.84.162.223
	country: CHN
	lat: 31.0456
	long: 121.4
	city: 23
	region: Shanghai
      */
      string sxzh("114.84.162.223");
      geo::geo_peer pmmp3 = geo::make_geo_peer(sxzh);
      print_geo_peer(pmmp3);

      string sxipv6("::ffff:46.165.244.207");
      geo::geo_peer pmmp4 = geo::make_geo_peer(sxipv6);
      print_geo_peer(pmmp4);
    }

  return ret;
}


/// Augmentation for Network characteristics GeoJSON from swarm_features.
void
augment_swarm_features_geojson(const string geoj, const auto& cartog,
			       string odir = "./tmp/")
{
  using std::clog;
  using std::endl;
  using svg::select;
  const auto& a = cartog.f.frame_area;

  // Get name from input GeoJSON file's collection_key field.
  // NB: key is the stringified version of the H3 Hexagon id.
  rj::Document dom = deserialize_json_to_dom_object(geoj);
  string sname = to_lowercase_string(search_dom_for_string_field(dom, "id"));
  string sdstamp = search_dom_for_string_field(dom, "datestamp");

  // Deserialize geojson file into into swarm_features.
  umsfeatures gfeatures = a60::deserialize_swarm_features(geoj);
  if (gfeatures.empty())
    {
      string m("augment_swarm_features_geojson: failed, input has no GeoJSON Features.");
      m += a60::k::newline;
      m += geoj;
      m += a60::k::newline;
    }
  else
    clog << "augment_swarm_features_geojson:: found " << gfeatures.size() << endl;


  // Display min and max.
  const uint dmin = 1.5;
  const uint dmax = 150;

  // Find serializied Feature.field for sizing data range.
  using size_type = swarm_datum::size_type;
  auto lget_min_max_member = [&gfeatures](size_type swarm_datum::* mptr)
  {
    std::set<size_type> values;
    for (const auto& [key, swrmf] : gfeatures)
	values.insert(swrmf.downloaders.*mptr);
    std::tuple<size_type, size_type> ret { *values.begin(), *values.rbegin() };
    return ret;
  };

  const auto [ szmin, szmax ] = lget_min_max_member(&swarm_datum::size);
  const auto [ mzmin, mzmax ] = lget_min_max_member(&swarm_datum::mobile);
  const auto [ satmin, satmax ] = lget_min_max_member(&swarm_datum::satellite);
  const auto [ hzmin, hzmax ] = lget_min_max_member(&swarm_datum::hosting);
  const auto [ serzmin, serzmax ] = lget_min_max_member(&swarm_datum::service);


  // Start rendering.
  render_state& rs = get_render_state();
  const render_state rspre = rs;

  select vm = select::vector | select::cartography | select::text;
  set_select(rs.visible_mode, vm);

  // Make display groups for text annotations, fiber, mobile, and
  // satellite downloaders.  Doing it this way will allow data to show
  // up as separate layers in the svg.
  group_element gtxt;
  gtxt.start_element("text");
  group_element gfiber;
  gfiber.start_element("fiber");
  group_element gnet;
  gnet.start_element("network-characteristics");
  group_element gmobile;
  gmobile.start_element("mobile");
  group_element gsat;
  gsat.start_element("satellite"); // asama orange

  const color_qi klr_lps(31,71,136); // jp lapis
  const color_qi klr_mul(59,14,75); // jp mulberry
  const color_qi klr_kgr(0,148,16); // kgreen
  const color_qi klr_r(255,29,16); // kred
  const color_qi klr_cr(220,20,60); // kcrimson
  style fstyl { klr_lps, 0.2, color::white, 0.0, 0.0 };
  style mstyl { klr_kgr, 0.2, klr_kgr, 0.0, 0.3 };
  style satstyl { klr_cr, 0.95, color::white, 1.0, 0.2 };
  typography typo = svg::k::apercu_typo;

  for (const auto& [ key, swrmf ] : gfeatures)
    {
      // Extract lat/log location, transform to display location.
      const swarm_locus& loc(swrmf.coordinates);
      const swarm_datum& dls(swrmf.downloaders);
      const point_2t cp = cartog.to_point_2d(loc.point);

      // downloaders.size
      if (dls.size)
	{
	  uint fsz = scale_value_on_range(dls.size, szmin, szmax, dmin, dmax);

	  // Style small instances as opaque, large as transparent.
	  style dlstyl(fstyl);
	  if (dls.size < szmax * 0.05)
	    dlstyl._M_fill_opacity = 1.0;
	  auto cdl = make_circle(cp, dlstyl, fsz);
	  gfiber.add_element(cdl);
	}

      // network characteristics hosting, service.
      svg_element rsvg("wrapper", a, false);
      if (dls.hosting >= hzmax * .25)
	{
	  //const uint thismax = double(hzmax) / szmax;
	  const uint thismax = double(dmax) / 3;
	  uint hsz = scale_value_on_range(dls.hosting, hzmin, hzmax, dmin, thismax);
	  point_to_ring_halo(rsvg, cp, hsz, hsz * 0.25,
			     color::darkviolet, color::white);
	  gnet.add_element(rsvg);
	}
      if (dls.service >= serzmax* .25)
	{
	  //const uint thismax = double(serzmax)/ szmax;
	  const uint thismax = double(dmax) / 3;
	  uint sersz = scale_value_on_range(dls.service, serzmin, serzmax, dmin, thismax);
	  point_to_ring_halo(rsvg, cp, sersz, sersz * 0.25,
			     color::asamapink, color::white);
	  gnet.add_element(rsvg);
	}

      // mobile
      if (dls.mobile)
	{
	  //const uint thismax = double(mzmax) / szmax;
	  const uint thismax = double(dmax) / 3;
	  uint msz = scale_value_on_range(dls.mobile, mzmin, mzmax, 2, thismax);

	  // Style small instances as outline, large as transparent.
	  style dlstyl(mstyl);
	  if (dls.mobile < szmax * 0.05)
	    {
	      msz += dmin;
	      dlstyl._M_fill_opacity = 0;
	      dlstyl._M_stroke_opacity = 1;
	    }

	  auto mdl = make_circle(cp, mstyl, msz);
	  gmobile.add_element(mdl);
	}

      // satellite
      if (dls.satellite)
	{
	  //const uint thismax = double(satmax) / szmax;
	  const uint thismax = double(dmax) / 7.5;
	  uint ssz = scale_value_on_range(dls.satellite, satmin, satmax, 2, thismax);
	  auto sdl = make_path_polygon(cp, satstyl, ssz, 3);
	  gsat.add_element(sdl);
	}

      // text (iff top n% in size) 10-50% only seoul
      // or min_max_median
      if (dls.size >= szmax * .25)
	{
	  string label = loc.city.empty() ? loc.country_code : loc.city;
	  text_element t = style_text(label, cp, typo);
	  gtxt.add_element(t);
	}
    }

  gtxt.finish_element();
  gfiber.finish_element();
  gnet.finish_element();
  gmobile.finish_element();
  gsat.finish_element();


  const string vpstr(to_string(uint(a._M_width)) + "-x-" + to_string(uint(a._M_height)));
  const string fname(sname + "-carto-" + sdstamp + "-" + vpstr);
  svg_element obj = make_map_base(odir + fname, rs, cartog);
  obj.add_element(gfiber);
  obj.add_element(gmobile);
  obj.add_element(gnet);
  obj.add_element(gsat);
  obj.add_element(gtxt);

  rs = rspre;
}



int main(int argc, char* argv[])
{
  using namespace rapidjson;
  using namespace libtorrent;

  // Input file, output directory.
  string input1, input2, input3;
  if (argc > 1)
    input1 = argv[1];
  else
    {
      std::cerr << usage() << std::endl;
      return 1;
    }

  if (argc > 2)
    input2 = argv[2];
  if (argc > 3)
    input3 = argv[3];

  // Time point.
  auto now = time_point_as_string(std::chrono::system_clock::now(), true);

  // Output.
  string odir = io::get_output_directory("tmp");
  io::pre_check_output_directory(odir);

  // 1
  pre_check_geoip_install();


  //auto& ckcarto = ckwecarto_engc;
  //auto* ckcarto = ckh4starxcarto_engc;
  //auto& ckcarto = ckwecarto_44x22;
  //auto& ckcarto = ckmwecarto_44x22;
  //auto& ckcarto = ckogwecarto_44x22;

  // 2
  //augment_carto_geo_specific(odir, ckcarto, "geo-specific-points");

  // 3
  //augment_carto_composite(odir, ckcarto);
  //augment_carto_variations(odir, ckcarto);

  // 4 slices
  //augment_carto_slices(odir, ckh2carto_1080p, ckh2state);
  //augment_carto_slices(odir, ckh2carto_engc, ckh2state);

  //augment_carto_slices(odir, ckh4starxcarto_a5, ckh4state);
  //augment_carto_slices(odir, ckh4carto_engc, ckh4state);
  //augment_carto_slices(odir, ckh4starxcarto_engc, ckh4state);

  //augment_carto_slices(odir, ckh4carto_44x22, ckh4state);

  // 5
  //augment_swarm_features_geojson(input1, ckcarto, odir);

  return 0;
}
