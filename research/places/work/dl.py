import json,time,re,os,urllib.request,collections
UA='sandboxzurich-research/1.0 (daniel.gnaegi@outlook.com)'
OUT='/Users/danielgnagi/sandboxzurich/data/raw/photos/places'
cand=json.load(open('cand.json'));meta=json.load(open('meta.json'));sel={}
bad=re.compile(r'Hauptbahnhof|swpsig|panoramio|Panorama|Luftbild|Karte|Plan|Logo|Wappen|map',re.I)
for k,c in cand.items():
    g=collections.Counter();s=[]
    for t in sorted(c,key=lambda t:c[t]):
        m=meta.get(t,{})
        if m.get('mime')!='image/jpeg' or not m.get('thumb') or bad.search(t):continue
        key=re.sub(r'[\d\W_]+',' ',t[5:])[:22]
        if g[key]>=2:continue
        g[key]+=1;s.append(t)
    sel[k]=s[:18]
os.makedirs(OUT,exist_ok=True)
for k,s in sel.items():
    os.makedirs(f'{OUT}/{k}',exist_ok=True)
    for i,t in enumerate(s):
        fn=f'{OUT}/{k}/{i:02d}.jpg'
        if os.path.exists(fn):continue
        for a in range(6):
            try:
                open(fn,'wb').write(urllib.request.urlopen(urllib.request.Request(meta[t]['thumb'],headers={'User-Agent':UA}),timeout=60).read());break
            except urllib.error.HTTPError as e:
                time.sleep(30*(a+1))
        time.sleep(3.6)
    print(k,len(s),flush=True)
json.dump(sel,open('sel.json','w'),ensure_ascii=False)
