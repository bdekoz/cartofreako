#!/usr/bin/env python3
"""Build and validate all requested native, default-atlas and climate plates."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from dataset import ROOT, DatasetError, IDENTIFIER, atomic_json, context, data_root, digest, implementation_record, lock, output, redact, utcnow


def run(command):
    if Path(str(command[0])).name in ('make','gmake') and os.environ.get('DATASET_OUTPUT_ROOT'):
        base=Path(os.environ['DATASET_OUTPUT_ROOT'])
        command=[*command, f'GENERATED_DIR={base / "native"}', f'ATLAS_OUTPUT={base / "atlas"}',
                 f'ATLAS_BASE={base / "atlas-base"}', f'DATASET_OUTPUT_ROOT={base}']
    print("atlas-optional: " + " ".join(map(str, command)), flush=True)
    subprocess.run([str(arg) for arg in command], cwd=ROOT, check=True)


def writable_product_copy(source,destination):
    """Materialize input products without inheriting immutable file modes."""
    destination=Path(destination)
    temporary=destination.with_name(destination.name+'.source-copy')
    temporary.unlink(missing_ok=True)
    shutil.copyfile(source,temporary)
    temporary.chmod(0o644)
    temporary.replace(destination)
    return destination


def completed_groups(base, dataset):
    """Never advance build-current after a partial/reduced optional render."""
    checks={}
    for name, relative in (('atlas','atlas/sources/current-validation.json'),
                           ('ocean','anthropocene-optional/ocean/validation.json'),
                           ('climate','anthropocene-optional/climate/validation.json')):
        receipt=base/relative
        value=json.loads(receipt.read_text())
        if value.get('status') != 'passed' or value.get('data_only'):
            raise DatasetError('A required full output validation is missing: '+name)
        checks[name]={'path':relative,'sha256':digest(receipt)}
    for book in json.loads((base/'atlas/sources/current-books.json').read_text())['books']:
        if digest(base/'atlas'/book['path']) != book['sha256']:
            raise DatasetError('Atlas book changed after assembly')
    if checks.keys() != {'atlas','ocean','climate'}:
        raise DatasetError('Missing product group')
    if json.loads((base/'anthropocene-optional/ocean/preview-manifest.json').read_text()).get('provisional_sst_only'):
        raise DatasetError('The reduced SST preview is not a complete optional build')
    return checks


def optional_products(jobs):
    selected = context(required=False)
    if selected:
        from dataset import binding
        ocean = output("anthropocene-optional/ocean")
        source = binding("OCEAN_ROOT")
        ocean.mkdir(parents=True, exist_ok=True)
        # Read-only large working arrays/cache stay in the immutable edition;
        # product arrays are copied because the review builder writes receipts.
        for name in ("work", "cache", "research"):
            destination = ocean / name
            if not destination.exists():
                destination.symlink_to(source / name, target_is_directory=True)
            elif not destination.is_symlink() or destination.resolve() != (source / name).resolve():
                raise DatasetError("Optional output has an incompatible source directory: " + str(destination))
        shutil.copytree(source / "data", ocean / "data", dirs_exist_ok=True,copy_function=writable_product_copy)
        climate = output("anthropocene-optional/climate")
        climate.mkdir(parents=True, exist_ok=True)
        path, manifest = selected
        relevant = {p for s in manifest['sources'] if s['id'] in ('ocean','ocean-context','india','anthropocene') for p in s['files']}
        atomic_json(climate / "data/stage-2-acquisition.json", {"dataset_id": manifest['dataset_id'],
            "inputs": [{"file": os.path.relpath(path.parent / row['path'], climate), "sha256": row['sha256']}
                       for row in manifest['files'] if row['path'] in relevant]})
    else:
        if os.environ.get("DATASET") != "legacy":
            raise DatasetError("A current dataset must be selected before building optional plates")
    run([sys.executable, ROOT / "scripts/compare-ocean-periods.py"])
    run([sys.executable, ROOT / "scripts/compare-jma-oisst.py"])
    run([sys.executable, ROOT / "scripts/plot-ocean-comparisons.py"])
    run([sys.executable, ROOT / "scripts/build-ocean-temperature-plates.py"])
    run([sys.executable, ROOT / "scripts/validate-ocean-products.py"])
    run(["make", "--no-print-directory", "-j1", "--no-keep-going", "prepare-ocean-stage-2"])
    run(["make", "--no-print-directory", "-j1", "--no-keep-going", "render-ocean-stage-2", "check-ocean-stage-2"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, choices=range(1, 33), default=2)
    parser.add_argument('--resume', help='Resume a failed build run in the selected edition')
    args = parser.parse_args()
    try:
        os.environ["ASSET_JOBS"] = str(args.jobs)
        os.environ.setdefault("OMP_NUM_THREADS", str(args.jobs))
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
        temporary = ROOT / "build/tmp"
        temporary.mkdir(parents=True, exist_ok=True)
        os.environ["TMPDIR"] = str(temporary)
        os.environ["MPLCONFIGDIR"] = str(temporary / "matplotlib")
        run([sys.executable, ROOT / "scripts/check-atlas-prerequisites.py"])
        selected = context(required=False)
        if selected:
            path, manifest = selected
            ident = manifest["dataset_id"]
        else:
            if os.environ.get("DATASET") != "legacy":
                raise DatasetError("Select a validated edition or choose DATASET=legacy")
            ident = "legacy"
        with lock(data_root(), "build-" + ident):
            if selected:
                build_id=args.resume or utcnow().replace('-','').replace(':','').lower()+'-'+uuid.uuid4().hex[:12]
                if not IDENTIFIER.fullmatch(build_id):
                    raise DatasetError('Invalid build resume ID')
                base=ROOT/'output/data-editions'/ident/'builds'/build_id
                state_path=base/'validation/build-state.json'
                implementation_paths=[p for folder in ('scripts','src.generate','src.projections','config') for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.sh','.cc','.h','.json')]+[ROOT/'Makefile',ROOT/'generation-style.json']
                identity=implementation_record(implementation_paths)
                if args.resume:
                    old=json.loads(state_path.read_text())
                    if old.get('status')=='complete' or old.get('manifest_sha256') != digest(path) or old.get('implementation') != identity:
                        raise DatasetError('Build resume requires the same failed run, dataset bytes and implementation')
                os.environ['DATASET_OUTPUT_ROOT']=str(base)
                os.environ['GENERATED_DIR']=str(base/'native')
                os.environ['ATLAS_OUTPUT']=str(base/'atlas')
                state={'dataset_id':ident,'build_id':build_id,'manifest_sha256':digest(path),'implementation':identity,'status':'building'}
                atomic_json(state_path,state)
                print(f'Build run {build_id}; outputs {base}',flush=True)
            run(["make", "--no-print-directory", "check-prerequisites"])
            run(["make", "--no-print-directory", "-j1", "--no-keep-going", "all-resilient", f"ASSET_JOBS={args.jobs}"])
            run(["make", "--no-print-directory", "-j1", "--no-keep-going", "atlas", f"ASSET_JOBS={args.jobs}"])
            optional_products(args.jobs)
            if selected:
                # Publication of the build pointer requires validated outputs
                # from every requested group, not just a new data selection.
                base = output("")
                checks=completed_groups(base,manifest)
                artifacts = [p for p in base.rglob("*") if p.is_file() and not p.is_symlink()
                             and p.suffix.lower() in (".svg", ".pdf", ".png", ".json", ".html")]
                if not artifacts:
                    raise DatasetError("The full build produced no artifacts")
                receipt = {"schema": "cartofreako-full-build-v1", "status": "passed", "dataset_id": ident,
                           "manifest_sha256": digest(path), "completed_at": utcnow(),
                           "build_id":build_id,"validation":checks,"implementation":identity,
                           "files": [{"path": str(p.relative_to(base)), "sha256": digest(p)} for p in sorted(artifacts)]}
                if implementation_record(implementation_paths) != identity:
                    raise DatasetError('Implementation changed during rendering; keep this run as failed evidence and start a new build')
                atomic_json(base / "validation/full-build.json", receipt)
                state['status']='complete'
                atomic_json(state_path,state)
                atomic_json(data_root() / "build-current.json", {"dataset_id": ident, "build_id":build_id,
                            "output":str(base),"receipt": str(base / "validation/full-build.json"),
                            "sha256": digest(base / "validation/full-build.json")})
        print("Complete native, atlas and optional Anthropocene build: dataset " + ident)
        return 0
    except Exception as error:
        if 'state' in locals():
            state.update(status='failed',error=redact(error))
            atomic_json(state_path,state)
            print(f"Resume this output run with make atlas-optional ATLAS_OPTIONAL_ARGS='--resume {state['build_id']}'",file=sys.stderr)
        print("atlas-optional: " + redact(error) + "; previous completed build retained", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
