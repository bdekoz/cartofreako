#!/usr/bin/env python3
"""Build and validate all requested native, default-atlas and climate plates."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from zoneinfo import ZoneInfo

from dataset import ROOT, DatasetError, IDENTIFIER, atomic_json, context, data_root, digest, implementation_record, lock, output, redact, utcnow, run_output, publish_output

ACTIVE_STATE = None
ACTIVE_STATE_PATH = None
# These commands run after native map production; changing them cannot bless
# a change to the saved native renderer, Make graph, styles or source config.
POST_NATIVE_METHODS = {'scripts/atlas-optional.py', 'scripts/generate-screen-1080p.mjs',
                       'scripts/setouchi_h3_trials.py', 'scripts/export-setouchi-sheets.py',
                       'scripts/build-current-atlas.py', 'scripts/prepare-marine-heatwaves.py',
                       'scripts/build-ocean-temperature-plates.py', 'scripts/build-ocean-stage-2-plates.py',
                       'scripts/optional_map_annotations.py', 'scripts/validate-ocean-products.py',
                       'scripts/validate-ocean-stage-2.py'}
INDEPENDENT_STUDY_METHODS = {'scripts/build-observer-hourly.py', 'scripts/observer_hourly.py',
                             'scripts/build-observer-instagram.py', 'scripts/observer-hourly-viewer.js'}


def report(message):
    print(datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z') + ': ' + message, flush=True)


def implementation_paths():
    suffixes = {'.py', '.sh', '.cc', '.h', '.json', '.mjs', '.js', '.ttf', '.otf'}
    paths = [p for folder in ('scripts', 'src.generate', 'src.projections', 'src.wasm', 'config', 'assets/fonts')
             for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in suffixes]
    return paths + [p for p in (ROOT/'Makefile', ROOT/'generation-style.json', ROOT/'generation-profile.json',
                                ROOT/'contracts/standard-artifact-manifest-v1.json') if p.is_file()]


def persist_state():
    if ACTIVE_STATE is not None:
        ACTIVE_STATE['updated_at'] = utcnow()
        atomic_json(ACTIVE_STATE_PATH, ACTIVE_STATE)


def run(command):
    if Path(str(command[0])).name in ('make','gmake') and os.environ.get('DATASET_OUTPUT_ROOT'):
        base=Path(os.environ['DATASET_OUTPUT_ROOT'])
        command=[*command, f'GENERATED_DIR={base / "native"}', f'ATLAS_OUTPUT={base / "atlas"}',
                 f'ATLAS_BASE={base / "atlas-base"}', f'DATASET_OUTPUT_ROOT={base}']
    report("atlas-optional: " + redact(" ".join(map(str, command))))
    if ACTIVE_STATE is None:
        subprocess.run([str(arg) for arg in command], cwd=ROOT, check=True)
        return
    phase = (Path(str(command[1])).stem if str(command[0]) == sys.executable else
             next((str(v) for v in command[1:] if not str(v).startswith('-') and '=' not in str(v)), 'command'))
    commands = ACTIVE_STATE.setdefault('commands', [])
    relative = f'logs/{len(commands)+1:03d}-{phase}.log'
    log = ACTIVE_STATE_PATH.parent.parent / relative
    log.parent.mkdir(parents=True, exist_ok=True)
    entry = {'phase': phase, 'argv': [redact(v) for v in command], 'started_at': utcnow(), 'log': relative,
             'status': 'running'}
    commands.append(entry)
    ACTIVE_STATE['phase'] = phase
    persist_state()
    with log.open('w') as stream:
        stream.write('Command: ' + redact(' '.join(map(str, command))) + '\n')
        stream.flush()
        process = subprocess.Popen([str(v) for v in command], cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
        entry['pid'] = process.pid
        persist_state()
        for line in process.stdout:
            line = redact(line)
            stream.write(line)
            stream.flush()
            print(line, end='', flush=True)
        process.stdout.close()
        code = process.wait()
    entry.update(status='passed' if code == 0 else 'failed', returncode=code, finished_at=utcnow())
    persist_state()
    if code:
        raise DatasetError(f'{phase} failed with exit status {code}; see {log}')


def native_reuse_methods(previous, current):
    """Require unchanged native producers, including legacy unrecorded JS/fonts."""
    old_files, new_files = previous['files'], current['files']
    if 'Makefile' not in old_files:
        raise DatasetError('Native recovery requires a recorded Makefile fingerprint')
    compared, changes = {}, []
    for name in sorted(set(old_files) | set(new_files)):
        if name in POST_NATIVE_METHODS or name in INDEPENDENT_STUDY_METHODS:
            if old_files.get(name) != new_files.get(name):
                changes.append(name)
            continue
        expected = old_files.get(name)
        if expected is None:
            # The first build schema omitted JavaScript, runtime helpers and
            # fonts. Compare those against its recorded Git revision, rather
            # than treating an absent fingerprint as permission to reuse.
            revision = previous.get('revision', '')
            if not revision or not all(c in '0123456789abcdef' for c in revision):
                raise DatasetError('Native recovery needs a valid source revision')
            result = subprocess.run(['git', 'show', f'{revision}:{name}'], cwd=ROOT, capture_output=True)
            if result.returncode:
                raise DatasetError('Unrecorded native implementation cannot be verified: ' + name)
            expected = hashlib.sha256(result.stdout).hexdigest()
        if new_files.get(name) != expected:
            raise DatasetError('Native recovery requires unchanged producer bytes: ' + name)
        compared[name] = expected
    return {'verified_producer_files': compared, 'allowed_post_native_or_independent_changes': changes}


def reuse_native(source_id, destination, manifest_path, manifest, identity):
    """Copy verified saved maps into a new run without changing the old record."""
    if not IDENTIFIER.fullmatch(source_id):
        raise DatasetError('Invalid native recovery build ID')
    source = destination.parent / source_id
    if not source.exists():
        source = run_output(manifest, source_id, existing=True)
    if source.resolve() == destination.resolve() or source.is_symlink():
        raise DatasetError('Native recovery needs a distinct, local source run')
    state_path = source / 'validation/build-state.json'
    state_hash = digest(state_path)
    previous = json.loads(state_path.read_text())
    if (previous.get('status') != 'failed' or previous.get('build_id') != source_id
            or previous.get('dataset_id') != manifest['dataset_id']
            or previous.get('manifest_sha256') != digest(manifest_path)):
        raise DatasetError('Native recovery requires a failed run of the exact selected dataset')
    methods = native_reuse_methods(previous['implementation'], identity)
    original = source / 'native'
    paths = sorted(original.rglob('*'))
    if original.is_symlink() or any(p.is_symlink() for p in paths):
        raise DatasetError('Native recovery does not follow symlinked outputs')
    files = [p for p in paths if p.is_file() and p.relative_to(original).parts[0] != 'catalog'
             and not any(part in ('screen-1080p', 'screen-1080p-webp') for part in p.relative_to(original).parts)]
    if not files or any(p.stat().st_size == 0 for p in files):
        raise DatasetError('Native recovery needs nonempty saved output files')
    records = []
    for index, path in enumerate(files):
        relative = path.relative_to(original)
        target = destination / 'native' / relative
        if target.exists():
            raise DatasetError('Native recovery destination already exists: ' + str(target))
        expected = digest(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        if digest(target) != expected or digest(path) != expected:
            raise DatasetError('Native output changed while recovering: ' + str(relative))
        records.append({'path': 'native/' + relative.as_posix(), 'sha256': expected,
                        'bytes': path.stat().st_size, 'source_mtime_ns': path.stat().st_mtime_ns})
        if (index + 1) % 100 == 0:
            report(f'Recovered and hashed {index + 1}/{len(files)} native files')
    if digest(state_path) != state_hash:
        raise DatasetError('Source build record changed during recovery')
    retained = destination / 'sources/reused-native-build-state.json'
    retained.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(state_path, retained)
    receipt = {'schema': 'cartofreako-native-recovery-v1', 'source_build_id': source_id,
               'source_state_sha256': state_hash, 'source_state': str(retained.relative_to(destination)),
               'dataset_id': manifest['dataset_id'], 'manifest_sha256': digest(manifest_path),
               'recovered_at': utcnow(), 'methods': methods, 'files': records}
    path = destination / 'validation/reused-native.json'
    atomic_json(path, receipt)
    report(f'Recovered {len(records)} native files; source run retained unchanged')
    return {'source_build_id': source_id, 'receipt': str(path.relative_to(destination)), 'sha256': digest(path)}


def build_artifacts(base):
    mutable = {base/'validation/build-state.json', base/'validation/full-build.json'}
    return sorted(p for p in base.rglob('*') if p.is_file() and not p.is_symlink() and p not in mutable
                  and p.suffix.lower() in ('.svg', '.gz', '.pdf', '.png', '.webp', '.json', '.html'))


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
    global ACTIVE_STATE, ACTIVE_STATE_PATH
    ACTIVE_STATE = ACTIVE_STATE_PATH = None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, choices=range(1, 33), default=2)
    recovery = parser.add_mutually_exclusive_group()
    recovery.add_argument('--resume', help='Resume a failed build run in the selected edition')
    recovery.add_argument('--reuse-native-from', help='Start a new run using verified native outputs of a failed run')
    recovery.add_argument('--refresh-legends', action='store_true', help='Refresh A3 legends and books from the verified completed build')
    recovery.add_argument('--refresh-maps', nargs='+', choices=('network-fiber', 'network-groundstations',
                          'orbital-technosphere-global', 'orbital-technosphere-observer'),
                          help='Refresh selected atlas map presentation, all legends and books from the verified completed build')
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
                base=run_output(manifest,build_id,existing=bool(args.resume))
                state_path=base/'validation/build-state.json'
                identity=implementation_record(implementation_paths())
                if args.resume:
                    old=json.loads(state_path.read_text())
                    if old.get('legend_refresh'):
                        raise DatasetError('Restart a failed legend refresh with --refresh-legends; its shared maps must not enter a full native rebuild')
                    if old.get('status')=='complete' or old.get('manifest_sha256') != digest(path) or old.get('implementation') != identity:
                        raise DatasetError('Build resume requires the same failed run, dataset bytes and implementation')
                os.environ['DATASET_OUTPUT_ROOT']=str(base)
                os.environ['GENERATED_DIR']=str(base/'native')
                os.environ['ATLAS_OUTPUT']=str(base/'atlas')
                state=old if args.resume else {'dataset_id':ident,'build_id':build_id,'manifest_sha256':digest(path),
                                              'implementation':identity,'started_at':utcnow(),'commands':[]}
                state.update(status='building')
                state.pop('error',None)
                ACTIVE_STATE, ACTIVE_STATE_PATH = state, state_path
                atomic_json(state_path,state)
                print(f'Build run {build_id}; outputs {base}',flush=True)
                if args.reuse_native_from:
                    state['phase']='recover-native'
                    persist_state()
                    state['native_recovery']=reuse_native(args.reuse_native_from,base,path,manifest,identity)
                    persist_state()
            elif args.reuse_native_from:
                raise DatasetError('Native recovery requires a selected immutable dataset')
            if args.refresh_legends or args.refresh_maps:
                if not selected:
                    raise DatasetError('Legend refresh requires a selected completed dataset')
                import refresh_atlas_legends as refresh
                state['phase']='verify-and-reuse-completed-build'
                persist_state()
                state['legend_refresh']=refresh.clone_completed(base,manifest)
                persist_state()
                refresh.refresh_atlas(base, map_stems=args.refresh_maps or ())
                if args.refresh_maps:
                    state['legend_refresh']['map_presentations'] = args.refresh_maps
                run([sys.executable, ROOT/'scripts/export-setouchi-sheets.py', '--delivery', base/'atlas', '--workers', str(args.jobs)])
                run([sys.executable, ROOT/'scripts/check-current-build.py', '--atlas'])
                run([sys.executable, ROOT/'scripts/build-current-books.py'])
                state['legend_refresh']['optional_legends']=refresh.refresh_optional(base,args.jobs)
                run([sys.executable, ROOT/'scripts/validate-ocean-products.py', '--exports-only'])
                run([sys.executable, ROOT/'scripts/validate-ocean-stage-2.py', '--exports-only'])
                state['legend_refresh'].update(refresh.verify_parent(base,state['legend_refresh']))
                atomic_json(base/'validation/legend-refresh.json',state['legend_refresh'])
                persist_state()
            else:
                run(["make", "--no-print-directory", "check-prerequisites"])
                run([sys.executable, ROOT / 'scripts/export-setouchi-sheets.py',
                     '--delivery', output('validation/image-decoder', ROOT/'build/atlas-image-decoder'),
                     '--check-image-decoder'])
                run(["make", "--no-print-directory", "-j1", "--no-keep-going", "all-resilient", f"ASSET_JOBS={args.jobs}"])
                run(["make", "--no-print-directory", "-j1", "--no-keep-going", "atlas", f"ASSET_JOBS={args.jobs}"])
                optional_products(args.jobs)
            if selected:
                # Publication of the build pointer requires validated outputs
                # from every requested group, not just a new data selection.
                base = output("")
                checks=completed_groups(base,manifest)
                artifacts = build_artifacts(base)
                if not artifacts:
                    raise DatasetError("The full build produced no artifacts")
                receipt = {"schema": "cartofreako-full-build-v1", "status": "passed", "dataset_id": ident,
                           "manifest_sha256": digest(path), "completed_at": utcnow(),
                           "build_id":build_id,"validation":checks,"implementation":identity,
                           "native_recovery":state.get('native_recovery'), "legend_refresh":state.get('legend_refresh'),
                           "files": [{"path": str(p.relative_to(base)), "sha256": digest(p)} for p in sorted(artifacts)]}
                if implementation_record(implementation_paths()) != identity:
                    raise DatasetError('Implementation changed during rendering; keep this run as failed evidence and start a new build')
                atomic_json(base / "validation/full-build.json", receipt)
                state.update(status='complete',phase='complete',completed_at=utcnow())
                atomic_json(state_path,state)
                public = publish_output(base,manifest,build_id)
                report('Completed delivery: '+str(public))
        print("Complete native, atlas and optional Anthropocene build: dataset " + ident)
        return 0
    except Exception as error:
        if 'state' in locals():
            state.update(status='failed',error=redact(error))
            atomic_json(state_path,state)
            if args.refresh_legends or args.refresh_maps:
                flags = '--refresh-maps '+' '.join(args.refresh_maps) if args.refresh_maps else '--refresh-legends'
                print("Restart from the completed parent with make atlas-optional ATLAS_OPTIONAL_ARGS='"+flags+"'",file=sys.stderr)
            else:
                print(f"Resume this output run with make atlas-optional ATLAS_OPTIONAL_ARGS='--resume {state['build_id']}'",file=sys.stderr)
        print("atlas-optional: " + redact(error) + "; previous completed build retained", file=sys.stderr)
        return 1
    finally:
        ACTIVE_STATE = ACTIVE_STATE_PATH = None


if __name__ == "__main__":
    sys.exit(main())
