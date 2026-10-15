import csv, sys
R='/Users/danielgnagi/gtazurich/research/'
import re
skip=re.compile(r'schul|kita|kindergarten|kinderkrippe|krippe|hort|school|kids? ?club|college|universit|berufsschule|gymnas', re.I)
def done(fn):
    s=set()
    with open(R+fn,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f): s.add(r['osm_id'])
    return s
out=[]
for k,osm,cur in [('k4','pois_kreis4_osm.csv','pois_kreis4.csv'),('k5','pois_kreis5_osm.csv','pois_kreis5.csv')]:
    d=done(cur)
    with open(R+osm,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            x=float(r['x']); y=float(r['y'])
            if not (600<=x<=1200 and -1000<=y<=-400): continue
            if r['osm_id'] in d: continue
            if skip.search(r['name'] or '') or skip.search(r['kind'] or ''): continue
            out.append((k,r['osm_id'],r['name'],r['kind'],r['address'],r['website'],x,y))
print('total',len(out))
from collections import Counter
print(Counter(o[0] for o in out))
if len(sys.argv)>1:
    a,b=int(sys.argv[1]),int(sys.argv[2])
    for o in out[a:b]: print('|'.join(str(v) for v in o))
