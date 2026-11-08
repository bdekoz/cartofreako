#!/usr/bin/env python3
"""Scientific and data-contract regression checks for the ocean additions."""
import importlib
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from scipy.io import netcdf_file

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ocean_temperature import NetCDF, h3_cell, h3_center
prep=importlib.import_module('prepare-ocean-temperature')
render=importlib.import_module('build-ocean-temperature-plates')


class OceanTests(unittest.TestCase):
    def test_calendar_alignment_after_leap_day(self):
        self.assertEqual(prep.calendar_slot(date(2024,3,1)),prep.calendar_slot(date(2025,3,1)))
        self.assertEqual(prep.calendar_slot(date(2024,2,29))+1,prep.calendar_slot(date(2024,3,1)))

    def test_strict_ties_and_history_eligibility(self):
        values=np.array([12.,12.,9.,np.nan,14.])
        eligible,high,low=prep.strict_records(values,np.array([12.,11.,12.,12.,13.]),np.array([8.,8.,10.,8.,9.]),np.array([40,30,30,40,29]))
        np.testing.assert_array_equal(eligible,[True,True,True,False,False])
        np.testing.assert_array_equal(high,[False,True,False,False,False])
        np.testing.assert_array_equal(low,[False,False,True,False,False])

    def test_target_is_compared_before_history_update(self):
        history=np.array([43]);high=np.array([25.]);low=np.array([11.])
        self.assertTrue(prep.strict_records(np.array([26.]),high,low,history)[1][0])
        high=np.maximum(high,[26.]);history+=1
        self.assertFalse(prep.strict_records(np.array([26.]),high,low,history)[1][0])

    def test_spatial_mean_precedes_record_test(self):
        actual=prep.aggregate_day(np.array([12.,8.,20.]),np.array([np.nan,np.nan,np.nan]),np.arange(3),np.array([0,0,1]),np.array([2,1]))
        np.testing.assert_allclose(actual,[10.,20.])
        # One source pixel set a high, but its H3 mean did not: do not sum
        # source-pixel record counts into the H3 record-day result.
        self.assertFalse(prep.strict_records(actual,np.array([11.,19.]),np.array([4.,4.]),np.array([30,30]))[1][0])

    def test_incomplete_membership_masks_cell_day(self):
        result=prep.aggregate_day(np.array([12.,np.nan,20.]),np.array([np.nan]*3),np.arange(3),np.array([0,0,1]),np.array([2,1]))
        self.assertTrue(np.isnan(result[0]));self.assertEqual(result[1],20.)

    def test_ice_fraction_and_sparse_ice_mask(self):
        result=prep.aggregate_day(np.array([-1.,2.,3.,4.]),np.array([.14999999,np.nan,.14,1.]),np.arange(4),np.arange(4),np.ones(4,dtype=int))
        np.testing.assert_allclose(result,[np.nan,2.,3.,np.nan],equal_nan=True)

    def test_netcdf_packed_values_fill_and_range(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture.nc'
            with netcdf_file(path,'w') as n:
                n.createDimension('x',5);v=n.createVariable('dhw','h',('x',));v[:]=[0,400,800,-32768,10001]
                v._FillValue=np.int16(-32768);v.scale_factor=np.float32(.01);v.valid_min=np.int16(0);v.valid_max=np.int16(10000)
            with NetCDF(path) as n:
                np.testing.assert_allclose(n.read('dhw'),[0,4,8,np.nan,np.nan],equal_nan=True)

    def test_h3_source_center_round_trip(self):
        c=h3_cell(34.45,133.99);lat,lon=h3_center(c)
        self.assertEqual(h3_cell(lat,lon),c)

    def test_boundaries_keep_coral_and_temperature_units_separate(self):
        self.assertEqual(render.classify(4,render.DHW_BOUNDS),1)
        self.assertEqual(render.classify(20,render.DHW_BOUNDS),5)
        self.assertEqual(render.classify(0,render.ANOMALY_BOUNDS),4)
        self.assertEqual(render.classify(5,render.HIGH_BOUNDS,side='left'),0)
        self.assertEqual(render.classify(6,render.HIGH_BOUNDS,side='left'),1)


if __name__=='__main__':unittest.main()
