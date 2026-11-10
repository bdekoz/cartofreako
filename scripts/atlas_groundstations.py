"""Use the accepted SLSL groundstation display in both default atlas builders.

Current editions pass their bound source profile; retained editions use the
pinned profile. Neither path needs the generated SLSL delivery to exist.
"""
import json

from atlas_presentation import groundstation_settings
from cartofreako_style import STYLE, Projection
from dataset import atomic_json
import starlink_star_light as S


def prepare(source, work, recipe, *, profile_path=None):
    config = groundstation_settings(STYLE)
    work.mkdir(parents=True, exist_ok=True)
    content, evidence = S.refine_groundstations(S.read_svg(source), config,
        Projection('authagraph', work/'groundstation-projection'), profile_path=profile_path, recipe=recipe)
    root = S.el('svg', width='44in', height=f'{S.HEIGHT}in', viewBox=f'0 0 44 {S.HEIGHT}',
                data_groundstation_presentation='slsl-v3')
    S.el('rect', root, width=S.WIDTH, height=S.HEIGHT, fill=recipe['background'])
    # The world framer reads native layers at the top level.
    root.extend(list(content))
    path = work/'network-groundstations-slsl-v3.svg'
    S.save(root, path)
    atomic_json(work/'groundstation-capability-evidence.json', evidence)
    return path, evidence


def replace_source(root, native):
    """Keep the accepted world/Japan viewport and replace its cartography."""
    banks = root.xpath('//*[@id="source-cartography" or @id="source-content"]')
    if len(banks) != 1:
        raise ValueError('Expected one groundstation source bank')
    old = banks[0]
    content = S.source_group(S.read_svg(native))
    content.set('id', old.get('id'))
    old.getparent().replace(old, content)
    S.remove(root, '//*[@id="antarctica-consolidated-inset"]')
    root.set('data-groundstation-presentation', 'slsl-v3')
    return root


