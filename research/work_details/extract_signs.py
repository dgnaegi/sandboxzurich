import json, glob, csv, collections, os
ROOT='/Users/danielgnagi/gtazurich'
signs={}
for f in sorted(glob.glob(f'{ROOT}/web/public/tiles/t_*.json')):
    d=json.load(open(f))
    tile=os.path.basename(f)[2:-5]
    for s in d.get('signs',[]):
        key=(s.get('osm'), s.get('name'))
        if key not in signs:
            signs[key]=dict(s, tile=tile)
rows=sorted(signs.values(), key=lambda s:(s.get('kind') or '', s.get('name') or ''))
out=f'{ROOT}/research/work_details/signs_raw.csv'
with open(out,'w',newline='') as fh:
    w=csv.writer(fh)
    w.writerow(['name','kind','osm','x','y','z','w','tile'])
    for s in rows:
        w.writerow([s.get('name'),s.get('kind'),s.get('osm'),s.get('x'),s.get('y'),s.get('z'),s.get('w'),s.get('tile')])
print('total unique signs', len(rows))
print(collections.Counter(s.get('kind') for s in rows).most_common(30))
print('with osm', sum(1 for s in rows if s.get('osm')))
