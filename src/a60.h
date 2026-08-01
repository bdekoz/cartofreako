// alpha60 root -*- mode: C++ -*-

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

#ifndef a60_H
#define a60_H 1

#include <cstdint>
#include <cmath>
#include <tuple>
#include <string>
#include <vector>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <chrono>
#include <numeric>
#include <algorithm>
#include <locale>
#include <codecvt>
#if __GNUG__ && !(__clang__)
  #include <ext/codecvt_specializations.h>
#endif
#include <sstream>
#include <iomanip> // put_time
#include <iostream>


/// The Alpha60 Project Namespace.
namespace a60 {

/**
   The Alpha60 Project.
   https://alpha60.co
*/


/// Parallel(ism) package preferences.
#define a60_SINGLE 0
#define a60_PARALLEL_THREAD_SIMPLE 0
#define a60_PARALLEL_THREAD_POOL 1
#define a60_PARALLEL_OPENMP 0


/// Constants, Constexpr, and Static Data namespace.
namespace constants {

  constexpr double b_in_gb(1000000000); // 9
  constexpr double gb_in_tb(1000); // 3
  constexpr double tb_in_pb(1000); // 3

  constexpr char tab('\t');
  constexpr char newline('\n');
  constexpr char space(' ');
  constexpr char comma(',');
  constexpr char period('.');
  constexpr char hyphen('-');
  constexpr char loline('_');
  constexpr char quote('"');
  constexpr char colon(':');

  constexpr const char* env_prefix_dir = "a60_PREFIX_DIR";
  constexpr const char* env_data_dir = "a60_DATA_DIR";
  constexpr const char* env_metadata_dir = "a60_METADATA_DIR";
  constexpr const char* env_sample_dir = "a60_SAMPLE_DIR";

  constexpr const char* cache_s = "cache";
  constexpr const char* persist_s = "persistent";
  constexpr const char* cache_persistent_s = "cache-persistent";

  constexpr const char* swarm_s = "swarm";
  constexpr const char* torrent_s = ".torrent";
  constexpr const char* peer_s = "downloader";
  constexpr const char* seed_s = "uploader";
  constexpr const char* inpeer_s = "peer";
  constexpr const char* inseed_s = "seed";

