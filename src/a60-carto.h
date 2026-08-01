// alpha60 cartography -*- mode: C++ -*-

// alpha60
// cartography

// Copyright (c) 2016-2022, 2025, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_H
#define a60_CARTOGRAPHY_H 1

#include <cmath>
#include <set>
#include <functional>
#include <iostream>
#include <mutex>
#include <condition_variable>
#include <shared_mutex>

#include "a60-io.h"
#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "a60-carto-projection-authagraph.h"
#include "a60-carto-projection-cahill-keyes.h"
#include "a60-carto-projection-myriahedral.h"
//#include "a60-carto-projection-cahill-keyes-butterfly.h"
//#include "a60-carto-projection-cahill-keyes-ckog.h"


/**
   Composed of the following elements:

   - projection (representation of Earth)
   - bounding frame
   - margin
   - neatline, if any (bounding edge of drawn information in frame)
   - symbology (legend, key, title, scale)

   - cartography (all the above)
   - slice, cartography with specified lat/long ranges and otional enlargement.

   - data
*/


/**
  Data Slice.

  Sub-sets and partitions of the collected data. Specific slices can
  be a geographic range, say longitudes from -175 to -30 (aka
  Americas), or by three-letter country code (aka BRA is Brazil).

  Country Ranges (ISO-3 Codes)

  USA
  BRA
  CAN

  Longitude Ranges

  USA -174.168 to 139.68
  BRA -72.783 to 0
  CAN -139.8 to 0

  Americas -175.0 to -30, no Iceland
  Asia and Oceania 60 to 180.0
*/


/// Cartography namespace.
namespace a60::carto {

/**
   Render Slices, Enlargement, & Tiling.

   Some (slice) renderings use more than one frame to complete the
   whole image.  This is called tiling, where the image is broken up
   in segments over a couple of frames, aka pages.

   1x == single || none || whole_earth
   1x all longitude values

   2x == duo (C-K) [landscape diptych engc]
   2x two logitude ranges
   1 = pacifica americas
   2 = afro eur asia

   [3,6]x == trio [three horizontal tiles, optionally north and south]
   1 = afro eur asia
   2 = americas
   3 = asia pacifica

   4x == quarto (C-K) [portrait 1,2,3,4 tiles engc]
   1 = pacifica america
   2 = americas
   3 = afro eur asia
   4 = asia pacifica
*/
enum class slice_mode
  {
    none,
    whole_earth,
    country_code,
    h_duo,
    h_duo_1, h_duo_2,
    h_trio,
    h_trio_1, h_trio_2, h_trio_3,
    h_quarto,
    h_quarto_1, h_quarto_2, h_quarto_3, h_quarto_4,
    v_duo,
    v_duo_north, v_duo_south,
    all
  };


/// Cartographic state type.
struct carto_state
{
  projection_mode	proj;
  slice_mode		hslyc;
  slice_mode		vslyc;

  carto_state(projection_mode p, slice_mode h, slice_mode v = slice_mode::none)
  : proj(p), hslyc(h), vslyc(v) { }

  bool
  is_h_slice() const
  {
    const bool b2all(hslyc == slice_mode::h_duo);
    const bool b2(hslyc == slice_mode::h_duo_1 || hslyc == slice_mode::h_duo_2);
    const bool b3all(hslyc == slice_mode::h_trio);
    const bool b31(hslyc == slice_mode::h_trio_1);
    const bool b32(hslyc == slice_mode::h_trio_2);
    const bool b33(hslyc == slice_mode::h_trio_3);
    const bool b3(b31 || b32 || b33);
    const bool b4all(hslyc == slice_mode::h_quarto);
    const bool b41(hslyc == slice_mode::h_quarto_1);
    const bool b42(hslyc == slice_mode::h_quarto_2);
    const bool b43(hslyc == slice_mode::h_quarto_3);
    const bool b44(hslyc == slice_mode::h_quarto_4);
    const bool b4(b41 || b42 || b43 || b44);
    return bool(b2all || b2 || b3all || b3 || b4all || b4);
  }

