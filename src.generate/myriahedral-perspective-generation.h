// Reproducible exploratory Myriahedral perspective metadata and tree data.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_MYRIAHEDRAL_PERSPECTIVE_GENERATION_H
#define CART0FREAK0_MYRIAHEDRAL_PERSPECTIVE_GENERATION_H 1

#include <array>
#include <cstddef>
#include <string_view>

#include "cart0freak0-myriahedral.h"

namespace cart0freak0::myriahedral_generation {

/// Fixed reference and exploratory cut-tree configurations.
enum class perspective
{
  reference,
  americas,
  atlantic,
  afro_eur_asia,
  pacific,
  antarctic,
};

/// Complete metadata required to reproduce and register one perspective.
struct perspective_metadata
{
  perspective id;                  ///< Stable programmatic identifier.
  std::string_view argument;       ///< Generator command-line spelling.
  std::string_view title;          ///< Human-readable map title.
  std::string_view output_tag;     ///< Artifact basename suffix.
  int depth;                       ///< Upstream mesh depth.
  double sigma;                    ///< Gaussian land smoothing sigma.
  double legacy_wlat;              ///< Legacy flag weighting longitude.
  double legacy_wlon;              ///< Legacy flag weighting latitude.
  double legacy_clat;              ///< Legacy flag used as center longitude.
  double legacy_clon;              ///< Legacy flag used as center latitude.
  double alpha;                    ///< Full-flattening parameter.
  double rotation_degrees;         ///< Counterclockwise planar registration.
  double minimum_x;                ///< Rotated raw planar minimum x.
  double minimum_y;                ///< Rotated raw planar minimum y.
  double maximum_x;                ///< Rotated raw planar maximum x.
  double maximum_y;                ///< Rotated raw planar maximum y.
  const char* parent_hex;          ///< Four-hex-digit parent per mesh face.
  std::string_view parent_hex_sha256; ///< Digest of embedded `.inc` data.
  std::string_view tree_sha256;    ///< Digest of the reproducible text tree.
};

inline constexpr char americas_parent_hex[] =
#include "myriahedral-perspective-americas-tree.inc"
  ;

inline constexpr char atlantic_parent_hex[] =
#include "myriahedral-perspective-atlantic-tree.inc"
  ;

inline constexpr char afro_eur_asia_parent_hex[] =
#include "myriahedral-perspective-afro-eur-asia-tree.inc"
  ;

inline constexpr char pacific_parent_hex[] =
#include "myriahedral-perspective-pacific-tree.inc"
  ;

inline constexpr char antarctic_parent_hex[] =
#include "myriahedral-perspective-antarctic-tree.inc"
  ;

static_assert(sizeof(americas_parent_hex) - 1
              == a60::carto::myriahedral_detail::face_count * 4);
static_assert(sizeof(atlantic_parent_hex) - 1
              == a60::carto::myriahedral_detail::face_count * 4);
static_assert(sizeof(afro_eur_asia_parent_hex) - 1
              == a60::carto::myriahedral_detail::face_count * 4);
static_assert(sizeof(pacific_parent_hex) - 1
              == a60::carto::myriahedral_detail::face_count * 4);
static_assert(sizeof(antarctic_parent_hex) - 1
              == a60::carto::myriahedral_detail::face_count * 4);

/// Reference plus five exploratory configurations. The historical helper
/// transposes the semantic use of its `wlat`/`wlon` and `clat`/`clon` names;
/// the field comments above state what each value actually controls.
inline constexpr std::array perspectives {
  perspective_metadata {
    perspective::reference,
    "myriahedral", "Myriahedral reference", "myriahedral-44-24.75",
    5, 0.7, 0.5, 0.1, -60, -65, 1, 335,
    -3.7949260457158975, -2.9255931762882703,
    2.5709697874339961, 1.6095082077949852,
    a60::carto::myriahedral_detail::spanning_tree_parent_hex,
    "e52f7f8391f7742d81342c2ee09b8a88f4a559af828a0444644e7ab7b7c7ce7a",
    "ebfcfb6a89ccf468d2df74d0f979af9cceeff06615f1f40b04c13e7a73b7c89e",
  },
  perspective_metadata {
    perspective::americas,
    "myriahedral-americas", "Myriahedral Americas perspective",
    "myriahedral-americas-44-24.75",
    5, 0.7, 0.5, 0.1, -100, 25, 1, 22,
    -4.1206004492940833, -2.4025065718012648,
    2.9997163078498215, 1.9224228379935782,
    americas_parent_hex,
    "30dc362622ed5ee971a62509ba4721df8bde67c4fcf599800808ae7f27381dbb",
    "a0c22c68f9c48a7f0d11d802c42702660f037220dde29372bf6f4a7e31b12a2c",
  },
  perspective_metadata {
    perspective::atlantic,
    "myriahedral-atlantic", "Myriahedral Atlantic perspective",
    "myriahedral-atlantic-44-24.75",
    5, 0.7, 0.5, 0.1, -25, 15, 1, 24,
    -2.7488319465535604, -3.4832056483745877,
    3.185914616795285, 1.6607341094173917,
    atlantic_parent_hex,
    "5af1647356663ee9affd7d7c87eacd8a3ed2575952a5c9b882c2e149f0b964dd",
    "ded9c5b12a71eddb04ab028b51f8a98416f563eb3b9efeac79ae034bbe2bcad5",
  },
  perspective_metadata {
    perspective::afro_eur_asia,
    "myriahedral-afro-eur-asia", "Myriahedral Afro Eur Asia perspective",
    "myriahedral-afro-eur-asia-44-24.75",
    5, 0.7, 0.5, 0.1, 35, 20, 1, 290,
    -3.8222780457297802, -3.0183800091994351,
    2.0414123593423841, 2.3162192770089409,
    afro_eur_asia_parent_hex,
    "a802f449429e340f7461ee665d67a56a742433ece4c86e18e5c71bdd2d7e3471",
    "3a62d8d2addae901944a776f4341b0776eb9ad89e758100f3ff3f76b62e6f499",
  },
  perspective_metadata {
    perspective::pacific,
    "myriahedral-pacific", "Myriahedral Pacific perspective",
    "myriahedral-pacific-44-24.75",
    5, 0.7, 0.5, 0.1, 160, 0, 1, 326,
    -3.3202431859536947, -2.5619480891692921,
    4.1983393519077943, 2.4960126305723755,
    pacific_parent_hex,
    "b0350cd818f935685f2e85aebd927ac418ca5bcd0f310b6164d8e85215aa132f",
    "b3acc26737648b70ad649a52c254f3b4265aff6053e14fae22fd6b18faff4744",
  },
  perspective_metadata {
    perspective::antarctic,
    "myriahedral-antarctic", "Myriahedral Antarctic perspective",
    "myriahedral-antarctic-44-24.75",
    5, 0.7, 0.3, 0.7, 0, -75, 1, 285,
    -4.972802183827822, -3.8525081072183327,
    1.6145189106927813, 0.80794382516716068,
    antarctic_parent_hex,
    "05fd9fde482bf9f0ec9c702fe182a2c9f35c8a9f5e725348a8036c59eddc5d3f",
    "6eb3c760cdf927669d97eacea2816dd4ccf430f140724fb8f21135d930b98151",
  },
};

/// Look up immutable metadata by identifier.
/// @param id Perspective to find.
/// @return Matching metadata record.
inline constexpr const perspective_metadata&
metadata(const perspective id)
{
  for (const perspective_metadata& candidate : perspectives)
    if (candidate.id == id)
      return candidate;
  return perspectives.front();
}

/// Lazily unfold and cache a selected perspective.
/// @param id Perspective whose tree and registration should be used.
/// @return Immutable complete projection layout.
inline const a60::carto::myriahedral_detail::projection_layout&
layout(const perspective id)
{
  using a60::carto::myriahedral_detail::make_projection_layout;
  switch (id)
    {
    case perspective::reference:
      return a60::carto::myriahedral_detail::layout();
    case perspective::americas:
      {
        static const auto value = make_projection_layout(
          americas_parent_hex, metadata(id).rotation_degrees);
        return value;
      }
    case perspective::atlantic:
      {
        static const auto value = make_projection_layout(
          atlantic_parent_hex, metadata(id).rotation_degrees);
        return value;
      }
    case perspective::afro_eur_asia:
      {
        static const auto value = make_projection_layout(
          afro_eur_asia_parent_hex, metadata(id).rotation_degrees);
        return value;
      }
    case perspective::pacific:
      {
        static const auto value = make_projection_layout(
          pacific_parent_hex, metadata(id).rotation_degrees);
        return value;
      }
    case perspective::antarctic:
      {
        static const auto value = make_projection_layout(
          antarctic_parent_hex, metadata(id).rotation_degrees);
        return value;
      }
    }
  return a60::carto::myriahedral_detail::layout();
}

} // namespace cart0freak0::myriahedral_generation

#endif
