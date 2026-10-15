import csv
done = {r['osm_id'] for r in csv.DictReader(open('/Users/danielgnagi/gtazurich/research/pois_kreis9.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open('/Users/danielgnagi/gtazurich/research/pois_kreis9_osm.csv', encoding='utf-8')))
todo = [r for r in rows if r['osm_id'] not in done]
import collections
print('total', len(rows), 'done', len(done), 'todo', len(todo))
print(collections.Counter(r['kind'] for r in todo).most_common(12))
def key(r):
    a = r['address'].lower()
    prio = 9
    for i, k in enumerate(['lindenplatz','bahnhof altstetten','altstetterstrasse','albisriederstrasse','albisriederplatz','hohlstrasse','badenerstrasse']):
        if k in a: prio = i; break
    return (prio, a)
todo.sort(key=key)
with open('/Users/danielgnagi/gtazurich/research/work_k9/todo.csv','w',encoding='utf-8',newline='') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(todo)
