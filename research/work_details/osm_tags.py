import json, csv, ast, sys
ROOT='/Users/danielgnagi/sandboxzurich'
want={}
for r in csv.DictReader(open(f'{ROOT}/research/work_details/signs_raw.csv')):
    want[str(r['osm'])]=r
d=json.load(open(f'{ROOT}/data/raw/osm/kreise.json'))
found={}
def parse(t):
    if isinstance(t,dict): return t
    try: return ast.literal_eval(t)
    except Exception:
        try: return json.loads(t)
        except Exception: return {}
for e in d['elements']:
    i=str(e.get('id'))
    if i in want and i not in found:
        found[i]=(e.get('type'), e.get('lat'), e.get('lon'), parse(e.get('tags')))
keys=['opening_hours','cuisine','outdoor_seating','website','contact:website','addr:street','addr:housenumber','addr:postcode','addr:city','description','brand','shop','amenity','craft','drink:beer','takeaway','wheelchair','phone','email','smoking','reservation','note','check_date','opening_hours:covid19']
out=f'{ROOT}/research/work_details/osm_tags.csv'
with open(out,'w',newline='') as fh:
    w=csv.writer(fh)
    w.writerow(['osm','name','osm_type','lat','lon']+keys+['other_tags'])
    for i,r in want.items():
        if i not in found:
            w.writerow([i,r['name'],'MISSING','','']+['']*len(keys)+['']); continue
        t,lat,lon,tags=found[i]
        row=[i,r['name'],t,lat,lon]+[tags.get(k,'') for k in keys]
        other={k:v for k,v in tags.items() if k not in keys and k!='name'}
        row.append(json.dumps(other,ensure_ascii=False)[:300])
        w.writerow(row)
print('signs',len(want),'found',len(found),'missing',len(want)-len(found))
