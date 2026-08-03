// alpha60 torrent carto geographic SVG routines -*- mode: C++ -*-

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

#ifndef a60_SVG_CARTO_GEO_H
#define a60_SVG_CARTO_GEO_H 1

#include <cinttypes>
#include <ctime>

#include <fstream>
#include <iomanip>
#include <thread>
#include <chrono>

#include "a60-json.h"
#include "a60-carto.h"
#include "a60-collection-json.h"
#include "a60-svg-collection.h"
#include "a60-telecom-infrastructure.h"


namespace a60 {

using svg::select;

/// Draw base cartography.
void
augment_carto_baseline(string odir, auto& dcarto, const string sname,
		       projection_base::raster_mode v = projection_base::filled)
{
  render_state rs;
  set_select(rs.visible_mode, select::cartography | select::vector);
  const string gname = sname.empty() ? dcarto.p.name : sname;
  const string fname("carto-baseline-" + gname);
  svg_element obj = make_map_base(odir + fname, rs, dcarto, v);
}


/// Base cartography with specific key points.
void
augment_carto_geo_specific(string odir, auto& dcarto, const string sname)
{
  // Center, North, South, East, West.
  a60::point_2t pcenter = dcarto.to_point_2d(0, 0);
  a60::point_2t pn = dcarto.to_point_2d(89.9, 0);
  a60::point_2t pn0 = dcarto.to_point_2d(80, 0);
  a60::point_2t ps = dcarto.to_point_2d(-89.9, 0);
  a60::point_2t ps0 = dcarto.to_point_2d(-80, 0);
  a60::point_2t pe = dcarto.to_point_2d(0, 179.9);
  a60::point_2t pe0 = dcarto.to_point_2d(0, 170);
  a60::point_2t pw = dcarto.to_point_2d(0, -179.9);
  a60::point_2t pw0 = dcarto.to_point_2d(0, -170);

  a60::point_2t pm2080 = dcarto.to_point_2d(-80, -20);

  a60::point_2t pm2019 = dcarto.to_point_2d(-20, -19);
  a60::point_2t pm2021 = dcarto.to_point_2d(-20, -21);
  a60::point_2t pm2023 = dcarto.to_point_2d(-20, -23);

  a60::point_2t pm5628 = dcarto.to_point_2d(-56, -19);
  a60::point_2t pm5629 = dcarto.to_point_2d(-56, -23);

  render_state rs;
  set_select(rs.visible_mode, select::cartography | select::vector);
  const string gname = sname.empty() ? dcarto.p.name : sname;
  const string fname("carto-test-points-" + gname);
  svg_element obj = make_map_base(odir + fname, rs, dcarto);

  group_element gbeg;
  gbeg.start_element("geo-specific-points");
  obj.add_element(gbeg);

  svg::style gstyl = svg::k::b_style;
  gstyl._M_fill_color = svg::color::gray50;
  auto c1 = make_circle(pcenter, gstyl, 50);
  auto c2 = make_circle({ 10, 0 }, gstyl, 15);
  auto c3 = make_circle({ 0, 10 }, gstyl, 15);
  auto c4 = make_circle({ 10, 10 }, gstyl, 15);
  obj.add_element(c1);
  obj.add_element(c2);
  obj.add_element(c3);
  obj.add_element(c4);

  svg::style styl = svg::k::b_style;
 auto c5 =  make_circle(pn, styl, 30);
 auto c6 =  make_circle(ps, styl, 30);
 auto c7 =  make_circle(pe, styl, 30);
 auto c8 =  make_circle(pw, styl, 30);
  obj.add_element(c5);
  obj.add_element(c6);
  obj.add_element(c7);
  obj.add_element(c8);

  gstyl._M_fill_color = svg::color::gray20;
  auto c9 =  make_circle(pn0, gstyl, 15);
  auto c10 = make_circle(ps0, gstyl, 15);
  auto c11 = make_circle(pe0, gstyl, 15);
  auto c12 = make_circle(pw0, gstyl, 15);
  obj.add_element(c9);
  obj.add_element(c10);
  obj.add_element(c11);
  obj.add_element(c12);

  gstyl._M_fill_color = svg::color::green;
  auto c13 = make_circle(pm2019, gstyl, 10);
  auto c14 = make_circle(pm2021, gstyl, 10);
  auto c15 = make_circle(pm2023, gstyl, 10);
  auto c16 = make_circle(pm2080, gstyl, 10);
  auto c17 = make_circle(pm5628, gstyl, 10);
  auto c18 = make_circle(pm5629, gstyl, 10);
  obj.add_element(c13);
  obj.add_element(c14);
  obj.add_element(c15);
  obj.add_element(c16);
  obj.add_element(c17);
  obj.add_element(c18);

  // Specific cities.
  vrange citylocations =
    {
      {40.7128, -74.0060},	// NYC
      {34.0549, -118.2426},	// LA
      {48.8575, 2.3514},	// Paris
      {-29.8587, 31.0218},	// Durban, South Africa
      {28.7041, 77.1025},	// Delhi
      {35.6895, 139.6917},	// Tokyo
      {-33.8688, 151.2093},	// Sydney
      {21.1444, -157.0226},	// Moloka'i
      {-23.5558, -46.6396},	// Sao Paulo
      {64.1470, -21.9408 },	// Reykjavik, Iceland
      {-18.1266, 178.4399},	// Suva, Fiji
      {-62.2001, 58.9642}	// Villa Las Estrellas, Antartica
    };

  strings citynames =
    {
      "NYC", "LA", "Paris", "Durban", "Delhi", "Tokyo", "Sydney",
      "Moloka'i", "Sao Paulo", "Reykjavik", "Suva", "Villa Las Estrellas"
    };

  gstyl._M_fill_color = svg::color::red;
  for (uint i = 0; i < citylocations.size(); i++)
    {
      const point_2t& p = citylocations[i];
      const string& name = citynames[i];
      auto [ lat, lng ] = p;
      point_2t pcart = dcarto.to_point_2d(lat, lng);
      auto c =  make_circle(pcart, gstyl, 20);
      obj.add_element(c);
      styled_text(obj, name, pcart, svg::k::apercu_typo);
    }

  group_element gend;
  gend.finish_element();
  obj.add_element(gend);
}

} // namespace a60

#endif
