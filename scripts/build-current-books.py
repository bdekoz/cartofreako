#!/usr/bin/env python3
"""Assemble dataset-bound World, Japan and combined atlas PDF books."""
from html import escape
import json
from pathlib import Path
import subprocess

from dataset import ROOT, atomic_json, context, digest, output
from legend_informatics import register_fonts


def frontmatter(path, dataset, catalog, scope):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    width,height=44*72,19.052559*72
    doc=canvas.Canvas(str(path),pagesize=(width,height),invariant=1)
    doc.setTitle('Cartofreako / '+scope+' / '+dataset['dataset_id'])
    doc.setSubject('Dataset manifest SHA-256: '+dataset['manifest_sha256'])
    def page():
        doc.setFillColor(HexColor('#240413'));doc.rect(0,0,width,height,fill=1,stroke=0)
        doc.setFillColor(HexColor('#fcc553'))
    page();doc.setFont('Atkinson-Regular',58);doc.drawString(90,height-170,'CARTOFREAKO / '+scope.upper())
    doc.setFont('Atkinson-Regular',24);doc.drawString(90,height-235,'Dataset '+dataset['dataset_id'])
    doc.drawString(90,height-280,'Resolved '+dataset['resolved_at'])
    doc.drawString(90,height-325,'Source periods, coverage and hashes: sources/dataset.json')
    doc.setFont('Atkinson-Regular',18);y=height-410
    for source in dataset['sources']:
        doc.drawString(90,y,source['id']+' / '+source['acquisition']);y-=35
    doc.showPage();page();doc.setFont('Atkinson-Regular',38);doc.drawString(90,height-100,'CONTENTS / separate map and source sheets')
    doc.setFont('Atkinson-Regular',19)
    for i,plate in enumerate(catalog):
        doc.drawString(100,height-155-i*27,f'{i+1:02d}  '+plate['title'])
    doc.showPage();doc.save()


def contact_sheet(root, catalog, rows, scope):
    from PIL import Image, ImageDraw
    columns,cell_width,cell_height=4,800,390
    image=Image.new('RGB',(columns*cell_width,((len(catalog)+columns-1)//columns)*cell_height),'#240413')
    draw=ImageDraw.Draw(image)
    for i,plate in enumerate(catalog):
        path=root/rows[plate['id'],scope,'map']['outputs']['preview']['path']
        with Image.open(path) as original:
            thumbnail=original.convert('RGB');thumbnail.thumbnail((cell_width-20,cell_height-50))
        x,y=(i%columns)*cell_width,(i//columns)*cell_height
        image.paste(thumbnail,(x+(cell_width-thumbnail.width)//2,y))
        draw.text((x+10,y+cell_height-35),f'{i+1:02d} '+plate['title'],fill='#fcc553')
    destination=root/('contact-'+scope+'.png');image.save(destination)
    return {'scope':scope,'path':destination.name,'sha256':digest(destination)}


def main():
    path, dataset = context()
    root = output("atlas")
    validation = json.loads((root / "sources/current-validation.json").read_text())
    if validation["dataset_id"] != dataset["dataset_id"] or validation["status"] != "passed":
        raise ValueError("Atlas validation must pass before book assembly")
    catalog = [p for p in dataset['products']['plates'] if p['default']]
    exports = json.loads((root / "sources/sheet-export-manifest.json").read_text())["records"]
    rows = {(r["stem"], r["scope"], r["kind"]): r for r in exports}
    register_fonts()
    books = []
    for edition, scopes in (("world", ("world",)), ("japan", ("japan",)), ("combined", ("world", "japan"))):
        inputs = [root / rows[p["id"], scope, kind]["outputs"]["pdf"]["path"]
                  for p in catalog for scope in scopes for kind in ("map", "legend")]
        destination = root / ("atlas-" + edition + ".pdf")
        opening=root/'sources'/('frontmatter-'+edition+'.pdf')
        frontmatter(opening,dataset,catalog,edition)
        inputs.insert(0,opening)
        temporary = destination.with_suffix(".tmp.pdf")
        subprocess.run(["pdfunite", *map(str, inputs), str(temporary)], check=True)
        temporary.replace(destination)
        books.append({"scope": edition, "path": destination.name, "sha256": digest(destination),
                      "sheet_count": len(inputs)-1, "page_count":len(inputs)+1,
                      "inputs": [{"path": str(p.relative_to(root)), "sha256": digest(p)} for p in inputs]})
        info=subprocess.check_output(['pdfinfo',str(destination)],text=True)
        import re
        if int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1]) != len(inputs)+1:
            raise ValueError('Atlas book page count does not match the selected catalog')
    contacts=[contact_sheet(root,catalog,rows,scope) for scope in ('world','japan')]
    atomic_json(root / "sources/current-books.json", {"dataset_id": dataset["dataset_id"], "books": books,'contacts':contacts})
    html = ["<!doctype html><html lang=en><meta charset=utf-8><title>Current Cartofreako atlas</title>",
            "<h1>Cartofreako</h1><p>Dataset " + escape(dataset["dataset_id"]) + "</p>",
            '<p><a href="sources/dataset.json">Dataset sources, periods and hashes</a></p>']
    for book in books:
        html.append(f'<p><a href="{book["path"]}">{book["scope"].title()} book ({book["sheet_count"]} sheets)</a></p>')
    for contact in contacts:
        html.append(f'<p><a href="{contact["path"]}">{contact["scope"].title()} contact sheet</a></p>')
    for plate in catalog:
        html.append("<article><h2>" + escape(plate["title"]) + "</h2>")
        for scope in ("world", "japan"):
            for kind in ("map", "legend"):
                row = rows[plate["id"], scope, kind]
                html.append(f'<p>{scope.title()} {kind}: <a href="{row["svg"]}">SVG</a> · '
                            f'<a href="{row["outputs"]["pdf"]["path"]}">PDF</a> · '
                            f'<a href="{row["outputs"]["png"]["path"]}">PNG</a></p>')
        html.append("</article>")
    (root / "index.html").write_text("\n".join(html) + "</html>\n")


if __name__ == "__main__":
    main()
