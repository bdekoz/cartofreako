// alpha60 cartography projection utility functions -*- mode: C++ -*-

// alpha60
// cartography projections functions

// Copyright (c) 2020, 2022, 2024 Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef a60_CARTOGRAPHY_PROJECTION_CK_FUNCTIONS_H
#define a60_CARTOGRAPHY_PROJECTION_CK_FUNCTIONS_H 1


namespace a60::carto {

/**
   Returns result of folding arbitrary paths over the
   - horizontal left and right edges
   - vertical top and bottom edges
   of a Cahill-Keyes projection.

   If a path is from quadrant 1 to 4, instead separate it into to paths:
   left edge to quadrant 1 point
   right edge to quadrant 4 point

   And reverse if it is from quadrant 4 to 1.

   Return as two paths.

   Same for top/bottom folds.

   Walks points in order, assumes adjacent indexes are closest points to each other.
*/
template<typename _Proj>
vvranges
fold_path_edges(const carto::cartography<_Proj>& cartog, const vrange& lpoints)
{
  const double vdeltamax = cartog.p.pframe.height() / 3;
  const double quaddist = cartog.p.pframe.width() / 4;

  const double xo = cartog.f.moriginx;
  const double yo = cartog.f.moriginy;

  vvranges vpaths;
  vrange lsegment;
  point_2t previous { };
  for (uint i = 0; i < lpoints.size(); ++i)
    {
      const auto& current = lpoints[i];
      const auto [xc, yc] = current;

      if (i > 0)
	{
	  const auto [xp, yp] = previous;

	  // Compute separate x and y distances.
	  // NB: Zeros here are fine, just zeroing out so one-dimension.
	  const point_2t prevx = { xp, 0 };
	  const point_2t prevy = { 0, yp };
	  const point_2t currx = { xc, 0 };
	  const point_2t curry = { 0, yc };

	  const bool deltax = distance_point_2t(currx, prevx) < (quaddist * 2);
	  const bool deltay = distance_point_2t(curry, prevy) < vdeltamax;

	  if (deltax && deltay)
	    lsegment.push_back(current);
	  else
	    {
	      slice_mode qprev = cartog.point_to_x_quadrant(previous);
	      slice_mode qcurr = cartog.point_to_x_quadrant(current);

	      slice_mode hprev = cartog.point_to_y_half(previous);
	      slice_mode hcurr = cartog.point_to_y_half(current);

	      // 1 XDELTA If more than one, two quadrants, start to take notice.
	      auto qpi = static_cast<int>(qprev);
	      auto qci = static_cast<int>(qcurr);
	      auto hrank = std::abs(qpi - qci);
	      if (!deltax && hrank >= 2)
		{
		  const slice_mode h1 = slice_mode::h_quarto_1;
		  const slice_mode h4 = slice_mode::h_quarto_4;
		  point_2t ledge = std::make_tuple(xo, yp);
		  point_2t redge = std::make_tuple(xo + cartog.p.pframe.width(),
						   yp);

		  bool adjustx = false;
		  if (qprev == h1 && qcurr == h4)
		    {
		      // Wrap left to right side.
		      lsegment.push_back(ledge);
		      vpaths.push_back(lsegment);

		      lsegment.clear();
		      lsegment.push_back(redge);
		      lsegment.push_back(current);
		      adjustx = true;
		    }

		  if (qprev == h4 && qcurr == h1)
		    {
		      // Wrap right to left side.
		      lsegment.push_back(redge);
		      vpaths.push_back(lsegment);

		      lsegment.clear();
		      lsegment.push_back(ledge);
		      lsegment.push_back(current);
		      adjustx = true;
		    }

		  if (!adjustx || !deltay)
		    {
		      string m("fold_path_edgs:: delta x done but ");
		      if (!adjustx)
			m += "no x adjustments" + k::newline;
		      if (!deltay)
			m += "also needed is y adjustment" + k::newline;
		      std::clog << m << k::newline;
		    }
		}

	      // 2 YDELTA If half changes suddently, start to take notice.
	      if (!deltay && hprev != hcurr)
		{
		  const slice_mode vn = slice_mode::v_duo_north;
		  const slice_mode vs = slice_mode::v_duo_south;
		  const point_2t tedge = std::make_tuple(xp, yo);
		  const point_2t bedge = std::make_tuple(xp, yo + cartog.p.pframe.height());

		  bool adjusty = false;
		  if (hprev == vn && hcurr == vs)
		    {
		      // Wrap from top to bottom.
		      lsegment.push_back(tedge);
		      vpaths.push_back(lsegment);

		      lsegment.clear();
		      lsegment.push_back(bedge);
		      lsegment.push_back(current);
		      adjusty = true;
		    }

		  if (hprev == vs && hcurr == vn)
		    {
		      // Move from bottom to top.
		      lsegment.push_back(bedge);
		      vpaths.push_back(lsegment);

		      lsegment.clear();
		      lsegment.push_back(tedge);
		      lsegment.push_back(current);
		      adjusty = true;
		    }

		  // Only do y adjustment, then bail.
		  if (!adjusty || !deltax)
		    {
		      string m("fold_edge_paths:: delta y done but ");
		      if (!adjusty)
			m += "no y adjustments" + k::newline;
		      if (!deltax)
			m += "also needed is x adjustment" + k::newline;
		      std::clog << m << k::newline;
		    }
		}

	      if (!deltax && !deltay)
		{
		  static int bothn(1);
		  string m("fold_edge_paths:: both deltas x & y, case number ");
		  m += to_string(bothn++);
		  std::clog << m << k::newline;
		}

	    } // else ! (deltax && deltay)
	} // if i > 0.
      else
	lsegment.push_back(current);
      previous = current;
    } // for i

  vpaths.push_back(lsegment);
  return vpaths;
}


/// Returns minimized path, fitting points to a globe.
/// If the minimized path is redirected, then the remaining
/// points in lpoints are the other half of the redirection.
template<typename _Proj>
vrange
minimize_path_distance(const carto::cartography<_Proj>& cartog,
		       vrange& lpoints)
{
  vrange lpointssmooth;

  /*
    Cahill-Keyes Butterfly has has 8 octants that have longitude ranges:
    (160-180 + -180 to -110), (-110, 0), (0, 70), (70, 160)

    Thus:
    "leftmost" is longitude 161
    "rightmost" is longitude 159
  */
  const double maxd = cartog.p.pframe.width * 0.5;
  const auto [xz, yz] = cartog.to_point_2d(0, 0);
  const auto [xl, yl] = cartog.to_point_2d(-20, -108);
  const auto [xr, yr] = cartog.to_point_2d(-20, 158);

  point_2t previous { };
  for (uint i = 0; i < lpoints.size(); ++i)
    {
      const auto& current = lpoints[i];
      if (i > 0)
	{
	  auto [xp, yp] = previous;
	  if (distance_point_2t(current, previous) < maxd)
	    lpointssmooth.push_back(current);
	  else
	    {
	      auto [xc, yc] = current;
	      auto y = (yp + yc) / 2;
	      point_2t smoothend;
	      point_2t smoothstart;
	      if (xp > xz)
		{
		  // Previous point in the RHS, current in LHS.
		  smoothend = { xr, y };
		  smoothstart = { xl, y };
		}
	      else
		{
		  // Previous point in the LHS, current in RHS.
		  smoothend = { xl, y };
		  smoothstart = { xr, y };
		}

	      // 1. Insert direction-flipped endpoint in lpsmooth.
	      lpointssmooth.push_back(smoothend);

	      // 2. Insert direction-flipped startpoint in lpoints.
	      // 3. Edit lpoints to remove points already smoothed.
	      vrange lpointsr;
	      lpointsr.push_back(smoothstart);
	      copy(lpoints.begin() + i, lpoints.end(), back_inserter(lpointsr));
	      lpoints = lpointsr;

	      // 3. Return.
	      break;
	    }
	}
      else
	lpointssmooth.push_back(current);
      previous = current;
    }
  vrange lpointsempty;
  lpoints = lpointsempty;
  return lpointssmooth;
}

} // namespace carto

#endif
