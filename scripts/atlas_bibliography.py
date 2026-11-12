"""Resolve each atlas subject's bibliography from its selected dataset inputs."""
import json
from html import escape
from pathlib import Path
import re

from dataset import binding, context, digest


def read(path):
    return json.loads(Path(path).read_text())


def prepared_metadata(path):
    """Read the small leading metadata object without loading all H3 features."""
    prefix = ''
    with Path(path).open() as stream:
        while len(prefix) < 16*1024*1024:
            chunk = stream.read(65536)
            if not chunk:
                break
            prefix += chunk
            match = re.search(r'"metadata"\s*:\s*',prefix)
            if match:
                try:
                    return json.JSONDecoder().raw_decode(prefix[match.end():])[0]
                except json.JSONDecodeError:
                    pass
    raise ValueError('Prepared source metadata is missing or too large: '+str(path))


def citation(source):
    title = source.get('title') or source.get('organization') or source.get('id', 'Source')
    period = source.get('reference_period') or source.get('available_through') or source.get('release')
    return title + (f' / {period}' if period else '') + (' / '+source['url'] if source.get('url') else '')


def geographic_context_citation():
    selected = context(required=False)
    edition = next(s for s in selected[1]['sources'] if s['id']=='natural-earth')['coverage']['edition'] if selected else None
    return 'Natural Earth'+(' '+edition if edition else '')+' geographic context and shoreline / public domain / https://www.naturalearthdata.com/'