  constexpr const char*	nulldatestamp = "XXXX-XX-XX";
}

/// Alias for constants.
namespace k = constants;


/// Basic data structures and naming patterns.
/// Counting and accumulating integers, floats.
using vul = std::vector<unsigned long>;
using vd = std::vector<double>;

using string = std::string;
using std::to_string;

using strings = std::vector<std::string>;
using vstrings = strings;
using vvstrings = std::vector<strings>;
using sstrings = std::set<string>;
using msstrings = std::multiset<string>;


/// Durational searching and sorting.
using umstrings = std::unordered_map<string, string>;
using usstrings = std::unordered_set<string>;
using cached_strings = usstrings;


/// Counts of similar identifiers.
using id_size = unsigned long;

using nstring = std::tuple<id_size, string>;
using snstrings = std::set<nstring, std::greater<nstring>>;


/// From multiset of strings to ordered elements of id (aka count, identifier).
snstrings
multiset_to_set_of_ids(const msstrings& values)
{
  snstrings ids;

  using mssiter = msstrings::iterator;
  mssiter iter = values.begin();
  mssiter iend = values.end();
  auto lmss = [&ids, &values, &iter] (const std::string& word)
  {
    if (!word.empty())
      {
	auto p = values.equal_range(word);
	unsigned int count = static_cast<int>(std::distance(p.first, p.second));
	ids.insert(make_tuple(count, word));
	std::advance(iter, count - 1);
      }
  };

  std::for_each<mssiter&>(iter, iend, lmss);
  return ids;
}


string
to_lowercase_string(string in)
{
  std::locale loc("");
  for (char& c: in)
    c = std::tolower(c, loc);
  return in;
}


string
to_uppercase_string(string in)
{
  std::locale loc("");
  for (char& c: in)
    c = std::toupper(c, loc);
  return in;
}


string
to_capitalized_string(string in)
{
  if (!in.empty())
    {
      std::locale loc("");
      char& c = in.front();
      c = std::toupper(c, loc);
    }
  return in;
}


string
to_erase_string(string in, const char targetc)
{
  auto pos = in.find(targetc);
  while (pos != string::npos)
    {
      in = in.erase(pos, 1);
      pos = in.find(targetc);
    }
  return in;
}


string
to_replace_string(string in, const char targetc = k::space,
		  const char replacec = k::hyphen)
{
  auto pos = in.find(targetc);
  while (pos != string::npos)
    {
      in = in.replace(pos, 1, string(1, replacec));
      pos = in.find(targetc);
    }
  return in;
}


string
to_replace_spaces_string(string in)
{ return to_replace_string(in, k::space); }


string
to_lowercase_alphanum_string(const string in)
{
  string s1;
  for (const char& c : in)
    if (ispunct(c) == 0)
      s1 += c;

  string s2 = to_replace_string(s1, k::space);
  string s3 = to_lowercase_string(s2);
  return s3;
}


/// Convert a vector of strings to a flattened and
/// comma-space-separated list of strings.
const string
strings_to_cssv_string(const vstrings& in)
{
  string flat;
  unsigned int i = 0;
  for (const string& s : in)
    {
      if (i > 0)
	flat += ", ";
      flat += s;
      i++;
    }
  return flat;
}


/// Sort with less comparator.
inline bool
btiha_less_mixedcase(const string& s1, const string& s2)
{ return s1 < s2; };

/// Sort with less using lowercase comparator.
inline bool
btiha_less_lowercase(const string& s1, const string& s2)
{
  string lc1(to_lowercase_string(s1));
  string lc2(to_lowercase_string(s2));
  return lc1 < lc2;
};

/***
    What BTIHA sorting strategy is in use?

    NB: comparing two collections with different sorting strategies
    means often you are comparing two different torrents to each
    other. This is not useful and is an error.

    2018-2024:	Sort 0
    2024-:	Sort 1
*/
#define a60_USE_BTIHA_SORT 1

#if (a60_USE_BTIHA_SORT == 0)
  const auto btiha_less = btiha_less_mixedcase;
#endif

#if (a60_USE_BTIHA_SORT == 1)
  const auto btiha_less = btiha_less_lowercase;
#endif



/// 2D and 3D coordinate systems.
using space_type = double;

/// 2t
/// C++17 Structured bindings:
/// auto& [ x, y ] = point_2t instance;
using point_2t = std::tuple<space_type, space_type>;

/// Convert point_2t to string.
string
to_string(point_2t p)
{
  auto [ x, y ] = p;
  std::ostringstream oss;
  oss << x << k::comma << y;
  return oss.str();
}

/// 3t
/// C++17 Structured bindings:
/// auto& [ x, y, z ] = point_3t instance;
using point_3t = std::tuple<space_type, space_type, space_type>;

/// 4t
/// C++17 Structured bindings:
/// auto& [ x, y, z, t ] = point_4t instance;
using point_4t = std::tuple<space_type, space_type, space_type, space_type>;

/// Latitude and Longitude Ranges.
using vrange = std::vector<point_2t>;
using vvranges = std::vector<vrange>;


/// 2D distance.
inline space_type
distance_point_2t(const point_2t& a, const point_2t& b)
{
  auto [ax, ay] = a;
  auto [bx, by] = b;
  space_type x = ax - bx;
  space_type y = ay - by;
  double dist(sqrt(pow(x, 2) + pow(y, 2)));
  return dist;
}


/// Normalize value from (min, max) on (nfloor, nceil)
inline double
normalize_on_range(double value, double min, double max,
		   double nfloor, double nceil)
{
  double numer = ((nceil - nfloor) * (value - min));
  double denom = (max - min) + nfloor;
  double weightn(numer / denom);
  return weightn;
}


/// Returns tuple<clustered (weight min, weight max), weight median>
template<typename T>
point_3t
min_max_median(const std::vector<T>& vc)
 {
   // min, max, median.
   auto [min_it, max_it] = std::ranges::minmax_element(vc);

   auto temp = vc;
   std::ranges::sort(temp);

   size_t size = temp.size();
   double median = (size % 2 == 0)
     ? (temp[size/2 - 1] + temp[size/2]) / 2 : temp[size/2];

   return { *min_it, *max_it, median };
 }


/// Convert MaxMind GeoIP information from ISO-8859-1 encoding to UTF-8.
string
convert_8859_to_utf8(string in)
{
  using namespace std;

  using result = codecvt_base::result;
  using int_type = char;
  using ext_type = char;
  string out;

#if __GNUG__ && !(__clang__)
  using state_type = __gnu_cxx::encoding_state;
  using ccutf8_codecvt = codecvt<int_type, ext_type, state_type>;

  const int_type* internal_ptr;
  ext_type* external_ptr;
  ext_type* buf = new int_type[in.size() * 3];

  // Use iconv on linux, ie `iconv --list`

  // Internal encoding is ISO 8859 and external is UTF-8.
  state_type state("ISO-8859-16", "UTF-8", 0, 0);

  ccutf8_codecvt* cvtf8 = new ccutf8_codecvt;
  locale loc(locale::classic(), cvtf8);
  const ccutf8_codecvt& cvt = use_facet<ccutf8_codecvt>(loc);
  result r = cvt.out(state, in.c_str(), in.c_str() + in.size(), internal_ptr,
		     buf, buf + in.size() * 3, external_ptr);
  if (r == codecvt_base::ok)
    out = string(buf, external_ptr);
  else
    {
      if (r == codecvt_base::partial)
	{
	  ext_type* n_ptr = external_ptr;
	  while (n_ptr > external_ptr)
	    {
	      external_ptr = n_ptr;
	      r = cvt.in(state, in.c_str(), in.c_str() + in.size(),
			 internal_ptr, buf, buf + in.size() * 3, n_ptr);
	    }

	  if (r == codecvt_base::ok)
	    out = string(buf, n_ptr);
	  else
	    {
	      std::cerr << "convert_to_utf8: partial at "
			<< static_cast<unsigned long>(n_ptr - in.c_str())
			<< " " << in << std::endl;
	      out = in;
	    }
	}
      if (r == codecvt_base::error)
	{
	  std::cerr << "convert_to_utf8: error " << in << std::endl;
	  out = in;
	}
    }

  // Any escape characters may have to be wrapped for HTML with &#[0][0][0];
  //delete cvtf8;
  delete [] buf;
#endif

  return out;
}


string
convert_to_utf8(string in)
{ return convert_8859_to_utf8(in); }


/// Encapsulated timer with reporting.
struct timer
{
  using clock_type = std::chrono::high_resolution_clock;
  using time_point = clock_type::time_point;
  using minutes = std::chrono::minutes;
  using seconds = std::chrono::seconds;
  using milliseconds = std::chrono::milliseconds;

