import csv, sys, re
R='/Users/danielgnagi/gtazurich/research/'
done=set()
with open(R+'pois_kreis4.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f): done.add(r['osm_id'])
skip=re.compile(r'schul|kita|kindergarten|kinderkrippe|krippe|hort|school|kindergarten|kids? ?club', re.I)
PRI=['langstrasse','helvetiaplatz','stauffacher','badenerstr','militärstr','militaerstr']
rows=[]
with open(R+'pois_kreis4_osm.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['osm_id'] in done: continue
        if skip.search(r['name'] or '') or skip.search(r['kind'] or ''): continue
        a=(r['address'] or '').lower()
        p=next((i for i,k in enumerate(PRI) if k in a),99)
        rows.append((p,r))
rows.sort(key=lambda t:t[0])
mode=sys.argv[1] if len(sys.argv)>1 else 'count'
if mode=='count':
    print('ungeprueft:',len(rows))
    from collections import Counter
    print(Counter(min(p,99) for p,_ in rows))
else:
    n=int(mode); off=int(sys.argv[2]) if len(sys.argv)>2 else 0
    for p,r in rows[off:off+n]:
        print(r['osm_id'],'|',r['name'],'|',r['kind'],'|',r['address'],'|',r['website'])
