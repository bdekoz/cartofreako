#!/usr/bin/env python3
"""An inspectable colour key and vector coral comparison for the study volume."""
from build_aggregate import *
def main():
    dest=OUT/'proposal/visual-revisions-and-coral-prototypes.pdf'
    c=canvas.Canvas(str(dest),pagesize=A4);c.setTitle('Resource colour key and coral prototypes / Setouchi 2028')
    chrome(c,'Visual revisions')
    y=paragraph(c,'Visual revisions and source changes',MARGIN,779,style=TITLE)
    for title,body in [
        ('Temperature','New daily-high records use shared classes of 1–5, 6–10, 11–20, 21–40, 41–80 and 81+ days. Red is reserved for more than 40 days. The 2025 field is complete; 2026 ends 28 October. Their raw annual counts are not a like-for-like annual trend.'),
        ('Resource colours','Data fills are 100% opaque. Fourteen metrics use 70 distinct named izzi-hue colours. Solar uses yellow/orange, petroleum brown. Five value classes follow each other metric’s original linear or log(1 + value) scale. Grey means missing. Petroleum comparison plates share their family key.'),
        ('Solar meaning and future work','Installed solar capacity is the year-end generating rating in MW, not electricity produced or local sunlight. Japan’s 2025 source value is 92,211 MW. Future companions should compare annual additions, capacity per person and measured generation.'),
        ('Network sources','CDN uses cloud_cdn_cache.bkoz’s 21 October manifest and Alpha60 r8 honeycomb/reference encodings. Swarm uses the actual Alpha60 cumulative-cache renderer for Dan Da Dan 210/211/212, September 2025–March 2026. Separate 1080p/4K and 720p/SD plates use the atlas AuthaGraph projection.'),
        ('Japan and water detail','Japan geographic coastlines are 1 pt. Fiber landing diameters are halved and their outlines are 0.5 pt. Fiber routes remain 0.5 pt / 75%. Inland rivers are 0.75 pt globally and 1.5 pt in Japan, retaining 85% opacity.'),
        ('Particulate enrichment','Japan MOE and China CNEMC via Quotsoft now supply measured PM2.5; selected Indian CPCB/AirNow stations and one separately labeled AirGradient sensor add coverage. At least 18 valid hours define a daily mean. Teal marks observed days; orange marks >35 micrograms/m3 days. Dates differ; no national exposure estimate. Sources: docs/pages/data/anthropocene-particulate.md.')]:
        y=paragraph(c,title,MARGIN,y-10,style=HEADING)
        y=paragraph(c,body,MARGIN,y-5,style=BODY)
    assert y>45,y;c.showPage()
    rows=json.loads((OUT/'sources/resource-color-assignments.json').read_text())['classifications']
    for start in range(0,len(rows),4):
        chrome(c,'Resource colour key')
        paragraph(c,'Named izzi-hue resource colours',MARGIN,779,style=TITLE)
        paragraph(c,'Solid data fills. Numeric ranges retain the source metric’s units; colours are not comparable quantities across different metrics.',MARGIN,737,style=SMALL)
        for j,r in enumerate(rows[start:start+4]):
            y=680-j*151
            paragraph(c,r['title'],MARGIN,y,style=HEADING)
            paragraph(c,escape(r['unit']+' / '+r['scale']),MARGIN,y-27,style=SMALL)
            width=WIDTH/len(r['bins'])
            for i,b in enumerate(r['bins']):
                x=MARGIN+i*width;col=b['color'];c.setFillColor(colors.HexColor(col['hex']));c.rect(x,y-64,width-8,18,stroke=0,fill=1)
                tiny=ParagraphStyle('tiny',parent=SMALL,fontSize=7.5,leading=9)
                paragraph(c,escape(b['label']),x,y-70,width-9,tiny)
                paragraph(c,escape(col['name']+' / '+col['hex']),x,y-95,width-9,tiny)
                if 'count' in b:paragraph(c,str(b['count'])+' country records',x,y-116,width-9,tiny)
        c.showPage()
    descriptions={
        'honeycomb':'Selected for the atlas. Each local display group retains the threat-class mixture as microhexes. Up to 61 cells are drawn per group; capped groups preserve class proportions and every source membership in the ledger.',
        'voronoi':'One bounded cell per original source cell, clipped to a 0.075 inch display radius. This separates adjacent cells, but the enlarged footprint can suggest continuous reef coverage. The filled area is a display device.',
        'clusters':'Circle area scales with source-cell count until the 0.13 inch radius cap; sectors retain class shares. Compact at global scale, but tiny minority sectors can disappear in a reduced print.'}
    for variant in ['honeycomb','voronoi','clusters']:
        chrome(c,'Coral prototype / '+variant)
        paragraph(c,'Coral reef / '+variant.title(),MARGIN,779,style=TITLE)
        for scope,y in [('world',467),('japan',210)]:
            source=OUT/f'prototypes/coral-reef/{variant}-{scope}.pdf'
            # Normalize PDF dictionary comments for pdfrw; retain vector streams
            # and leave the approved prototype files untouched.
            normalized=io.BytesIO();writer=PdfWriter();writer.append(source,import_outline=False);writer.write(normalized)
            form=pagexobj(FormReader(fdata=normalized.getvalue()).pages[0]);scale=WIDTH/float(form.BBox[2]-form.BBox[0]);c.saveState();c.translate(MARGIN,y);c.scale(scale,scale);c.doForm(makerl(c,form));c.restoreState()
            c.setFillColor(MUTED);c.setFont('Atlas-Bold',8);c.drawString(MARGIN,y+WIDTH*19.052559/44+9,scope.upper())
        y=paragraph(c,descriptions[variant],MARGIN,185,style=BODY)
        paragraph(c,'All three retain WRI’s 2011 baseline: 7,215 occupied 0.25 degree cells, with the highest original threat retained per source cell. The 844 display groups do not measure reef area or present-day condition. Full SVG/PDF/PNG comparisons and memberships: prototypes/coral-reef/index.html.',MARGIN,y-12,style=SMALL)
        c.showPage()
    c.save();print('Visual annex:',len(PdfReader(dest).pages),'pages',flush=True)
if __name__=='__main__':main()
