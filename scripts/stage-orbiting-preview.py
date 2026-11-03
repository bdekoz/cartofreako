#!/usr/bin/env python3
"""Refresh six orbital map/legend preview pairs and their source receipt."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def record(path):
    return {"path": str(path.resolve().relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--product", choices=("global", "observer"), default="global")
    args = parser.parse_args()
    pass_name = "orbital-technosphere-" + args.product
    maps = sorted(p for p in args.build_root.glob("*/svg/" + pass_name + "-*.svg")
                  if not p.stem.endswith("-legend"))
    if len(maps) != 6:
        parser.error(f"expected six {args.product} projection SVGs")
    svgs = [p for m in maps for p in (m, m.with_name(m.stem+"-legend.svg"))]
    pngs = [p.parent.parent / "png" / (p.stem + ".png") for p in svgs]
    for png in pngs:
        with Image.open(png) as image:
            if max(image.size) != 3840:
                parser.error(f"expected a 3840-pixel full render: {png}")
    subprocess.run(["python3", str(ROOT / "scripts/verify-orbiting-layers.py"),
                    "--profile", str(args.profile), *map(str, maps)], check=True)
    profile = json.loads(args.profile.read_text())
    snapshot = profile["timestamp"][:10].replace("-", "")
    output = ROOT / "assets.tot"
    # Preserve the existing global receipt path for downstream links.
    receipt_prefix = "orbital-technosphere" if args.product == "global" else pass_name
    receipt_path = output / (receipt_prefix + "-" + snapshot + ".json")
    products = []
    for svg, png in zip(svgs, pngs):
        directory = output / "products/standard" / svg.parts[-3]
        full = directory / "full" / (svg.stem + ".webp")
        thumb = directory / "thumbnail" / (svg.stem + ".png")
        screen = directory / "screen-1080p/webp" / (svg.stem + ".webp")
        for path in (full, thumb, screen):
            path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(png) as source:
            image = source.convert("RGB")
            image.save(full, "WEBP", quality=90, method=6)
            thumbnail = ImageOps.contain(image, (480, 480), Image.Resampling.LANCZOS)
            thumbnail.save(thumb)
            # Match the screen contract's contain fit and padding color.
            contained = ImageOps.contain(image, (1920, 1080), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1920, 1080), "#f4f5f5")
            canvas.paste(contained, ((1920-contained.width)//2, (1080-contained.height)//2))
            canvas.save(screen, "WEBP", quality=90, method=6)
        products.append({"projection": svg.parts[-3],
                         "kind": "legend" if svg.stem.endswith("-legend") else "map",
                         "sourceSvg": record(svg),
                         "files": [record(path) for path in (full, thumb, screen)]})
    receipt = {"schema": "cartofreako-orbital-preview-update-v1",
               "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "sourceRevision": {"gitCommit": subprocess.check_output(
                   ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   "workingTree": "modified" if subprocess.check_output(
                       ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True).strip() else "clean"},
               "pass": pass_name,
               "timestamp": profile["timestamp"], "sourceProfile": record(args.profile),
               "snapshotChecksums": record(args.profile.parent / "SHA256SUMS"),
               "sourceFiles": [record(ROOT / path) for path in (
                   "src.generate/orbiting-data.h", "src.generate/orbiting-generation.h",
                   "scripts/stage-orbiting-preview.py", "scripts/split-orbiting-plates.py",
                   "generation-style.json", "assets/fonts/atkinson-hyperlegible/provenance.json")],
               "layers": "constellation/name,locpoint",
               "namesVisible": profile["display"].get("show_satellite_names", False),
               "starlinkIds": {"visible": args.product == "global", "fontSizePt": 10},
               "layout": "setouchi-st2-separate-map-legend",
               "namedGroups": [g["constellation"] for g in profile["catalogs"]["groups"] if "constellation" in g],
               "products": products}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    updates = [u for u in manifest.get("updates", []) if u["pass"] != pass_name]
    updates.append({"pass": pass_name, "receipt": receipt_path.name,
                    "timestamp": profile["timestamp"], "artifactCount": len(products)})
    manifest["updates"] = updates
    manifest["artifactCount"] = sum(1 for p in (output / "products").rglob("*.webp") if p.parent.name == "full")
    manifest["storedBytes"] = sum(p.stat().st_size for p in (output / "products").rglob("*") if p.is_file())
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Staged {len(maps)} {args.product} map/legend pairs with thumbnail/full/screen derivatives; {receipt_path}")


if __name__ == "__main__":
    main()
