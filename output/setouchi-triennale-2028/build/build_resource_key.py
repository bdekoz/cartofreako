#!/usr/bin/env python3
"""Render the resource key directly from the audited colour/class assignments."""
from pathlib import Path
from html import escape
import json
OUT=Path(__file__).resolve().parents[1]
data=json.loads((OUT/'sources/resource-color-assignments.json').read_text())
parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resource colour key / Setouchi 2028</title><style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#17212b}p{line-height:1.5}article{padding:20px 0;border-top:1px solid #ccd5dd}.ramp{display:flex;gap:12px}.bin{flex:1;min-width:0}.color{height:38px;margin-bottom:10px}small{display:block;margin:8px 0;overflow-wrap:anywhere}a{color:#155b91}@media(max-width:700px){.ramp{flex-wrap:wrap}.bin{flex:1 0 28%}}</style><a href="../index.html">Back to atlas</a><h1>Resource colour key</h1><p>Fourteen metrics use 70 distinct named colours from <code>svg::izzi_hue_palette</code>. All data fills are 100% opaque. No exact RGB is reused between metrics; petroleum comparison plates share the petroleum family. Grey means missing. Numeric ranges retain each metric's units and are not comparable across resources.</p><p><a href="resource-color-assignments.json">Inspect names, RGB values, thresholds and country counts</a></p>''']
for row in data['classifications']:
    parts.append('<article><h2>'+escape(row['title'])+'</h2><p>'+escape(row['unit']+' · '+row['scale'])+'</p><div class="ramp">')
    for item in row['bins']:
        color=item['color']
        parts.append('<div class="bin"><div class="color" style="background:'+color['hex']+'"></div><strong>'+escape(item['label'])+'</strong><small>'+escape(color['name']+' · '+color['hex'])+'</small>')
        if 'count' in item:parts.append('<small>'+str(item['count'])+' reported country records</small>')
        parts.append('</div>')
    parts.append('</div></article>')
parts.append('<p>Solar capacity is the installed rating at year end, not electricity generation, sunlight or a plant-location inventory. Next improvements: country-year additions, per-person capacity and measured generation; preserve the total-capacity view for comparisons of scale. 1,000 MW = 1 GW. Japan: 92,211 MW in the 2025 source.</p></html>')
(OUT/'sources/resource-color-key.html').write_text(''.join(parts))
print('Resource key: 14 metrics, 70 named colours')
