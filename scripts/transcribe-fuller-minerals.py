#!/usr/bin/env python3
"""Transcribe Fuller's 1960 mineral-production matrix from page images.

This is a maintainer tool, not part of a normal build.  It expects images made
at 150 DPI from PDF pages 62--73 of the 1963 BFI Phase I report, using the
``cartofreako-minerals-NNN.png`` names produced by ``pdftoppm``.
The page order in the scan is non-linear for the final country block; the
explicit table below records that archival fact.  Every accepted number is
reported in the source with three decimal places and is reconstructed from the
OCR digit sequence.  Ambiguous cells remain null and are listed in the audit.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import json
import math
import pathlib
import re
import subprocess
from typing import Iterable

import cv2


COUNTRIES = (
    "Afghanistan", "Albania", "Algeria", "Angola", "Argentina",
    "Australia", "Austria", "Bechuanaland", "Belgium", "Bolivia",
    "Brazil", "Bulgaria", "Burma", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Ceylon", "Chad", "Chile", "China",
    "Colombia", "Congo (Brazzaville)", "Congo (Leopoldville)", "Cuba",
    "Cyprus", "Czechoslovakia", "Dominican Republic", "Ecuador",
    "El Salvador", "Ethiopia", "Fiji Islands", "Finland", "France",
    "Gabon", "Germany (East)", "Germany (West)", "Ghana", "Greece",
    "Greenland", "Guatemala", "Guinea",
    "Guyana", "Haiti", "Honduras", "Hong Kong", "Hungary", "India",
    "Indonesia", "Iraq", "Iran", "Ireland", "Israel", "Italy",
    "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kenya",
    "Korea (North)", "Korea (South)", "Kuwait", "Laos", "Lebanon",
    "Liberia", "Libya", "Luxembourg", "Malagasy Republic", "Malawi",
    "Malaysia", "Mali", "Mauritania", "Mexico", "Morocco", "Mozambique",
    "Netherlands", "New Caledonia", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "Norway", "Pakistan", "Panama",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Rhodesia", "Romania", "Ruanda-Urundi", "Saudi Arabia", "Senegal",
    "Sierra Leone", "Somali Republic", "South Africa", "Southwest Africa",
    "Spain", "Spanish Sahara", "Sudan", "Surinam", "Swaziland", "Sweden",
    "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Togo",
    "Trinidad and Tobago", "Tunisia", "Turkey", "UAR (Egypt)", "Uganda",
    "United Kingdom", "Upper Volta", "Uruguay", "USA", "USSR", "Venezuela",
    "Viet Nam (North)", "Viet Nam (South)", "Yugoslavia", "Zambia",
)

RESOURCES = (
    "Aluminum", "Antimony", "Asbestos", "Bauxite", "Cement", "Chromite",
    "Coal - anthracite", "Coal - lignite", "Cobalt", "Copper (mined)",
    "Industrial diamonds", "Feldspar", "Fluorspar", "Gold", "Gypsum",
    "Iron ore", "Lead", "Magnesite", "Manganese", "Mercury", "Mica",
    "Molybdenum", "Natural gas", "Nickel", "Nitrogen", "Petroleum",
    "Phosphate rock", "Platinum", "Potash", "Salt", "Silver", "Steel",
    "Sulfur", "Thorium", "Tin (mined)", "Titanium", "Tungsten", "Uranium",
    "Vanadium", "Zinc",
)


@dataclasses.dataclass(frozen=True)
class Page:
    country_block: int
    resource_offset: int
    resource_count: int
    filename: str
    first_center: float
    last_center: float
    left: float
    column_step: float


# Coordinates are in the unscaled scan images.  A missing outer rule is
# represented by an extrapolated coordinate, then clipped during extraction.
PAGES = (
    Page(0, 0, 9, "cartofreako-minerals-062.png", 260.5, 1315, 195, 103.9),
    Page(0, 9, 11, "cartofreako-minerals-063.png", 238, 1301, -2, 103.9),
    Page(0, 20, 9, "cartofreako-minerals-064.png", 351, 1414.5, 258, 104.0),
    Page(0, 29, 11, "cartofreako-minerals-065.png", 244, 1307, -18, 103.3),
    Page(1, 0, 9, "cartofreako-minerals-066.png", 379, 1454, 231, 104.1),
    Page(1, 9, 11, "cartofreako-minerals-067.png", 225.5, 1324, -15, 104.8),
    Page(1, 20, 9, "cartofreako-minerals-068.png", 314.5, 1375, 194, 103.5),
    Page(1, 29, 11, "cartofreako-minerals-069.png", 231, 1306.5, -26, 103.7),
    Page(2, 0, 9, "cartofreako-minerals-072.png", 366, 1420, 222, 104.0),
    Page(2, 9, 11, "cartofreako-minerals-073.png", 227, 1247, -15, 104.7),
    Page(2, 20, 9, "cartofreako-minerals-070.png", 315, 1380.5, 255, 105.1),
    Page(2, 29, 11, "cartofreako-minerals-071.png", 234.5, 1315, -10, 104.8),
)

# Baseline text centers measured from the country-labelled pages.  Affine
# mapping preserves the intentionally thicker section separators on every
# companion commodity page.
ROW_PATTERNS = (
    (260.5, 283, 307.5, 332, 356, 386.5, 411.5, 435.5, 459.5, 484.5,
     514, 539.5, 564, 588.5, 613, 645.5, 670, 694, 718.5, 742.5, 774,
     798.5, 822, 847, 867.5, 901, 925, 949.5, 974, 998.5, 1028.5,
     1053, 1077.5, 1103, 1128.5, 1159, 1183.5, 1208.5, 1233.5, 1258,
     1290, 1315),
    (379, 405.5, 430, 456, 480, 512.5, 537.5, 563.5, 587, 611.5,
     640.5, 665.5, 685.5, 710.5, 735.5, 768, 794, 817.5, 842.5, 866.5,
     895.5, 921.5, 945.5, 971, 996, 1027, 1050.5, 1075.5, 1100, 1125.5,
     1158.5, 1183.5, 1209.5, 1234.5, 1262, 1293, 1318.5, 1342.5,
     1368.5, 1397.5, 1427.5, 1454),
    (366, 391.5, 412, 437, 461.5, 493.5, 518.5, 543, 566, 590, 622,
     645, 670, 693, 718.5, 749.5, 773, 797.5, 822, 846, 878.5, 901,
     927.5, 952.5, 977, 1010.5, 1035.5, 1057.5, 1083, 1106.5, 1137,
     1162, 1186, 1210, 1238.5, 1264.5, 1289, 1312, 1337.5, 1364,
     1395.5, 1420),
)


def _best_rule(line_image, expected: float, horizontal: bool) -> int:
    """Snap an expected grid rule to the strongest nearby long-line signal."""
    limit = line_image.shape[0 if horizontal else 1]
    center = max(0, min(limit - 1, round(expected)))
    candidates = range(max(0, center - 11), min(limit, center + 12))
    if horizontal:
        return max(candidates, key=lambda value: int(line_image[value, :].sum()))
    return max(candidates, key=lambda value: int(line_image[:, value].sum()))


def _png_cell(gray, x0: int, x1: int, y0: int, y1: int) -> bytes:
    # Stay inside the rules instead of removing them morphologically.  The
    # latter also removed long horizontal strokes from this condensed typeface
    # (notably changing 3 to 8 and making otherwise clear cells unreadable).
    x0, x1 = max(0, x0 + 8), min(gray.shape[1], x1 - 8)
    y0, y1 = max(0, y0 + 3), min(gray.shape[0], y1 - 3)
    cell = gray[y0:y1, x0:x1]
    if cell.size == 0:
        return b""
    cell = cv2.copyMakeBorder(cell, 5, 5, 5, 5, cv2.BORDER_CONSTANT,
                              value=255)
    cell = cv2.resize(cell, None, fx=5, fy=5,
                      interpolation=cv2.INTER_CUBIC)
    return cv2.imencode(".png", cell)[1].tobytes()


def _ocr(payload: bytes) -> str:
    if not payload:
        return ""
    result = subprocess.run(
        ("tesseract", "stdin", "stdout", "--psm", "6", "-l", "eng",
         "-c", "tessedit_char_whitelist=0123456789.NA*.,"),
        input=payload, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return ""
    text = result.stdout.decode("utf-8", "replace").strip().replace(" ", "")
    # Dust and isolated rule fragments are commonly recognized as punctuation;
    # they are blank cells, not ambiguous numeric observations.
    if re.fullmatch(r"[.,*]+", text):
        return ""
    return text


def _parse(raw: str):
    upper = raw.upper().replace(",", ".")
    if "NA" in upper or "N.A" in upper:
        return {"status": "not-applicable", "raw_ocr": raw}
    # On bold leader cells Tesseract often recognizes the final asterisk as a
    # fourth fractional digit.  The source grammar always has exactly three
    # fractional digits, so retain the mark without admitting a fourth digit.
    decimal = re.search(r"([0-9]{1,3})\.([0-9]{4})", upper)
    inferred_leader = decimal is not None
    if decimal is not None:
        upper = (upper[:decimal.start()] + decimal.group(1) + "."
                 + decimal.group(2)[:3] + "*" + upper[decimal.end():])
    digits = "".join(re.findall(r"[0-9]", upper))
    if not 3 <= len(digits) <= 6:
        return None
    value = int(digits) / 1000.0
    if not math.isfinite(value) or value > 100:
        return None
    return {
        "status": "reported",
        "percent_world_total": value,
        "leading_producer": "*" in upper or inferred_leader,
        "raw_ocr": raw,
    }


def transcribe(image_directory: pathlib.Path):
    jobs = []
    for page in PAGES:
        path = image_directory / page.filename
        gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"failed to read {path}")
        # Several source pages are cropped through the final table column, so
        # its extrapolated outer rule may legitimately sit just off-canvas.
        required_width = round(page.left + page.column_step
                               * page.resource_count) - 70
        required_height = round(page.last_center) + 15
        if gray.shape[1] < required_width or gray.shape[0] < required_height:
            raise RuntimeError(
                f"{path} is {gray.shape[1]}x{gray.shape[0]}; expected a "
                "150-DPI page render (image is too small for the table grid)")
        pattern = ROW_PATTERNS[page.country_block]
        source_first, source_last = pattern[0], pattern[-1]
        centers = [page.first_center + (value - source_first)
                   * (page.last_center - page.first_center)
                   / (source_last - source_first) for value in pattern]
        xs = [round(page.left + page.column_step * i)
              for i in range(page.resource_count + 1)]
        for row in range(42):
            for column in range(page.resource_count):
                jobs.append((page, row, column,
                             _png_cell(gray, xs[column], xs[column + 1],
                                       round(centers[row] - 12),
                                       round(centers[row] + 12))))

    values = [[None for _ in RESOURCES] for _ in COUNTRIES]
    audit = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        texts = executor.map(_ocr, (job[3] for job in jobs))
        for (page, row, column, _), raw in zip(jobs, texts):
            country_index = page.country_block * 42 + row
            resource_index = page.resource_offset + column
            parsed = _parse(raw)
            values[country_index][resource_index] = parsed
            if raw and parsed is None:
                audit.append({
                    "country": COUNTRIES[country_index],
                    "resource": RESOURCES[resource_index],
                    "raw_ocr": raw,
                })

    # Asterisks are a secondary source mark.  Retain OCR marks, and add the
    # mathematically largest reported share for each column as an audit aid.
    sums = []
    for resource_index, resource in enumerate(RESOURCES):
        reported = [
            (index, item[resource_index]) for index, item in enumerate(values)
            if item[resource_index] is not None
            and item[resource_index]["status"] == "reported"
        ]
        total = sum(item["percent_world_total"] for _, item in reported)
        maximum = max((item["percent_world_total"] for _, item in reported),
                      default=None)
        leaders = []
        if maximum is not None:
            for country_index, item in reported:
                if item["percent_world_total"] == maximum:
                    item["largest_reported_share"] = True
                    leaders.append(COUNTRIES[country_index])
        sums.append({"resource": resource, "reported_sum": round(total, 3),
                     "reported_cells": len(reported), "largest": maximum,
                     "largest_countries": leaders})

    return {
        "schema": "cartofreako-fuller-mineral-matrix-transcription-v1",
        "publication_year": 1963,
        "production_year": 1960,
        "source": {
            "title": "Inventory of World Resources, Human Trends, and Needs",
            "authors": ["R. Buckminster Fuller", "John McHale"],
            "publisher": "World Resources Inventory, Southern Illinois University",
            "url": ("https://www.bfi.org/wp-content/uploads/2014/01/"
                    "wdsd_phase1_doc1_inventory.pdf"),
            "pdf_pages": "62-73",
        },
        "missing_semantics": "null means blank or unverified; never zero",
        "countries": list(COUNTRIES),
        "resources": list(RESOURCES),
        "values": values,
        "audit": {"unparsed_nonblank_cells": audit, "column_sums": sums},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_directory", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    arguments = parser.parse_args()
    result = transcribe(arguments.image_directory)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n",
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