  bool
  is_v_slice() const
  {
    const bool vn(vslyc == slice_mode::v_duo_north);
    const bool vs(vslyc == slice_mode::v_duo_south);
    return bool(vslyc == slice_mode::v_duo || vn || vs);
  }
};


/// Standard cartography state, AuthaGraph.
const carto_state agwestate(authagraph, slice_mode::whole_earth);


/// Standard cartography states, Cahill-Keyes
const carto_state ckwestate(cahill_keyes, slice_mode::whole_earth);

const carto_state ckh2state(cahill_keyes, slice_mode::h_duo);
const carto_state ckh3state(cahill_keyes, slice_mode::h_trio);
const carto_state ckh3v2state(cahill_keyes, slice_mode::h_trio, slice_mode::v_duo);

const carto_state ckh4state(cahill_keyes, slice_mode::h_quarto);
const carto_state ckh4v2state(cahill_keyes, slice_mode::h_quarto, slice_mode::v_duo);


/**
   Cartography,
   meta object for all components of visual representation of a
   geosphere.

   Includes the cartographic projection, and the frame in which it
   will be placed. Together, these two items are called a
   cartographic plate, or, simply the "plate."

   Projections that span more than one plate are "tiled plates" or "tiles."
*/
template<typename _Proj>
struct cartography
{
  using projection = _Proj;

  frame			f;
  projection		p;

  // Offsets for horizontal and vertical tiles, used in slices and
  // larger displays.
  vd			h_tiles;
  vd			v_tiles;

  cartography(const frame& fin, const projection& pin, const bool cp = false)
  : f(fin), p(pin)
  {
    if (cp)
      f.center(p.pframe);
  }

  cartography(const frame& fin, const projection& pin,
	      const vd& htile, const vd& vtile)
  : f(fin), p(pin), h_tiles(htile), v_tiles(vtile)
  { }

  // Slices with offsets.
  cartography(const frame& fin, const projection& pin,
	      const double x, const double y)
  : f(fin.frame_area, x, y), p(pin)
  { }

  cartography(const cartography& other)
  : f(other.f), p(other.p), h_tiles(other.h_tiles), v_tiles(other.v_tiles)
  { }

  const frame&
  get_frame() const
  { return f; }

  const projection&
  get_projection() const
  { return p; }

  void
  set_frame(const frame& fin)
  { f = fin; }

  void
  set_frame_portrait(void)
  {
    if (f.width() > f.height())
      {
	auto oldw = f.width();
	auto oldh = f.height();
	f.width() = oldh;
	f.height() = oldw;
      }
  }

  void
  set_projection(const projection& pin)
  { p = pin; }

  void
  set(const cartography& crt)
  {
    f = crt.f;
    p = crt.p;
  }

  a60::point_2t
  to_point_2d(const double lt, const double lng) const
  {
    auto [ x, y ] = p.meridians_to_point_2d(lt, lng);

    // Position map in frame.
    x += f.moriginx;
    y += f.moriginy;

    return std::make_tuple(x, y);
  }

  a60::point_2t
  to_point_2d(const a60::point_2t& po) const
  {
    auto [ lt, lng ] = po;
    return to_point_2d(lt, lng);
  }

  /**
     Proceeding left to right from the leftmost edge of the projection:

     quad 1 == x [0, quartowidth)
     quad 2 == x [quartowidth, quartowidth * 2)
     quad 3 == x [quartowidth * 2, quartowidth * 3)
     quad 4 == x [quartowidth * 3, quartowidth * 4)

     Cahill-Keyes Butterfly has has 8 octants that have longitude ranges:
     (160-180 + -180 to -110), (-110, 0), (0, 70), (70, 160)

     Thus:
     "leftmost" is longitude 160
     "rightmost" is longitude 159
  */
  slice_mode
  point_to_x_quadrant(const point_2t po) const
  {
    const auto quartowidth = p.pframe.width() / 4;
    const auto xo = f.moriginx;
    auto [x, y] = po;

    slice_mode m = slice_mode::none;
    if (xo <= x && x < xo + quartowidth)
      m = slice_mode::h_quarto_1;
    if (xo + quartowidth <= x && x < xo + (quartowidth * 2))
      m = slice_mode::h_quarto_2;
    if (xo + (quartowidth * 2) <= x && x < xo + (quartowidth * 3))
      m = slice_mode::h_quarto_3;
    if (xo + (quartowidth * 3) <= x && x < xo + (quartowidth * 4))
      m = slice_mode::h_quarto_4;
    return m;
  }

