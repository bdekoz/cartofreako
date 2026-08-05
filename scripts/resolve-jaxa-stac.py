#!/usr/bin/env python3

"""Resolve and download one latest-not-after JAXA Earth static-STAC mosaic."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import sys
import urllib.parse
import urllib.request


USER_AGENT = "cartofreako-cloud-atmosphere/1.0 (+https://github.com/bkoz/cartofreako)"


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks UTC offset: {value}")
    return parsed.astimezone(dt.timezone.utc)


def read_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def links(document: dict, relation: str) -> list[tuple[str, dict]]:
    result: list[tuple[str, dict]] = []
    base = document["_document_url"]
    for link in document.get("links", []):
        if link.get("rel") == relation and link.get("href"):
            result.append((urllib.parse.urljoin(base, link["href"]), link))
    return result


def load(url: str) -> dict:
    document = read_json(url)
    document["_document_url"] = url
    return document


def collect_items(url: str, depth: int = 0) -> list[dict]:
    if depth > 8:
        raise RuntimeError(f"STAC nesting is unexpectedly deep below {url}")
    document = load(url)
    if document.get("type") == "Feature":
        return [document]
    result: list[dict] = []
    for item_url, _ in links(document, "item"):
        result.append(load(item_url))
    child_links = links(document, "child")
    child_ids = [catalog_id(child_url) for child_url, _ in child_links]
    if child_ids and all(identifier.isdigit() for identifier in child_ids):
        # JAXA Earth day/hour catalogs expose overlapping numeric spatial-tile
        # levels. Use only the most subdivided published level so the same
        # observation is not weighted repeatedly during H3 aggregation.
        selected_level = max(int(identifier) for identifier in child_ids)
        child_links = [entry for entry in child_links
                       if int(catalog_id(entry[0])) == selected_level]
    for child_url, _ in child_links:
        result.extend(collect_items(child_url, depth + 1))
    return result


def catalog_id(url: str) -> str:
    path = pathlib.PurePosixPath(urllib.parse.urlparse(url).path)
    return path.parent.name


def eligible_catalogs(document: dict, cutoff_key: str) -> list[str]:
    candidates = [url for url, _ in links(document, "child")
                  if catalog_id(url) <= cutoff_key]
    return sorted(candidates, key=catalog_id, reverse=True)


def item_interval(item: dict) -> tuple[dt.datetime, dt.datetime]:
    properties = item.get("properties", {})
    start_text = properties.get("start_datetime") or properties.get("datetime")
    end_text = properties.get("end_datetime") or properties.get("datetime")
    if not start_text or not end_text:
        raise RuntimeError(f"STAC item lacks an observation interval: {item['_document_url']}")
    return parse_time(start_text), parse_time(end_text)


def select_items(collection: dict, cutoff: dt.datetime) -> list[dict]:
    cutoff_month = cutoff.strftime("%Y-%m")
    for month_url in eligible_catalogs(collection, cutoff_month):
        month = load(month_url)
        # Leaf identifiers are collection-specific: current daily products
        # use DD, while compatible subdaily products can use DD-HH. Sort every
        # available leaf newest first and decide eligibility from STAC
        # observation timestamps, never from a filename convention.
        leaf_urls = sorted(
            (url for url, _ in links(month, "child")),
            key=catalog_id,
            reverse=True,
        )
        for day_url in leaf_urls:
            items = collect_items(day_url)
            eligible = [item for item in items if item_interval(item)[1] <= cutoff]
            if eligible:
                newest_end = max(item_interval(item)[1] for item in eligible)
                return [item for item in eligible
                        if item_interval(item)[1] == newest_end]
    raise RuntimeError(
        f"collection {collection['_document_url']} has no item not after {cutoff.isoformat()}")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def download(url: str, output: pathlib.Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    temporary = output.with_suffix(output.suffix + ".part")
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as sink:
        shutil.copyfileobj(response, sink, length=1024 * 1024)
    if temporary.stat().st_size == 0:
        raise RuntimeError(f"download is empty: {url}")
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--output-directory", required=True, type=pathlib.Path)
    parser.add_argument("--output-json", required=True, type=pathlib.Path)
    arguments = parser.parse_args()

    cutoff = parse_time(arguments.cutoff)
    root = load(arguments.root)
    collection_url = None
    expected = f"/{arguments.collection}/collection.json"
    for child_url, _ in links(root, "child"):
        if urllib.parse.urlparse(child_url).path.endswith(expected):
            collection_url = child_url
            break
    if collection_url is None:
        raise RuntimeError(f"JAXA STAC root has no collection {arguments.collection}")
    collection = load(collection_url)
    selected = select_items(collection, cutoff)

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    files = []
    starts: list[dt.datetime] = []
    ends: list[dt.datetime] = []
    for item_index, item in enumerate(selected):
        start, end = item_interval(item)
        starts.append(start)
        ends.append(end)
        assets = item.get("assets", {})
        data_assets = [(key, asset) for key, asset in assets.items()
                       if "data" in asset.get("roles", ["data"])]
        if not data_assets:
            raise RuntimeError(f"STAC item has no data asset: {item['_document_url']}")
        for asset_key, asset in data_assets:
            asset_url = urllib.parse.urljoin(item["_document_url"], asset["href"])
            basename = pathlib.PurePosixPath(urllib.parse.urlparse(asset_url).path).name
            filename = safe_name(f"{arguments.source}-{item_index:02d}-{asset_key}-{basename}")
            output = arguments.output_directory / filename
            download(asset_url, output)
            rasters = asset.get("je:rasters", {})
            conversion = rasters.get("dn2value", {})
            raw = rasters.get("dn", {})
            files.append({
                "path": filename,
                "source_url": asset_url,
                "sha256": sha256(output),
                "scale": conversion.get("slope"),
                "offset": conversion.get("offset"),
                "nodata": raw.get("nodata"),
                "asset_key": asset_key,
                "item_url": item["_document_url"],
            })

    fetched_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    result = {
        "source": arguments.source,
        "collection": arguments.collection,
        "start_utc": min(starts).isoformat().replace("+00:00", "Z"),
        "end_utc": max(ends).isoformat().replace("+00:00", "Z"),
        "fetched_at_utc": fetched_at.isoformat().replace("+00:00", "Z"),
        "source_url": collection_url,
        "coverage": arguments.coverage,
        "files": files,
    }
    arguments.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # concise command-line failure, no credentials
        print(f"resolve-jaxa-stac: {error}", file=sys.stderr)
        raise SystemExit(1)
