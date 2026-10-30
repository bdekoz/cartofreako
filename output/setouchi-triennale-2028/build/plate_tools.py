"""Native AuthaGraph coordinates and simple, inspectable SVG composition."""
from pathlib import Path
from lxml import etree as E
import copy, math, subprocess
OUT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
SUFFIX='-authagraph-44-19.052559'
PARSER=E.XMLParser(huge_tree=True)
def el(tag,parent=None,**a):
    e=E.Element('{'+NS+'}'+tag,nsmap={None:NS}) if parent is None else E.SubElement(parent,'{'+NS+'}'+tag)
    for k,v in a.items(): e.set(k.replace('_','-'),str(v))
    return e
def txt(p,x,y,s,size=.22,**a):
    e=el('text',p,x=x,y=y,font_family='Liberation Sans',font_size=size,fill='#202020',**a);e.text=str(s);return e
def project(coords):
    r=subprocess.run([str(OUT/'build/project-points')],input=''.join(f'{x} {y}\n' for x,y in coords),capture_output=True,text=True,check=True)
    return [tuple(map(float,l.split())) for l in r.stdout.splitlines()]
def base(title,description):
    doc=el('svg',width='44in',height='19.052559in',viewBox='0 0 44 19.052559',role='img')
    el('title',doc).text=title;el('desc',doc).text=description
    el('rect',doc,width=44,height=19.052559,fill='white')
    earth=E.parse(str(OUT/'plates/world/svg'/('earth'+SUFFIX+'.svg')),PARSER)
    land=copy.deepcopy(earth.xpath('//*[@id="land"]')[0]);land.set('id','land')
    for p in land.xpath('.//*[local-name()="path"]'):
        p.attrib.pop('style',None);p.set('fill','#f2f2f2');p.set('stroke','none')
    doc.append(land);return doc
def hexpoints(x,y,r):
    return ' '.join(f'{x+r*math.cos(math.pi*i/3):.6f},{y+r*math.sin(math.pi*i/3):.6f}' for i in range(6))
def hexoffsets(n,r):
    k=math.ceil(math.sqrt(n))+2
    pts=[(r*1.5*q,r*math.sqrt(3)*(s+q/2),q,s) for q in range(-k,k+1) for s in range(-k,k+1)]
    return [(x,y) for x,y,q,s in sorted(pts,key=lambda p:(round(p[0]**2+p[1]**2,12),p[2],p[3]))[:n]]
def save(doc,path):
    path.parent.mkdir(parents=True,exist_ok=True);E.ElementTree(doc).write(str(path),encoding='UTF-8',xml_declaration=True)