  /// Top (h1) and bottom (h2) vertical.
  slice_mode
  point_to_y_half(const point_2t po) const
  {
    const auto halfy = p.pframe.height() / 2;
    const auto yo = f.moriginy;
    auto [x, y] = po;

    slice_mode m = slice_mode::none;
    if (yo <= y && y < yo + halfy)
      m = slice_mode::v_duo_north;
    else
      m = slice_mode::v_duo_south;
    return m;
  }
};


/// Standard cartography object, AuthaGraph A3 source plate.
const cartography<agproj> agwecarto_a3(pauthagraph_a3, ag_a3);


/// Standard cartography objects, Cahill-Keyes projection.

/// Frame == 1080p
const cartography<ckproj> ckwecarto_1080p(f1080p_090_h, ck_1x1080, true);
const cartography<ckproj> ckh2carto_1080p(f1080p_090_h, ck_2x1080,
					  tiles_ck_2x1080p_h,
					  tiles_ck_2x1080p_v);
const cartography<ckproj> ckh4carto_1080p(f1080p_090_v, ck96_2bisx);

/// Frame == ENGC
const cartography<ckproj> ckwecarto_engc(f22x17_096_h, ck_1xengc, true);
const cartography<ckproj> ckh2carto_engc(f22x17_096_h, ck_2xengc,
					 tiles_ck_2xengc_h,
					 tiles_ck_2xengc_v);
const cartography<ckproj> ckh3carto_engc(f22x17_096_h, ck_4xengc,
					tiles_ck_4x_h, tiles_ck_4x_v);
const cartography<ckproj> ckh4carto_engc(f17x22_096_v, ck96_2bisx,
					 tiles_ck_2bisx_h, tiles_ck_2bisx_v);
const cartography<ckproj> ckh4starxcarto_engc(f17x22_096_v, ck96_starx_engc,
					      tiles_ck_starx_engc_h,
					      tiles_ck_starx_engc_v);
const cartography<ckproj> ckh4starxcarto_a5(fa5_096_v, ck96_starx_a5,
					    tiles_ck_starx_a5_h,
					    tiles_ck_starx_a5_v);

const cartography<ckproj> ckwecarto_qa4(fqa4b_096_h, ck_1xengc, true);
const cartography<ckproj> ckh3carto_qa4(fqa4b_096_h, ck_4xengc,
					tiles_ck_4x_h, tiles_ck_4x_v);
const cartography<ckproj> ckh4carto_qa4v(fqa4b_096_v, ck96_2bisx,
					 tiles_ck_2bisx_h, tiles_ck_2bisx_v);
const cartography<ckproj> ckh4carto_qa4h(fqa4b_096_h, ck96_2bisx,
					tiles_ck_2bisx_h, tiles_ck_2bisx_v2);

/// Frame == 44
const cartography<ckproj> ckwecarto_44x22(f44x22h, ck_44x22, true);
const cartography<ckproj> ckh4carto_44x22(f22x44v, ck_44x22,
					  tiles_ck_4x44x22_h,
					  tiles_ck_4x44x22_v);
//const cartography<ckmproj> ckmwecarto_44x22(f44x22h, ckm_44x22, true);
//const cartography<ckogproj> ckogwecarto_44x22(f44x22h, ckog_44x22, true);


/// Slice base type
struct slice_base
{
  using srange = a60::point_2t;
  static constexpr srange	longr_all = std::make_tuple(-180.0, 180.0);

  /// Longitude ranges trio.
  static constexpr srange	longr_3_asiap = std::make_tuple(60.0, 180.0);
  static constexpr srange	longr_3_afroe = std::make_tuple(-29.99, 59.99);
  static constexpr srange	longr_3_amecs = std::make_tuple(-175.0, -30.0);

  /// Longitude ranges quadro.
  /// Horizontal slices from Cahill-Keyes octets
  /// (using adjacent north/south pairs of octets)
  /// NB: For this projection, want both 160 to 180 and -110 to -180
  static constexpr srange	longr_4_1 = std::make_tuple(70.0, 159.99);
  static constexpr srange	longr_4_2 = std::make_tuple(-20, 69.99);
  static constexpr srange	longr_4_3 = std::make_tuple(-110.0, -19.99);
  static constexpr srange	longr_4_4 = std::make_tuple(160.0, -110.01);
  static constexpr srange	longr_4_4a = std::make_tuple(160.0, 180.0);
  static constexpr srange	longr_4_4b = std::make_tuple(-180, -110.01);

