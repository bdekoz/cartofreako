#!/usr/bin/env python3
"""Build the current mineral sheets and a color/shape-coded combined overview."""
from copy import deepcopy
from html import escape
import json
import math
import os
from pathlib import Path
import subprocess

from lxml import etree as E
from shapely.geometry import shape

from atlas_review_sheets import ROOT, NS, el, legend, export, font_environment
from cartofreako_style import Projection
from ocean_temperature import digest, write_json

OUT=ROOT/'output/mineral-additions-20261108'
TEMPLATE='resources-mineral-rare-earth-mine-production-2025'
TYPES={'rare-earth-mine-production':('rare-earth',2025),'lithium-mine-production':('lithium',2025),'uranium-mine-production':('uranium',2024)}


def prepare_native(profile_path):
    """Build source SVGs from the checked profile, including after a clean checkout."""
    subprocess.run(['make',str(profile_path.relative_to(ROOT)), 'src.generate/generate-resources'],cwd=ROOT,check=True)
    native=OUT/'native';native.mkdir(parents=True,exist_ok=True)
    inputs=[profile_path,profile_path.parent/'resources-values.json',
            ROOT/'src.generate/generate-resources',ROOT/'generation-style.json']
    fingerprint={str(p.relative_to(ROOT)):digest(p) for p in inputs}
    receipt=native/'inputs.json'
    previous=json.loads(receipt.read_text()) if receipt.exists() else {}
    env=os.environ.copy()
    env.update(NATURAL_EARTH_DIR=str(ROOT/'assets.static/natural-earth/10m-physical-vectors'),
               CARTOFREAKO_LABEL_FONT='Atkinson Hyperlegible')
    for metric,(_,year) in TYPES.items():
        target=native/f'resources-mineral-{metric}-{year}-authagraph-44-19.052559.svg'
        if previous.get('inputs')!=fingerprint or not target.exists() or previous.get('outputs',{}).get(target.name)!=digest(target):
            subprocess.run([str(ROOT/'src.generate/generate-resources'),'resources-mineral','authagraph',str(profile_path),metric],cwd=native,env=env,check=True)
    write_json(receipt,{'inputs':fingerprint,'outputs':{p.name:digest(p) for p in native.glob('*.svg')}})


def frame(scope,stem,title):
    tree=E.parse(str(ROOT/'output/atlas/maps'/scope/'svg'/(TEMPLATE+'.svg')),E.XMLParser(huge_tree=True))
    root=tree.getroot();root.set('data-canonical-plate-id',stem)
    root.set('data-legend-companion',f'../../../legends/{scope}/svg/{stem}-legend.svg')
    for node in root.xpath('./*[local-name()="title"]'):node.text=title
    return root


