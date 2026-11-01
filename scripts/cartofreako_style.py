"""Shared reviewed styles, native projection coordinates and SVG composition."""
from pathlib import Path
from lxml import etree as E
import copy, hashlib, json, math, os, subprocess

ROOT = Path(__file__).resolve().parents[1]
STYLE = json.loads((ROOT / 'generation-style.json').read_text())
NS = 'http://www.w3.org/2000/svg'
PARSER = E.XMLParser(huge_tree=True)

def swarm_label_attributes(attributes):
    """Keep native location label fills and typography, without text outlines."""
    attributes = dict(attributes)
    if not STYLE['swarm']['location_label_outline']:
        style = dict(part.strip().split(':', 1) for part in attributes.get('style', '').split(';') if ':' in part)
        style.update({'stroke': 'none', 'stroke-width': '0'})
        attributes.update({'stroke': 'none', 'stroke-width': '0',
                           'style': ';'.join(key + ':' + value for key, value in style.items())})
    return attributes

def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def el(tag, parent=None, **attributes):
    item = E.Element('{'+NS+'}'+tag, nsmap={None:NS}) if parent is None else E.SubElement(parent, '{'+NS+'}'+tag)
    for name,value in attributes.items(): item.set(name.replace('_','-'), str(value))
    return item

def txt(parent,x,y,value,size=.22,**attributes):
    item=el('text',parent,x=x,y=y,font_family='Liberation Sans',font_size=size,fill='#202020',**attributes)
    item.text=str(value);return item

def save(document,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    E.ElementTree(document).write(str(path),encoding='UTF-8',xml_declaration=True)

def hexpoints(x,y,radius):
    return ' '.join(f'{x+radius*math.cos(math.pi*i/3):.6f},{y+radius*math.sin(math.pi*i/3):.6f}' for i in range(6))

def hexoffsets(count,radius):
    extent=math.ceil(math.sqrt(count))+2
    candidates=[(radius*1.5*q,radius*math.sqrt(3)*(s+q/2),q,s) for q in range(-extent,extent+1) for s in range(-extent,extent+1)]
    return [(x,y) for x,y,q,s in sorted(candidates,key=lambda p:(round(p[0]**2+p[1]**2,12),p[2],p[3]))[:count]]

class Projection:
    def __init__(self,name=None,work=None):
        self.name=name or STYLE['default_projection']
        self.binary=ROOT/'build/generation-context'
        self.work=Path(work or ROOT/'build/default-styles'/self.name)
        self.work.mkdir(parents=True,exist_ok=True)
        self.info=json.loads(subprocess.check_output([str(self.binary),'info',self.name],text=True))
        self.width,self.height=self.info['width'],self.info['height'];self.suffix=self.info['suffix']
    def project(self,coordinates):
        result=subprocess.run([str(self.binary),'points',self.name],input=''.join(f'{x} {y}\n' for x,y in coordinates),text=True,capture_output=True,check=True)
        return [tuple(map(float,line.split())) for line in result.stdout.splitlines()]
    def geography(self):
        path=self.work/'basemap.svg'
        if not path.exists() or path.stat().st_mtime<self.binary.stat().st_mtime:
            env=dict(os.environ);env.setdefault('NATURAL_EARTH_DIR',str(ROOT/'assets.static/natural-earth/10m-physical-vectors'))
            subprocess.run([str(self.binary),'basemap',self.name,str(path.with_suffix(''))],env=env,check=True)
        return E.parse(str(path),PARSER)
    def base(self,title,description):
        doc=el('svg',width=f'{self.width}in',height=f'{self.height}in',viewBox=f'0 0 {self.width} {self.height}',role='img',data_projection=self.name)
        el('title',doc).text=title;el('desc',doc).text=description
        el('rect',doc,width=self.width,height=self.height,fill='white')
        doc.append(copy.deepcopy(self.geography().xpath('//*[@id="land"]')[0]));return doc
