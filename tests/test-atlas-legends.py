#!/usr/bin/env python3
"""Physical legend regressions and atomic date-based delivery publication."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import dataset
import atlas_legends as legends
import atlas_bibliography as bibliography


class Legends(unittest.TestCase):
    def render(self, sections=None):
        return legends.legend('test','Temperature','World / 2025',sections or [],
                              ['Daily means / degC; missing is not zero.'],['NOAA / retained 2025 source'])

    def test_a3_type_palette_and_required_sections(self):
        tree=self.render()
        legends.validate_legend(tree)
        self.assertEqual((tree.get('width'),tree.get('height')),('420mm','297mm'))
        for role,points in [('title',27),('heading',15),('body',11),('source',10.5)]:
            values=tree.xpath(f'//*[@data-type-role="{role}"]')
            self.assertTrue(values)
            self.assertTrue(all(abs(float(n.get('font-size'))*72-points)<1e-8 for n in values))

    def test_native_units_symbols_and_colors_survive_reflow(self):
        old=E.fromstring(b'<g xmlns="http://www.w3.org/2000/svg" transform="scale(15)"><text font-size=".12pt">Celsius / 2025</text><circle cx="1" cy="2" r=".1" fill="#1256ab"/><text font-size=".12pt">0 to &lt;5 degC</text></g>')
        keys,notes=legends.native_content(old)
        tree=self.render([{'title':'Source scale','keys':keys,'notes':notes}])
        legends.validate_legend(tree)
        self.assertIn('0 to <5 degC',''.join(tree.itertext()))
        self.assertEqual(tree.xpath('//*[local-name()="circle"]')[0].get('fill'),'#1256ab')
        self.assertEqual(len(tree.xpath('//*[@id="legend-symbol-0"]')),1)

    def test_dense_cdn_key_retains_all_25_labels_at_11_points(self):
        labels=[f'Provider {i:02d} / cloud infrastructure' for i in range(25)]
        tree=self.render([{'title':'Providers','keys':[('#345678',s) for s in labels]}])
        legends.validate_legend(tree)
        for label in labels:self.assertIn(label,''.join(tree.itertext()))

    def test_repeated_v3_source_refresh_replaces_previous_bibliography(self):
        tree=E.Element('{http://www.w3.org/2000/svg}svg')
        legends.update_a3_sources(tree,['Obsolete bibliography'])
        legends.update_a3_sources(tree,['Current bibliography'])
        self.assertEqual(len(tree.xpath('//*[@id="data-sources"]')),1)
        self.assertNotIn('Obsolete bibliography',''.join(tree.itertext()))
        self.assertIn('Current bibliography',''.join(tree.itertext()))

    def test_unknown_plate_cannot_fall_back_to_generic_manifest_bibliography(self):
        with patch.object(bibliography,'context',return_value=(None,{'dataset_id':'fixture','sources':[{'id':'natural-earth','coverage':{'edition':'5.1.1'}}]})):
            with self.assertRaisesRegex(ValueError,'Missing plate bibliography'):
                bibliography.bibliography({'id':'unknown','source_stem':'unknown'})

    def test_water_has_actual_basemap_release_and_depth_source(self):
        with patch.object(bibliography,'context',return_value=(None,{'dataset_id':'fixture','sources':[{'id':'natural-earth','coverage':{'edition':'5.1.1'}}]})):
            refs=bibliography.bibliography({'id':'water','source_stem':'water'})['references']
        self.assertIn('5.1.1',' '.join(refs))
        self.assertIn('bathymetry',' '.join(refs))
        self.assertIn('https://www.naturalearthdata.com/',' '.join(refs))

    def test_retained_models_drop_observer_note_and_reflow_reading_section(self):
        tree=legends.legend('astro-observer-hubble','Hubble','Japan',[],
                            ['Retained reading guidance'],['Retained source'],
                            observer='Obsolete observer paragraph')
        legends.validate_legend(tree)
        self.assertNotIn('Obsolete observer paragraph',E.tostring(tree,encoding='unicode'))
        self.assertFalse(tree.xpath('//*[@id="observer-note" or @data-type-role="observer"]'))
        self.assertIsNone(tree.get('data-observer-notes'))
        model=json.loads(tree.xpath('//*[@id="atlas-legend-model"]')[0].text)
        self.assertNotIn('observer',model)
        key=tree.xpath('//*[@id="legend"]/*[1]')[0]
        reading=tree.xpath('//*[@id="how-to-read"]/*[1]')[0]
        self.assertEqual(key.get('y'),reading.get('y'))

    def test_retained_slsl_refresh_removes_note_and_closes_gap_idempotently(self):
        tree=E.fromstring(b'<svg xmlns="http://www.w3.org/2000/svg" data-observer-notes="Old note"><text x="5.7" y="1.65">Observer notes</text><g id="observer-notes"><text>Old note</text></g><text x="5.7" y="4">How to read the plate</text><text x="5.7" y="4.4">Keep this guidance</text><text x=".45" y="2">Keep this key</text></svg>')
        legends.update_a3_sources(tree,['Retained source'])
        first=E.tostring(tree)
        legends.update_a3_sources(tree,['Retained source'])
        self.assertEqual(first,E.tostring(tree))
        self.assertNotIn('observer',first.decode().lower())
        reading=tree.xpath('//*[local-name()="text" and text()="How to read this plate"]')[0]
        self.assertAlmostEqual(float(reading.get('y')),1.65)
        guidance=tree.xpath('//*[local-name()="text" and text()="Keep this guidance"]')[0]
        self.assertAlmostEqual(float(guidance.get('y')),2.05)
        self.assertIn('Keep this key',''.join(tree.itertext()))

    def test_firms_bibliography_follows_ingestion_not_optional_profile_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            profile={'data':{'geojson':'observations.geojson','sha256':'fixture'},
                     'sources':[{'id':'nasa-firms','status':'configured-optional','url':'https://firms.modaps.eosdis.nasa.gov/api/area/'},
                                {'id':'noaa-ghcn-gsn','status':'included','available_through':'2026-08-04','url':'https://www.ncei.noaa.gov/'}]}
            (root/'anthropocene-particulate-2026-profile.json').write_text(json.dumps(profile))
            (root/'observations.geojson').write_text(json.dumps({'metadata':{'calendar_year':2026,'source_statistics':{
                'firms_rows':1000,'firms_detection_dates':['2026-11-08','2026-11-09']}},'features':[]}))
            with patch.object(bibliography,'binding',return_value=root),patch.object(bibliography,'context',return_value=(None,{
                    'dataset_id':'fixture','sources':[{'id':'natural-earth','coverage':{'edition':'5.1.1'}}]})):
                result=bibliography.bibliography({'id':'anthropocene-particulate-2026','source_stem':'anthropocene-particulate-2026'})
            refs=' '.join(result['references'])
            self.assertIn('NASA FIRMS',refs)
            self.assertIn('2026-11-09',refs)
            self.assertIn('ingested observations',refs)
            self.assertIn('2026 source observations',refs)
            self.assertNotIn('2026-08-04',refs)

    def test_validator_rejects_transformed_type_or_wrong_paper(self):
        tree=self.render();tree.set('width','44in')
        with self.assertRaisesRegex(ValueError,'A3'):legends.validate_legend(tree)
        tree=self.render();tree.xpath('//*[@id="legend-paper"]')[0].set('fill','#240413')
        with self.assertRaisesRegex(ValueError,'light'):legends.validate_legend(tree)

    def test_optional_refresh_keeps_distinct_metric_paths(self):
        from refresh_atlas_legends import render_optional_legend
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            rows=[]
            for metric in ('event_days','longest_duration'):
                prefix='marine-heatwave/annual/'+metric+'/'
                row={'stem':'marine-2025','scope':'world',
                     'svg':prefix+'legends/world/svg/marine-2025-legend.svg',
                     'pdf':prefix+'legends/world/pdf/marine-2025-legend.pdf',
                     'preview':prefix+'previews/world/marine-2025-legend.png'}
                def render(source,destination,*args,**kwargs):
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(source.read_bytes())
                with patch('refresh_atlas_legends.render_svg',side_effect=render):
                    render_optional_legend(root,row,self.render(),{})
                rows.append(row)
            self.assertNotEqual(rows[0]['svg'],rows[1]['svg'])
            self.assertEqual(len(list(root.rglob('*.svg'))),2)
            for row in rows:self.assertEqual(dataset.digest(root/row['pdf']),row['pdf_sha256'])

    def test_moved_atlas_source_requires_matching_retained_bytes(self):
        from refresh_atlas_legends import retained_source
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            path=base/'native/authagraph/svg/geometry.svg'
            path.parent.mkdir(parents=True)
            path.write_text('Retained geometry')
            old='/removed/build/native/authagraph/svg/geometry.svg'
            self.assertEqual(retained_source(old,dataset.digest(path),base),str(path))
            with self.assertRaisesRegex(dataset.DatasetError,'Retained atlas source changed'):
                retained_source(old,'wrong hash',base)

    def test_fiber_key_retains_light_route_ink_with_visible_dark_outline(self):
        builder=importlib.import_module('build-current-atlas')
        sections=builder.fiber_legend_sections({'text':legends.PAPER,'background':legends.INK})
        tree=self.render(sections)
        legends.validate_legend(tree)
        for i in (3,4,5):
            lines=tree.xpath(f'//*[@id="legend-symbol-{i}"]/*')
            self.assertEqual([line.get('stroke') for line in lines],[legends.INK,legends.PAPER])
            self.assertGreater(float(lines[0].get('stroke-width')),float(lines[1].get('stroke-width')))
        notes=builder.fiber_reading_notes(['Kelly green = ITU land fibre | black = submarine cables | 0.5 pt / 75%',
                                         'ITU: solid operational; dash construction; dots planned/proposed. Black: dash planned; dots 2022-only.'])
        self.assertNotIn('black',' '.join(notes).lower())
        self.assertIn('light dyad ink = submarine cables',notes[0])
        self.assertIn('Submarine: dash planned; dots 2022-only.',notes[1])


class Delivery(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.manifest={'dataset_id':'fixture','requested_as_of':'2026-11-11T04:36:05Z'}
        for patcher in (patch.object(dataset,'ROOT',self.root),patch.object(dataset,'data_root',return_value=self.root/'.data')):
            patcher.start();self.addCleanup(patcher.stop)

    def complete(self,ident):
        root=dataset.run_output(self.manifest,ident)
        dataset.atomic_json(root/'validation/full-build.json',{'status':'passed','dataset_id':'fixture','build_id':ident})
        (root/'atlas').mkdir();(root/'atlas/book.pdf').write_text(ident)
        return root

    def test_publication_uses_dataset_date_and_preserves_previous_run(self):
        old=self.complete('old');new=self.complete('new')
        path=dataset.publish_output(old,self.manifest,'old')
        self.assertEqual(path,self.root/'output/data-edition/20261111')
        dataset.publish_output(new,self.manifest,'new')
        self.assertEqual((path/'atlas/book.pdf').read_text(),'new')
        self.assertEqual((old/'atlas/book.pdf').read_text(),'old')
        pointer=json.loads((self.root/'.data/build-current.json').read_text())
        self.assertEqual(pointer['output'],str(path))
        self.assertEqual(pointer['sha256'],dataset.digest(new/'validation/full-build.json'))

    def test_failed_build_cannot_replace_visible_delivery(self):
        old=self.complete('old');bad=self.complete('bad')
        path=dataset.publish_output(old,self.manifest,'old')
        dataset.atomic_json(bad/'validation/full-build.json',{'status':'failed','dataset_id':'fixture','build_id':'bad'})
        with self.assertRaises(dataset.DatasetError):dataset.publish_output(bad,self.manifest,'bad')
        self.assertEqual(path.resolve(),old)

    def test_existing_user_directory_is_not_displaced(self):
        public=dataset.delivery_output(self.manifest);public.mkdir(parents=True)
        with self.assertRaisesRegex(dataset.DatasetError,'existing directory'):
            dataset.publish_output(self.complete('new'),self.manifest,'new')

    def test_legacy_resume_path_is_retained_and_output_escape_rejected(self):
        old=self.root/'output/data-editions/fixture/builds/old';old.mkdir(parents=True)
        self.assertEqual(dataset.run_output(self.manifest,'old',existing=True),old)
        with patch.object(dataset,'context',return_value=(None,self.manifest)),patch.dict(os.environ,{'DATASET_OUTPUT_ROOT':'/tmp/escape'}):
            with self.assertRaises(dataset.DatasetError):dataset.output('atlas')


if __name__=='__main__':unittest.main()
