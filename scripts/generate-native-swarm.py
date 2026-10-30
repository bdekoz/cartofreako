#!/usr/bin/env python3
"""Render separate native Alpha60 resolution plates with Cartofreako projections."""
from cartofreako_style import ROOT, STYLE, Projection, E, digest, el, txt
from pathlib import Path
import argparse, collections, copy, fcntl, json, os, re, shutil, subprocess, tarfile, xml.sax
from xml.sax.saxutils import XMLGenerator

class Native(xml.sax.ContentHandler):
    def __init__(self, stream, band):
        self.writer=XMLGenerator(stream,encoding='utf-8');self.band=band
        self.depth=0;self.active=False;self.styles={};self.ids=collections.Counter();self.count=0
    def startElement(self,name,attrs):
        self.depth+=1;a=dict(attrs)
        if self.depth==2:
            self.active=a.get('id','').startswith('vector-peer-clouds-') or a.get('id')=='text-geolocation-text'
        if not self.active:return
        if name=='image' or name=='g' and 'transform' in a:
            raise ValueError('Unexpected transform or raster in native cloud groups')
        if 'id' in a:
            old=a['id'];self.ids[old]+=1;a['id']=self.band+'-'+old.replace('/','-')+'-'+str(self.ids[old])
        if name=='circle':
            style=a.pop('style')
            if 'fill-opacity:0.05' not in style.replace(' ',''):raise ValueError('Native circle opacity changed')
            a['class']=self.styles.setdefault(style,'native-c'+str(len(self.styles)));self.count+=1
        self.writer.startElement(name,a)
    def endElement(self,name):
        if self.active:self.writer.endElement(name)
        if self.depth==2:self.active=False
        self.depth-=1
    def characters(self,text):
        if self.active:self.writer.characters(text)

def extract(archive, work):
    fingerprint=digest(archive);cache=work/'cache'/fingerprint
    marker=cache/'complete.json'
    if marker.exists():return cache, fingerprint
    cache.mkdir(parents=True,exist_ok=True);names=set()
    with tarfile.open(archive,'r|xz') as stream:
        for entry in stream:
            name=Path(entry.name).name
            if not entry.isfile() or '-cumulative-' not in name or not name.endswith('.json'):continue
            if name in names:raise ValueError('Duplicate cumulative cache filename: '+name)
            names.add(name)
            with stream.extractfile(entry) as source,(cache/name).open('wb') as target:shutil.copyfileobj(source,target)
    if not names:raise ValueError('Archive contains no cumulative documents')
    marker.write_text(json.dumps(dict(archive=str(archive),sha256=fingerprint,documents=len(names)))+'\n')
    return cache, fingerprint

