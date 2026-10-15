import csv, math
ROOT='/Users/danielgnagi/sandboxzurich'
sig={r['osm']:r for r in csv.DictReader(open(f'{ROOT}/research/work_details/signs_raw.csv'))}
rows=list(csv.DictReader(open(f'{ROOT}/research/work_details/osm_tags.csv')))
NIGHT={'bar','pub','nightclub','restaurant','fast_food','cafe'}
HOSP=NIGHT|{'ice_cream','bakery','kiosk','erotic','cannabis','music','books','clothes','bicycle','motorcycle','beauty','hairdresser','pharmacy','jewelry','bag','community_centre','kindergarten','company','architect','it','joiner','furniture','interior_decoration','convenience'}
def dist(lat,lon,la,lo): return math.hypot((lat-la)*111320,(lon-lo)*111320*math.cos(math.radians(47.37)))
HP=(47.3757,8.5252)
out=[]
for r in rows:
    if r['osm_type']=='MISSING': continue
    s=sig[r['osm']]; kind=s['kind']; st=r['addr:street']
    lat,lon=float(r['lat']),float(r['lon']); dh=dist(lat,lon,*HP)
    if kind in NIGHT and st=='Langstrasse': p=1
    elif kind in NIGHT and (dh<300 or st in ('Stauffacherstrasse','Hohlstrasse','Kanonengasse','Militärstrasse','Dienerstrasse','Brauerstrasse','Lagerstrasse','Ankerstrasse')): p=2
    elif kind in HOSP: p=3
    else: p=4
    if st=='Langstrasse' and kind not in NIGHT and kind in HOSP: p=2
    out.append([p,r['osm'],s['name'],kind,(st+' '+r['addr:housenumber']).strip(),r['website'] or r['contact:website'],r['opening_hours'][:70],r['cuisine'],r['outdoor_seating'],round(dh)])
out.sort(key=lambda x:(x[0],-(x[9]<300 and 1 or 0),x[2]))
with open(f'{ROOT}/research/work_details/batches.tsv','w') as fh:
    fh.write('prio\tosm\tname\tkind\taddr\twebsite\topening_hours\tcuisine\toutdoor\tdist_hp\n')
    for o in out: fh.write('\t'.join(str(x) for x in o)+'\n')
import collections
print(collections.Counter(o[0] for o in out))
