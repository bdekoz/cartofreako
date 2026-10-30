#!/usr/bin/env python3
"""Check local atlas links and the changed offline controls in headless Chrome."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse,unquote
import json,subprocess,tempfile
OUT=Path(__file__).resolve().parents[1]
checks=[]
cases=[
 ('index.html', '''const cards=[...document.querySelectorAll('#plates article')];
 check('38 plate pairs',cards.length===38);let f=document.querySelector('#find');
 f.value='swarm';f.dispatchEvent(new Event('input'));check('swarm search',cards.filter(x=>!x.hidden).length===2);
 f.value='';f.dispatchEvent(new Event('input'));check('reset search',cards.every(x=>!x.hidden));'''),
 ('prototypes/coral-reef/index.html', '''const views=[...document.querySelectorAll('.pair>div')];
 check('six comparison views',views.length===6);
 for(const scope of ['japan','world','both']){document.querySelector('[data-scope="'+scope+'"]').click();
 check('coral '+scope,views.filter(x=>!x.hidden).length===(scope==='both'?6:3)&&views.filter(x=>!x.hidden).every(x=>scope==='both'||x.classList.contains(scope)));}'''),
 ('sources/resource-color-key.html', '''const swatches=[...document.querySelectorAll('.color')];
 check('14 resource keys',document.querySelectorAll('article').length===14);
 check('70 distinct displayed colours',swatches.length===70&&new Set(swatches.map(x=>getComputedStyle(x).backgroundColor)).size===70);
 check('opaque colour key',swatches.every(x=>getComputedStyle(x).opacity==='1'&&!getComputedStyle(x).backgroundColor.startsWith('rgba')));''')]
with tempfile.TemporaryDirectory(prefix='cartofreako-browser-') as tmp:
    tmp=Path(tmp)
    for filename,js in cases:
        source=OUT/filename;soup=BeautifulSoup(source.read_text(),'html.parser')
        count=0
        for item in soup.select('[href],[src]'):
            ref=item.get('href',item.get('src'));url=urlparse(ref)
            if url.scheme or url.netloc or not url.path:continue
            assert (source.parent/unquote(url.path)).resolve().exists(),(filename,ref)
            count+=1
        checks.append({'page':filename,'name':'local links and images resolve','count':count,'passed':True})
        for width,height in [(1440,1100),(390,900)]:
            test=tmp/'test.html'
            script='''<script>const results=[];const check=(name,passed)=>results.push({name,passed});
            try{TESTS
            check('no horizontal overflow',document.documentElement.scrollWidth<=window.innerWidth+1);
            }catch(e){results.push({name:String(e),passed:false})}
            const result=document.createElement('pre');result.id='qa-result';result.textContent=JSON.stringify(results);document.body.append(result);</script>'''.replace('TESTS',js)
            test.write_text(source.read_text().replace('<meta charset=', '<base href="'+source.parent.as_uri()+'/"><meta charset=',1)+script)
            command=['google-chrome','--headless','--no-sandbox','--disable-gpu','--no-first-run','--disable-background-networking','--user-data-dir='+str(tmp/'chrome'),f'--window-size={width},{height}','--virtual-time-budget=1500','--dump-dom',test.as_uri()]
            r=subprocess.run(command,capture_output=True,text=True,check=True,timeout=45)
            result=BeautifulSoup(r.stdout,'html.parser').select_one('#qa-result');assert result,(filename,r.stderr[-500:])
            values=json.loads(result.get_text());assert all(c['passed'] for c in values),(filename,width,values)
            checks.extend(dict(c,page=filename,viewport=[width,height]) for c in values)
old=OUT/'sources/browser-validation.json';previous=json.loads(old.read_text())
output={'browser':'headless Chrome','status':'passed','checks':checks,'earlier_petroleum_checks':previous.get('earlier_petroleum_checks',previous.get('checks',[]))}
old.write_text(json.dumps(output,indent=2)+'\n')
print('Browser controls and local links passed:',len(checks),'checks')
