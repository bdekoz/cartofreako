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
    """Use the approved A3 companion for both geographic scopes."""
    config = groundstation_settings(STYLE)
    root = S.make_legend('SLSL4', 'world', None, config, {}, evidence,
                         'source snapshot '+evidence['source_date'])
    root.set('data-groundstation-presentation', 'slsl-v3')
    root.set('data-canonical-plate-id', 'network-groundstations')
    root.set('id', 'groundstation-default-legend-'+scope)
    S.el('metadata', root, id='groundstation-legend-ledger').text = json.dumps(
        {k:v for k,v in evidence.items() if k not in ('records', 'placement')}, sort_keys=True)
    if scope == 'japan':
        # Geographic scope changes; source totals and marker populations do not.
        from atlas_legends import observer_note, wrap, text, WIDTH
        observer = observer_note('network-groundstations', scope)
        root.set('data-observer-notes', observer)
        for node in root.xpath('//*[local-name()="text"]'):
            if (node.text or '').startswith('World  |'):
                node.text = node.text.replace('World  |', 'Japan  |', 1)
            if (node.text or '').startswith('STARLINK STAR LIGHT /'):
                node.text = node.text.replace('/ WORLD /', '/ JAPAN /')
        group = root.xpath('//*[@id="observer-notes"]')[0]
        # Keep the original paragraph height; the new regional note is shorter.
        for node in list(group):
            group.remove(node)
        col = (WIDTH-1.3)/3
        for i, line in enumerate(wrap(observer, 12, col)):
            text(group, .65+col, 2.05+i*12/72*1.4, line, 12, role='observer')
    return root
