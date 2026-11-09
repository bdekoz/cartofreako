"""Shared scientific paths and periods; legacy dates are an explicit fallback."""
from datetime import date
import json
import os
from pathlib import Path

from dataset import ROOT, binding, context, output


def input_path(name, legacy):
    if os.environ.get("DATASET_MANIFEST"):
        return binding(name)
    return Path(os.environ.get(name, legacy))


def output_path(name, legacy):
    if context(required=False):
        return output(name)
    return Path(legacy)


def atlas_root():
    return output_path("atlas", os.environ.get("ATLAS_OUTPUT", ROOT / "output/atlas"))


def ocean_root():
    return input_path("OCEAN_ROOT", ROOT / "output/ocean-temperature-20261108")


def ocean_output():
    return output_path("anthropocene-optional/ocean", os.environ.get("OCEAN_OUTPUT", ocean_root()))


def climate_output():
    return output_path("anthropocene-optional/climate", os.environ.get("CLIMATE_OUTPUT", ROOT / "output/ocean-temperature-stage-2-20261108"))


def climate_config():
    return input_path("CLIMATE_CONFIG", ROOT / "config/ocean-stage-2-20261108.json")


def cutoff():
    return date.fromisoformat(json.loads(climate_config().read_text())["ocean_cutoff"])


def snapshot_date():
    return date.fromisoformat(json.loads(climate_config().read_text())["snapshot_as_of"])


def matched_cutoff(year=2025):
    day = cutoff()
    try:
        return day.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


def matched_days(year=2025):
    return (matched_cutoff(year) - date(year, 1, 1)).days + 1


def product_months():
    return range(1, cutoff().month + 1)
