"""Reproducible Starlink Star Light v3 maps, A3 keys and format proofs.

The geography and the celestial sphere use different coordinate systems.
USA sky sheets therefore pair a complete sky with three geographic locators;
they never crop celestial coordinates using terrestrial longitude/latitude.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import gzip
import html
import importlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

from lxml import etree as E
from PIL import Image

from atlas_presentation import settings, css, paint
from cartofreako_style import Projection, STYLE
from dataset import ROOT, atomic_json, digest
from groundstation_capabilities import CAPABILITIES, normalize
from legend_informatics import NS, XL, WIDTH, HEIGHT, SUFFIX, el, save, register_fonts, font_environment

CAP = importlib.import_module('build-groundstation-capabilities')
MSP = importlib.import_module('build-msp-speculations')
FRAMING = importlib.import_module('setouchi_world_framing')
CONFIG = ROOT / 'config/starlink-star-light-v3-20261109.json'
BG, FG = '#240413', '#fcc553'
TITLES = {'SLSL1': 'All-sky celestial context', 'SLSL2': 'Orbital technosphere / observer',
          'SLSL3': 'Orbital technosphere / global', 'SLSL4': 'Starlink / groundstations and links'}
STEMS = {'SLSL1': 'astro-all-sky', 'SLSL2': 'orbital-technosphere-observer',
         'SLSL3': 'orbital-technosphere-global', 'SLSL4': 'network-groundstations'}


def read_svg(path):
    path = Path(path)
    content = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    return E.fromstring(content, E.XMLParser(huge_tree=True))


def remove(root, xpath):
    for node in root.xpath(xpath):
        node.getparent().remove(node)


def source_group(root):
    found = root.xpath('//*[@id="source-cartography"]')
    if found:
        return deepcopy(found[0])
    group = el('g', id='source-cartography')
    for child in root:
        if child.get('id') in ('constellation-legend', 'terrestrial-background', 'observer-background', 'astronomy-background'):
            continue
        if E.QName(child).localname != 'rect':
            group.append(deepcopy(child))
    return group


def tx(parent, x, y, value, points=11, color=FG, **attrs):
    node = el('text', parent, x=x, y=y, font_family='Atkinson Hyperlegible',
              font_size=points/72, fill=color, **attrs)
    node.text = value
    return node


def wrap(value, points, width, bold=False):
    """Use the bundled font metrics, including URLs and long identifiers."""
    from reportlab.pdfbase import pdfmetrics
    font = 'Atkinson-Bold' if bold else 'Atkinson-Regular'
    lines, line = [], ''
    for word in value.split():
        if line and pdfmetrics.stringWidth(line+' '+word, font, points)/72 > width:
            lines.append(line)
            line = ''
        while pdfmetrics.stringWidth(word, font, points)/72 > width:
            cut = len(word)-1
            while pdfmetrics.stringWidth(word[:cut], font, points)/72 > width:
                cut -= 1
            lines.append(word[:cut])
            word = word[cut:]
        line = (line+' '+word).strip()
    if line:
        lines.append(line)
    return lines


def paragraph(parent, x, y, value, width, points=11, color=BG, bold=False):
    for line in wrap(value, points, width, bold):
        tx(parent, x, y, line, points, color, font_weight='700' if bold else '400')
        y += points/72*1.4
    return y+.12


def unit_polygon(shape):
    """Nine silhouettes with equal enclosed area (one square source unit).

    Every vertex fits inside the unit circumcircle used by the collision pass.
    Radius squared, rather than silhouette choice, controls the enclosed area.
    """
    if shape == 'circle':
        return None
    if shape in ('cross', 'saltire'):
        a = .28
        points = [(-a,-1),(a,-1),(a,-a),(1,-a),(1,a),(a,a),
                  (a,1),(-a,1),(-a,a),(-1,a),(-1,-a),(-a,-a)]
        if shape == 'saltire':
            points = [((x-y)/math.sqrt(2), (x+y)/math.sqrt(2)) for x,y in points]
    else:
        n = {'square': 4, 'diamond': 4, 'pentagon': 5, 'hexagon': 6, 'star': 10, 'octagon': 8}[shape]
        angle = math.pi/4 if shape == 'square' else -math.pi/2
        points = [((.45 if shape == 'star' and i%2 else 1)*math.cos(angle+2*math.pi*i/n),
                   (.45 if shape == 'star' and i%2 else 1)*math.sin(angle+2*math.pi*i/n)) for i in range(n)]
    area = abs(sum(x*y1-x1*y for (x,y),(x1,y1) in zip(points,points[1:]+points[:1])))/2
    return [(x/math.sqrt(area),y/math.sqrt(area)) for x,y in points]


def marker(parent, record, shape, x, y, radius, identifier, *, foreground=FG, background=BG):
    known = record.get('aperture_proxy_m2') is not None
    status = record.get('status', 'unconfirmed')
    group = el('g', parent, id=identifier, transform=f'translate({x} {y})',
               data_marker_shape=shape, data_capability=record['capability'], data_status=status,
               data_radius_inches=radius, data_size_known=str(known).lower(),
               data_aperture_m2=record['aperture_proxy_m2'] if known else '')
    attributes = {'fill': foreground, 'fill_opacity': .25, 'stroke': foreground,
                  'stroke_width': .009, 'stroke_linejoin': 'round', 'data_role': 'capability-outline'}
    if status != 'reported-operational':
        attributes['stroke_dasharray'] = '.024 .014' if status == 'unconfirmed' else '.004 .012'
    points = unit_polygon(shape)
    if points is None:
        el('circle', group, cx=0, cy=0, r=radius/math.sqrt(math.pi), **attributes)
    else:
        el('polygon', group, points=' '.join(f'{x*radius:.12g},{y*radius:.12g}' for x,y in points), **attributes)
    if not known:
        el('rect', group, x=-radius*.16, y=-radius*.16, width=radius*.32, height=radius*.32,
           fill=background, stroke=foreground, stroke_width=.006, data_role='unknown-size')
    el('title', group).text = (record.get('name', CAPABILITIES[record['capability']][0])
                             + ' / ' + CAPABILITIES[record['capability']][0]
                             + f' / listed aperture: {record.get("aperture_proxy_m2")} m² / {status}')
    return group


def refine_groundstations(approved, config, projection, *, profile_path=None, recipe=None):
    capability = json.loads((ROOT/config['capability_config']).read_text())
    profile_path = Path(profile_path or ROOT/capability['source_profile']).resolve()
    profile = json.loads(profile_path.read_text())
    input_path = profile_path.parent/profile['source']['geojson']
    capability['source'] = str(input_path.relative_to(ROOT)) if input_path.is_relative_to(ROOT) else str(input_path)
    capability['source_profile'] = str(profile_path.relative_to(ROOT)) if profile_path.is_relative_to(ROOT) else str(profile_path)
    foreground, background = (recipe['text'], recipe['background']) if recipe else (FG, BG)
    if digest(input_path) != profile['source']['gateways_sha256']:
        raise ValueError('Groundstation input differs from its pinned profile')
    records, summary = normalize(json.loads(input_path.read_text()))
    old_radii = {r['id']: CAP.radius(r, capability) for r in records if r['kind'] != 'link'}
    capability['size']['radius_spread_multiplier'] = config['radius_spread_multiplier']
    placement = CAP.layout(records, projection, capability)
    source = source_group(approved)
    # Remove the actual filled land layer. Stroking its tessellated pieces
    # would introduce artificial triangle boundaries, not coastlines.
    remove(source, './/*[@id="terrestrial-land" or @id="land" or @id="antarctica-consolidated-inset"]')
    remove(source, './/*[starts-with(@id,"starlink-gateways-") or contains(@id,"legend")]')
    remove(source, './/*[@id="groundstations-starlink" or @id="groundstation-location-tethers" or '
                   '@id="groundstation-pops" or @id="groundstation-cell-guides" or '
                   '@id="groundstation-capability-metadata" or local-name()="defs"]')
    links = source.xpath('.//*[@data-gateway-link="true"]')
    link_records = [r for r in records if r['kind']=='link']
    if len(links) != len(link_records):
        raise ValueError('Groundstation link geometry differs from selected source')
    for node, record in zip(links, link_records):
        node.set('data-record-id', record['id'])
        paint(node.attrib, stroke=foreground, stroke_opacity=1, stroke_width=.008)
    tethers = CAP.layer(source, 'groundstation-location-tethers', 'Source position tethers')
    vendor = CAP.layer(source, 'groundstations-starlink', 'Starlink / antenna capabilities')
    pops = CAP.layer(source, 'groundstation-pops', 'PoPs / fixed size')
    groups = {}
    for key, (title, _, _) in CAPABILITIES.items():
        parent = CAP.layer(vendor, 'groundstations-'+key, title)
        groups[key] = (CAP.layer(parent, 'groundstations-'+key+'-locpoint', 'locpoint'),
                       CAP.layer(parent, 'groundstations-'+key+'-name', 'name', True))
    for r in records:
        if r['kind'] == 'link':
            continue
        x,y = r['display_xy']; sx,sy = r['source_xy']
        r['previous_radius_inches'] = old_radii[r['id']]
        if math.dist((x,y),(sx,sy)) > .015:
            el('path', tethers, d=f'M {sx} {sy} L {x} {y}', fill='none', stroke='#b7873f',
               stroke_width='.004', stroke_opacity='.6', data_record_id=r['id'])
        if r['kind'] == 'pop':
            el('circle', pops, id='pop-'+r['id'], cx=x, cy=y, r=r['radius_inches'], fill='none',
               stroke=foreground, stroke_width='.009', data_record_id=r['id'], data_kind='pop')
            continue
        marks,names = groups[r['capability']]
        node = marker(marks,r,config['capability_markers'][r['capability']],x,y,r['radius_inches'],'site-'+r['id'],
                      foreground=foreground, background=background)
        for key,value in {'record-id':r['id'], 'groundstation':'true', 'name':r['name'],
                          'longitude':r['geometry']['coordinates'][0], 'latitude':r['geometry']['coordinates'][1],
                          'source-x':sx, 'source-y':sy, 'group':r['group']}.items():
            node.set('data-'+key,str(value))
        tx(names,x,y-r['radius_inches']-.03,r['name'],9/FRAMING.SCALE,foreground,
           data_record_id=r['id'],data_locpoint=node.get('id'),text_anchor='middle')
    evidence = {'schema':'cartofreako-slsl-groundstations-v3','source':capability['source'],
                'source_sha256':digest(input_path),'source_profile_sha256':digest(profile_path),
                'source_date':profile['source']['datestamp'],'configuration':capability,'summary':summary,
                'placement':placement,'records':records,'markers':config['capability_markers'],
                'radius_formula':'r_new = r_min + 2 * (r_previous - r_min); unknowns and PoPs unchanged',
                'marker_area_formula':'enclosed source area = r_new squared for every capability silhouette'}
    el('metadata',source,id='slsl-groundstation-encoding').text = json.dumps({k:v for k,v in evidence.items() if k not in ('records','placement')},sort_keys=True)
    return source,evidence


def orbital_source(native, plate, recipe):
    source = deepcopy(native)
    if plate == 'SLSL3':
        starlink = source.xpath('//*[@id="starlink"]')[0]
        ids = CAP.layer(starlink,'starlink-id','id')
        for label in source.xpath('//*[@id="starlink-name"]/*'):
            copy = deepcopy(label)
            copy.set('id','id-norad-'+label.get('data-norad-id'))
            copy.set('data-object-kind','id')
            copy.text = label.get('data-norad-id')
            ids.append(copy)
    MSP.apply_variant(source,recipe,STEMS[plate],'map')
    MSP.apply_palette(source,recipe,'map')
    return source_group(source)


def sheet(plate, scope, kind='map', size=(WIDTH,HEIGHT)):
    w,h = size
    root = el('svg',id=f'{plate}-{scope}-{kind}',width=f'{w}in',height=f'{h}in',viewBox=f'0 0 {w} {h}',role='img',
              data_plate=plate,data_scope=scope,data_sheet_kind=kind,data_atlas_presentation='wine-amber')
    el('title',root).text = f'{plate} / {TITLES[plate]} / {scope} / {kind}'
    el('rect',root,id='sheet-paper',width=w,height=h,fill=BG if kind=='map' else FG)
    return root


def fit_transform(bounds, box):
    bx,by,bw,bh = bounds; x,y,w,h = box
    scale = min(w/bw,h/bh)
    return scale, x+(w-bw*scale)/2-bx*scale, y+(h-bh*scale)/2-by*scale


def fix_sky_labels(source, scale, points):
    from reportlab.pdfbase import pdfmetrics
    changes = []
    for index,label in enumerate(source.xpath('.//*[@id="labels"]//*[local-name()="text"]')):
        label.set('id',f'slsl-sky-label-{index}')
        original = [float(label.get('x')),float(label.get('y'))]
        size = points/scale
        width = pdfmetrics.stringWidth(label.text or '', 'Atkinson-Regular', size)/72
        x = min(max(original[0],.08),WIDTH-.08-width)
        y = min(max(original[1],size/72),HEIGHT-size/72)
        label.set('x',str(x)); label.set('y',str(y)); label.set('text-anchor','start')
        label.set('font-size',str(size/72))
        paint(label.attrib,fill=FG,stroke='none',font_size=size/72)
        label.set('data-physical-font-size-pt',str(points))
        changes.append({'id':label.get('id'),'text':label.text,'before_xy':original,'after_xy':[x,y],
                        'estimated_width_source_inches':width,'physical_font_size_pt':points})
    return changes


def add_sky(root, source, box, points=None, *, side_margin_factor=1, margin_box=None):
    # The reference frame is finite; glyphs and ornaments are allowed outside
    # it. Begin with the conservative source gutter, then tighten the requested
    # side margins uniformly. Export validation checks every visible edge glyph.
    bounds = (-.6,-.6,WIDTH+1.2,HEIGHT+1.2)
    scale,dx,dy = fit_transform(bounds,box)
    mx,my,mw,mh = margin_box or box
    previous_margin = (mw-WIDTH*scale)/2
    if not 0 < side_margin_factor <= 1:
        raise ValueError('Sky side-margin factor must be in (0, 1]')
    margin = previous_margin*side_margin_factor
    if side_margin_factor != 1:
        scale = (mw-2*margin)/WIDTH
        dx,dy = mx+margin,my+(mh-HEIGHT*scale)/2
    content = deepcopy(source)
    changes = fix_sky_labels(content,scale,points) if points is not None else []
    if points is None:
        for layer in content.xpath('.//*[@id="starlink-name" or @id="starlink-id"]'):
            for label in layer:
                label.set('font-size',str(6/72/scale))
                paint(label.attrib,font_size=6/72/scale)
    content.set('transform',f'translate({dx} {dy}) scale({scale})')
    root.append(content)
    root.set('data-image-scale',str(scale))
    root.set('data-celestial-frame','complete-sphere-with-glyph-gutter')
    root.set('data-frame-side-margin-inches',str(margin))
    return {'scale':scale,'translation':[dx,dy],'source_bounds':bounds,'box':box,
            'previous_side_margin_inches':previous_margin,'side_margin_inches':margin,
            'side_margin_factor':side_margin_factor,'label_adjustments':changes}


def region_bounds(projection, region):
    west,south,east,north = region['bounds_lon_lat']
    points = [(west+(east-west)*i/80,south+(north-south)*j/40)
              for i in range(81) for j in range(41)]
    xy = projection.project([((lon+180)%360-180,lat) for lon,lat in points])
    xs,ys = zip(*xy)
    pad = .18
    return [min(xs)-pad,min(ys)-pad,max(xs)-min(xs)+2*pad,max(ys)-min(ys)+2*pad]


def groundstation_regions(regions, evidence):
    """Include whole displaced glyphs for every record selected geographically.

    Collision displacement can exceed a geographic crop's fixed padding. The
    selection always uses source longitude/latitude, never display position.
    """
    result=[]
    for region in regions:
        region=deepcopy(region)
        west,south,east,north=region['bounds_lon_lat']
        x,y,w,h=region['projected_bounds'];x1,y1=x+w,y+h
        selected=[]
        for record in evidence['records']:
            if record['kind']=='link':
                continue
            lon,lat=record['geometry']['coordinates'][:2]
            if west>0 and lon<0:
                lon+=360
            if west<=lon<=east and south<=lat<=north:
                selected.append(record['id'])
                px,py=record['display_xy'];r=record['radius_inches']+.02
                x,y,x1,y1=min(x,px-r),min(y,py-r),max(x1,px+r),max(y1,py+r)
        region['geographic_projected_bounds']=region['projected_bounds']
        region['projected_bounds']=[x,y,x1-x,y1-y]
        region['selected_source_record_ids']=selected
        result.append(region)
    return result


def viewport(root, identifier, href, bounds, box, title, title_size=16):
    x,y,w,h = box
    defs = root.find(f'{{{NS}}}defs')
    clip = el('clipPath',defs,id=identifier+'-clip',clipPathUnits='userSpaceOnUse')
    el('rect',clip,x=x,y=y,width=w,height=h)
    outer = el('g',root,id=identifier,clip_path=f'url(#{identifier}-clip)',
               data_source_bounds=json.dumps(bounds),data_viewport=json.dumps(box))
    scale,dx,dy = fit_transform(bounds,box)
    use = el('use',outer,transform=f'translate({dx} {dy}) scale({scale})')
    use.set('{'+XL+'}href','#'+href)
    tx(root,x,y-.13,title,title_size)
    el('rect',root,x=x,y=y,width=w,height=h,fill='none',stroke=FG,stroke_width='.008',stroke_opacity='.5')
    return {'id':identifier,'bounds':bounds,'box':box,'scale':scale}


def make_map(plate, scope, source, locator, config, regions):
    root = sheet(plate,scope)
    details = {}
    sky = plate in ('SLSL1','SLSL2')
    if sky:
        box = (.25,.25,43.5,HEIGHT-.5) if scope=='world' else (.25,.65,30.4,HEIGHT-1.05)
        details['sky'] = add_sky(root,source,box,config['astronomy_labels']['after_pt'] if plate=='SLSL1' else None,
                                 side_margin_factor=config['astronomy_side_margin_factor'] if plate=='SLSL1' else 1,
                                 margin_box=(0,0,WIDTH,HEIGHT) if scope=='world' else None)
        if scope=='usa':
            defs = el('defs',root)
            defs.append(deepcopy(locator))
            boxes = [(31.2,1.1,12.2,6),(31.2,8.05,12.2,5.5),(31.2,14.5,12.2,3.9)]
            details['panels'] = [viewport(root,r['id'],'usa-locator',r['projected_bounds'],box,r['name'],14)
                                 for r,box in zip(regions,boxes)]
            tx(root,.7,HEIGHT-.24,'Complete celestial sphere / USA location context at right',14)
        return root,details
    defs = el('defs',root)
    content = deepcopy(source)
    content.set('id','source-cartography')
    defs.append(content)
    if scope=='world':
        clip = el('clipPath',defs,id='world-window',clipPathUnits='userSpaceOnUse')
        el('rect',clip,width=WIDTH,height=HEIGHT)
        frame = el('g',root,id='st2-image-frame',transform=f'translate({FRAMING.DX} {FRAMING.DY}) scale({FRAMING.SCALE})')
        if plate=='SLSL3':
            # Retain the accepted world basemap inset on the global orbital
            # plate. Regional views continue to use unmodified geography.
            land=content.xpath('.//*[@id="terrestrial-land"]')[0]
            piece=FRAMING.partition(land,FRAMING.antarctic_cap(),changes=[])
            if piece is not None:
                dx,dy=FRAMING.ANTARCTIC_TRANSLATION
                inset=el('g',frame,id='antarctica-consolidated-inset',transform=f'translate({dx} {dy})')
                inset.append(piece)
        window = el('g',frame,clip_path='url(#world-window)')
        for offset in (FRAMING.SHIFT-WIDTH,FRAMING.SHIFT,FRAMING.SHIFT+WIDTH):
            el('use',window,transform=f'translate({offset} 0)').set('{'+XL+'}href','#source-cartography')
        details['cyclic_shift_source_inches'] = FRAMING.SHIFT
    else:
        boxes = [(.5,.8,29.9,17.7),(31.1,.8,12.3,9.4),(31.1,11.1,12.3,7.4)]
        details['panels'] = [viewport(root,r['id'],'source-cartography',r['projected_bounds'],box,r['name'],16)
                             for r,box in zip(regions,boxes)]
    return root,details


def make_locator(land, projection):
    locator = el('g',id='usa-locator')
    copy = deepcopy(land)
    for n in copy.iter():
        if n.get('id'):
            n.set('id','locator-'+n.get('id'))
        if E.QName(n).localname=='path':
            paint(n.attrib,fill='#47231d',stroke='none')
    locator.append(copy)
    x,y = projection.project([(-122.4194,37.7749)])[0]
    el('circle',locator,cx=x,cy=y,r=.04,fill=FG,data_reference='San Francisco / 37.7749 N, 122.4194 W')
    tx(locator,x+.08,y-.04,'San Francisco',7)
    return locator


def observer_notes(plate, scope):
    notes = {
        'SLSL1': 'The viewer is conceptually at Earth, looking outward over the complete celestial sphere in right ascension and declination. This all-sky catalog view includes objects below the San Francisco horizon. SLSL2 selects artificial satellites above that local horizon; SLSL3 turns inward to Earth subpoints, and SLSL4 follows infrastructure on the surface.',
        'SLSL2': 'The observer stands at San Francisco, California (37.7749 N, 122.4194 W; 16 m elevation), looking outward. Only objects above the local horizon at the calculation instant are admitted, plotted as celestial directions. Visibility does not mean naked-eye detectability. SLSL1 supplies natural celestial context; SLSL3 shows the Earth subpoints of the orbital population and SLSL4 the terrestrial network.',
        'SLSL3': 'The viewer looks down conceptually on the whole Earth, unfolded in AuthaGraph. Each satellite is plotted at its terrestrial subpoint, not at orbital height or apparent position in the sky. Representative paths are ground tracks. SLSL2 instead looks outward from San Francisco; SLSL1 maps natural sky objects and SLSL4 maps surface infrastructure.',
        'SLSL4': 'The viewer looks down conceptually on Earth, unfolded in AuthaGraph. The marks represent source-listed antenna sites and network points; lines follow the supplied link geometry. Displaced symbols retain tethers to their source positions. Compare these surface locations with satellite subpoints in SLSL3; SLSL1 and SLSL2 look outward into celestial space.'}
    if scope=='usa':
        notes[plate] += (' The full sky remains intact beside locators for the contiguous USA, Alaska and Hawaii; these locators do not relocate the observer or imply three regional sky observations.' if plate in ('SLSL1','SLSL2') else
                         ' The three panels enlarge the contiguous USA, Alaska including the Aleutians, and Hawaii including its northwest islands. The panels use independent scales and include neighboring geography.')
    return notes[plate]


def source_keys(source, plate, profile, config, evidence):
    keys=[]
    if plate=='SLSL1':
        objects=source.xpath('.//*[@data-kind]')
        counts=Counter(n.get('data-kind') for n in objects)
        for kind,count in counts.items():
            sample=next(n for n in objects if n.get('data-kind')==kind)
            keys.append((kind.replace('-',' ').title()+f' / {count:,}',sample))
    elif plate in ('SLSL2','SLSL3'):
        names={g['constellation']['id']:g['constellation']['name'] for g in profile['catalogs']['groups'] if 'constellation' in g}
        for group in source.xpath('.//*[@data-display-group and @data-object-count]'):
            count=int(group.get('data-object-count'))
            samples=group.xpath('.//*[@data-marker-shape]')
            if count and samples:
                ident=group.get('data-display-group')
                keys.append((names.get(ident,ident.replace('-',' ').title())+f' / {count:,}',samples[0]))
    else:
        for kind in CAPABILITIES:
            example={'capability':kind,'status':'reported-operational','aperture_proxy_m2':50}
            sample=marker(el('g'),example,config['capability_markers'][kind],0,0,.14,'key-sample-'+kind)
            keys.append((CAPABILITIES[kind][0]+f' / {evidence["summary"]["capabilities"][kind]}',sample))
    return keys


def icon(parent, sample, x, y, identifier):
    # Read exact source bounds, including categorical polygons and path symbols.
    copy=deepcopy(sample)
    if copy.get('data-capability'):
        copy.attrib.pop('transform',None)
        radius=float(copy.get('data-radius-inches'))
        bounds=(-radius,-radius,radius,radius)
    else:
        bounds=MSP.ORBITAL.LAYOUT.shape_bounds(copy)
    x0,y0,x1,y1=bounds
    scale=min(.22/max(x1-x0,.001),.22/max(y1-y0,.001))
    el('rect',parent,x=x-.16,y=y-.16,width=.32,height=.32,rx='.035',fill=BG)
    group=el('g',parent,id=identifier,transform=f'translate({x} {y}) scale({scale}) translate({-(x0+x1)/2} {-(y0+y1)/2})')
    for n in copy.iter():
        n.attrib.pop('id',None)
        for key in list(n.attrib):
            if key.startswith('data-'):
                del n.attrib[key]
    group.append(copy)


def make_legend(plate, scope, source, config, profile, evidence, timestamp):
    w,h=[v/25.4 for v in config['legend_mm']]
    root=sheet(plate,scope,'legend',(w,h))
    root.set('data-palette-reversed','true')
    root.set('data-observer-notes',observer_notes(plate,scope))
    tx(root,.45,.65,plate+' / '+TITLES[plate],27,BG,font_weight='700')
    tx(root,.45,1.04,('World' if scope=='world' else 'USA / mainland, Alaska and Hawaii')+'  |  '+timestamp,12,BG)
    col=(w-1.3)/3
    xs=[.45,.65+col,.85+2*col]
    y=1.65
    tx(root,xs[0],y,'Symbols / full source population',15,BG,font_weight='700'); y+=.42
    keys=source_keys(source,plate,profile,config,evidence)
    for i,(label,sample) in enumerate(keys):
        icon(root,sample,xs[0]+.17,y-.04,f'key-{i}')
        rows=wrap(label,10.5,col-.6)
        for line in rows:
            tx(root,xs[0]+.45,y,line,10.5,BG);y+=.205
        y+=.14
    if plate=='SLSL4':
        y+=.12
        for status,label in [('reported-operational','Solid / reported operational'),('unconfirmed','Dashed / planned or unconfirmed'),('retired','Dotted / source reports retirement')]:
            sample=marker(el('g'),{'capability':'ka','status':status,'aperture_proxy_m2':50},'circle',0,0,.14,'status-'+status)
            icon(root,sample,xs[0]+.17,y-.04,'key-'+status)
            tx(root,xs[0]+.45,y,label,10.5,BG); y+=.36
        sample=marker(el('g'),{'capability':'ka','status':'unconfirmed','aperture_proxy_m2':None},'circle',0,0,.14,'unknown')
        icon(root,sample,xs[0]+.17,y-.04,'key-unknown-size')
        tx(root,xs[0]+.45,y,'Central hollow square / size unknown',10.5,BG);y+=.36
        sample=el('circle',cx=0,cy=0,r='.08',fill='none',stroke=FG,stroke_width='.012')
        icon(root,sample,xs[0]+.17,y-.04,'key-pop')
        tx(root,xs[0]+.45,y,'Open circle / 66 PoPs, fixed size',10.5,BG);y+=.4
        tx(root,xs[0],y,'124 source links / amber; thin tethers / ochre',10.5,BG)
        y+=.5
        tx(root,xs[0],y,'Aperture proxy / World-sheet symbol sizes',11,BG,font_weight='700')
        y+=.55
        for i,area in enumerate((13.577335130284366,50,100,200)):
            x=xs[0]+.5+i*1.15
            example={'kind':'antenna-site','capability':'ka','status':'reported-operational','aperture_proxy_m2':area}
            radius=CAP.radius(example,evidence['configuration'])*FRAMING.SCALE
            el('rect',root,x=x-.48,y=y-.38,width='.96',height='.76',rx='.035',fill=BG)
            marker(root,example,'circle',x,y,radius,'aperture-key-'+str(i))
            tx(root,x,y+.57,f'{area:.1f} m²' if i==0 else f'{area:g} m²',9,BG,text_anchor='middle')
        y+=.8
    if y>h-.65:
        raise ValueError('Legend keys overflow '+plate)
    x=xs[1];y=1.65
    tx(root,x,y,'Observer notes',15,BG,font_weight='700'); y+=.4
    notes=el('g',root,id='observer-notes')
    y=paragraph(notes,x,y,observer_notes(plate,scope),col,12)
    y+=.2
    tx(root,x,y,'How to read the plate',15,BG,font_weight='700');y+=.4
    common={'SLSL1':['Stellar glyph sizes follow source magnitude; colors retain the source bins. Aquamarine circles identify exoplanet hosts. Planet disks are fixed display glyphs; thin dashed outlines encode true angular extent. Rays are decorative.',
                     'Object-name type: 12 pt before revision; 9.6 pt after revision, a 20% reduction in both views. A complete celestial frame with a glyph gutter and inward label placement prevents edge clipping.',
                     ('This edition uses the latest preserved all-sky artwork in this checkout, calculated 29 October 2026. The separately documented November astronomy exports are unavailable here.' if timestamp=='2026-10-29T20:00:00Z' else 'The explicitly selected all-sky source retains its own calculation timestamp and catalog selection, recorded in the input manifest.')],
            'SLSL2':['Names shown for Starlink only, at 6 pt on the map. Starlink uses 1.5x sunbursts. Other fleet colors and shapes retain the accepted source encoding.',
                     'Opacity records illumination. A black x with an amber halo marks debris. The horizon and equator describe the observer frame; the full frame does not imply an unobstructed view in every direction.'],
            'SLSL3':['Starlink NORAD IDs appear at 6 pt on the world sheet, in a separate layer beneath the satellite marks. USA panels magnify this type with the map. Names remain editable and hidden. Sunbursts use the accepted 1.5x size; representative tracks use 2x stroke weight.',
                     'One plotted satellite per NORAD ID. Overlapping memberships resolve by the profile order. Seven-day element age and six-hour future tolerance apply; these are calculated visualization positions.'],
            'SLSL4':['Nine silhouettes identify capability categories; silhouette area is equal at equal radius. The listed aperture proxy is the largest complete bank, max(N x pi x D squared / 4); bands are never summed.',
                     'The minimum radius remains 0.04 in. Radius = 0.04 + 2 x (previous radius - 0.04): the low-to-high radius span doubles. This is an enhanced display scale, not direct area proportionality to aperture. Unknown sizes and PoPs keep their previous size.',
                     '538 antenna records have a size proxy; 52 do not. The 590 antenna records include proposed and retired sites. A source record is not necessarily a unique operating installation. Links include backbone and community satellite links; they are not all fibre.',
                     'Filled continental land and the consolidated Antarctic inset are removed. Cluster displacement is recomputed to keep the larger marks apart; tethers retain the source-location connection.']}
    for note in common[plate]:
        y=paragraph(root,x,y,note,col,11)
    if y>h-.7:
        raise ValueError('Legend notes overflow '+plate)
    x=xs[2];y=1.65
    tx(root,x,y,'Sources / calculation',15,BG,font_weight='700'); y+=.4
    if plate=='SLSL1':
        sources=['Gaia DR3 / ESA: bright stars. NASA Exoplanet Archive: host systems. NASA/JPL: approximate Solar System positions; curated persistent and transient sources.',
                 'Source IDs, per-object URLs, coordinates, counts and source glyph colors remain in the editable SVG. The source artwork and its SHA-256 are recorded in sources/input-manifest.json.',
                 'https://gea.esac.esa.int/archive/', 'https://exoplanetarchive.ipac.caltech.edu/', 'https://ssd.jpl.nasa.gov/',
                 'Calculation: '+timestamp+'. Astronomy and orbital source dates are recorded separately.']
    elif plate in ('SLSL2','SLSL3'):
        meta=source.xpath('.//*[@id="orbital-technosphere-metadata"]')[0]
        sources=['CelesTrak OMM elements and named memberships; the 9 November 2026 snapshot is propagated with SGP4, WGS-72 and AFSPC mode.',
                 'https://celestrak.org/NORAD/documentation/gp-data-formats.php',
                 'https://celestrak.org/publications/AIAA/2006-6753/',
                 f'Calculation: {timestamp}. Plotted: {meta.get("data-visible-records")}; epoch exclusions: {meta.get("data-skipped-stale")}; propagation failures: {meta.get("data-failed-propagation")}.',
                 'The retained NASA SSC reference is historical validation only. It does not independently validate the November positions.',
                 'The pinned profile, acquisition receipt and catalog checksums are copied under sources/orbital/.']
    else:
        sources=['Unofficial Starlink Global Gateways & PoPs. Supplied KML snapshot dated 3 November 2026; faithfully converted to GeoJSON. 780 records: 590 antenna records, 66 PoPs and 124 lines.',
                 'The filename date is not a per-site verification date. The supplied KML does not identify an author or license. The collection is not attributed to SpaceX.',
                 'Numeric antenna diameters are interpreted as metres, consistent with FCC DOC-374641A1 and DOC-395259A1. This does not verify individual sites.',
                 'https://docs.fcc.gov/public/attachments/DOC-374641A1.pdf',
                 'https://docs.fcc.gov/public/attachments/DOC-395259A1.pdf',
                 'Source fields, conflicts, incomplete inventories, old/new radii and display positions: sources/capability-evidence.json.']
    sources+=['AuthaGraph / Cartofreako. Natural Earth supplies terrestrial context. Atkinson Hyperlegible supplies the type.',
              'https://www.naturalearthdata.com/',
              'Map: wine #240413, amber #fcc553; legend: amber ground, wine text. Symbol colors are retained on dark sample swatches.']
    for note in sources:
        y=paragraph(root,x,y,note,col,10.5)
    if y>h-.7:
        raise ValueError('Legend sources overflow '+plate)
    tx(root,.45,h-.3,'STARLINK STAR LIGHT / v3 / '+plate+' / '+scope.upper()+' / A3 landscape / 420 x 297 mm',9,BG)
    return root


def query_boxes(svg, env):
    run=subprocess.run(['bash',str(ROOT/'scripts/run-inkscape.sh'),'inkscape',str(svg),'--query-all'],
                       env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    result={}
    for line in run.stdout.splitlines():
        parts=line.split(',')
        if len(parts)==5:
            try: result[parts[0]]=list(map(float,parts[1:]))
            except ValueError: pass
    return result


def export(record, output, env, width):
    svg=output/record['svg']; base=svg.parent.parent
    pdf=base/'pdf'/(svg.stem+'.pdf'); preview=base/'preview'/(svg.stem+'.png')
    archive=svg.with_suffix('.svg.gz')
    for path in (pdf,preview): path.parent.mkdir(parents=True,exist_ok=True)
    archive.write_bytes(gzip.compress(svg.read_bytes(),mtime=0))
    log=output/'sources/export-logs'/(record['plate']+'-'+record['scope']+'-'+record['kind']+'.log')
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w') as stream:
        for path in (pdf,preview):
            command=['bash',str(ROOT/'scripts/run-inkscape.sh'),'inkscape',str(svg),'--export-area-page','--export-filename='+str(path)]
            if path==preview: command+=['--export-width='+str(width)]
            subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    with Image.open(preview) as im:
        im.convert('RGB').save(preview.with_suffix('.webp'),quality=90)
    record['outputs']={k:{'path':str(p.relative_to(output)),'sha256':digest(p),'bytes':p.stat().st_size}
                       for k,p in [('pdf',pdf),('png',preview),('webp',preview.with_suffix('.webp')),('svg.gz',archive)]}
    print('Exported',record['plate'],record['scope'],record['kind'],flush=True)
    return record


def validate(output, records, sources, config, evidence, env, exports=True):
    checks=[]
    if len(records)!=16 or len({(r['plate'],r['scope'],r['kind']) for r in records})!=16:
        raise ValueError('Expected all sixteen unique map/legend sheets')
    for record in records:
        svg=output/record['svg'];root=read_svg(svg)
        ids=root.xpath('//*[@id]/@id')
        if len(ids)!=len(set(ids)):
            raise ValueError('Duplicate SVG IDs: '+str(svg))
        if record['kind']=='legend':
            width,height=map(float,root.get('viewBox').split()[2:])
            if abs(width*25.4-420)>1e-7 or abs(height*25.4-297)>1e-7:
                raise ValueError('Legend must be landscape A3')
            if root.xpath('//*[@id="sheet-paper"]')[0].get('fill')!=FG or not root.xpath('//*[@id="observer-notes"]'):
                raise ValueError('Missing reversed palette or observer notes')
        else:
            original=sources[record['plate']]
            if record['plate']=='SLSL1':
                before={n.get('id'):dict(n.attrib) for n in original.xpath('.//*[@data-kind]')}
                after={n.get('id'):dict(n.attrib) for n in root.xpath('//*[@data-kind]')}
                if before!=after:
                    raise ValueError('Astronomy object position, size or color changed')
                labels=root.xpath('//*[@id="labels"]//*[local-name()="text"]')
                if len(labels)!=len(original.xpath('.//*[@id="labels"]//*[local-name()="text"]')):
                    raise ValueError('Astronomy labels lost')
                if any(abs(float(n.get('data-physical-font-size-pt'))-9.6)>1e-8 for n in labels):
                    raise ValueError('Astronomy type must be 9.6 pt')
            if record['plate']=='SLSL4':
                if root.xpath('//*[@id="terrestrial-land" or @id="antarctica-consolidated-inset"]'):
                    raise ValueError('Removed groundstation layers survived')
                sites=root.xpath('//*[@data-groundstation="true"]')
                if len(sites)!=590 or len(root.xpath('//*[@data-kind="pop"]'))!=66 or len(root.xpath('//*[@data-gateway-link="true"]'))!=124:
                    raise ValueError('Groundstation conservation failed')
                if {n.get('data-marker-shape') for n in sites}!=set(config['capability_markers'].values()):
                    raise ValueError('Expected nine capability silhouettes')
            if record['plate'] in ('SLSL2','SLSL3'):
                before={n.get('data-norad-id'):dict(n.attrib) for n in original.xpath('.//*[@data-object-kind="locpoint"]')}
                marks=root.xpath('//*[@data-object-kind="locpoint"]')
                after={n.get('data-norad-id'):dict(n.attrib) for n in marks}
                if before!=after or len(after)!=len(marks):
                    raise ValueError('Orbital membership or styled marker geometry changed')
                meta=root.xpath('//*[@id="orbital-technosphere-metadata"]')[0]
                if len(marks)!=int(meta.get('data-visible-records')):
                    raise ValueError('Orbital count differs from propagation metadata')
            if record['scope']=='usa' and any(not root.xpath('//*[@id=$id]',id=r['id']) for r in config['regions']):
                raise ValueError('USA coverage is incomplete')
            if record['plate']=='SLSL4' and record['scope']=='usa':
                by_id={r['id']:r for r in evidence['records']}
                for region in record['layout']['groundstation_regions']:
                    x,y,w,h=region['projected_bounds']
                    for ident in region['selected_source_record_ids']:
                        item=by_id[ident];px,py=item['display_xy'];r=item['radius_inches']+.005
                        if not (x<=px-r and px+r<=x+w and y<=py-r and py+r<=y+h):
                            raise ValueError('USA groundstation clipped after displacement: '+ident)
        if exports:
            page_w,page_h=(float(v)*96 for v in root.get('viewBox').split()[2:])
            if record['plate']=='SLSL1' and record['kind']=='map':
                targets=root.xpath('//*[@data-kind or starts-with(@id,"stationary-rays-") or starts-with(@id,"slsl-sky-label-")]/@id')
            elif record['kind']=='legend':
                targets=['observer-notes']
                # Inkscape-generated IDs are not present in query-all. The full
                # page artwork bound still detects any overflowing text/keys.
                targets += [root.get('id')]
            else: targets=[]
            boxes=query_boxes(svg,env) if targets else {}
            for ident in targets:
                if ident not in boxes:
                    raise ValueError('Missing rendered geometry '+ident)
                x,y,w,h=boxes[ident]
                if min(x,y)<-.1 or x+w>page_w+.1 or y+h>page_h+.1:
                    raise ValueError(f'Clipped artwork in {svg.name}: {ident} {boxes[ident]}')
            info=subprocess.check_output(['pdfinfo',str(output/record['outputs']['pdf']['path'])],text=True)
            size=re.search(r'Page size:\s+([\d.]+) x ([\d.]+) pts',info)
            if not size or any(abs(float(value)-expected*.75)>.1 for value,expected in zip(size.groups(),(page_w,page_h))):
                raise ValueError('PDF dimensions differ from SVG')
        checks.append({'plate':record['plate'],'scope':record['scope'],'kind':record['kind'],'passed':True})
    sites=[r for r in evidence['records'] if r['kind']=='antenna-site' and r['aperture_proxy_m2'] is not None]
    old=[r['previous_radius_inches'] for r in sites];new=[r['radius_inches'] for r in sites]
    if abs((max(new)-min(new))/(max(old)-min(old))-2)>1e-10:
        raise ValueError('Radius span did not double')
    points=[r for r in evidence['records'] if r['kind']!='link']
    clearance=min(math.dist(a['display_xy'],b['display_xy'])-a['radius_inches']-b['radius_inches']
                  for i,a in enumerate(points) for b in points[i+1:])
    if clearance<evidence['configuration']['layout']['collision_padding_inches']-1e-9:
        raise ValueError('Expanded groundstation symbols overlap')
    receipt={'schema':'cartofreako-slsl-validation-v1','sheets':checks,'exports_checked':exports,
             'astronomy_object_and_label_conservation':True,'radius_before_inches':[min(old),max(old)],
             'radius_after_inches':[min(new),max(new)],'radius_span_multiplier':2,
             'minimum_groundstation_clearance_inches':clearance}
    atomic_json(output/'validation.json',receipt)
    return receipt


def gallery(output, records):
    page=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">',
          '<title>Starlink Star Light / v3</title><style>body{background:#240413;color:#fcc553;font:18px system-ui;margin:2rem auto;max-width:1600px;padding:0 1rem}a{color:inherit}p{max-width:90ch;line-height:1.5}article{margin:3rem 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}img{width:100%;height:auto}figure{margin:0}figcaption{margin:.7rem 0}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>',
          '<h1>Starlink Star Light / v3</h1><p>Four perspectives, World and USA. Wine/amber maps; amber/wine A3 landscape legends. USA sky sheets retain celestial coordinates with mainland, Alaska and Hawaii locators. Source dates are explicit in each legend and the production record.</p>',
          '<p><a href="starlink-star-light-v3.pdf">All 16 sheets / vector PDF</a> · <a href="pod/format-proofs.pdf">Book format proofs</a> · <a href="plan.md">Plan and production record</a> · <a href="pod-options.md">IngramSpark options</a> · <a href="validation.json">Validation</a> · <a href="manifest.json">Manifest</a></p>']
    for plate in TITLES:
        for scope in ('world','usa'):
            page.append('<article><h2>'+html.escape(plate+' / '+TITLES[plate]+' / '+scope.upper())+'</h2><div class="pair">')
            for r in (r for r in records if r['plate']==plate and r['scope']==scope):
                links='<a href="'+r['svg']+'">SVG</a> · '+' · '.join('<a href="'+r['outputs'][key]['path']+'">'+key.upper()+'</a>' for key in ('pdf','png','svg.gz'))
                page.append('<figure><a href="'+r['outputs']['pdf']['path']+'"><img alt="'+plate+' '+scope+' '+r['kind']+'" loading="lazy" src="'+r['outputs']['webp']['path']+'"></a><figcaption>'+r['kind'].title()+' / '+links+'</figcaption></figure>')
            page.append('</div></article>')
    page.append('</html>')
    (output/'index.html').write_text('\n'.join(page)+'\n')


def book_proofs(output, records):
    """Actual-size comparison pages; explicitly a layout study, not press PDFs."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    path=output/'pod/format-proofs.pdf';path.parent.mkdir(parents=True,exist_ok=True)
    pdf=canvas.Canvas(str(path));pdf.setTitle('Starlink Star Light / IngramSpark format studies')
    comparisons=[]
    for title,w,h in [('A5 portrait',5.83,8.27),('Small square',8,8),('Landscape',11,8.5)]:
        scale=(w-1)/WIDTH
        comparisons.append({'format':title,'trim_inches':[w,h],'map_width_inches':w-1,
                            'full_map_scale':scale,'astronomy_label_pt':9.6*scale,'satellite_label_pt':6*scale})
        for plate in ('SLSL1','SLSL4'):
            pdf.setPageSize((w*72,h*72))
            pdf.setFillColor(HexColor(FG));pdf.rect(0,0,w*72,h*72,fill=1,stroke=0)
            pdf.setFillColor(HexColor(BG));pdf.setFont('Atkinson-Bold',17)
            pdf.drawString(36,h*72-48,title+' / '+plate)
            record=next(r for r in records if r['plate']==plate and r['scope']=='world' and r['kind']=='map')
            image_height=(w-1)*HEIGHT/WIDTH
            pdf.drawImage(str(output/record['outputs']['png']['path']),36,h*72-72-image_height*72,
                          width=(w-1)*72,height=image_height*72)
            y=h*72-96-image_height*72
            paragraphs=[f'Trim: {w:g} x {h:g} in. A 0.5-inch margin leaves {w-1:g} inches for the full-width map.',
                        f'At this reduction, 9.6 pt astronomy names become {9.6*scale:.2f} pt; 6 pt satellite text becomes {6*scale:.2f} pt.',
                        'Treat this overview as a visual index. Recompose the book with regional details and reflowed 10-11 pt notes; a miniature poster cannot carry readable labels.',
                        'FORMAT STUDY / RGB preview image. This is not a PDF/X interior, finished book, cover or publishing submission. See pod-options.md for the proposed page sequence.']
            pdf.setFont('Atkinson-Regular',10.5)
            for value in paragraphs:
                for line in wrap(value,10.5,w-1):
                    pdf.drawString(36,y,line);y-=14
                y-=8
            if y<36:
                raise ValueError('Book proof text overflow')
            pdf.showPage()
    pdf.save();atomic_json(output/'pod/format-comparison.json',comparisons)
    return comparisons