def compose(source,output,projection,band,collection,period):
    title=STYLE['swarm']['partitions'][band];geo=projection.geography()
    land=copy.deepcopy(geo.xpath('//*[@id="land"]')[0])
    for node in land.xpath('.//*[local-name()="path"]'):
        node.attrib.pop('style',None);node.set('fill','white');node.set('stroke','none')
    coast=copy.deepcopy(geo.xpath('//*[@id="terrestrial-coastline"]')[0])
    doc=el('svg',width=f'{projection.width}in',height=f'{projection.height}in',viewBox=f'0 0 {projection.width} {projection.height}',role='img',data_projection=projection.name,data_resolution_partition=band,data_native_units_per_inch=96)
    el('title',doc).text=f'Network swarm / {collection} / {title} / {projection.info["title"]}'
    el('desc',doc).text='Native cumulative downloader observations; original member colours and weighted radii, 5% fill opacity. Observations are not unique people or traffic.'
    el('rect',doc,width=projection.width,height=projection.height,fill='#f2f2f2')
    doc.append(land)
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.svg.tmp')
    with temporary.open('w') as stream:
        stream.write(E.tostring(doc,encoding='unicode')[:-6]+'<g transform="scale(0.010416666666666666)">')
        handler=Native(stream,band);xml.sax.parse(str(source),handler)
        stream.write('</g>'+E.tostring(coast,encoding='unicode'))
        legend=el('g',id='swarm-legend',transform=f'translate({projection.width-44} {projection.height-19.052559})')
        el('rect',legend,x=28.5,y=16.25,width=15.2,height=2.5,fill='white',fill_opacity=.94)
        txt(legend,29,16.8,'NETWORK SWARM / '+collection.upper(),.4,font_weight='bold')
        txt(legend,29,17.25,title+' / '+projection.info['title'],.32,font_weight='bold')
        lines=['Cumulative observations · '+period[0]+'–'+period[1],
               'Native circle area follows weight; 5% opacity; member colours.',
               '2160p: yellow; 1080p: pink/purple.' if band=='ge-1080p' else '720p: blue; SD: green.',
               'Observations across torrents are not unique people or traffic.']
        for i,line in enumerate(lines):txt(legend,29,17.64+i*.26,line,.19)
        stream.write(E.tostring(legend,encoding='unicode'))
        stream.write('<style>'+''.join('.'+name+'{'+style+'}' for style,name in handler.styles.items())+'</style></svg>')
    temporary.replace(output)
    return dict(band=band,projection=projection.name,native_circles=handler.count,fill_opacity=.05,source_svg_sha256=digest(source),output=output.name)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projection',default=STYLE['default_projection'])
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--collection',default=STYLE['swarm']['collection'])
    parser.add_argument('--cache-archive',type=Path,default=(ROOT/STYLE['swarm']['cache_archive']).resolve())
    parser.add_argument('--cache-directory',type=Path)
    parser.add_argument('--geolocation-database',type=Path,default=ROOT.parent/'geoip-databases/ipinfo/standard_location.mmdb')
    parser.add_argument('--work-dir',type=Path,default=ROOT/'build/default-styles/swarm')
    args=parser.parse_args();args.work_dir=args.work_dir.resolve();args.work_dir.mkdir(parents=True,exist_ok=True)
    projection=Projection(args.projection,args.work_dir/args.projection)
    raw=projection.work/'native';raw.mkdir(parents=True,exist_ok=True)
    with (args.work_dir/'render.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if args.cache_directory:
            cache=args.cache_directory.resolve();archive_sha=None
        else:
            if not args.cache_archive.is_file():raise FileNotFoundError('Native swarm cache unavailable; supply --cache-archive or --cache-directory: '+str(args.cache_archive))
            cache,archive_sha=extract(args.cache_archive,args.work_dir)
        documents=sorted(cache.glob('*-cumulative-*.json'))
        if not documents:raise ValueError('No cumulative cache documents: '+str(cache))
        binary=ROOT/'build/generate-native-swarm'
        signature=dict(binary_sha256=digest(binary),projection=args.projection,collection=args.collection,
                       archive_sha256=archive_sha,geolocation_sha256=digest(args.geolocation_database),
                       documents=[(p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in documents])
        marker=raw/'render-inputs.json';serialized=json.dumps(signature,sort_keys=True)
        complete=marker.exists() and marker.read_text()==serialized
        complete=complete and all(len(list(raw.glob('*-downloader-cumulative-'+band+'-render*.svg')))==1 for band in STYLE['swarm']['partitions'])
        if not complete:
            # Changing the collection or torrent count changes native filenames.
            # Remove only this adapter's stale, regenerable raw partitions.
            for previous in raw.glob('*-downloader-cumulative-*-render*.svg'):previous.unlink()
            env=dict(os.environ,a60_PREFIX_DIR=os.environ.get('ALPHA60_ROOT',str(ROOT.parent/'alpha60')),a60_DATA_DIR=str(ROOT.parent/'alpha60-data'),a60_GEOLOCATION_DB=str(args.geolocation_database.resolve()))
            print('Rendering native Alpha60 cumulative cache in '+args.projection,flush=True)
            subprocess.run([str(binary),args.projection,str(cache),args.collection,str(raw)],cwd=args.work_dir,env=env,check=True)
            marker.write_text(serialized)
        dates=[re.search(r'-cumulative-(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})\.json$',p.name) for p in documents]
        if not all(dates):raise ValueError('Cache document lacks an observation period')
        period=[min(m[1] for m in dates),max(m[2] for m in dates)]
        receipts=[]
        for band in STYLE['swarm']['partitions']:
            sources=list(raw.glob('*-downloader-cumulative-'+band+'-render*.svg'))
            if len(sources)!=1:raise ValueError('Native renderer did not produce exactly one '+band+' partition')
            output=args.output_dir/('network-swarm-'+band+projection.suffix+'.svg')
            receipt=compose(sources[0],output,projection,band,args.collection,period)
            receipt.update(collection=args.collection,period=period,cache_directory=str(cache),cache_archive_sha256=archive_sha,cache_documents=len(documents),style_sha256=digest(ROOT/'generation-style.json'))
            output.with_suffix('.provenance.json').write_text(json.dumps(receipt,indent=2)+'\n');receipts.append(receipt)
            print('Rendered',output.name,receipt['native_circles'],'native circles',flush=True)
        # Keep the existing gallery/artifact identifier as a 1080p/4K alias.
        high=args.output_dir/('network-swarm-ge-1080p'+projection.suffix+'.svg')
        alias=args.output_dir/('network-swarm'+projection.suffix+'.svg')
        if alias.exists():alias.unlink()
        os.link(high,alias)
        receipt=dict(receipts[0],output=alias.name,alias_of=high.name)
        alias.with_suffix('.provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
        return receipts

if __name__=='__main__':main()
