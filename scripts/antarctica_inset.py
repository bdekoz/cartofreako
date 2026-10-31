"""Translate the existing Antarctic land polygons into one deliberate editorial inset."""
import copy
import hashlib
import json
import re
import subprocess
from functools import lru_cache

from shapely.geometry import Point, Polygon
from legend_informatics import E, ROOT, WIDTH, HEIGHT, el

TOKEN=re.compile(r'[MmLlHhVvZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?')


def subpaths(value):
    """Read the linear paths emitted by the native renderer and Inkscape."""
    if re.search(r'[AaCcQqSsTt]',value):raise ValueError('Antarctic land must contain linear paths')
    tokens=TOKEN.findall(value);result=[];points=[];x=y=0.;i=0;command=None
    while i<len(tokens):
        if tokens[i] in 'MmLlHhVvZz':command=tokens[i];i+=1
        if command in 'Zz':
            if points:
                x,y=points[0]
                result.append((points,True));points=[]
            command=None;continue
        if command is None:raise ValueError('Missing SVG path command')
        relative=command.islower();operation=command.upper()
        if operation in ('M','L'):
            a,b=map(float,tokens[i:i+2]);i+=2
            x,y=(x+a,y+b) if relative else (a,b)
            if operation=='M':
                if points:result.append((points,False))
                points=[];command='l' if relative else 'L'
        elif operation=='H':
            a=float(tokens[i]);i+=1;x=x+a if relative else a
        elif operation=='V':
            a=float(tokens[i]);i+=1;y=y+a if relative else a
        else:raise ValueError('Unexpected path command')
        points.append((x,y))
    if points:result.append((points,False))
    return result


def serialize(parts):
    return ' '.join('M '+' L '.join(f'{x:.12g},{y:.12g}' for x,y in points)+(' Z' if closed else '') for points,closed in parts)


@lru_cache(maxsize=1)
def antarctic_cap():
    coordinates=''.join(f'{lon} -60\n' for lon in range(-180,181))
    result=subprocess.run([str(ROOT/'build/generation-context'),'points','authagraph'],input=coordinates,
                          capture_output=True,text=True,check=True)
    boundary=[tuple(map(float,line.split())) for line in result.stdout.splitlines()]
    # The 60°S selection boundary crosses the periodic page edge; unwrap it
    # around Antarctica before using it as a spatial predicate.
    cap=Polygon([(x+WIDTH if x<WIDTH/2 else x,y) for x,y in boundary])
    if not cap.is_valid:raise ValueError('Projected Antarctic cap must be continuous')
    return cap


def antarctic_part(points, closed, cap):
    centre=Polygon(points).representative_point() if closed and len(points)>=3 else Point(points[0])
    if centre.x<WIDTH/2:centre=Point(centre.x+WIDTH,centre.y)
    return cap.covers(centre)


def consolidate(root):
    """Isolate land south of 60°S in the unchanged projection, then translate it."""
    cap=antarctic_cap()
    groups=root.xpath('//*[@id="terrestrial-land"]')
    if len(groups)!=1:raise ValueError('Expected one terrestrial-land layer')
    pieces=[];all_points=[];kept=0
    for node in list(groups[0]):
        if E.QName(node).localname!='path':continue
        remaining=[];antarctic=[]
        for points,closed in subpaths(node.get('d','')):
            centre=Polygon(points).representative_point() if closed and len(points)>=3 else Point(points[0])
            if centre.x<WIDTH/2:centre=Point(centre.x+WIDTH,centre.y)
            if cap.covers(centre):
                antarctic.append((points,closed));all_points.extend(points)
            else:remaining.append((points,closed));kept+=1
        if antarctic:
            piece=copy.deepcopy(node);piece.set('d',serialize(antarctic))
            piece.set('id',node.get('id','land')+'-antarctic-inset');pieces.append(piece)
            if remaining:node.set('d',serialize(remaining))
            else:groups[0].remove(node)
    if not pieces:raise ValueError('No Antarctic land polygons isolated')
    x0=min(p[0] for p in all_points);x1=max(p[0] for p in all_points)
    y0=min(p[1] for p in all_points);y1=max(p[1] for p in all_points)
    if not (35<x0<x1<WIDTH and 9<y0<y1<HEIGHT):raise ValueError('Unexpected Antarctic bounds')
    dx=.45-x0;dy=HEIGHT-.45-y1
    inset=el('g',id='antarctica-consolidated-inset',transform=f'translate({dx:.12g} {dy:.12g})',
             data_geographic_adjustment='Antarctica deliberately displaced to lower-left; original land silhouette retained')
    for piece in pieces:inset.append(piece)
    receipt={'status':'human-requested editorial displacement','latitude_selection':'land south of 60°S',
             'source_bounds_inches':[x0,y0,x1,y1],'translation_source_inches':[dx,dy],
             'inset_bounds_inches':[x0+dx,y0+dy,x1+dx,y1+dy],
             'source_vertex_count':len(all_points),'other_land_subpaths_retained':kept,
             'source_vertices_sha256':hashlib.sha256(json.dumps(all_points).encode()).hexdigest(),
             'network_data_moved':False,'scale_or_rotation_change':False}
    return inset,receipt