def write_plan(output, config, records, validation):
    dates={r['plate']:r['timestamp'] for r in records}
    sky_layout=next(r['layout']['sky'] for r in records if r['plate']=='SLSL1' and r['scope']=='world' and r['kind']=='map')
    lines=['# Starlink Star Light v3: production plan and record','',
           'Eight map views and eight companion legends. Maps retain the 44 x 19.052559 inch plate; legends are landscape A3 (420 x 297 mm).',
           '', '## Source selection', '',
           '| Plate | Calculation or source date |', '| --- | --- |',
           *[f'| {p}: {TITLES[p]} | {dates[p]} |' for p in TITLES], '',
           'SLSL1 uses the latest preserved accepted all-sky SVG by default. The November astronomy preview and its staged input directory documented elsewhere in this checkout are absent. No file has been relabeled as a newer calculation. An explicitly supplied `--astronomy-source` replaces that artwork and its date is read from the SVG.', '',
           'SLSL2 and SLSL3 are regenerated from the pinned November 9 CelesTrak snapshot. Natural Earth 5.1.1 supplies the global land. SLSL4 reuses the accepted source geometry and independently rebuilds the capability display from the supplied November 3 GeoJSON. Source paths and SHA-256 values are in `sources/input-manifest.json`.', '',
           '## Stages and validation', '',
           '| Stage | Result |', '| --- | --- |',
           '| Select and pin sources | Complete; dates remain distinct |',
           '| Rebuild orbital positions | Complete; 17,956 global objects, 972 above the San Francisco horizon |',
           '| Revise symbols, framing and typography | Complete; source positions and membership retained |',
           '| Compose World and USA | Complete; eight maps |',
           '| Compose reversed A3 legends | Complete; eight legends with observer notes |',
           '| Render and validate | '+('Complete; 16 SVG/PDF pairs, rendered bounds and PDF dimensions checked' if validation['exports_checked'] else 'SVG checks complete; exports explicitly skipped')+' |',
           '| Examine IngramSpark formats | Three options; see pod-options.md and pod/format-proofs.pdf |', '',
           '## Typography', '',
           '| Element | Before | After |', '| --- | ---: | ---: |',
           '| SLSL1 element names, World | 12 pt | 9.6 pt |',
           '| SLSL1 element names, USA | 12 pt | 9.6 pt |',
           '| SLSL2 Starlink names, both views | 6 pt | 6 pt |',
           '| SLSL3 Starlink IDs, World | 6 pt | 6 pt |',
           '| A3 legend title / headings | Reflowed from the wide source sheet | 27 / 15 pt |',
           '| A3 legend observer / body / sources | Reflowed from the wide source sheet | 12 / 11 / 10.5 pt |', '',
           'All numbers are physical points. SLSL1 type is compensated for each viewport scale, so the USA context layout does not reduce the text a second time. Labels move inward where their measured text width crosses the frame. Object coordinates and scientific attributes remain unchanged. The celestial composition is centered, without the former cyclic clipping window. SLSL3 USA panels magnify the 6 pt master type with the underlying map.', '',
           f'SLSL1 World left and right frame margins are halved from {sky_layout["previous_side_margin_inches"]:.6f} to {sky_layout["side_margin_inches"]:.6f} inches each. Uniform enlargement preserves the projection proportions; the actual rendered glyphs, rays and labels are checked against every page edge. The USA sky viewport also halves its internal side gutters.', '',
           '## Groundstation encoding', '',
           '| Source capability | Marker |', '| --- | --- |',
           *[f'| {CAPABILITIES[k][0]} | {v} |' for k,v in config['capability_markers'].items()], '',
           'The display radius follows `r_new = 0.04 + 2 * (r_previous - 0.04)` in source inches. This defines “2x more variance” as twice the low-to-high radius span; mathematical variance would increase fourfold. The aperture calculation remains the largest complete listed bank, `max(N * pi * D^2 / 4)`, never a sum across bands.', '',
           f'Before: {validation["radius_before_inches"][0]:.6f} to {validation["radius_before_inches"][1]:.6f} in. After: {validation["radius_after_inches"][0]:.6f} to {validation["radius_after_inches"][1]:.6f} in. Unknown-radius records remain 0.055 in; PoPs remain 0.032 in.', '',
           'Every capability silhouette encloses the same area at equal radius (`area = r_new^2`), while remaining within the collision radius. Recomputed hexagonal placement prevents larger symbols overlapping; tethers retain source registration. Radius expansion means the final symbol area is no longer linearly proportional to aperture. The full 590 antenna records, 66 PoPs and 124 source links remain. Unknowns, incomplete inventories and status claims retain their source meaning.', '',
           'The filled continental land and consolidated Antarctic inset are absent from SLSL4. No artificial coast outlines are derived from tessellation boundaries. SLSL3 retains the accepted world Antarctic basemap inset.', '',
           'This groundstation presentation is also the saved default for current and retained atlas builds through generation-style.json. Both use the same renderer and recipe, with source-specific capability evidence and matching legends; a current build uses its dataset-bound profile.', '',
           '## USA and observer semantics', '',
           'The terrestrial detail panels cover the contiguous USA, Alaska including the Aleutians, and Hawaii including the northwest islands. Panel scales are independent and their bounding rectangles include neighboring geography. SLSL4 extends those rectangles to contain every geographically selected record after collision displacement, including each complete symbol. The geographic bounds and original projected extents are in the input manifest; expanded groundstation extents and selected source IDs are in the sheet layout receipt.', '',
           'Celestial coordinates cannot be cropped to US longitude and latitude. The USA SLSL1 and SLSL2 sheets retain their full celestial data and add three geographic locators. San Francisco remains the observer/reference location; the other locators do not claim a sky calculation from Alaska or Hawaii. Each legend explains its relationship to all four perspectives.', '',
           '## Reproduction', '', '```sh',
           'make DATASET=legacy starlink-star-light-v3',
           'make DATASET=legacy check-starlink-star-light-v3', '```', '',
           'The build needs the repository native compiler prerequisites, lxml, Pillow, Shapely, ReportLab, Inkscape, fontconfig and Poppler. It uses `build/slsl-venv/bin/python` when available; `SLSL_PYTHON` overrides it. `SLSL_LAND_DIR` selects an existing Natural Earth 10m land directory. The full existing fetch target is `make fetch-natural-earth-10m`. The focused first run used the land-only archive recorded in the development record. Native inputs can be supplied with `--native` and a newer all-sky SVG with `--astronomy-source`.', '',
           'PDFs are vector review plates; PNG and WebP are 2560-pixel previews. The six-page book comparison is a layout study. These RGB artifacts are not PDF/X press interiors or covers.', '']
    (output/'plan.md').write_text('\n'.join(lines))
    pod=(ROOT/'docs/development/20261109_starlink_star_light_v3_pod.md').read_text()
    pod=pod.replace('../../output/starlink-star-light-v3-20261109/','')
    (output/'pod-options.md').write_text(pod)


