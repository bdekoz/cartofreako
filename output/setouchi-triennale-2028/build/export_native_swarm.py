#!/usr/bin/env python3
"""Export the complete native world swarm with librsvg/Cairo, without sampling."""
from pathlib import Path
import gi,cairo,json,hashlib,os,io,xml.sax,sys
from xml.sax.saxutils import XMLGenerator
from PIL import Image
gi.require_version('Rsvg','2.0')
from gi.repository import Rsvg
OUT=Path(__file__).resolve().parents[1]
os.environ.setdefault('XDG_CACHE_HOME','/tmp/cartofreako-render-cache')
source=Path(sys.argv[1]).resolve()
scope=source.parents[1].name
band='ge-1080p' if 'ge-1080p' in source.stem else 'lt-1080p'
partition=json.loads((OUT/'sources'/('network-swarm-'+band+'.json')).read_text())
expected=partition['native_circles' if scope=='world' else 'japan_visible_circles']
pdf=OUT/f'plates/{scope}/pdf'/source.with_suffix('.pdf').name
png=OUT/f'plates/{scope}/png'/source.with_suffix('.png').name
preview=OUT/f'previews/{scope}'/png.name
class Definitions(xml.sax.ContentHandler):
    def __init__(self):self.depth=0;self.common=[]
    def startElement(self,name,attrs):
        if self.depth or name in ['defs','style']:
            if not self.depth:self.buffer=io.StringIO();self.writer=XMLGenerator(self.buffer,encoding='utf-8')
            self.depth+=1;self.writer.startElement(name,dict(attrs))
    def characters(self,text):
        if self.depth:self.writer.characters(text)
    def endElement(self,name):
        if self.depth:
            self.writer.endElement(name);self.depth-=1
            if not self.depth:self.common.append(self.buffer.getvalue())
print('Collecting native clip definitions and colour styles',flush=True)
definitions=Definitions();xml.sax.parse(str(source),definitions)
common=''.join(definitions.common)
pdf_surface=cairo.PDFSurface(str(pdf)+'.tmp',3168,19.052559*72)
pdf_surface.set_metadata(cairo.PDF_METADATA_TITLE,'Dan Da Dan / AuthaGraph / '+partition['title']+' / '+scope)
png_surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,13200,5716)
class Layers(xml.sax.ContentHandler):
    # Bound librsvg memory while preserving source element order, ancestor transforms,
    # clipping, circle geometry and CSS. Only open group wrappers repeat between layers.
    def __init__(self):self.stack=[];self.skip=0;self.count=0;self.layer_count=0;self.total=0;self.new_layer()
    def new_layer(self):
        self.buffer=io.StringIO();self.writer=XMLGenerator(self.buffer,encoding='utf-8')
        for name,attrs in self.stack:
            self.writer.startElement(name,attrs)
            if name=='svg':self.buffer.write(common)
        self.count=0
    def render(self):
        handle=Rsvg.Handle.new_from_data(self.buffer.getvalue().encode());handle.set_dpi(96)
        for surface,width,height in [(pdf_surface,3168,19.052559*72),(png_surface,13200,5716)]:
            context=cairo.Context(surface);viewport=Rsvg.Rectangle();viewport.x=viewport.y=0;viewport.width=width;viewport.height=height
            assert handle.render_document(context,viewport)
        self.layer_count+=1
        if self.layer_count%5==0:print('Rendered',self.total,'native circles in',self.layer_count,'ordered layers',flush=True)
    def startElement(self,name,attrs):
        if self.skip or name in ['defs','style']:self.skip+=1;return
        if name=='g':
            assert 'opacity' not in attrs and not any(x.strip().startswith('opacity:') for x in attrs.get('style','').split(';')),'Group compositing opacity needs a different partition boundary'
        if name=='circle' and self.count>=50000:
            for tag,_ in reversed(self.stack):self.writer.endElement(tag)
            self.render();self.new_layer()
        self.stack.append((name,dict(attrs)));self.writer.startElement(name,dict(attrs))
        if name=='svg':self.buffer.write(common)
        if name=='circle':self.count+=1;self.total+=1
    def characters(self,text):
        if not self.skip:self.writer.characters(text)
    def endElement(self,name):
        if self.skip:self.skip-=1;return
        self.writer.endElement(name);self.stack.pop()
    def endDocument(self):self.render()
print('Rendering complete vector PDF and 300 dpi PNG in ordered layers',flush=True)
layers=Layers();xml.sax.parse(str(source),layers);assert layers.total==expected,(layers.total,expected)
pdf_surface.finish();Path(str(pdf)+'.tmp').replace(pdf)
raw=Path(str(png)+'.tmp');png_surface.write_to_png(str(raw));png_surface.finish()
with Image.open(raw) as opened:
    image=opened.convert('RGB');image.save(png,dpi=(300,300));image.thumbnail((1600,693),Image.Resampling.LANCZOS);image.save(preview)
raw.unlink()
receipt={'renderer':'librsvg '+'.'.join(map(str,[Rsvg.MAJOR_VERSION,Rsvg.MINOR_VERSION,Rsvg.MICRO_VERSION]))+' / Cairo '+cairo.cairo_version_string(),'scope':scope+' / '+band,'reason':'Bounded-memory export retains every native circle and original paint order','source':str(source.relative_to(OUT)),'source_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),'native_circles_retained':layers.total,'ordered_layers':layers.layer_count,'partitioning':'50,000 circles per layer; source paint order, ancestor transforms, clipping and styles retained. No group compositing opacity is permitted across split boundaries.','vector_pdf':True,'fonts':'embedded by Cairo','png_pixels':[13200,5716],'png_dpi':300,'preview':'downsampled from full-resolution PNG'}
(OUT/'sources'/('swarm-export-'+scope+'-'+band+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print('Native world swarm PDF / PNG / preview complete',flush=True)
