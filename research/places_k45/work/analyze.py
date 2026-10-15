import pickle,json,math,sys,collections
sys.path.insert(0,'.')
from places_def import PLACES
from pyproj import Transformer
T=Transformer.from_crs(4326,2056,always_xy=True)
def loc(la,lo):
    e,n=T.transform(lo,la); return round(e-2681400),round(n-1248700)
o=pickle.load(open('osm_slim.pkl','rb'))
her=json.load(open('/Users/danielgnagi/sandboxzurich/data/raw/heritage/inv.geojson'))['features']
res={}
for slug,(name,kr,la,lo,rad,_) in PLACES.items():
    cx,cy=loc(la,lo); L=[f"CENTER local x={cx} y={cy} r={rad}"]
    near=[]
    for t,i,a,b,tg in o:
        x,y=loc(a,b) if abs(a-la)<0.004 and abs(b-lo)<0.006 else (1e9,1e9)
        d=math.hypot(x-cx,y-cy)
        if d<=rad: near.append((d,x,y,t,i,tg))
    near.sort(key=lambda z:z[0])
    bld=[n for n in near if 'building' in n[5] and n[3]=='way']
    big=[n for n in bld if any(k in n[5] for k in('height','building:levels','name','building:colour','building:material','roof:shape'))]
    L.append(f"buildings {len(bld)}; tagged:")
    for d,x,y,t,i,tg in big[:14]:
        s={k:v for k,v in tg.items() if k in('name','building','height','building:levels','building:colour','building:material','roof:shape','roof:colour','roof:material','start_date','addr:street','addr:housenumber')}
        L.append(f"  ({x},{y}) {s}")
    shops=[n for n in near if n[3]=='node' and any(k in n[5] for k in('shop','amenity')) and 'name' in n[5] and n[5].get('amenity') not in('bench','bicycle_parking','waste_basket','drinking_water','toilets','parking_entrance','car_sharing','bicycle_rental','post_box','recycling','vending_machine')]
    L.append("named shops/amenity: "+"; ".join(f"{n[5]['name']} [{n[5].get('shop') or n[5].get('amenity')}]({n[1]},{n[2]})" for n in shops[:30]))
    cnt=collections.Counter()
    for d,x,y,t,i,tg in near:
        for k in('highway','railway','natural','leisure','amenity','public_transport','man_made','barrier'):
            if k in tg and not (k=='highway' and t=='way'): cnt[f"{k}={tg[k]}"]+=1
    L.append("counts: "+", ".join(f"{k}:{v}" for k,v in cnt.most_common(22)))
    sf=collections.Counter(n[5].get('surface') for n in near if n[3]=='way' and 'highway' in n[5] and n[5].get('surface'))
    L.append("surfaces: "+str(dict(sf)))
    st=collections.Counter(n[5].get('name') for n in near if n[3]=='way' and 'highway' in n[5] and n[5].get('name'))
    L.append("streets: "+", ".join(k for k,_ in st.most_common(10)))
    ph=[]
    for f in her:
        lo2,la2=f['geometry']['coordinates'][:2] if f['geometry']['type']=='Point' else (None,None)
        if lo2 is None or abs(la2-la)>0.004 or abs(lo2-lo)>0.006: continue
        x,y=loc(la2,lo2)
        if math.hypot(x-cx,y-cy)<=rad:
            p=f['properties']; ph.append(f"{p['objektbeze']} [{p['inventarka']},{p['baujahr']}]({x},{y})")
    L.append(f"heritage {len(ph)}: "+"; ".join(ph[:18]))
    open(f'osm_{slug}.txt','w').write("\n".join(L)+"\n"); res[slug]=(cx,cy)
    print(slug,res[slug],len(bld),len(ph))
json.dump(res,open('centers.json','w'))
