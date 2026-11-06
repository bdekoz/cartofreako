"""Keep source hues and deduplicate repeated image objects in trial PDFs."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import subprocess
import zlib

import numpy as np
from PIL import Image
from lxml import etree

from legend_informatics import ROOT, digest
from setouchi_futures import write_json


def pikepdf_module():
    # Optional PDF tooling is isolated from the system Python environment.
    sys.path.append(str(ROOT / 'build/setouchi-h3-python'))
    import pikepdf
    return pikepdf


def optimize_pdf(path, svg, settings, receipt_path):
    pikepdf = pikepdf_module()
    old = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    if old and old['output_sha256'] == digest(path) and old['optimizer_sha256'] == digest(Path(__file__)):
        return old
    colors_by_alpha = {}
    tree = etree.parse(str(svg))
    for image in tree.xpath('//*[local-name()="image"]'):
        layer = image.getparent().get('id')
        colors = {tuple(round(v*255) for v in s[part][:3]) for s in settings['styles'][layer].values()
                  for part in ('fill', 'stroke') if s[part][3] > 0}
        if len(colors) == 1:
            png = svg.parent / image.get('{http://www.w3.org/1999/xlink}href')
            with Image.open(png) as source:
                alpha = source.getchannel('A').tobytes()
                colors_by_alpha[(source.width, source.height, sha256(alpha).hexdigest())] = next(iter(colors))
    original_hash, original_size = digest(path), path.stat().st_size
    normalized, max_error = 0, 0.0
    before_masks = set()
    aliases, canonical = {}, {}
    temporary = path.with_suffix('.optimized.pdf')
    with pikepdf.open(path) as pdf:
        images = [o for o in pdf.objects if isinstance(o, pikepdf.Stream) and o.get('/Subtype') == pikepdf.Name.Image]
        for obj in images:
            if '/SMask' not in obj: continue
            width, height = int(obj.Width), int(obj.Height)
            alpha = obj.SMask.read_bytes()
            bits = int(obj.SMask.BitsPerComponent)
            expected = ((width*bits+7)//8)*height
            if int(obj.SMask.Width)!=width or int(obj.SMask.Height)!=height or len(alpha)!=expected:
                raise ValueError('Unexpected PDF alpha-plane dimensions')
            key = width, height, sha256(alpha).hexdigest()
            before_masks.add(key)
            # Cairo can encode entirely transparent layers as 1-bit gray
            # images/masks. They have no visible hue to normalize.
            if bits != 8: continue
            color = colors_by_alpha.get(key)
            if color is None: continue
            if obj.ColorSpace != pikepdf.Name.DeviceRGB or int(obj.BitsPerComponent) != 8:
                raise ValueError('Expected RGB8 trial image')
            pixels = obj.read_bytes()
            if len(pixels) != width*height*3: raise ValueError('Unexpected PDF RGB-plane dimensions')
            rgb = np.frombuffer(pixels, dtype=np.uint8).reshape(height,width,3)
            a = np.frombuffer(alpha,dtype=np.uint8).reshape(height,width)
            error = 0.0
            for start in range(0,height,128):
                delta = np.abs(rgb[start:start+128].astype(np.int16)-np.array(color,dtype=np.int16))
                error=max(error,float((delta.astype(np.float32)*a[start:start+128,:,None]/255).max()))
            if error > 1.01:
                raise ValueError('PDF color differs from the declared source hue beyond alpha rounding')
            max_error=max(max_error,error)
            compressor=zlib.compressobj(9)
            row=bytes(color)*width
            encoded=b''.join(compressor.compress(row) for _ in range(height))+compressor.flush()
            obj.write(encoded,filter=pikepdf.Name.FlateDecode)
            if '/DecodeParms' in obj:del obj['/DecodeParms']
            normalized+=1
        # Repeated cyclic placements share identical images and masks. Compare
        # decoded pixels and all image semantics before redirecting references.
        def signature(obj):
            return (int(obj.Width),int(obj.Height),int(obj.BitsPerComponent),str(obj.ColorSpace),
                    bool(obj.get('/Interpolate',False)),str(obj.get('/Decode','')),
                    sha256(obj.read_bytes()).hexdigest(),
                    signature(obj.SMask) if '/SMask' in obj else None)
        for obj in images:
            if '/Mask' in obj:raise ValueError('Unexpected color-key mask in trial PDF')
            key=signature(obj)
            if key in canonical:aliases[obj.objgen]=canonical[key]
            else:canonical[key]=obj
        seen=set()
        def replace_refs(obj):
            if not isinstance(obj,(pikepdf.Dictionary,pikepdf.Stream,pikepdf.Array)):return
            ident=obj.objgen
            if ident!=(0,0):
                if ident in seen:return
                seen.add(ident)
            keys=range(len(obj)) if isinstance(obj,pikepdf.Array) else list(obj.keys())
            for key in keys:
                value=obj[key]
                if isinstance(value,(pikepdf.Dictionary,pikepdf.Stream,pikepdf.Array)):
                    if value.objgen in aliases:obj[key]=aliases[value.objgen];value=obj[key]
                    replace_refs(value)
        replace_refs(pdf.Root)
        pdf.save(temporary,compress_streams=True,recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate,deterministic_id=True)
    with pikepdf.open(temporary) as pdf:
        if pdf.check_pdf_syntax():raise ValueError('Optimized PDF syntax check failed')
        after_masks={(int(o.Width),int(o.Height),sha256(o.SMask.read_bytes()).hexdigest()) for o in pdf.objects
                     if isinstance(o,pikepdf.Stream) and o.get('/Subtype')==pikepdf.Name.Image and '/SMask' in o}
        if before_masks!=after_masks:raise ValueError('PDF opacity planes changed')
    temporary.replace(path)
    receipt={'input_sha256':original_hash,'output_sha256':digest(path),'input_bytes':original_size,
             'output_bytes':path.stat().st_size,'normalized_single_hue_images':normalized,
             'deduplicated_image_objects':len(aliases),'maximum_premultiplied_channel_change_255':max_error,
             'alpha_planes_unchanged':True,'image_dimensions_unchanged':True,
             'optimizer_sha256':digest(Path(__file__)),'pikepdf_version':pikepdf.__version__}
    write_json(receipt_path,receipt)
    print(f'Packaged {path.name}: {original_size/1e6:.1f} → {path.stat().st_size/1e6:.1f} MB',flush=True)
    return receipt


def package_delivery(config, products):
    """Package completed renders and refresh their receipts without rerendering."""
    from setouchi_h3_trials import write_review
    output=ROOT/config['output']
    records=[]
    for product in products:
        resolution,stem=product['h3_resolution'],product['stem']
        build=ROOT/config['build']/f'h3r{resolution}'/product['subject']
        settings=json.loads((build/'render-settings.json').read_text())
        for scope in ['world','japan']:
            receipt=build/(scope+'-plate.json')
            record=json.loads(receipt.read_text())
            if record['fingerprint'].get('export_contract')!='linked-png-checked-decoder-v1':
                raise ValueError('Render with the checked PNG decoder before packaging')
            svg=output/f'h3r{resolution}/maps/{scope}/{stem}.svg'
            pdf=svg.with_suffix('.pdf')
            opt_receipt=build/(scope+'-pdf-optimization.json')
            old=json.loads(opt_receipt.read_text()) if opt_receipt.exists() else None
            for item in record['files']:
                path=output/item['path']
                if digest(path)!=item['sha256'] and not (path==pdf and old
                        and old['input_sha256']==item['sha256'] and old['output_sha256']==digest(path)):
                    raise ValueError('Changed render artifact before packaging: '+str(path))
            result=optimize_pdf(pdf,svg,settings,opt_receipt)
            for item in record['files']:
                if output/item['path']==pdf:
                    item.update(sha256=digest(pdf),bytes=pdf.stat().st_size)
            record['pdf_packaging']=result
            write_json(receipt,record)
            write_json(output/f'sources/h3r{resolution}/{scope}-{stem}-pdf.json',result)
            records.append(record)
    write_json(output/'plates.json',{'schema':'cartofreako-setouchi-h3-trial-plates-v1',
        'config':config,'plates':records,'publication_status':'local-only'})
    write_review(config,records)
    for resolution in sorted({p['h3_resolution'] for p in products}):
        for scope in ['world','japan']:
            inputs=[]
            for stem in ['cloud-atmosphere','anthropocene-temperature-2026']:
                inputs.extend([output/f'h3r{resolution}/maps/{scope}/{stem}.pdf',
                               output/f'h3r{resolution}/legends/{scope}/{stem}-legend.pdf'])
            if all(p.exists() for p in inputs):
                subprocess.run(['pdfunite',*map(str,inputs),str(output/f'h3r{resolution}/{scope}.pdf')],check=True)
