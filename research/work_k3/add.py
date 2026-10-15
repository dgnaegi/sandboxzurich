import csv,sys
R='/Users/danielgnagi/gtazurich/research/'
src=R+'pois_kreis3_osm.csv'; dst=R+'pois_kreis3.csv'
osm={r['osm_id']:r for r in csv.DictReader(open(src,encoding='utf-8'))}
done={r['osm_id'] for r in csv.DictReader(open(dst,encoding='utf-8'))}
VALID={"ok","closed","renamed","moved","unclear","new"}
n=0
with open(dst,'a',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    for line in sys.stdin:
        line=line.rstrip('\n')
        if not line.strip(): continue
        p=[x.strip() for x in line.split('|')]+['']*5
        oid,status,new,addr,url=p[:5]
        assert status in VALID, line
        if oid in done: print('skip dup',oid); continue
        if status=='new': w.writerow(['',new,'new','',addr,url,'2026-10-14'])
        else: w.writerow([oid,osm.get(oid,{}).get('name',''),status,new,addr,url,'2026-10-14'])
        done.add(oid); n+=1
print('appended',n)