  /// Longitude ranges duo, idealized and including overlap.

  // Without overlap: longr_4_4a + longr_4_4b + longr_4_3
  static constexpr srange	longr_2_1 = std::make_tuple(-20, 159.99);

  // Without overlap: longr_4_2 + longr_4_1
  static constexpr srange	longr_2_2 = std::make_tuple(160, -19.99);


  /// Latitude ranges.
  static constexpr srange	latr_all = std::make_tuple(90.0, -90.0);

  static constexpr srange	latr_n = std::make_tuple(90.0, 0.0);
  static constexpr srange	latr_s = std::make_tuple(0.0, -90.0);
};


/// Slice type
template<typename _Proj>
struct slice: slice_base
{
  using projection = _Proj;
  using carto_type =  cartography<projection>;

  string			name;

  /// Longitude, (-180 to 180)
  /// NB: Each range in longr should not overlap.
  vrange			longr;

  /// Latitude
  /// (90 to 0)		== Northern Hemisphere
  /// (0 to -90)	== Southern Hemisphere
  /// Each range in longr should not overlap.
  vrange			latr;

  carto_type			plate;

  slice(const string nm, const srange lng1, const srange lt1,
	const carto_type& crto)
    : name(nm), longr({lng1}), latr({lt1}), plate(crto)
  { }

  slice(const slice&) = default;
};


/// Vector of slice objects.
template<typename _Proj>
using slices = std::vector<slice<_Proj>>;

using ckproj_slices = std::vector<slice<ckproj>>;


void
get_slices_quatro(ckproj_slices& s, const cartography<ckproj>& carto,
		  const carto_state cstate, const string prefix = "")
{
  using slice_type = ckproj_slices::value_type;

  if (carto.h_tiles.empty() && carto.v_tiles.empty())
    throw std::runtime_error("get_slices_quatro:: no vertical or horizontal");

  const vd& xoff = carto.h_tiles;
  const double yoff = carto.v_tiles[0];
  const slice_mode hslyc = cstate.hslyc;

  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_1)
    {
      const cartography carto1(carto.f, carto.p, xoff[0], yoff);
      slice_type s1(prefix + "Pacifica America",
		    slice_base::longr_4_4a, slice_base::latr_all, carto1);
      s1.longr.push_back(slice_base::longr_4_4b);
      s.push_back(s1);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_2)
    {
      const cartography carto2(carto.f, carto.p, xoff[1], yoff);
      slice s2(prefix + "Americas",
	       slice_base::longr_4_3, slice_base::latr_all, carto2);
      s.push_back(s2);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_3)
    {
      const cartography carto3(carto.f, carto.p, xoff[2], yoff);
      slice s3(prefix + "Afro Eur Asia",
	       slice_base::longr_4_2, slice_base::latr_all, carto3);
      s.push_back(s3);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_4)
    {
      const cartography carto4(carto.f, carto.p, xoff[3], yoff);
      slice s4(prefix + "Asia Pacifica",
	       slice_base::longr_4_1, slice_base::latr_all, carto4);
      s.push_back(s4);
    }
}


// Bottom slice of CK, if be.
void
get_slices_quatro_v_s(ckproj_slices& s, const cartography<ckproj>& carto,
		      const carto_state cstate)
{
  using slice_type = ckproj_slices::value_type;

  const string sou("South");
  const vd& xoff = carto.h_tiles;
  const double yoff = carto.v_tiles[1];
  const slice_mode hslyc = cstate.hslyc;

  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_1)
    {
      frame f1b(carto.f, xoff[0], yoff);
      const cartography carto1(f1b, carto.p, f1b.moriginx, f1b.moriginy);
      slice_type s1(sou + k::space + "Pacifica Americas",
		    slice_base::longr_4_4a, slice_base::latr_all, carto1);
      s1.longr.push_back(slice_base::longr_4_4b);
      s.push_back(s1);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_2)
    {
      frame f2b(carto.f, xoff[1], yoff);
      const cartography carto2(f2b, carto.p, f2b.moriginx, f2b.moriginy);
      slice s2(sou + k::space + "Americas",
	       slice_base::longr_4_3, slice_base::latr_all, carto2);
      s.push_back(s2);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_3)
    {
      frame f3b(carto.f, xoff[2], yoff);
      const cartography carto3(f3b, carto.p, f3b.moriginx, f3b.moriginy);
      slice s3(sou + k::space + "Afro Eur Asia",
	       slice_base::longr_4_2, slice_base::latr_all, carto3);
      s.push_back(s3);
    }
  if (hslyc == slice_mode::h_quarto || hslyc == slice_mode::h_quarto_4)
    {
      frame f4b(carto.f, xoff[3], yoff);
      const cartography carto4(f4b, carto.p, f4b.moriginx, f4b.moriginy);
      slice s4(sou + k::space + "Asia Pacifica",
	       slice_base::longr_4_1, slice_base::latr_all, carto4);
      s.push_back(s4);
    }
}


