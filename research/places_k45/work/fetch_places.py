import json,os,sys,time,re,requests
sys.path.insert(0,os.path.dirname(__file__))
from places_def import PLACES
R='/Users/danielgnagi/sandboxzurich'
API="https://commons.wikimedia.org/w/api.php"
UA={"User-Agent":"sandboxzurich/0.1 (research; daniel.gnaegi@outlook.com)"}
PAUSE=3.6
def get(url,params=None,stream=False):
    for a in range(6):
        try:
            r=requests.get(url,params=params,headers=UA,timeout=60)
            if r.status_code==200: return r
            print('HTTP',r.status_code,url[:80],flush=True)
            if r.status_code==404: return None
        except Exception as e: print('err',e,flush=True)
        time.sleep(15*(a+1))
    return None
def strip(s): return re.sub(r'<[^>]+>','',s or '').strip()
meta_path=R+'/research/places_k45/places_photos.json'
meta=json.load(open(meta_path)) if os.path.exists(meta_path) else {}
for slug,(name,kr,lat,lon,rad,qs) in PLACES.items():
    if slug in meta and meta[slug]: continue
    out=R+f'/data/raw/photos/places_k45/{slug}'; os.makedirs(out,exist_ok=True)
    seen={};cands=[]
    for q in qs:
        r=get(API,{"action":"query","generator":"search","gsrsearch":q,"gsrnamespace":6,"gsrlimit":14,"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1024,"format":"json"})
        time.sleep(PAUSE)
        if not r: continue
        pages=(r.json().get('query') or {}).get('pages',{})
        for p in sorted(pages.values(),key=lambda p:p.get('index',99)):
            ii=(p.get('imageinfo') or [None])[0]
            if not ii or ii.get('mime')!='image/jpeg' or ii.get('width',0)<900: continue
            if p['title'] in seen: continue
            seen[p['title']]=1; cands.append((q,p['title'],ii))
    cands=cands[:11]
    recs=[]
    for i,(q,title,ii) in enumerate(cands,1):
        fn=f"{i:02d}.jpg"
        r=get(ii['thumburl'])
        time.sleep(PAUSE)
        if not r: continue
        open(f"{out}/{fn}",'wb').write(r.content)
        em=ii.get('extmetadata',{})
        recs.append({"file":f"data/raw/photos/places_k45/{slug}/{fn}","commons_title":title,"page":ii.get('descriptionurl'),
          "author":strip(em.get('Artist',{}).get('value')),"license":strip(em.get('LicenseShortName',{}).get('value')),
          "license_url":em.get('LicenseUrl',{}).get('value',''),"date":strip(em.get('DateTimeOriginal',{}).get('value')),
          "desc":strip(em.get('ImageDescription',{}).get('value'))[:200],"query":q})
    meta[slug]=recs
    json.dump(meta,open(meta_path,'w'),ensure_ascii=False,indent=1)
    print(slug,len(recs),flush=True)
