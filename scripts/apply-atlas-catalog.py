#!/usr/bin/env python3
"""Apply current names/groups/default selection to a local atlas, retaining source provenance."""
import argparse
from copy import deepcopy
from html import escape
import importlib
import json
import os
from pathlib import Path
import shutil

from lxml import etree as E

from atlas_catalog import ROOT, PATH, catalog, default_entries, lookup
from ocean_temperature import digest, write_json


def apply(root):
    bank=lookup()
    bookpath=root/'plate-source-bibliography.json'
    book=json.loads(bookpath.read_text())
    sourcepath=root/'sources/separate-sheets.json'
    source=json.loads(sourcepath.read_text())
    supplement_root=ROOT/'output/mineral-additions-20261108'
    supplement_path=supplement_root/'supplement-manifest.json'
    if not supplement_path.exists():
        raise FileNotFoundError('Build the authorized mineral additions before applying the current atlas catalog: '+str(supplement_path))
    supplement=json.loads(supplement_path.read_text())
    replacement={e['stem'] for e in supplement['entries']}
    book['entries']=[e for e in book['entries'] if e['stem'] not in replacement]+supplement['entries']
    book['sources'].update(supplement['sources'])
    source['records']=[r for r in source['records'] if r['stem'] not in replacement]
    for r in supplement['records']:
        for field in ('svg',):
            path=supplement_root/r[field]
            assert digest(path)==r[field+'_sha256']
            target=root/r[field];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
        source['records'].append(r)
    book['entries']=default_entries(book['entries'])
    ordinals={e['stem']:e['ordinal'] for e in book['entries']}
    book['catalog']={'path':str(PATH.relative_to(ROOT)),'sha256':digest(PATH),'reviewed_on':'2026-11-08'}
    records=[];selected_inputs={}
    for old in source['records']:
        plate=bank[old['stem']]
        if not plate['default']:
            continue
        row=deepcopy(old);oldstem=row['stem'];newstem=plate['id']
        target=root/row['svg'].replace(oldstem,newstem)
        selected=plate.get('selected_presentation')
        source_svg=root/row['svg']
        if selected:
            for item in selected['inputs']:
                assert digest(ROOT/item['path'])==item['sha256'],item['path']
                selected_inputs[item['path']]=item
            source_svg=ROOT/selected['root']/('maps' if row['kind']=='map' else 'legends')/row['scope']/(newstem+('' if row['kind']=='map' else '-legend')+'.svg')
        if oldstem!=newstem or row['kind']=='legend' or selected:
            tree=E.parse(str(source_svg),E.XMLParser(huge_tree=True))
            tree.getroot().set('data-canonical-plate-id',newstem)
            tree.getroot().set('data-legacy-source-stem',oldstem)
            if selected:
                assert tree.getroot().get('data-h3-resolution')==str(selected['h3_resolution'])
                tree.getroot().set('data-selected-presentation',selected['settings'])
                companion=root/('legends' if row['kind']=='map' else 'maps')/row['scope']/'svg'/(newstem+('-legend' if row['kind']=='map' else '')+'.svg')
                tree.getroot().set('data-legend-companion' if row['kind']=='map' else 'data-map-companion',os.path.relpath(companion,target.parent))
                for node in tree.xpath('//*[local-name()="image"]'):
                    key='{http://www.w3.org/1999/xlink}href' if node.get('{http://www.w3.org/1999/xlink}href') else 'href'
                    href=node.get(key)
                    if href and not href.startswith('data:'):node.set(key,os.path.relpath((source_svg.parent/href).resolve(),target.parent))
                row.update(presentation='selected-setouchi-h3r5',presentation_source=str(source_svg.relative_to(ROOT)),
                           presentation_source_sha256=digest(source_svg),source=str(source_svg),geometry_audit=None)
            for node in tree.iter():
                for key in ('data-legend-companion','data-map-companion'):
                    if node.get(key):node.set(key,node.get(key).replace(oldstem,newstem))
                if E.QName(node).localname=='title' and node.getparent() is tree.getroot():node.text=plate['title']
                if E.QName(node).localname=='text' and node.text:
                    if 'land-temperature' in newstem and node.text=='Anthropocene':node.text='Anthropocene / land temperature'
                    if newstem.startswith('resources-energy-petroleum') and node.text in ('Petroleum','Petroleum sources'):node.text='Energy resources / petroleum'
                    if newstem=='anthropocene-coral-reef-threat-2011' and node.text=='Coral reefs':node.text='Anthropocene / coral reefs'
            if row['kind']=='legend':
                nodes=tree.xpath('//*[@id="plate-number"]')
                if nodes:
                    nodes[0].text=f'{ordinals[newstem]:02d}'
                else:
                    node=E.SubElement(tree.getroot(),'{http://www.w3.org/2000/svg}text',id='plate-number',x='43.2',y='18.65',**{'font-family':'Atkinson Hyperlegible','font-size':'.5','font-weight':'700','text-anchor':'end','fill':'#fcc553'})
                    node.text=f'{ordinals[newstem]:02d}'
                for node in tree.xpath('//*[@data-plate-ordinal]'):node.set('data-plate-ordinal',str(ordinals[newstem]))
            target.parent.mkdir(parents=True,exist_ok=True)
            tree.write(str(target),encoding='UTF-8',xml_declaration=True)
        row.update(stem=newstem,source_stem=plate['source_stem'],svg=str(target.relative_to(root)),svg_sha256=digest(target),group=plate['group'])
        row['sheet_background']=tree.getroot().get('data-sheet-background','#240413') if selected else '#240413'
        # The current atlas exporter owns PDF/PNG receipts. The supplement's
        # exports describe its unnumbered sheets and must not overwrite or
        # compete with the current atlas's numbered legends and exports.
        for key in ('pdf','pdf_sha256','preview','preview_sha256'):row.pop(key,None)
        records.append(row)
    for entry in book['entries']:
        entry['separate_sheets']=[r for r in records if r['stem']==entry['stem']]
        if bank[entry['stem']].get('selected_presentation'):
            entry['method']='H3r5 original-source-center analysis; saved Setouchi radiation opacity (100 levels, 0–400 W/m²), amber map background and white land outlines. Separate legend/source sheet.'
            entry['presentation']='Approved November 6/7 Setouchi presentation; pinned inputs in the current atlas catalog.'
            entry['inputs']=list({item['path']:item for item in entry['inputs']+list(selected_inputs.values())}.values())
    source['records']=records;source['catalog']=book['catalog']
    write_json(sourcepath,source)
    presentation_path=root/'sources/atlas-presentation.json'
    if presentation_path.exists():
        presentation=json.loads(presentation_path.read_text());presentation['records']=records
        presentation['inputs']=list({item['path']:item for item in presentation['inputs']+list(selected_inputs.values())}.values())
        presentation['catalog']=book['catalog']
        presentation['supplement']={'path':str(supplement_path.relative_to(ROOT)),'sha256':digest(supplement_path)}
        write_json(presentation_path,presentation)
    importlib.import_module('build-setouchi-bibliography').write_outputs(book,root,None)
    write_json(root/'sources/atlas-catalog.json',catalog())
    # A current local index provides the canonical grouping; sealed edition
    # indexes keep their historical names and source dates.
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cartofreako / current atlas</title><style>body{margin:3rem auto;padding:0 2rem;max-width:80rem;background:#240413;color:#fcc553;font:18px sans-serif}a{color:inherit}article{margin:1rem 0}h2{margin-top:2.5rem}</style><h1>Cartofreako / current atlas</h1><p>Catalog reviewed 8 November 2026. Observation dates remain specific to each plate. Maps and source legends are separate.</p>']
    for group in catalog()['groups']:
        rows=[e for e in book['entries'] if e['group']==group['id']]
        if not rows:continue
        parts.append('<h2>'+escape(group['title'])+'</h2>')
        for e in rows:
            links=[]
            for scope in ('world','japan'):
                for kind in ('map','legend'):
                    rr=next((r for r in e['separate_sheets'] if r['scope']==scope and r['kind']==kind),None)
                    if rr:links.append('<a href="'+escape(rr['svg'])+'">'+scope.title()+' '+kind+'</a>')
            parts.append('<article><strong>'+escape(e['title'])+'</strong><br><code>'+escape(e['stem'])+'</code><br>'+' · '.join(links)+'</article>')
    parts.append('<h2>Prototypes</h2><p>Bathymetry and the Stage 1/2 climate review editions remain optional prototypes, excluded from default plates.</p><p><a href="../ocean-temperature-20261108/index.html">Water-temperature Stage 1</a> · <a href="../ocean-temperature-stage-2-20261108/index.html">Derived climate plates / Stage 2</a></p></html>')
    (root/'index.html').write_text('\n'.join(parts)+'\n')
    print(f'Applied current catalog: {len(book["entries"])} default plates / {len(records)} sheets')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--atlas',type=Path,default=ROOT/'output/atlas')
    apply(parser.parse_args().atlas)
