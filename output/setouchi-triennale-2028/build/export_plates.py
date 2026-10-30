#!/usr/bin/env python3
"""Export vector PDFs, full 300-dpi PNGs and small previews from every plate."""
from pathlib import Path
import concurrent.futures, json, os, subprocess, sys
OUT=Path(__file__).resolve().parents[1]

def export(svg):
    scope=svg.parents[1].name
    pdf=OUT/'plates'/scope/'pdf'/svg.with_suffix('.pdf').name
    png=OUT/'plates'/scope/'png'/svg.with_suffix('.png').name
    preview=OUT/'previews'/scope/svg.with_suffix('.png').name
    for p in [pdf,png,preview]:p.parent.mkdir(parents=True,exist_ok=True)
    log=OUT/'logs'/f'export-{scope}-{svg.stem}.log'
    config=OUT/'build/inkscape-config'/f'{scope}-{svg.stem}'
    config.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,INKSCAPE_PROFILE_DIR=str(config))
    if svg.stem.startswith('network-swarm-'):
        if any(not p.exists() or p.stat().st_mtime<svg.stat().st_mtime for p in [pdf,png,preview]):
            with log.open('w') as f:
                result=subprocess.run(['python3',str(OUT/'build/export_native_swarm.py'),str(svg)],stdout=f,stderr=subprocess.STDOUT)
            if result.returncode or any(not p.exists() for p in [pdf,png,preview]):
                return {'scope':scope,'stem':svg.stem,'status':'failed','format':'native swarm export'}
        print('Exported',scope,svg.stem,flush=True)
        return {'scope':scope,'stem':svg.stem,'status':'ok'}
    with log.open('w') as f:
        for target,options in [(pdf,['--export-type=pdf','--export-text-to-path']),
                               (png,['--export-type=png','--export-dpi=300','--export-png-color-mode=RGB_8']),
                               (preview,['--export-type=png','--export-width=1600','--export-png-color-mode=RGB_8'])]:
            if target.exists() and target.stat().st_mtime>=svg.stat().st_mtime:continue
            cmd=['inkscape',str(svg),'--export-area-page','--export-background=white','--export-background-opacity=255',*options,'--export-filename='+str(target)]
            f.write(json.dumps(cmd)+'\n');f.flush()
            r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
            if r.returncode or not target.exists() or target.stat().st_size<100:
                print('FAILED',scope,svg.name,target.suffix,flush=True)
                return {'scope':scope,'stem':svg.stem,'status':'failed','format':target.suffix}
    print('Exported',scope,svg.stem,flush=True)
    return {'scope':scope,'stem':svg.stem,'status':'ok'}

if __name__=='__main__':
    scope=sys.argv[1] if len(sys.argv)>1 else '*'
    files=sorted((OUT/'plates').glob(scope+'/svg/*.svg'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(export,files))
    (OUT/'logs'/f'export-{scope.replace("*","all")}-results.json').write_text(json.dumps(results,indent=2)+'\n')
    sys.exit(any(r['status']!='ok' for r in results))
