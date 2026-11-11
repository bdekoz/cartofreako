#!/usr/bin/env python3
"""Annotated, source-backed PDF comparing the November 3 and 9 observer plates."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from zoneinfo import ZoneInfo

from PIL import Image
import starlink_star_light as S

ROOT=S.ROOT
OLD=ROOT/'output/msp-speculations-20261103/msp-speculation-5/wine-amber/orbital-technosphere-observer-authagraph-44-19.052559.svg.gz'
NEW=ROOT/'output/starlink-star-light-world-20261110/maps/world/svg/slsl2-orbital-technosphere-observer.svg'
URL='https://benjamin.dekosnik.com/wp-content/uploads/2026/11/cartofreako-orbital-technosphere-observer-authagraph-44-19.052559-scaled.png'
OUT=ROOT/'output/orbital-observer-nov3-nov9-comparison'
W,H=420/25.4*72,297/25.4*72
M=44
INK,PAPER,WINE,CYAN,PINK='#240413','#fffaf0','#240413','#29d4e0','#ff6eae'


def txt(root,x,y,value,size=14,color=INK,bold=False,**attrs):
    n=S.el('text',root,x=x,y=y,font_family='Atkinson Hyperlegible',font_size=size,
           font_weight=700 if bold else 400,fill=color,**attrs);n.text=value;return n


def para(root,x,y,value,width,size=14,color=INK):
    for line in S.wrap(value,size,width/72):
        txt(root,x,y,line,size,color);y+=size*1.38
    return y+9


def section(root,x,y,title,value,width,size=14):
    txt(root,x,y,title,17,bold=True)
    return para(root,x,y+26,value,width,size)


def page(number,title,lead):
    r=S.el('svg',width='420mm',height='297mm',viewBox=f'0 0 {W} {H}',id=f'comparison-page-{number}')
    S.el('rect',r,width=W,height=H,fill=PAPER)
    txt(r,M,28,'ORBITAL TECHNOSPHERE / OBSERVER COMPARISON',10,bold=True)
    txt(r,M,64,title,29,bold=True)
    para(r,M,94,lead,W-2*M,15)
    S.el('line',r,x1=M,y1=H-44,x2=W-M,y2=H-44,stroke='#cbbcae',stroke_width='.6')
    txt(r,M,H-24,'Sources and reproducible calculations: page 8 / evidence.json',10)
    txt(r,W-M,H-24,f'{number:02d} / 08',10,text_anchor='end')
    return r


def embed(root,art,x,y,width,height,prefix):
    copy=deepcopy(art)
    ids={n.get('id'):prefix+n.get('id') for n in copy.iter() if isinstance(n.tag,str) and n.get('id')}
    for n in copy.iter():
        if not isinstance(n.tag,str):continue
        if n.get('id'):n.set('id',ids[n.get('id')])
        for key,value in list(n.attrib.items()):
            if value.startswith('#') and value[1:] in ids:value='#'+ids[value[1:]]
            value=re.sub(r'url\(#([^)]+)\)',lambda m:'url(#'+ids.get(m[1],m[1])+')',value)
            n.set(key,value)
    copy.set('x',str(x));copy.set('y',str(y));copy.set('width',str(width));copy.set('height',str(height))
    copy.set('preserveAspectRatio','xMidYMid meet');root.append(copy);return copy


def map_view(root,art,x,y,width,prefix):
    height=width*S.HEIGHT/S.WIDTH
    embed(root,art,x,y,width,height,prefix)
    return x,y,width,height


def raster(root,path,x,y,width):
    with Image.open(path) as im:height=width*im.height/im.width
    n=S.el('image',root,x=x,y=y,width=width,height=height)
    n.set('{'+S.XL+'}href','data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode())
    return x,y,width,height


def screen(point):
    x,y=point
    return S.FRAMING.DX+S.FRAMING.SCALE*((x+S.FRAMING.SHIFT)%S.WIDTH),S.FRAMING.DY+S.FRAMING.SCALE*y


def points(node):
    values=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',node.get('d',''))]
    return list(zip(values[::2],values[1::2]))


def nearest(root,kind,fx,fy):
    xy=[screen(p) for n in root.xpath('//*[starts-with(@id,$prefix)]',prefix=kind) for p in points(n)]
    return min(xy,key=lambda p:(p[0]/S.WIDTH-fx)**2+(p[1]/S.HEIGHT-fy)**2)


def pin(root,box,point,label,color=CYAN):
    bx,by,bw,bh=box;px=bx+point[0]/S.WIDTH*bw;py=by+point[1]/S.HEIGHT*bh
    S.el('circle',root,cx=px,cy=py,r=12,fill=PAPER,stroke=color,stroke_width=2)
    txt(root,px,py+4,label,12,WINE,True,text_anchor='middle')


def curves(old,new=None):
    doc=S.el('svg',width='44in',height=f'{S.HEIGHT}in',viewBox=f'0 0 44 {S.HEIGHT}')
    S.el('rect',doc,width=44,height=S.HEIGHT,fill=WINE)
    defs=S.el('defs',doc)
    clip=S.el('clipPath',defs,id='curve-window');S.el('rect',clip,width=44,height=S.HEIGHT)
    items=[('equator',old,'celestial-equator','#cccccc','',.035),('old-horizon',old,'observer-horizon',CYAN,'',.055)]
    if new is not None:items.append(('new-horizon',new,'observer-horizon',PINK,'.18 .11',.055))
    for ident,source,prefix,color,dash,weight in items:
        bank=S.el('g',defs,id=ident)
        for n in source.xpath('//*[starts-with(@id,$prefix)]',prefix=prefix):
            if S.E.QName(n).localname!='path':continue
            S.el('path',bank,d=n.get('d'),fill='none',stroke=color,stroke_width=weight,stroke_dasharray=dash)
        frame=S.el('g',doc,transform=f'translate({S.FRAMING.DX} {S.FRAMING.DY}) scale({S.FRAMING.SCALE})')
        window=S.el('g',frame,clip_path='url(#curve-window)')
        for offset in (-39.6,4.4,48.4):S.el('use',window,transform=f'translate({offset} 0)').set('{'+S.XL+'}href','#'+ident)
    return doc


def previous_horizon_overlay(current,old):
    result=deepcopy(current)
    overlay=curves(old)
    S.remove(overlay,'./*[local-name()="rect"]')
    S.remove(overlay,'.//*[@id="equator"]')
    # Remove the equator uses as well; retain only the previous horizon.
    for use in overlay.xpath('.//*[local-name()="use"]'):
        if use.get('{'+S.XL+'}href')=='#equator':use.getparent().remove(use)
    for path in overlay.xpath('.//*[local-name()="path"]'):
        path.set('stroke-dasharray','.18 .10')
    result.extend(list(overlay))
    return result


def utc(value):return datetime.fromisoformat(value.replace('Z','+00:00'))


def lst(instant):
    jd=instant.timestamp()/86400+2440587.5;t=(jd-2451545)/36525
    seconds=-6.2e-6*t**3+.093104*t*t+(876600*3600+8640184.812866)*t+67310.54841
    return (seconds/240-122.4194)%360


def horizon(orientation):
    phi=math.radians(37.7749);values=[]
    for az in range(361):
        a=math.radians(az)
        dec=math.degrees(math.asin(math.cos(phi)*math.cos(a)))
        hour=math.degrees(math.atan2(-math.sin(a),-math.sin(phi)*math.cos(a)))
        values.append(((orientation-hour)%360,dec))
    return values


def plot_horizons(path,angles):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/observer-comparison-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from legend_informatics import FONT_DIR
    font_manager.fontManager.addfont(str(FONT_DIR/'AtkinsonHyperlegible-Regular.ttf'))
    plt.rcParams.update({'font.family':'Atkinson Hyperlegible','font.size':13,'svg.fonttype':'path'})
    fig,ax=plt.subplots(figsize=(14.8,4.0),facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.axhline(0,color='#8c8585',lw=1.2,label='Celestial equator: fixed')
    for angle,color,label,dash in zip(angles,[CYAN,PINK],['Nov 3 horizon','Nov 9 horizon'],['-', '--']):
        data=horizon(angle);segments=[[]]
        for p in data:
            if segments[-1] and abs(p[0]-segments[-1][-1][0])>180:segments.append([])
            segments[-1].append(p)
        for i,segment in enumerate(segments):
            xs,ys=zip(*segment);ax.plot(xs,ys,color=color,lw=2.6,ls=dash,label=label if i==0 else None)
        ax.scatter([angle],[37.7749],color=color,s=65,marker='*',zorder=5)
        ax.annotate('Zenith', (angle,37.7749),xytext=(0,11),textcoords='offset points',ha='center',fontsize=11)
    ax.set(xlim=(0,360),ylim=(-80,80),xlabel='Right ascension (degrees) — increasing to the right in this explanatory diagram',ylabel='Declination (degrees)')
    ax.set_xticks(range(0,361,45));ax.set_yticks([-60,-30,0,30,60]);ax.grid(alpha=.18)
    ax.legend(loc='lower center',ncol=3,fontsize=12,frameon=False)
    fig.tight_layout();fig.savefig(path,format='svg');plt.close(fig)


def render_raster_reference_page(svg,pdf,current_preview):
    """Embed the unchanged PNG directly, without the system D-Bus image loader."""
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    c=canvas.Canvas(str(pdf),pagesize=(W,H))
    c.setTitle('Orbital technosphere / annotated observer comparison')
    for n in S.read_svg(svg):
        tag=S.E.QName(n).localname
        fill=n.get('fill','none');stroke=n.get('stroke','none')
        if fill!='none':c.setFillColor(HexColor(fill))
        if stroke!='none':c.setStrokeColor(HexColor(stroke))
        c.setLineWidth(float(n.get('stroke-width',1)))
        if tag=='rect':
            x,y,w,h=[float(n.get(k,0)) for k in ('x','y','width','height')]
            c.rect(x,H-y-h,w,h,fill=fill!='none',stroke=stroke!='none')
        elif tag=='line':
            c.line(float(n.get('x1')),H-float(n.get('y1')),float(n.get('x2')),H-float(n.get('y2')))
        elif tag=='circle':c.circle(float(n.get('cx')),H-float(n.get('cy')),float(n.get('r')),fill=fill!='none',stroke=stroke!='none')
        elif tag=='text':
            font='Atkinson-Bold' if n.get('font-weight')=='700' else 'Atkinson-Regular'
            c.setFont(font,float(n.get('font-size')))
            draw={'middle':c.drawCentredString,'end':c.drawRightString}.get(n.get('text-anchor'),c.drawString)
            draw(float(n.get('x')),H-float(n.get('y')),n.text or '')
        elif tag in ('image','svg'):
            if tag=='image':
                uri=n.get('{'+S.XL+'}href');im=ImageReader(BytesIO(base64.b64decode(uri.split(',',1)[1])))
            else:im=ImageReader(str(current_preview))
            x,y,w,h=[float(n.get(k,0)) for k in ('x','y','width','height')]
            c.drawImage(im,x,H-y-h,width=w,height=h)
    c.showPage();c.save()


def table(root,x,y,width,headers,rows,col_weights,size=13,row_height=31):
    starts=[x]
    for weight in col_weights[:-1]:starts.append(starts[-1]+width*weight)
    S.el('rect',root,x=x,y=y,width=width,height=row_height,fill='#eadfcf')
    for sx,value in zip(starts,headers):txt(root,sx+9,y+21,value,size,bold=True)
    for i,row in enumerate(rows):
        yy=y+(i+1)*row_height
        if i%2==0:S.el('rect',root,x=x,y=yy,width=width,height=row_height,fill='#f5ecdf')
        for sx,value in zip(starts,row):txt(root,sx+9,yy+21,str(value),size)
    return y+(len(rows)+1)*row_height


def build(reference,output):
    output.mkdir(parents=True,exist_ok=True);(output/'sources').mkdir(exist_ok=True)
    reference_copy=output/'sources/nov3-published-reference.png'
    if reference.resolve()!=reference_copy.resolve():shutil.copyfile(reference,reference_copy)
    S.register_fonts();old=S.read_svg(OLD);new=S.read_svg(NEW)
    om=old.xpath('//*[@id="orbital-technosphere-metadata"]')[0];nm=new.xpath('//*[@id="orbital-technosphere-metadata"]')[0]
    ot,nt=utc(om.get('data-timestamp')),utc(nm.get('data-timestamp'))
    angles=[lst(ot),lst(nt)];delta=(angles[1]-angles[0])%360
    oa={n.get('data-norad-id'):n for n in old.xpath('//*[@data-object-kind="locpoint"]')}
    na={n.get('data-norad-id'):n for n in new.xpath('//*[@data-object-kind="locpoint"]')}
    old_uses=[n.get('transform') for n in old.xpath('//*[local-name()="use"]')]
    new_uses=[n.get('transform') for n in new.xpath('//*[local-name()="use"]')]
    eq=lambda r:[n.get('d') for n in r.xpath('//*[starts-with(@id,"celestial-equator-segment-")]')]
    assert old_uses==new_uses==['translate(-39.6 0)','translate(4.4 0)','translate(48.4 0)']
    old_frame=old.xpath('//*[@id="st2-image-frame"]')[0].get('transform')
    new_frame=new.xpath('//*[@id="observer-image-frame"]')[0].get('transform')
    assert old_frame==new_frame
    assert eq(old)==eq(new)
    assert len(oa)==1088 and len(na)==972
    source_records=[{'path':str(p.relative_to(ROOT)),'sha256':S.digest(p)} for p in (OLD,NEW,ROOT/'src.generate/orbiting-generation.h',ROOT/'src.generate/orbiting-data.h',ROOT/'src.generate/third_party/sgp4/SGP4.cpp')]
    evidence={'question':'Why do the November 3 and November 9 observer plates look different?',
        'reference_url':URL,'reference_png_sha256':S.digest(reference_copy),'source_files':source_records,
        'nov3_metadata':dict(om.attrib),'nov9_metadata':dict(nm.attrib),'same_cyclic_framing':True,
        'native_shift_inches':4.4,'printed_shift_inches':4.35,'source_width_inches':44,
        'printed_image_width_inches':43.5,'scale':S.FRAMING.SCALE,'equator_path_geometry_identical':True,
        'elapsed_hours':(nt-ot).total_seconds()/3600,'local_sidereal_degrees':angles,'sidereal_phase_change_degrees':delta,
        'visible_sets':{'nov3':len(oa),'nov9':len(na),'shared':len(oa.keys()&na.keys()),'nov3_only':len(oa.keys()-na.keys()),'nov9_only':len(na.keys()-oa.keys())},
        'satellite_example':{day:dict(n.attrib) for day,n in [('nov3',oa['39078']),('nov9',na['39078'])]},
        'scientific_caveat':'The two catalogs and times differ; visible-population changes are not a causal estimate of catalog growth, satellite loss or time-only effects.',
        'external_sources':['https://aa.usno.navy.mil/data/siderealtime','https://aa.usno.navy.mil/faq/GAST']}
    S.atomic_json(output/'evidence.json',evidence)
    pages=[]
    r=page(1,'Same page frame; a different orientation of the sky',
        'November 3 reference versus the current November 9 observer plate / San Francisco, 37.7749° N, 122.4194° W, 16 m')
    txt(r,M,142,'Executive Summary',19,bold=True)
    y=para(r,M,170,'Both plates already use the same 4.35-inch printed cyclic move and the same 43.5-inch image width. The current framing is not rotated by 126°. The fixed celestial-equator paths match exactly. [1–3]',W-2*M,17)
    y=para(r,M,y,'The observation instants are 5 days, 8 hours and 2 minutes apart. Earth’s rotation changes the observer’s orientation relative to the celestial grid by 125.758° modulo complete turns. Reprojecting the new local horizon produces a very different curve. [2–5]',W-2*M,17)
    gap=28;pw=(W-2*M-gap)/2;py=305
    txt(r,M,py-15,'NOV 3 / 17:10 UTC / 09:10 PST',15,bold=True)
    txt(r,M+pw+gap,py-15,'NOV 9 / 01:12 UTC / NOV 8, 17:12 PST',15,bold=True)
    raster(r,reference_copy,M,py,pw);map_view(r,new,M+pw+gap,py,pw,'p1-new-')
    section(r,M,py+pw*S.HEIGHT/S.WIDTH+38,'Why this is more than a calendar-date comparison',
        'The local clock differs by 8 hours 2 minutes. At the same clock time exactly six days later, the residual sky rotation would be about 5.9°, after six complete turns. The six date numbers on the filenames are not six equal 24-hour steps at a fixed time of day.',W-2*M,15)
    para(r,M,H-104,'The plotted population also changes: 1,088 to 972 objects above the horizon. My earlier explanation overstated the role of restored framing; the current two-plate comparison has identical framing.',W-2*M,14)
    pages.append(r)

    r=page(2,'Annotated November 3 reference',
        'The supplied PNG is shown unchanged below; the date and counts come from the matching preserved editable SVG. [1,2]')
    box=raster(r,reference_copy,M,132,W-2*M)
    pin(r,box,nearest(old,'celestial-equator-segment-',.55,.7),'A')
    pin(r,box,nearest(old,'observer-horizon-segment-',.24,.70),'B')
    pin(r,box,(28,6),'C')
    pin(r,box,(15,17),'D')
    notes=[('A / Faint curve: celestial equator','Zero declination in the celestial coordinate grid. Its shape and placement are unchanged in the November 9 plate.'),
           ('B / Bright curve: local horizon','The 0° elevation boundary for San Francisco at 17:10 UTC. This is a sky-selection boundary, not an orbital path.'),
           ('C / Satellite marks and labels','1,088 objects pass the above-horizon test, including 549 Starlink objects. The source is a calculated catalog view, not a photograph.'),
           ('D / Empty part of the rectangle','Below-horizon directions remain in the full celestial frame but do not receive satellite marks. Empty space here is a selection effect.')]
    for i,(title,value) in enumerate(notes):
        col=i%2;row=i//2;section(r,M+col*((W-2*M)/2+10),642+row*77,title,value,(W-2*M)/2-26,12.3)
    pages.append(r)

    r=page(3,'November 9, annotated with the previous horizon',
        'Current plate: gold horizon and current satellite positions. Cyan dashed overlay: November 3 horizon, placed in the identical frame. [2,3]')
    box=map_view(r,previous_horizon_overlay(new,old),M,132,W-2*M,'p3-')
    pin(r,box,nearest(new,'celestial-equator-segment-',.58,.70),'A')
    pin(r,box,nearest(old,'observer-horizon-segment-',.25,.70),'B')
    pin(r,box,nearest(new,'observer-horizon-segment-',.52,.80),'C',PINK)
    pin(r,box,(35,9),'D',PINK)
    notes=[('A / Equator stays registered','The reference equator is exactly the same SVG path geometry in both sources. This is the cleanest check that the sky grid did not move on the paper.'),
           ('B / Previous horizon, cyan dashed','Only the old horizon is overlaid. Old satellite marks are omitted so a dashed line cannot be mistaken for a satellite trajectory.'),
           ('C / Current horizon, gold','The later observation samples a different celestial hemisphere above the same San Francisco horizon. Curvature changes after AuthaGraph projection.'),
           ('D / New satellite positions','972 objects are above the horizon, including 453 Starlink objects. Both their propagated positions and membership of the visible set can differ.')]
    for i,(title,value) in enumerate(notes):section(r,M+(i%2)*((W-2*M)/2+10),642+(i//2)*77,title,value,(W-2*M)/2-26,12.3)
    pages.append(r)

    r=page(4,'Remove the satellites: the horizon is what changes',
        'Co-registered source curves: November 3 horizon in cyan; November 9 horizon in pink dashes; shared celestial equator in gray.')
    box=map_view(r,curves(old,new),M,132,W-2*M,'p4-')
    pin(r,box,nearest(old,'celestial-equator-segment-',.60,.71),'A')
    pin(r,box,nearest(old,'observer-horizon-segment-',.53,.36),'B')
    pin(r,box,nearest(new,'observer-horizon-segment-',.90,.45),'C',PINK)
    section(r,M,646,'A / No frame adjustment was needed',
        'Both source SVGs use scale 43.5 / 44 = 0.98863636, translation (0.25, 0.108253) inches, and three cyclic copies at −39.6, +4.4 and +48.4 native inches. Their clipping rectangle is 44 × 19.052559 native inches.',(W-2*M)/2-20,14)
    section(r,W/2+10,646,'B–C / A moving boundary in a fixed celestial grid',
        'The horizon is fixed relative to the observer’s local ground, but its right ascension changes with Earth’s rotation. AuthaGraph is nonlinear: rotating this great circle on the sphere can turn a broad wave into steep, split curves on the flat plate.',(W-2*M)/2-20,14)
    pages.append(r)

    r=page(5,'What cyclic framing alone actually does',
        'Controlled comparison: both panels use the same November 9 source objects, horizon and time. Only the final horizontal display roll differs.')
    unshifted=deepcopy(new)
    for node,offset in zip(unshifted.xpath('//*[local-name()="use"]'),(-44,0,44)):node.set('transform',f'translate({offset} 0)')
    gap=28;pw=(W-2*M-gap)/2
    txt(r,M,145,'CONTROL / NO CYCLIC MOVE',15,bold=True);txt(r,M+pw+gap,145,'CURRENT / 4.35-INCH PRINTED MOVE',15,bold=True)
    b1=map_view(r,unshifted,M,163,pw,'p5-control-');b2=map_view(r,new,M+pw+gap,163,pw,'p5-current-')
    for box,fx,width in [(b1,.25+39.6*S.FRAMING.SCALE,4.35),(b2,.25,4.35)]:
        x,y,w,h=box
        S.el('rect',r,x=x+fx/44*w,y=y+S.FRAMING.DY/S.HEIGHT*h,width=width/44*w,height=43.5/44*h,
             fill=CYAN,fill_opacity='.14',stroke=CYAN,stroke_width=1.5)
    txt(r,M,435,'The cyan strip is the rightmost 10% of the native rectangle; it reappears at the left edge after the roll.',14)
    y=section(r,M,481,'Step 1 / Project celestial directions',
        'Convert each satellite’s topocentric right ascension and declination into AuthaGraph coordinates. The central right ascension is 12 h in both source profiles. This stage produces a native rectangle 44 inches wide.',W-2*M,15)
    y=section(r,M,y+4,'Step 2 / Move and wrap the already projected rectangle',
        'Add 4.4 native inches to every x coordinate, wrap at 44, then print the rectangle at 43.5 / 44 scale. A point at native x = 2 moves to 6.4. A point at x = 42 moves to 2.4 after wrapping. Every y coordinate stays unchanged.',W-2*M,15)
    txt(r,M,y+15,'x_print = 0.25 + (43.5 / 44) × ((x_native + 4.4) mod 44)',17,bold=True)
    txt(r,M,y+43,'y_print = 0.108253 + (43.5 / 44) × y_native',17,bold=True)
    para(r,M,y+80,'This is a 10% horizontal image roll, not 36° or 126° of physical sky rotation: AuthaGraph x is not a linear right-ascension axis. In the actual November 3 → November 9 comparison, this roll is already identical on both plates.',W-2*M,15)
    pages.append(r)

    r=page(6,'Why the same local horizon looks different',
        'Earth rotates the observer relative to the celestial grid before projection; cyclic framing moves the finished rectangle after projection. [4,5]')
    plot_path=output/'sources/horizon-right-ascension-declination.svg';plot_horizons(plot_path,angles)
    art=S.read_svg(plot_path);embed(r,art,M,136,W-2*M,300,'p6-plot-')
    y=table(r,M,461,W-2*M,['Quantity','November 3','November 9'],[
        ['UTC calculation time','Nov 3, 17:10','Nov 9, 01:12'],
        ['San Francisco clock (PST)','Nov 3, 09:10','Nov 8, 17:12'],
        ['Model local sidereal orientation',f'{angles[0]:.3f}°',f'{angles[1]:.3f}°'],
        ['Observer latitude / longitude','37.7749° N / 122.4194° W','same'],
        ['Cyclic printed move','4.35 inches','same']], [.40,.30,.30],14,31)
    para(r,M,y+25,f'The model sidereal phase changes by {delta:.3f}° after complete turns are removed. The horizon and zenith shift in right ascension; the equator remains at zero declination. “Above the horizon” means local elevation ≥ 0°, not necessarily above a curve on the printed page.',W-2*M,15)
    para(r,M,y+99,'An exactly 24-hour sequence would leave about 0.986° of residual rotation, rather than return to an identical sky orientation. A sidereal day is about 23 h 56 min; satellite positions still would not repeat.',W-2*M,14)
    pages.append(r)

    r=page(7,'The populations change as well as their placement',
        'Counts are unique plotted NORAD objects in each source, with the same ≥ 0° elevation threshold and the same observer location. [2,3]')
    count=lambda records,group:sum(n.get('data-display-group')==group for n in records.values())
    rows=[['Propagated global catalog',om.get('data-propagated-records'),nm.get('data-propagated-records')],
          ['Above local horizon',len(oa),len(na)],['Starlink above horizon',count(oa,'starlink'),count(na,'starlink')],
          ['Debris above horizon',count(oa,'objects-debris'),count(na,'objects-debris')],
          ['Epoch exclusions',om.get('data-skipped-stale'),nm.get('data-skipped-stale')],
          ['Sun altitude at observer','+24.617°','−2.351°']]
    table(r,M,145,(W-2*M)/2-15,['Population / measure','Nov 3','Nov 9'],rows,[.62,.19,.19],13,31)
    section(r,W/2+12,161,'Only 202 NORAD IDs appear in both visible sets',
        '886 appear only in the November 3 view; 770 appear only in the November 9 view. The net decrease of 116 visible objects is not evidence that 116 satellites disappeared. The global propagated catalog actually grows by 47 objects.',(W-2*M)/2-24,15)
    para(r,W/2+12,309,'Time, orbital motion, the elevation filter and refreshed elements/catalog membership all contribute. These two endpoints alone do not isolate each contribution. Both plates include objects that are not naked-eye visible.',(W-2*M)/2-24,14)
    txt(r,M,440,'A useful reference object: AMAZONAS 3 / NORAD 39078',19,bold=True)
    a,b=oa['39078'],na['39078']
    rows=[['Local azimuth',a.get('data-observer-azimuth-deg')+'°',b.get('data-observer-azimuth-deg')+'°'],
          ['Local elevation',a.get('data-observer-elevation-deg')+'°',b.get('data-observer-elevation-deg')+'°'],
          ['Topocentric right ascension',a.get('data-topocentric-ra-deg')+'°',b.get('data-topocentric-ra-deg')+'°']]
    table(r,M,461,W-2*M,['Coordinate','November 3','November 9'],rows,[.40,.30,.30],14,33)
    para(r,M,624,'This near-geostationary object stays at almost the same local azimuth and elevation. Its right ascension advances by about 125.757° modulo 360°, so its location on the fixed celestial-grid plate changes substantially. A large paper displacement does not necessarily mean a large change in local viewing direction.',W-2*M,15)
    para(r,M,720,'Presentation change to keep separate: current debris x marks are white; the older plate used black x marks with halos. This changes visibility of small symbols, not the geometry of the horizon or equator.',W-2*M,14)
    pages.append(r)

    r=page(8,'Sources, limits and reproducibility',
        'The overlays are explanatory additions. The published PNG and the current production SVG remain unchanged.')
    refs=[('[1] Published reference image',URL),
          ('[2] Matching November 3 editable plate',str(OLD.relative_to(ROOT))),
          ('[3] Current November 9 editable plate',str(NEW.relative_to(ROOT))),
          ('[4] Renderer and Earth-rotation calculation','src.generate/orbiting-generation.h: horizontal_to_equatorial, add_reference_lines, visible_in_product; src.generate/orbiting-data.h: topocentric_equatorial; src.generate/third_party/sgp4/SGP4.cpp: gstime_SGP4.'),
          ('[5] U.S. Naval Observatory / sidereal time','https://aa.usno.navy.mil/data/siderealtime — definition; https://aa.usno.navy.mil/faq/GAST — local-longitude relation and approximate GMST.')]
    y=146
    for title,value in refs:
        y=section(r,M,y,title,value,W-2*M,13.5)+7
    y=section(r,M,y,'What was verified',
        'Identical frame scales, translations and three cyclic-copy offsets; exact equality of all celestial-equator SVG paths; source-metadata counts reconciled to unique plotted NORAD IDs; matched-object coordinates read from both SVGs. The reference PNG visually matches the preserved November 3 artwork; its timestamp comes from the SVG metadata, not from the PNG filename.',W-2*M,14)
    y=section(r,M,y,'Precision and interpretation',
        'Sidereal values reproduce the renderer’s SGP4 GMST calculation using its UTC Julian-date input, plus San Francisco longitude. They describe this visualization; no higher-precision UT1 or apparent-sidereal correction is claimed. The RA/declination figure is an explanatory coordinate diagram, with zeniths marked by stars; it is not a new satellite propagation.',W-2*M,13.5)
    para(r,M,y,'Inputs, full SHA-256 values, metadata, formulas and matched-object evidence are saved in evidence.json. Rebuild: python3 scripts/build-orbital-observer-comparison.py --reference PATH_TO_REFERENCE_PNG. The hourly sequence and 1080p MKV proposal are documented separately in docs/development/20261109_starlink_star_light_v4_observer_orientation_relative_celestial_grid.md.',W-2*M,13)
    pages.append(r)

    svg_dir=output/'pages';svg_dir.mkdir(exist_ok=True)
    paths=[]
    for i,r in enumerate(pages,1):
        p=svg_dir/f'{i:02d}.svg';S.save(r,p);paths.append(p)
    env=S.font_environment()
    def render(path):
        pdf=path.with_suffix('.pdf')
        if path.stem in ('01','02'):
            render_raster_reference_page(path,pdf,NEW.parent.parent/'preview'/NEW.with_suffix('.png').name)
        else:
            subprocess.run(['bash',str(ROOT/'scripts/run-inkscape.sh'),'inkscape',str(path),'--export-area-page','--export-filename='+str(pdf)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        return pdf
    with ThreadPoolExecutor(max_workers=2) as pool:pdfs=list(pool.map(render,paths))
    result=output/'orbital-observer-nov3-vs-nov9-annotated.pdf'
    subprocess.run(['pdfunite',*map(str,pdfs),str(result)],check=True)
    info=subprocess.check_output(['pdfinfo',str(result)],text=True)
    assert re.search(r'Pages:\s+8\b',info)
    S.atomic_json(output/'manifest.json',{'pdf':result.name,'pdf_sha256':S.digest(result),
        'pages':8,'page_size_mm':[420,297],'builder_sha256':S.digest(Path(__file__)),
        'evidence_sha256':S.digest(output/'evidence.json'),'source_files':source_records})
    print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,default=OUT/'sources/nov3-published-reference.png')
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();build(args.reference.resolve(),args.output.resolve())
