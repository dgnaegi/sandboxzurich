"""Extract OSM features around Zuerich HB -> research/hb/osm.json (local metres) + summary."""
import json, math, sys
import numpy as np
sys.path.insert(0, '/Users/danielgnagi/sandboxzurich/pipeline')
import sources
C = (1790, -640); R = 420
nodes, els = sources.osm()
out = []
for e in els:
    t = e.get('tags', {})
    if e['type'] != 'way': continue
    pts = [nodes[n] for n in e['nodes'] if n in nodes]
    if len(pts) < 2: continue
    m = np.mean(pts, axis=0)
    if math.hypot(m[0] - C[0], m[1] - C[1]) > R: continue
    keep = any(k in t for k in ('railway', 'building', 'public_transport', 'indoor', 'highway', 'platform', 'name'))
    if not keep: continue
    out.append({'id': e['id'], 'tags': t, 'pts': np.round(pts, 1).tolist()})
json.dump(out, open('/Users/danielgnagi/sandboxzurich/research/hb/osm.json', 'w'))
print(len(out))
for o in out:
    t = o['tags']
    if t.get('public_transport') in ('station',) or 'Hauptbahnhof' in t.get('name', '') or t.get('building') in ('train_station', 'roof') or t.get('railway') == 'platform':
        a = np.array(o['pts']); print(o['id'], {k: v for k, v in t.items() if k in ('name', 'ref', 'building', 'railway', 'public_transport', 'level', 'height', 'building:levels', 'layer', 'covered')}, len(a), a.min(0), a.max(0))
