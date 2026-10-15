import csv, sys, json
R='/Users/danielgnagi/gtazurich/research/pois_kreis5.csv'
rows=json.load(open(sys.argv[1],encoding='utf-8'))
with open(R,'a',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    for r in rows:
        w.writerow([r['osm_id'],r['name'],r['status'],r.get('new_name',''),r.get('address',''),r.get('source_url',''),'2026-10-14'])
print('appended',len(rows))
