#!/usr/bin/env python3
"""Build the deterministic Stage 6b resources snapshot from local sources.

This program never downloads data.  The companion fetch script supplies an
IRENA PDF, a USGS PDF, Natural Earth Admin-0 geometry, and World Bank indicator
ZIP files.  Keeping preparation separate makes ordinary generation fully
offline and makes a source refresh reviewable before it replaces the snapshot.
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
WORLD_BANK_URL = "https://api.worldbank.org/v2/en/indicator/{code}?downloadformat=csv"

WB_CODES = (
    "AG.PRD.FOOD.XD",
    "AG.LND.FRST.ZS",
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
    }
    result.update(aliases)
    return result


def irena_solar_values(
    pdf: Path, names: dict[str, str], mapped_iso3s: set[str]
) -> tuple[list[dict], int]:
    with tempfile.TemporaryDirectory(prefix="cartofreako-irena-") as temporary:
        text_path = Path(temporary) / "irena.txt"
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True)
        text = text_path.read_text(encoding="utf-8", errors="replace")
    total_anchor = text.find("2 391 584")
    require(total_anchor >= 0, "IRENA report has no 2025 solar world total")
    start = text.rfind("Solar energy", 0, total_anchor)
    require(start >= 0, "IRENA report has no Solar energy table")
    start = text.find("CAP (MW)", start, total_anchor)
    end = text.find("Solar photovoltaic", start)
    require(start >= 0 and end > start, "IRENA solar table boundaries drifted")
    section = text[start:end]
    world_match = re.search(r"^World\s+(.+)$", section, re.MULTILINE)
    require(world_match is not None, "IRENA solar table has no world total")
    world_numbers = re.findall(
        r"(?<!\d)(?:\d{1,3}(?: \d{3})+|\d+)(?!\d)", world_match.group(1)
    )
    require(world_numbers, "IRENA solar table has no numeric world total")
    world_total = int(world_numbers[-1].replace(" ", ""))
    require(world_total == 2_391_584, "IRENA 2025 solar world total drifted")

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
            "Falkland Is", "Faroe Is", "French Guiana", "French Polynesia",
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
        require(iso3 not in seen, f"duplicate IRENA solar country mapping: {iso3}")
        seen.add(iso3)
        result.append({
            "family": "resources-energy",
            "metric": "solar-capacity",
            "iso3": iso3,
            "year": 2025,
            "value": value,
            "state": "reported-or-estimated",
        })
    require(not unmatched, "unmapped IRENA solar rows: " + ", ".join(unmatched))
    require(len(result) >= 150, "IRENA solar snapshot is unexpectedly sparse")
    result.sort(key=lambda record: record["iso3"])
    return result, world_total


def wb_metric_values(
    family: str, metric: str, table: dict[str, tuple[int, float]],
    mapped_iso3s: set[str], state: str,
) -> list[dict]:
    return [
        {
            "family": family, "metric": metric, "iso3": iso3,
            "year": table[iso3][0], "value": round(table[iso3][1], 8),
            "state": state,
        }
        for iso3 in sorted(mapped_iso3s & table.keys())
    ]


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
    *, output_total: float | None = None,
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
        result["output_percent"] = round(
            100 * sum(record["value"] for record in records) / output_total, 3
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
    *, scale: str = "linear", output_tag: str = "", metric_coverage: dict | None = None,
) -> dict:
    return {
        "id": identifier, "title": title, "unit": unit,
        "reference_period": period, "evidence_class": evidence,
        "source_ids": source_ids, "status": status, "scale": scale,
        "output_tag": output_tag, "coverage": metric_coverage,
        "notes": notes,
    }


def build_profile(
    geometry_sha: str, values_sha: str, source_shas: dict[str, str],
    coverages: dict[str, dict],
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
            "id": "iaea-pris", "organization": "IAEA",
            "title": "Power Reactor Information System", "release": "current snapshot required",
            "url": "https://pris.iaea.org/PRIS/home.aspx", "retrieved_at": SNAPSHOT_DATE,
            "license": "Review before promotion", "sha256": "not-yet-ingested",
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
                metric("wind-capacity", "Installed wind generating capacity", "MW", "2025", "reported-statistic", ["irena-rsc-2026"], "planned", "Separate onshore and offshore when ingested."),
                metric("nuclear-operating-capacity", "Operating nuclear net electrical capacity", "MW", "snapshot", "reported-statistic", ["iaea-pris"], "planned", "Exclude shutdown and under-construction reactors."),
                metric("oil-field-production", "Crude oil and lease-condensate production", "defined source unit", "annual", "reported-statistic", [], "planned", "Global well-level coverage is not claimed; fields are supplemental."),
                metric("petroleum-refinery-capacity", "Petroleum refinery capacity", "barrels/day", "annual", "reported-statistic", [], "planned", "Capacity is not throughput or extraction."),
                metric("petroleum-refinery-throughput", "Petroleum refinery throughput", "barrels/day", "annual", "reported-statistic", [], "planned", "Kept separate from capacity."),
                metric("gas-processing-and-lng", "Natural-gas processing and LNG capacity", "defined source unit", "annual", "reported-statistic", [], "planned", "Processing plants, LNG terminals, and pipelines remain distinct."),
                metric("unconventional-gas-production", "Explicitly reported unconventional-gas production", "defined source unit", "annual", "reported-statistic", [], "supplemental", "Never infer fracking from generic gas production or facility presence."),
            ],
        },
        {
            "id": "resources-food", "title": "Food resources",
            "default_metric": "food-production-index",
            "palette": {"low": [246, 236, 180], "high": [45, 126, 70], "missing": [211, 208, 198]},
            "metrics": [
                metric("food-production-index", "Food production index", "index, 2014–2016=100", "latest accepted through 2025", "reported-statistic", ["wdi-2026-07-13"], "default", "Country observations retain their individual years.", output_tag="food-production-index-latest-2026", metric_coverage=coverages["food-production-index"]),
                metric("crop-production", "Primary crop production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Keep tonnes, harvested area, and yield separate."),
                metric("livestock-production", "Livestock production", "commodity-specific", "annual", "reported-statistic", ["fao-faostat"], "planned", "Animal counts, biomass, meat, milk, and eggs are not interchangeable."),
                metric("capture-fisheries", "Capture fisheries production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Separate wild capture from aquaculture."),
                metric("aquaculture", "Aquaculture production", "tonnes", "annual", "reported-statistic", ["fao-faostat"], "planned", "Separate aquatic animals and plants."),
                metric("dietary-energy-supply", "Dietary energy supply", "kcal/person/day", "annual", "reported-statistic", ["fao-faostat"], "planned", "Food supply is not production, intake, or a nutrition outcome."),
            ],
        },
        {
            "id": "resources-flora", "title": "Flora resources",
            "default_metric": "forest-area-percent",
            "palette": {"low": [238, 229, 171], "high": [26, 102, 59], "missing": [211, 208, 198]},
            "metrics": [
                metric("forest-area-percent", "Forest area", "% of land area", "latest accepted through 2025", "reported-statistic", ["wdi-2026-07-13"], "default", "National statistic; not a remotely sensed density field.", output_tag="forest-area-percent-latest-2026", metric_coverage=coverages["forest-area-percent"]),
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
                metric("population-over-60", "Population age 60 and older", "% of population", "2024", "derived-statistic", ["wdi-2026-07-13"], "available", "Derived from age 60–64 and age 65+ using matched population denominators."),
                metric("adult-literacy", "Adult literacy, age 15+", "%", "latest accepted", "reported-statistic", ["uis"], "planned", "Expose each country's observation year."),
                metric("upper-secondary-attainment", "Completed ISCED 3 or higher, age 25+", "%", "latest accepted", "reported-statistic", ["uis"], "planned", "Do not substitute enrollment."),
                metric("bachelors-attainment", "Completed ISCED 6 or higher, age 25+", "%", "latest accepted", "reported-statistic", ["uis"], "planned", "Keep short-cycle ISCED 5 separate."),
                metric("advanced-degree-attainment", "Completed ISCED 7 or 8, age 25+", "%", "latest accepted", "reported-statistic", ["uis"], "planned", "Preserve sex disaggregation where coverage permits."),
                metric("resident-patent-applications-per-million", "Resident patent applications", "three-year mean per million residents", "latest accepted", "derived-statistic", ["wipo", "wdi-2026-07-13"], "planned", "Applications are not grants or patent quality."),
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
        "schema": "cartofreako-resources-profile-v2",
        "name": "Resources Stage 6b current-source atlas",
        "description": "Five independent resource families with explicit metric units, evidence classes, observation periods, and non-sparse coverage gates.",
        "snapshot_as_of": SNAPSHOT_DATE,
        "missing_semantics": "Missing is unknown and is never rendered as observed zero.",
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
    parser.add_argument("--usgs-pdf", type=Path, required=True)
    parser.add_argument("--world-bank-cache", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    for path in (
        arguments.natural_earth_shapefile, arguments.natural_earth_archive,
        arguments.irena_pdf, arguments.usgs_pdf,
    ):
        require(path.is_file(), f"missing source input: {path}")

    geometry_path = arguments.output_dir / "countries-110m.geojson"
    geometry, mapped_iso3s = prepare_geometry(
        arguments.natural_earth_shapefile, geometry_path
    )
    tables, wb_names = wb_tables(arguments.world_bank_cache)
    names = country_name_index(geometry, wb_names)

    solar, solar_total = irena_solar_values(
        arguments.irena_pdf, names, mapped_iso3s
    )
    food = wb_metric_values(
        "resources-food", "food-production-index",
        tables["AG.PRD.FOOD.XD"], mapped_iso3s, "reported-or-estimated",
    )
    forest = wb_metric_values(
        "resources-flora", "forest-area-percent",
        tables["AG.LND.FRST.ZS"], mapped_iso3s, "reported-or-estimated",
    )
    under_30, over_60 = human_age_values(arguments.world_bank_cache, mapped_iso3s)
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

    all_records = solar + food + forest + minerals + under_30 + over_60
    all_records.sort(key=lambda record: (record["family"], record["metric"], record["iso3"]))
    values_document = {
        "schema": "cartofreako-resources-values-v2",
        "snapshot_as_of": SNAPSHOT_DATE,
        "records": all_records,
    }
    values_path = arguments.output_dir / "resources-values.json"
    write_json(values_path, values_document)

    population = tables["SP.POP.TOTL"]
    coverages = {
        "solar-capacity": coverage(solar, mapped_iso3s, population, output_total=solar_total),
        "food-production-index": coverage(food, mapped_iso3s, population),
        "forest-area-percent": coverage(forest, mapped_iso3s, population),
        "rare-earth-mine-production": coverage(
            minerals, mapped_iso3s, population,
            output_total=USGS_RARE_EARTH_WORLD_TOTAL,
        ),
        "population-under-30": coverage(under_30, mapped_iso3s, population),
    }
    for identifier, item in coverages.items():
        require(item["passes_non_sparse"], f"default metric failed coverage gate: {identifier}")

    profile = build_profile(
        digest(geometry_path), digest(values_path),
        {
            "natural-earth": digest(arguments.natural_earth_archive),
            "irena": digest(arguments.irena_pdf), "usgs": digest(arguments.usgs_pdf),
            "world-bank": world_bank_input_digest(arguments.world_bank_cache),
        },
        coverages,
    )
    profile_path = arguments.output_dir / "resources-profile.json"
    write_json(profile_path, profile)

    checksum_lines = [
        f"{digest(geometry_path)}  {geometry_path.name}",
        f"{digest(profile_path)}  {profile_path.name}",
        f"{digest(values_path)}  {values_path.name}",
    ]
    (arguments.output_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    print(
        "prepared Stage 6b resources snapshot: "
        f"{len(all_records)} records, {len(mapped_iso3s)} mapped countries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
