import json,math,collections
from pyproj import Transformer
T=Transformer.from_crs(4326,2056,always_xy=True)
def loc(lat,lon):
    x,y=T.transform(lon,lat);return x-2681400,y-1248700
PL={'altstetten_bahnhof':(47.3913,8.4885,330),'lindenplatz':(47.3878,8.4848,230),
'hohlstrasse_k9':(47.3866,8.4990,0),'wiedikon_bahnhof':(47.3716,8.5230,230),
'schmiede_wiedikon':(47.3701,8.5245,200),'badenerstrasse_albisrieder_linden':(47.3830,8.4960,0)}
d=json.load(open('/Users/danielgnagi/gtazurich/data/raw/osm/kreise.json'))['elements']
# print centers for hohlstrasse
hs=[e for e in d if 'lat' in e and e.get('tags',{}).get('addr:street')=='Hohlstrasse']
xs=sorted((loc(e['lat'],e['lon']),e['tags'].get('addr:housenumber')) for e in hs)
print('Hohlstr addr x range',xs[0],xs[-1],len(xs))
bs=[e for e in d if 'lat' in e and e.get('tags',{}).get('addr:street')=='Badenerstrasse']
b=sorted((loc(e['lat'],e['lon']),e['tags'].get('addr:housenumber')) for e in bs)
print('Badener range',b[0],b[-1],len(b))
out={}
for k,(la,lo,r) in PL.items():
    if r==0: continue
    cx,cy=loc(la,lo);items=[]
    for e in d:
        if 'lat' not in e: continue
        t=e.get('tags')
        if not t: continue
        x,y=loc(e['lat'],e['lon'])
        if math.hypot(x-cx,y-cy)>r: continue
        keys=[kk for kk in('shop','amenity','tourism','leisure','railway','public_transport','man_made','historic','natural','building','height','building:levels','name','bench','shelter') if kk in t]
        if t.get('building') or t.get('name') or t.get('shop') or t.get('amenity') or t.get('historic') or t.get('natural')=='tree' or t.get('man_made'):
            items.append({'x':round(x),'y':round(y),'tags':{kk:t[kk] for kk in t if kk in('name','shop','amenity','tourism','leisure','railway','public_transport','man_made','historic','natural','building','height','building:levels','roof:shape','building:colour','building:material','roof:colour','cuisine','addr:street','addr:housenumber','tram','bus','bench','shelter','covered','bin','artwork_type','denomination','religion')}})
    out[k]={'center_local':[round(cx),round(cy)],'items':items}
    print(k,'center',round(cx),round(cy),'items',len(items))
json.dump(out,open('osm_nodes.json','w'),ensure_ascii=False)
