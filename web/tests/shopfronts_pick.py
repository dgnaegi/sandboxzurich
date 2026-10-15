"""Pick annotated venues from rebuilt tiles for the comparison sheet -> logs/shopfronts_pick.json (run from repo root)."""
import json, math, sys, glob
L = {str(s['id']).lstrip('nwr'): s for s in json.load(open('research/shops_v3/shops_v3.json')) if s.get('photo_ok')}
out = []
for f in sorted(glob.glob('web/public/tiles/t_*.json')):
    m = json.load(open(f))
    for s in m.get('signs', []):
        r = L.get(str(s['osm']))
        if not r or 'v' not in s: continue
        ph = (r.get('photos_r2') or r.get('photos') or [None])[0]
        if not ph: continue
        v = s['v']
        score = (2 if v.get('a') else 0) + (2 if v.get('t') else 0) + (1 if v.get('p') else 0) + (1 if v.get('b') else 0) + (1 if v.get('s') in ('letters', 'box', 'neon') else 0) + (1 if s['w'] > 3 else 0)
        nx, ny = s['ty'], -s['tx']
        out.append(dict(name=s['name'], score=score, photo=ph['file'], x=s['x'], y=s['y'], nx=nx, ny=ny, v=v, pd=s.get('pd')))
out.sort(key=lambda o: -o['score'])
pick, seen = [], set()
for o in out:
    if o['name'] in seen: continue
    seen.add(o['name']); pick.append(o)
    if len(pick) >= 14: break
json.dump(pick, open('logs/shopfronts_pick.json', 'w'), ensure_ascii=False)
print(len(out), len(pick), [p['name'] for p in pick])
