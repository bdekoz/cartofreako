#!/usr/bin/env python3
"""Regenerate the 38 reviewed world plates from source."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, os, subprocess, sys

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
STATIC = ROOT / 'assets.static'
DATA = OUT / 'sources/data'
BIN = OUT / 'build'
WORLD = OUT / 'plates/world/svg'
WORLD.mkdir(parents=True, exist_ok=True)
STAMP = '2026-10-29T20:00:00Z'
EPOCH = int(datetime.datetime.fromisoformat(STAMP.replace('Z','+00:00')).timestamp())
SUFFIX = '-authagraph-44-19.052559.svg'
env = dict(os.environ, NATURAL_EARTH_DIR=str(STATIC/'natural-earth/10m-physical-vectors'),
           CARTOFREAKO_LABEL_FONT='atkinson_hyperlegible', SOURCE_DATE_EPOCH=str(EPOCH))

def write_profile(path, changes):
    d=json.loads(path.read_text())
    d.update(changes)
    path.write_text(json.dumps(d,indent=2)+'\n')

def jobs():
    items=[]
    def add(stem, generator, args, title, note, dest=WORLD):
        items.append(dict(stem=stem,title=title,note=note,destination=str(dest),
                          command=[str(BIN/('generate-'+generator)),*map(str,args)]))
    for stem,title in [('geometry','Native geometry'),('graticules','Graticules'),('earth','Earth'),('water','Water'),
                       ('bathymetry-roulette','Bathymetry Roulette'),('bathymetry-hamonshu','Bathymetry Hamonshu')]:
        add(stem,stem,['authagraph'],title,'Natural Earth physical vectors in the current checkout; bathymetry is generalized, not a navigation chart.' if stem not in ['geometry','graticules'] else 'Mathematical projection reference; no observational data.')
    for stem,gen,args,title,note in [
        ('cloud-atmosphere','cloud-atmosphere',['authagraph',DATA/'cloud-atmosphere/cloud-atmosphere-profile.json',DATA/'cloud-atmosphere/.prepared/cloud-atmosphere-latest.geojson'],'Atmosphere','JAXA observations refreshed 2026-10-29. Cloud through Oct 29; precipitation Oct 26; aerosols and shortwave Oct 15. Layers have distinct acquisition times.'),
        ('network-cdn','network-infrastructure',['authagraph',STATIC/'network-infrastructure/network-infrastructure-sites-profile.json',ROOT.parent/'cloud_cdn_cache.bkoz'],'Network CDN sites','Cloud/CDN source records, manifest 21 October 2026; Alpha60 r8 honeycomb and reference symbols. Counts are typed records, not verified active facilities.'),
        ('network-fiber','fiber-synthesized',['authagraph',STATIC/'fiber-synthesized'],'Network Fiber','Cleaned union of 2022 and 2026-08-05 cable snapshots. Routes are schematic; positions are not surveyed cable locations.'),
        ('network-groundstations','network-groundstations',['authagraph',STATIC/'network-groundstations'],'Network Groundstations','Groundstation snapshot 2025-09-02. A location is not evidence of present operation.'),
        ('network-swarm-ge-1080p','network-swarm',[],'Network swarm / Dan Da Dan / 1080p / 4K','Dan Da Dan cumulative cache, September 2025–March 2026; native Alpha60 circles in AuthaGraph. Observations are not unique people.'),
        ('network-swarm-lt-1080p','network-swarm',[],'Network swarm / Dan Da Dan / 720p / SD','Dan Da Dan cumulative cache, September 2025–March 2026; native Alpha60 circles in AuthaGraph. Observations are not unique people.')]:
        add(stem,gen,args,title,note)
    for family in ['particulate','temperature']:
        for year in [2025,2026]:
            stem=f'anthropocene-{family}-{year}'
            adir = DATA/'anthropocene' if family=='particulate' or year==2026 else STATIC/'anthropocene'
            profile=adir/f'{stem}-profile.json'
            d=json.loads(profile.read_text())
            note=f"Local snapshot: {d.get('snapshot',{})}. "
            note += ('Japan MOE and China CNEMC measured PM2.5; selected Indian CPCB/AirNow monitors and a separate AirGradient sensor. Coverage periods vary; at least 18 valid hours per station-day. Concentration thresholds are separate from EPA AQI and smoke.' if family=='particulate' else 'Daily land-temperature record counts on H3 cells; no marine or neighborhood temperature measurement.')
            add(stem,f'anthropocene-{family}',['authagraph',profile,adir/f'{stem}.geojson'],f'{family.title()} {year}',note)
    # Freeze astronomy at one reproducible instant and use the refreshed catalogs.
    for profile in ['astro-profile.json','astro-hubble-profile.json']:
        write_profile(DATA/'astronomy'/profile,{'timestamp':STAMP})
    write_profile(DATA/'orbital-technosphere/orbital-technosphere-profile.json',{'timestamp':STAMP})
    for product,profile,stem,title in [('all-sky','astro-profile.json','astro-all-sky','Astronomy: all sky'),('observer','astro-profile.json','astro-observer-ground-multiband','Astronomy: ground observer'),('observer','astro-hubble-profile.json','astro-observer-hubble','Astronomy: Hubble observer')]:
        add(stem,'astro',['authagraph',product,DATA/'astronomy'/profile],title,'Celestial coordinates. Refreshed astronomy catalogs, calculated at '+STAMP+'. The world ground-observer reference remains San Francisco; the Japan companion uses Setouchi.')
    for product in ['global','observer']:
        add('orbital-technosphere-'+product,'orbiting',['authagraph',product,DATA/'orbital-technosphere/orbital-technosphere-profile.json'],'Orbital Technosphere: '+product,'CelesTrak catalogs retrieved 2026-10-29; SGP4 at '+STAMP+'. Native age/future-epoch filters retained. Observer product uses celestial coordinates.')
    resource_profile=DATA/'resources/resources-profile.json'
    for family in json.loads(resource_profile.read_text())['families']:
        for metric in family['metrics']:
            if metric['status'] not in ['default','released']: continue
            add(f"{family['id']}-{metric['output_tag']}",'resources',[family['id'],'authagraph',resource_profile,metric['id']],metric['title'],f"{metric['reference_period']}; {metric['unit']}. {metric['notes']} Country-level statistics are not Setouchi-specific measurements.")
    custom={'network-cdn':'build_cdn.py','resources-fauna-coral-reef-threat-2011':'build_reef_prototypes.py'}
    for item in items:
        if item['stem'] in custom:item['command']=['python3',str(BIN/custom[item['stem']])]
        if item['stem'].startswith('network-swarm-'):
            item['command']=['python3',str(BIN/'build_swarm.py'),'--band',item['stem'].removeprefix('network-swarm-')]
    # Keep the reviewed title and interpretation alongside each executable path.
    previous=OUT/'sources/generation-plan.json'
    if previous.exists():
        reviewed={i['stem']:i for i in json.loads(previous.read_text())['plates']}
        for item in items:
            if item['stem'] in reviewed:
                item['title']=reviewed[item['stem']]['title'];item['note']=reviewed[item['stem']]['note']
    return items

def run(item):
    p=Path(item['destination'])/(item['stem']+SUFFIX)
    log=OUT/'logs'/('generate-'+item['stem']+'.log')
    if '--resume' in sys.argv and p.is_file() and p.stat().st_size>100:
        return dict(item,status='cached',bytes=p.stat().st_size)
    with log.open('w') as f:
        f.write(json.dumps(item['command'])+'\n'); f.flush()
        r=subprocess.run(item['command'],cwd=item['destination'],env=env,stdout=f,stderr=subprocess.STDOUT)
    result=dict(item,status='ok' if r.returncode==0 and p.is_file() else 'failed',exit_code=r.returncode,
                bytes=p.stat().st_size if p.is_file() else 0)
    print(result['status'],item['stem'],result['bytes'],flush=True)
    return result

if __name__=='__main__':
    items=jobs()
    (OUT/'sources/generation-plan.json').write_text(json.dumps({'instant':STAMP,'dpi':300,'world_inches':[44,19.052559],'plates':items},indent=2)+'\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,items))
    (OUT/'logs/generation-results.json').write_text(json.dumps(results,indent=2)+'\n')
    failures=[r['stem'] for r in results if r['status']=='failed']
    print('World plates:',len(results),'Failures:',failures)
    sys.exit(bool(failures))
