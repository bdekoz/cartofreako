"""Source adapters for isolated, validated current-data editions."""
from datetime import date, datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import tarfile

from dataset import ROOT, DatasetError, atomic_json, digest, file_record, redact, utcnow


def copy_file(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise DatasetError(f"Missing configured local input: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Never share writable cache inodes with an active or historical edition.
    result = subprocess.run(["cp", "--reflink=auto", str(source), str(destination)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode:
        shutil.copyfile(source, destination)


def copy_tree(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_dir():
        raise DatasetError(f"Missing configured local input directory: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True, copy_function=copy_file,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.part"))


def netcdf_days(path, variable):
    from ocean_temperature import NetCDF
    import numpy as np
    with NetCDF(path) as nc:
        units = nc.attributes("time")["units"]
        prefix, origin = units.split(" since ", 1)
        start = datetime.fromisoformat(origin.replace(" UTC", "").strip())
        scale = {"days": 86400, "hours": 3600, "seconds": 1}.get(prefix)
        if scale is None:
            raise DatasetError("Unsupported source time axis: " + units)
        values = nc.read("time")
        days = [(start + timedelta(seconds=float(value) * scale)).date() for value in values]
        if not days or any(b - a != timedelta(days=1) for a, b in zip(days, days[1:])):
            raise DatasetError("Source has a missing, duplicate or unordered daily time axis")
        if nc.shape(variable)[0] != len(days):
            raise DatasetError("Source time axis does not match its data")
        # Reading one cell verifies decoding without loading an entire grid.
        if not np.isfinite(values).all():
            raise DatasetError("Nonfinite source time axis")
        return days


def local_input_paths():
    """Configured pinned inputs required before an expensive acquisition."""
    paths = [ROOT / "assets.static" / name for name in
             ("astronomy/curated-sky.json", "anthropocene", "resources", "cloud-atmosphere/cloud-atmosphere-profile.json",
              "atoll-evidence", "network-swarm", "network-groundstations", "network-infrastructure", "fiber-synthesized",
              "petroleum/normalized/eia-series.csv", "petroleum/normalized/opec-liquids-supply.csv",
              "petroleum/normalized/opec-country-coverage.csv")]
    cable = Path(os.environ.get("SUBMARINE_CABLE_SOURCE", ROOT.parent / "www.submarinecablemap.com"))
    paths += [cable / "web/public/api" / name for name in ("v3.2022", "v3.20260805")]
    paths += [cable / "web/public/api/v3", Path(os.environ.get("INTERNET_EXCHANGE_SOURCE", ROOT.parent / "www.internetexchangemap.com")) / "public/api/v2"]
    paths.append(Path(os.environ.get("NETWORK_INFRASTRUCTURE_CLOUD_SOURCE", ROOT.parent / "cloud_cdn_cache")) / "data")
    cfg_path = Path(os.environ.get("CDN_SOURCE_PROFILE", ROOT / "config/cdn-sources.json"))
    cfg = json.loads(cfg_path.read_text())
    paths += [(cfg_path.parent / cfg[key]).resolve() for key in ("manifest", "city_lookup", "country_registry")]
    if cfg.get("geographic_centerpoints", {}).get("enabled"):
        paths.append((cfg_path.parent / cfg["geographic_centerpoints"]["lookup"]).resolve())
    style = json.loads((ROOT / "generation-style.json").read_text())
    archive = Path(os.environ.get("NATIVE_SWARM_CACHE_ARCHIVE", style["swarm"]["cache_archive"]))
    cached_directory=os.environ.get("NATIVE_SWARM_CACHE_DIRECTORY")
    paths += [Path(cached_directory) if cached_directory else archive if archive.is_absolute() else ROOT / archive,
              Path(os.environ.get("NATIVE_SWARM_GEOLOCATION_DB", ROOT.parent / "geoip-databases/ipinfo/standard_location.mmdb"))]
    paths.append(Path(os.environ.get('NATIVE_SWARM_DATA_ROOT',ROOT.parent/'alpha60-data'))/'torrent'/style['swarm']['collection'])
    return paths


class Sources:
    def __init__(self, edition, requested_as_of, cache, jobs=2):
        self.edition, self.cache = Path(edition), Path(cache)
        self.as_of = datetime.fromisoformat(requested_as_of)
        self.last_day = self.as_of.date() - timedelta(days=1)
        self.jobs = jobs
        self.bindings = {}
        self.records = []
        self.env = {**os.environ, "CCACHE_DISABLE": "1", "DATASET": "legacy", "DATASET_BOUND": "1",
                    "DATA_HTTP_CACHE": str(cache), "DATA_UPDATE_AS_OF": requested_as_of,
                    "DATA_UPDATE_RUN_ID": self.edition.name,
                    "CPC_END_YEAR": "2026",
                    "SOURCE_DATE_EPOCH": str(int(self.as_of.timestamp()))}
        self.env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + self.env.get("PATH", "")
        # Parent Make command-line assignments must not override adapter paths.
        self.env.pop("MAKEFLAGS", None)
        self.env.pop("MAKEOVERRIDES", None)
        self.env.pop("DATASET_MANIFEST", None)

    def run(self, *args, **env):
        print("  " + " ".join(redact(arg) for arg in args), flush=True)
        process = subprocess.Popen([str(arg) for arg in args], cwd=ROOT, env={**self.env, **env},
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(redact(line), end="", flush=True)
        if process.wait():
            raise DatasetError("Source command failed: " + redact(args[0]))

    def make(self, *targets, **variables):
        self.run("make", "--no-print-directory", "-j1", "--no-keep-going", *targets,
                 *[f"{key}={value}" for key, value in variables.items()])

    def validate_profiles(self):
        self.make('build/validate-dataset-native')
        self.run(ROOT/'build/validate-dataset-native',
                 self.edition/self.bindings['ORBITING_PROFILE'],
                 self.edition/self.bindings['ASTRO_DATA_DIR'],
                 self.edition/self.bindings['ANTHROPOCENE_DATA_DIR'],
                 self.edition/self.bindings['RESOURCES_DATA_DIR']/'resources-profile.json',
                 self.edition/self.bindings['CLOUD_ATMOSPHERE_DATA_DIR'],
                 self.edition/self.bindings['NATIVE_SWARM_GEOLOCATION_DB'])

    def directory(self, name):
        path = self.edition / "inputs" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def bind(self, name, path):
        self.bindings[name] = Path(path).relative_to(self.edition).as_posix()

    def record(self, ident, directory, coverage, acquisition="remote-checked", **notes):
        files = [p for p in Path(directory).rglob("*") if p.is_file() and not p.is_symlink()
                 and not any(part == "__pycache__" for part in p.parts)
                 and not p.name.endswith((".part", ".lock"))]
        if not files:
            raise DatasetError("Source produced no inputs: " + ident)
        checked=utcnow()
        self.records.append({"id": ident, "status": "validated", "acquisition": acquisition,
                             "checked_at": checked, "retrieved_at":checked if acquisition=='remote-checked' else None,
                             "coverage": coverage, "notes": notes,
                             "acquisition_receipts":[p.relative_to(self.edition).as_posix() for p in files if p.name.endswith('.receipt.json')],
                             "files": [p.relative_to(self.edition).as_posix() for p in sorted(files)]})

    def astronomy(self):
        target = self.directory("astronomy")
        copy_file(ROOT / "assets.static/astronomy/curated-sky.json", target / "curated-sky.json")
        for name in ("astro-profile.json", "astro-hubble-profile.json"):
            copy_file(ROOT / "assets.static/astronomy" / name, target / name)
            profile = json.loads((target / name).read_text())
            profile["timestamp"] = self.as_of.isoformat().replace("+00:00", "Z")
            atomic_json(target / name, profile)
        self.make("fetch-astro-data", ASTRO_DATA_DIR=target)
        # The Hubble input is a separate dependency, not supplied by the
        # bounded star/exoplanet/small-body fetcher.
        orbital = json.loads((self.edition / self.bindings["ORBITING_PROFILE"]).read_text())
        science = next(g for g in orbital["catalogs"]["groups"] if g["id"] == "science")
        hubble = json.loads((target / "astro-hubble-profile.json").read_text())
        filename = "celestrak-hubble.csv"
        hubble["observer"]["omm_catalog"] = filename
        atomic_json(target / "astro-hubble-profile.json", hubble)
        source = self.edition / Path(self.bindings["ORBITING_PROFILE"]).parent / science["file"]
        import csv
        with source.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = [row for row in reader if row["NORAD_CAT_ID"] == "20580"]
        if len(rows) != 1:
            raise DatasetError("The current science OMM catalog lacks one Hubble record")
        epoch = datetime.fromisoformat(rows[0]["EPOCH"].replace("Z", "+00:00"))
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=timezone.utc)
        age = (self.as_of - epoch).total_seconds()
        if not -6 * 3600 <= age <= 7 * 86400:
            raise DatasetError("Hubble OMM epoch is outside the allowed calculation-time window")
        with (target / filename).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fields)
            writer.writeheader()
            writer.writerows(rows)
        self.bind("ASTRO_DATA_DIR", target)
        self.record("astronomy", target, {"calculation_time": self.as_of.isoformat(),
                    "catalogs": "bounded provider queries; epochs remain source-declared"})

    def orbital(self):
        target = self.edition / "inputs/orbital"
        template = Path(os.environ.get("ORBITING_PROFILE", ROOT / "assets.static/orbital-technosphere/20261109/orbital-technosphere-profile.json"))
        self.run("python3", ROOT / "scripts/refresh-orbiting-snapshot.py", "--template", template,
                 "--output", target, "--timestamp", self.as_of.isoformat().replace("+00:00", "Z"),
                 "--cache", self.cache / "celestrak", "--historical-reference-profile",
                 ROOT / "assets.static/orbital-technosphere/orbital-technosphere-profile.json")
        profile = json.loads((target / "orbital-technosphere-profile.json").read_text())
        self.bind("ORBITING_PROFILE", target / "orbital-technosphere-profile.json")
        self.bind("ORBITING_DATA_DIR", target)
        self.record("orbital", target, {"calculation_time": profile["timestamp"],
                    "nasa": profile["catalogs"]["nasa_ssc_reference"].get("reference_status")},
                    notes="CelesTrak two-hour cache; NASA reference may be historical")

    def natural_earth(self):
        target = self.directory("natural-earth")
        prior = Path(os.environ.get("NATURAL_EARTH_DIR", ROOT / "assets.static/natural-earth/10m-physical-vectors"))
        if prior.is_dir():
            copy_tree(prior, target)
        self.make("fetch-natural-earth-10m", NATURAL_EARTH_DIR=target)
        archive = target / "10m_physical.zip"
        if digest(archive) != "a79cc39162f29832b567de5e24e8770f04a0b997eefd8d067ae4c9df40d21d2a":
            raise DatasetError("Pinned Natural Earth archive checksum mismatch")
        import hashlib
        with zipfile.ZipFile(archive) as bundle:
            for path in target.iterdir():
                if path.suffix in (".shp", ".shx", ".dbf", ".prj"):
                    if path.name not in bundle.namelist() or digest(path) != hashlib.sha256(bundle.read(path.name)).hexdigest():
                        raise DatasetError("Natural Earth payload differs from its pinned archive: " + path.name)
        self.bind("NATURAL_EARTH_DIR", target)
        self.record("natural-earth", target, {"edition": "5.1.1", "role": "pinned basemap"}, "pinned-local")

    def anthropocene(self):
        target = self.directory("anthropocene")
        for path in (ROOT / "assets.static/anthropocene").glob("*-profile.json"):
            copy_file(path, target / path.name)
        self.make("fetch-anthropocene-cpc-data", ANTHROPOCENE_DATA_DIR=target)
        cpc = target / ".raw/cpc"
        manifest_sha = digest(cpc / "SHA256SUMS")
        for year in (2025, 2026):
            days = [set(netcdf_days(cpc / f"{var}.{year}.nc", var)) for var in ("tmax", "tmin")]
            common = sorted(days[0] & days[1])
            if not common or common[0] != date(year,1,1) or (year == 2025 and common[-1] != date(2025,12,31)):
                raise DatasetError(f'CPC lacks the required contiguous product-year support: {year}')
            through = min(common[-1], self.last_day, date(year, 12, 31))
            if through.year != year:
                raise DatasetError(f"No CPC data in requested product year {year}")
            profile_path = target / f"anthropocene-land-temperature-{year}-profile.json"
            profile = json.loads(profile_path.read_text())
            profile["snapshot"] = {"as_of_utc": self.as_of.isoformat().replace("+00:00", "Z"),
                                   "data_through": str(through), "partial_year": through != date(year, 12, 31)}
            profile["source"]["manifest_sha256"] = manifest_sha
            atomic_json(profile_path, profile)
            particulate_path = target / f"anthropocene-particulate-{year}-profile.json"
            particulate = json.loads(particulate_path.read_text())
            particulate["snapshot"] = {"as_of_utc": self.as_of.isoformat().replace("+00:00", "Z"),
                                       "data_through": str(min(date(year, 12, 31), self.last_day)),
                                       "partial_year": self.last_day < date(year, 12, 31)}
            atomic_json(particulate_path, particulate)
        self.make("fetch-anthropocene-data", "prepare-anthropocene-data",
                  "prepare-anthropocene-temperature-data", ANTHROPOCENE_DATA_DIR=target)
        for year in (2025, 2026):
            for stem in ("anthropocene-particulate", "anthropocene-land-temperature"):
                candidate = target / ".prepared" / f"{stem}-{year}.geojson"
                data = json.loads(candidate.read_text())
                if data.get("type") != "FeatureCollection" or not data.get("features"):
                    raise DatasetError("Empty or invalid normalized Anthropocene data")
                destination = target / candidate.name
                copy_file(candidate, destination)
                path = target / f"{stem}-{year}-profile.json"
                profile = json.loads(path.read_text())
                profile["data"]["sha256"] = digest(destination)
                profile["data"]["geojson"] = destination.name
                atomic_json(path, profile)
                self.run("bash", ROOT / "scripts/verify-anthropocene-particulate-data.sh", path, destination)
        self.bind("ANTHROPOCENE_DATA_DIR", target)
        self.record("anthropocene", target, {"cpc": {str(y): json.loads((target / f"anthropocene-land-temperature-{y}-profile.json").read_text())["snapshot"] for y in (2025, 2026)},
                    "particulate": "source-specific eligible dates retained in normalized metadata"})

    def resources(self):
        base, target = self.directory("resources-base"), self.directory("resources")
        self.make("refresh-resources-data", RESOURCES_BASE_DATA_DIR=base, RESOURCES_DATA_DIR=target)
        profile_path = target / "resources-profile.json"
        profile = json.loads(profile_path.read_text())
        profile["name"] = "Current resource observations / " + self.as_of.date().isoformat()
        profile["dataset_resolved_at"] = self.as_of.isoformat()
        # snapshot_as_of and metric reference years describe observations,
        # not the time we downloaded their publications.
        atomic_json(profile_path, profile)
        (target / "SHA256SUMS").write_text("".join(digest(target / name) + "  " + name + "\n" for name in
                    ("resources-profile.json", "resources-values.json", "countries-110m.geojson", "coral-reefs-025deg.geojson")))
        self.bind("RESOURCES_DATA_DIR", target)
        self.record("resources", target, {"metric_periods": {m["id"]: m["reference_period"] for f in profile["families"] for m in f["metrics"]}},
                    configured_annual_publications="Audited release definitions remain explicitly pinned; query sources refreshed")

    def atmosphere(self):
        target = self.directory("atmosphere")
        copy_file(ROOT / "assets.static/cloud-atmosphere/cloud-atmosphere-profile.json", target / "cloud-atmosphere-profile.json")
        self.make("install-jaxa-certificate", "prepare-cloud-atmosphere-data", "verify-cloud-atmosphere-data", CLOUD_ATMOSPHERE_DATA_DIR=target)
        self.bind("CLOUD_ATMOSPHERE_DATA_DIR", target)
        self.bind("CLOUD_ATMOSPHERE_PROFILE", target / "cloud-atmosphere-profile.json")
        self.bind("CLOUD_ATMOSPHERE_GEOJSON", target / ".prepared/cloud-atmosphere-latest.geojson")
        atlas_profile = json.loads((target / "cloud-atmosphere-profile.json").read_text())
        atlas_profile["aggregation"]["h3_resolution"] = 5
        atlas_profile["data"]["prepared_snapshot"] = ".prepared/cloud-atmosphere-atlas.geojson"
        atomic_json(target / "cloud-atmosphere-atlas-profile.json", atlas_profile)
        self.run(ROOT / "src.generate/prepare-cloud-atmosphere", target / "cloud-atmosphere-atlas-profile.json",
                 target / ".raw/cloud-atmosphere-fetch-manifest.json", target / ".prepared/cloud-atmosphere-atlas.geojson")
        atlas_data = json.loads((target / ".prepared/cloud-atmosphere-atlas.geojson").read_text())
        if not atlas_data.get("features") or atlas_data["metadata"]["fixture"]:
            raise DatasetError("The atlas cloud variant has no observed source support")
        self.bind("ATLAS_CLOUD_PROFILE", target / "cloud-atmosphere-atlas-profile.json")
        self.bind("ATLAS_CLOUD_GEOJSON", target / ".prepared/cloud-atmosphere-atlas.geojson")
        fetch = json.loads((target / ".raw/cloud-atmosphere-fetch-manifest.json").read_text())
        self.record("atmosphere", target, {"observations": fetch.get("observations", [])})

    def atoll(self):
        target = self.directory("atoll")
        source = ROOT / "assets.static/atoll-evidence"
        for path in source.iterdir():
            if path.is_file():
                copy_file(path, target / path.name)
        self.make("prepare-atoll-evidence-data", ATOLL_EVIDENCE_DIR=target)
        self.bind("ATOLL_EVIDENCE_DIR", target)
        self.record("atoll", target, {"scope": "configured USGS evidence; publication periods retained"})

    def network(self):
        target = self.directory("network")
        for directory in ("network-swarm", "network-groundstations", "network-infrastructure", "fiber-synthesized"):
            copy_tree(ROOT / "assets.static" / directory, target / directory)
        cable = Path(os.environ.get("SUBMARINE_CABLE_SOURCE", ROOT.parent / "www.submarinecablemap.com"))
        for name in ("v3.2022", "v3.20260805"):
            copy_tree(cable / "web/public/api" / name, target / "cable-inputs" / name)
        self.make("refresh-network-fiber", FIBER_SYNTHESIZED_DATA_DIR=target / "fiber-synthesized",
                  FIBER_SYNTHESIZED_OLD_SOURCE=target / "cable-inputs/v3.2022",
                  FIBER_SYNTHESIZED_NEW_SOURCE=target / "cable-inputs/v3.20260805")
        self.make("prepare-network-swarm-data", NETWORK_SWARM_DATA_DIR=target / "network-swarm")
        cloud = Path(os.environ.get("NETWORK_INFRASTRUCTURE_CLOUD_SOURCE", ROOT.parent / "cloud_cdn_cache"))
        exchange = Path(os.environ.get("INTERNET_EXCHANGE_SOURCE", ROOT.parent / "www.internetexchangemap.com"))
        self.run("bash", ROOT / "scripts/check-network-infrastructure-sources.sh", "topology", cloud, cable, exchange)
        copy_tree(cable / "web/public/api/v3", target / "cable-source/web/public/api/v3")
        copy_tree(exchange / "public/api/v2", target / "exchange-source/public/api/v2")
        copy_tree(cloud / "data", target / "cloud/data")
        for folder in ("schema", "schemas"):
            if (cloud / folder).exists():
                copy_tree(cloud / folder, target / "cloud" / folder)
        revision = subprocess.check_output(["git", "-C", str(cloud), "rev-parse", "HEAD"], text=True).strip()
        atomic_json(target / "cloud/source-checkout.json", {"commit": revision, "source": "https://github.com/bdekoz/cloud_cdn_cache"})
        cfg_path = Path(os.environ.get("CDN_SOURCE_PROFILE", ROOT / "config/cdn-sources.json"))
        cfg = json.loads(cfg_path.read_text())
        manifest = (cfg_path.parent / cfg["manifest"]).resolve()
        if digest(manifest) != cfg["manifest_sha256"]:
            raise DatasetError("Configured CDN provider manifest changed")
        copy_tree(manifest.parent, target / "cdn/source/data")
        cfg["manifest"] = "source/data/" + manifest.name
        for key in ("city_lookup", "country_registry"):
            original = (cfg_path.parent / cfg[key]).resolve()
            if digest(original) != cfg[key + "_sha256"]:
                raise DatasetError("Configured CDN reference changed: " + key)
            copy_file(original, target / "cdn/references" / original.name)
            cfg[key] = "references/" + original.name
        area = cfg.get("geographic_centerpoints", {})
        if area.get("enabled"):
            original = (cfg_path.parent / area["lookup"]).resolve()
            if digest(original) != area["lookup_sha256"]:
                raise DatasetError("Configured CDN area reference changed")
            copy_file(original, target / "cdn/references" / original.name)
            area["lookup"] = "references/" + original.name
        atomic_json(target / "cdn/cdn-sources.json", cfg)
        style = json.loads((ROOT / "generation-style.json").read_text())
        archive = Path(os.environ.get("NATIVE_SWARM_CACHE_ARCHIVE", style["swarm"]["cache_archive"]))
        if not archive.is_absolute():
            archive = ROOT / archive
        cached_directory=os.environ.get('NATIVE_SWARM_CACHE_DIRECTORY')
        if cached_directory:
            for path in Path(cached_directory).glob('*-cumulative-*.json'):
                copy_file(path,target/'native-swarm/unpacked'/path.name)
        else:
            copy_file(archive, target / "native-swarm/cache.tar.xz")
            # Validate the compressed stream and every cumulative JSON before
            # declaring the pinned local archive a usable source.
            cumulative=set()
            with tarfile.open(target/'native-swarm/cache.tar.xz','r|xz') as bundle:
                for member in bundle:
                    name=Path(member.name).name
                    if member.isfile() and '-cumulative-' in name and name.endswith('.json'):
                        if name in cumulative:
                            raise DatasetError('Duplicate cumulative swarm archive member: '+name)
                        cumulative.add(name)
                        unpacked=target/'native-swarm/unpacked'/name
                        unpacked.parent.mkdir(parents=True,exist_ok=True)
                        with bundle.extractfile(member) as stream,unpacked.open('wb') as destination:
                            shutil.copyfileobj(stream,destination)
                        with unpacked.open() as stream:
                            value=json.load(stream)
                        if not isinstance(value,dict) or not value:
                            raise DatasetError('Invalid cumulative swarm document: '+name)
            self.bind("NATIVE_SWARM_CACHE_ARCHIVE", target / "native-swarm/cache.tar.xz")
        documents=list((target/'native-swarm/unpacked').glob('*-cumulative-*.json'))
        if not documents:
            raise DatasetError('The configured native swarm input has no cumulative JSON documents')
        for document in documents:
            with document.open() as stream:
                value=json.load(stream)
            if not isinstance(value,dict) or not value:
                raise DatasetError('Invalid cumulative swarm document: '+document.name)
        collection=style['swarm']['collection']
        data_root=Path(os.environ.get('NATIVE_SWARM_DATA_ROOT',ROOT.parent/'alpha60-data'))
        copy_tree(data_root/'torrent'/collection,target/'native-swarm/data/torrent'/collection)
        if not list((target/'native-swarm/data/torrent'/collection).glob('*.torrent')):
            raise DatasetError('The native swarm collection has no torrent member definitions')
        database = Path(os.environ.get("NATIVE_SWARM_GEOLOCATION_DB", ROOT.parent / "geoip-databases/ipinfo/standard_location.mmdb"))
        copy_file(database, target / "native-swarm/standard_location.mmdb")
        self.make('build/generate-native-swarm')
        self.run(ROOT/'build/generate-native-swarm','--check-inputs',target/'native-swarm/unpacked',collection,
                 a60_PREFIX_DIR=str(Path(self.env.get('ALPHA60_ROOT',ROOT.parent/'alpha60')).resolve()),
                 a60_DATA_DIR=str(target/'native-swarm/data'),a60_METADATA_DIR=str(target/'native-swarm/data'),
                 a60_SAMPLE_DIR=str(target/'native-swarm/unpacked'),
                 a60_GEOLOCATION_DB=str(target/'native-swarm/standard_location.mmdb'))
        self.bind("NETWORK_SWARM_PROFILE", target / "network-swarm/network-swarm-profile.json")
        self.bind("NETWORK_SWARM_DATA_DIR", target / "network-swarm")
        self.bind("FIBER_SYNTHESIZED_DATA_DIR", target / "fiber-synthesized")
        self.bind("NETWORK_GROUNDSTATIONS_DATA_DIR", target / "network-groundstations")
        self.bind("NETWORK_GROUNDSTATIONS_PROFILE", target / "network-groundstations/network-groundstations-profile.json")
        self.bind("NETWORK_INFRASTRUCTURE_DATA_DIR", target / "network-infrastructure")
        self.bind("NETWORK_INFRASTRUCTURE_CLOUD_SOURCE", target / "cloud")
        self.bind("SUBMARINE_CABLE_SOURCE", target / "cable-source")
        self.bind("INTERNET_EXCHANGE_SOURCE", target / "exchange-source")
        self.bind("CDN_SOURCE_PROFILE", target / "cdn/cdn-sources.json")
        self.bind("NATIVE_SWARM_GEOLOCATION_DB", target / "native-swarm/standard_location.mmdb")
        self.bind('NATIVE_SWARM_DATA_ROOT',target/'native-swarm/data')
        self.bind('NATIVE_SWARM_CACHE_DIRECTORY',target/'native-swarm/unpacked')
        self.record("network", target, {"scope": "configured local snapshot/archive inputs; no provider-latest claim", "cloud_commit": revision}, "pinned-local")

    def petroleum(self):
        target = self.directory("petroleum")
        copy_tree(ROOT / "assets.static/petroleum", target)
        subprocess.run(['sha256sum','--check','SHA256SUMS'],cwd=target,check=True,stdout=subprocess.DEVNULL)
        for name in ("eia-series.csv", "opec-liquids-supply.csv", "opec-country-coverage.csv"):
            if not (target / "normalized" / name).is_file():
                raise DatasetError("Missing audited petroleum input: " + name)
        self.bind("PETROLEUM_DATA", target)
        self.record("petroleum", target, {"scope": "audited local EIA/OPEC releases; reported/forecast classes retained"}, "pinned-local")

    def ocean(self):
        target = self.directory("ocean")
        self.run("python3", ROOT / "scripts/fetch-ocean-temperature.py", "--output", target / "cache/oisst",
                 "--end-year", "2026", "--workers", str(self.jobs))
        cache = target / "cache/oisst"
        days = [set(netcdf_days(cache / f"{var}.day.mean.2026.nc", variable))
                for var, variable in (("sst", "sst"), ("icec", "icec"))]
        common = sorted(days[0] & days[1])
        if not common or common[0] != date(2026,1,1):
            raise DatasetError('OISST lacks the current product-year time support')
        through = min(common[-1], self.last_day)
        config = {"schema": "cartofreako-current-ocean-v1", "snapshot_as_of": str(self.as_of.date()),
                  "ocean_cutoff": str(through), "years": [2025, 2026], "baseline": [1991, 2020],
                  "record_baseline_start": 1982}
        atomic_json(target / "ocean-config.json", config)
        self.bind("OCEAN_ROOT", target)
        self.bind("OCEAN_CONFIG", target / "ocean-config.json")
        self.record("ocean", target, {"oisst_available_through": str(common[-1]), "selected_through": str(through)})

    def ocean_context(self):
        from data_http import fetch
        import re
        target = self.edition / self.bindings["OCEAN_ROOT"]
        config = json.loads((target / "ocean-config.json").read_text())
        limit = date.fromisoformat(config["ocean_cutoff"])
        base = "https://www.star.nesdis.noaa.gov/pub/socd/mecb/crw/data/5km/v3.1_op/nc/v1.0/"
        receipts = []
        listing = target / "cache/coral/current-index.html"
        fetch(base + "daily/year-to-date/", listing, self.cache)
        candidates = sorted({value for value in re.findall(r"ct5km_dhw-max-ytd_v3\.1_(\d{8})\.nc", listing.read_text())
                             if datetime.strptime(value, "%Y%m%d").date() <= limit and value.startswith("2026")})
        if not candidates:
            raise DatasetError("CRW does not advertise current-year context within the requested window")
        coral_day = datetime.strptime(candidates[-1], "%Y%m%d").date()
        # Choose a single actual ocean context window; files are not relabeled
        # as current merely because they were downloaded today.
        limit = min(limit, coral_day)
        stamp = limit.strftime("%Y%m%d")
        matched = date(2025, limit.month, limit.day).strftime("%Y%m%d")
        files = [
            (f"annual/ct5km_dhw-max_v3.1_2025.nc", "2025", "annual"),
            (f"daily/year-to-date/ct5km_dhw-max-ytd_v3.1_{stamp}.nc", "2026", "annual"),
            (f"daily/year-to-date_2025/ct5km_dhw-max-ytd_v3.1_{matched}.nc", "2025", "matched")]
        coral = []
        for relative, year, period in files:
            path = target / "cache/coral" / Path(relative).name
            record = fetch(base + relative, path, self.cache)
            coral.append({**record, "path": path.name, "year": int(year), "period": period})
            receipts.append(record)
        atomic_json(target / "cache/coral/manifest.json", coral)
        # JMA is an independent comparison. Discover its real publication
        # boundary instead of substituting a fixed November 7 file.
        jma_base = f"https://www.data.jma.go.jp/goos/data/pub/JMA-product/mgd_sst_glb_D/{limit.year}/"
        listing = target / "research/jma-index.html"
        fetch(jma_base, listing, self.cache)
        available = sorted({value for value in re.findall(r"mgd_sst_glb_D(\d{8})\.txt\.gz", listing.read_text())
                            if datetime.strptime(value, "%Y%m%d").date() <= limit})
        if not available:
            raise DatasetError("JMA comparison has no advertised observation within the selected period")
        name = "mgd_sst_glb_D" + available[-1] + ".txt.gz"
        receipts.append(fetch(jma_base + name, target / "research" / name, self.cache))
        atomic_json(target / "data/context-inputs.json", receipts)
        config.update(ocean_cutoff=str(limit), coral_through=str(coral_day), jma_through=available[-1])
        atomic_json(target / "ocean-config.json", config)
        climate = json.loads((ROOT / "config/ocean-stage-2-20261108.json").read_text())
        climate.update(snapshot_as_of=str(self.as_of.date()), ocean_cutoff=str(limit))
        atomic_json(target / "climate-config.json", climate)
        self.bind("CLIMATE_CONFIG", target / "climate-config.json")
        prepared_cache=self.cache/'ocean-working'
        if prepared_cache.is_dir():
            copy_tree(prepared_cache,target/'work')
        self.run("python3", ROOT / "scripts/prepare-ocean-temperature.py", "--root", target,
                 "--cutoff", str(limit), "--snapshot-date", str(self.as_of.date()))
        self.run("python3", ROOT / "scripts/prepare-coral-thermal-stress.py", "--root", target,
                 RESOURCES_DATA_DIR=str(self.edition / self.bindings["RESOURCES_DATA_DIR"]))
        self.run('python3',ROOT/'scripts/validate-ocean-products.py','--root',target,'--data-only',
                 CLIMATE_CONFIG=str(target/'climate-config.json'))
        copy_tree(target/'work',prepared_cache)
        # The earlier acquisition record now includes its verified daily
        # arrays and normalized products; context gets separate provenance.
        self.records[:] = [r for r in self.records if r["id"] != "ocean"]
        self.record("ocean", target, {"oisst_and_coral_selected_through": str(limit), "jma_through": available[-1]})
        self.record("ocean-context", target / "cache/coral", {"selected_through": str(limit), "source_grid": "CRW original centers; historical reef locator"})

    def india(self):
        import csv
        target = self.directory("india")
        inventory = ROOT / "scripts/data/india-openaq-locations-20261108.json"
        self.run("python3", ROOT / "scripts/fetch-india-openaq-pm25.py", "--output", target / "openaq",
                 "--cache-dir", self.cache / "india-openaq",
                 "--locations-json", inventory, "--start", "2025-01-01", "--end", str(self.last_day),
                 "--refresh-index")
        report = json.loads((target / "openaq/openaq-quality.json").read_text())
        if report.get("failures"):
            raise DatasetError("OpenAQ archive acquisition has failed required station files")
        rows = []
        with gzip.open(target / "openaq/openaq-station-days.csv.gz", "rt") as stream:
            for row in csv.DictReader(stream):
                rows.append({"canonical_id": "openaq:" + row["station_id"], "openaq_id": row["station_id"],
                             "sensor_id": row["sensor_id"],
                             "parameter": "pm25", "date": row["date"], "valid_hours": row["valid_hours"],
                             "mean": row["mean_ug_m3"], "latitude": row["latitude"], "longitude": row["longitude"],
                             "eligible": row["eligible"], "station_name": row["station_name"],
                             "station_type": row["station_type"], "source": row["source"], "unit": "µg/m³"})
        keys = [(r["canonical_id"], r["date"]) for r in rows]
        if not rows or len(set(keys)) != len(keys):
            raise DatasetError("Missing/duplicate current India station-day records")
        path = target / "observations/openaq-station-days.csv.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", newline="") as stream:
            writer = csv.DictWriter(stream, rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        # Use the product's real station/cell crosswalk validator before
        # activation; metadata drift cannot hide in a freshly hashed table.
        import importlib
        normalized,stations=importlib.import_module('prepare-heat-particulate-coexposure').read_observations(path)
        through=json.loads((self.edition/self.bindings['CLIMATE_CONFIG']).read_text())['ocean_cutoff']
        for kind in ('reference','low-cost'):
            if not any(row['station_type']==kind and row['eligible']=='True' and
                       '2026-01-01' <= row['date'] <= through for row in normalized):
                raise DatasetError('India source has no eligible current-year shared-window station-days: '+kind)
        copy_file(inventory, target / "locations.json")
        self.bind("INDIA_OBSERVATIONS", path)
        self.bind("INDIA_METADATA", target / "locations.json")
        self.record("india", target, {"observed_through": report["observed_last_date"],
                    "eligible_through": report["eligible_last_date"], "scope": report["coverage"],
                    "monitor_classes": ["reference", "low-cost"]}, "policy-cache",
                    raw_cache_policy=report.get('raw_cache_policy'),
                    raw_acquisition_counts=report.get('raw_acquisition_counts'))
