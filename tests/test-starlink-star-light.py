#!/usr/bin/env python3
"""Consequential display invariants for SLSL v3, independent of export tools."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import starlink_star_light as s


class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s.register_fonts()
        cls.config=json.loads(s.CONFIG.read_text())
        cls.capability=json.loads((s.ROOT/cls.config['capability_config']).read_text())

    def test_spread_keeps_floor_unknowns_and_pops(self):
        revised=deepcopy(self.capability)
        revised['size']['radius_spread_multiplier']=2
        for area in (1,13.577335130284366,200):
            record={'kind':'antenna-site','aperture_proxy_m2':area}
            old=s.CAP.radius(record,self.capability)
            self.assertAlmostEqual(s.CAP.radius(record,revised),.04+2*(old-.04))
        for record in ({'kind':'antenna-site','aperture_proxy_m2':None},{'kind':'pop'}):
            self.assertEqual(s.CAP.radius(record,self.capability),s.CAP.radius(record,revised))
        revised['size']['radius_spread_multiplier']=-1
        with self.assertRaises(ValueError):
            s.CAP.radius({'kind':'antenna-site','aperture_proxy_m2':50},revised)

    def test_nine_shapes_have_equal_area_and_fit_collision_circle(self):
        shapes=self.config['capability_markers']
        self.assertEqual(len(set(shapes.values())),9)
        self.assertNotIn('triangle',shapes.values())
        for shape in shapes.values():
            points=s.unit_polygon(shape)
            if points is None:
                self.assertAlmostEqual(math.pi*(1/math.sqrt(math.pi))**2,1)
                continue
            area=abs(sum(x*y1-x1*y for (x,y),(x1,y1) in zip(points,points[1:]+points[:1])))/2
            self.assertAlmostEqual(area,1)
            self.assertLessEqual(max(math.hypot(x,y) for x,y in points),1)

    def test_edge_labels_keep_physical_size_and_fit_both_scales(self):
        root=s.el('g');group=s.el('g',root,id='labels')
        for x,y in ((0,0),(44,19.052559),(43.9,.02)):
            s.tx(group,x,y,'A long edge object name',12)
        for scale in (.91,.67):
            result=deepcopy(root)
            adjustments=s.fix_sky_labels(result,scale,9.6)
            for change,label in zip(adjustments,result.xpath('.//*[local-name()="text"]')):
                x,y=change['after_xy']
                self.assertGreaterEqual(x,0)
                self.assertLessEqual(x+change['estimated_width_source_inches'],s.WIDTH)
                self.assertGreater(y,0)
                self.assertLess(y,s.HEIGHT)
                self.assertAlmostEqual(float(label.get('font-size'))*72*scale,9.6)

    def test_usa_regions_include_aleutians_and_northwest_hawaii(self):
        probes={'conus':[(-122.4194,37.7749),(-68.2,44.4)],
                'alaska':[(172.5,52.9),(-130,55),(-156.8,71.3)],
                'hawaii':[(-178.3,28.4),(-155.5,19.6)]}
        for region in self.config['regions']:
            west,south,east,north=region['bounds_lon_lat']
            for lon,lat in probes[region['id']]:
                if west>0 and lon<0: lon+=360
                self.assertLessEqual(west,lon);self.assertLessEqual(lon,east)
                self.assertLessEqual(south,lat);self.assertLessEqual(lat,north)

    def test_sky_uses_gutter_without_clipping_or_moving_objects(self):
        source=s.el('g',id='source-cartography')
        stars=s.el('g',source,id='stars')
        s.el('circle',stars,id='edge-object',cx=0,cy=0,r='.15',data_kind='planet')
        labels=s.el('g',source,id='labels');s.tx(labels,0,0,'Edge object',12)
        root=s.sheet('SLSL1','world')
        result=s.add_sky(root,source,(.25,.25,43.5,s.HEIGHT-.5),9.6,
                         side_margin_factor=.5,margin_box=(0,0,s.WIDTH,s.HEIGHT))
        self.assertFalse(root.xpath('//*[@clip-path]'))
        self.assertEqual(root.xpath('//*[@id="edge-object"]')[0].get('cx'),'0')
        scale=result['scale'];dx,dy=result['translation']
        self.assertAlmostEqual(result['side_margin_inches']*2,result['previous_side_margin_inches'])
        self.assertAlmostEqual(dx,s.WIDTH-(dx+s.WIDTH*scale))
        self.assertGreater(dx-.15*scale,0)
        self.assertGreater(dy-.15*scale,0)

    def test_world_sky_fits_ink_after_removing_an_existing_print_inset(self):
        source=s.el('g',id='source-cartography')
        frame=s.el('g',source,id='setouchi-astronomy-frame',transform='translate(.25 .108) scale(.988636)')
        stars=s.el('g',frame,id='stars')
        s.el('circle',stars,id='edge-object',cx=0,cy=0,r='.15',data_kind='planet')
        labels=s.el('g',frame,id='labels');s.tx(labels,0,0,'Edge object',12)
        bounds=[-.15,-.15,44.3,s.HEIGHT+.3]
        def measured(content):
            self.assertIsNone(content.xpath('.//*[@id="setouchi-astronomy-frame"]')[0].get('transform'))
            return bounds
        root=s.sheet('SLSL1','world')
        with patch.object(s,'astronomy_ink_bounds',side_effect=measured):
            result=s.add_sky(root,source,(.25,.25,43.5,s.HEIGHT-.5),9.6,
                margin_box=(0,0,s.WIDTH,s.HEIGHT),page_margin_inches=.125)
        scale=result['scale'];dx,dy=result['translation'];x,y,w,h=bounds
        margins=[dx+x*scale,dy+y*scale,s.WIDTH-dx-(x+w)*scale,s.HEIGHT-dy-(y+h)*scale]
        self.assertGreaterEqual(min(margins),.125-1e-9)
        self.assertAlmostEqual(min(margins),.125)
        self.assertLess(max(margins),.5)
        self.assertEqual(root.xpath('//*[@id="edge-object"]')[0].get('cx'),'0')
        label=root.xpath('//*[@id="labels"]/*')[0]
        self.assertAlmostEqual(float(label.get('font-size'))*72*scale,9.6)

    def test_observer_notes_distinguish_sky_from_geographic_details(self):
        for plate in s.TITLES:
            self.assertIn('SLSL',s.observer_notes(plate,'world'))
            self.assertIn('Alaska',s.observer_notes(plate,'usa'))
        self.assertIn('do not relocate',s.observer_notes('SLSL2','usa'))

    def test_regional_crop_contains_displaced_source_records(self):
        regions=[{'id':'conus','bounds_lon_lat':[-125,24,-66,50],'projected_bounds':[20,2,8,7]}]
        records=[{'id':'us-site','kind':'antenna-site','geometry':{'coordinates':[-122,38]},
                  'display_xy':[30,11],'radius_inches':.32},
                 {'id':'outside','kind':'pop','geometry':{'coordinates':[10,50]},
                  'display_xy':[42,16],'radius_inches':.032}]
        result=s.groundstation_regions(regions,{'records':records})[0]
        self.assertEqual(result['selected_source_record_ids'],['us-site'])
        x,y,w,h=result['projected_bounds']
        self.assertGreater(x+w,30.32);self.assertGreater(y+h,11.32)
        self.assertLess(x+w,42)
        self.assertEqual(regions[0]['projected_bounds'],[20,2,8,7])


if __name__=='__main__':
    unittest.main()