  time_point		begin;
  time_point		end;

  timer() = default;
  ~timer() = default;

  void
  start() { begin = clock_type::now(); }

  void
  stop() { end = clock_type::now(); }

  string
  report()
  {
    minutes em = std::chrono::duration_cast<minutes>(end - begin);
    seconds es = std::chrono::duration_cast<seconds>(end - begin);
    milliseconds ems = std::chrono::duration_cast<milliseconds>(end - begin);

    std::ostringstream ostr;
    if (em.count() > 0)
      ostr << em.count() << " minutes";
    else
      {
	if (es.count() > 0)
	  ostr << es.count() << " seconds";
	else
	  ostr << ems.count() << " milliseconds";
      }
    ostr << std::endl;
    return ostr.str();
  }
};


/// timer with RAII
struct scoped_timer
{
  string			message;
  std::ostream&		sink;
  timer			elapsed;

  scoped_timer(std::ostream& out, string m)
    : message(m), sink(out), elapsed() { elapsed.start(); }

  ~scoped_timer()
  {
    elapsed.stop();
    sink << message << " time: " << elapsed.report() << std::endl;
  }
};


/// ISO date time stamp as default.
string
time_point_as_string(const std::chrono::system_clock::time_point& tp,
		     bool stampp = true)
{
  using namespace std::chrono;
  std::time_t tp_c = system_clock::to_time_t(tp);
  std::ostringstream odates;

  if (stampp)
    odates << std::put_time(std::localtime(&tp_c), "%Y-%m-%d-at-%H-%M");
  else
    odates << std::ctime(&tp_c);
  return odates.str();
}


/// Top countries for media study.
strings
media_countries()
{
  strings cslices = { "BRA", "IND", "CHN", "RUS", "USA", "KOR", "NLD" };
  return cslices;
};

/// Top countries for leak sample set.
strings
cyberwar_countries()
{
  const strings t10down = { "RUS", "KOR", "BRA", "USA", "TUR",	\
			    "FRA", "CHN", "MEX", "ESP", "DEU" };

  const strings t10up = { "USA", "CHN", "UKR", "RUS", "SWE",	\
			  "CAN", "DEU", "JPN", "NLD", "HKG"};

  strings iso3s;
  if (iso3s.empty())
    {
      /// Set global countrys to specific countries desired
      /// (for serialize_btiha_per).
      sstrings isos;
      isos.insert(t10down.begin(), t10down.end());
      isos.insert(t10up.begin(), t10up.end());
      iso3s = strings(isos.begin(), isos.end());
    }
  return iso3s;
}


strings&
segment_by_country()
{
  // static strings cslices = media_countries();
  static strings cslices = cyberwar_countries();
  return cslices;
};



} // namespace a60
#endif
