import csv, sys
R='/Users/danielgnagi/gtazurich/research/pois_kreis4.csv'
VALID={'ok','closed','renamed','moved','unclear','new'}
done=set()
with open(R,newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f): done.add(r['osm_id'])
out=[]
names={}
with open('/Users/danielgnagi/gtazurich/research/pois_kreis4_osm.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f): names[r['osm_id']]=r['name']
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    p=line.split('|')
    p+=['']*(5-len(p))
    oid,status,new,addr,src=[x.strip() for x in p[:5]]
    if status not in VALID: print('BAD STATUS',oid,status); continue
    if oid in done: print('DUP',oid); continue
    done.add(oid)
    out.append([oid,names.get(oid,''),status,new,addr,src,'2026-10-15'])
with open(R,'a',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    for o in out:
        o[1]=o[1]  # name filled below
        w.writerow(o)
print('appended',len(out))
