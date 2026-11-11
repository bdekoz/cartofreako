#!/usr/bin/env python3
"""Exercise complete transactions, frozen build routing and scientific lags."""
from datetime import date
import builtins
import csv
import gzip
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

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

    def test_preflight_rejects_missing_python_gdal_before_acquisition(self):
        credentials = self.root/'netrc'
        credentials.write_text('machine ftp.ptree.jaxa.jp login fixture password fixture\n')
        credentials.chmod(0o600)
        original_import = builtins.__import__
        def without_gdal(name, *args, **kwargs):
            if name == 'osgeo':
                raise ModuleNotFoundError("No module named 'osgeo'")
            return original_import(name, *args, **kwargs)
        with patch.dict(os.environ, {'PTREE_NETRC': str(credentials),
                                     'ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY': '0'}), \
             patch('shutil.which', return_value='/fixture/bin/tool'), \
             patch('builtins.__import__', side_effect=without_gdal), \
             patch('subprocess.run') as run, \
             patch('data_sources.local_input_paths') as inputs:
            with self.assertRaisesRegex(dataset.DatasetError, 'GDAL Python bindings unavailable.*python3-gdal'):
                update.preflight(self.root)
        self.assertEqual(run.call_count, 1)
        self.assertIn('--check-credentials', run.call_args.args[0])
        inputs.assert_not_called()

    def test_native_country_references_are_required_from_configured_data_root(self):
        with patch.dict(os.environ, {'NATIVE_SWARM_DATA_ROOT': str(self.root)}):
            required = set(local_input_paths())
        for name in ('all.json', 'slim-2.json', 'slim-3.json'):
            self.assertIn(self.root/'iso-3166'/name, required)

    def india_source(self, *, second_longitude=None, sensor_eligible=True):
        edition = self.root/'edition'
        edition.mkdir()
        climate = edition/'climate.json'
        climate.write_text(json.dumps({'ocean_cutoff': '2026-11-07'}))
        source = Sources(edition, '2026-11-11T00:00:00Z', self.root/'cache')
        source.bind('CLIMATE_CONFIG', climate)
        reference = dict(station_id='233415', sensor_id='1', date='2026-11-05',
                         valid_hours='24', mean_ug_m3='25', latitude='30.735567',
                         longitude='76.775714', eligible='True', station_name='Chandigarh',
                         station_type='reference', source='openaq-cpcb')
        rows = [reference, {**reference, 'station_id': '5728639', 'sensor_id': '2',
                           'station_type': 'air-sensor', 'station_name': 'Srinagar',
                           'source': 'openaq-airgradient', 'eligible': str(sensor_eligible)}]
        if second_longitude is not None:
            rows.append({**reference, 'date': '2026-11-06', 'longitude': second_longitude})

        def fetched(*args, **kwargs):
            output = edition/'inputs/india/openaq'
            output.mkdir(parents=True)
            with gzip.open(output/'openaq-station-days.csv.gz', 'wt', newline='') as stream:
                writer = csv.DictWriter(stream, rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            (output/'openaq-quality.json').write_text(json.dumps({
                'failures': [], 'observed_last_date': '2026-11-06',
                'eligible_last_date': '2026-11-06', 'coverage': 'fixture monitors'}))
        source.run = Mock(side_effect=fetched)
        return source

    def test_india_accepts_archive_air_sensor_as_validated_low_cost_class(self):
        source = self.india_source()
        source.india()
        self.assertEqual(source.records[0]['id'], 'india')
        path = source.edition/source.bindings['INDIA_OBSERVATIONS']
        with gzip.open(path, 'rt') as stream:
            self.assertIn('air-sensor', {row['station_type'] for row in csv.DictReader(stream)})

    def test_india_ignores_coordinate_serialization_noise(self):
        source = self.india_source(second_longitude='76.77571400000001')
        source.india()
        self.assertEqual(source.records[0]['status'], 'validated')

    def test_india_still_rejects_station_movement(self):
        source = self.india_source(second_longitude='76.775715')
        with self.assertRaisesRegex(AssertionError, 'Station metadata drift'):
            source.india()

    def test_india_still_requires_eligible_low_cost_observations(self):
        source = self.india_source(sensor_eligible=False)
        with self.assertRaisesRegex(dataset.DatasetError, 'station-days: low-cost'):
            source.india()

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

    def completed_failure(self):
        def reject():
            raise dataset.DatasetError('fixture final validation failure')
        with self.assertRaisesRegex(dataset.DatasetError, 'fixture final validation'):
            update.update(self.root, requested_as_of='2026-11-08T00:00:00Z',
                          adapters=self.adapters(), validate_sources=reject)
        path = next((self.root/'runs').glob('*/state.json'))
        return path, json.loads(path.read_text())

    def test_validation_only_retry_retains_acquisition_and_records_new_validator(self):
        state_path, state = self.completed_failure()
        acquisition = state['implementation']
        revised = {**acquisition, 'revision': 'f' * 40}
        validator = Mock()
        with patch.object(update, 'implementation_record', return_value=revised), \
             patch.object(Sources, 'run', side_effect=AssertionError('acquisition must not run')):
            path = update.validate_completed(self.root, state['dataset_id'], validate_sources=validator)
        validator.assert_called_once_with()
        manifest = dataset.load(path)[1]
        self.assertEqual(manifest['implementation'], acquisition)
        self.assertEqual(manifest['validation']['implementation'], revised)
        self.assertEqual(dataset.load(self.root/'current.json')[0], path)
        final = json.loads(state_path.read_text())
        self.assertEqual(final['status'], 'active')
        self.assertNotIn('error', final)

    def test_validation_only_retry_rejects_incomplete_acquisition(self):
        with self.assertRaises(dataset.DatasetError):
            self.execute(adapters=self.adapters(fail='ocean'))
        state = json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        with self.assertRaisesRegex(dataset.DatasetError, 'all sources complete'):
            update.validate_completed(self.root, state['dataset_id'], validate_sources=Mock())
        self.assertFalse((self.root/'current.json').exists())

    def test_validation_only_retry_rejects_unverified_acquisition_method(self):
        path, state = self.completed_failure()
        state.pop('acquisition_verified')
        state['error'] = 'Implementation changed during acquisition'
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(dataset.DatasetError, 'completion is unverified'):
            update.validate_completed(self.root, state['dataset_id'], validate_sources=Mock())

    def test_validation_only_retry_recognizes_legacy_final_native_failure(self):
        path, state = self.completed_failure()
        state.pop('acquisition_verified')
        state['error'] = 'Source command failed: ' + str(ROOT/'build/validate-dataset-native')
        path.write_text(json.dumps(state))
        result = update.validate_completed(self.root, state['dataset_id'], validate_sources=lambda: None)
        self.assertEqual(dataset.load(result)[1]['implementation'], state['implementation'])

    def test_validation_only_retry_rejects_changed_completed_bytes(self):
        _, state = self.completed_failure()
        row = state['completed_files']['natural-earth'][0]
        (self.root/'editions'/state['dataset_id']/row['path']).write_text('changed')
        with self.assertRaisesRegex(dataset.DatasetError, 'checkpoint changed'):
            update.validate_completed(self.root, state['dataset_id'], validate_sources=Mock())
        self.assertFalse((self.root/'current.json').exists())

    def test_validation_only_retry_rejects_changed_product_definitions(self):
        _, state = self.completed_failure()
        original = update.digest
        with patch.object(update, 'digest', side_effect=lambda p: '0' * 64
                          if Path(p).name == 'data-products.json' else original(p)):
            with self.assertRaisesRegex(dataset.DatasetError, 'Product definitions changed'):
                update.validate_completed(self.root, state['dataset_id'], validate_sources=Mock())

    def test_validation_only_retry_rejects_validator_input_mutation(self):
        _, state = self.completed_failure()
        row = state['completed_files']['natural-earth'][0]
        path = self.root/'editions'/state['dataset_id']/row['path']
        with self.assertRaisesRegex(dataset.DatasetError, 'bytes changed during final validation'):
            update.validate_completed(self.root, state['dataset_id'],
                                      validate_sources=lambda: path.write_text('changed'))
        self.assertFalse((self.root/'current.json').exists())

    def test_validation_only_retry_rejects_validator_implementation_change(self):
        _, state = self.completed_failure()
        changed = {**state['implementation'], 'revision': 'f' * 40}
        with patch.object(update, 'implementation_record', side_effect=[state['implementation'], changed]):
            with self.assertRaisesRegex(dataset.DatasetError, 'Implementation changed during final validation'):
                update.validate_completed(self.root, state['dataset_id'], validate_sources=lambda: None)
        self.assertFalse((self.root/'current.json').exists())

    def test_interrupted_validation_only_retry_can_continue(self):
        state_path, state = self.completed_failure()
        with self.assertRaises(KeyboardInterrupt):
            update.validate_completed(self.root, state['dataset_id'],
                                      validate_sources=Mock(side_effect=KeyboardInterrupt))
        self.assertEqual(json.loads(state_path.read_text())['status'], 'validating')
        path = update.validate_completed(self.root, state['dataset_id'], validate_sources=lambda: None)
        self.assertEqual(dataset.load(self.root/'current.json')[0], path)

    def test_deferred_astronomy_saves_other_sources_and_resume_completes_it(self):
        old,_=fixtures.fixture(self.root/'editions/old','old')
        dataset.activate(self.root,old)
        before=(self.root/'current.json').read_bytes()
        calls=[]
        validate=Mock()
        with self.assertRaisesRegex(update.IncompleteUpdate,'astronomy'):
            update.update(self.root,requested_as_of='2026-11-08T00:00:00Z',
                          adapters=self.adapters(calls=calls),validate_sources=validate,
                          keep_going=True,defer=['astronomy'])
        self.assertEqual(calls,[name for name in update.ORDER if name!='astronomy'])
        validate.assert_not_called()
        state_path=next((self.root/'runs').glob('*/state.json'))
        state=json.loads(state_path.read_text())
        self.assertEqual(state['status'],'incomplete')
        self.assertEqual(state['issues']['astronomy']['status'],'deferred')
        self.assertEqual(len(state['sources']),11)
        self.assertEqual((self.root/'current.json').read_bytes(),before)
        self.assertFalse((self.root/'editions'/state['dataset_id']/'dataset.json').exists())
        calls=[]
        path=self.execute(resume=state['dataset_id'],adapters=self.adapters(calls=calls),keep_going=True)
        self.assertEqual(calls,['astronomy'])
        self.assertEqual(dataset.load(self.root/'current.json')[0],path)

    def test_resilient_failure_continues_other_sources_without_activation(self):
        calls=[]
        with self.assertRaisesRegex(update.IncompleteUpdate,'astronomy'):
            self.execute(adapters=self.adapters(fail='astronomy',calls=calls),keep_going=True)
        self.assertEqual(calls,list(update.ORDER))
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        self.assertEqual(state['issues']['astronomy']['status'],'failed')
        self.assertEqual(len(state['sources']),11)
        self.assertFalse((self.root/'current.json').exists())

    def test_resilient_orbital_failure_blocks_astronomy_and_keeps_independent_work(self):
        calls=[]
        with self.assertRaises(update.IncompleteUpdate):
            self.execute(adapters=self.adapters(fail='orbital',calls=calls),keep_going=True)
        self.assertNotIn('astronomy',calls)
        self.assertIn('anthropocene',calls)
        self.assertIn('india',calls)
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        self.assertEqual(state['issues']['astronomy']['status'],'blocked')
        self.assertEqual(state['issues']['astronomy']['dependencies'],['orbital'])

    def test_resilient_resources_failure_blocks_ocean_context_and_india(self):
        calls=[]
        with self.assertRaises(update.IncompleteUpdate):
            self.execute(adapters=self.adapters(fail='resources',calls=calls),keep_going=True)
        self.assertIn('ocean',calls)
        self.assertIn('atmosphere',calls)
        self.assertNotIn('ocean-context',calls)
        self.assertNotIn('india',calls)
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        self.assertEqual(state['issues']['india']['dependencies'],['ocean-context'])

    def test_failed_adapter_cannot_leave_partial_validation_records_or_bindings(self):
        adapters=self.adapters()
        original=adapters['resources']
        def fail_after_record(source):
            original(source)
            source.bind('LEAKED_PARTIAL_BINDING',source.directory('resources')/'input.json')
            raise dataset.DatasetError('fixture failed after recording partial work')
        adapters['resources']=fail_after_record
        with self.assertRaises(update.IncompleteUpdate):
            self.execute(adapters=adapters,keep_going=True)
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        self.assertNotIn('resources',[r['id'] for r in state['sources']])
        self.assertNotIn('resources',state['completed_files'])
        self.assertNotIn('LEAKED_PARTIAL_BINDING',state['bindings'])

    def test_failed_context_invalidates_mutated_ocean_checkpoint_and_resume_repairs_it(self):
        adapters=self.adapters()
        def fail_after_mutation(source):
            (source.directory('ocean')/'input.json').write_text('modified by failed context preparation')
            raise dataset.DatasetError('context failed')
        adapters['ocean-context']=fail_after_mutation
        with self.assertRaises(update.IncompleteUpdate):
            self.execute(adapters=adapters,keep_going=True)
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        self.assertNotIn('ocean',[r['id'] for r in state['sources']])
        self.assertNotIn('ocean',state['completed_files'])
        self.assertEqual(state['issues']['ocean']['status'],'invalidated')
        calls=[]
        path=self.execute(resume=state['dataset_id'],adapters=self.adapters(calls=calls),keep_going=True)
        self.assertEqual(calls,['ocean','ocean-context','india'])
        self.assertTrue(path.is_file())

    def test_resilient_resume_still_rejects_changed_completed_bytes(self):
        with self.assertRaises(update.IncompleteUpdate):
            self.execute(adapters=self.adapters(),keep_going=True,defer=['astronomy'])
        state=json.loads(next((self.root/'runs').glob('*/state.json')).read_text())
        record=state['completed_files']['natural-earth'][0]
        (self.root/'editions'/state['dataset_id']/record['path']).write_text('corrupt')
        calls=[]
        with self.assertRaisesRegex(dataset.DatasetError,'Resume source bytes changed'):
            self.execute(resume=state['dataset_id'],adapters=self.adapters(calls=calls),keep_going=True)
        self.assertEqual(calls,[])
        self.assertFalse((self.root/'current.json').exists())

    def test_unknown_deferred_source_is_rejected_before_acquisition(self):
        calls=[]
        with self.assertRaisesRegex(dataset.DatasetError,'Unknown deferred source'):
            self.execute(adapters=self.adapters(calls=calls),defer=['not-a-source'])
        self.assertEqual(calls,[])
        self.assertFalse((self.root/'runs').exists())

    def test_resilient_mode_never_blesses_unexpected_changes_to_a_completed_source(self):
        calls=[]
        adapters=self.adapters(calls=calls)
        original=adapters['resources']
        def unexpected_mutation(source):
            original(source)
            (source.directory('natural-earth')/'input.json').write_text('unexpected change')
        adapters['resources']=unexpected_mutation
        with self.assertRaisesRegex(dataset.DatasetError,'Completed source changed unexpectedly'):
            self.execute(adapters=adapters,keep_going=True)
        self.assertNotIn('atmosphere',calls)
        self.assertFalse((self.root/'current.json').exists())

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
