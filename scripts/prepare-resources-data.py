#!/usr/bin/env python3
"""Build the deterministic Stage 12 resources snapshot from local sources.

This program never downloads data.  The companion fetch script supplies an
IRENA PDF, IAEA PDF, USGS PDF, UN refinery CSV, WRI reef KMZ, Natural Earth
Admin-0 geometry, and World Bank indicator ZIP files.  Keeping preparation
separate makes ordinary generation fully offline and makes a source refresh
reviewable before it replaces the snapshot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from osgeo import ogr

ogr.UseExceptions()


SNAPSHOT_DATE = "2026-08-06"
NATURAL_EARTH_URL = (
    "https://naturalearth.s3.amazonaws.com/110m_cultural/"
    "ne_110m_admin_0_countries.zip"
)
IRENA_URL = (
    "https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Mar/"
    "IRENA_DAT_RE_capacity_statistics_2026.pdf"
)
USGS_URL = "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026.pdf"
IAEA_URL = "https://www-pub.iaea.org/MTCD/publications/PDF/RDS-2-45_web.pdf"
UNDATA_REFINERY_URL = (
    "https://data.un.org/Handlers/DownloadHandler.ashx?"
    "DataFilter=cmID%3aGR%3btrID%3a086&DataMartId=EDATA&Format=csv"
)
WRI_REEF_URL = (
    "https://wriorg.s3.amazonaws.com/s3fs-public/"
    "reefs_at_risk_revisited_present.kmz"
)
WORLD_BANK_URL = "https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"

WB_CODES = (
    "AG.PRD.FOOD.XD",
    "AG.LND.FRST.ZS",
    "ER.FSH.PROD.MT",
    "IP.PAT.RESD",
    "SE.ADT.LITR.ZS",
    "SE.SEC.CUAT.UP.ZS",
    "SE.TER.CUAT.BA.ZS",
    "SE.TER.CUAT.MS.ZS",
    "SP.POP.0014.TO",
    "SP.POP.1519.FE.5Y",
    "SP.POP.1519.MA.5Y",
    "SP.POP.2024.FE.5Y",
    "SP.POP.2024.MA.5Y",
    "SP.POP.2529.FE.5Y",
    "SP.POP.2529.MA.5Y",
    "SP.POP.6064.FE.5Y",
    "SP.POP.6064.MA.5Y",
    "SP.POP.65UP.TO",
    "SP.POP.TOTL",
    "SP.POP.TOTL.FE.IN",
    "SP.POP.TOTL.MA.IN",
)

# USGS MCS 2026, Rare Earths, p. 153.  The table describes 2025 estimates in
# metric tons of rare-earth-oxide equivalent.  Values are deliberately kept
# here as a small auditable transcription; the PDF digest and table total are
# checked below before they can enter the normalized snapshot.
USGS_RARE_EARTH_2025 = {
    "USA": 51_000,
    "AUS": 29_000,
    "BRA": 2_000,
    "MMR": 22_000,
    "CHN": 270_000,
    "IND": 2_900,
    "MDG": 2_700,
    "MYS": 110,
    "NGA": 1_500,
    "RUS": 2_600,
    "THA": 4_800,
    "VNM": 150,
}
USGS_RARE_EARTH_OTHER = 550
USGS_RARE_EARTH_WORLD_TOTAL = 390_000

# IAEA RDS-2/45, table 1, operating net electrical capacity at 31 Dec. 2024.
# Taiwan is included in the published total through the table footnote.
IAEA_NUCLEAR_CAPACITY_2024 = {
    "ARG": 1_641, "ARM": 416, "BLR": 2_220, "BEL": 3_908,
    "BRA": 1_884, "BGR": 2_006, "CAN": 12_714, "CHN": 55_320,
    "CZE": 3_963, "FIN": 4_369, "FRA": 63_000, "HUN": 1_916,
    "IND": 6_920, "IRN": 915, "JPN": 12_631, "KOR": 25_609,
    "MEX": 1_552, "NLD": 482, "PAK": 3_262, "ROU": 1_300,
    "RUS": 26_802, "SVK": 2_302, "SVN": 696, "ZAF": 1_854,
    "ESP": 7_123, "SWE": 7_008, "CHE": 2_973, "ARE": 5_348,
    "GBR": 5_883, "UKR": 13_107, "USA": 96_952, "TWN": 938,
}
IAEA_NUCLEAR_WORLD_TOTAL_2024 = 377_014

REEF_THREATS = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
REEF_REGIONS = (
    "Atlantic", "Australia", "Indian Ocean", "Middle East", "Pacific",
    "Southeast Asia",
)
REEF_GRID_DEGREES = 0.25


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def world_bank_input_digest(cache: Path) -> str:
    """Digest the exact ZIP/JSON file selected for every WDI series."""
    result = hashlib.sha256()
    for code in WB_CODES:
        archive = cache / f"cartofreako-wb-{code}.zip"
        fallback = cache / f"cartofreako-wb-{code}.json"
        source = archive if archive.is_file() else fallback
        require(source.is_file(), f"missing World Bank input for digest: {code}")
        result.update(f"{code}\0{digest(source)}\n".encode("ascii"))
    return result.hexdigest()


def normalized_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def read_wb_csv(cache: Path, code: str) -> tuple[list[str], list[dict[str, str]]]:
    archive = cache / f"cartofreako-wb-{code}.zip"
    json_fallback = cache / f"cartofreako-wb-{code}.json"
    if not archive.is_file() and json_fallback.is_file():
        document = json.loads(json_fallback.read_text(encoding="utf-8"))
        require(
            isinstance(document, list) and len(document) == 2
            and isinstance(document[1], list),
            f"unexpected World Bank JSON layout: {json_fallback}",
        )
        years = sorted({record["date"] for record in document[1]})
        by_country: dict[str, dict[str, str]] = {}
        for record in document[1]:
            iso3 = record.get("countryiso3code", "")
            row = by_country.setdefault(iso3, {
                "Country Name": record.get("country", {}).get("value", ""),
                "Country Code": iso3,
            })
            if record.get("value") is not None:
                row[record["date"]] = str(record["value"])
        return years, list(by_country.values())
    require(archive.is_file(), f"missing World Bank input: {archive}")
    with zipfile.ZipFile(archive) as package:
        candidates = [
            name for name in package.namelist()
            if name.startswith(f"API_{code}_") and name.endswith(".csv")
        ]
        require(len(candidates) == 1, f"unexpected World Bank archive layout: {archive}")
        text = package.read(candidates[0]).decode("utf-8-sig")
    lines = text.splitlines()
    heading = next(
        (index for index, line in enumerate(lines) if line.startswith('"Country Name"')),
        None,
    )
    require(heading is not None, f"World Bank CSV has no heading: {archive}")
    reader = csv.DictReader(lines[heading:])
    rows = list(reader)
    require(rows and reader.fieldnames is not None, f"World Bank CSV is empty: {archive}")
    years = [field for field in reader.fieldnames if re.fullmatch(r"\d{4}", field)]
    return years, rows


def wb_tables(cache: Path) -> tuple[
    dict[str, dict[str, tuple[int, float]]], dict[str, str]
]:
    tables: dict[str, dict[str, tuple[int, float]]] = {}
    country_names: dict[str, str] = {}
    for code in WB_CODES:
        years, rows = read_wb_csv(cache, code)
        table: dict[str, tuple[int, float]] = {}
        for row in rows:
            iso3 = row["Country Code"].strip()
            if not re.fullmatch(r"[A-Z]{3}", iso3):
                continue
            country_names[normalized_name(row["Country Name"])] = iso3
            for year_text in reversed(years):
                raw = row.get(year_text, "").strip()
                if not raw:
                    continue
                value = float(raw)
                if math.isfinite(value):
                    table[iso3] = (int(year_text), value)
                    break
        tables[code] = table
    return tables, country_names


def wb_values_for_year(cache: Path, code: str, year: int) -> dict[str, float]:
    years, rows = read_wb_csv(cache, code)
    year_text = str(year)
    require(year_text in years, f"World Bank {code} has no {year_text} column")
    result: dict[str, float] = {}
    for row in rows:
        iso3 = row["Country Code"].strip()
        raw = row.get(year_text, "").strip()
        if not re.fullmatch(r"[A-Z]{3}", iso3) or not raw:
            continue
        value = float(raw)
        if math.isfinite(value):
            result[iso3] = value
    return result


def prepare_geometry(source: Path, output: Path) -> tuple[dict, set[str]]:
    with tempfile.TemporaryDirectory(prefix="cartofreako-resources-geometry-") as temporary:
        converted = Path(temporary) / "countries.geojson"
        subprocess.run(
            [
                "ogr2ogr", "-f", "GeoJSON", str(converted), str(source),
                "-select",
                "ADMIN,NAME,NAME_LONG,FORMAL_EN,NAME_CIAWF,ADM0_A3,ISO_A3,WB_A3",
            ],
            check=True,
        )
        document = json.loads(converted.read_text(encoding="utf-8"))

    features = document.get("features", [])
    require(len(features) == 177, "Natural Earth Admin-0 feature count drifted")
    explicit = {"KOS": "XKX", "SDS": "SSD"}
    iso3s: set[str] = set()
    for feature in features:
        properties = feature["properties"]
        candidates = [
            properties.get("ISO_A3", ""), properties.get("WB_A3", ""),
            properties.get("ADM0_A3", ""),
        ]
        selected = next(
            (explicit.get(code, code) for code in candidates
             if re.fullmatch(r"[A-Z]{3}", str(code)) and code != "-99"),
            "",
        )
        properties["RESOURCE_A3"] = selected
        if selected and selected != "ATA":
            iso3s.add(selected)
    document["cartofreako"] = {
        "schema": "cartofreako-resources-country-geometry-v1",
        "source": NATURAL_EARTH_URL,
        "release": "Natural Earth 5.1.1, 1:110m Admin-0 countries",
        "license": "public domain",
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return document, iso3s


def country_name_index(
    geometry: dict, wb_names: dict[str, str]
) -> dict[str, str]:
    result = dict(wb_names)
    for feature in geometry["features"]:
        properties = feature["properties"]
        iso3 = properties.get("RESOURCE_A3", "")
        if not iso3:
            continue
        for field in ("ADMIN", "NAME", "NAME_LONG", "FORMAL_EN", "NAME_CIAWF"):
            if properties.get(field):
                result[normalized_name(properties[field])] = iso3
    aliases = {
        "centafrrep": "CAF", "congodr": "COD", "congorep": "COG",
        "cotedivoire": "CIV", "eqguinea": "GNQ", "saotomeprn": "STP",
        "bruneidarsm": "BRN", "chinesetaipei": "TWN", "koreadpr": "PRK",
        "korearep": "KOR", "laopdr": "LAO", "timorleste": "TLS",
        "russianfed": "RUS", "antiguabarb": "ATG", "dominicanrep": "DOM",
        "stkittsnevis": "KNA", "stlucia": "LCA", "stvincentgren": "VCT",
        "trinidadtobago": "TTO", "bosniaherzg": "BIH", "iranir": "IRN",
        "moldovarep": "MDA", "syrianar": "SYR", "uae": "ARE", "uk": "GBR",
        "usa": "USA", "micronesiafs": "FSM", "papuanewguin": "PNG",
        "solomonis": "SLB", "tanzania": "TZA", "bolivia": "BOL",
        "venezuela": "VEN", "palestine": "PSE", "turkiye": "TUR",
        "czechrep": "CZE", "eswatini": "SWZ", "caboverde": "CPV",
        "unitedarabem": "ARE", "micronesia": "FSM", "papuanguin": "PNG",
        "boliviaplurstateof": "BOL", "iranislamicrepof": "IRN",
        "koreadempplsrep": "PRK", "korearepublicof": "KOR",
        "netherlandskingdofthe": "NLD", "republicofmoldova": "MDA",
        "russianfederation": "RUS", "syrianarabrepublic": "SYR",
        "unitedrepoftanzania": "TZA", "venezuelabolivarrep": "VEN",
        "vietnam": "VNM",
        "turkiye": "TUR", "uae": "ARE", "uk": "GBR", "usa": "USA",
    }
    result.update(aliases)
    return result


def irena_capacity_values(
    pdf: Path, names: dict[str, str], mapped_iso3s: set[str], *,
    metric_id: str, table_title: str, next_table_title: str,
    expected_world_total: int,
) -> tuple[list[dict], int]:
    with tempfile.TemporaryDirectory(prefix="cartofreako-irena-") as temporary:
        text_path = Path(temporary) / "irena.txt"
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True)
        text = text_path.read_text(encoding="utf-8", errors="replace")
    total_text = f"{expected_world_total:,}".replace(",", " ")
    total_anchor = text.find(total_text)
    require(total_anchor >= 0, f"IRENA report has no 2025 {table_title} world total")
    start = text.rfind(table_title, 0, total_anchor)
    require(start >= 0, f"IRENA report has no {table_title} table")
    start = text.find("CAP (MW)", start, total_anchor)
    end = text.find(next_table_title, start)
    require(start >= 0 and end > start,
            f"IRENA {table_title} table boundaries drifted")
    section = text[start:end]
    world_match = re.search(r"^World\s+(.+)$", section, re.MULTILINE)
    require(world_match is not None, f"IRENA {table_title} table has no world total")
    world_numbers = re.findall(
        r"(?<!\d)(?:\d{1,3}(?: \d{3})+|\d+)(?!\d)", world_match.group(1)
    )
    require(world_numbers, f"IRENA {table_title} table has no numeric world total")
    world_total = int(world_numbers[-1].replace(" ", ""))
    require(world_total == expected_world_total,
            f"IRENA 2025 {table_title} world total drifted")

    aggregates = {
        normalized_name(name) for name in (
            "World", "Africa", "Asia", "C America + Carib", "Eurasia", "Europe",
            "European Union (27)", "European Union", "Middle East", "N America", "Oceania",
            "S America",
        )
    }
    known_unmapped = {
        normalized_name(name) for name in (
            "Anguilla", "Aruba", "BES Islands", "Br Virgin Is", "Cayman Is",
            "China HK SAR", "China Mac SAR", "Cook Islands", "Curacao",
            "Falkland Is", "Falklands Malv", "Faroe Is", "Faroe Islands",
            "French Guiana", "French Polynesia",
            "Gibraltar", "Greenland", "Guadeloupe", "Guam", "Martinique",
            "Mayotte", "Montserrat", "Neth Antilles", "New Caledonia", "Niue",
            "N Mariana Is", "Puerto Rico", "Reunion", "St Barth", "St Helena",
            "St Maarten", "St Martin", "Turks Caicos", "US Virgin Is",
            "Cabo Verde", "Comoros", "Mauritius", "Sao Tome Prn", "Seychelles",
            "Maldives", "Singapore", "Antigua Barb", "Barbados", "Dominica",
            "Grenada", "St Kitts Nevis", "St Lucia", "St Vincent Gren",
            "Andorra", "Malta", "Bahrain", "Amer Samoa", "Cook Is", "Kiribati",
            "Marshall Is", "Micronesia", "Nauru", "Palau", "Samoa", "Tokelau", "Tonga", "Tuvalu",
            "Fr Guiana", "Fr Polynesia", "New Caledon",
        )
    }
    result: list[dict] = []
    unmatched: list[str] = []
    seen: set[str] = set()
    row_pattern = re.compile(r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 +().'-]*?)\s{2,}(.+)$")
    for line in section.splitlines():
        match = row_pattern.match(line)
        if not match:
            continue
        label, columns = match.groups()
        key = normalized_name(label)
        if key in aggregates or label.startswith("CAP "):
            continue
        numbers = re.findall(r"(?<!\d)(?:\d{1,3}(?: \d{3})+|\d+)(?!\d)", columns)
        if not numbers:
            continue
        value = int(numbers[-1].replace(" ", ""))
        iso3 = names.get(key, "")
        if not iso3 or iso3 not in mapped_iso3s:
            if value > 0 and key not in known_unmapped:
                unmatched.append(f"{label}={value}")
            continue
        require(iso3 not in seen,
                f"duplicate IRENA {metric_id} country mapping: {iso3}")
        seen.add(iso3)
        result.append({
            "family": "resources-energy",
            "metric": metric_id,
            "iso3": iso3,
            "year": 2025,
            "value": value,
            "state": "reported-or-estimated",
        })
    require(not unmatched,
            f"unmapped IRENA {metric_id} rows: " + ", ".join(unmatched))
    # IRENA omits many countries without wind capacity from this aggregate
    # table; the output-share coverage gate below is the release criterion.
    require(len(result) >= 100,
            f"IRENA {metric_id} snapshot is unexpectedly sparse: "
            f"{len(result)} mapped countries")
    result.sort(key=lambda record: record["iso3"])
    return result, world_total


def nuclear_capacity_values(pdf: Path, mapped_iso3s: set[str]) -> list[dict]:
    text = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        check=True, capture_output=True, text=True,
    ).stdout
    require("OVERVIEW OF POWER REACTORS AND NUCLEAR SHARE, 31 DEC. 2024" in text,
            "IAEA operating-reactor table title drifted")
    require("417                  377014" in text,
            "IAEA operating-reactor total drifted")
    require(sum(IAEA_NUCLEAR_CAPACITY_2024.values())
            == IAEA_NUCLEAR_WORLD_TOTAL_2024,
            "IAEA nuclear transcription disagrees with the published total")
    require(set(IAEA_NUCLEAR_CAPACITY_2024) <= mapped_iso3s,
            "IAEA nuclear transcription contains an unmapped country")
    return [
        {
            "family": "resources-energy",
            "metric": "nuclear-operating-capacity",
            "iso3": iso3, "year": 2024, "value": value,
            "state": "reported-or-estimated",
        }
        for iso3, value in sorted(IAEA_NUCLEAR_CAPACITY_2024.items())
    ]


def refinery_throughput_values(
    csv_path: Path, names: dict[str, str], mapped_iso3s: set[str]
) -> tuple[list[dict], float]:
    with csv_path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    require(rows, "UN Energy Statistics refinery extract is empty")
    require(set(rows[0]) >= {
        "Country or Area", "Commodity - Transaction", "Year", "Unit", "Quantity"
    }, "UN Energy Statistics refinery columns drifted")

    excluded = {
        normalized_name(name) for name in (
            "Czechoslovakia (former)", "German Dem. R. (former)",
            "Germany, Fed. R. (former)", "Neth. Antilles (former)",
            "Serbia and Montenegro", "Sudan (former)", "USSR (former)",
            "Yemen Arab Rep. (former)", "Yemen, Dem. (former)",
            "Yugoslavia, SFR (former)", "Ethiopia, incl. Eritrea", "Other Asia",
        )
    }
    latest: dict[str, tuple[int, float, bool]] = {}
    unmapped_latest: dict[str, tuple[int, float]] = {}
    for row in rows:
        if row["Commodity - Transaction"] != "Total refinery throughput":
            continue
        require(row["Unit"].replace(" ", "") == "Metrictons,thousand",
                "UN refinery throughput unit drifted")
        name = row["Country or Area"]
        key = normalized_name(name)
        if key in excluded:
            continue
        year = int(row["Year"])
        value = float(row["Quantity"])
        require(1990 <= year <= 2024 and math.isfinite(value) and value >= 0,
                f"invalid UN refinery observation for {name}")
        estimated = bool(row.get("Quantity Footnotes", "").strip())
        iso3 = names.get(key, "")
        destination = latest if iso3 in mapped_iso3s else unmapped_latest
        selected_key = iso3 if iso3 in mapped_iso3s else name
        if selected_key not in destination or year > destination[selected_key][0]:
            if destination is latest:
                destination[selected_key] = (year, value, estimated)
            else:
                destination[selected_key] = (year, value)

    require(len(latest) >= 90, "UN refinery throughput snapshot is unexpectedly sparse")
    output_total = sum(value for _, value, _ in latest.values())
    output_total += sum(value for _, value in unmapped_latest.values())
    # Keep the released map current enough to compare countries.  Older rows
    # remain part of the denominator used by the output-share coverage gate,
    # so dropping them cannot make the gate easier to pass.
    result = [
        {
            "family": "resources-energy",
            "metric": "petroleum-refinery-throughput",
            "iso3": iso3, "year": year, "value": round(value, 8),
            "state": "estimated" if estimated else "reported-or-estimated",
        }
        for iso3, (year, value, estimated) in sorted(latest.items())
        if year >= 2018
    ]
    require(len(result) >= 100,
            "UN refinery throughput has fewer than 100 current observations")
    return result, output_total


def iter_polygons(geometry: ogr.Geometry):
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        yield geometry
        return
    require(kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection),
            "WRI reef source contains unsupported geometry "
            + ogr.GeometryTypeToName(geometry.GetGeometryType()))
    for index in range(geometry.GetGeometryCount()):
        yield from iter_polygons(geometry.GetGeometryRef(index))


def prepare_reef_grid(source: Path, output: Path) -> dict:
    dataset = ogr.Open(str(source), 0)
    require(dataset is not None, f"GDAL cannot open WRI reef source: {source}")
    cells: dict[tuple[int, int], dict] = {}
    source_features = 0
    source_polygons = 0
    for region in REEF_REGIONS:
        layer = dataset.GetLayerByName(region)
        require(layer is not None, f"WRI reef source omits region {region}")
        require(layer.GetFeatureCount() == 4,
                f"WRI reef threat-class count drifted for {region}")
        layer.ResetReading()
        feature = layer.GetNextFeature()
        while feature is not None:
            source_features += 1
            threat = feature.GetFieldAsString("Name")
            require(threat in REEF_THREATS,
                    f"WRI reef source has unknown threat class {threat}")
            geometry = feature.GetGeometryRef()
            require(geometry is not None and not geometry.IsEmpty(),
                    f"WRI reef source has empty geometry in {region}")
            for polygon in iter_polygons(geometry):
                source_polygons += 1
                point = polygon.PointOnSurface()
                require(point is not None and not point.IsEmpty(),
                        "WRI reef polygon has no interior point")
                column = min(1439, max(0, math.floor(
                    (point.GetX() + 180) / REEF_GRID_DEGREES
                )))
                row = min(719, max(0, math.floor(
                    (point.GetY() + 90) / REEF_GRID_DEGREES
                )))
                key = (column, row)
                item = cells.setdefault(key, {
                    "rank": 0, "source_polygons": 0, "regions": set(),
                })
                item["rank"] = max(item["rank"], REEF_THREATS[threat])
                item["source_polygons"] += 1
                item["regions"].add(region)
            feature = layer.GetNextFeature()

    require(source_features == 24, "WRI reef source feature count drifted")
    require(source_polygons == 63_383, "WRI reef polygon count drifted")
    require(len(cells) >= 7_000, "derived WRI reef grid is unexpectedly sparse")
    threat_names = {rank: name for name, rank in REEF_THREATS.items()}
    features = []
    for feature_index, ((column, row), item) in enumerate(sorted(cells.items()), 1):
        west = -180 + column * REEF_GRID_DEGREES
        south = -90 + row * REEF_GRID_DEGREES
        east = west + REEF_GRID_DEGREES
        north = south + REEF_GRID_DEGREES
        features.append({
            "type": "Feature", "id": f"reef-cell-{feature_index}",
            "properties": {
                "threat": threat_names[item["rank"]],
                "threat_rank": item["rank"],
                "source_polygons": item["source_polygons"],
                "regions": sorted(item["regions"]),
            },
            "geometry": {"type": "Polygon", "coordinates": [[
                [west, south], [east, south], [east, north], [west, north],
                [west, south],
            ]]},
        })
    document = {
        "type": "FeatureCollection",
        "cartofreako": {
            "schema": "cartofreako-resources-reef-grid-v1",
            "source": WRI_REEF_URL,
            "source_release": "Reefs at Risk Revisited, 2011",
            "derivation": "Each 500 m source reef polygon is assigned by an interior point to a 0.25 degree cell; overlapping cells retain the highest integrated local threat class.",
            "resolution_degrees": REEF_GRID_DEGREES,
            "source_features": source_features,
            "source_polygons": source_polygons,
            "grid_cells": len(cells),
        },
        "features": features,
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return document["cartofreako"]


def wb_metric_values(
    family: str, metric: str, table: dict[str, tuple[int, float]],
    mapped_iso3s: set[str], state: str, *, minimum_year: int | None = None,
) -> list[dict]:
    return [
        {
            "family": family, "metric": metric, "iso3": iso3,
            "year": table[iso3][0], "value": round(table[iso3][1], 8),
            "state": state,
        }
        for iso3 in sorted(mapped_iso3s & table.keys())
        if minimum_year is None or table[iso3][0] >= minimum_year
    ]


def resident_patent_rate_values(
    cache: Path, mapped_iso3s: set[str]
) -> tuple[list[dict], float, float]:
    years = (2019, 2020, 2021)
    patents = {
        year: wb_values_for_year(cache, "IP.PAT.RESD", year)
        for year in years
    }
    populations = {
        year: wb_values_for_year(cache, "SP.POP.TOTL", year)
        for year in years
    }
    result = []
    for iso3 in sorted(mapped_iso3s):
        if not all(iso3 in patents[year] and iso3 in populations[year]
                   for year in years):
            continue
        patent_total = sum(patents[year][iso3] for year in years)
        population_total = sum(populations[year][iso3] for year in years)
        if population_total <= 0:
            continue
        result.append({
            "family": "resources-human",
            "metric": "resident-patent-applications-per-million",
            "iso3": iso3, "year": 2021,
            "value": round(1_000_000 * patent_total / population_total, 8),
            "state": "derived",
        })
    world_total = sum(patents[year]["WLD"] for year in years)
    covered_total = sum(
        patents[year][record["iso3"]]
        for record in result for year in years
    )
    require(len(result) >= 90,
            "resident-patent rate snapshot is unexpectedly sparse")
    return result, world_total, covered_total


def human_age_values(
    cache: Path, mapped_iso3s: set[str]
) -> tuple[list[dict], list[dict]]:
    under_30: list[dict] = []
    over_60: list[dict] = []
    codes = {
        "age0_14": "SP.POP.0014.TO",
        "female": "SP.POP.TOTL.FE.IN", "male": "SP.POP.TOTL.MA.IN",
        "total": "SP.POP.TOTL", "age65": "SP.POP.65UP.TO",
        "f15": "SP.POP.1519.FE.5Y", "m15": "SP.POP.1519.MA.5Y",
        "f20": "SP.POP.2024.FE.5Y", "m20": "SP.POP.2024.MA.5Y",
        "f25": "SP.POP.2529.FE.5Y", "m25": "SP.POP.2529.MA.5Y",
        "f60": "SP.POP.6064.FE.5Y", "m60": "SP.POP.6064.MA.5Y",
    }
    year_tables = {
        name: wb_values_for_year(cache, code, 2024)
        for name, code in codes.items()
    }
    for iso3 in sorted(mapped_iso3s):
        parts = {name: table.get(iso3) for name, table in year_tables.items()}
        if all(value is not None for value in parts.values()):
            values = {name: float(value) for name, value in parts.items() if value is not None}
            total = values["total"]
            if total <= 0:
                continue
            youth = values["age0_14"]
            youth += values["female"] * (values["f15"] + values["f20"] + values["f25"]) / 100
            youth += values["male"] * (values["m15"] + values["m20"] + values["m25"]) / 100
            older = values["age65"]
            older += values["female"] * values["f60"] / 100
            older += values["male"] * values["m60"] / 100
            under_30.append({
                "family": "resources-human", "metric": "population-under-30",
                "iso3": iso3, "year": 2024,
                "value": round(100 * youth / total, 8), "state": "derived",
            })
            over_60.append({
                "family": "resources-human", "metric": "population-over-60",
                "iso3": iso3, "year": 2024,
                "value": round(100 * older / total, 8), "state": "derived",
            })
    require(len(under_30) >= 150, "derived under-30 coverage is unexpectedly sparse")
    return under_30, over_60


def coverage(
    records: list[dict], mapped_iso3s: set[str], population: dict[str, tuple[int, float]],
    *, output_total: float | None = None, output_numerator: float | None = None,
) -> dict:
    covered = {record["iso3"] for record in records}
    population_denominator = sum(
        population[iso3][1] for iso3 in mapped_iso3s if iso3 in population
    )
    population_numerator = sum(
        population[iso3][1] for iso3 in covered if iso3 in population
    )
    result = {
        "covered_countries": len(covered),
        "mapped_countries": len(mapped_iso3s),
        "country_percent": round(100 * len(covered) / len(mapped_iso3s), 3),
        "population_percent": round(
            100 * population_numerator / population_denominator, 3
        ) if population_denominator else None,
        "output_percent": None,
        "passes_non_sparse": False,
    }
    if output_total is not None:
        numerator = (sum(record["value"] for record in records)
                     if output_numerator is None else output_numerator)
        require(numerator <= output_total * 1.01,
                "covered output exceeds the published total by more than 1%")
        result["output_percent"] = round(
            min(100.0, 100 * numerator / output_total), 3
        )
        result["passes_non_sparse"] = result["output_percent"] >= 90
    else:
        result["passes_non_sparse"] = (
            result["country_percent"] >= 80
            and result["population_percent"] is not None
            and result["population_percent"] >= 90
        )
    return result


def metric(
    identifier: str, title: str, unit: str, period: str, evidence: str,
    source_ids: list[str], status: str, notes: str,
    *, scale: str = "linear", output_tag: str = "",
    metric_coverage: dict | None = None, spatial: dict | None = None,
) -> dict:
    return {
        "id": identifier, "title": title, "unit": unit,
        "reference_period": period, "evidence_class": evidence,
        "source_ids": source_ids, "status": status, "scale": scale,
        "output_tag": output_tag, "coverage": metric_coverage,
        "spatial": spatial,
        "notes": notes,
    }


def build_profile(
    geometry_sha: str, values_sha: str, source_shas: dict[str, str],
    coverages: dict[str, dict], reef_spatial: dict,
) -> dict:
    sources = [
        {
            "id": "natural-earth-admin0", "organization": "Natural Earth",
            "title": "Admin 0 – Countries, 1:110m", "release": "5.1.1",
            "url": NATURAL_EARTH_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "Public domain", "sha256": source_shas["natural-earth"],
        },
        {
            "id": "irena-rsc-2026", "organization": "IRENA",
            "title": "Renewable Capacity Statistics 2026", "release": "2026-03",
            "url": IRENA_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "IRENA publication; normalized factual extract",
            "sha256": source_shas["irena"],
        },
        {
            "id": "usgs-mcs-2026", "organization": "U.S. Geological Survey",
            "title": "Mineral Commodity Summaries 2026", "release": "2026",
            "url": USGS_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "U.S. Government work; normalized factual extract",
            "sha256": source_shas["usgs"],
        },
        {
            "id": "wdi-2026-07-13", "organization": "World Bank",
            "title": "World Development Indicators", "release": "2026-07-13",
            "url": "https://databank.worldbank.org/source/world-development-indicators",
            "retrieved_at": SNAPSHOT_DATE, "license": "CC BY 4.0",
            "sha256": source_shas["world-bank"],
        },
        {
            "id": "iaea-rds-2-45", "organization": "IAEA",
            "title": "Operating Experience with Nuclear Power Stations in Member States in 2024",
            "release": "RDS No. 2/45, 2025",
            "url": IAEA_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "IAEA publication; normalized factual extract",
            "sha256": source_shas["iaea"],
        },
        {
            "id": "unsd-energy-2025", "organization": "United Nations Statistics Division",
            "title": "Energy Statistics Database — total refinery throughput",
            "release": "UNdata update 2025-12-15",
            "url": UNDATA_REFINERY_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "UNdata terms; normalized factual extract",
            "sha256": source_shas["refinery"],
        },
        {
            "id": "wri-reefs-at-risk-2011", "organization": "World Resources Institute",
            "title": "Reefs at Risk Revisited — present reefs and integrated local threat",
            "release": "2011 global 500 m KML",
            "url": WRI_REEF_URL, "retrieved_at": SNAPSHOT_DATE,
            "license": "CC BY 3.0",
            "sha256": source_shas["reef"],
        },
        {
            "id": "fao-faostat", "organization": "FAO",
            "title": "FAOSTAT production and food balances", "release": "current snapshot required",
            "url": "https://www.fao.org/faostat/en/#home", "retrieved_at": SNAPSHOT_DATE,
            "license": "FAOSTAT terms apply", "sha256": "not-yet-ingested",
        },
        {
            "id": "uis", "organization": "UNESCO Institute for Statistics",
            "title": "UIS education data", "release": "2026 refresh",
            "url": "https://databrowser.uis.unesco.org/", "retrieved_at": SNAPSHOT_DATE,
            "license": "Review export terms before promotion", "sha256": "not-yet-ingested",
        },
        {
            "id": "wipo", "organization": "WIPO",
            "title": "Intellectual Property Statistics", "release": "current snapshot required",
            "url": "https://www.wipo.int/en/web/ip-statistics/about", "retrieved_at": SNAPSHOT_DATE,
            "license": "Review export terms before promotion", "sha256": "not-yet-ingested",
        },
        {
            "id": "world-bank-wbl-2026", "organization": "World Bank",
            "title": "Women, Business and the Law 2026", "release": "2026",
            "url": "https://wbl.worldbank.org/en/data/download-data", "retrieved_at": SNAPSHOT_DATE,
            "license": "Review workbook terms before promotion", "sha256": "not-yet-ingested",
        },
        {
            "id": "world-bank-gdim", "organization": "World Bank",
            "title": "Global Database on Intergenerational Mobility", "release": "current snapshot required",
            "url": "https://www.worldbank.org/en/topic/poverty/brief/what-is-the-global-database-on-intergenerational-mobility-gdim",
            "retrieved_at": SNAPSHOT_DATE, "license": "Review before promotion",
            "sha256": "not-yet-ingested",
        },
    ]

    families = [
        {
            "id": "resources-energy", "title": "Energy resources",
            "default_metric": "solar-capacity",
            "palette": {"low": [255, 241, 168], "high": [177, 61, 32], "missing": [211, 208, 198]},
            "metrics": [
                metric("solar-capacity", "Installed solar generating capacity", "MW", "2025", "reported-statistic", ["irena-rsc-2026"], "default", "End-of-year capacity; not generation.", scale="log1p", output_tag="solar-capacity-2025", metric_coverage=coverages["solar-capacity"]),
                metric("wind-capacity", "Installed wind generating capacity", "MW", "2025", "reported-statistic", ["irena-rsc-2026"], "released", "End-of-year onshore and offshore capacity combined; not generation.", scale="log1p", output_tag="wind-capacity-2025", metric_coverage=coverages["wind-capacity"]),
                metric("nuclear-operating-capacity", "Operating nuclear net electrical capacity", "MW(e)", "31 December 2024", "reported-statistic", ["iaea-rds-2-45"], "released", "Operating capacity only; suspended, shutdown, and under-construction reactors are excluded.", scale="log1p", output_tag="nuclear-operating-capacity-2024", metric_coverage=coverages["nuclear-operating-capacity"]),
                metric("oil-field-production", "Crude oil and lease-condensate production", "defined source unit", "annual", "reported-statistic", [], "planned", "Global well-level coverage is not claimed; fields are supplemental."),
                metric("petroleum-refinery-capacity", "Petroleum refinery capacity", "barrels/day", "annual", "reported-statistic", [], "planned", "Capacity is not throughput or extraction."),
                metric("petroleum-refinery-throughput", "Petroleum refinery throughput", "thousand metric tonnes/year", "latest reported from 2018–2024", "reported-statistic", ["unsd-energy-2025"], "released", "The public petrochemical target selects this comparable refinery-processing measure. It is throughput, not nameplate capacity, extraction, or total petrochemical output; observations before 2018 are excluded.", scale="log1p", output_tag="petrochemical-refinery-throughput-latest-2024", metric_coverage=coverages["petroleum-refinery-throughput"]),
                metric("gas-processing-and-lng", "Natural-gas processing and LNG capacity", "defined source unit", "annual", "reported-statistic", [], "planned", "Processing plants, LNG terminals, and pipelines remain distinct."),
                metric("unconventional-gas-production", "Explicitly reported unconventional-gas production", "defined source unit", "annual", "reported-statistic", [], "supplemental", "Never infer fracking from generic gas production or facility presence."),
            ],
        },
        {
            "id": "resources-food", "title": "Food resources",
            "default_metric": "food-production-index",
            "palette": {"low": [246, 236, 180], "high": [45, 126, 70], "missing": [211, 208, 198]},
            "metrics": [
                metric("food-production-index", "Food production index", "index, 2014–2016=100", "2022", "reported-statistic", ["wdi-2026-07-13"], "default", "Latest published WDI country observations in the pinned snapshot.", output_tag="food-production-index-2022", metric_coverage=coverages["food-production-index"]),
                metric("crop-production", "Primary crop production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Keep tonnes, harvested area, and yield separate."),
                metric("livestock-production", "Livestock production", "commodity-specific", "annual", "reported-statistic", ["fao-faostat"], "planned", "Animal counts, biomass, meat, milk, and eggs are not interchangeable."),
                metric("dietary-energy-supply", "Dietary energy supply", "kcal/person/day", "annual", "reported-statistic", ["fao-faostat"], "planned", "Food supply is not production, intake, or a nutrition outcome."),
            ],
        },
        {
            "id": "resources-fauna", "title": "Fauna resources",
            "default_metric": "fisheries-production",
            "palette": {"low": [190, 231, 232], "high": [13, 82, 121], "missing": [211, 208, 198]},
            "metrics": [
                metric("fisheries-production", "Total fisheries production", "metric tonnes", "latest accepted through 2024", "reported-statistic", ["wdi-2026-07-13"], "default", "FAO-supplied World Development Indicator; capture fisheries and aquaculture are combined in this released total.", scale="log1p", output_tag="fisheries-production-latest-2024", metric_coverage=coverages["fisheries-production"]),
                metric("coral-reef-threat", "Coral reef integrated local threat", "four-class spatial field", "Reefs at Risk Revisited 2011", "derived-spatial-field", ["wri-reefs-at-risk-2011"], "released", "Actual 500 m reef polygons are normalized to a 0.25 degree presence grid; overlaps retain the highest source threat class. This is a historical baseline, not current reef condition.", output_tag="coral-reef-threat-2011", spatial=reef_spatial),
                metric("capture-fisheries", "Capture fisheries production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Separate wild capture from aquaculture in a later fauna increment."),
                metric("aquaculture", "Aquaculture production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Separate aquatic animals and plants in a later fauna increment."),
            ],
        },
        {
            "id": "resources-flora", "title": "Flora resources",
            "default_metric": "forest-area-percent",
            "palette": {"low": [238, 229, 171], "high": [26, 102, 59], "missing": [211, 208, 198]},
            "metrics": [
                metric("forest-area-percent", "Forest area", "% of land area", "2023", "reported-statistic", ["wdi-2026-07-13"], "default", "Latest published WDI country observations in the pinned snapshot; not a remotely sensed density field.", output_tag="forest-area-percent-2023", metric_coverage=coverages["forest-area-percent"]),
                metric("land-cover", "Plant life and land-cover class", "class", "2020", "remote-sensed-field", [], "planned", "Copernicus global field; land cover is not biodiversity."),
                metric("forest-cover-density", "Tree-cover density", "%", "source-specific", "remote-sensed-field", [], "planned", "Declare the product domain and masks."),
                metric("savanna-mask", "Savanna class mask", "class", "source-specific", "derived-statistic", [], "planned", "Requires a pinned land-cover/ecological-zone crosswalk."),
                metric("tropical-rainforest-mask", "Tropical rainforest class mask", "class", "source-specific", "derived-statistic", [], "planned", "Not a simple tree-percentage threshold."),
                metric("plant-biodiversity", "Sampling-adjusted vascular-plant richness", "modeled richness", "source-specific", "modeled-field", [], "supplemental", "Raw occurrence counts are dominated by sampling effort."),
            ],
        },
        {
            "id": "resources-mineral", "title": "Mineral resources",
            "default_metric": "rare-earth-mine-production",
            "palette": {"low": [226, 216, 201], "high": [91, 65, 125], "missing": [211, 208, 198]},
            "metrics": [
                metric("rare-earth-mine-production", "Rare-earth mine production", "metric tonnes REO equivalent", "2025 estimate", "reported-statistic", ["usgs-mcs-2026"], "default", "Mine production; reserves and processing are separate.", scale="log1p", output_tag="rare-earth-mine-production-2025", metric_coverage=coverages["rare-earth-mine-production"]),
                *[
                    metric(identifier, title, "commodity-specific", "2025 estimate", "reported-statistic", ["usgs-mcs-2026"], "planned", "Preserve mine/refined production, reserves, resources, and trade as separate measures.")
                    for identifier, title in (
                        ("uranium", "Uranium"), ("lithium", "Lithium"),
                        ("cobalt", "Cobalt"), ("nickel", "Nickel"),
                        ("natural-graphite", "Natural graphite"), ("manganese", "Manganese"),
                        ("copper", "Copper"), ("bauxite-aluminum", "Bauxite and aluminum"),
                        ("gallium", "Gallium"), ("germanium", "Germanium"),
                        ("indium", "Indium"), ("tellurium", "Tellurium"),
                        ("silicon-metal", "Silicon metal"), ("antimony", "Antimony"),
                        ("tungsten", "Tungsten"), ("tin", "Tin"),
                        ("tantalum", "Tantalum"), ("niobium", "Niobium"),
                        ("titanium", "Titanium"), ("vanadium", "Vanadium"),
                        ("platinum-group-metals", "Platinum-group metals"),
                        ("phosphate-rock", "Phosphate rock"), ("potash", "Potash"),
                    )
                ],
            ],
        },
        {
            "id": "resources-human", "title": "Human resources and capabilities",
            "default_metric": "population-under-30",
            "palette": {"low": [219, 229, 239], "high": [32, 95, 142], "missing": [211, 208, 198]},
            "metrics": [
                metric("population-under-30", "Population under age 30", "% of population", "2024", "derived-statistic", ["wdi-2026-07-13"], "default", "Derived from age 0–14 and sex-specific five-year age bands using matched population denominators.", output_tag="population-under-30-2024", metric_coverage=coverages["population-under-30"]),
                metric("population-over-60", "Population age 60 and older", "% of population", "2024", "derived-statistic", ["wdi-2026-07-13"], "released", "Derived from age 60–64 and age 65+ using matched population denominators.", output_tag="population-over-60-2024", metric_coverage=coverages["population-over-60"]),
                metric("adult-literacy", "Adult literacy, age 15+", "%", "latest accepted through 2024", "reported-statistic", ["wdi-2026-07-13"], "planned", "Stage 12 tested the WDI/UIS series, but its 144 mapped countries cover only 89.432% of mapped population and therefore miss the 90% population gate."),
                metric("upper-secondary-attainment", "Completed ISCED 3 or higher, age 25+", "%", "latest observation from 2018–2025", "reported-statistic", ["wdi-2026-07-13"], "released", "Educational attainment, not enrollment; every released observation is from 2018 or later.", output_tag="upper-secondary-attainment-latest-2025", metric_coverage=coverages["upper-secondary-attainment"]),
                metric("bachelors-attainment", "Completed ISCED 6 or higher, age 25+", "%", "latest observation from 2018–2024", "reported-statistic", ["wdi-2026-07-13"], "released", "At least bachelor's or equivalent; short-cycle ISCED 5 is excluded and every released observation is from 2018 or later.", output_tag="bachelors-attainment-latest-2024", metric_coverage=coverages["bachelors-attainment"]),
                metric("advanced-degree-attainment", "Completed ISCED 7 or higher, age 25+", "%", "latest observation from 2018–2024", "reported-statistic", ["wdi-2026-07-13"], "planned", "Stage 12 tested the master's-or-equivalent WDI/UIS series; 126 mapped countries cover 90.335% of population but miss the 80% country gate."),
                metric("resident-patent-applications-per-million", "Resident patent applications", "2019–2021 applications per million person-years", "2019–2021 mean", "derived-statistic", ["wdi-2026-07-13"], "released", "A matched three-year resident-application rate; applications are not grants, invention quality, or current 2026 activity.", scale="log1p", output_tag="resident-patent-applications-per-million-2019-2021", metric_coverage=coverages["resident-patent-applications-per-million"]),
                metric("international-departures-per-capita", "International departures", "departures per resident", "annual", "derived-statistic", ["wdi-2026-07-13"], "supplemental", "A flow proxy; not percentage of unique people taking a trip."),
                metric("books-read-median", "Books read in one calendar year", "median books/person", "annual", "reported-statistic", [], "research-gap", "No harmonized non-sparse global source identified."),
                metric("gender-equality-law", "Gender-equality legal framework", "dimension-specific score", "2026", "legal-policy-observation", ["world-bank-wbl-2026"], "planned", "Law, supportive framework, enforcement, and outcomes remain separate."),
                metric("consensual-same-sex-activity-law", "Consensual same-sex activity legal status", "reviewed legal category", "reviewed snapshot", "legal-policy-observation", [], "planned", "Use a reviewed legal dataset; never label one dimension 'sexual freedom'."),
                metric("drug-possession-penalty", "Personal drug-possession legal response", "substance- and conduct-specific category", "reviewed snapshot", "legal-policy-observation", [], "planned", "Decriminalization must be substance-, quantity-, conduct-, and enforcement-specific."),
                metric("intergenerational-mobility", "Intergenerational mobility", "cohort estimate", "source cohort", "reported-statistic", ["world-bank-gdim"], "planned", "Cohort estimates are not current-year behavior."),
            ],
        },
    ]
    return {
        "schema": "cartofreako-resources-profile-v3",
        "name": "Resources Stage 12 current-source atlas",
        "description": "Six independent resource families with fourteen released country or spatial products, explicit units, observation periods, and non-sparse coverage gates.",
        "snapshot_as_of": SNAPSHOT_DATE,
        "missing_semantics": "Missing is unknown and is never rendered as observed zero.",
        "display": {"data_graphic_opacity": 0.30},
        "country_geometry": {
            "path": "countries-110m.geojson", "sha256": geometry_sha,
            "source_id": "natural-earth-admin0",
        },
        "values": {"path": "resources-values.json", "sha256": values_sha},
        "sources": sources,
        "families": families,
    }


def write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--natural-earth-shapefile", type=Path, required=True)
    parser.add_argument("--natural-earth-archive", type=Path, required=True)
    parser.add_argument("--irena-pdf", type=Path, required=True)
    parser.add_argument("--iaea-pdf", type=Path, required=True)
    parser.add_argument("--usgs-pdf", type=Path, required=True)
    parser.add_argument("--refinery-csv", type=Path, required=True)
    parser.add_argument("--reef-kmz", type=Path, required=True)
    parser.add_argument("--world-bank-cache", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    for path in (
        arguments.natural_earth_shapefile, arguments.natural_earth_archive,
        arguments.irena_pdf, arguments.iaea_pdf, arguments.usgs_pdf,
        arguments.refinery_csv, arguments.reef_kmz,
    ):
        require(path.is_file(), f"missing source input: {path}")

    geometry_path = arguments.output_dir / "countries-110m.geojson"
    geometry, mapped_iso3s = prepare_geometry(
        arguments.natural_earth_shapefile, geometry_path
    )
    tables, wb_names = wb_tables(arguments.world_bank_cache)
    names = country_name_index(geometry, wb_names)

    solar, solar_total = irena_capacity_values(
        arguments.irena_pdf, names, mapped_iso3s,
        metric_id="solar-capacity", table_title="Solar energy",
        next_table_title="Solar photovoltaic",
        expected_world_total=2_391_584,
    )
    wind, wind_total = irena_capacity_values(
        arguments.irena_pdf, names, mapped_iso3s,
        metric_id="wind-capacity", table_title="Wind energy",
        next_table_title="Onshore wind energy",
        expected_world_total=1_291_368,
    )
    nuclear = nuclear_capacity_values(arguments.iaea_pdf, mapped_iso3s)
    refinery, refinery_total = refinery_throughput_values(
        arguments.refinery_csv, names, mapped_iso3s
    )
    food = wb_metric_values(
        "resources-food", "food-production-index",
        tables["AG.PRD.FOOD.XD"], mapped_iso3s, "reported-or-estimated",
    )
    forest = wb_metric_values(
        "resources-flora", "forest-area-percent",
        tables["AG.LND.FRST.ZS"], mapped_iso3s, "reported-or-estimated",
    )
    fisheries = wb_metric_values(
        "resources-fauna", "fisheries-production",
        tables["ER.FSH.PROD.MT"], mapped_iso3s, "reported-or-estimated",
    )
    under_30, over_60 = human_age_values(arguments.world_bank_cache, mapped_iso3s)
    upper_secondary = wb_metric_values(
        "resources-human", "upper-secondary-attainment",
        tables["SE.SEC.CUAT.UP.ZS"], mapped_iso3s, "reported-or-estimated",
        minimum_year=2018,
    )
    bachelors = wb_metric_values(
        "resources-human", "bachelors-attainment",
        tables["SE.TER.CUAT.BA.ZS"], mapped_iso3s, "reported-or-estimated",
        minimum_year=2018,
    )
    patents, patent_world_total, patent_covered_total = resident_patent_rate_values(
        arguments.world_bank_cache, mapped_iso3s
    )
    minerals = [
        {
            "family": "resources-mineral", "metric": "rare-earth-mine-production",
            "iso3": iso3, "year": 2025, "value": value, "state": "estimated",
        }
        for iso3, value in sorted(USGS_RARE_EARTH_2025.items())
    ]
    require(
        sum(USGS_RARE_EARTH_2025.values()) + USGS_RARE_EARTH_OTHER
        <= USGS_RARE_EARTH_WORLD_TOTAL,
        "USGS rare-earth transcription exceeds the rounded world total",
    )
    usgs_text = subprocess.run(
        ["pdftotext", "-layout", str(arguments.usgs_pdf), "-"],
        check=True, capture_output=True, text=True,
    ).stdout
    rare_section = usgs_text[usgs_text.find("RARE EARTHS") :]
    require("World total (rounded)" in rare_section and "390,000" in rare_section,
            "USGS rare-earth table total drifted")

    reef_path = arguments.output_dir / "coral-reefs-025deg.geojson"
    reef_metadata = prepare_reef_grid(arguments.reef_kmz, reef_path)

    all_records = (
        solar + wind + nuclear + refinery + food + fisheries + forest
        + minerals + under_30 + over_60 + upper_secondary + bachelors + patents
    )
    all_records.sort(key=lambda record: (record["family"], record["metric"], record["iso3"]))
    values_document = {
        "schema": "cartofreako-resources-values-v3",
        "snapshot_as_of": SNAPSHOT_DATE,
        "records": all_records,
    }
    values_path = arguments.output_dir / "resources-values.json"
    write_json(values_path, values_document)

    population = tables["SP.POP.TOTL"]
    coverages = {
        "solar-capacity": coverage(solar, mapped_iso3s, population, output_total=solar_total),
        "wind-capacity": coverage(wind, mapped_iso3s, population, output_total=wind_total),
        "nuclear-operating-capacity": coverage(
            nuclear, mapped_iso3s, population,
            output_total=IAEA_NUCLEAR_WORLD_TOTAL_2024,
        ),
        "petroleum-refinery-throughput": coverage(
            refinery, mapped_iso3s, population, output_total=refinery_total,
        ),
        "food-production-index": coverage(food, mapped_iso3s, population),
        "fisheries-production": coverage(fisheries, mapped_iso3s, population),
        "forest-area-percent": coverage(forest, mapped_iso3s, population),
        "rare-earth-mine-production": coverage(
            minerals, mapped_iso3s, population,
            output_total=USGS_RARE_EARTH_WORLD_TOTAL,
        ),
        "population-under-30": coverage(under_30, mapped_iso3s, population),
        "population-over-60": coverage(over_60, mapped_iso3s, population),
        "upper-secondary-attainment": coverage(
            upper_secondary, mapped_iso3s, population
        ),
        "bachelors-attainment": coverage(bachelors, mapped_iso3s, population),
        "resident-patent-applications-per-million": coverage(
            patents, mapped_iso3s, population, output_total=patent_world_total,
            output_numerator=patent_covered_total,
        ),
    }
    for identifier, item in coverages.items():
        require(item["passes_non_sparse"],
                f"released metric failed coverage gate: {identifier}")

    reef_spatial = {
        "path": reef_path.name,
        "sha256": digest(reef_path),
        "source_features": reef_metadata["source_features"],
        "source_polygons": reef_metadata["source_polygons"],
        "mapped_features": reef_metadata["grid_cells"],
        "resolution_degrees": reef_metadata["resolution_degrees"],
        "class_property": "threat_rank",
        "passes_non_sparse": reef_metadata["grid_cells"] >= 7_000,
    }

    profile = build_profile(
        digest(geometry_path), digest(values_path),
        {
            "natural-earth": digest(arguments.natural_earth_archive),
            "irena": digest(arguments.irena_pdf), "usgs": digest(arguments.usgs_pdf),
            "iaea": digest(arguments.iaea_pdf),
            "refinery": digest(arguments.refinery_csv),
            "reef": digest(arguments.reef_kmz),
            "world-bank": world_bank_input_digest(arguments.world_bank_cache),
        },
        coverages, reef_spatial,
    )
    profile_path = arguments.output_dir / "resources-profile.json"
    write_json(profile_path, profile)

    checksum_lines = [
        f"{digest(geometry_path)}  {geometry_path.name}",
        f"{digest(reef_path)}  {reef_path.name}",
        f"{digest(profile_path)}  {profile_path.name}",
        f"{digest(values_path)}  {values_path.name}",
    ]
    (arguments.output_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    print(
        "prepared Stage 12 resources snapshot: "
        f"{len(all_records)} records, {len(mapped_iso3s)} mapped countries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
