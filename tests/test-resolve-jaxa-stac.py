#!/usr/bin/env python3

"""Exercise latest-not-after selection without network or raster downloads."""

from __future__ import annotations

import copy
import pathlib
import runpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "scripts" / "resolve-jaxa-stac.py"))
BASE = "https://example.invalid/stac/collection/"


def link(relation: str, href: str) -> dict[str, str]:
    return {"rel": relation, "href": href}


def item(identifier: str, start: str, end: str) -> dict:
    return {
        "type": "Feature",
        "id": identifier,
        "properties": {"start_datetime": start, "end_datetime": end},
        "links": [],
    }


documents = {
    BASE + "collection.json": {
        "type": "Collection",
        "links": [link("child", BASE + "2026-08/catalog.json")],
    },
    BASE + "2026-08/catalog.json": {
        "type": "Catalog",
        # Current JAXA daily products use DD leaves. The first leaf is after
        # the cutoff; the next contains the latest eligible two-tile
        # observation.
        "links": [
            link("child", BASE + "2026-08/05/catalog.json"),
            link("child", BASE + "2026-08/04/catalog.json"),
            link("child", BASE + "2026-08/03/catalog.json"),
        ],
    },
    BASE + "2026-08/05/catalog.json": {
        "type": "Catalog",
        "links": [link("item", BASE + "2026-08/05/future.json")],
    },
    BASE + "2026-08/04/catalog.json": {
        "type": "Catalog",
        "links": [
            # Numeric spatial levels overlap; only the most subdivided level
            # is eligible for aggregation.
            link("child", BASE + "2026-08/04/0/catalog.json"),
            link("child", BASE + "2026-08/04/1/catalog.json"),
        ],
    },
    BASE + "2026-08/04/0/catalog.json": {
        "type": "Catalog",
        "links": [link("item", BASE + "2026-08/04/0/coarse.json")],
    },
    BASE + "2026-08/04/1/catalog.json": {
        "type": "Catalog",
        "links": [
            link("item", BASE + "2026-08/04/1/west.json"),
            link("item", BASE + "2026-08/04/1/east.json"),
        ],
    },
    BASE + "2026-08/03/catalog.json": {
        "type": "Catalog",
        "links": [link("item", BASE + "2026-08/03/old.json")],
    },
    BASE + "2026-08/05/future.json": item(
        "future", "2026-08-05T00:00:00Z", "2026-08-05T23:00:00Z"
    ),
    BASE + "2026-08/04/0/coarse.json": item(
        "coarse", "2026-08-04T00:00:00Z", "2026-08-04T23:00:00Z"
    ),
    BASE + "2026-08/04/1/west.json": item(
        "west", "2026-08-04T00:00:00Z", "2026-08-04T23:00:00Z"
    ),
    BASE + "2026-08/04/1/east.json": item(
        "east", "2026-08-04T00:00:00Z", "2026-08-04T23:00:00Z"
    ),
    BASE + "2026-08/03/old.json": item(
        "old", "2026-08-03T00:00:00Z", "2026-08-03T23:00:00Z"
    ),
}


def fake_load(url: str) -> dict:
    document = copy.deepcopy(documents[url])
    document["_document_url"] = url
    return document


select_items = MODULE["select_items"]
select_items.__globals__["load"] = fake_load
cutoff = MODULE["parse_time"]("2026-08-05T04:00:00Z")
selected = select_items(fake_load(BASE + "collection.json"), cutoff)

assert [entry["id"] for entry in selected] == ["west", "east"]
assert MODULE["catalog_id"](BASE + "2026-08/04/catalog.json") == "04"
