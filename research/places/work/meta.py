import json,time,urllib.request,urllib.parse,re
UA='gtazurich-research/1.0 (daniel.gnaegi@outlook.com)'
cand=json.load(open('cand.json'));meta={}
titles=sorted({t for c in cand.values() for t in c})
for i in range(0,len(titles),40):
    p={'action':'query','prop':'imageinfo','iiprop':'url|extmetadata|size|mime','iiurlwidth':1024,'titles':'|'.join(titles[i:i+40]),'format':'json'}
    for a in range(6):
        try:
            r=json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p),headers={'User-Agent':UA}),timeout=40));break
        except urllib.error.HTTPError as e:
            time.sleep(20*(a+1))
    for pg in r['query']['pages'].values():
        ii=(pg.get('imageinfo') or [{}])[0];em=ii.get('extmetadata',{})
        g=lambda k:re.sub('<[^>]+>','',em.get(k,{}).get('value',''))
        meta[pg['title']]={'thumb':ii.get('thumburl'),'w':ii.get('width'),'h':ii.get('height'),'mime':ii.get('mime'),'license':g('LicenseShortName'),'author':g('Artist')[:80],'date':g('DateTimeOriginal')[:20],'desc':g('ImageDescription')[:150],'page':ii.get('descriptionurl')}
    time.sleep(1.5)
json.dump(meta,open('meta.json','w'),ensure_ascii=False)
for k,c in cand.items():
    print('##',k)
    for t in sorted(c,key=lambda t:c[t]):
        m=meta.get(t,{})
        if m.get('mime')!='image/jpeg':continue
        print(int(c[t]),t[5:70],'|',m['license'][:12],'|',m['desc'][:50])