/// Also fpod_iso, fpod_usa sizes.
template<typename _Proj>
void
get_slices_trio(slices<_Proj>& s, const cartography<_Proj>& carto,
		const carto_state cstate, const string prefix = "")
{
  using slice_type = typename slices<_Proj>::value_type;

  const vd& xoff = carto.h_tiles;
  const double yoff = carto.v_tiles[0];
  const slice_mode hslyc = cstate.hslyc;

  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_1)
    {
      const cartography carto3(carto.f, carto.p, xoff[2], yoff);
      slice_type s3(prefix + "Afro Eur Asia",
		    slice_base::longr_3_afroe, slice_base::latr_all, carto3);
      s.push_back(s3);
    }
  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_2)
    {
      const cartography carto2(carto.f, carto.p, xoff[1], yoff);
      slice_type s2(prefix + "Americas",
		    slice_base::longr_3_amecs, slice_base::latr_all, carto2);
      s.push_back(s2);
    }
  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_3)
    {
      const cartography carto1(carto.f, carto.p, xoff[0], yoff);
      slice_type s1(prefix + "Asia Pacifica",
		    slice_base::longr_3_asiap, slice_base::latr_all, carto1);
      s.push_back(s1);
    }
}


template<typename _Proj>
void
get_slices_trio_v_s(slices<_Proj>& s, const cartography<_Proj>& carto,
		    const carto_state cstate)
{
  using slice_type = typename slices<_Proj>::value_type;

  const string sou("South");
  const vd& xoff = carto.h_tiles;
  const double yoff = carto.v_tiles[0];
  const slice_mode hslyc = cstate.hslyc;

  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_1)
    {
      frame f3a(carto.f, xoff[2], yoff);
      frame f3b = f3a.bottom_tile_frame();
      const cartography carto3(f3b, carto.p, f3b.moriginx, f3b.moriginy);
      slice_type s3(sou + k::space + "Afro Eur Asia",
		    slice_base::longr_3_afroe, slice_base::latr_s, carto3);
      s.push_back(s3);
    }
  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_2)
    {
      frame f2a(carto.f, xoff[1], yoff);
      frame f2b = f2a.bottom_tile_frame();
      const cartography carto2(f2b, carto.p, f2b.moriginx, f2b.moriginy);
      slice_type s2(sou + k::space + "Americas",
		    slice_base::longr_3_amecs, slice_base::latr_s, carto2);
      s.push_back(s2);
    }
  if (hslyc == slice_mode::h_trio || hslyc == slice_mode::h_trio_3)
    {
      frame f1a(carto.f, xoff[0], yoff);
      frame f1b = f1a.bottom_tile_frame();
      const cartography carto1(f1b, carto.p, f1b.moriginx, f1b.moriginy);
      slice_type s1(sou + k::space + "Asia Pacifica",
		    slice_base::longr_3_asiap, slice_base::latr_s, carto1);
      s.push_back(s1);
    }
}


void
get_slices_duo(ckproj_slices& s, const cartography<ckproj>& carto,
	       const carto_state cstate, const string prefix = "")
{
  using slice_type = ckproj_slices::value_type;

  const double yoff = carto.v_tiles[0];
  const vd& xoff = carto.h_tiles;
  const slice_mode hslyc = cstate.hslyc;

  // Use full longitude ranges for diptychs that bleed into each other.
  if (hslyc == slice_mode::h_duo || hslyc == slice_mode::h_duo_1)
    {
      const cartography carto1(carto.f, carto.p, xoff[0], yoff);
      slice_type s1(prefix + "Pacifica Americas",
		    slice_base::longr_4_4a, slice_base::latr_all, carto1);
      s1.longr.push_back(slice_base::longr_4_4b);
      s1.longr.push_back(slice_base::longr_4_3);
      s.push_back(s1);
    }
  if (hslyc == slice_mode::h_duo || hslyc == slice_mode::h_duo_2)
    {
      const cartography carto2(carto.f, carto.p, xoff[1], yoff);
      slice s2(prefix + "Afro Eur Asia",
	       slice_base::longr_4_2, slice_base::latr_all, carto2);
      s2.longr.push_back(slice_base::longr_4_1);
      s.push_back(s2);
    }
}


