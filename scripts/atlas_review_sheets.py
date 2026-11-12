"""Separate map/legend review sheets using the current wine/amber atlas theme."""
from pathlib import Path
from atlas_legends import legend, PAPER

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



def export(root,stem,scope,kind,tree,env):
    folder=root/('maps' if kind=='map' else 'legends')/scope
    suffix='' if kind=='map' else '-legend'
    path=folder/'svg'/(stem+suffix+'.svg');save(tree,path)
    pdf=folder/'pdf'/(stem+suffix+'.pdf');pdf.parent.mkdir(parents=True,exist_ok=True)
    render_svg(path,pdf,env)
    png=root/'previews'/scope/(stem+suffix+'.png');png.parent.mkdir(parents=True,exist_ok=True)
    render_svg(path,png,env,width=1920 if kind=='map' else 2200)
    return {'stem':stem,'scope':scope,'kind':kind,'sheet_background':PAPER if kind=='legend' else BG,'svg':str(path.relative_to(root)),
            'svg_sha256':digest(path),'pdf':str(pdf.relative_to(root)),'pdf_sha256':digest(pdf),
            'preview':str(png.relative_to(root)),'preview_sha256':digest(png)}
