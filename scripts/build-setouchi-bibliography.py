#!/usr/bin/env python3
"""Build the 38-pair source bibliography from the inputs actually used by Setouchi."""
import argparse
from functools import lru_cache
from html import escape
import json
import math
from pathlib import Path
import re

from legend_informatics import ROOT, SUFFIX, digest, register_fonts


@lru_cache(maxsize=None)
def asset(path):
    path=Path(path).resolve()
    label=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return {'path':label,'sha256':digest(path),'bytes':path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def build(delivery, revision):
    data=delivery/'sources/data'; registry={}

    def source(identifier,title,url,period,notes='',license_note='',files=(),**extra):
        registry[identifier]={'id':identifier,'title':title,'url':url,'period':period,'notes':notes,
                              'license':license_note,'inputs':[asset(p) for p in files],**extra}
        return identifier

    source('authagraph','Hajime Narukawa — AuthaGraph formulation','https://doi.org/10.11212/jjca.60.1_1',
           '2022 formulation; native Cartofreako implementation',
           'Projection and graticules are mathematical constructions. Horizontal periodicity supports the ST2 framing study.',
           files=[ROOT/'src.projections/cart0freak0-authagraph.h'])
    physical=ROOT/'assets.static/natural-earth/10m-physical-vectors'
    source('natural-earth-physical','Natural Earth — 1:10m physical vectors',
           'https://www.naturalearthdata.com/downloads/10m-physical-vectors/',
           'Pinned local vectors used by the 29 October 2026 delivery; not new observations',
           'Land, coastline, minor islands, lakes, rivers, ice and generalized bathymetry. Individual version files and component hashes are in the JSON ledger.',
           'Public domain',files=sorted(p for p in physical.iterdir() if p.suffix in ('.shp','.dbf','.shx','.prj') or p.name.endswith('.VERSION.txt')))
    source('japan-boundary','Natural Earth — Japan geographic boundary',
           'https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/',
           '1:10m boundary extracted for the 29 October 2026 delivery',
           'Defines the Japan/Setouchi viewport. It does not turn national statistics into island-level measurements.',
           'Public domain',files=[delivery/'sources/japan-boundary.geojson',delivery/'sources/japan-view.json'])
    resources=read(data/'resources/resources-profile.json')
    for record in resources['sources']:
        if record.get('sha256')=='not-yet-ingested':continue
        source(record['id'],record['organization']+' — '+record['title'],record['url'],
               record['release']+'; retrieved '+record['retrieved_at'],license_note=record['license'],
               files=[data/'resources/resources-profile.json'],upstream_sha256=record['sha256'])
    atmosphere=read(data/'cloud-atmosphere/cloud-atmosphere-profile.json')
    dates={'jaxa-ptree-cloud':'29 October 2026, 18:20 UTC', 'jaxa-gcom-c-aod':'15 October 2026, 00:00 UTC',
           'jaxa-gsmap-precipitation':'26 October 2026, 23:00 UTC', 'jaxa-jasmes-swr':'15 October 2026, 23:59 UTC'}
    for record in atmosphere['sources']:
        source(record['id'],record['title'],record['url'],dates[record['id']],record['coverage'],
               'Provider attribution and reuse conditions: '+record['license_url'],
               files=[data/'cloud-atmosphere/cloud-atmosphere-profile.json'],collection=record['collection'])
    cdn_config=read(ROOT/'config/cdn-sources.json')
    cdn_manifest=(ROOT/'config'/cdn_config['manifest']).resolve()
    cdn=read(cdn_manifest)
    cdn_urls=[]
    for layer in cdn['layers']:
        for record in layer.get('sources',[]):
            if record.get('source_url'):
                cdn_urls.append({'layer':layer['layer'],'url':record['source_url'],
                                 'retrieved_at':layer.get('retrieved_at',[]),
                                 'sha256':record.get('source_sha256',record.get('sha256'))})
    source('cdn-cache','Cloud/CDN source cache and Alpha60 reference registries',
           'https://github.com/bdekoz/cloud_cdn_cache.bkoz',
           'Manifest 21 October 2026; source revision '+cdn_config['source_revision'],
           'Canonical provider layers are distinct from derived city/area references and separate locality claims. '
           '28,243 records: 13,140 source coordinates, 1,405 reference placements, 13,698 unplotted; 80 independent claims.',
           'Individual provider/source terms apply; cache membership is not a new blanket license.',
           files=[cdn_manifest,ROOT/'config/cdn-sources.json',delivery/'sources/cdn-refresh.json'],references=cdn_urls)
    fiber=ROOT/'assets.static/fiber-synthesized'
    source('telegeography','TeleGeography — Submarine Cable Map snapshots',
           'https://github.com/telegeography/www.submarinecablemap.com',
           '2022 and 5 August 2026 snapshots',
           '767 route features: 718 current and 49 unmatched 2022 features; 2,037 cleaned-union landings. '
           'Snapshot-only status does not establish construction or decommission.',
           'CC BY-NC-SA 3.0 Unported',files=[fiber/'manifest.json',fiber/'routes.geojson',fiber/'landings.geojson'])
    itu=read(fiber/'itu/provenance.json')
    source('itu','International Telecommunication Union — public terrestrial fibre',itu['source_page'],
           itu['retrieved_at_utc'],'37,397 anonymous public WFS features: 35,212 operational, 639 under construction, '
           '1,248 planned and 298 proposed. Microwave and restricted layers excluded; routes are schematic.',
           'ITU public BBmaps source terms; no new redistribution license inferred.',
           files=[fiber/'itu/provenance.json'],query_url=itu['url'],upstream_sha256=itu['sha256'])
    ground=ROOT/'assets.static/network-groundstations'
    source('groundstations','Alpha60 data — Starlink gateways and points of presence',
           'https://github.com/bdekoz/alpha60-data/tree/2e0493073b01742bdd4dff9ace7126f5a97111a9',
           '2 September 2025; 618 source records','Location does not prove current operation.',
           'See the source alpha60-data README; public access is not a new license.',
           files=[ground/'network-groundstations-profile.json',ground/'starlink-global-gateways-pops.20250902.json'])
    swarm=read(delivery/'sources/swarm-refresh.json')
    source('alpha60-swarm','Alpha60 — Dan Da Dan 210 cumulative sample cache',
           'https://github.com/bdekoz/alpha60/blob/'+swarm['source_revision']+'/src/a60-carto-geo.cc',
           '4 September 2025–4 March 2026; cache.20260304.tar.xz',
           'Episodes 210/211/212. Native weighted circles and per-member colors, 5% opacity. '
           'Repeated downloader observations are not unique people or traffic volume. Raw participant files are excluded from this delivery.',
           'Local research cache; bibliography identifies the aggregate input without republishing raw observations.',
           files=[delivery/'sources/swarm-refresh.json',delivery/'sources/swarm-cache-extraction.json'],
           upstream_sha256=swarm['cache_archive']['sha256'])
    source('ipinfo','IPinfo — Standard Location geolocation database','https://ipinfo.io/products/ip-geolocation-database',
           'Local database pinned by SHA-256 in swarm-refresh.json',
           'IP-derived locations are approximate; the database snapshot is not a survey of participants.',
           'Provider/database terms apply; database not redistributed.',upstream_sha256=swarm['geolocation_database']['sha256'])
    for year in (2025,2026):
        profile=read(data/f'anthropocene/anthropocene-particulate-{year}-profile.json')
        titles={'noaa-ghcn-gsn':'NOAA/NCEI — GHCN Daily, Global Surface Network stations',
                'epa-airdata-pm25':'US EPA — AirData PM2.5 AQI',
                'noaa-hms-smoke':'NOAA — Hazard Mapping System smoke polygons',
                'noaa-storm-events':'NOAA/NCEI — Storm Events Database',
                'cwfis-hotspots':'Natural Resources Canada — Canadian Wildland Fire Information System',
                'jp-moe-soramame':'Japan Ministry of the Environment — Soramame provisional PM2.5',
                'cnemc-quotsoft':'China CNEMC — PM2.5 via Wang Xiaolei / Quotsoft',
                'openaq-cpcb':'India CPCB — selected PM2.5 monitors via OpenAQ',
                'openaq-airnow':'AirNow — selected Indian PM2.5 monitors via OpenAQ',
                'openaq-airgradient':'AirGradient — Srinagar sensor via OpenAQ'}
        for record in profile['sources']:
            if record['status']!='included':continue
            source(record['id']+'-'+str(year),titles[record['id']],record['url'],
                   'Available through '+record['available_through'],
                   record['coverage']+'. Source-specific cutoff; no inference of absence beyond coverage.',
                   'CC BY 4.0; AirGradient attribution.' if record['id']=='openaq-airgradient' else 'Source/provider-specific terms retained in the particulate source documentation.',
                   files=[data/f'anthropocene/anthropocene-particulate-{year}-profile.json'])
    source('noaa-cpc','NOAA CPC / NOAA PSL — Global Unified Temperature V1.0',
           'https://psl.noaa.gov/data/gridded/data.cpc.globaltemp.html',
           '2025 complete; 2026 through 28 October',
           '0.5° land TMAX/TMIN analysis aggregated to H3 resolution 3. Same-calendar-day strict records with at least 30 valid history years.',
           'No usage restrictions; NOAA PSL acknowledgment requested.',
           files=[data/f'anthropocene/anthropocene-temperature-{year}-profile.json' for year in (2025,2026)]+
                 [delivery/'sources/temperature-classification.json',delivery/'sources/temperature-refresh.json'])
    astronomy=data/'astronomy'
    source('gaia','ESA — Gaia DR3 bright-star selection','https://gea.esac.esa.int/tap-server/tap/sync',
           'Retrieved 29 October 2026; Gaia DR3',
           'ADQL: TOP 500 sources with phot_g_mean_mag < 5.5, ordered by magnitude. A bounded catalogue selection, not all stars.',
           'Retain ESA/Gaia/DPAC acknowledgments.',files=[astronomy/'gaia-dr3-bright.csv',ROOT/'scripts/fetch-astro-data.sh'])
    source('exoplanets','NASA Exoplanet Archive — nearby host selection','https://exoplanetarchive.ipac.caltech.edu/TAP/sync',
           'Retrieved 29 October 2026','TOP 250 pscomppars entries with RA/Dec, ordered by system distance. Host positions, not resolved planet surfaces.',
           'NASA Exoplanet Archive acknowledgment.',files=[astronomy/'nasa-exoplanet-nearby.csv'])
    source('jpl-sbdb','NASA/JPL — Small-Body Database','https://ssd-api.jpl.nasa.gov/sbdb.api',
           'Retrieved 29 October 2026; evaluated 29 October 2026 at 20:00 UTC',
           'Ceres, Vesta, Eros, Apophis, Halley, Encke and 67P. Approximate two-body propagation; not a mission-navigation ephemeris.',
           'NASA/JPL source acknowledgment.',files=sorted(astronomy.glob('sbdb-*.json')))
    curated=read(astronomy/'curated-sky.json')
    curated_urls=sorted(set(o['source_url'] for o in curated.get('objects',[]) if o.get('source_url')))
    source('curated-sky','Cartofreako — curated multi-band and transient context','https://heasarc.gsfc.nasa.gov/',
           'Pinned curated entries retained; individual dates and roles remain in curated-sky.json',
           'Curated positions and mission context are not a new transient survey. Discovery/context-only source links do not imply ingested measurements.',
           'Retain each underlying provider acknowledgment.',files=[astronomy/'curated-sky.json'],
           references=[{'layer':'curated object source','url':url} for url in curated_urls])
    orbital=read(data/'orbital-technosphere/orbital-technosphere-profile.json')
    catalogs=[orbital['catalogs']['primary'],*orbital['catalogs']['groups']]
    source('celestrak','CelesTrak — general perturbations orbital element groups',
           'https://celestrak.org/NORAD/elements/',
           '16 CSV groups retrieved 29 October 2026; SGP4 evaluated at 20:00 UTC that day',
           'Active, Starlink, OneWeb, Kuiper, Qianfan, Hulianwang, GNSS, Iridium NEXT, Globalstar, ORBCOMM, resource, science, '
           'stations and three debris groups. Native seven-day age and six-hour future-epoch filters remain.',
           'CelesTrak source attribution and terms apply.',
           files=[data/'orbital-technosphere'/c['file'] for c in catalogs],
           references=[{'layer':c['id'],'url':c['source_url']} for c in catalogs])
    source('nasa-ssc-reference','NASA SSCWeb — retained validation reference',
           orbital['catalogs']['nasa_ssc_reference']['source_url'],
           'Historical 13 August 2026 reference; 29 October refresh timed out',
           'Validation context only. It did not replace the newly retrieved CelesTrak orbital elements and is not a separate plotted live feed.',
           'NASA acknowledgment.',files=[data/'orbital-technosphere/nasa-ssc-reference.json'])
    petroleum=ROOT/'assets.static/petroleum'
    source('eia-steo','US EIA — Short-Term Energy Outlook, tables 3b and 3c',
           'https://www.eia.gov/outlooks/steo/data.php?type=tables','October 2026 release; 2025 annual historical/estimated liquids production',
           '36 countries, including Russia, Brazil, Canada, Venezuela, Mexico and the USA. Total liquids include NGLs, other liquids and processing gain; not crude-only output.',
           'US EIA source acknowledgment.',files=[petroleum/'eia-usa'/f'steo-2026-10-table{t}.pdf' for t in ('3b','3c')]+[petroleum/'normalized/eia-series.csv'])
    source('opec-woo','OPEC — World Oil Outlook 2026','https://publications.opec.org/woo','2026 outlook; user-supplied report and 14 workbooks',
           'All 202 worksheets and 17,920 nonempty cells retained. Register: 209 countries/territories; 17 with separately indexed numeric cells; '
           '14 with suitable total-liquids series. This is World Oil Outlook, not the Annual Statistical Bulletin. Regional totals are not allocated to countries.',
           'OPEC publication/account terms; final exhibition excerpt and attribution review remains open.',
           files=[petroleum/'opec/woo-2026.pdf',*sorted((petroleum/'opec/data').glob('*.xlsx')),
                  petroleum/'normalized/opec-liquids-supply.csv',petroleum/'normalized/opec-country-coverage.csv'])

    plan=read(delivery/'sources/generation-plan.json')['plates']
    legend={r['stem']:r for r in read(revision/'sources/legend-catalog.json')}
    changes=read(revision/'sources/legend-revision.json')['records']
    values=read(data/'resources/resources-values.json')['records']
    coverage=read(data/'anthropocene/pm25-enrichment-quality.json')['country_coverage']
    sheets_path=revision/'sources/separate-sheets.json'
    sheets=read(sheets_path)['records'] if sheets_path.exists() else []
    entries=[]
    for ordinal,item in enumerate(plan,1):
        stem=item['stem'];m=legend[stem]
        entry={'ordinal':ordinal,'stem':stem,'title':item['title'],'period_and_units':m['units'],
               'interpretation':item['note'],'source_ids':['authagraph'],'method':m['method'],
               'japan':'Same evidence in the Japan/Setouchi geographic viewport; neighboring countries may appear. No island-level value is inferred.',
               'inputs':[], 'key':[{'label':k['label'],'original_label':k['original_label']} for k in m['keys']],
               'plate_inputs':[r for r in changes if r['stem']==stem]}
        if stem in ('geometry','graticules'):
            entry['period_and_units']='Mathematical construction; no observational period'
            entry['japan']='AuthaGraph geographic reference frame around Japan; not observational data.'
        else:entry['source_ids'].append('natural-earth-physical')
        if 'metric' in m:
            metric=m['metric'];entry['source_ids']=['authagraph','natural-earth-admin0',*metric['source_ids']]
            rows=[r for r in values if r['family']==m['family'] and r['metric']==metric['id']]
            vals=[r['value'] for r in rows];lo,hi=min(vals),max(vals)
            if metric['id']=='solar-capacity':
                entry['class_definition']={'method':'fixed MW boundaries','boundaries':[0,100,1000,10000,50000,200000],
                                           'intervals':'Lower inclusive, upper exclusive; final class ≥200,000 MW.'}
            else:
                cuts=[math.expm1(math.log1p(lo)+i/5*(math.log1p(hi)-math.log1p(lo))) if metric['scale']=='log1p'
                      else lo+i/5*(hi-lo) for i in range(6)]
                cuts[0]=lo;cuts[-1]=hi
                entry['class_definition']={'method':'five equal intervals of '+('log(1 + value)' if metric['scale']=='log1p' else 'value'),
                                           'boundaries':cuts,'minimum':lo,'maximum':hi,
                                           'formula':('u=(log1p(value)-log1p(minimum))/(log1p(maximum)-log1p(minimum))' if metric['scale']=='log1p' else 'u=(value-minimum)/(maximum-minimum)')+'; class=min(4,floor(5*u))',
                                           'intervals':'Lower inclusive, upper exclusive; the last interval includes the maximum. Legend labels are rounded.'}
            row=next((r for r in rows if r['iso3']=='JPN'),None)
            entry['japan']+=' '+('Japan value: '+str(row['value'])+' '+metric['unit']+' ('+str(row['year'])+').' if row else 'Japan has no reported country value; missing is not zero.')
            entry['coverage']=metric['coverage'];entry['inputs']=[asset(data/'resources/resources-values.json')]
        elif stem=='resources-fauna-coral-reef-threat-2011':
            entry['source_ids']+=['wri-reefs-at-risk-2011']
            entry['method']='Highest local threat among source polygons in each 0.25° cell; 7,215 occupied cells grouped into 844 radial honeycombs. One microhex per cell, display capped at 61 per group; four class composition retained.'
            entry['class_definition']={'method':'WRI source categories','categories':['Low','Medium','High','Very high'],'intervals':'Historical threat ranks, not current coral cover or reef area.'}
            entry['inputs']=[asset(data/'resources/coral-reefs-025deg.geojson')]
        elif stem=='cloud-atmosphere':
            entry['source_ids']+=[r['id'] for r in atmosphere['sources']]
            entry['method']='H3 resolution 3; per-layer quality masks and valid-sample threshold retained. Source times differ. Solar geometry is calculated at 29 October 2026, 20:00 UTC. Land fill opacity zero, outlines above data.'
            entry['japan']+=' The nighttime snapshot contains no positive daytime cloud retrievals; missing cloud is not clear sky.'
            entry['inputs']=[asset(data/'cloud-atmosphere/.prepared/cloud-atmosphere-latest.geojson')]
        elif stem=='network-cdn':entry['source_ids']+=['cdn-cache']
        elif stem=='network-fiber':entry['source_ids']+=['telegeography','itu']
        elif stem=='network-groundstations':entry['source_ids']+=['groundstations']
        elif stem.startswith('network-swarm-'):
            entry['source_ids']+=['alpha60-swarm','ipinfo']
            entry['japan']+=' Physical circle areas match the world scale. The 1080p/4K and 720p/lower-resolution partitions are separate plates.'
        elif stem.startswith('anthropocene-particulate'):
            year=int(stem[-4:]);profile=read(data/f'anthropocene/anthropocene-particulate-{year}-profile.json')
            entry['source_ids'] += [r['id']+'-'+str(year) for r in profile['sources'] if r['status']=='included']
            entry['method']='H3 resolution 4, source-separated unique reporting days. Monitor daily means require ≥18 distinct valid hours; concentration >35 µg/m³ is distinct from EPA AQI >100. Missing dates are not zero; low-cost AirGradient sensor days remain separate.'
            entry['coverage']=[r for r in coverage if r['year']==year]
            entry['japan']+=' Japan observations cover '+('November–December 2025' if year==2025 else 'January–September 2026')+'. Provisional 999x status codes are excluded. Extreme reported daily means remain in the operator-review ledger.'
            entry['inputs']=[asset(data/f'anthropocene/anthropocene-particulate-{year}.geojson'),asset(data/'anthropocene/pm25-enrichment-quality.json')]
            entry['excluded_sources']='PurpleAir, IQAir, WAQI and optional FIRMS are not claimed as newly ingested data. China uses a 2022 coordinate inventory; India is a selected 16-monitor/14-city sample plus one separate sensor.'
        elif stem.startswith('anthropocene-temperature'):
            year=int(stem[-4:]);entry['source_ids']+=['noaa-cpc']
            entry['method']=f'11,945 H3 resolution 3 land cells. Strict same-calendar-day maximum and minimum records against 1979–{year-1}, with ≥30 valid history years. 2026 is partial; counts are not a year-on-year warming estimate.'
            entry['class_definition']={'method':'new daily high count','categories':['1–5','6–10','11–20','21–40','41–80','≥81'],
                                       'intervals':'Neutral covered land: zero; blank: unobserved. Blue outlines encode record-low counts separately.'}
            entry['inputs']=[asset(Path(item['command'][-1]))]
        elif stem.startswith('astro-'):
            entry['source_ids']=['authagraph','gaia','exoplanets','jpl-sbdb','curated-sky']
            if stem=='astro-observer-hubble':entry['source_ids'].append('celestrak')
            entry['period_and_units']='Celestial directions / calculation at 29 October 2026, 20:00 UTC'
            entry['japan']=('Ground observer recalculated for Setouchi, 34.45°N 133.99°E, instead of San Francisco. ' if stem=='astro-observer-ground-multiband' else 'All-sky/Hubble sky context retained; a geographic Japan crop is undefined. ')+ 'Companion includes a geographic locator; the yellow reference is conceptual, not a confirmed venue.'
            entry['inputs']=[asset(astronomy/('astro-hubble-profile.json' if stem.endswith('hubble') else 'astro-profile.json')),asset(astronomy/'astro-setouchi-profile.json')]
        elif stem.startswith('orbital-'):
            entry['source_ids']+=['celestrak']
            entry['supporting_source_ids']=['nasa-ssc-reference']
            entry['period_and_units']='SGP4 positions / 29 October 2026, 20:00 UTC'
            if stem.endswith('observer'):entry['japan']='Celestial directions calculated from Setouchi, 34.45°N 133.99°E, with a geographic locator; not a geographic crop or observed satellite photograph.'
            entry['inputs']=[asset(data/'orbital-technosphere/orbital-technosphere-profile.json'),asset(data/'orbital-technosphere/orbital-setouchi-profile.json')]
        elif stem.startswith('petroleum-'):
            entry['source_ids']=['authagraph','natural-earth-admin0','eia-steo' if 'eia-' in stem else 'opec-woo']
            if 'coverage' in stem:
                entry['class_definition']={'method':'source coverage','categories':['country figures indexed','registered, no separate figure','not matched to report register'],
                                           'intervals':'These are provenance categories, not production amounts.'}
            else:
                entry['class_definition']={'method':'fixed million-barrels/day thresholds','boundaries':[.1,.5,1,2,5,10,25],
                                           'intervals':'First ≤0.1; subsequent lower exclusive, upper inclusive. Values above 25 would be clamped into the last class; no current mapped value exceeds 25.'}
            entry['inputs']=[asset(petroleum/'normalized'/('eia-series.csv' if 'eia-' in stem else 'opec-country-coverage.csv' if 'coverage' in stem else 'opec-liquids-supply.csv'))]
            entry['excluded_sources']='ANP Brazil, Statistics Canada and US national corroboration are supporting research, not substituted into these country fills. Austrian WKO and Energy Institute numerical data were not ingested.'
        entry['japan_source_ids']=['japan-boundary']
        entry['presentation']='Separate map and legend/source sheets. Maps use a centered 43.5-inch image on the 44-inch sheet (98.863636% proportional scale); legend typography retains its declared physical sizes.'
        entry['world_presentation']='Every world sheet uses the same horizontal cyclic move of +4.35 printed inches. Where terrestrial geography is present, Antarctica, its coastlines, ice and attached country fills share the approved lower-left translation. This position is editorial, not geographically accurate. Network, climate, orbital and celestial observations retain their source coordinates within the shifted frame. Japan detail framing is retained.'
        if stem in ('earth','water','bathymetry-roulette','bathymetry-hamonshu'):
            entry['world_presentation']+=' Ocean-colored editorial backing closes the former Antarctic land void; that backing is not a new bathymetric measurement. Existing subsea contours retain their source coordinates.'
        if stem=='network-fiber':
            entry['presentation']+=' Map route strokes become 0.494318 pt after reduction; opacity remains 75%.'
        entry['separate_sheets']=[r for r in sheets if r['stem']==stem]
        entries.append(entry)
    assert len(entries)==38
    for entry in entries:
        for identifier in entry['source_ids']+entry['japan_source_ids']+entry.get('supporting_source_ids',[]):
            if identifier not in registry:raise ValueError('Unresolved source: '+identifier)
    return {'schema':'setouchi-plate-bibliography-v1','edition':'Setouchi Triennale 2028 — ST2',
            'prepared_on':'2026-10-30','source_delivery':str(delivery.relative_to(ROOT)),
            'note':'Documents the snapshots actually drawn; this legend/framing revision does not refresh observational data.',
            'entries':entries,'sources':registry}


def paragraphs(entry,registry):
    rows=[('Period and units',entry['period_and_units'] or 'See individual source periods.'),
          ('Meaning',entry['interpretation']),('Method',entry['method'] or 'Native AuthaGraph geometry.'),
          ('Japan companion',entry['japan'])]
    if entry.get('class_definition'):
        c=entry['class_definition'];description=c['method']+'. '
        if c.get('boundaries'):description+='Boundaries: '+', '.join(format(x,'.12g') for x in c['boundaries'])+'. '
        if c.get('categories'):
            description+='Classes: '+', '.join(c['categories'])+'. '
        description+=c['intervals'];rows.append(('Key definitions',description))
    if isinstance(entry.get('coverage'),list):
        rows.append(('Measured coverage','; '.join(f"{r['country']} / {r['instrument_class']}: {r['stations']:,} stations, {r['h3_cells']} cells, {r['first_date']}–{r['last_date']}" for r in entry['coverage'])+'.'))
    elif entry.get('coverage'):
        c=entry['coverage'];rows.append(('Coverage',f"{c['covered_countries']} of {c['mapped_countries']} mapped country geometries."))
    if entry.get('excluded_sources'):rows.append(('Scope',entry['excluded_sources']))
    rows.append(('Presentation',entry['presentation']))
    if entry.get('world_presentation'):rows.append(('World framing',entry['world_presentation']))
    return rows


def write_outputs(book,output,docs_page):
    register_fonts();output.mkdir(parents=True,exist_ok=True)
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
    styles={name:ParagraphStyle(name,fontName='Atkinson-'+role,fontSize=size,leading=leading,
                                spaceAfter=space,textColor=colors.HexColor('#272523'),keepWithNext=keep)
            for name,role,size,leading,space,keep in [('title','Bold',24,28,18,True),('h1','Bold',16,20,10,True),
                ('h2','Bold',12,15,8,True),('body','Regular',9.3,13,8,False),('small','Regular',8,11,6,False)]}
    def para(value,style='body'):return Paragraph(value,styles[style])
    intro='Sources for all 38 world/Japan pairs. Plate numbers match the revised legend footers. This bibliography identifies the snapshots actually drawn; a new render does not make dated observations current. Full file paths and SHA-256 hashes are in the accompanying JSON ledger.'
    pdf=[para('Setouchi Triennale 2028','title'),para('Data plate bibliography · ST2','h1'),para(escape(intro)),
         para('Prepared 30 October 2026. Country statistics use national geometries; the Japan detail does not infer local values. Missing data are not zero. Exact formulas and full-precision boundaries are retained in the JSON ledger; printed legend labels are rounded.')]
    md=['---','layout: default','title: Setouchi 2028 plate bibliography','---','','# Setouchi 2028 plate bibliography','',intro,'',
        '[Review guide](setouchi-2028.md) · [Particulate source detail](../data/anthropocene-particulate.md)','','## Plate index','']
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
          '<title>Setouchi 2028 data plate bibliography</title><style>body{font:18px/1.5 system-ui;color:#292722;max-width:1000px;margin:2rem auto;padding:0 1rem}a{color:#503b75}h1,h2,h3{line-height:1.15}article{border-top:1px solid #ccc;padding:1rem 0}code{overflow-wrap:anywhere;font-size:.85em}li{margin:.4rem 0}nav{columns:2}p{overflow-wrap:anywhere}small{color:#555}@media(max-width:650px){nav{columns:1}}@media print{nav{display:none}article{break-inside:avoid}body{font-size:10pt}}</style>',
          '<h1>Setouchi 2028<br>Data plate bibliography</h1><p>'+escape(intro)+'</p><p><a href="plate-source-bibliography.pdf">PDF</a> · <a href="plate-source-bibliography.json">Source ledger and hashes</a> · <a href="index.html">Plate review</a></p><nav><ol>']
    for e in book['entries']:
        anchor=f"plate-{e['ordinal']:02d}";title=f"{e['ordinal']:02d} · {e['title']}"
        md.append(f"- [{title}](#{anchor})")
        html.append(f'<li><a href="#{anchor}">{escape(e["title"])}</a></li>')
    html.append('</ol></nav>')
    for e in book['entries']:
        anchor=f"plate-{e['ordinal']:02d}";title=f"{e['ordinal']:02d} · {e['title']}"
        pdf += [Spacer(1,10),para(escape(title),'h1')]
        md += ['',f'<a id="{anchor}"></a>','',f'## {title}','',f'`{e["stem"]}`','']
        html += [f'<article id="{anchor}"><h2>{escape(title)}</h2><code>{escape(e["stem"])}</code>']
        for label,value in paragraphs(e,book['sources']):
            pdf.append(para('<b>'+escape(label)+':</b> '+escape(value)))
            md += [f'**{label}:** {value}','']
            html.append(f'<p><strong>{escape(label)}:</strong> {escape(value)}</p>')
        ids=list(dict.fromkeys(e['source_ids']+e['japan_source_ids']))
        links=[]
        for identifier in ids:
            s=book['sources'][identifier]
            links.append(f'<link href="{escape(s["url"],quote=True)}" color="#503b75">{escape(s["title"])}</link> [{escape(identifier)}]')
        pdf.append(para('<b>Sources:</b> '+'; '.join(links)+'.','small'))
        md += ['**Sources:** '+ '; '.join(f'[{book["sources"][i]["title"]}]({book["sources"][i]["url"]}) ([record](#source-{i}))' for i in ids)+'.','']
        html.append('<p><strong>Sources:</strong> '+'; '.join(f'<a href="#source-{i}">{escape(book["sources"][i]["title"])}</a>' for i in ids)+'.</p></article>')
        if e.get('supporting_source_ids'):
            label='Validation-only context: '+', '.join(book['sources'][i]['title'] for i in e['supporting_source_ids'])+'. Historical NASA reference retained after timeout; not live plotted observations.'
            md += [label,''];pdf.append(para(escape(label),'small'))
    pdf += [PageBreak(),para('Source records','title')]
    md += ['','## Source records','','The JSON ledger contains component checksums and unrounded class boundaries. Source terms below describe the retained evidence; they do not grant additional rights.','']
    html.append('<h2>Source records</h2>')
    for identifier,s in book['sources'].items():
        pdf += [Spacer(1,8),para(escape(s['title']),'h2')]
        md += [f'<a id="source-{identifier}"></a>','',f'### {s["title"]}','',f'[{s["title"]}]({s["url"]}) · `{identifier}`','']
        html.append(f'<article id="source-{identifier}"><h3>{escape(s["title"])}</h3><p><a href="{escape(s["url"],quote=True)}">Provider/source page</a> · <code>{identifier}</code></p>')
        pdf.append(para(f'<link href="{escape(s["url"],quote=True)}" color="#503b75">{escape(s["url"])}</link>','small'))
        for value in [s['period'],s['notes'],s['license']]:
            if value:
                pdf.append(para(escape(value),'small'));md += [value,''];html.append('<p>'+escape(value)+'</p>')
        if s.get('upstream_sha256'):
            value='Upstream SHA-256: '+s['upstream_sha256']
            pdf.append(para(escape(value),'small'));md += ['`'+value+'`',''];html.append('<p><code>'+value+'</code></p>')
        if s.get('references'):
            md += ['Retained source links:',''];html.append('<ul>')
            for ref in s['references']:
                label=ref['layer'];url=ref['url']
                md.append(f'- [{label}]({url})')
                html.append(f'<li><a href="{escape(url,quote=True)}">{escape(label)}</a></li>')
                pdf.append(para(f'{escape(label)}: <link href="{escape(url,quote=True)}" color="#503b75">{escape(url)}</link>','small'))
            md += [''];html.append('</ul>')
        html.append('</article>')
    html.append('</html>')
    def footer(canvas,document):
        canvas.setFont('Atkinson-Regular',8);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(42,24,'Setouchi 2028 · ST2 source bibliography · 30 October 2026')
        canvas.drawRightString(A4[0]-42,24,str(document.page))
    SimpleDocTemplate(str(output/'plate-source-bibliography.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,
                      topMargin=42,bottomMargin=42,title='Setouchi 2028 — Data plate bibliography',author='Cartofreako').build(pdf,onFirstPage=footer,onLaterPages=footer)
    (output/'plate-source-bibliography.html').write_text('\n'.join(html)+'\n')
    markdown='\n'.join(md).rstrip()+'\n'
    (output/'plate-source-bibliography.md').write_text(markdown.replace('[Review guide](setouchi-2028.md)',
        '[Plate review](index.html)').replace('(../data/anthropocene-particulate.md)',
        '(https://bdekoz.github.io/cartofreako/docs/pages/data/anthropocene-particulate.html)'))
    (output/'plate-source-bibliography.json').write_text(json.dumps(book,indent=2,ensure_ascii=False)+'\n')
    if docs_page:
        docs_page.write_text(markdown.replace('## Plate index',
            '[Download source ledger and checksums]('+docs_page.with_suffix('.json').name+')\n\n## Plate index',1))
        docs_page.with_suffix('.json').write_text(json.dumps(book,indent=2,ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',type=Path,default=ROOT/'output/setouchi-triennale-2028')
    parser.add_argument('--output',type=Path,default=ROOT/'output/setouchi-triennale-2028-st2')
    parser.add_argument('--docs-page',type=Path)
    args=parser.parse_args();book=build(args.delivery.resolve(),args.output.resolve())
    write_outputs(book,args.output,args.docs_page)
    print(f"Bibliography: {len(book['entries'])} plate pairs; {len(book['sources'])} source records")


if __name__=='__main__':main()
