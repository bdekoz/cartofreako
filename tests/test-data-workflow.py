#!/usr/bin/env python3
"""Exercise complete transactions, frozen build routing and scientific lags."""
from datetime import date
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import dataset
from data_sources import Sources, local_input_paths
update = importlib.import_module('data-update')
build = importlib.import_module('dataset-context')
fixtures = importlib.import_module('test-dataset')


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = json.loads((ROOT/'config/data-products.json').read_text())

    def adapters(self, *, fail=None, calls=None):
        def callback(ident):
            def run(source):
                if calls is not None:
                    calls.append(ident)
                if ident == fail:
                    raise dataset.DatasetError('fixture outage')
                target = source.directory(ident)
                (target/'input.json').write_text(json.dumps({'source':ident}))
                source.record(ident, target, {'observed_through':'2026-11-05'}, 'pinned-local')
                for group in self.registry['groups'].values():
                    for name in group['bindings']:
                        source.bind(name, target/'input.json')
            return run
        return {ident:callback(ident) for ident in update.ORDER}

    def execute(self, **kwargs):
        return update.update(self.root, requested_as_of='2026-11-08T00:00:00Z',
                             validate_sources=lambda:None, **kwargs)

    def test_complete_update_activates_without_modifying_previous_edition(self):
        old, _ = fixtures.fixture(self.root/'editions/old', 'old')
        dataset.activate(self.root, old)
        before = old.read_bytes()
        path = self.execute(adapters=self.adapters())
        self.assertEqual(dataset.load(self.root/'current.json')[0],path)
        self.assertEqual(old.read_bytes(),before)
        self.assertEqual(len(dataset.load(path)[1]['sources']),len(update.ORDER))
        self.assertEqual(path.stat().st_mode & 0o222,0)

    def test_failure_retains_pointer_and_resume_skips_verified_completed_sources(self):
        old, _ = fixtures.fixture(self.root/'editions/old','old')
        dataset.activate(self.root,old)
        before=(self.root/'current.json').read_bytes()
        with self.assertRaisesRegex(dataset.DatasetError,'outage'):
            self.execute(adapters=self.adapters(fail='resources'))
        self.assertEqual((self.root/'current.json').read_bytes(),before)
        state_path=next((self.root/'runs').glob('*/state.json'))
        state=json.loads(state_path.read_text());self.assertEqual(state['status'],'failed')
        calls=[]
        path=self.execute(resume=state['dataset_id'],adapters=self.adapters(calls=calls))
        self.assertEqual(calls,list(update.ORDER)[4:])
        self.assertEqual(dataset.load(self.root/'current.json')[0],path)

    def test_resume_rejects_modified_completed_bytes(self):
        with self.assertRaises(dataset.DatasetError):
            self.execute(adapters=self.adapters(fail='resources'))
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        first=self.root/'editions'/state['dataset_id']/state['completed_files']['natural-earth'][0]['path']
        first.write_text('corrupt')
        with self.assertRaisesRegex(dataset.DatasetError,'Resume source bytes changed'):
            self.execute(resume=state['dataset_id'],adapters=self.adapters())
        self.assertFalse((self.root/'current.json').exists())

    def test_candidate_only_never_changes_current(self):
        path=self.execute(adapters=self.adapters(),candidate_only=True)
        self.assertTrue(path.is_file());self.assertFalse((self.root/'current.json').exists())

    def test_build_bindings_are_frozen_and_recursive_make_receives_them(self):
        first,manifest=fixtures.fixture(self.root/'editions/first','first')
        dataset.activate(self.root,first)
        resolved,loaded=dataset.load(self.root/'current.json')
        second,_=fixtures.fixture(self.root/'editions/second','second');dataset.activate(self.root,second)
        with patch.dict(os.environ,{'MAKEFLAGS':''}):
            command,env=build.build_command(resolved,loaded,['make','all-resilient'])
        self.assertEqual(env['DATASET_MANIFEST'],str(first))
        self.assertIn('DATASET_MANIFEST='+str(first),command)
        self.assertIn('/first/native',env['GENERATED_DIR'])
        self.assertEqual(env['SOURCE_DATE_EPOCH'],'1794096000')

    def test_profile_override_in_inherited_makeflags_is_rejected(self):
        path,manifest=fixtures.fixture(self.root/'editions/first','first')
        with patch.dict(os.environ,{'MAKEFLAGS':' -- ORBITING_PROFILE=unrelated.json'}):
            with self.assertRaisesRegex(dataset.DatasetError,'Conflicting dataset/profile override'):
                build.build_command(path,manifest,['make','atlas'])

    def test_build_child_failure_is_propagated(self):
        path,_=fixtures.fixture(self.root/'editions/one','one')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/dataset-context.py'),'--manifest',str(path),'--',
                               sys.executable,'-c','raise SystemExit(19)'],capture_output=True,text=True)
        self.assertEqual(result.returncode,19,result.stderr)

    def test_current_ocean_cutoff_uses_selected_config(self):
        import viz_context
        cfg=self.root/'climate.json';cfg.write_text(json.dumps({'ocean_cutoff':'2026-06-04','snapshot_as_of':'2026-06-07'}))
        with patch.dict(os.environ,{'CLIMATE_CONFIG':str(cfg)},clear=False):
            with patch.object(viz_context,'context',return_value=None):
                self.assertEqual(viz_context.cutoff(),date(2026,6,4))
                self.assertEqual(viz_context.matched_cutoff(),date(2025,6,4))
                self.assertEqual(viz_context.matched_days(),155)
                self.assertEqual(list(viz_context.product_months()),[1,2,3,4,5,6])

    def test_source_submakes_cannot_inherit_parent_path_overrides(self):
        with patch.dict(os.environ,{'MAKEFLAGS':' -- ASTRO_DATA_DIR=wrong','MAKEOVERRIDES':'ASTRO_DATA_DIR=wrong'}):
            source=Sources(self.root,'2026-11-08T00:00:00Z',self.root/'cache')
        self.assertNotIn('MAKEFLAGS',source.env)
        self.assertNotIn('MAKEOVERRIDES',source.env)

    @unittest.skipUnless((ROOT/'build/generation-context').is_file(), 'Build the native projection helper for composition integration')
    def test_fresh_composition_and_optional_viewport_use_new_layer_values(self):
        from lxml import etree as E
        from setouchi_h3_trials import settings_for
        compositor=importlib.import_module('build-current-atlas')
        native=self.root/'native';atlas=self.root/'atlas'
        folder=native/'authagraph/svg';folder.mkdir(parents=True)
        suffix='-authagraph-44-19.052559.svg'
        source=folder/('anthropocene-land-temperature-2026'+suffix)
        path,manifest=fixtures.fixture(self.root/'edition','fresh')
        plate={'id':'anthropocene-land-temperature-2026','source_stem':'anthropocene-temperature-2026','title':'Land temperature','default':True}
        def write(value):
            source.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="44in" height="19.052559in" viewBox="0 0 44 19.052559">
