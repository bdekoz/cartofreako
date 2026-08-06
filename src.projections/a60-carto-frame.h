// alpha60 cartography frame -*- mode: C++ -*-

// alpha60
// frame and frame constants

// Copyright (c) 2016-2020, 2024, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_FRAME_H
#define a60_CARTOGRAPHY_FRAME_H 1

#include <a60-numeric.h>
#include <a60-svg.h>

namespace a60::carto {


enum class frame_scale { print, video };
constexpr frame_scale dframe_scale = frame_scale::print;


/**
     Margin is required space from edge of the frame for a given output device.
     For reductions (say 50%), one needs 2x the space....
   const int fmargin = 50; // viz-65
   const int fmargin = 75; // Createspace try v13 -
   const int fmargin = 100; // Createspace try v67 +
  */
constexpr int
frame_margin()
{
  if constexpr (dframe_scale == frame_scale::print)
    return 120; // Createspace try v73 +, at 96dp 1.25"
  if constexpr (dframe_scale == frame_scale::video)
    return 60;
}

/// Common offset for placements next to or from...
const int fspacer = 5;


/**
   Frame

   Output size, display size, ie bounded area into which the
   projection, legend, title, and other symbology are drawn to
   create the map.
*/
struct frame
{
  using atype = space_type;
  using area = svg::area<atype>;

  /// Map-coordinate extent. The SVG document selects its physical unit; the
  /// print generators interpret one frame unit as one inch.
  area		frame_area;

  /// Projection coordinates in frame, at origin (0,0).
  double	moriginx;
  double	moriginy;

  frame(const area a, const double x = 0.0, const double y = 0.0)
  : frame_area(a), moriginx(x), moriginy(y) { }

  frame(const atype w, const atype h, const double x = 0.0, const double y = 0.0)
  : frame_area({w, h}), moriginx(x), moriginy(y) { }

  /// Frame with explicit projection coordinates given.
  frame(const frame& f, const double x, const double y)
  : frame_area(f.frame_area), moriginx(x), moriginy(y) { }

  frame(const frame&) = default;
  frame& operator=(const frame&) = default;

  void
  center(const frame& pf)
  {
    moriginx = (width() - pf.width()) / 2;
    moriginy = ((height() - pf.height()) / 2);
  }

  frame
  bottom_tile_frame() const
  {
    frame ret(*this);
    ret.moriginy -= ret.frame_area._M_height;
    return ret;
  }

  double&
  width() { return frame_area._M_width; }

  double&
  height() { return frame_area._M_height; }


  double
  width() const { return frame_area._M_width; }

  double
  height() const { return frame_area._M_height; }
};


/**
   Standard frame constants.

   (common video and print forms)

   Assumes orientation explicitly noted as
     landscape (horizontal or h) orientation
     portrait (vertical or v) orientation.
*/

/// 1080p video
const frame f1080p_090_h(svg::k::v1080p_h);
const frame f1080p_096_h(2048, 1152);
const frame f1080pduo_096_h(3840, 1920);

const frame f1080p_090_v(svg::k::v1080p_v);
const frame f1080p_096_v(1152, 2048);

const frame f1080p_n1(2048, 2304, -3084, 62);
const frame f1080p_n1a(2048, 1152, -3084, 162);
const frame f1080p_n1b = f1080p_n1a.bottom_tile_frame();

const frame f1080p_n2(2048, 2304, -220, 62);
const frame f1080p_n2a(2048, 1152, -220, 62);
const frame f1080p_n2b = f1080p_n2a.bottom_tile_frame();

const frame f1080p_n3(2048, 2304, -1550, 62);
const frame f1080p_n3a(2048, 1152, -1550, 62);
const frame f1080p_n3b = f1080p_n3a.bottom_tile_frame();


/// 4k == 2160p video
const frame f4k_090_h(svg::k::v4k_h);
const frame f4k_096_h(svg::k::v4k_v);
const frame f4kduo_096_h(7680, 3840);


/// 2:1 HD, 4k frames for cahill-keyes.
const frame pck_1x1080(1920, 960);
const frame pck_2x1080(3840, 1920);

/// ISO 216 A2 paper size is mm(594 x 420) or inches(23.4 x 16.5)
const frame fa2_096_h(2245, 1587);
const frame fa2_300_h(7016, 4960);


/// ISO 216 A4 paper size is mm(297.4 x 210) or inches(11.7 x 8.3)
const frame fa4_096_h(1123, 794);
const frame fa4_300_h(3508, 2480);

/// ISO 216 A4 Bleed paper size is mm(303 x 216) or inches(11.9 x 8.5)
const frame fa4b_096_h(1145, 816);
const frame fa4b_300_h(3579, 2541);


/// ISO 216 A5 paper size is mm(794, 559)
const frame fa5_096_h(794, 559);
const frame fa5_096_v(559, 794);


/// USA Letter paper size inches(11 x 8.5)
const frame fletter_096_h(svg::k::letter_096_h);

/// USA Letter Bleed paper size inches(11.25 x 8.625)
const frame fletterb_096_h(1080, 828);


/// USA Engineering C paper size is inches(22 x 17)
/// Quarto: USA Letter

/// 1x landscape at 90, 96 dpi
const frame f22x17_090_h(1980, 1530);
const frame f22x17_096_h(svg::k::p22x17_096_h);
const frame f17x22_090_h(1530, 1980);
const frame f17x22_096_v(svg::k::p17x22_096_v);

/// 2x portrait (top-bottom vertical stack landscape) (22 x 34 inches) at 96 dpi
const frame f22x34_096_v(2112, 3264);

/// 4x landscape (2x horizontal 2x vertical) (44 x 34 inches) at 96 dpi
const frame f44x34_096_h(4224, 3264);


/// 7.3x Star-X
const frame pck_7x(4984, 2492);
const frame pck_3x(2004, 1002);

/// USA crown point full sheet is 44x30.

/// Epson P9000 max width size for Cahill-Keyes is 44x22.
const frame f44x22h(svg::k::p44x22_h);
const frame f22x44v(svg::k::p22x44_v);

/**
     ISO Quarto

     BUD Potsdam 2 x A4 with full bleed

     Direct to POD with slices and tiles.

     Assume quarto printing, so 50% shrink is one full-bleed A4-sized page.
  */

// ISO Quarto (paper - paper bleed size).

/// 1x landscape at 90, 96 dpi
const frame fqa4b_096_h(2290, 1632);

/// 1x portrait at 90, 96 dpi
const frame fqa4b_096_v(1632, 2290);


/**
     USA Quarto

     Amazon 2 x 8.5 x 11 with full bleed (8.625 x 11.25),
     22.5 x 17.25 inches == 6750 x 5175 pixels @ 300 dpi

     Direct to POD on Amazon's createspace or Ingram Spark, with slices
     and tiles.

     Assume quarto printing, so 50% shrink is one full-bleed letter-sized page.
  */

// USA Quarto (paper - paper bleed size).
const frame fqletterb_096_h(2160, 1656);
const frame fqletterb_096_v(1656, 2160);

} // namespace carto

#endif