def bibliography(plate):
    """Return printable citations and exact local source evidence, fail closed."""
    _, dataset = context()
    stem = plate['source_stem']
    ident = plate['id']
    natural = next(s for s in dataset['sources'] if s['id'] == 'natural-earth')
    base = f"Natural Earth {natural['coverage']['edition']}, 1:10m physical vectors / public domain / https://www.naturalearthdata.com/downloads/10m-physical-vectors/"
    refs, evidence = [], []

    def profile(path):
        path = Path(path)
        evidence.append({'path': str(path), 'sha256': digest(path)})
        return read(path)

    if ident in ('geometry', 'graticules', 'earth', 'water'):
        if ident == 'geometry':
            refs.append('Cartofreako AuthaGraph projection construction and seam geometry / src.projections and src.generate in the recorded implementation. These lines are calculated geometry, not observed measurements.')
        elif ident == 'graticules':
            refs.append('Cartofreako generated longitude/latitude graticule in AuthaGraph / src.projections and src.generate in the recorded implementation. These lines are calculated coordinates, not observed measurements.')
        elif ident == 'water':
            refs.append('Natural Earth physical layers: bathymetry (0 to -10,000 m contours), minor islands, glaciated areas, Antarctic ice shelves, lakes, playas, rivers, reefs and coastline. This is a cartographic release, not a November water observation.')
        else:
            refs.append('Natural Earth land and ocean polygons, coastlines and geographic context. The dataset date is not the observation date of every coastline.')
        if ident in ('earth','water'):
            refs.append(base)
    elif ident == 'cloud-atmosphere':
        p = profile(binding('ATLAS_CLOUD_PROFILE'))
        intervals = {r['source']: r for r in next(s for s in dataset['sources'] if s['id']=='atmosphere')['coverage']['observations']}
        for source in p['sources']:
            interval = intervals.get(source['id'], {})
            times = ' to '.join(str(interval[k]) for k in ('start_utc','end_utc') if interval.get(k))
            refs.append(citation(source) + (' / observed '+times if times else ''))
    elif stem.startswith('resources-') or ident == 'anthropocene-coral-reef-threat-2011':
        p = profile(binding('RESOURCES_DATA_DIR')/'resources-profile.json')
        metrics = [m for f in p['families'] for m in f['metrics']]
        if ident == 'resources-mineral-mine-production-comparison':
            metrics = [m for m in metrics if m['id'] in ('rare-earth-mine-production','lithium-mine-production','uranium-mine-production')]
        else:
            metrics = [m for m in metrics if m.get('output_tag') and stem.endswith(m['output_tag'])]
        if not metrics:
            raise ValueError('No source metric for '+stem)
        ids = {s for m in metrics for s in m['source_ids']}
        refs.extend(m['title']+' / reference period '+m['reference_period']+' / '+m['unit'] for m in metrics)
        refs.extend(citation(s) for s in p['sources'] if s['id'] in ids or s['id']=='natural-earth-admin0')
    elif stem.startswith('petroleum-'):
        profile(binding('PETROLEUM_DATA')/'download-manifest.json')
        if 'eia' in stem:
            refs.append('US Energy Information Administration, Short-Term Energy Outlook, October 2026, petroleum and other liquid fuels production tables; 2025 historical/estimate values / https://www.eia.gov/outlooks/steo/data.php?type=tables')
        else:
            refs.append('OPEC, World Oil Outlook 2026 / '+('country source-coverage register' if 'coverage' in stem else '2030 liquids-supply projection')+' / https://publications.opec.org/woo')
        refs.append(base)
    elif ident.startswith('anthropocene-particulate-'):
        folder = binding('ANTHROPOCENE_DATA_DIR')
        p = profile(folder/(ident+'-profile.json'))
        metadata = prepared_metadata(folder/p['data']['geojson'])
        evidence.append({'prepared_source_statistics':metadata['source_statistics'],
                         'prepared_geojson_sha256':p['data']['sha256']})
        names = {'noaa-ghcn-gsn':'NOAA GHCN Daily / Global Climate Observing System Surface Network',
                 'epa-airdata-pm25':'US EPA AirData daily PM2.5 (parameter 88101)',
                 'noaa-hms-smoke':'NOAA Hazard Mapping System smoke polygons',
                 'noaa-storm-events':'NOAA Storm Events Database',
                 'cwfis-hotspots':'Natural Resources Canada, CWFIS hotspots',
                 'nasa-firms':'NASA FIRMS active fire detections'}
        for source in p['sources']:
            firms = source['id']=='nasa-firms' and metadata['source_statistics'].get('firms_rows',0)>0
            if source['status']=='included' or firms:
                selected = {**source, 'title':names.get(source['id'],source['id'])}
                # available_through is a retained configuration hint, not
                # refreshed by the preparer. Never print it as an observed cutoff.
                selected.pop('available_through',None)
                selected['reference_period']=str(metadata['calendar_year'])+' source observations'
                if firms:
                    dates=metadata['source_statistics']['firms_detection_dates']
                    selected['reference_period']=min(dates)+' through '+max(dates)
                    selected['url']='https://firms.modaps.eosdis.nasa.gov/'
                refs.append(citation(selected))
        if metadata['source_statistics'].get('firms_rows',0)>0:
            refs.append('FIRMS inclusion is verified from ingested observations, despite the profile\'s optional label.')
        refs.append('Providers have different reporting coverage. The acquisition timestamp does not establish a common observation cutoff; retained profile availability hints are not presented as measured dates. Validation-only and excluded providers are not mapped.')
    elif ident.startswith('anthropocene-land-temperature-'):
        p = profile(binding('ANTHROPOCENE_DATA_DIR')/(ident+'-profile.json'))
        refs.extend([citation(p['source']), 'Observation window: '+str(p['duration']['year'])+'-01-01 through '+p['snapshot']['data_through']+'. Same-calendar-day record history '+str(p['records']['baseline_start'])+'-'+str(p['records']['baseline_end'])+'.'])
    elif ident == 'network-cdn':
        path = binding('CDN_SOURCE_PROFILE')
        p = profile(path)
        m = profile(path.parent/p['manifest'])
        appendix = path.parent/'source'/m['bibliography']['files']['json']['path']
        full = profile(appendix)
        evidence.append({'plotted_layers':[{k:layer[k] for k in ('layer','snapshot_tag','sources','providers') if k in layer}
                                          for layer in m['layers']]})
        evidence.append({'provider_bibliography':full})
        origin = profile(binding('NETWORK_INFRASTRUCTURE_DATA_DIR')/'network-infrastructure-sites-profile.json')['sources']['cloud_cdn']['repository']
        refs.extend(['Retained cloud/CDN provider source manifest '+Path(p['manifest']).stem.removeprefix('manifest.')+' / '+origin+'/tree/'+p['source_revision']+'.',
                     f"The retained provider bibliography contains {m['bibliography']['reference_count']} references, including supporting context. Citations for the plotted source layers, their URLs and retrieval dates: sources/plate-bibliography.html#network-cdn.",
                     'Source layers retain their own snapshot dates. Record totals are not a verified census of active facilities.',
                     'Example primary references: Google infrastructure / https://peering.google.com/static/js/site/modules/pages/infrastructure.html ; Google data centers / https://datacenters.google/locations/'])
    elif ident == 'network-fiber':
        p = profile(binding('FIBER_SYNTHESIZED_DATA_DIR')/'manifest.json')
        refs.extend(['TeleGeography Submarine Cable Map, retained snapshots '+', '.join(s['snapshot'] for s in p['sources'])+' / '+p['source_repository']+' / '+p['license'],
                     'ITU Broadband Maps terrestrial fibre snapshot, 29 October 2026 / https://bbmaps.itu.int/ . Source operational, construction and planned statuses remain distinct.'])
    elif ident.startswith('network-swarm-'):
        from cartofreako_style import STYLE
        cache = binding('NATIVE_SWARM_CACHE_DIRECTORY')
        dates = [re.search(r'-cumulative-(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})\.json$', p.name) for p in cache.glob('*-cumulative-*.json')]
        if not dates or not all(dates):
            raise ValueError('Swarm observation periods are missing')
        refs.extend(['Alpha60 cumulative downloader observations / '+STYLE['swarm']['collection']+' / '+min(m[1] for m in dates)+' through '+max(m[2] for m in dates)+' / https://github.com/alpha60-devops/alpha60',
                     'IPinfo retained geolocation database / https://ipinfo.io/ . Locations are IP geolocation estimates, not verified household or person locations.',
                     f'{len(dates)} pinned cumulative cache documents and torrent definitions are retained in the dataset. Circle areas follow native observation weights; cross-torrent observations are not unique people or traffic.'])
    elif ident == 'network-groundstations':
        p = profile(binding('NETWORK_GROUNDSTATIONS_PROFILE'))['source']
        refs.append(p['title']+' / supplied KML snapshot '+p['datestamp']+' / '+p['kml']+' / '+p['license']+'. The supplied collection is not attributed to SpaceX.')
        from atlas_presentation import groundstation_settings
        from cartofreako_style import STYLE
        from dataset import ROOT
        config=profile(ROOT/groundstation_settings(STYLE)['capability_config'])
        refs.extend('Capability interpretation reference: '+citation(r) for r in config['references'])
        refs.append('Capability references support the antenna-size and band interpretation; they do not independently verify each site or its operational status.')
    elif ident.startswith('astro-'):
        p = profile(binding('ASTRO_DATA_DIR')/('astro-hubble-profile.json' if ident.endswith('hubble') else 'astro-profile.json'))
        refs.extend(['ESA Gaia DR3 bright-star query / https://gea.esac.esa.int/archive/',
                     'NASA Exoplanet Archive host-system query / https://exoplanetarchive.ipac.caltech.edu/',
                     'NASA/JPL Small-Body Database orbital elements and approximate Solar System calculations / https://ssd.jpl.nasa.gov/tools/sbdb_query.html',
                     'Curated persistent and transient sky objects retain per-object references in the source catalog and SVG. Calculation: '+p['timestamp']+'.'])
        if ident.endswith('hubble'):
            refs.append('Hubble orbit: CelesTrak science OMM catalog / '+p['observer']['source_url'])
    elif ident.startswith('orbital-'):
        p = profile(binding('ORBITING_PROFILE'))
        refs.extend(['CelesTrak OMM elements and named memberships, propagated with SGP4 / https://celestrak.org/NORAD/documentation/gp-data-formats.php',
                     'SGP4 reference / https://celestrak.org/publications/AIAA/2006-6753/',
                     'Calculation: '+str(p.get('timestamp',dataset['requested_as_of']))+'. The retained NASA SSC reference is historical validation, not current position evidence.'])
    else:
        raise ValueError('Missing plate bibliography: '+ident)
    if not refs:
        raise ValueError('Empty plate bibliography: '+ident)
    return {'plate':ident, 'references':refs, 'evidence':evidence,
            'dataset_id':dataset['dataset_id']}


