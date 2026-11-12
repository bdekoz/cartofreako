#!/usr/bin/env python3
"""Prevent borrowed regional headers and land-temperature legends on ocean maps."""
import importlib
from pathlib import Path
import sys
import tempfile
import unittest

from lxml import etree as E

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from optional_map_annotations import annotate_map,check_map_annotations,period_label

STEM='anthropocene-water-temperature-2025'
TITLE='Sea-surface temperature and coral heat stress / 2025'
META={'year':2025,'period':'annual','data_through':'2025-12-31'}


def template():
    return E.fromstring(b'''<svg xmlns="http://www.w3.org/2000/svg" width="44in" height="19.052559in">
      <title>Japan / land temperature 2026</title><text>JAPAN / LAND TEMPERATURE 2026</text>
      <g id="data"><path id="coast" d="M 1 2 L 3 4"/><g id="cpc-temperature-coverage"/>
        <g id="cpc-temperature-record-high-days"/><g id="cpc-temperature-record-low-days"/></g>
      <g id="detail-notes"><text>Japan-only total / source: land-temperature-2026.svg</text>
        <g id="legend-and-provenance"><text>NEW DAILY HIGH RECORDS / 2026</text></g></g></svg>''')


class Annotations(unittest.TestCase):
    def test_japan_uses_own_measure_year_and_legend(self):
        doc=template();geometry=E.tostring(doc.xpath('//*[@id="data"]')[0])
        with self.assertRaises(AssertionError):check_map_annotations(doc,'japan',STEM,TITLE,META)
        annotate_map(doc,'japan',STEM,TITLE,META)
        check_map_annotations(doc,'japan',STEM,TITLE,META)
        self.assertEqual(E.tostring(doc.xpath('//*[@id="data"]')[0]),geometry)
        visible=' '.join(doc.xpath('//*[local-name()="text"]/text()'))
        self.assertIn('JAPAN / SEA-SURFACE TEMPERATURE AND CORAL HEAT STRESS / 2025',visible)
        self.assertNotIn('2026',visible);self.assertNotIn('DAILY HIGH RECORDS',visible)

    def test_india_does_not_inherit_japan_annotations(self):
        doc=template();annotate_map(doc,'india',STEM,TITLE,META)
        check_map_annotations(doc,'india',STEM,TITLE,META)
        visible=' '.join(doc.xpath('//*[local-name()="text"]/text()'))
        self.assertIn('INDIA /',visible);self.assertNotIn('Japan',visible);self.assertNotIn('JAPAN',visible)
        self.assertEqual(doc.get('data-legend-companion'),'../../../legends/india/svg/'+STEM+'-legend.svg')

    def test_world_preserves_layout_and_removes_borrowed_legend(self):
        doc=template()
        for n in doc.xpath('./*[local-name()="text"]'):doc.remove(n)
        geometry=E.tostring(doc.xpath('//*[@id="data"]')[0])
        annotate_map(doc,'world',STEM,TITLE,META);check_map_annotations(doc,'world',STEM,TITLE,META)
        self.assertFalse(doc.xpath('//*[@id="optional-map-heading"]'))
        self.assertEqual(E.tostring(doc.xpath('//*[@id="data"]')[0]),geometry)

    def test_world_without_root_title_gets_accessible_product_title(self):
        doc=template()
        for node in doc.xpath('./*[local-name()="title" or local-name()="text"]'):
            doc.remove(node)
        geometry=E.tostring(doc.xpath('//*[@id="data"]')[0])
        annotate_map(doc,'world',STEM,TITLE,META)
        check_map_annotations(doc,'world',STEM,TITLE,META)
        self.assertEqual(E.QName(doc[0]).localname,'title')
        self.assertEqual(doc[0].text,TITLE)
        self.assertEqual(E.tostring(doc.xpath('//*[@id="data"]')[0]),geometry)

    def test_duplicate_template_titles_are_normalized(self):
        doc=template()
        E.SubElement(doc,'{http://www.w3.org/2000/svg}title').text='Stale second title'
        annotate_map(doc,'world',STEM,TITLE,META)
        annotate_map(doc,'world',STEM,TITLE,META)
        check_map_annotations(doc,'world',STEM,TITLE,META)
        self.assertEqual(doc.xpath('./*[local-name()="title"]/text()'),[TITLE])

    def test_world_source_title_changes_but_basemap_title_remains(self):
        doc=template()
        source=E.SubElement(doc,'g',id='source-cartography')
        E.SubElement(source,'{http://www.w3.org/2000/svg}title').text='Land temperature'
        basemap=E.SubElement(source,'g',id='terrestrial-land')
        E.SubElement(basemap,'{http://www.w3.org/2000/svg}title').text='Natural Earth land'
        annotate_map(doc,'world',STEM,TITLE,META)
        check_map_annotations(doc,'world',STEM,TITLE,META)
        self.assertEqual(source[0].text,TITLE)
        self.assertEqual(basemap[0].text,'Natural Earth land')

    def test_full_matched_ytd_and_season_periods(self):
        cases=[(META,'Full year'),({**META,'period':'matched','data_through':'2025-11-09'},'Matched calendar window'),
               ({'year':2026,'period':'annual','data_through':'2026-11-09'},'Year to date'),
               ({'year':2026,'period':'season','data_through':'2026-11-09'},'Warm-peak year')]
        for metadata,label in cases:
            with self.subTest(metadata=metadata):
                self.assertEqual(period_label(metadata),label)
                doc=template();annotate_map(doc,'japan',STEM,TITLE,metadata)
                period=doc.xpath('//*[@id="optional-map-source-period"]/text()')[0]
                self.assertEqual(period,f"{metadata['year']} / {label} / through {metadata['data_through']}")

    def test_validation_rejects_stale_heading_cutoff_and_companion(self):
        for field in ('heading','cutoff','companion','old-legend'):
            with self.subTest(field=field),self.assertRaises(AssertionError):
                doc=template();annotate_map(doc,'india',STEM,TITLE,META)
                if field=='heading':doc.xpath('//*[@id="optional-map-heading"]')[0].text='JAPAN / LAND TEMPERATURE 2026'
                elif field=='cutoff':doc.set('data-data-through','2026-11-09')
                elif field=='companion':doc.set('data-legend-companion','wrong.svg')
                else:E.SubElement(doc,'g',id='legend-and-provenance')
                check_map_annotations(doc,'india',STEM,TITLE,META)

    def test_shared_frame_accepts_india_display_region(self):
        maps=importlib.import_module('build-ocean-temperature-plates')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'atlas/maps/japan/svg'/(maps.TEMPLATE+'.svg')
            source.parent.mkdir(parents=True);source.write_bytes(E.tostring(template()))
            doc=maps.frame(root/'atlas','japan',STEM,TITLE,root/'tiles',
                           {'layers':[{'id':'sst','tiles':[{'scope':'japan','file':'india.png'}]}]},
                           {'views':[{'id':'japan','bounds':[1,2,3,4]}]},root/'delivery',META,
                           display_scope='india')
            check_map_annotations(doc,'india',STEM,TITLE,META)
            self.assertEqual(doc.get('data-canonical-plate-id'),STEM)
            self.assertTrue(doc.xpath('//*[@id="sst"]/*[local-name()="image"]'))
            self.assertFalse(doc.xpath('//*[@id="cpc-temperature-coverage"]'))


if __name__=='__main__':unittest.main()
