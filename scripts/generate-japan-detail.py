#!/usr/bin/env python3
"""Generate a geographic Japan companion with the shared physical stroke defaults."""
from cartofreako_style import ROOT, STYLE, Projection, E, digest, el, txt, save, swarm_label_attributes
from pathlib import Path
import argparse, io, json, re, subprocess, tempfile, textwrap, xml.sax
from xml.sax.saxutils import XMLGenerator

def divided(value,scale):
    match=re.fullmatch(r'([0-9.eE+-]+)([a-z]*)',value)
    if not match:raise ValueError('Unsupported SVG measurement: '+value)
    return format(float(match[1])/scale,'.12g')+match[2]

class Detail(xml.sax.ContentHandler):
    def __init__(self,stream,scale,visible):
        self.writer=XMLGenerator(stream,encoding='utf-8');self.scale=scale;self.visible=visible
        self.stack=[];self.legends=[];self.legend_depth=0;self.swarm=False;self.total=0;self.shown=0
    def startElement(self,name,attrs):
        a=dict(attrs);depth=len(self.stack)
        if not depth:
            self.swarm='data-resolution-partition' in a
            self.stack.append((name,a,False));return
        if self.legend_depth:
            self.collector.startElement(name,a);self.legend_depth+=1;self.stack.append((name,a,False));return
        if 'legend' in a.get('id','') and name=='g':
            self.buffer=io.StringIO();self.collector=XMLGenerator(self.buffer,encoding='utf-8')
            self.collector.startElement(name,a);self.legend_depth=1;self.stack.append((name,a,False));return
        parents={item[1].get('id','') for item in self.stack}
        keep=depth==1 or self.stack[-1][2]
        style=dict(part.strip().split(':',1) for part in a.get('style','').split(';') if ':' in part)
        if name=='path' and parents.intersection({'coastline','terrestrial-coastline'}):
            style['stroke-width']=str(STYLE['coastline']['japan_width_pt']/72/self.scale)
        if name=='path' and 'rivers' in parents:
            style['stroke-width']=str(STYLE['water']['japan_river_width_pt']/72/self.scale)
            style['stroke-opacity']=str(STYLE['water']['river_opacity'])
        if a.get('data-fiber-route')=='true' or a.get('data-itu-fiber-route')=='true':
            style['stroke-width']=str(STYLE['fiber']['width_pt']/72/self.scale)
            style['stroke-opacity']=str(STYLE['fiber']['opacity'])
        if a.get('data-fiber-landing')=='true':
            a['r']=str(float(a['r'])*STYLE['fiber']['japan_landing_radius_multiplier'])
            style['stroke-width']=str(STYLE['fiber']['japan_landing_outline_pt']/72/self.scale)
        if self.swarm and name=='circle':
            self.total+=1
            if STYLE['swarm']['japan_preserve_physical_circle_area']:a['r']=divided(a['r'],self.scale)
            x,y,radius=(float(a[k])/96 for k in ['cx','cy','r'])
            left,top,right,bottom=self.visible
            keep=keep and x+radius>=left and x-radius<=right and y+radius>=top and y-radius<=bottom
            self.shown+=keep
        if name=='text' and (self.swarm or 'cdn-labels' in parents):
            if 'font-size' in a:a['font-size']=divided(a['font-size'],self.scale)
            if 'stroke-width' in a:a['stroke-width']=divided(a['stroke-width'],self.scale)
            if 'stroke-width' in style:style['stroke-width']=divided(style['stroke-width'],self.scale)
        if style:a['style']=';'.join(k+':'+v for k,v in style.items())
        if self.swarm and name in ('text','tspan') and any('text-geolocation-text' in identifier for identifier in parents):
            a=swarm_label_attributes(a)
        if keep:self.writer.startElement(name,a)
        self.stack.append((name,a,keep))
    def endElement(self,name):
        _,_,keep=self.stack.pop()
        if self.legend_depth:
            self.collector.endElement(name);self.legend_depth-=1
            if not self.legend_depth:self.legends.append(self.buffer.getvalue())
        elif keep:self.writer.endElement(name)
    def characters(self,text):
        if self.legend_depth:self.collector.characters(text)
        elif self.stack and self.stack[-1][2]:self.writer.characters(text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--projection',default=STYLE['default_projection'])
    parser.add_argument('--title');args=parser.parse_args()
    if args.source.resolve()==args.output.resolve():parser.error('The Japan output must differ from its world source.')
    if args.source.name.startswith(('astro-','orbital-technosphere-observer')):
        parser.error('A geographic crop is undefined for celestial plates; generate an observer-specific sky instead.')
    projection=Projection(args.projection)
    with args.source.open('rb') as stream:
        context=E.iterparse(stream,events=('start',),huge_tree=True)
        source_attributes=dict(next(context)[1].attrib)
        del context
    source_box=list(map(float,source_attributes['viewBox'].replace(',',' ').split()))
    if source_attributes.get('data-projection',projection.name)!=projection.name or any(abs(a-b)>1e-5 for a,b in zip(source_box,[0,0,projection.width,projection.height])):
        parser.error('Source projection or frame does not match --projection.')
    band=source_attributes.get('data-resolution-partition')
    boundary=json.loads((ROOT/'config/regions/japan-10m.geojson').read_text())['geometry']
    rings=[ring for poly in boundary['coordinates'] for ring in poly] if boundary['type']=='MultiPolygon' else boundary['coordinates']
    projected=[projection.project(ring) for ring in rings];points=[p for ring in projected for p in ring]
    xs,ys=zip(*points);pad=STYLE['japan']['boundary_padding_inches']
    box=[min(xs)-pad,min(ys)-pad,max(xs)-min(xs)+2*pad,max(ys)-min(ys)+2*pad]
    vx,vy,vw,vh=STYLE['japan']['viewport_inches'];scale=min(vw/box[2],vh/box[3])
    dx=vx+(vw-box[2]*scale)/2-box[0]*scale;dy=vy+(vh-box[3]*scale)/2-box[1]*scale
    visible=((vx-dx)/scale,(vy-dy)/scale,(vx+vw-dx)/scale,(vy+vh-dy)/scale)
    title=args.title or args.source.stem.removesuffix(projection.suffix).replace('-',' ')
    if band and not args.title:title='Network swarm / '+STYLE['swarm']['partitions'][band]
    doc=el('svg',width='44in',height='19.052559in',viewBox='0 0 44 19.052559',role='img',data_projection=projection.name)
    if band:
        doc.set('data-resolution-partition',band)
        doc.set('data-native-units-per-inch','96')
    el('title',doc).text='Japan / '+title;el('rect',doc,width=44,height=19.052559,fill='white')
    txt(doc,.7,.8,'JAPAN / '+title.upper(),.45,font_weight='bold')
    txt(doc,.7,1.35,projection.info['title']+' geographic detail / source dates and units retained',.23)
    defs=el('defs',doc);clip=el('clipPath',defs,id='japan-detail-viewport');el('rect',clip,x=vx,y=vy,width=vw,height=vh)
    args.output.parent.mkdir(parents=True,exist_ok=True);temporary=args.output.with_suffix('.svg.tmp')
    with temporary.open('w') as stream:
        stream.write(E.tostring(doc,encoding='unicode')[:-6])
        stream.write(f'<g clip-path="url(#japan-detail-viewport)"><g transform="translate({dx} {dy}) scale({scale})">')
        handler=Detail(stream,scale,visible);xml.sax.parse(str(args.source),handler)
        outline=el('g',id='japan-outline')
        for ring in projected:
            el('path',outline,d='M '+' L '.join(f'{x} {y}' for x,y in ring)+' Z',fill='none',stroke='#202020',stroke_width=STYLE['coastline']['japan_width_pt']/72/scale)
        stream.write(E.tostring(outline,encoding='unicode')+'</g></g>')
        notes=el('g',id='detail-notes');txt(notes,30,2.35,'READ THIS PLATE',.28,font_weight='bold')
        body=f"Japan and nearby countries in the parent projection. Coastlines are {STYLE['coastline']['japan_width_pt']:g} pt. Geographic enlargement preserves source observations and their dates; this viewport is not a Japan-only total."
        if handler.swarm and STYLE['swarm']['japan_preserve_physical_circle_area']:body+=' Native swarm circle areas use the same physical scale as the world plate, at 5% opacity.'
        for i,line in enumerate(textwrap.wrap(body,70)):txt(notes,30,2.9+i*.36,line,.23)
        txt(notes,.7,18.35,'44 × 19.052559 in / '+projection.info['title']+' / source: '+args.source.name,.2)
        if handler.legends:
            legend=el('svg',width=f'{projection.width}in',height=f'{projection.height}in',viewBox=f'0 0 {projection.width} {projection.height}')
            group=el('g',legend,id='detail-source-legend')
            for fragment in handler.legends:group.append(E.fromstring(fragment.encode()))
            with tempfile.TemporaryDirectory(prefix='cartofreako-legend-') as tmp:
                path=Path(tmp)/'legend.svg';save(legend,path)
                result=subprocess.run(['inkscape',str(path),'--query-id=detail-source-legend','--query-x','--query-y','--query-width','--query-height'],capture_output=True,text=True,check=True)
                lx,ly,lw,lh=[float(v)/96 for v in result.stdout.split()]
            fit=min(12.8/lw,6.3/lh)
            wrapper=el('g',notes,transform=f'translate(30 10.5) scale({fit}) translate({-lx} {-ly})')
            for child in group:wrapper.append(child)
        stream.write(E.tostring(notes,encoding='unicode')+'</svg>')
    temporary.replace(args.output)
    receipt=dict(source=str(args.source),source_sha256=digest(args.source),projection=projection.name,
                 world_viewbox=box,geographic_scale=scale,style_sha256=digest(ROOT/'generation-style.json'))
    if handler.swarm:receipt.update(native_circles=handler.total,japan_visible_circles=handler.shown)
    args.output.with_suffix('.provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Generated Japan detail:',args.output,flush=True)

if __name__=='__main__':main()
