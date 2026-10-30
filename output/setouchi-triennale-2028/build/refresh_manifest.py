#!/usr/bin/env python3
"""Refresh the delivery inventory without walking private native cache inputs."""
from pathlib import Path
import json,hashlib,datetime
OUT=Path(__file__).resolve().parents[1]
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
inputs=OUT/'sources/code-inputs.json'
paths={Path(r['path']) for r in json.loads(inputs.read_text())}
paths.update((OUT/'build').glob('*.py'));paths.update((OUT/'build').glob('*.cc'))
paths.update(OUT.parents[1]/'scripts'/n for n in ['fetch-soramame-pm25.py','fetch-cnemc-pm25.py','fetch-openaq-pm25.py','prepare-asia-pm25.py','fetch-itu-fiber.py'])
inputs.write_text(json.dumps([{'path':str(p),'sha256':digest(p)} for p in sorted(paths)],indent=2)+'\n')
p=OUT/'manifest.json';manifest=json.loads(p.read_text())
files={OUT/r['path'] for r in manifest['files']}
for dirname in ['plates','previews','prototypes','proposal','sources/data/cdn','sources/data/anthropocene','sources/research']:
    files.update(p for p in (OUT/dirname).rglob('*') if p.is_file() and not p.is_symlink())
files.update(p for d in ['build','sources'] for p in (OUT/d).iterdir() if p.is_file())
files.update([OUT/'.gitignore', OUT/'.gitattributes', OUT/'GIT-CONTENTS.md', OUT/'build/swarm-runtime/.gitignore',OUT/'build/swarm-runtime/earth-ck-44-22.svg'])
files={p for p in files if not (p.is_relative_to(OUT/'sources/research') and p.suffix=='.js') and p.suffix not in ['.pyc','.pid'] and '__pycache__' not in p.parts}
assert all(p.is_file() for p in files)
assert not any('/swarm-runtime/cache/' in str(p) or '/swarm-runtime/tmp/' in str(p) for p in files)
manifest['files']=[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(files)]
aggregate=json.loads((OUT/'sources/aggregate-pdf-validation.json').read_text())
manifest['plate_count_world']=38
manifest['plate_count_japan']=38
manifest['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest['aggregate_document']={'path':'setouchi-tri-explore-v1.pdf','pages':aggregate['pages'],'bookmarks':aggregate['bookmarks'],'validation':'sources/aggregate-pdf-validation.json'}
manifest['coral_prototypes']={'variants':3,'scales':2,'formats':['svg','pdf','png'],'gallery':'prototypes/coral-reef/index.html'}
manifest['refinement_validation']='sources/refinement-validation.json'
manifest['excluded']='Runtime logs, Inkscape profiles, Python bytecode, process IDs, downloaded application JavaScript used only for source discovery, superseded intermediate files, native swarm participant cache and native swarm render intermediates; no public upload'
p.write_text(json.dumps(manifest,indent=2)+'\n')
rows=[r['sha256']+'  '+r['path'] for r in manifest['files']]
rows.append(digest(p)+'  manifest.json')
(OUT/'SHA256SUMS').write_text('\n'.join(rows)+'\n')
print('Delivery inventory:',len(files),'files; raw native swarm cache excluded')
