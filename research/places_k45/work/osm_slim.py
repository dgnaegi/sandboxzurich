import json,pickle
d=json.load(open('/Users/danielgnagi/sandboxzurich/data/raw/osm/kreise.json'))['elements']
nodes={e['id']:(e['lat'],e['lon']) for e in d if e['type']=='node'}
out=[]
for e in d:
    t=e.get('tags')
    if not t: continue
    if e['type']=='node': c=(e['lat'],e['lon'])
    elif e['type']=='way':
        pts=[nodes[n] for n in e['nodes'] if n in nodes]
        if not pts: continue
        c=(sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts))
    else: continue
    out.append((e['type'],e['id'],c[0],c[1],t))
pickle.dump(out,open('osm_slim.pkl','wb'));print(len(out))