def verify_delivery(output):
    output=Path(output).resolve()
    status=json.loads((output/'build-status.json').read_text())
    if status['state']!='complete':
        raise ValueError('Delivery has no completed export receipt')
    manifest=json.loads((output/'manifest.json').read_text())
    if digest(output/'manifest.json')!=status['manifest_sha256']:
        raise ValueError('Delivery manifest changed after completion')
    if len(manifest['records'])!=16 or not manifest['validation']['exports_checked']:
        raise ValueError('Incomplete map/legend delivery')
    for record in manifest['files']:
        path=(output/record['path']).resolve()
        if not path.is_relative_to(output) or digest(path)!=record['sha256']:
            raise ValueError('Changed or missing delivery artifact: '+record['path'])
    for record in manifest['records']:
        root=read_svg(output/record['svg'])
        companion=(output/record['svg']).parent/root.get('data-companion')
        if not companion.is_file():
            raise ValueError('Broken map/legend companion')
    print('Verified 16 sheets and',len(manifest['files']),'delivery files')


def build(config_path=CONFIG, output=None, native=None, astronomy=None, workers=2, preview_width=2560, exports=True):
    config_path=Path(config_path).resolve()
    register_fonts();config=json.loads(config_path.read_text())
    output=Path(output or ROOT/config['output']).resolve();output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/'build-status.json',{'state':'building'})
    native=Path(native or ROOT/config['orbital_native_directory']).resolve()
    projection=Projection('authagraph',output/'sources/projection')
    _,recipe=settings(STYLE)
    inputs=[]
    land_archive=ROOT/'build/starlink-star-light-v3/native-data/ne_10m_land.zip'
    if land_archive.is_file():
        inputs.append({'role':'natural-earth-download','path':str(land_archive.relative_to(ROOT)),
                       'sha256':digest(land_archive),'url':'https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip',
                       'version':'5.1.1'})
    for name,record in config['sources'].items():
        path=ROOT/record['path']
        if digest(path)!=record['sha256']:
            raise ValueError('Pinned artwork changed: '+str(path))
        inputs.append({'role':name,'path':record['path'],'sha256':digest(path)})
    sky_document=read_svg(astronomy or ROOT/config['sources']['astronomy']['path'])
    dimensions=list(map(float,sky_document.get('viewBox').split()))
    if any(abs(a-b)>1e-6 for a,b in zip(dimensions,(0,0,WIDTH,HEIGHT))):
        raise ValueError('An AuthaGraph 44 x 19.052559 inch all-sky source is required')
    sky=source_group(sky_document)
    if sky.xpath('.//*[@id="astro-metadata"]')[0].get('data-product')!='all-sky':
        raise ValueError('SLSL1 requires the complete all-sky product')
    if astronomy:
        inputs.append({'role':'selected-astronomy','path':str(astronomy),'sha256':digest(astronomy)})
        # Fresh native astronomy uses the same source colors with theme text.
        for n in sky.xpath('.//*[local-name()="text"]'):
            paint(n.attrib,fill=FG,stroke='none')
    profile_path=ROOT/config['orbital_profile'];profile=json.loads(profile_path.read_text())
    native_maps={p:read_svg(native/(STEMS[p]+SUFFIX+'.svg')) for p in ('SLSL2','SLSL3')}
    for plate,root in native_maps.items():
        metadata=root.xpath('//*[@id="orbital-technosphere-metadata"]')[0]
        if metadata.get('data-timestamp')!=profile['timestamp']:
            raise ValueError('Orbital native SVG does not match selected snapshot')
        inputs.append({'role':plate,'path':str(native/(STEMS[plate]+SUFFIX+'.svg')),
                       'sha256':digest(native/(STEMS[plate]+SUFFIX+'.svg'))})
    orbital=output/'sources/orbital';orbital.mkdir(parents=True,exist_ok=True)
    for name in ('orbital-technosphere-profile.json','acquisition.json','SHA256SUMS'):
        path=profile_path.parent/name
        (orbital/name).write_bytes(path.read_bytes())
        inputs.append({'role':'orbital-input','path':str(path.relative_to(ROOT)),'sha256':digest(path)})
    ground,evidence=refine_groundstations(read_svg(ROOT/config['sources']['groundstations']['path']),config,projection)
    atomic_json(output/'sources/capability-evidence.json',evidence)
    sources={'SLSL1':sky,'SLSL2':orbital_source(native_maps['SLSL2'],'SLSL2',recipe),
             'SLSL3':orbital_source(native_maps['SLSL3'],'SLSL3',recipe),'SLSL4':ground}
    locator=make_locator(native_maps['SLSL3'].xpath('//*[@id="terrestrial-land"]')[0],projection)
    regions=[dict(r,projected_bounds=region_bounds(projection,r)) for r in config['regions']]
    timestamps={p:profile['timestamp'] for p in ('SLSL2','SLSL3')}
    timestamps['SLSL1']=sky.xpath('.//*[@id="astro-metadata"]')[0].get('data-timestamp')
    timestamps['SLSL4']='source snapshot 2026-11-03'
    atomic_json(output/'sources/input-manifest.json',{'inputs':inputs,'config_sha256':digest(config_path),
                'style_sha256':digest(ROOT/'generation-style.json'),'timestamps':timestamps,
                'astronomy_availability':'explicit source override' if astronomy else 'latest preserved artwork; November preview/export directories absent',
                'regions':regions,'recipe':recipe})
    records=[]
    for plate,source in sources.items():
        for scope in ('world','usa'):
            selected_regions=groundstation_regions(regions,evidence) if plate=='SLSL4' and scope=='usa' else regions
            root,details=make_map(plate,scope,source,locator,config,selected_regions)
            if plate=='SLSL4' and scope=='usa':
                details['groundstation_regions']=selected_regions
            legend=make_legend(plate,scope,source,config,profile,evidence,timestamps[plate])
            for kind,tree in (('map',root),('legend',legend)):
                stem=plate.lower()+'-'+STEMS[plate]+('-legend' if kind=='legend' else '')
                path=output/(kind+'s')/scope/'svg'/(stem+'.svg')
                tree.set('data-calculation-or-source-date',timestamps[plate])
                companion=output/('legends' if kind=='map' else 'maps')/scope/'svg'/(plate.lower()+'-'+STEMS[plate]+('-legend' if kind=='map' else '')+'.svg')
                tree.set('data-companion',os.path.relpath(companion,path.parent))
                save(tree,path)
                records.append({'plate':plate,'scope':scope,'kind':kind,'svg':str(path.relative_to(output)),
                                'svg_sha256':digest(path),'timestamp':timestamps[plate],'layout':details if kind=='map' else {'size_mm':config['legend_mm']}})
            print('Composed',plate,scope,flush=True)
    env=font_environment()
    if exports:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            records=list(pool.map(lambda r:export(r,output,env,preview_width),records))
        subprocess.run(['pdfunite',*[str(output/r['outputs']['pdf']['path']) for r in records],str(output/'starlink-star-light-v3.pdf')],check=True)
        book_proofs(output,records)
        gallery(output,records)
    result=validate(output,records,sources,config,evidence,env,exports)
    write_plan(output,config,records,result)
    files=[{'path':str(p.relative_to(output)),'sha256':digest(p),'bytes':p.stat().st_size}
           for p in sorted(output.rglob('*')) if p.is_file() and p.name not in ('manifest.json','build-status.json')
           and 'export-logs' not in p.parts]
    atomic_json(output/'manifest.json',{'schema':'cartofreako-slsl-v3','configuration':config,'records':records,
                'input_manifest_sha256':digest(output/'sources/input-manifest.json'),'validation':result,'files':files,
                'implementation':{str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__),config_path,
                                    ROOT/'scripts/build-groundstation-capabilities.py',ROOT/'scripts/build-starlink-star-light.py')}})
    atomic_json(output/'build-status.json',{'state':'complete' if exports else 'svg-only',
                                          'manifest_sha256':digest(output/'manifest.json')})
    return output,records,result
