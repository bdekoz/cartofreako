"""Revalidate remote objects without modifying previously selected editions."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import re
from urllib.error import HTTPError
from urllib.request import Request

from dataset import DatasetError, atomic_json, digest, lock, redact, utcnow
from data_http_policy import Pacer, Progress, open_response


def fetch(url, destination, cache, *, minimum_interval=0, headers=None, range_size=None, same_day_cache=False):
    if range_size is not None and range_size <= 0:
        raise DatasetError("HTTP byte-range size must be positive")
    cache = Path(cache)
    key = hashlib.sha256((url + json.dumps(headers or {}, sort_keys=True)).encode()).hexdigest()
    with lock(cache / "http", key):
        return _fetch(url, destination, cache, minimum_interval=minimum_interval,
                      headers=headers, range_size=range_size, same_day_cache=same_day_cache)


def _download(url, headers, temporary, partial_receipt, range_size, pacer, progress):
    partial = json.loads(partial_receipt.read_text()) if partial_receipt.exists() else {}
    offset = temporary.stat().st_size if temporary.exists() else 0
    validator = partial.get("etag") or partial.get("last_modified")
    if not (validator and offset and (not partial.get("bytes") or offset < partial["bytes"])):
        offset = 0
    progress.offset, progress.total = offset, partial.get('bytes') if offset else None
    progress.report('resuming' if offset else 'checking provider', force=True)
    while True:
        request_headers = dict(headers)
        if offset:
            request_headers.pop("If-None-Match", None)
            request_headers.pop("If-Modified-Since", None)
            request_headers["If-Range"] = validator
        if range_size:
            end = offset + range_size - 1
            if offset and partial.get("bytes"):
                end = min(end, partial["bytes"] - 1)
            request_headers["Range"] = f"bytes={offset}-{end}"
        elif offset:
            request_headers["Range"] = f"bytes={offset}-"
        with open_response(Request(url, headers=request_headers), pacer, progress) as response:
            expected = response.headers.get("Content-Length")
            total = int(expected) if expected else None
            etag = response.headers.get("ETag")
            # Weak ETags cannot establish a byte-range identity.
            if etag and etag.startswith("W/"):
                etag = None
            last_modified = response.headers.get("Last-Modified")
            current_validator = etag or last_modified
            if response.status == 206:
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                if (not match or "Range" not in request_headers or int(match[1]) != offset
                        or not offset <= int(match[2]) < int(match[3])
                        or (range_size and int(match[2]) > end)
                        or (offset and (current_validator != validator
                            or (partial.get("bytes") and int(match[3]) != partial["bytes"])))):
                    temporary.unlink(missing_ok=True)
                    partial_receipt.unlink(missing_ok=True)
                    raise DatasetError("Provider returned an inconsistent partial response")
                total = int(match[3])
                response_end = int(match[2]) + 1
                if expected is not None and int(expected) != response_end - offset:
                    raise DatasetError("Provider returned an inconsistent byte-range length")
                if response_end < total and not current_validator:
                    raise DatasetError("Provider returned a byte range without an identity validator")
            else:
                offset = 0  # Changed If-Range identity or server without range support.
                response_end = total
            partial = {"etag": etag, "last_modified": last_modified, "bytes": total}
            atomic_json(partial_receipt, partial)
            progress.offset, progress.total = offset, total
            with open(temporary, "ab" if offset else "wb") as stream:
                while block := response.read(1024 * 1024):
                    stream.write(block)
                    progress.offset += len(block)
                    progress.report()
                stream.flush()
                os.fsync(stream.fileno())
            size = temporary.stat().st_size
            if not size or (response_end is not None and size != response_end):
                raise DatasetError("Empty or incomplete download; validated partial retained: " + redact(url))
            if total is None or size == total:
                progress.report('download complete', force=True)
                return {"etag": response.headers.get("ETag"), "last_modified": last_modified}
            offset, validator = size, current_validator


def _fetch(url, destination, cache, *, minimum_interval=0, headers=None, range_size=None, same_day_cache=False):
    cache, destination = Path(cache), Path(destination)
    key = hashlib.sha256((url + json.dumps(headers or {}, sort_keys=True)).encode()).hexdigest()
    receipts = cache / "http"
    receipts.mkdir(parents=True, exist_ok=True)
    receipt = receipts / (key + ".json")
    previous = json.loads(receipt.read_text()) if receipt.exists() else None
    prior = cache / "sha256" / previous["sha256"] if previous else None
    if previous and (not prior.is_file() or digest(prior) != previous["sha256"]):
        raise DatasetError("Corrupted HTTP cache object: " + key)
    checked = datetime.now(timezone.utc)
    age = ((checked - datetime.fromisoformat(previous["checked_at"])).total_seconds()
           if previous else float("inf"))
    request_headers = {"User-Agent": "cartofreako-data-update/1.0", **(headers or {})}
    run_id = os.environ.get('DATA_UPDATE_RUN_ID')
    same_run = bool(run_id and previous and previous.get('checked_run') == run_id)
    same_day = bool(same_day_cache and previous and age >= 0
                    and datetime.fromisoformat(previous['checked_at']).astimezone(timezone.utc).date() == checked.date())
    if previous and (same_run or same_day or 0 <= age < minimum_interval):
        policy = 'same-run' if same_run else 'same-utc-day' if same_day else 'minimum-interval'
        record = {**previous, "acquisition": "policy-cache", "cache_policy": policy}
        progress = Progress(url)
        progress.offset = progress.total = record['bytes']
        progress.report(f'using validated cache ({policy}); provider checked {record["checked_at"]}', force=True)
    else:
        if previous:
            if previous.get("etag"):
                request_headers["If-None-Match"] = previous["etag"]
            if previous.get("last_modified"):
                request_headers["If-Modified-Since"] = previous["last_modified"]
        temporary = receipts / (key + ".part")
        partial_receipt = receipts / (key + ".partial.json")
        progress = Progress(url)
        pacer = Pacer(url, cache)
        try:
            try:
                validators = _download(url, request_headers, temporary, partial_receipt, range_size, pacer, progress)
                size, sha = temporary.stat().st_size, digest(temporary)
                obj = cache / "sha256" / sha
                obj.parent.mkdir(parents=True, exist_ok=True)
                if obj.exists():
                    if digest(obj) != sha:
                        raise DatasetError("Corrupted immutable HTTP object")
                else:
                    os.replace(temporary, obj)
                    obj.chmod(0o444)
                record = {"url": redact(url), "sha256": sha, "bytes": size,
                          "retrieved_at": utcnow(), "checked_at": utcnow(),
                          **validators, "acquisition": "remote-checked"}
            except HTTPError as error:
                if error.code != 304 or previous is None:
                    error.close()
                    raise
                error.close()
                record = {**previous, "checked_at": utcnow(), "acquisition": "remote-checked"}
            record['checked_run'] = run_id
            atomic_json(receipt, record)
        except Exception as error:
            retained = temporary.stat().st_size if temporary.exists() else 0
            raise DatasetError(f"Remote freshness check failed for {progress.name}; "
                               f"{retained:,} partial bytes retained: " + redact(error)) from None
        else:
            temporary.unlink(missing_ok=True)
            partial_receipt.unlink(missing_ok=True)
    obj = cache / "sha256" / record["sha256"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".download")
    shutil.copyfile(obj, temporary)
    temporary.replace(destination)
    atomic_json(destination.with_name(destination.name + ".receipt.json"), record)
    return record
