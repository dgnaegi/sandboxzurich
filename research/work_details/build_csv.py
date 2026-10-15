import csv, json
R='/Users/danielgnagi/sandboxzurich/research/work_details'
facts={}
for l in open(f'{R}/facts.jsonl'):
    if l.strip():
        d=json.loads(l); facts[d['osm']]=d
rows=list(csv.DictReader(open(f'{R}/batches.tsv'),delimiter='\t'))
osm={r['osm']:r for r in csv.DictReader(open(f'{R}/osm_tags.csv'))}
OSMMAP={'yes':'ja (OSM)','no':'nein (OSM)'}
hdr=['name','osm_id','kind','address','cuisine_sortiment','opening_hours','opening_src','outdoor_seating','schild_schaufenster','stimmung_publikum','status','quelle_url','notiz']
with open('/Users/danielgnagi/sandboxzurich/research/pois_testarea_details.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(hdr)
    for r in rows:
        f=facts.get(r['osm'],{}); o=osm.get(r['osm'],{})
        oh=o.get('opening_hours','')
        out=f.get('outdoor','')
        if out in ('','unbekannt'):
            out=OSMMAP.get(r['outdoor'],'unbekannt')
        w.writerow([r['name'],r['osm'],r['kind'],r['addr'],r['cuisine'],oh,'OSM' if oh else '',out,f.get('schild',''),f.get('stimmung',''),f.get('status','offen'),f.get('quelle',r['website']),f.get('notiz','')])
print('rows',len(rows),'with facts',sum(1 for r in rows if r['osm'] in facts))