def legend(scope, evidence, recipe):
    """Wide atlas companion with source-derived counts and the revised keys."""
    summary, config = evidence['summary'], evidence['configuration']
    foreground, background = recipe['text'], recipe['background']
    root = S.el('svg', width='44in', height=f'{S.HEIGHT}in', viewBox=f'0 0 44 {S.HEIGHT}',
                data_sheet_kind='legend', data_groundstation_presentation='slsl-v3')
    root.set('id', 'groundstation-default-legend-'+scope)
    S.el('rect', root, id='legend-paper', width=S.WIDTH, height=S.HEIGHT, fill=background)
    S.el('metadata', root, id='groundstation-legend-ledger').text = json.dumps(
        {k:v for k,v in evidence.items() if k not in ('records', 'placement')}, sort_keys=True)
    def tx(x, y, value, points=20, **attrs):
        return S.tx(root, x, y, value, points, foreground, **attrs)
    tx(.8, 1.0, 'Network groundstations / '+scope.title(), 36, font_weight='700')
    tx(.8, 1.65, f"Source snapshot {evidence['source_date']} / "
       f"{summary['kinds']['antenna-site']} antenna records / {summary['kinds']['pop']} PoPs / {summary['kinds']['link']} links", 23)
    tx(.8, 2.7, 'Capability silhouettes', 25, font_weight='700')
    for i, (capability, shape) in enumerate(evidence['markers'].items()):
        y = 3.5+i*.7
        record = {'capability':capability, 'status':'reported-operational', 'aperture_proxy_m2':50}
        S.marker(root, record, shape, 1.2, y-.08, .28, 'key-'+capability,
                 foreground=foreground, background=background)
        tx(1.85, y, S.CAPABILITIES[capability][0]+f" / {summary['capabilities'].get(capability, 0)}")
    for i, (status, label) in enumerate((('reported-operational', 'Solid / reported operational'),
                                      ('unconfirmed', 'Dashed / planned or unconfirmed'),
                                      ('retired', 'Dotted / source reports retirement'))):
        y = 10.3+i*.7
        S.marker(root, {'capability':'ka', 'status':status, 'aperture_proxy_m2':50}, 'circle',
                 1.2, y-.08, .28, 'status-'+status, foreground=foreground, background=background)
        tx(1.85, y, label)
    S.marker(root, {'capability':'unknown', 'status':'unconfirmed', 'aperture_proxy_m2':None},
             'octagon', 1.2, 12.32, .28, 'unknown-size', foreground=foreground, background=background)
    tx(1.85, 12.4, 'Central hollow square / size unknown')
    S.el('circle', root, cx=1.2, cy=13.02, r=.13, fill='none', stroke=foreground, stroke_width=.009)
    tx(1.85, 13.1, 'Open circle / PoP, fixed size')
    tx(.8, 14.2, 'Aperture proxy / actual World-sheet sizes', 21, font_weight='700')
    for i, area in enumerate((13.577335130284366, 50, 100, 200)):
        x = 1.6+i*3.0
        record = {'kind':'antenna-site', 'capability':'ka', 'status':'reported-operational', 'aperture_proxy_m2':area}
        radius = S.CAP.radius(record, config)*S.FRAMING.SCALE
        S.marker(root, record, 'circle', x, 15.1, radius, 'size-'+str(i), foreground=foreground, background=background)
        tx(x, 15.85, f'{area:.1f} m²' if i==0 else f'{area:g} m²', 18, text_anchor='middle')
    notes = [
        'The listed aperture proxy is the largest complete antenna bank, max(N × pi × D² / 4). Bands are never added together. This describes listed hardware, not throughput or installed capacity.',
        f"The radius spread is {config['size']['radius_spread_multiplier']:g}× the previous display, about the unchanged {config['size']['minimum_radius_inches']:g}-inch floor. Equal-radius silhouettes enclose equal area. Final area is not directly proportional to aperture.",
        f"{summary['sized_sites']} antenna records have a size proxy; {summary['unknown_size_sites']} do not. Unknown sizes retain {config['size']['unknown_radius_inches']:g}-inch radii; PoPs remain 0.032 inch. {summary['incomplete_inventories']} inventories are incomplete.",
        'Source flags distinguish reported operational, unconfirmed/planned and retired records. These flags are not independent verification. A record is not necessarily a unique operating installation.',
        'Hexagonal grouping is recomputed for the expanded marks. Thin tethers lead to original source positions. Links retain supplied geometry; they include backbone and community satellite links and are not all fibre.',
        'Filled continental land and the consolidated Antarctic inset are absent.'
    ]
    tx(15.1, 2.7, 'How to read the plate', 25, font_weight='700')
    y = 3.5
    for note in notes:
        y = S.paragraph(root, 15.1, y, note, 13.0, 19, foreground)+.25
    tx(29.4, 2.7, 'Observer notes and sources', 25, font_weight='700')
    observer = ('A projected world network viewed from outside Earth. Marks describe terrestrial infrastructure; '
                'they do not show the sky from an observer location.' if scope=='world' else
                'A geographic enlargement around Japan of the same dated world network. The crop does not '
                'relocate source sites or claim a Japan-only total; legend counts describe the full source.')
    sources = [observer, 'Unofficial Starlink Global Gateways & PoPs / supplied KML converted to GeoJSON. Source order, repeated records, raw fields and incomplete inventories remain in the capability evidence receipt.',
               'Snapshot: '+evidence['source_date']+'. No license is specified by the supplied KML.',
               'Source: '+evidence['source'], 'SHA-256: '+evidence['source_sha256'],
               'Capability diameter assumptions and primary references are retained in '+config['source_profile']+' and the capability configuration.',
               *[reference['url'] for reference in config['references']]]
    y = 3.5
    for note in sources:
        y = S.paragraph(root, 29.4, y, note, 13.0, 18, foreground)+.2
    if y>S.HEIGHT-.8:
        raise ValueError('Groundstation atlas legend exceeds sheet')
    return root
