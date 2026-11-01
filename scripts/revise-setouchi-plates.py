#!/usr/bin/env python3
"""Apply the supplied legend-informatics design without changing map data."""
import argparse
import copy
import hashlib
import html
import io
import json
import re
import shutil
import xml.sax
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import XMLGenerator, quoteattr

from legend_informatics import E, ROOT, NS, WIDTH, HEIGHT, SUFFIX, digest, el, text, save, legend_group, register_fonts
from setouchi_delivery import COMPOSITION, migrate_composition
from cartofreako_style import swarm_label_attributes

REFERENCE = ROOT/'assets.static/legend-informatics/resources-mineral-rare-earth-mine-production-2025-authagraph-44-19.legend-rework.svg'
PALETTES = {
    'wind-capacity':'Cyan', 'nuclear-operating-capacity':'Indigo',
    'petroleum-refinery-throughput':'Brown', 'food-production-index':'Pink',
    'fisheries-production':'Blue', 'forest-area-percent':'Green',
    'rare-earth-mine-production':'Purple', 'population-under-30':'Yellow-green',
    'population-over-60':'Red', 'upper-secondary-attainment':'Mauve',
    'bachelors-attainment':'Orange', 'resident-patent-applications-per-million':'Royal blue',
}
SHAPES = {'path','circle','ellipse','rect','polygon','polyline','line','use'}


class Capture(xml.sax.ContentHandler):
    def __init__(self):
        self.depth=0;self.root=None;self.fragments=[]
    def startElement(self,name,attrs):
        if self.root is None:self.root=dict(attrs)
        if self.depth or (name=='g' and legend_group(attrs.get('id',''))):
            if not self.depth:
                self.buffer=io.StringIO();self.writer=XMLGenerator(self.buffer,encoding='utf-8')
            self.depth+=1;self.writer.startElement(name,dict(attrs))
    def characters(self,value):
        if self.depth:self.writer.characters(value)
    def endElement(self,name):
        if self.depth:
            self.writer.endElement(name);self.depth-=1
            if not self.depth:self.fragments.append(self.buffer.getvalue())


def old_legend(path):
    capture=Capture();xml.sax.parse(str(path),capture)
    if not capture.fragments:return None
    namespaces=' '.join(key+'='+quoteattr(value) for key,value in capture.root.items() if key.startswith('xmlns'))
    wrapper=E.fromstring(('<svg '+namespaces+'>'+capture.fragments[0]+'</svg>').encode())
    return wrapper[0]


def legend_content(group):
    keys=[];notes=[];pending=[]
    if group is None:return keys,notes
    for node in group:
        tag=E.QName(node).localname
        if tag in SHAPES:
            if tag=='rect' and float(node.get('width','0'))>1:
                continue
            pending.append(copy.deepcopy(node))
        elif tag=='text':
            label=html.unescape(' '.join(''.join(node.itertext()).split()))
            if pending:
                keys.append({'label':label,'original_label':label,'shapes':pending});pending=[]
            else:notes.append(label)
    return keys,notes


def symbol(label,color,kind='rect',dash=None):
    if kind=='line':
        node=el('line',x1=0,y1=0,x2=.48,y2=0,stroke=color,stroke_width=.025)
        if dash:node.set('stroke-dasharray',dash)
    elif kind=='circle':node=el('circle',cx=.14,cy=.14,r=.14,fill=color)
    else:node=el('rect',width=.48,height=.28,fill=color)
    return {'label':label,'original_label':label,'shapes':[node]}


def format_number(value):
    value=float(value)
    decimals=2 if 0<abs(value)<10 else 1 if 0<abs(value)<100 else 0
    result=f'{value:,.{decimals}f}'
    return result.rstrip('0').rstrip('.') if decimals else result


def rounded_label(label):
    label=label.replace('<','').replace('>=','≥')
    label=re.sub(r'(?<=\d),(?=\d)','',label)
    return re.sub(r'(?<![\w.])[-+]?\d+(?:\.\d+)?',lambda m:format_number(m.group()),label)


