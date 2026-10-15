import json,time,re,os,urllib.request,urllib.parse,collections
UA='sandboxzurich-research/1.0 (daniel.gnaegi@outlook.com)'
OUT='/Users/danielgnagi/sandboxzurich/data/raw/photos/places'
def api(**p):
    p['format']='json'
    for i in range(6):
        try:
            r=json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p),headers={'User-Agent':UA}),timeout=40));time.sleep(1.5);return r
        except urllib.error.HTTPError as e: time.sleep(20*(i+1))
PL={'schmiede_wiedikon':[(47.3700,8.5192,250),(47.3706,8.5170,200)],
'badenerstrasse':[(47.3804,8.5050,160),(47.3824,8.5000,160),(47.3844,8.4950,160),(47.3863,8.4900,160),(47.3782,8.5103,200)]}
bad=re.compile(r'Hauptbahnhof|panoramio|Panorama|Luftbild|Karte|Plan|Logo|Wappen|map',re.I)
old=json.load(open('sel.json'));sel={}
for k,pts in PL.items():
    c={}
    for la,lo,r in pts:
        for t in api(action='query',list='geosearch',gscoord=f'{la}|{lo}',gsradius=r,gslimit=60,gsnamespace=6)['query']['geosearch']:c[t['title']]=min(c.get(t['title'],999),t['dist'])
    c={t:d for t,d in c.items() if t not in old[k]}
    titles=list(c);meta={}
    for i in range(0,len(titles),40):
        r=api(action='query',prop='imageinfo',iiprop='url|extmetadata|size|mime',iiurlwidth=1024,titles='|'.join(titles[i:i+40]))
        for pg in r['query']['pages'].values():
            ii=(pg.get('imageinfo') or [{}])[0];em=ii.get('extmetadata',{})
            g=lambda k:re.sub('<[^>]+>','',em.get(k,{}).get('value',''))
            meta[pg['title']]={'thumb':ii.get('thumburl'),'mime':ii.get('mime'),'license':g('LicenseShortName'),'author':g('Artist')[:80],'date':g('DateTimeOriginal')[:20],'desc':g('ImageDescription')[:150],'page':ii.get('descriptionurl')}
    gc=collections.Counter();s=[]
    for t in sorted(c,key=lambda t:c[t]):
        m=meta.get(t,{})
        if m.get('mime')!='image/jpeg' or not m.get('thumb') or bad.search(t):continue
        key=re.sub(r'[\d\W_]+',' ',t[5:])[:22]
        if gc[key]>=2:continue
        gc[key]+=1;s.append(t)
    s=s[:16];print(k,len(titles),len(s),flush=True)
    m0=json.load(open('meta.json'));m0.update(meta);json.dump(m0,open('meta.json','w'),ensure_ascii=False)
    for i,t in enumerate(s):
        fn=f'{OUT}/{k}/s{i:02d}.jpg'
        if not os.path.exists(fn):
            for a in range(6):
                try:open(fn,'wb').write(urllib.request.urlopen(urllib.request.Request(meta[t]['thumb'],headers={'User-Agent':UA}),timeout=60).read());break
                except urllib.error.HTTPError: time.sleep(30*(a+1))
            time.sleep(3.6)
    sel[k]=s
json.dump(sel,open('sel_supp.json','w'),ensure_ascii=False)