<g id="land"><path d="M 40.4 14 L 40.6 14 L 40.5 14.2 Z M 20 5 L 21 5 L 21 6 Z" fill="white"/></g>
<g id="cpc-temperature-coverage"><path id="cpc-covered-cells" d="M 20 5 L 21 5 L 21 6 Z" style="fill:rgb(100,100,100);fill-opacity:1;stroke:rgb(100,100,100);stroke-opacity:0;stroke-width:0"/></g>
<g id="cpc-temperature-record-high-days"><path data-bin="1" data-current-value="{value}" d="M 20 5 L 21 5 L 21 6 Z" style="fill:rgb(250,100,50);fill-opacity:1;stroke:rgb(250,100,50);stroke-opacity:0;stroke-width:0"/></g>
</svg>''')
        with patch.object(compositor,'context',return_value=(path,manifest)), patch.object(compositor,'output',side_effect=lambda name:{'atlas':atlas,'native':native}[name]):
            write(12);first=compositor.build([plate]);before=(atlas/'maps/world/svg'/f"{plate['id']}.svg").read_bytes()
            settings=settings_for(atlas,plate['id'],30)
            self.assertEqual([v['id'] for v in settings['views']],['world','japan'])
            self.assertGreater(settings['views'][1]['pixels_per_unit'],30)
            write(19);second=compositor.build([plate]);after=(atlas/'maps/world/svg'/f"{plate['id']}.svg").read_bytes()
        self.assertNotEqual(before,after)
        self.assertNotEqual(first[0]['source_sha256'],second[0]['source_sha256'])
        self.assertIn(b'data-current-value="19"',after)
        tree=E.fromstring(after)
        self.assertEqual(tree.get('data-dataset-id'),'fresh')
        self.assertEqual(len(second),4)
        for record in second:
            self.assertEqual(dataset.digest(atlas/record['svg']),record['svg_sha256'])

    def test_partial_group_validation_cannot_become_a_full_build(self):
        aggregate=importlib.import_module('atlas-optional')
        path=self.root/'atlas/sources/current-validation.json'
        dataset.atomic_json(path,{'status':'passed'})
        path=self.root/'anthropocene-optional/ocean/validation.json'
        dataset.atomic_json(path,{'status':'passed','data_only':True})
        with self.assertRaisesRegex(dataset.DatasetError,'full output validation'):
            aggregate.completed_groups(self.root,{})

    def test_failed_build_keeps_completed_pointer_and_artifacts(self):
        aggregate=importlib.import_module('atlas-optional')
        path,manifest=fixtures.fixture(self.root/'edition','fixture')
        pointer=self.root/'data/build-current.json'
        dataset.atomic_json(pointer,{'dataset_id':'older','receipt':'previous-validated-build'})
        before=pointer.read_bytes()
        artifact=self.root/'previous.pdf';artifact.write_bytes(b'previous completed artifact')
        def stage(command):
            if 'all-resilient' in command:
                raise subprocess.CalledProcessError(2,command)
        with patch.object(aggregate,'ROOT',self.root), patch.object(aggregate,'context',return_value=(path,manifest)), \
             patch.object(aggregate,'data_root',return_value=self.root/'data'), patch.object(aggregate,'run',side_effect=stage), \
             patch.object(aggregate,'implementation_record',return_value={'fixture':'methods'}), \
             patch.object(sys,'argv',['atlas-optional.py']), patch.dict(os.environ,{},clear=False):
            self.assertEqual(aggregate.main(),1)
        self.assertEqual(pointer.read_bytes(),before)
        self.assertEqual(artifact.read_bytes(),b'previous completed artifact')
        state=json.loads(next((self.root/'output').rglob('build-state.json')).read_text())
        self.assertEqual(state['status'],'failed')

    def test_document_self_fragment_resolves_in_repository(self):
        checker=importlib.import_module('check-doc-links')
        source=self.root/'guide.md';source.write_text('# Dataset workflow\n\n[Jump](#dataset-workflow)\n')
        target,fragment=checker.local_target(self.root,Path('guide.md'),'#dataset-workflow')
        self.assertEqual(target,source)
        self.assertIn(fragment,checker.document_anchors(target))

    def test_immutable_input_products_become_independently_writable_outputs(self):
        aggregate=importlib.import_module('atlas-optional')
        source=self.root/'input.json';source.write_text('source observations');source.chmod(0o444)
        destination=self.root/'output.json'
        aggregate.writable_product_copy(source,destination)
        destination.write_text('new build validation')
        self.assertEqual(source.read_text(),'source observations')
        aggregate.writable_product_copy(source,destination)
        self.assertEqual(destination.read_text(),'source observations')

    @unittest.skipUnless((ROOT/'build/generation-context').is_file(), 'Native projection helper required')
    def test_japan_sky_has_fresh_observer_view_and_geographic_locator(self):
        from lxml import etree as E
        compositor=importlib.import_module('build-current-atlas')
        source=self.root/'sky.svg';earth=self.root/'earth.svg';target=self.root/'japan.svg'
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg"><g id="labels"><text x="2" y="3">Fresh sky</text></g><circle cx="3" cy="4" r=".1" data-current-object="current"/></svg>')
        earth.write_text('<svg xmlns="http://www.w3.org/2000/svg"><g id="land"><path d="M 1 1 L 2 1 L 2 2 Z"/></g></svg>')
        compositor.japan_sky(source,target,earth)
        _,recipe=compositor.settings(compositor.STYLE)
        compositor.celestial_presentation(target,{'id':'astro-observer-ground-multiband'},recipe)
        tree=E.parse(str(target))
        self.assertEqual(len(tree.xpath('//*[@data-current-object="current"]')),1)
        self.assertEqual(len(tree.xpath('//*[@id="japan-earth-context"]')),1)
        self.assertEqual(len(tree.xpath('//*[@data-reference]')),1)
        self.assertIn('Fresh sky',target.read_text())

    @unittest.skipUnless(__import__('shutil').which('inkscape'), 'Inkscape integration requires the export toolchain')
    def test_native_legend_units_survive_composition_and_pdf_export(self):
        compositor=importlib.import_module('build-current-atlas')
        source=self.root/'native.svg'
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="44in" height="19.052559in" viewBox="0 0 44 19.052559">'
                          '<g id="native-legend"><text x="2" y="4" font-size=".3">Temperature / degC / 12 to 15</text></g></svg>')
        target=self.root/'legend.svg'
        compositor.standalone_legend({'id':'fixture','source_stem':'fixture','title':'Temperature'},source,target,{'dataset_id':'fixture'},'world',[])
        self.assertIn('Temperature / degC / 12 to 15',target.read_text())
        pdf=self.root/'legend.pdf'
        subprocess.run(['bash',str(ROOT/'scripts/run-inkscape.sh'),'inkscape',str(target),'--export-filename='+str(pdf)],
                       check=True,capture_output=True,text=True)
        self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))
        info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
        self.assertIn('3168',info)


if __name__=='__main__':unittest.main()
