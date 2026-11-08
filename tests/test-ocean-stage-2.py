#!/usr/bin/env python3
"""Independent numerical fixtures for Stage 2 scientific boundary rules."""
from datetime import date,timedelta
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from ocean_stage_2 import climatology,event_flags,event_edges,thermal_seasons,dates,OUTPUT


class ClimateTests(unittest.TestCase):
    def test_percentile_and_leap_smoothing(self):
        rng=np.random.default_rng(42);a=rng.normal(size=(2,30,365)).astype('float32')
        mean,q,counts,years=climatology(a)
        for c in range(2):
            raw=[];rm=[]
            for d in range(365):
                values=a[c][:,[(d+k)%365 for k in range(-5,6)]].ravel().astype('float64')
                raw.append(np.quantile(values,.9,method='linear'));rm.append(np.mean(values,dtype='float64'))
            for values,actual in [(raw,q[c]),(rm,mean[c])]:
                leap=np.insert(values,59,(values[58]+values[59])/2)
                expected=np.array([np.mean(leap[[(d+k)%366 for k in range(-15,16)]]) for d in range(366)])
                np.testing.assert_allclose(actual,expected,atol=2e-7)
        self.assertTrue(np.all(counts==330));self.assertTrue(np.all(years==30))

    def test_insufficient_years_and_missing_window(self):
        a=np.ones((2,30,365),dtype='float32');a[0,:7]=np.nan;a[1,:,100:120]=np.nan
        m,q,_,_=climatology(a)
        self.assertTrue(np.isnan(q[0]).all());self.assertTrue(np.isnan(q[1,110]))
        self.assertAlmostEqual(float(m[1,300]),1)


class EventTests(unittest.TestCase):
    def flags(self,a):
        ds=[date(2025,12,20)+timedelta(days=i) for i in range(len(a))]
        return event_flags(np.array([a]),np.ones((1,366)),ds)[0]

    def test_duration_and_strict_ties(self):
        f=self.flags([1]+[2]*4+[1]+[2]*5+[1]*3)
        self.assertEqual(int(np.sum((f&4)>0)),5)
        self.assertEqual(int(np.sum((f&2)>0)),9)

    def test_observed_gap_and_missing_barrier(self):
        for gap,expected in [([0,0],12),([0,0,0],10),([np.nan],10)]:
            f=self.flags([0]+[2]*5+gap+[2]*5+[0]*3)
            self.assertEqual(int(np.sum((f&4)>0)),expected)
            self.assertEqual(int(np.sum((f&8)>0)),1 if len(gap)==2 else 2)

    def test_pending_at_cutoff_and_calendar_year(self):
        f=self.flags([0]*10+[2]*4)
        self.assertEqual(int(np.sum((f&32)>0)),4);self.assertFalse(np.any(f&4))
        f=self.flags([0]*10+[2]*6+[0]*3)
        self.assertEqual(int(np.sum((f&8)>0)),1)

    def test_pending_run_can_extend_an_earlier_event(self):
        f=self.flags([0]+[2]*5+[0]*2+[2]*3)
        self.assertTrue(event_edges(f,1,5)[1])
        known=((f&1)>0)&((f&32)==0)
        self.assertEqual(int(known.sum()),8)


class JointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules=[]
        for name in ('prepare-coastal-compound-heat','prepare-heat-particulate-coexposure'):
            spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);cls.modules.append(module)

    def test_four_states_and_missing_side(self):
        coastal,_=self.modules;land=np.array([[0,2,0,2,np.nan]]);water=np.array([[0,0,2,2,2]])
        states=coastal.joint_states(land,water,np.ones((5,366)),np.ones((5,366)),[date(2025,1,1)])
        self.assertEqual(states.tolist(),[[1,2,3,4,0]])

    def test_containing_cell_and_shift(self):
        _,india=self.modules
        self.assertEqual(india.containing_cell(28.75,77.25),122*720+154)
        pm=np.array([[36.],[36.],[35.]]);valid=np.array([[True],[False],[True]])
        heat=np.array([[2.],[0.],[2.]]);q=np.ones((1,366));ds=dates(2025,3)
        self.assertEqual(india.station_states(pm,valid,heat,q,ds).ravel().tolist(),[4,0,2])
        self.assertEqual(india.station_states(pm,valid,heat,q,ds,shift=1).ravel().tolist(),[3,0,0])

    def test_geometry_barrier_and_dateline(self):
        import shapely
        coastal,_=self.modules
        land=shapely.box(-2,-2,0,2).union(shapely.box(1,-.5,1.5,.5))
        result=coastal.sea_visible((0,0),np.array([[2,2],[0,2],[0,-1]]),land)
        self.assertEqual(result.tolist(),[True,False,False])
        self.assertFalse(coastal.sea_visible((0,179),np.array([[0,-179]]),shapely.box(0,0,1,1))[0])

    def test_reference_detector_on_complete_series(self):
        path=OUTPUT/'research/marineHeatWaves.py'
        if not path.exists():self.skipTest('Pinned reference must be fetched for the integration comparison')
        spec=importlib.util.spec_from_file_location('mhw_reference',path);ref=importlib.util.module_from_spec(spec)
        # NumPy 2 rejects the reference's implicit conversion of a length-one
        # array to a scalar. Keep downloaded bytes pristine; adapt that one
        # indexing assignment in memory without altering the event algorithm.
        code=path.read_text();old='doy[tt] = doy_leapYear[(month_leapYear == month[tt]) * (day_leapYear == day[tt])]'
        assert code.count(old)==1
        exec(compile(code.replace(old,old+'.item()').replace('np.NaN','np.nan'),str(path),'exec'),ref.__dict__)
        ds=sum([dates(y) for y in range(1991,2027)],[])
        t=np.array([d.toordinal() for d in ds]);x=np.zeros(len(t))
        baseline_end=ds.index(date(2021,1,1));x[:baseline_end]=np.arange(baseline_end)%3
        first=ds.index(date(2025,1,1));x[first+3:first+8]=3;x[first+10:first+16]=3
        x[first+30:first+34]=3;x[first+60:first+65]=3
        event,clim=ref.detect(t,x,climatologyPeriod=[1991,2020])
        q=np.full((1,366),2.);f=event_flags(x[None,:],q,ds)[0]
        self.assertEqual(np.flatnonzero(f&8).tolist(),list(event['index_start']))
        self.assertEqual(np.flatnonzero(f&16).tolist(),list(event['index_end']))


class SeasonTests(unittest.TestCase):
    def fixture(self,phase=0,cutoff=None,missing=False):
        ds=dates(2024)+dates(2025)+dates(2026)
        if cutoff:ds=[d for d in ds if d<=cutoff]
        curve=15-5*np.cos(2*np.pi*(np.arange(366)-phase)/366)
        values=np.array([curve[(d.replace(year=2000)-date(2000,1,1)).days] for d in ds])
        if missing:values[ds.index(date(2025,2,1))]=np.nan
        return curve,values,ds

    def test_north_and_south_seasons(self):
        for phase in (0,183):
            curve,values,ds=self.fixture(phase)
            r=thermal_seasons(values[None,:],curve[None,:],ds,2025)
            self.assertEqual(r['status'][0],0);self.assertEqual(r['onset_departure'][0],0)
            self.assertTrue(170<r['length'][0]<195);self.assertEqual(r['length_departure'][0],0)

    def test_weak_multi_missing_and_open(self):
        curve,values,ds=self.fixture(cutoff=date(2026,7,1))
        r=thermal_seasons(values[None,:],curve[None,:],ds,2026)
        self.assertEqual(r['status'][0],6);self.assertTrue(np.isnan(r['length'][0]))
        r=thermal_seasons(values[None,:],np.ones((1,366)),ds,2026);self.assertEqual(r['status'][0],1)
        multi=15-5*np.cos(4*np.pi*np.arange(366)/366)
        r=thermal_seasons(values[None,:],multi[None,:],ds,2025);self.assertEqual(r['status'][0],3)
        curve,values,ds=self.fixture(missing=True)
        r=thermal_seasons(values[None,:],curve[None,:],ds,2025);self.assertEqual(r['status'][0],5)


if __name__=='__main__':unittest.main()
