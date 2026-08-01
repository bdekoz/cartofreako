// See this to install d3 for node
// https://github.com/d3-node/d3-node
//<script src="https://d3js.org/d3.v5.js"></script>
//<script src="https://unpkg.com/d3-geo-polygon"></script>

const π = Math.PI;
const radians = π/ 180;
const degrees = 180 /π;

var fs = require("fs");
//var d3 = Object.assign({}, require("d3-geo"), require("d3-geo-polygon"));
var d3 = Object.assign({});


var projectionMutator = d3.geoProjectionMutator;

d3.geoPolyhedralCahillKeyes = function(faceProjection) {

  faceProjection = faceProjection || function(face) {
    var centroid = face.length === 6 ? d3.geoCentroid({type: "MultiPoint", coordinates: face}) : face[0];
    return d3.geoCahillKeyes().scale(1);
  };


// TODO generate on-the-fly to avoid external modification.
var octahedron = [
  [0, 90],
  [-90, 0], [0, 0], [90, 0], [180, 0],
  [0, -90]
];

octahedron = [
  [0, 2, 1],
  [0, 3, 2],
  [5, 1, 2],
  [5, 2, 3],
  [0, 1, 4],
  [0, 4, 3],
  [5, 4, 1],
  [5, 3, 4]
].map(function(face) {
  return face.map(function(i) {
    return octahedron[i];
  });
});

  var ck = octahedron.map(function(face) {
    var xyz = face.map(cartesian),
	n = xyz.length,
	a = xyz[n - 1],
	b,
	θ = 17,
	cosθ = Math.cos(θ*radians),
	sinθ = Math.sin(θ*radians),
	hexagon = [];
    for (var i = 0; i < n; ++i) {
      b = xyz[i];
      hexagon.push(spherical([
	a[0] * cosθ + b[0] * sinθ,
	a[1] * cosθ + b[1] * sinθ,
	a[2] * cosθ + b[2] * sinθ
      ]), spherical([
	b[0] * cosθ + a[0] * sinθ,
	b[1] * cosθ + a[1] * sinθ,
	b[2] * cosθ + a[2] * sinθ
      ]));
      a = b;
    }
    return hexagon;
  });

  var cornerNormals = [];

  var parents = [-1, 3, 0, 2, 0, 1, 4, 5];

  ck.forEach(function(hexagon, j) {
    var face = octahedron[j],
	n = face.length,
	normals = cornerNormals[j] = [];
    for (var i = 0; i < n; ++i) {
      ck.push([
	face[i],
	hexagon[(i * 2 + 2) % (2 * n)],
	hexagon[(i * 2 + 1) % (2 * n)]
      ]);
      parents.push(j);
      normals.push(cross(
	cartesian(hexagon[(i * 2 + 2) % (2 * n)]),
	cartesian(hexagon[(i * 2 + 1) % (2 * n)])
      ));
    }
  });

  var faces = ck.map(function(face) {
    return {
      project: faceProjection(face),
      face: face
    };
  });

  parents.forEach(function(d, i) {
    var parent = faces[d];
    parent && (parent.children || (parent.children = [])).push(faces[i]);
  });
  return d3.geoPolyhedral(faces[0], face, 0, true).center([0, 45]);

  function face(λ, φ) {
    var cosφ = Math.cos(φ),
	p = [cosφ * Math.cos(λ), cosφ * Math.sin(λ), Math.sin(φ)];

    var hexagon = λ < -π / 2 ? φ < 0 ? 6 : 4
	: λ < 0 ? φ < 0 ? 2 : 0
	: λ < π / 2 ? φ < 0 ? 3 : 1
	: φ < 0 ? 7 : 5;

    var n = cornerNormals[hexagon];

    return faces[
	dot(n[0], p) < 0 ? 8 + 3 * hexagon
      : dot(n[1], p) < 0 ? 8 + 3 * hexagon + 1
      : dot(n[2], p) < 0 ? 8 + 3 * hexagon + 2
      : hexagon];
  }
};





function dot(a, b) {
  for (var i = 0, n = a.length, s = 0; i < n; ++i) s += a[i] * b[i];
  return s;
}

function cross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0]
  ];
}

// Converts 3D Cartesian to spherical coordinates (degrees).
function spherical(cartesian) {
  return [
    Math.atan2(cartesian[1], cartesian[0]) * degrees,
    Math.asin(Math.max(-1, Math.min(1, cartesian[2]))) * degrees
  ];
}

