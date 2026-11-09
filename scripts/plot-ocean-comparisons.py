#!/usr/bin/env python3
"""Standalone seasonal comparison figure, computed from the paired-day ledger."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ocean_temperature import digest, write_json

from viz_context import ocean_output, cutoff
ROOT=ocean_output()


def main():
    source=ROOT/'data/matched-comparison.json'
    rows=json.loads(source.read_text())['regions']
    selected=[rows[i] for i in (0,1,2,3,4)]
    labels=['Global sample','Japan region','Northern Hemisphere','Southern Hemisphere','Tropics']
    colors=['#f2b94e','#66c2a5','#8da0cb','#e78ac3','#d9c98b']
    plt.rcParams.update({'font.size':11,'svg.fonttype':'none','savefig.facecolor':'#240413',
                         'text.color':'#fff6e3','axes.labelcolor':'#fff6e3','xtick.color':'#fff6e3','ytick.color':'#fff6e3'})
    fig,(left,right)=plt.subplots(1,2,figsize=(15,6.4),facecolor='#240413')
    for ax in (left,right):
        ax.set_facecolor('#240413');ax.grid(axis='y',alpha=.18,color='#fff6e3')
        for spine in ax.spines.values():spine.set_color('#9e8994')
        months=[m['month'] for m in selected[0]['months']]
        ax.set_xticks(months,[__import__('calendar').month_abbr[m] for m in months])
        ax.tick_params(axis='x',labelsize=9);ax.set_xlim(.7,max(months)+.3)
        ax.axvspan(max(months)-.4,max(months)+.3,color='#fff6e3',alpha=.07)
    changes=[]
    for row,label,color in zip(selected,labels,colors):
        months=row['months'];x=[m['month'] for m in months]
        left.plot(x,[m['sst_2026_degC'] for m in months],color=color,marker='o',markersize=4,label=label)
        right.plot(x,[m['difference_2026_minus_2025_degC'] for m in months],color=color,marker='o',markersize=4)
        full=[m for m in months if m['days']==__import__('calendar').monthrange(2026,m['month'])[1] and m['sst_2026_degC'] is not None and m['difference_2026_minus_2025_degC'] is not None]
        changes.append({'region':row['region'],'warmest_complete_2026_month':max(full,key=lambda m:m['sst_2026_degC'])['month'] if full else None,
                        'largest_absolute_paired_difference_complete_month':max(full,key=lambda m:abs(m['difference_2026_minus_2025_degC']))['month'] if full else None})
    right.axhline(0,color='#fff6e3',alpha=.8,linewidth=.8)
    left.set_title('2026 monthly SST on paired support',loc='left',color='#fcc553')
    right.set_title('Same-period difference: 2026 minus 2025',loc='left',color='#fcc553')
    left.set_ylabel('Sea-surface temperature (°C)');right.set_ylabel('Difference (°C)')
    legend=fig.legend(*left.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.52,.11),ncol=5,
                      fontsize=9,frameon=False)
    for text in legend.get_texts():text.set_color('#fff6e3')
    fig.suptitle('Ocean seasons differ by region',x=.07,ha='left',fontsize=19,color='#fcc553')
    fig.text(.07,.08,'NOAA OISST • H3r5 native-center aggregation • identical valid cell-days within each monthly year-pair • area-approximate weights',fontsize=10)
    fig.text(.07,.045,f'Calendar window ends {cutoff()}. Monthly cohorts can differ. These two years do not establish a climate trend.',fontsize=10)
    fig.subplots_adjust(left=.07,right=.98,top=.86,bottom=.23,wspace=.22)
    out=ROOT/'figures';out.mkdir(parents=True,exist_ok=True)
    for extension in ('png','svg','pdf'):fig.savefig(out/f'monthly-paired-comparison.{extension}',dpi=180)
    plt.close(fig)
    write_json(out/'monthly-paired-comparison.json',{'source':str(source.relative_to(ROOT)),'source_sha256':digest(source),
               'seasonal_rankings':changes,'outputs':{p.name:digest(p) for p in out.glob('monthly-paired-comparison.*') if p.suffix!='.json'}})
    print('Seasonal figure saved with source digest and actual calendar cutoff')


if __name__=='__main__':main()