def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'.gitignore').write_text('/native/\n/maps/\n/legends/\n/work/\n/build.log\n')
    env=font_environment()
    profile_path=ROOT/'assets.static/resources/current-20261108/resources-profile.json'
    prepare_native(profile_path)
    profile=json.loads(profile_path.read_text());values=json.loads((profile_path.parent/'resources-values.json').read_text())['records']
    family=next(f for f in profile['families'] if f['id']=='resources-mineral')
    style=json.loads((ROOT/'generation-style.json').read_text())['resources']
    definitions={m['id']:m for m in family['metrics'] if m['id'] in TYPES}
    records=[];entries=[]
    sources={s['id']:{**s,'period':s['release'],'notes':'Pinned source extract; observation year is in each metric.'} for s in profile['sources'] if s['id'] in {i for m in definitions.values() for i in m['source_ids']}}
    for metric,(kind,year) in TYPES.items():
        m=definitions[metric];stem=f'resources-mineral-{metric}-{year}'
        source=OUT/'native'/(stem+'-authagraph-44-19.052559.svg')
        native=E.parse(str(source),E.XMLParser(huge_tree=True))
        # Native legend class bounds are retained; map labels/values are not
        # inferred from color or replaced with fabricated country observations.
        native_text=[''.join(n.itertext()).strip() for n in native.xpath('//*[local-name()="text"]')]
        write_json(OUT/'data'/(stem+'-legend-extract.json'),native_text)
        rows=[r for r in values if r['metric']==metric]
        palette=style['metric_palettes'][metric]
        lo=min(r['value'] for r in rows);hi=max(r['value'] for r in rows)
        limits=[math.expm1(math.log1p(lo)+(math.log1p(hi)-math.log1p(lo))*i/5) for i in range(6)]
        keys=[(color,f'{limits[i]:,.2f} to {limits[i+1]:,.2f}') for i,color in enumerate(palette)]
        units=m['unit'];title=m['title']+' / '+str(year)
        source_notes=[sources[i]['title']+' — '+sources[i]['url'] for i in m['source_ids']]
        for scope in ('world','japan'):
            root=frame(scope,stem,title)
            for id in ('resources-metadata','resource-country-coverage'):
                old=root.xpath('//*[@id=$id]',id=id)
                new=native.xpath('//*[@id=$id]',id=id)
                assert len(old)==len(new)==1
                old[0].getparent().replace(old[0],deepcopy(new[0]))
            records.append(export(OUT,stem,scope,'map',root,env))
            sheet=legend(stem,title,units+' / country-level mine output / '+scope.title(),
                [{'title':'Production classes','keys':keys+[("#d3d0c6",'Missing or withheld; not zero')],
                  'notes':['Five equal intervals in log1p space. Lower bound included; upper bound goes to the following class, except the maximum.']},
                 {'title':'Coverage','notes':[f'{len(rows)} country values in the published extract.',f'Published-output coverage: {m["coverage"]["output_percent"]:.3f}%.',m['notes']]},
                 {'title':'Mineral identity','keys':[(style['mineral_types'][kind]['color'],kind.replace('-',' ').title(),style['mineral_types'][kind]['shape'])],
                  'notes':['Color is fixed by commodity. Quantity classes apply only within this mineral.','Country fills do not locate mines. The Japan view repeats national observations; it is not island-level production.']}],
                ['Reference years differ across mineral sources. Mine output, reserves, resources, refining and nuclear generating capacity remain separate measures.'],source_notes)
            records.append(export(OUT,stem,scope,'legend',sheet,env))
        entries.append(dict(stem=stem,title=title,period_and_units=f'{year} / {units}',interpretation=m['notes'],source_ids=m['source_ids'],japan_source_ids=m['source_ids'],method='Country choropleth; five log1p quantity classes; fixed mineral hue.',japan='National observations in the existing Japan viewport; not local mine locations.',inputs=[dict(path=str(profile_path.relative_to(ROOT)),sha256=digest(profile_path))],key=[],presentation='Wine/amber, Atkinson Hyperlegible, separate source sheet.'))
    stem='resources-mineral-mine-production-comparison';title='Minerals / mine production'
    geo=json.loads((profile_path.parent/'countries-110m.geojson').read_text())
    anchors={}
    for f in geo['features']:
        geometry=shape(f['geometry']);largest=max(geometry.geoms,key=lambda p:p.area) if geometry.geom_type=='MultiPolygon' else geometry
        point=largest.representative_point();anchors[f['properties']['RESOURCE_A3']]=(point.x,point.y)
    projection=Projection('authagraph',OUT/'work');codes=sorted(anchors);xy=dict(zip(codes,projection.project([anchors[c] for c in codes])))
    for scope in ('world','japan'):
        root=frame(scope,stem,title)
        coverage=root.xpath('//*[@id="resource-country-coverage"]')[0]
        # A neutral country base does not imply zero production.
        for path in root.xpath('//*[@id="resource-country-coverage" or @id="resource-country-coverage-antarctic-inset"]//*[local-name()="path"]'):
            path.set('style','fill:#64555e;fill-opacity:.35;stroke:#fcc553;stroke-opacity:.3;stroke-width:.004')
        for n in root.xpath('//*[@id="resources-metadata"]'):n.getparent().remove(n)
        group=el('g',coverage.getparent(),id='mineral-type-production',data_geometry='country representative points; not mine sites')
        for column,(metric,(kind,year)) in enumerate(TYPES.items()):
            rows=[r for r in values if r['metric']==metric];maximum=max(r['value'] for r in rows);sty=style['mineral_types'][kind]
            for row in rows:
                if row['value']<=0:continue
                x,y=xy[row['iso3']];x+=(column-1)*.48;r=.22*math.sqrt(row['value']/maximum)
                attrs=dict(fill=sty['color'],data_mineral=kind,data_iso3=row['iso3'],data_value=row['value'],data_year=year,data_unit=definitions[metric]['unit'])
                if sty['shape']=='circle':node=el('circle',group,cx=x,cy=y,r=r,**attrs)
                elif sty['shape']=='square':node=el('rect',group,x=x-r,y=y-r,width=2*r,height=2*r,**attrs)
                else:node=el('polygon',group,points=f'{x},{y-r} {x-r},{y+r} {x+r},{y+r}',**attrs)
                el('title',node).text=f'{row["iso3"]}: {row["value"]:,} {definitions[metric]["unit"]}, {year}; {row["state"]}'
        records.append(export(OUT,stem,scope,'map',root,env))
        sections=[]
        for metric,(kind,year) in TYPES.items():
            m=definitions[metric];sty=style['mineral_types'][kind];rows=[r for r in values if r['metric']==metric]
            sections.append(dict(title=kind.replace('-',' ').title()+f' / {year}',keys=[(sty['color'],sty['shape'].title(),sty['shape'])],notes=[m['unit'],f'Largest symbol: {max(r["value"] for r in rows):,}.',f'{len(rows)} country values; {m["coverage"]["output_percent"]:.3f}% of the source output total.',m['notes']]))
        sheet=legend(stem,title,'Color and shape identify the mineral; symbol area compares countries within one mineral.',sections,
            ['Three side-by-side symbols at each country representative point. Symbol area is proportional to production within each mineral, independently normalized to its largest country. Do not compare areas across mineral types.',
             'Rare earths are measured as oxide equivalent; lithium and uranium as contained elements. Years differ. No aggregate mineral tonnage is calculated.',
             'Neutral countries and absent symbols are not zero. Germany’s uranium zero is retained in the table; withheld U.S. lithium and absent Russian uranium remain missing.'],
            [s['title']+' — '+s['url'] for s in sources.values()])
        records.append(export(OUT,stem,scope,'legend',sheet,env))
    entries.append(dict(stem=stem,title=title,period_and_units='Rare earths 2025, lithium 2025, uranium 2024; distinct source units',interpretation='Commodity colors and shapes; country locations; no cross-commodity total.',source_ids=list(sources),japan_source_ids=list(sources),method='Symbol area proportional within each mineral; independently normalized; country representative points.',japan='National producer symbols, not mine locations.',inputs=[],key=[],presentation='Wine/amber, Atkinson Hyperlegible, separate source sheet.'))
    write_json(OUT/'supplement-manifest.json',{'entries':entries,'sources':sources,'records':records})
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Minerals / 8 November 2026</title><style>body{background:#240413;color:#fcc553;font:18px sans-serif;margin:2rem}a{color:inherit}img{width:90%;max-width:1500px}article{margin:3rem 0}</style><h1>Minerals / 8 November 2026</h1>']
    for e in entries:
        html.append('<article id="'+e['stem']+'"><h2>'+escape(e['title'])+'</h2>')
        for scope in ('world','japan'):
            for kind in ('map','legend'):
                r=next(r for r in records if r['stem']==e['stem'] and r['scope']==scope and r['kind']==kind)
                html.append('<p><a href="'+r['svg']+'">'+scope+' '+kind+' SVG</a> · <a href="'+r['pdf']+'">PDF</a></p>')
                if scope=='world':html.append('<img src="'+r['preview']+'" alt="'+escape(e['title']+' '+kind)+'">')
        html.append('</article>')
    (OUT/'index.html').write_text('\n'.join(html)+'</html>\n')
    print(f'Mineral sheets complete: {len(entries)} plate pairs, {len(records)} map/legend sheets')


if __name__=='__main__':main()
