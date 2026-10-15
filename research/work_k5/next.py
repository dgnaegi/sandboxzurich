import csv, sys, re
R='/Users/danielgnagi/sandboxzurich/research/'
done=set()
with open(R+'pois_kreis5.csv',encoding='utf-8') as f:
    for r in csv.DictReader(f): done.add(r['osm_id'])
prio=['Viadukt','Josefstr','Limmatstr','Röntgenplatz','Langstr','Hardbrücke','Prime','Escher-Wyss','Geroldstr']
rows=[]
with open(R+'pois_kreis5_osm.csv',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['osm_id'] in done: continue
        a=r['address'] or ''
        p=len(prio)
        for i,k in enumerate(prio):
            if k in a: p=i; break
        rows.append((p,r))
rows.sort(key=lambda t:t[0])
n=int(sys.argv[1]) if len(sys.argv)>1 else 25
off=int(sys.argv[2]) if len(sys.argv)>2 else 0
print('unchecked total:',len(rows))
for p,r in rows[off:off+n]:
    print(r['osm_id'],'|',r['name'],'|',r['kind'],'|',r['address'],'|',r['website'])