def metadata(item,ordinal,delivery,resources):
    stem=item['stem'];source=delivery/'plates/world/svg'/(stem+SUFFIX+'.svg')
    group=old_legend(source);keys,notes=legend_content(group)
    m={'ordinal':ordinal,'stem':stem,'title_lines':[item['title']], 'units':'',
       'method':'','coverage':'','notes':[], 'keys':keys,'has_legend':group is not None,
       'source_note':item['note'],'legacy_text':notes,'source_svg_sha256':digest(source)}
    metric=next(((family,metric) for family in resources['families'] for metric in family['metrics']
                 if family['id']+'-'+metric.get('output_tag','')==stem),None)
    if metric and stem!='resources-fauna-coral-reef-threat-2011':
        family,metric=metric;m['metric']=metric;m['family']=family['id']
        family_name={'resources-human':'Human resources'}.get(family['id'],family['id'].removeprefix('resources-').title()+' resources')
        m['title_lines']=[family_name,metric['title']]
        period=metric['reference_period'].replace('latest observation from ','').replace('latest reported from ','').replace('latest accepted through ','through ')
        m['units']=metric['unit']+' / '+period
        if metric['id']=='solar-capacity':
            m['method']='Six Yellow–orange capacity classes. Grey: missing'
            m['notes']=['Installed capacity at year end; 1,000 MW = 1 GW. Not electricity generation.']
        else:
            operation='log(1 + value)' if metric.get('scale')=='log1p' else 'value'
            m['method']=f"Five equal intervals of {PALETTES[metric['id']]} using {operation}. Grey: missing"
        for key in keys:key['label']=rounded_label(key['label'])
        coverage=metric['coverage']
        m['coverage']=f"Country statistics; {coverage['covered_countries']} of {coverage['mapped_countries']} mapped countries."
        m['notes'].append(metric['notes'])
        m['keys']=list(reversed(keys))
    elif stem.startswith('petroleum-'):
        m['title_lines']=['Petroleum',item['title'].split(' / ')[0]]
        if 'coverage' in stem:
            m['title_lines']=['Petroleum sources','World Oil Outlook country coverage']
            m['units']='Country coverage / World Oil Outlook 2026'
            m['method']='Brown: country figures indexed. Grey: no separate figure'
            m['coverage']='209 countries and territories retained in the source register.'
            # The first edition retained obsolete "Blue" wording after its palette revision.
            m['keys']=[symbol('Country figures indexed','#865a3d'),symbol('No separate country figure','#d6d6d2'),
                       symbol('Not matched to the report register','#f0ece6')]
            m['notes']=['Source coverage, not production. Regional figures are not allocated to countries.']
        else:
            future='projection' in stem
            m['units']='Million barrels/day / '+('2030 projection' if future else '2025 historical/estimate')
            m['method']='Seven Brown production classes. Grey: no separate value'
            m['coverage']=('14 country projections; OPEC World Oil Outlook 2026.' if future else '36 country observations; EIA October 2026.')
            m['notes']=['Regional totals are not allocated to countries.' if future else 'Total liquids include processing gain. Bahrain is represented by a point.']
            for i,key in enumerate(keys):
                upper=key['label'].removeprefix('≤').strip()
                key['label']=('≤ '+upper) if i==0 else keys[i-1]['original_label'].removeprefix('≤').strip()+' to '+upper
            m['keys']=list(reversed(keys))
    elif stem.startswith('anthropocene-temperature'):
        year=stem[-4:];m['title_lines']=['Anthropocene','New daily high records']
        m['units']='Days per H3 cell / '+('2025 complete year' if year=='2025' else '2026 through 28 October')
        m['method']='Six Yellow–red count classes. Neutral land: zero; blank: unobserved'
        m['coverage']='11,945 covered cells; NOAA CPC land-temperature analysis.'
        m['notes']=['Strict same-calendar-day records; at least 30 years of history.',
                    'Blue outlines show record-low days. Partial-year counts are not annual trends.']
        m['keys']=list(reversed(keys))
    elif stem.startswith('anthropocene-particulate'):
        m['title_lines']=['Anthropocene','Particulate observations']
        m['units']='Source-separated observations / '+stem[-4:]
        m['method']='Marker type identifies the measurement. Blank: unobserved'
        m['coverage']='Measured PM2.5, EPA AQI, sensors and smoke remain distinct.'
        m['notes']=['Monitor/sensor days require at least 18 valid hours. Coverage periods vary.',
                    'A missing exceedance mark does not establish clean air without observed-day coverage.']
        renames={'PM2.5 valid monitor days (at least 18 hours)':'Monitor days · ≥18 valid hours',
                 'Monitor daily PM2.5 >35 µg/m³ days':'Monitor days · PM2.5 >35 µg/m³',
                 'AirGradient valid sensor days (separate)':'AirGradient sensor days',
                 'AirGradient daily PM2.5 >35 µg/m³ days':'Sensor days · PM2.5 >35 µg/m³'}
        for key in keys:key['label']=renames.get(key['label'],key['label'])
    elif stem=='network-fiber':
        m.update(title_lines=['Network fiber','Ocean and land routes'],units='Schematic routes / 2022–2026 snapshots',
                 method='Submarine cables: Black. ITU land fibre: Kelly green',
                 coverage='718 current + 49 historical route features; 37,397 ITU land features.',
                 notes=['2,037 cleaned-union landings. Routes are not surveyed locations.',
                        'Snapshot membership does not establish construction or decommission.',
                        'TeleGeography CC BY-NC-SA 3.0; ITU public BBmaps, 29 October 2026.'])
        m['keys']=[symbol('Submarine · current','#000','line'),symbol('Submarine · planned','#000','line','.08 .05'),
                   symbol('Submarine · 2022 only','#000','line','.025 .035'),symbol('Land · operational','#4cbb17','line'),
                   symbol('Land · construction','#4cbb17','line','.08 .05'),symbol('Land · planned/proposed','#4cbb17','line','.025 .035')]
    elif stem=='network-groundstations':
        m.update(title_lines=['Network','Groundstations'],units='Gateway and point-of-presence records / 2 September 2025',
                 method='Source locations and links; current operation is not established',
                 coverage='618 Starlink gateway/PoP records; Alpha60 data snapshot.',notes=[])
    elif stem.startswith('network-swarm-'):
        high='ge-1080p' in stem
        m.update(title_lines=['Network swarm / Dan Da Dan','1080p / 4K' if high else '720p / lower resolutions'],
                 units='Cumulative observations / 4 September 2025–4 March 2026',
                 method='Circle area follows native weight; member colors at 5% opacity',
                 coverage='Dan Da Dan 210 cache; episodes 210, 211 and 212.',
                 notes=['Repeated observations across torrents are not unique people or traffic volume.'])
        m['keys']=[symbol('2160p / 4K','#ffff00','circle'),symbol('1080p · member colors','#dc55c3','circle')] if high else [symbol('720p · member colors','#287ddc','circle'),symbol('SD · member colors','#28a663','circle')]
    elif stem=='network-cdn':
        m.update(title_lines=['Network infrastructure','Cloud and CDN records'],units='Typed source records / 21 October 2026',
                 method='One hexagon per record; display cap 320 per group',
                 coverage='28,243 records: 13,140 source coordinates; 1,405 references; 13,698 unplotted.',
                 notes=['Solid triangles: approximate city/area references. Dashed: separate locality claims.',
                        '80 separate locality claims. Source records are not a census of active facilities.'])
    elif stem=='cloud-atmosphere':
        m.update(title_lines=['Solar / cloud','Atmosphere'],units='Physical observations / 15–29 October 2026',
                 method='Land outlines above data; fill opacity zero. Blank: unobserved',
                 coverage='JAXA/EORC observations; NASA MODIS shortwave input.',
                 notes=['Cloud retrievals are regional and daytime only. AOD is not smoke or PM2.5.'])
        labels=['Shortwave radiation · W/m² · 15 Oct','Aerosol optical depth · 500 nm · 15 Oct',
                'Precipitation · mm/hour · 26 Oct','Confident-cloud fraction · 29 Oct',
                'Cloud optical thickness · 29 Oct','Cloud-top height · km · 29 Oct','ISCCP cloud type · 29 Oct']
        for key,label in zip(keys,labels):key['label']=label
    elif stem=='resources-fauna-coral-reef-threat-2011':
        m.update(title_lines=['Coral reefs','Integrated local threat'],units='Source-cell threat classes / 2011',
                 method='Radial honeycombs retain the four threat classes; blank: no source cell',
                 coverage='7,215 occupied source cells in 844 groups; WRI Reefs at Risk Revisited.',
                 notes=['One microhex per 0.25° source cell, capped at 61 displayed cells per group.',
                        'Highest source threat per original cell. Symbol area is not reef extent or current condition.'])
        m['keys']=list(reversed(keys))
    elif stem.startswith('bathymetry-'):
        kind=stem.removeprefix('bathymetry-').title()
        m.update(title_lines=['Bathymetry',kind],units='Generalized depth classes / metres',
                 method='Blue ramp and drawing motifs follow the depth class',
                 coverage='Natural Earth physical vectors; these contours are not a navigation chart.',
                 notes=['Curve parameters describe the artwork, not measurement uncertainty.'])
        for key in keys:key['label']=re.sub(r'^(-?\d+) m',lambda n:format_number(n[1])+' m',key['label'])
    if not m['has_legend']:m['notes']=[item['note']]
    if stem.startswith('astro-'):
        observer={'astro-all-sky':'All-sky celestial context','astro-observer-ground-multiband':'Setouchi ground observer',
                  'astro-observer-hubble':'Hubble Space Telescope observer'}[stem]
        m.update(title_lines=['Astronomy',observer],units='Celestial directions / 29 October 2026, 20:00 UTC',
                 method='Selected Gaia, NASA and JPL catalogs; not a census of the sky',
                 coverage='500 bright-star entries; 250 nearby exoplanet entries; curated context.')
        m['notes']=({'astro-all-sky':['The all-sky field is shared celestial context; a geographic Japan crop is undefined.'],
                     'astro-observer-ground-multiband':['Ground observer recalculated for Setouchi (34.45°N, 133.99°E). The world plate uses San Francisco.'],
                     'astro-observer-hubble':['Hubble observer and orbital visibility constraints retained. The Japan locator does not change the observer to the ground.']}[stem])
    elif stem.startswith('orbital-technosphere'):
        m.update(title_lines=['Orbital technosphere','Observer directions' if stem.endswith('observer') else 'Global positions'],
                 units='SGP4 positions / 29 October 2026, 20:00 UTC',
                 method='CelesTrak elements; seven-day age and six-hour future filters',
                 coverage='16 catalog groups retrieved 29 October 2026.')
        m['notes']=['Setouchi observer (34.45°N, 133.99°E); the world observer uses its original reference.' if stem.endswith('observer')
                    else 'Geographic enlargement of the global positions; neighboring countries may appear.',
                    'The historical NASA SSC validation reference was retained after a refresh timeout.']
    return m


