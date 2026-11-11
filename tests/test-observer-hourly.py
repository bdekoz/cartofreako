#!/usr/bin/env python3
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import observer_hourly as H


class HourlyStudyTests(unittest.TestCase):
    def test_schedule_keeps_original_minute_and_rolls_dates(self):
        rows=H.schedule('2026-11-09T01:12:00Z',25)
        self.assertEqual(H.timestamp(rows[23]),'2026-11-10T00:12:00Z')
        self.assertEqual(H.timestamp(rows[24]),'2026-11-10T01:12:00Z')
        self.assertEqual(rows[0].astimezone(H.PACIFIC).strftime('%Y-%m-%d %H:%M %Z'),'2026-11-08 17:12 PST')
        self.assertEqual({int((b-a).total_seconds()) for a,b in zip(rows,rows[1:])},{3600})

    def test_ambiguous_time_and_invalid_steps_are_rejected(self):
        for value in ('2026-11-09T01:12:00','2026-11-09'):
            with self.assertRaises(ValueError):H.instant(value)
        with self.assertRaises(ValueError):H.schedule('2026-11-09T01:12:00Z',24,0)

    def test_derivation_changes_time_and_resolves_paths_without_rewriting_acquisition(self):
        original={'timestamp':'2026-11-09T01:12:00Z','catalogs':{'primary':{'file':'active.csv'},'nasa_ssc_reference':{'file':'reference.json'}},
                  'snapshot':{'collection_completed_at':'2026-11-09T01:12:36Z','checksum_file':'SHA256SUMS'}}
        result=H.derived_profile(original,Path('/tmp/catalog'),H.instant('2026-11-09T02:12:00Z'))
        self.assertEqual(result['catalogs']['primary']['file'],'/tmp/catalog/active.csv')
        self.assertEqual(result['catalogs']['nasa_ssc_reference']['file'],'/tmp/catalog/reference.json')
        self.assertEqual(result['snapshot']['collection_completed_at'],original['snapshot']['collection_completed_at'])
        self.assertEqual(original['timestamp'],'2026-11-09T01:12:00Z')
        self.assertEqual(original['catalogs']['primary']['file'],'active.csv')

    def test_sidereal_reproduces_reference_and_hourly_change(self):
        start=H.instant('2026-11-09T01:12:00Z')
        angle=H.sidereal_degrees(start,-122.4194)
        self.assertAlmostEqual(angle,303.813,places=3)
        following=H.schedule(start,2)[1]
        self.assertAlmostEqual((H.sidereal_degrees(following,-122.4194)-angle)%360,15.0410686,places=5)

    def test_duplicate_and_below_horizon_objects_are_rejected(self):
        root=H.S.el('svg')
        H.S.el('circle',root,data_object_kind='locpoint',data_norad_id='1',data_observer_elevation_deg='2')
        H.S.el('circle',root,data_object_kind='locpoint',data_norad_id='1',data_observer_elevation_deg='3')
        with self.assertRaisesRegex(ValueError,'Duplicate'):H.inventory(root)
        root.remove(root[-1]);root[0].set('data-observer-elevation-deg','-0.1')
        with self.assertRaisesRegex(ValueError,'Below-horizon'):H.inventory(root)

    def test_cache_rejects_changed_or_missing_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'map.svg';p.write_text('original')
            rows=[H.file_record(p,root)]
            self.assertTrue(H.files_match(rows,root))
            p.write_text('changed!');self.assertFalse(H.files_match(rows,root))
            p.unlink();self.assertFalse(H.files_match(rows,root))

    def test_partial_schedule_is_not_a_complete_delivery(self):
        with self.assertRaisesRegex(ValueError,'incomplete'):H.validate_sequence([],{},60,24)

    def test_orientation_view_removes_satellites_and_keeps_curves(self):
        root=H.S.el('svg');defs=H.S.el('defs',root);source=H.S.el('g',defs,id='source-cartography')
        curves=H.S.el('g',source,id='observer-reference')
        H.S.el('path',curves,id='observer-horizon-segment-1',d='M 0 1 L 2 3')
        H.S.el('path',curves,id='celestial-equator-segment-1',d='M 0 2 L 3 4')
        objects=H.S.el('g',source,id='starlink')
        H.S.el('circle',objects,data_object_kind='locpoint',data_norad_id='1')
        result=H.orientation_only(root)
        self.assertEqual(H.paths(result,'celestial-equator'),H.paths(root,'celestial-equator'))
        self.assertFalse(result.xpath('//*[@data-object-kind]'))
        self.assertEqual(len(root.xpath('//*[@data-object-kind]')),1)


if __name__=='__main__':unittest.main()
