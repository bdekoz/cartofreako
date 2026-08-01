// alpha60 cartography projection Cahill-Keyes -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2018-2025, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_PROJECTION_CK_H
#define a60_CARTOGRAPHY_PROJECTION_CK_H 1


namespace a60::carto {

/**
   Cahill-Keyes projection.

   https://en.wikipedia.org/wiki/Gene_Keyes
   http://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-&-coastline.html
   https://gist.github.com/espinielli/4259835
   https://observablehq.com/@fil/cahill-keyes-projection
*/
struct ckproj : public projection_base, public projection_api
{
  ckproj(const projection_base d) : projection_base(d) { }

  ckproj(const ckproj&) = default;

  string
  image_filename(const raster_mode v) const
  {
    const string cartodata = "visionscarto-map";
    auto& rtr = io::get_run_time_resources();
    string ret(io::end_path(rtr.data) + cartodata + "/" + name);
    if (v == outline)
      ret += "-outline";
    if (v == inverse)
      ret += "-inverse";
    if (v == raster_mode(outline | inverse))
      ret += "-outline-inverse";
    if (v == grid)
      ret += "-grid";
    if (v == glitch)
      ret += "-gitch";
    return ret + ".png";
  }

  /// Use nodejs to run D3 projection via d3-geo-polygon
  a60::point_2t
  meridians_to_point_2d_via_js(const double lt, const double lng) const
  {
    const string ofname("./js-output.txt");
    const string script("a60-carto-projection-cahill-keyes.js");
    const auto& rtr = io::get_run_time_resources();

    // Call script + args, pipe to tmp file
    std::ostringstream cli;
    cli << "node";
    cli << k::space;
    cli << "--experimental-modules"; // loads modules
    cli << k::space;
    cli << rtr.prefix << "/src/" << script;
    cli << k::space;
    cli << pframe.height() / 2;
    cli << k::space;
    cli << lng;
    cli << k::space;
    cli << lt;
    cli << k::space;
    cli << ">> " << ofname;

    int status = system(cli.str().c_str());
    if (status == -1)
      {
	std::ostringstream oss;
	oss << "system call failed with status:" << status << std::endl;
	oss << cli.str() << std::endl;
	throw std::runtime_error(oss.str());
      }

    double ckx(0);
    double cky(0);
    std::ifstream ifs(ofname, std::ios::in);
    if (!ifs.good())
      {
	std::ostringstream oss;
	oss << "system call output failed: " << ofname << std::endl;
	throw std::runtime_error(oss.str());
      }
    ifs >> ckx;
    ifs >> cky;

    // Remove temporary file.
    std::remove(ofname.c_str());

    // ..add to origin point to get final destination.
    double x = longitude_zero_x + ckx;
    double y = latitude_zero_y - cky;
    return std::make_tuple(x, y);
  }

  using ump2tduce = std::unordered_map<a60::point_2t, a60::point_2t>;

  template<int _Height>
  struct ckcache
  {
    static ump2tduce&
    get_cache()
    {
      // Cached pairs of (lat, long) to (x, y)
      // This has to be unique for every height used, as this changes
      // the values returned from the projection formula.
      static ump2tduce xy;
      return xy;
    }
  };

  ump2tduce&
  get_cache_per() const
  {
    // Get per-height cache.
    const auto height = pframe.height();
    if (height == 960)
      return ckcache<960>::get_cache();
    if (height == 1002)
      return ckcache<1920>::get_cache();
    if (height == 1056)
      return ckcache<1056>::get_cache();
    if (height == 1080)
      return ckcache<1080>::get_cache();
    if (height == 1556)
      return ckcache<1556>::get_cache();
    if (height == 1920)
      return ckcache<1920>::get_cache();
    if (height == 2112)
      return ckcache<2112>::get_cache();
    if (height == 2160)
      return ckcache<2160>::get_cache();
    if (height == 2492)
      return ckcache<2492>::get_cache();
    if (height == 2640)
      return ckcache<2640>::get_cache();
    if (height == 3297)
      return ckcache<3297>::get_cache();
    if (height == 3840)
      return ckcache<3840>::get_cache();
    if (height == 4224)
      return ckcache<4224>::get_cache();
    if (height == 6600)
      return ckcache<6600>::get_cache();
    if (height == 8250)
      return ckcache<8250>::get_cache();
    if (height == 13163)
      return ckcache<13163>::get_cache();

    string m("ckproj::get_cache_per height unknown for height value ");
    m += to_string(height);
    throw std::runtime_error(m);
  }