/// Per-country slices.
template<typename _Proj>
void
get_slices_by_country(slices<_Proj>& s, cartography<_Proj> carto,
		      const strings& countrynames = segment_by_country())
{
  using slice_type = typename slices<_Proj>::value_type;
  for (const string& n : countrynames)
    {
      std::cout << "slice by country: " << n << std::endl;
      slice_type sc(n, slice_base::longr_all, slice_base::latr_all, carto);
      s.push_back(sc);
    }
}


/// Get set of all slices.
template<typename _Proj>
slices<_Proj>
get_slices(const cartography<_Proj>& carto, const carto_state cstate);


/// Cahill-Keyes slices.
template<>
slices<ckproj>
get_slices(const cartography<ckproj>& carto, const carto_state cstate)
{
  slices<ckproj> s;
  const slice_mode hslyc = cstate.hslyc;
  const slice_mode vslyc = cstate.vslyc;

  const bool pv(vslyc == slice_mode::all || vslyc == slice_mode::v_duo);

  /// Quattro
  const bool p41(hslyc == slice_mode::h_quarto_1);
  const bool p42(hslyc == slice_mode::h_quarto_2);
  const bool p43(hslyc == slice_mode::h_quarto_3);
  const bool p44(hslyc == slice_mode::h_quarto_4);
  const bool all4p(hslyc == slice_mode::h_quarto);
  if (p41 || p42 || p43 || p44 || all4p)
    {
      // No vertical slice.
      if (vslyc == slice_mode::none)
	get_slices_quatro(s, carto, cstate);

      // Two vertical slices: north, south, each a landscape plate.
      if (pv || vslyc == slice_mode::v_duo_north)
	get_slices_quatro(s, carto, cstate, "North ");
      if (pv || vslyc == slice_mode::v_duo_south)
	get_slices_quatro_v_s(s, carto, cstate);
    }

  /// Trio
  const bool p31(hslyc == slice_mode::h_trio_1);
  const bool p32(hslyc == slice_mode::h_trio_2);
  const bool p33(hslyc == slice_mode::h_trio_3);
  const bool all3p(hslyc == slice_mode::h_trio);
  if (p31 || p32 || p33 || all3p)
    {
      // No vertical slice, plate is the size of 2 landscape plates.
      if (vslyc == slice_mode::none)
	{
	  frame fdoublev(carto.f);
	  fdoublev.height() *= 2;
	  auto cartodoublev(carto);
	  cartodoublev.f = fdoublev;
	  get_slices_trio(s, cartodoublev, cstate);
	}

      // Two vertical slices: north, south, each a landscape plate.
      if (pv || vslyc == slice_mode::v_duo_north)
	get_slices_trio(s, carto, cstate, "North ");
      if (pv || vslyc == slice_mode::v_duo_south)
	get_slices_trio_v_s(s, carto, cstate);
    }

  /// Duo
  const bool p21(hslyc == slice_mode::h_duo_1);
  const bool p22(hslyc == slice_mode::h_duo_2);
  const bool all2p(hslyc == slice_mode::h_duo);
  if (p21 || p22 || all2p)
    {
      // No vertical slice.
      if (vslyc == slice_mode::none)
	get_slices_duo(s, carto, cstate);
      else
	{
	  string m("get_slices:: h duo does not have a vertical slice");
	  throw std::runtime_error(m);
	}
    }

  if (hslyc == slice_mode::country_code)
    get_slices_by_country(s, carto);
  return s;
}


/// Cahill-Keyes Butterfly slices.
#if 0
template<>
slices<ckmproj>
get_slices(const cartography<ckmproj>&, const carto_state)
{
  // No existing slices on this projection.
  slices<ckmproj> s;
  return s;
}
#endif

} // namespace carto

#endif
