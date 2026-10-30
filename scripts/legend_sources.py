"""Lay out each plate's source bibliography in the free area of its legend sheet."""
import importlib
from urllib.parse import urlsplit

from legend_informatics import XL,el,text


def bibliography(group,entry,sources,scope):
    revised=importlib.import_module('revise-setouchi-plates')
    # The original right-hand legend retains its supplied physical typography.
    # The source panel uses the unused left two-thirds of the separate sheet.
    panel=el('g',group,id='plate-source-bibliography',data_plate_ordinal=entry['ordinal'])
    text(panel,.80,.80,'Data bibliography',28/72,font_weight='700')
    for i,line in enumerate(revised.wrap(entry['title']+' / '+scope.title(),22/72,27,'Bold')):
        text(panel,.80,1.28+i*.35,line,22/72,font_weight='700')
    columns=[.80,14.8];width=12.9;bottom=17.9;column=0;y=1.95
    dense=len(entry['source_ids'])>10
    body_size=(17 if dense else 18)/72;line_height=.30 if dense else .32
    def wrap(value,size,role='Regular'):
        words=[]
        for word in value.split():
            while revised.width_in(word,size,role)>width:
                cut=1
                while cut<len(word) and revised.width_in(word[:cut+1],size,role)<=width:cut+=1
                separator=max(word.rfind('/',0,cut),word.rfind('?',0,cut))
                if separator>cut//2:cut=separator+1
                words.append(word[:cut]);word=word[cut:]
            if word:words.append(word)
        return revised.wrap(' '.join(words),size,width,role)
    def block(label,paragraphs,url=None):
        nonlocal column,y
        rows=[]
        if label:rows.extend((line,20/72,'700') for line in wrap(label,20/72,'Bold'))
        for value in paragraphs:
            if value:rows.extend((line,body_size,None) for line in wrap(value,body_size))
        needed=len(rows)*line_height+.25
        if y+needed>bottom:
            column+=1;y=1.95
        if column>=len(columns):raise ValueError('Bibliography exceeds legend sheet: '+entry['stem'])
        target=panel
        if url:
            target=el('a',panel);target.set('{'+XL+'}href',url)
        for line,size,weight in rows:
            attrs={'font_weight':weight} if weight else {}
            text(target,columns[column],y,line,size,**attrs);y+=line_height
        y+=.25
    ids=list(dict.fromkeys(entry['source_ids']+(entry['japan_source_ids'] if scope=='japan' else [])))
    for index,identifier in enumerate(ids,1):
        source=sources[identifier]
        url=source['url']
        # Exact URLs are visible and clickable; no unlabeled source abbreviations.
        block(f'{index:02d}  '+source['title'],[source['period'],source['notes'],url,
                                               ('Attribution / use: '+source['license']) if source['license'] else ''],url)
    for identifier in entry.get('supporting_source_ids',[]):
        source=sources[identifier]
        block('Validation context only: '+source['title'],[source['period'],source['notes'],source['url']],source['url'])
    block('Measure and interpretation',[entry['period_and_units'],entry['method']])
    if scope=='japan':block('Japan companion',[entry['japan']])
    if entry.get('excluded_sources'):block('Source scope',[entry['excluded_sources']])
    block('Source ledger',['Pinned input files, complete source manifests and checksums:',
                          'https://bdekoz.github.io/cartofreako/docs/pages/gallery/setouchi-2028-bibliography.json'],
          'https://bdekoz.github.io/cartofreako/docs/pages/gallery/setouchi-2028-bibliography.json')
    return {'columns_used':column+1,'last_baseline_inches':y-line_height-.25,'source_ids':ids}