  // Cached version of above.
  a60::point_2t
  meridians_to_point_2d(double lt, double lng) const
  {
    ump2tduce& cachexy = get_cache_per();

    // Use it.
    a60::point_2t latlngval = std::make_pair(lt, lng);
    a60::point_2t retval;
    auto i = cachexy.find(latlngval);
    if (i != cachexy.end())
      retval = i->second;
    else
      {
	retval = meridians_to_point_2d_via_js(lt, lng);
	cachexy.insert(std::make_pair(latlngval, retval));
      }
    return retval;
  }
};


/**
   Cahill-Keyes-as-per visionscarto.net's Cahill-Keyes Projection.

   vc.net == visioncarto.net
   https://vc.net/carte-di-base
   https://vc.net/public/fonds-de-cartes-it/visionscarto-cahillkeyes.svg

   https://observablehq.com/@fil/cahill-keyes-projection

   In the Cahill-Keyes octant assembly, y is the distance from the
   equator to the north pole, -y is the distance from the equator to
   the south pole, and the total circumfrence of the globe is a
   distance of 4y.

   For rendering to screen with this projection, derive y via
   4y = projection.width

   Since the rendered images are full-width but not full-height (for
   the octant grid where 2y = height.
*/

/// 1080P
const ckproj ck_1x1080({pck_1x1080, 960, 480, cahillkeyes, "visionscarto-cahillkeyes-1080p-1x.096"});

const ckproj ck_2x1080({pck_2x1080, 1920, 960, cahillkeyes, "visionscarto-cahillkeyes-1080p-2x.096"});


/// ENGC

/// 1x
/// 22 x 17 map (landscape)
const ckproj ck_1xengc({{2112, 1056}, 1056, 528, cahillkeyes, "visionscarto-cahillkeyes-engc-1x.096"});

/// 2x
/// 2 x Engineering C (landscape)
/// 44 x 17 map (landscape)
const ckproj ck_2xengc({{4224, 2112}, 2112, 1056, cahillkeyes, "visionscarto-cahillkeyes-engc-2x-v3.300"});

/// 2.66x
/// 44 x 34 map (landscape)
const ckproj ck_4xengc({{8448, 4224}, 4224, 2112, cahillkeyes, "visionscarto-cahillkeyes-engc-4x.096"});

/// 2.5x
/// 4 x Engineering C (portrait)
/// (17 x 22) x 4 slices == (portrait) 68 x 22
const ckproj ck96_2bisx({{5280, 2640}, 2640, 1320, cahillkeyes, "visionscarto-cahillkeyes-engc-2.5x.096"});
const ckproj ck300_2bisx({{16500, 8250}, 8250, 4125, cahillkeyes, "visionscarto-cahillkeyes-engc-2.5x.300"});

/// 7.3x aka "star x"
/// 4 x Engineering C (portrait)
/// (17 x 22) x 2 slices (invert and mirror) top		-> 34 x 22
/// (17 x 22) x 2 slices bottom					-> 34 x 22
/// Tiled to project over North Pole				-> 34 x 44
/// Felix Gonzalez-Torres "Untitled", 1992/1993, poster SFMOMA  -> 29 x 44
const ckproj ck96_starx_engc({pck_7x, 2492, 1246, cahillkeyes, "visionscarto-cahillkeyes-engc-7.3x-starx.096"});
const ckproj ck300_starx_engc({pck_7x, 2492, 1246, cahillkeyes, "visionscarto-cahillkeyes-engc-7.3x-starx.300"});

/// 3x aka "star x"
/// 4 x A5 (portrait)
const ckproj ck96_starx_a5({pck_3x, 1002, 501, cahillkeyes, "visionscarto-cahillkeyes-a5-3x-starx"});

/// 44x22
const ckproj ck_44x22({f44x22h, 2112, 1056, cahillkeyes, "visionscarto-cahillkeyes-44x22.300"});


const vd tiles_ck_2xengc_h = { 0, -2112 };
const vd tiles_ck_2xengc_v = { -240 };

const vd tiles_ck_2x1080p_h = { 0, -1920 };
const vd tiles_ck_2x1080p_v = { -280 };

// NB: Formula is xoff, xoff - (n * 1320) where n >= 1
const vd tiles_ck_2bisx_h = { 156, -1164, -2484, -3804 };
const vd tiles_ck_2bisx_v = { -265 };
const vd tiles_ck_2bisx_v2 = { -126, -886 };

const vd tiles_ck_4x_h = { -6208, -1754, -4570 };
const vd tiles_ck_4x_v = { 19 };

const vd tiles_ck_4x44x22_h = { 0, -1056, -2112, -3168 };
const vd tiles_ck_4x44x22_v = { 19 };

// 378, -1254, -2098, -3728
const vd tiles_ck_starx_engc_h = { 378, -1254, -2098, -3728 };
const vd tiles_ck_starx_engc_v = { -190 };

// 378, -1254, -2098, -3728
const vd tiles_ck_starx_a5_h = { 57, -503, -939, -1500 };
const vd tiles_ck_starx_a5_v = { -104 };

} // namespace carto

#endif
