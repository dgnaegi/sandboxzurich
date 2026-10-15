# stdin lines: osm_id|status|new_name|address|source_url ; name taken from pois_kreis9_osm.csv
import csv, sys, datetime
OUT = '/Users/danielgnagi/gtazurich/research/pois_kreis9.csv'
OSM = '/Users/danielgnagi/gtazurich/research/pois_kreis9_osm.csv'
names = {r['osm_id']: r['name'] for r in csv.DictReader(open(OSM, encoding='utf-8'))}
today = datetime.date.today().isoformat()
rows = []
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    p = (line.split('|') + ['']*5)[:5]
    osm_id, status, new_name, address, src = p
    assert status in ('ok','closed','renamed','moved','unclear','new'), line
    rows.append([osm_id, names.get(osm_id, ''), status, new_name, address, src, today])
with open(OUT, 'a', encoding='utf-8', newline='') as f:
    csv.writer(f).writerows(rows)
print('appended', len(rows))