// Converts spherical coordinates (degrees) to 3D Cartesian.
function cartesian(coordinates) {
  var λ = coordinates[0] * radians,
      φ = coordinates[1] * radians,
      cosφ = Math.cos(φ);
  return [
    cosφ * Math.cos(λ),
    cosφ * Math.sin(λ),
    Math.sin(φ)
  ];
}



    function sinci(x) {
      return x ? x / Math.sin(x) : 1;
    }

    function sgn(x) {
      return x > 0 ? 1 : x < 0 ? -1 : 0;
    }

    function asin(x) {
      return x > 1 ? π/ 2 : (x < -1 ? -π/2 : Math.asin(x));
  }

  function acos(x) {
    return x > 1 ? 0 : x < -1 ? π : Math.acos(x);
  }

  function asqrt(x) {
    return x > 0 ? Math.sqrt(x) : 0;
  }

  // all names of reference points, A, B, D, ... , G, P75
  // or zones, A-L, are detailed fully in Gene Keyes'
  // web site http://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-&-coastline.html

  function cahillKeyes(mg) {
    var CK = {
      "lengthMG": mg // magic scaling length
    };

    preliminaries();

    function preliminaries() {
      var pointN, lengthMB, lengthMN, lengthNG, pointU;
      var m = 29, // meridian
	p = 15, // parallel
	p73a, lF, lT, lM, l, pointV,
	k = Math.sqrt(3);

      CK.lengthMA = 940 / 10000 * CK.lengthMG; //->GLOBAL
      CK.lengthParallel0to73At0 = CK.lengthMG / 100; //->GLOBAL
      CK.lengthParallel73to90At0 = ((CK.lengthMG - CK.lengthMA) -
	(CK.lengthParallel0to73At0 * 73)) / (90 - 73); //->GLOBAL
      CK.sin60 = 0.866025403784439; // √3/2  //->GLOBAL
      CK.cos60 = 0.5; //->GLOBAL
      CK.yTranslate = CK.lengthMG * CK.sin60; //->GLOBAL
      CK.pointM = [0, 0]; //->GLOBAL
      CK.pointG = [CK.lengthMG, 0]; //->GLOBAL
      pointN = [CK.lengthMG, CK.lengthMG * Math.tan(30 * radians)];
      CK.pointA = [CK.lengthMA, 0]; //->GLOBAL
      CK.pointB = lineIntersection(CK.pointM, 30, CK.pointA, 45); //->GLOBAL
      CK.lengthAG = distance(CK.pointA, CK.pointG); //->GLOBAL
      CK.lengthAB = distance(CK.pointA, CK.pointB); //->GLOBAL
      lengthMB = distance(CK.pointM, CK.pointB);
      lengthMN = distance(CK.pointM, pointN);
      lengthNG = distance(pointN, CK.pointG);
      CK.pointD = interpolate(lengthMB, lengthMN, pointN, CK.pointM); //->GLOBAL
      CK.pointF = [CK.lengthMG, lengthNG - lengthMB]; //->GLOBAL
      CK.pointE = [pointN[0] - CK.lengthMA * Math.sin(30 * radians),
	pointN[1] - CK.lengthMA * Math.cos(30 * radians)
      ]; //->GLOBAL
      CK.lengthGF = distance(CK.pointG, CK.pointF); //->GLOBAL
      CK.lengthBD = distance(CK.pointB, CK.pointD); //->GLOBAL
      CK.lengthBDE = CK.lengthBD + CK.lengthAB; // lengthAB = lengthDE  //->GLOBAL
      CK.lengthGFE = CK.lengthGF + CK.lengthAB; // lengthAB = lengthFE  //->GLOBAL
      CK.deltaMEq = CK.lengthGFE / 45; //->GLOBAL
      CK.lengthAP75 = (90 - 75) * CK.lengthParallel73to90At0; //->GLOBAL
      CK.lengthAP73 = CK.lengthMG - CK.lengthMA - CK.lengthParallel0to73At0 * 73; //->GLOBAL
      pointU = [CK.pointA[0] + CK.lengthAP73 * Math.cos(30 * radians),
	CK.pointA[1] + CK.lengthAP73 * Math.sin(30 * radians)
      ];
      CK.pointT = lineIntersection(pointU, -60, CK.pointB, 30); //->GLOBAL

      p73a = parallel73(m);
      lF = p73a.lengthParallel73;
      lT = lengthTorridSegment(m);
      lM = lengthMiddleSegment(m);
      l = p * (lT + lM + lF) / 73;
      pointV = [0, 0];
      CK.pointC = [0, 0]; //->GLOBAL
      CK.radius = 0; //->GLOBAL

      l = l - lT;
      pointV = interpolate(l, lM, jointT(m), jointF(m));
      CK.pointC[1] = (pointV[0] * pointV[0] + pointV[1] * pointV[1] -
	CK.pointD[0] * CK.pointD[0] - CK.pointD[1] * CK.pointD[1]) /
	(2 * (k * pointV[0] + pointV[1] - k * CK.pointD[0] - CK.pointD[1]));
      CK.pointC[0] = k * CK.pointC[1];
      CK.radius = distance(CK.pointC, CK.pointD);

      return CK;
    }

    //**** helper functions ****//

    // distance between two 2D coordinates

    function distance(p1, p2) {
      var deltaX = p1[0] - p2[0],
	deltaY = p1[1] - p2[1];
      return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    }

    // return 2D point at position length/totallength of the line
    // defined by two 2D points, start and end.

    function interpolate(length, totalLength, start, end) {
      var xy = [start[0] + (end[0] - start[0]) * length / totalLength,
	start[1] + (end[1] - start[1]) * length / totalLength
      ];
      return xy;
    }

    // return the 2D point intersection between two lines defined
    // by one 2D point and a slope each.

    function lineIntersection(point1, slope1, point2, slope2) {
      // s1/s2 = slope in degrees
      var m1 = Math.tan(slope1 * radians),
	m2 = Math.tan(slope2 * radians),
	p = [0, 0];
      p[0] = (m1 * point1[0] - m2 * point2[0] - point1[1] + point2[1]) / (m1 - m2);
      p[1] = m1 * (p[0] - point1[0]) + point1[1];
      return p;
    }

    // return the 2D point intercepting a circumference centered
    // at cc and of radius rn and a line defined by 2 points, p1 and p2:
    // First element of the returned array is a flag to state whether there is
    // an intersection, a value of zero (0) means NO INTERSECTION.
    // The following array is the 2D point of the intersection.
    // Equations from "Intersection of a Line and a Sphere (or circle)/Line Segment"
    // at http://paulbourke.net/geometry/circlesphere/

    function circleLineIntersection(cc, r, p1, p2) {
      var x1 = p1[0],
	y1 = p1[1],
	x2 = p2[0],
	y2 = p2[1],
	xc = cc[0],
	yc = cc[1],
	a = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1),
	b = 2 * ((x2 - x1) * (x1 - xc) + (y2 - y1) * (y1 - yc)),
	c = xc * xc + yc * yc + x1 * x1 + y1 * y1 - 2 * (xc * x1 + yc * y1) - r * r,
	d = b * b - 4 * a * c,
	u1 = 0,
	u2 = 0,
	x = 0,
	y = 0;
      if (a === 0) {
	return [0, [0, 0]];
      } else if (d < 0) {
	return [0, [0, 0]];
      }
      u1 = (-b + Math.sqrt(d)) / (2 * a);
      u2 = (-b - Math.sqrt(d)) / (2 * a);
      if ((0 <= u1) && (u1 <= 1)) {
	x = x1 + u1 * (x2 - x1);
	y = y1 + u1 * (y2 - y1);
	return [1, [x, y]];
      } else if ((0 <= u2) && (u2 <= 1)) {
	x = x1 + u2 * (x2 - x1);
	y = y1 + u2 * (y2 - y1);
	return [1, [x, y]];
      } else {
	return [0, [0, 0]];
      }
    }

    // counterclockwise rotate 2D vector, xy, by angle (in degrees)
    // [original CKOG uses clockwise rotation]

    function rotate(xy, angle) {
      var xynew = [0, 0];

      if (angle === -60) {
	xynew[0] = xy[0] * CK.cos60 + xy[1] * CK.sin60;
	xynew[1] = -xy[0] * CK.sin60 + xy[1] * CK.cos60;
      } else if (angle === -120) {
	xynew[0] = -xy[0] * CK.cos60 + xy[1] * CK.sin60;
	xynew[1] = -xy[0] * CK.sin60 - xy[1] * CK.cos60;
      } else {
	// !!!!! This should not happen for this projection!!!!
	// the general algorith: cos(angle) * xy + sin(angle) * perpendicular(xy)
	// return cos(angle * radians) * xy + sin(angle * radians) * perpendicular(xy);
	console.log('rotate: angle ' + angle + ' different than -60 or -120!');
	// counterclockwise
	xynew[0] = xy[0] * Math.cos(angle * radians) - xy[1] * Math.sin(angle * radians);
	xynew[1] = xy[0] * Math.sin(angle * radians) + xy[1] * Math.cos(angle * radians);

      }

      return xynew;
    }

    function sgn(x) {
      return x >= 0 ? 1 : -1;
    }

    // truncate towards zero like int() in Perl

    function truncate(n) {
      return Math[n > 0 ? "floor" : "ceil"](n);
    }

    function equator(m) {
      var l = CK.deltaMEq * m,
	jointE = [0, 0];
      if (l <= CK.lengthGF) {
	jointE = [CK.pointG[0], l];
      } else {
	l = l - CK.lengthGF;
	jointE = interpolate(l, CK.lengthAB,
	  CK.pointF,
	  CK.pointE);
      }
      return jointE;
    }

    function jointE(m) {
      return equator(m);
    }

    function jointT(m) {
      return lineIntersection(CK.pointM, 2 * m / 3,
	jointE(m), m / 3);
    }

    function jointF(m) {
      if (m === 0) {
	return [CK.pointA + CK.lengthAB, 0];
      }
      var xy = lineIntersection(CK.pointA, m,
	CK.pointM, 2 * m / 3);
      return xy;
    }

    function lengthTorridSegment(m) {
      return distance(jointE(m), jointT(m));
    }

    function lengthMiddleSegment(m) {
      return distance(jointT(m), jointF(m));
    }

    function parallel73(m) {
      var p73 = [0, 0],
	jF = jointF(m),
	lF = 0,
	xy = [0, 0];
      if (m <= 30) {
	p73[0] = CK.pointA[0] +
	  CK.lengthAP73 * Math.cos(m * radians);
	p73[1] = CK.pointA[1] +
	  CK.lengthAP73 * Math.sin(m * radians);
	lF = distance(jF, p73);
      } else {
	p73 = lineIntersection(CK.pointT, -60, jF, m);
	lF = distance(jF, p73);
	if (m > 44) {
	  xy = lineIntersection(CK.pointT, -60, jF, 2 / 3 * m);
	  if (xy[0] > p73[0]) {
	    p73 = xy;
	    lF = -distance(jF, p73);
	  }
	}
      }
      return {
	"parallel73": p73,
	"lengthParallel73": lF
      };
    }

    function parallel75(m) {
      return [CK.pointA[0] +
	CK.lengthAP75 * Math.cos(m * radians),
	CK.pointA[1] +
	CK.lengthAP75 * Math.sin(m * radians)];
    }

    // special functions to transform lon/lat to x/y

    function ll2mp(lon, lat) {
      var south = [0, 6, 7, 8, 5],
	o = truncate(((lon + 180) / 90) + 1),
	p, // parallel
	m = ((lon + 180) - 90 * (o - 1)) - 45, // meridian
	s = sgn(m); // sign

      m = Math.abs(m);
      if (o === 5) o = 1;
      if (lat < 0) o = south[o];
      p = Math.abs(lat);
      return [m, p, s, o];
    }

    function zoneA(m, p) {
      return [CK.pointA[0] + (90 - p) * 104, 0];
    }

    function zoneB(m, p) {
      return [CK.pointG[0] - p * 100, 0];
    }

    function zoneC(m, p) {
      var l = 104 * (90 - p);
      return [CK.pointA[0] + l * Math.cos(m * radians),
	CK.pointA[1] + l * Math.sin(m * radians)];
    }

    function zoneD(m, p) {
      p = p; // just keep it for symmetry in signature
      return equator(m);
    }

    function zoneE(m, p) {
      var l = 1560 + (75 - p) * 100;
      return [CK.pointA[0] + l * Math.cos(m * radians),
	CK.pointA[1] + l * Math.sin(m * radians)];
    }

    function zoneF(m, p) {
      return interpolate(p, 15,
	CK.pointE,
	CK.pointD);
    }

    function zoneG(m, p) {
      var l = p - 15;
      return interpolate(l, 58, CK.pointD, CK.pointT);
    }

    function zoneH(m, p) {
      var p75 = parallel75(45),
	p73a = parallel73(m),
	p73 = p73a.parallel73,
	lF = distance(CK.pointT, CK.pointB),
	lF75 = distance(CK.pointB, p75),
	l = (75 - p) * (lF75 + lF) / 2,
	xy = [0, 0];
      if (l <= lF75) {
	xy = interpolate(l, lF75, p75, CK.pointB);
      } else {
	l = l - lF75;
	xy = interpolate(l, lF, CK.pointB, p73);
      }
      return xy;
    }

    function zoneI(m, p) {
      var p73a = parallel73(m),
	lT = lengthTorridSegment(m),
	lM = lengthMiddleSegment(m),
	l = p * (lT + lM + p73a.lengthParallel73) / 73,
	xy;
      if (l <= lT) {
	xy = interpolate(l, lT, jointE(m), jointT(m));
      } else if (l <= (lT + lM)) {
	l = l - lT;
	xy = interpolate(l, lM, jointT(m), jointF(m));
      } else {
	l = l - lT - lM;
	xy = interpolate(l, p73a.lengthParallel73, jointF(m), p73a.parallel73);
      }
      return xy;
    }

    function zoneJ(m, p) {
      var p75 = parallel75(m),
	lF75 = distance(jointF(m), p75),
	p73a = parallel73(m),
	p73 = p73a.parallel73,
	lF = p73a.lengthParallel73,
	l = (75 - p) * (lF75 - lF) / 2,
	xy = [0, 0];

      if (l <= lF75) {
	xy = interpolate(l, lF75, p75, jointF(m));
      } else {
	l = l - lF75;
	xy = interpolate(l, -lF, jointF(m), p73);
      }
      return xy;
    }

    function zoneK(m, p, l15) {
      var l = p * l15 / 15,
	lT = lengthTorridSegment(m),
	lM = lengthMiddleSegment(m),
	xy = [0, 0];
      if (l <= lT) { // point is in torrid segment
	xy = interpolate(l, lT, jointE(m), jointT(m));
      } else { // point is in middle segment
	l = l - lT;
	xy = interpolate(l, lM, jointT(m), jointF(m));
      }
      return xy;
    }

    function zoneL(m, p, l15) {
      var p73a = parallel73(m),
	p73 = p73a.parallel73,
	lT = lengthTorridSegment(m),
	lM = lengthMiddleSegment(m),
	xy,
	lF = p73a.lengthParallel73,
	l = l15 + (p - 15) * ((lT + lM + lF) - l15) / 58;
      if (l <= lT) { //on torrid segment
	xy = interpolate(l, lT, jointE(m), jointF(m));
      } else if (l <= lT + lM) { //on middle segment
	l = l - lT;
	xy = interpolate(l, lM, jointT(m), jointF(m));
      } else { //on frigid segment
	l = l - lT - lM;
	xy = interpolate(l, lF, jointF(m), p73);
      }
      return xy;
    }

    // convert half-octant meridian,parallel to x,y coordinates.
    // arguments are meridian, parallel

    function mp2xy(m, p) {
      var xy = [0, 0],
	lT,
	p15a,
	p15,
	flag15,
	l15;

      if (m === 0) { // zones (a) and (b)
	if (p >= 75) {
	  xy = zoneA(m, p);
	} else {
	  xy = zoneB(m, p);
	}
      } else if (p >= 75) {
	xy = zoneC(m, p);
      } else if (p === 0) {
	xy = zoneD(m, p);
      } else if ((p >= 73) && (m <= 30)) {
	xy = zoneE(m, p);
      } else if (m === 45) {
	if (p <= 15) {
	  xy = zoneF(m, p);
	} else if (p <= 73) {
	  xy = zoneG(m, p);
	} else {
	  xy = zoneH(m, p);
	}
      } else {
	if (m <= 29) {
	  xy = zoneI(m, p);
	} else { // supple zones (j), (k) and (l)
	  if (p >= 73) {
	    xy = zoneJ(m, p);
	  } else { //zones (k) and (l)
	    p15a = circleLineIntersection(CK.pointC,
	      CK.radius,
	      jointT(m), jointF(m));
	    flag15 = p15a[0];
	    p15 = p15a[1];
	    lT = lengthTorridSegment(m);
	    if (flag15 === 1) { // intersection is in middle segment
	      l15 = lT + distance(jointT(m), p15);
	    } else { // intersection is in torrid segment
	      p15a = circleLineIntersection(CK.pointC,
		CK.radius,
		jointE(m), jointT(m));
	      flag15 = p15a[0];
	      p15 = p15a[1];
	      if (flag15 === 0) {
		console.log('Something weird!');
		// TODO: Trap this! Something odd happened!
	      }
	      l15 = lT - distance(jointT(m), p15);
	    }
	    if (p <= 15) {
	      xy = zoneK(m, p, l15);
	    } else { //zone (l)
	      xy = zoneL(m, p, l15);
	    }
	  }
	}
      }
      return xy;
    }

    // from half-octant to megamap (single rotated octant)

    function mj2g(xy, octant) {
      var xynew = [0, 0];

      if (octant === 0) {
	xynew = rotate(xy, -60);
      } else if (octant === 1) {
	xynew = rotate(xy, -120);
	xynew[0] -= CK.lengthMG;
      } else if (octant === 2) {
	xynew = rotate(xy, -60);
	xynew[0] -= CK.lengthMG;
      } else if (octant === 3) {
	xynew = rotate(xy, -120);
	xynew[0] += CK.lengthMG;
      } else if (octant === 4) {
	xynew = rotate(xy, -60);
	xynew[0] += CK.lengthMG;
      } else if (octant === 5) {
	xynew = rotate([(2 * CK.lengthMG - xy[0]), xy[1]], -60);
	xynew[0] += CK.lengthMG;
      } else if (octant === 6) {
	xynew = rotate([(2 * CK.lengthMG - xy[0]), xy[1]], -120);
	xynew[0] -= CK.lengthMG;
      } else if (octant === 7) {
	xynew = rotate([(2 * CK.lengthMG - xy[0]), xy[1]], -60);
	xynew[0] -= CK.lengthMG;
      } else if (octant === 8) {
	xynew = rotate([(2 * CK.lengthMG - xy[0]), xy[1]], -120);
	xynew[0] += CK.lengthMG;
      } else {
	// TODO trap this some way.
	// ERROR!
	// print "Error converting to M-map coordinates; there is no Octant octant!\n";
	console.log('mj2g: something weird happened!');
	return xynew;
      }
      xynew[1] += CK.yTranslate;

      return xynew;
    }


    // general CK map projection

    function forward(λ, φ) {
      // λ, φ are in radians.
      var lon = λ * degrees,
	lat = φ * degrees,
	res = ll2mp(lon, lat),
	m = res[0],
	p = res[1],
	s = res[2],
	o = res[3],
	xy = mp2xy(m, p),
	mm = mj2g([xy[0], s * xy[1]], o);

      return mm;
    }

      function forward_deg(lon, lat) {
	var res = ll2mp(lon, lat),
	m = res[0],
	p = res[1],
	s = res[2],
	o = res[3],
	xy = mp2xy(m, p),
	mm = mj2g([xy[0], s * xy[1]], o);

      return mm;
    }

      // Export functions.
      cahillKeyes.forward_deg = forward_deg;
      cahillKeyes.ll2mp = ll2mp;

    return forward;
  }

/*
  Use a rendered map that is a tight horizontal crop on the octants.

  Half of the height is the equator.
  Half of the width is the prime meridian (29W).

  That is the (x,y) == (0,0) origin for drawing.
*/
var mg = 10000;


// (maxmind) negative longitude is west of the prime meridian

// where prime merdian is defined differently
// (maxmind) grenech meridian is 51 N, 5.33 W
// (cahill) meridian is 15 N, 29 W (prime 29 meridian west)
//var m = 29 - 5.33; // meridian

var m = 29 - 8; // meridian
var p = 0; // parallel

function cahill_keyes_projection(rmg, lng, lat) {
    var ckinit = cahillKeyes(rmg);
    var cxy = cahillKeyes.forward_deg(lng + m, lat + p);
    var x = cxy[0];
    var y = cxy[1];

    console.log(x);
    console.log(y);
}

// debug with specific values for dublin
// cahill_keyes_projection(-6.25, 53.33);

// call using arguments to script invocation for long, lat
var ckargs = process.argv.slice(2);
var rmg = parseFloat(ckargs[0]);
var lng = parseFloat(ckargs[1]);
var lat = parseFloat(ckargs[2]);
cahill_keyes_projection(rmg, lng, lat);
