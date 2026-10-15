import json,time,urllib.request,os,random
UA='sandboxzurich-research/1.0'
OUT='/Users/danielgnagi/sandboxzurich/data/raw/photos/places'
# bbox points: (name, lon, lat, d)
P={'altstetten_bahnhof':[(8.4885,47.3913),(8.4880,47.3922)],
'lindenplatz':[(8.4848,47.3878),(8.4842,47.3872)],
'hohlstrasse_k9':[(8.4946,47.3896),(8.5016,47.3881),(8.4860,47.3917),(8.4990,47.3871)],
'wiedikon_bahnhof':[(8.5230,47.3716),(8.5222,47.3712)],
'schmiede_wiedikon':[(8.5245,47.3701),(8.5240,47.3698)],
'badenerstrasse':[(8.4930,47.3830),(8.4890,47.3850),(8.4960,47.3800)]}
res={}
for k,pts in P.items():
    got=[]
    for lo,la in pts:
        d=0.0006
        u=f'https://api.panoramax.xyz/api/search?bbox={lo-d},{la-d},{lo+d},{la+d}&limit=40'
        try:f=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40))['features']
        except Exception as e:print(k,e);continue
        f.sort(key=lambda x:x['properties'].get('datetime',''),reverse=True)
        seen=set()
        for it in f:
            c=it['properties'].get('geovisio:producer','')+it['collection'] if 'collection' in it else it['id']
            if c in seen: continue
            seen.add(c);got.append(it)
            if len(got)>=(5 if len(pts)<3 else 3)*(pts.index((lo,la))+1):break
        time.sleep(1)
    os.makedirs(f'{OUT}/{k}/pmx',exist_ok=True);res[k]=[]
    for i,it in enumerate(got[:8]):
        a=it['assets'].get('sd') or it['assets'].get('hd')
        fn=f'{OUT}/{k}/pmx/{i:02d}.jpg'
        try:open(fn,'wb').write(urllib.request.urlopen(urllib.request.Request(a['href'],headers={'User-Agent':UA}),timeout=60).read())
        except Exception as e:print(e);continue
        p=it['properties']
        res[k].append({'file':fn.split('photos/')[1],'id':it['id'],'datetime':p.get('datetime'),'license':p.get('license'),'producer':p.get('geovisio:producer'),'coord':it['geometry']['coordinates'],'src':'Panoramax','url':'https://api.panoramax.xyz/api/collections/%s/items/%s'%(it.get('collection'),it['id'])})
        time.sleep(1)
    print(k,len(res[k]),flush=True)
json.dump(res,open('pmx.json','w'),ensure_ascii=False)