def write_bibliography(destination, plates):
    from dataset import atomic_json
    destination = Path(destination)
    atomic_json(destination/'sources/plate-bibliography.json', {'plates':plates})
    html = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
            '<title>Atlas data bibliography</title><style>body{max-width:70rem;margin:3rem auto;padding:0 1.5rem;font:18px/1.5 sans-serif;background:#fcc553;color:#240413}a{color:inherit}article{margin:3rem 0}li{margin:.8rem 0;overflow-wrap:anywhere}</style>',
            '<h1>Atlas data bibliography</h1><p><a href="../index.html">Atlas</a> · <a href="plate-bibliography.json">Exact source evidence and hashes</a></p>',
            '<p>Each subject below cites its bound dataset inputs. Source observation periods, release dates and acquisition dates remain distinct.</p>']
    for plate in plates:
        html.append('<article id="'+escape(plate['plate'])+'"><h2>'+escape(plate['plate'])+'</h2><ul>')
        html.extend('<li>'+escape(ref)+'</li>' for ref in plate['references'])
        html.append('</ul>')
        for evidence in plate['evidence']:
            if 'plotted_layers' in evidence:
                html.append('<h3>Input layers and primary references</h3><ul>')
                for layer in evidence['plotted_layers']:
                    html.append('<li>'+escape(layer['layer'])+' / '+escape(str(layer.get('snapshot_tag','source-declared')))+'<ul>')
                    for source in layer.get('sources',[]):
                        url=source.get('source_url','')
                        html.append('<li><a href="'+escape(url,quote=True)+'">'+escape(url)+'</a></li>')
                    html.append('</ul></li>')
                html.append('</ul>')
            if 'provider_bibliography' in evidence:
                html.append('<details><summary>Complete retained provider bibliography (also includes supporting context)</summary><ul>')
                for ref in evidence['provider_bibliography']['references']:
                    url=ref.get('source_url','')
                    html.append('<li><a href="'+escape(url,quote=True)+'">'+escape(ref['title'])+'</a> / '+escape(str(ref.get('publisher','')))+
                                ' / retrieved '+escape(str(ref.get('retrieved_at','not recorded')))+'<br>'+escape(ref.get('role_and_limits',''))+'</li>')
                html.append('</ul></details>')
        html.append('</article>')
    (destination/'sources/plate-bibliography.html').write_text('\n'.join(html)+'\n</html>\n')
