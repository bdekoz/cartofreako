"""Label optional maps from their own measure, region and observation period."""
import textwrap

from atlas_review_sheets import el, text

STALE_GROUPS = ('detail-notes', 'legend-and-provenance')


def period_label(metadata):
    if metadata['period'] == 'matched':
        return 'Matched calendar window'
    if metadata['period'] == 'season':
        return 'Warm-peak year'
    return 'Full year' if metadata['data_through'] == f"{metadata['year']}-12-31" else 'Year to date'


def annotate_map(doc, scope, stem, title, metadata):
    """Keep geographic data/frame geometry; replace the borrowed annotations."""
    companion = f'../../../legends/{scope}/svg/{stem}-legend.svg'
    doc.set('data-display-scope', scope)
    doc.set('data-legend-companion', companion)
    doc.set('data-data-through', metadata['data_through'])
    titles = doc.xpath('./*[local-name()="title"]')
    heading = titles[0] if titles else el('title')
    if not titles:
        doc.insert(0, heading)
    heading.text = title
    for duplicate in titles[1:]:
        doc.remove(duplicate)
    for node in doc.xpath('//*[@id="source-cartography"]/*[local-name()="title"]'):
        node.text = title
    for identifier in STALE_GROUPS:
        for node in doc.xpath('//*[@id=$identifier]', identifier=identifier):
            if node.getparent() is not None:
                node.getparent().remove(node)
    if scope == 'world':
        return
    if scope not in ('japan', 'india'):
        raise ValueError('Unsupported optional map region: ' + scope)
    for node in doc.xpath('./*[local-name()="text"]'):
        doc.remove(node)
    text(doc, .7, .8, scope.upper() + ' / ' + title.upper(), .45,
         font_weight='bold', id='optional-map-heading')
    text(doc, .7, 1.35, f"{metadata['year']} / {period_label(metadata)} / through {metadata['data_through']}",
         .23, id='optional-map-source-period')
    notes = el('g', doc, id='optional-map-notes')
    text(notes, 30, 2.35, 'READ THIS PLATE', .28, font_weight='bold')
    paragraphs = [
        f'{scope.title()} and nearby countries in the parent projection. Geographic enlargement preserves the original observation supports.',
        'Read the companion legend for this measure, units, source dates and eligibility rules. Empty space is not an observed zero.',
        'This viewport is a geographic detail, not a regional total.'
    ]
    y = 2.9
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, 70):
            text(notes, 30, y, line, .23)
            y += .36
        y += .18
    link = el('a', notes, id='optional-map-legend-link')
    link.set('{http://www.w3.org/1999/xlink}href', companion)
    text(link, 30, y + .4, 'Open legend and sources', .26, text_decoration='underline')
    text(notes, .7, 18.35, f"AuthaGraph / {scope.title()} detail / {period_label(metadata)} / through {metadata['data_through']}", .2)


def check_map_annotations(doc, scope, stem, title, metadata):
    """Check captions against product metadata, not the template's old labels."""
    assert doc.get('data-display-scope') == scope, 'Optional map region'
    assert doc.get('data-data-through') == metadata['data_through'], 'Optional map cutoff'
    assert doc.xpath('./*[local-name()="title"]/text()') == [title], 'Optional map title'
    assert all(value == title for value in doc.xpath('//*[@id="source-cartography"]/*[local-name()="title"]/text()')), 'Optional source-cartography title'
    companion = f'../../../legends/{scope}/svg/{stem}-legend.svg'
    assert doc.get('data-legend-companion') == companion, 'Optional map companion'
    for identifier in STALE_GROUPS:
        assert not doc.xpath('//*[@id=$identifier]', identifier=identifier), 'Inherited template annotation: ' + identifier
    if scope != 'world':
        headings = doc.xpath('//*[@id="optional-map-heading"]')
        assert len(headings) == 1 and ''.join(headings[0].itertext()) == scope.upper() + ' / ' + title.upper(), 'Regional map heading'
        periods = doc.xpath('//*[@id="optional-map-source-period"]')
        expected = f"{metadata['year']} / {period_label(metadata)} / through {metadata['data_through']}"
        assert len(periods) == 1 and ''.join(periods[0].itertext()) == expected, 'Regional map period'
        links = doc.xpath('//*[@id="optional-map-legend-link"]')
        assert len(links) == 1 and links[0].get('{http://www.w3.org/1999/xlink}href') == companion, 'Regional legend link'
