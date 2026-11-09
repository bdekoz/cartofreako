"""Separate map/legend review sheets using the current wine/amber atlas theme."""
from pathlib import Path
import textwrap

from lxml import etree as E

from legend_informatics import ROOT, WIDTH, HEIGHT, font_environment
from setouchi_h3_trials import render_svg
from ocean_temperature import digest
from viz_context import snapshot_date

NS='http://www.w3.org/2000/svg'
INK='http://www.inkscape.org/namespaces/inkscape'
BG='#240413';FG='#fcc553'


def el(tag,parent=None,**attrs):
    node=E.Element('{'+NS+'}'+tag,nsmap={None:NS}) if parent is None else E.SubElement(parent,'{'+NS+'}'+tag)
    for k,v in attrs.items():node.set(k.replace('_','-'),str(v))
    return node


def text(parent,x,y,value,size=.24,**attrs):
    n=el('text',parent,x=x,y=y,font_family='Atkinson Hyperlegible',font_size=size,fill=FG,**attrs);n.text=value;return n


def save(root,path):
    from dataset import context, digest
    selected = context(required=False)
    if selected:
        manifest, value = selected
        root.set('data-dataset-id', value['dataset_id'])
        root.set('data-dataset-manifest-sha256', digest(manifest))
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    E.ElementTree(root).write(str(path),encoding='UTF-8',xml_declaration=True)


def legend(stem,title,subtitle,sections,notes,sources):
    root=el('svg',width=f'{WIDTH}in',height=f'{HEIGHT}in',viewBox=f'0 0 {WIDTH} {HEIGHT}',role='img',data_canonical_plate_id=stem,data_sheet_kind='legend')
    el('title',root).text=title+' / legend and sources'
    el('rect',root,width=WIDTH,height=HEIGHT,fill=BG)
    text(root,.8,1.1,title,.50,font_weight='700')
    text(root,.8,1.65,subtitle,.28)
    for col,section in enumerate(sections):
        x=.8+col*14.3;y=2.55
        text(root,x,y,section['title'],.32,font_weight='700');y+=.6
        for item in section.get('keys',[]):
            color,label=item[:2];shape=item[2] if len(item)>2 else 'rect'
            if shape=='outline':el('rect',root,x=x,y=y-.23,width=.4,height=.32,fill='none',stroke=color,stroke_width=.035)
            elif shape=='circle':el('circle',root,cx=x+.2,cy=y-.07,r=.16,fill=color)
            elif shape=='triangle':el('polygon',root,points=f'{x+.2},{y-.26} {x},{y+.08} {x+.4},{y+.08}',fill=color)
            else:el('rect',root,x=x,y=y-.23,width=.4,height=.32,fill=color)
            text(root,x+.65,y,label,.25);y+=.53
        for paragraph in section.get('notes',[]):
            for line in textwrap.wrap(paragraph,88):text(root,x,y,line,.225);y+=.31
            y+=.18
    y=11.6
    for paragraph in notes:
        for line in textwrap.wrap(paragraph,190):text(root,.8,y,line,.245);y+=.34
        y+=.12
    y=max(y+.25,15.15)
    for source in sources:
        for line in textwrap.wrap(source,200):text(root,.8,y,line,.205);y+=.29
    if y>18.65:raise ValueError('Legend content overflows the sheet: '+stem)
    text(root,.8,18.65,'CARTOFREAKO  /  '+snapshot_date().strftime('%-d %B %Y').upper()+'  /  Separate map and source sheet',.20)
    return root


def export(root,stem,scope,kind,tree,env):
    folder=root/('maps' if kind=='map' else 'legends')/scope
    suffix='' if kind=='map' else '-legend'
    path=folder/'svg'/(stem+suffix+'.svg');save(tree,path)
    pdf=folder/'pdf'/(stem+suffix+'.pdf');pdf.parent.mkdir(parents=True,exist_ok=True)
    render_svg(path,pdf,env)
    png=root/'previews'/scope/(stem+suffix+'.png');png.parent.mkdir(parents=True,exist_ok=True)
    render_svg(path,png,env,width=1920 if kind=='map' else 2200)
    return {'stem':stem,'scope':scope,'kind':kind,'sheet_background':BG,'svg':str(path.relative_to(root)),
            'svg_sha256':digest(path),'pdf':str(pdf.relative_to(root)),'pdf_sha256':digest(pdf),
            'preview':str(png.relative_to(root)),'preview_sha256':digest(png)}
