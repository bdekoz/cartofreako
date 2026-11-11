"""Shared SLSL World maps and A3 legends for both atlas source workflows."""
import json
from pathlib import Path

from cartofreako_style import STYLE, Projection
from dataset import ROOT
import starlink_star_light as S

PLATES={stem:plate for plate,stem in S.STEMS.items()}


def settings():
    return json.loads((ROOT/STYLE['atlas']['presentation']['world_recipe_file']).read_text())


def compose(stem, source, work, recipe, *, orbital_profile=None,
            groundstation_profile=None, styled=False):
    """Style selected source bytes; retain their dates and object populations."""
    S.register_fonts()
    config=settings()
    plate=PLATES[stem]
    document=S.read_svg(source) if isinstance(source,(str,Path)) else source
    evidence={}
    profile={}
    if plate=='SLSL4':
        content,evidence=S.refine_groundstations(document,config,
            Projection('authagraph',work/'world-projection'),
            profile_path=groundstation_profile,recipe=recipe)
        timestamp='source snapshot '+evidence['source_date']
    elif plate=='SLSL1':
        content=S.source_group(document)
        timestamp=content.xpath('.//*[@id="astro-metadata"]')[0].get('data-timestamp')
    else:
        profile=json.loads(Path(orbital_profile or ROOT/config['orbital_profile']).read_text())
        content=S.source_group(document) if styled else S.orbital_source(document,plate,recipe)
        for marker in content.xpath('.//*[@data-role="debris" and @data-marker-shape="x"]'):
            S.paint(marker.attrib,stroke='#ffffff',stroke_opacity=1)
        timestamp=content.xpath('.//*[@id="orbital-technosphere-metadata"]')[0].get('data-timestamp')
    root,layout=S.make_map(plate,'world',content,None,config,[])
    legend=S.make_legend(plate,'world',content,config,profile,evidence,timestamp)
    for tree in (root,legend):
        tree.set('data-atlas-world-presentation','slsl-v3')
        tree.set('data-canonical-plate-id',stem)
        tree.set('data-calculation-or-source-date',timestamp)
        tree.set('data-sheet-background',S.FG if tree is legend else S.BG)
    return root,legend,layout
