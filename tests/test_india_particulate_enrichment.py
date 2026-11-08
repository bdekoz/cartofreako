"""Scientific aggregation and identity boundaries for the India adapters."""
import importlib.util
import math
from pathlib import Path
import unittest

import pandas as pd

SPEC = importlib.util.spec_from_file_location('india', Path(__file__).resolve().parents[1]/'scripts/prepare-india-particulate-enrichment.py')
india = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(india)


def reading(hour, value=40, sensor=1, parameter='pm25', minute=0):
    return dict(sensor_id=sensor,parameter=parameter,
        datetime_local=f'2026-11-04T{hour:02}:{minute:02}:00+05:30',
        value=value,quality_flag='',latitude=28.6,longitude=77.3)


class IndiaParticulateTests(unittest.TestCase):
    def test_units_and_missing_are_not_zero(self):
        self.assertEqual(india.normalize_value('pm25','µg/m³','0'),(0,''))
        for unit,value in [('AQI','40'),('µg/m³','NA'),('µg/m³','-1')]:
            result,reason=india.normalize_value('pm25',unit,value)
            self.assertTrue(math.isnan(result));self.assertTrue(reason)
        self.assertEqual(india.normalize_value('temperature','c','-4'),(-4,''))

    def test_subhourly_samples_do_not_inflate_completeness(self):
        raw=pd.DataFrame([reading(h,minute=m) for h in range(17) for m in [0,15,30,45]])
        _,hour,daily=india.hourly_and_daily(raw)
        self.assertEqual(len(hour),17)
        self.assertFalse(daily.iloc[0].eligible)

    def test_conflicts_are_excluded_and_cannot_be_restored_by_duplicates(self):
        raw=pd.DataFrame([reading(h) for h in range(18)]+[reading(0,60),reading(0,40)])
        normalized,hour,daily=india.hourly_and_daily(raw)
        self.assertEqual(len(hour),17)
        self.assertFalse(daily.iloc[0].eligible)
        self.assertEqual(normalized.iloc[0].quality_flag,'conflicting_duplicate')

    def test_sensor_selection_and_local_midnight(self):
        raw=pd.DataFrame([reading(h,sensor=s) for s in [2,1] for h in range(18)])
        _,hour,daily=india.hourly_and_daily(raw)
        self.assertEqual(daily.iloc[0].sensor_id,1)
        self.assertEqual(hour.selected.sum(),18)
        self.assertEqual(hour.iloc[0].hour_utc,'2026-11-03T18:30:00Z')

    def test_wind_direction_uses_circular_mean(self):
        raw=pd.DataFrame([reading(0,359,parameter='wind_direction'),reading(0,1,parameter='wind_direction',minute=30)])
        _,hour,_=india.hourly_and_daily(raw)
        self.assertLess(min(hour.iloc[0].value,360-hour.iloc[0].value),1e-6)

    def test_negative_coarse_fraction_is_visible(self):
        raw=pd.DataFrame([reading(0,80),reading(0,60,sensor=2,parameter='pm10')])
        _,hour,_=india.hourly_and_daily(raw)
        pair=india.paired_hours(hour)
        self.assertEqual(pair.iloc[0].coarse_ug_m3,-20)
        self.assertEqual(pair.iloc[0].quality_flag,'pm25_exceeds_pm10')

    def test_missing_day_breaks_episode_and_censors_boundary(self):
        frame=pd.DataFrame([dict(canonical_id='x',parameter='pm25',date=d,mean=100,eligible=True)
                            for d in ['2026-11-01','2026-11-02','2026-11-04']])
        runs=[r for r in india.episodes(frame) if r['benchmark']=='atlas_35']
        self.assertEqual([r['observed_days'] for r in runs],[2,1])
        self.assertTrue(runs[0]['right_censored'])

    def test_ambiguous_station_match_is_not_merged(self):
        row=dict(station_id='site_1',station_name='Anand Vihar, Delhi - DPCC',source='cpcb_caaqm',latitude=28.6,longitude=77.3)
        match,status=india.match_station('Anand Vihar, New Delhi - DPCC','CPCB',28.6,77.3,[row,dict(row,station_id='site_2')])
        self.assertIsNone(match);self.assertEqual(status,'ambiguous_match')

    def test_published_model_discrepancy_is_flagged_without_rescaling(self):
        html="""const data = { labels: ["2026-11-08"], datasets: [
        {label: 'One', data: [60]}, {label: 'Two', data: [41]}]
        };
        const data2 = { labels: ["2026-11-07 12:00:00"], datasets: [
        {label: 'Stubble Burning', data: [7]}]
        };"""
        rows=india.parse_dss(html)
        self.assertEqual(rows[0]['percent_total_pm25'],60)
        self.assertEqual(rows[0]['published_category_sum_percent'],101)
        self.assertTrue(rows[0]['composition_quality_flag'])
        self.assertFalse(rows[0]['renormalized'])
        self.assertEqual(rows[0]['issue_time_utc'],'')
        self.assertIsNone(rows[-1]['published_category_sum_percent'])

    def test_pm10_cell_days_union_multiple_monitors(self):
        spec=importlib.util.spec_from_file_location('profiles',Path(__file__).resolve().parents[1]/'scripts/build-india-particulate-profiles.py')
        profiles=importlib.util.module_from_spec(spec);spec.loader.exec_module(profiles)
        rows=pd.DataFrame([dict(date='2026-11-01',latitude=28.6,longitude=77.3,
            mean=value,valid_hours=hours,eligible=hours>=18) for value,hours in [(80,24),(120,18),(200,17)]])
        measured,high=profiles.cell_days(rows)
        self.assertEqual(sum(map(len,measured.values())),1)
        self.assertEqual(sum(map(len,high.values())),1)


if __name__=='__main__':
    unittest.main()
