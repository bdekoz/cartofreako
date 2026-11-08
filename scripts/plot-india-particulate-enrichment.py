#!/usr/bin/env python3
"""Export scientific review figures from the dated local enrichment outputs."""
import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); root = args.root.resolve()
    output = root/'figures'; output.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
                         'axes.spines.top':False, 'axes.spines.right':False})
    days = pd.date_range('2026-10-01', '2026-11-08', name='date')
    context = pd.read_csv(root/'context/delhi-episode-context.csv.gz', parse_dates=['date']).set_index('date').reindex(days)
    fire = pd.read_csv(root/'context/firms-satellite-days.csv.gz', parse_dates=['local_date'])
    dss = pd.read_csv(root/'context/iitm-model-contributions.csv.gz', parse_dates=['valid_date'])
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True,
                             gridspec_kw={'height_ratios':[1.3, 1, 1, 1]})
    for name, label, color in [('pm25','PM2.5','#a94323'),('pm10','PM10','#346492')]:
        axes[0].plot(days, context[name], label=label, color=color, marker='.', ms=4)
    axes[0].set_ylabel('Daily mean\nµg/m³'); axes[0].legend(loc='upper left', ncol=2)
    axes[0].set_title('Anand Vihar, Delhi: provisional monitor observations',loc='left',fontsize=12)
    axes[1].plot(days, context.wind_speed, color='#007f79', marker='.', ms=4)
    axes[1].set_ylabel('Station wind\nm/s')
    axes[1].set_title('Measured station weather; regional boundary-layer height unavailable',loc='left',fontsize=11)
    for index, (satellite, group) in enumerate(fire.groupby('satellite')):
        offset=pd.Timedelta(hours=-5 if index==0 else 5)
        axes[2].bar(group.local_date+offset, group.detections, width=0.38,
                    label=satellite, color=['#6950a1','#b58dce'][index])
    axes[2].set_ylabel('VIIRS detections\nnominal / high confidence')
    axes[2].legend(loc='upper left', ncol=2)
    axes[2].set_title('Cross-border regional box: 72–79°E, 27–33°N; separate satellite counts',loc='left',fontsize=11)
    history=dss[dss.evidence_kind.eq('published_model_daily_history')].set_index('valid_date').reindex(days)
    axes[3].plot(days,history.percent_total_pm25,color='#626262',marker='.',label='Published daily model history')
    forecast=dss[dss.evidence_kind.eq('published_model_forecast') & dss.source_category.eq('Stubble Burning') & (dss.valid_date<=days[-1])]
    axes[3].plot(forecast.valid_date,forecast.percent_total_pm25,color='#8c3180',ls='--',marker='o',label='Published forecast (issue time unknown)')
    axes[3].set_ylabel('IITM stubble estimate\n% of modeled PM2.5')
    axes[3].legend(loc='upper left',ncol=2,fontsize=9)
    for ax in axes:
        ax.grid(axis='y',alpha=0.18);ax.set_ylim(bottom=0)
        ax.set_xlim(days[0]-pd.Timedelta(hours=12),days[-1]+pd.Timedelta(hours=12))
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=7))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    axes[-1].set_xlabel('2026 date: observations in Asia/Kolkata; IITM labels as published; cutoff 8 November')
    fig.suptitle('Delhi episode context: measured, detected and modeled evidence',x=.08,ha='left',fontsize=16)
    fig.text(.08,.025,'Monitor / weather means require ≥18 valid hours; gaps remain missing. FIRMS rolling feed has partial boundary days.\n'
             'Detections are not unique fires or crop-burning attribution. IITM forecast categories total >100%; no rescaling or causal inference.\n'
             'Sources: CPCB via OpenAQ; NASA FIRMS NOAA-20/21 VIIRS C2 NRT; IITM DSS. Snapshot: 8 November 2026.',fontsize=9)
    fig.subplots_adjust(left=.12,right=.97,bottom=.15,top=.91,hspace=.43)
    for suffix in ['png','pdf']:
        fig.savefig(output/f'delhi-episode-context.{suffix}',dpi=180)
    plt.close(fig)

    model=np.load(root/'model/longpmind-2022-grid.npz')
    coast=gpd.read_file(ROOT/'assets.static/natural-earth/10m-physical-vectors/ne_10m_coastline.shp',bbox=(65,5,99,38))
    fig,axes=plt.subplots(1,2,figsize=(11.5,7.2),sharex=True,sharey=True)
    for ax,parameter,title in zip(axes,['pm25','pm10'],['PM2.5','PM10']):
        mesh=ax.pcolormesh(model['lon'],model['lat'],model[parameter],shading='nearest',
                           cmap='YlOrBr',vmin=0,vmax=210,rasterized=True)
        coast.plot(ax=ax,color='#888888',linewidth=.35)
        ax.set_xlim(65,99);ax.set_ylim(5,38);ax.set_aspect(1/np.cos(np.deg2rad(23)))
        ax.set_title(title,loc='left',fontsize=14);ax.set_xlabel('Longitude (°E)')
    axes[0].set_ylabel('Latitude (°N)')
    fig.suptitle('LongPMInd v2: modeled annual particulate concentrations, 2022',x=.06,ha='left',fontsize=15)
    fig.subplots_adjust(left=.07,right=.87,bottom=.18,top=.89,wspace=.12)
    bar=fig.colorbar(mesh,cax=fig.add_axes([.90,.24,.018,.55]))
    bar.set_label('Modeled annual mean (µg/m³)')
    fig.text(.06,.04,'Native nominal 10 km grid; calendar-day-weighted monthly means require 12 finite, nonnegative months.\n'
             '22 negative PM10 cell-months are masked and audited. Blank cells are missing; no 2025/2026 observation gap filling.\n'
             'Source: LongPMInd v2, DOI 10.5281/zenodo.14557027 (CC BY 4.0). Coastline: Natural Earth.\n'
             'Concentration units are documented in the paper; the NetCDF pollutant variables omit a units attribute. Independent validation is pending.',fontsize=9)
    for suffix in ['png','pdf']:
        fig.savefig(output/f'longpmind-2022-model.{suffix}',dpi=180)
    plt.close(fig)
    print('Saved scientific review figures:',output)


if __name__=='__main__':
    main()