def shape_bounds(node):
    tag=E.QName(node).localname
    get=lambda name,default=0:float(node.get(name,default))
    if tag=='rect':return get('x'),get('y'),get('x')+get('width'),get('y')+get('height')
    if tag in ('circle','ellipse'):
        rx=get('r') if tag=='circle' else get('rx');ry=get('r') if tag=='circle' else get('ry')
        return get('cx')-rx,get('cy')-ry,get('cx')+rx,get('cy')+ry
    if tag=='line':return min(get('x1'),get('x2')),min(get('y1'),get('y2')),max(get('x1'),get('x2')),max(get('y1'),get('y2'))
    values=[float(s) for s in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',node.get('points',node.get('d','')))]
    if not values or len(values)%2:raise ValueError('Unsupported legend symbol: '+tag)
    return min(values[::2]),min(values[1::2]),max(values[::2]),max(values[1::2])


def width_in(value,size,role='Regular'):
    from reportlab.pdfbase import pdfmetrics
    return pdfmetrics.stringWidth(value,'Atkinson-'+role,size*72)/72


def wrap(value,size,width,role='Regular'):
    lines=[];line=''
    for word in value.split():
        proposed=(line+' '+word).strip()
        if line and width_in(proposed,size,role)>width:lines.append(line);line=word
        else:line=proposed
    if line:lines.append(line)
    return lines


def make_legend(m,scope,delivery):
    group=el('g',id='legend-informatics',data_plate_ordinal=m['ordinal'],data_legend_style='setouchi-st2')
    lines=list(m['title_lines'])
    if scope=='japan':lines[0]='Japan / '+lines[0]
    if len(lines)==1:lines=['Setouchi atlas',lines[0]]
    size=min(56/72,12.8/max(width_in(line,1,'Bold') for line in lines))
    for index,line in enumerate(lines[:2]):
        text(group,.27,-43.42+index*.63,line,size,font_weight='700',transform='rotate(90)',dominant_baseline='central')
    right=42.38;available=12.25;y=.42
    units=m['units'] or 'AuthaGraph / source periods retained'
    for line in wrap(units,24/72,available,'Bold'):
        text(group,right,y,line,24/72,text_anchor='end',font_weight='700',dominant_baseline='central');y+=.42
    for line in wrap(m['method'],16/72,available):
        text(group,right,y+.04,line,16/72,text_anchor='end',dominant_baseline='central');y+=.30
    coverage=('World dataset: ' if scope=='japan' and m['coverage'] else '')+m['coverage']
    for line in wrap(coverage,12/72,available,'Italic'):
        text(group,right,y+.10,line,12/72,text_anchor='end',font_style='italic',dominant_baseline='central');y+=.25
    y=max(1.95,y+.30);key_size=18/72;gap=.30 if len(m['keys'])>15 else .458333
    for key in m['keys']:
        label=key['label'];fitted=min(key_size,11.6/max(width_in(label,1),.01))
        label_node=text(group,41.70,y,label,fitted,text_anchor='end',dominant_baseline='central',data_original_label=key['original_label'])
        el('title',label_node).text='Original interval or category: '+key['original_label']
        boxes=[shape_bounds(node) for node in key['shapes']]
        x0,y0=min(b[0] for b in boxes),min(b[1] for b in boxes)
        x1,y1=max(b[2] for b in boxes),max(b[3] for b in boxes)
        scale=min(.48/max(x1-x0,.001),.28/max(y1-y0,.001))
        icon=el('g',group,transform=f'translate(42.14 {y}) scale({scale}) translate({-(x0+x1)/2} {-(y0+y1)/2})')
        for node in key['shapes']:
            node=copy.deepcopy(node);node.attrib.pop('id',None);icon.append(node)
        y+=gap
    y+=.25
    notes=list(m['notes'])
    if scope=='japan':
        if 'metric' in m:
            rows=json.loads((delivery/'sources/data/resources/resources-values.json').read_text())['records']
            row=next((r for r in rows if r['iso3']=='JPN' and r['family']==m['family'] and r['metric']==m['metric']['id']),None)
            notes.insert(0,('Japan: '+f"{row['value']:,.2f}".rstrip('0').rstrip('.')+' '+m['metric']['unit']+f" ({row['year']}).") if row else 'Japan: no reported country value. Missing is not zero.')
        if m['stem'].startswith('astro-') or m['stem']=='orbital-technosphere-observer':
            notes.insert(0,'Celestial directions, not a geographic Japan crop. The locator provides Setouchi context.')
        else:notes.append('Japan detail includes neighboring countries; it is not a Japan-only total.')
        if not m['stem'].startswith('network-swarm-'):
            notes.append('Yellow point: conceptual Setouchi reference (34.45°N, 133.99°E); venue unconfirmed.')
        if m['stem'].startswith('anthropocene-particulate'):
            records=json.loads((delivery/'sources/data/anthropocene/pm25-enrichment-quality.json').read_text())['country_coverage']
            row=next(r for r in records if r['year']==int(m['stem'][-4:]) and r['country']=='JPN' and r['instrument_class']=='monitor')
            notes.insert(0,f"Japan: {row['stations']:,} reporting monitors; {row['h3_cells']} H3 cells. {row['first_date']} to {row['last_date']}.")
    note_width=4.6 if scope=='world' else available
    for note in notes:
        for line in wrap(note,14/72,note_width):
            text(group,right,y,line,14/72,text_anchor='end');y+=.28
        y+=.10
    if y>17.8:raise ValueError('Legend exceeds page: '+m['stem'])
    text(group,right,18.55,f"Sources and class definitions: plate bibliography {m['ordinal']:02d}",12/72,text_anchor='end',font_style='italic')
    if scope=='japan' and (m['stem'].startswith('astro-') or m['stem']=='orbital-technosphere-observer'):
        text(group,right,10.35,'Japan / geographic locator',16/72,text_anchor='end')
    return group


class Rewrite(xml.sax.ContentHandler):
    def __init__(self,stream,legend,scope,stem=''):
        self.writer=XMLGenerator(stream,encoding='utf-8');self.stream=stream
        self.legend=legend;self.scope=scope;self.stack=[];self.skip=0
        self.hash=hashlib.sha256();self.counts=Counter()
        self.swarm=stem.startswith('network-swarm-');self.label_depth=0
    def startDocument(self):self.writer.startDocument()
    def startElement(self,name,attrs):
        a=dict(attrs);depth=len(self.stack)
        rejected=(name=='g' and (legend_group(a.get('id','')) or a.get('id')=='detail-notes'))
        if self.scope=='japan' and depth==1 and name in ('text','polygon'):rejected=True
        if self.skip or rejected:
            self.skip+=1;self.stack.append(False);return
        if depth==0:a['data-legend-style']='setouchi-st2'
        if self.swarm and name=='g' and 'text-geolocation-text' in a.get('id',''):
            self.label_depth=depth+1
        if self.label_depth and name in ('text','tspan'):
            a=swarm_label_attributes(a)
        if name in SHAPES:
            self.hash.update(json.dumps([name,sorted(a.items())],separators=(',',':')).encode());self.counts[name]+=1
        self.writer.startElement(name,a);self.stack.append(True)
    def characters(self,value):
        if not self.skip:self.writer.characters(value)
    def endElement(self,name):
        keep=self.stack.pop()
        if len(self.stack)<self.label_depth:self.label_depth=0
        if not keep:self.skip-=1;return
        if not self.stack:self.stream.write(E.tostring(self.legend,encoding='unicode'))
        self.writer.endElement(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028')
    parser.add_argument('--output',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--update-manifest',action='store_true',help='Merge a selected revision into the complete existing manifest')
    args=parser.parse_args();register_fonts()
    args.output.mkdir(parents=True,exist_ok=True)
    if not (args.output/'.gitignore').exists():
        (args.output/'.gitignore').write_text('# Local generated print and review delivery.\n*\n')
    migrate_composition(args.output)
    plan=json.loads((args.delivery/'sources/generation-plan.json').read_text())
    resources=json.loads((args.delivery/'sources/data/resources/resources-profile.json').read_text())
    catalog=[];records=[]
    for ordinal,item in enumerate(plan['plates'],1):
        if args.only and item['stem'] not in args.only:continue
        m=metadata(item,ordinal,args.delivery,resources)
        encoded={k:v for k,v in m.items() if k!='keys'}
        encoded['keys']=[{**{k:v for k,v in key.items() if k!='shapes'},'symbols':[E.tostring(node,encoding='unicode') for node in key['shapes']]} for key in m['keys']]
        catalog.append(encoded)
        for scope in ('world','japan'):
            name=item['stem']+SUFFIX+('-japan' if scope=='japan' else '')+'.svg'
            source=args.delivery/'plates'/scope/'svg'/name;target=args.output/COMPOSITION/'plates'/scope/'svg'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            if not m['has_legend'] and scope=='world':
                shutil.copyfile(source,target)
                record={'scope':scope,'stem':item['stem'],'status':'no-existing-legend','source_sha256':digest(source),'output_sha256':digest(target)}
            else:
                legend=make_legend(m,scope,args.delivery)
                with target.open('w') as stream:
                    handler=Rewrite(stream,legend,scope,item['stem']);xml.sax.parse(str(source),handler)
                record={'scope':scope,'stem':item['stem'],'status':'revised','source_sha256':digest(source),
                        'output_sha256':digest(target),'cartography_sha256':handler.hash.hexdigest(),'cartography_shape_counts':dict(handler.counts)}
            records.append(record);print(scope,item['stem'],record['status'],flush=True)
    directory=args.output/'sources';directory.mkdir(parents=True,exist_ok=True)
    tag='-selected' if args.only else ''
    (directory/('legend-catalog'+tag+'.json')).write_text(json.dumps(catalog,indent=2)+'\n')
    (directory/('legend-revision'+tag+'.json')).write_text(json.dumps({'reference':str(REFERENCE.relative_to(ROOT)),
        'reference_sha256':digest(REFERENCE),'records':records},indent=2)+'\n')
    if args.only and args.update_manifest:
        existing=json.loads((directory/'legend-catalog.json').read_text())
        updates={r['stem']:r for r in catalog}
        (directory/'legend-catalog.json').write_text(json.dumps([updates.get(r['stem'],r) for r in existing],indent=2)+'\n')
        existing=json.loads((directory/'legend-revision.json').read_text())
        updates={(r['stem'],r['scope']):r for r in records}
        existing['records']=[updates.get((r['stem'],r['scope']),r) for r in existing['records']]
        (directory/'legend-revision.json').write_text(json.dumps(existing,indent=2)+'\n')


if __name__=='__main__':main()
