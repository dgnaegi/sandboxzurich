"""Zuerich HB track / platform table -> research/hb/tracks.json (local metres), from OSM platform relations + SBB open data (perron).
Frame: d along the tracks toward the head end (angle -21 deg), c across (to the north-east). Numbering: Perron X/Y has track X on its south-west
side, track Y on its north-east side; Aussenperron 3 lies south-west of track 3, Aussenperron 18 north-east of track 18."""
import json, sys, math
import numpy as np
sys.path.insert(0, '/Users/danielgnagi/sandboxzurich/pipeline')
import sources
ROOT = '/Users/danielgnagi/sandboxzurich/'
TH = math.radians(-21); D = np.array([math.cos(TH), math.sin(TH)]); Cc = np.array([-math.sin(TH), math.cos(TH)])
nodes, els = sources.osm()
ways = {e['id']: e for e in els if e['type'] == 'way'}
out = {'frame': {'angle_deg': -21, 'note': 'x=d*cos+c*(-sin); d toward the head end (east-south-east), c to the north-east'}, 'platforms': [], 'tracks': []}


def poly_of(ids):
    pts = []
    for i in ids:
        w = ways.get(i)
        if w: pts += [nodes[n] for n in w['nodes'] if n in nodes]
    return np.array(pts)


def add(ref, level, a, src):
    dd, cc = a @ D, a @ Cc
    dmax = dd.max(); sel = dd > dmax - 6
    c0, c1 = cc[sel].min(), cc[sel].max()
    # width of the platform at the head = c1-c0 (nose); use the central part for edges
    mid = (dd > dmax - 120) & (dd < dmax - 30)
    e0, e1 = (cc[mid].min(), cc[mid].max()) if mid.any() else (c0, c1)
    P = lambda d, c: np.round(d * D + c * Cc, 1).tolist()
    out['platforms'].append({'ref': ref, 'level': level, 'src': src, 'head_d': round(float(dmax), 1), 'edge_sw_c': round(float(e0), 1), 'edge_ne_c': round(float(e1), 1),
                             'head_corner_sw': P(dmax, e0), 'head_corner_ne': P(dmax, e1), 'head_centre': P(dmax, (e0 + e1) / 2),
                             'width_m': round(float(e1 - e0), 1)})


for e in els:
    t = e.get('tags', {})
    if e['type'] == 'relation' and t.get('railway') == 'platform' and t.get('ref') and t.get('type') == 'multipolygon':
        a = poly_of([m['ref'] for m in e['members'] if m['role'] == 'outer' and m['type'] == 'way'])
        if len(a) and 1400 < a[:, 0].mean() < 1900 and -800 < a[:, 1].mean() < -400: add(t['ref'], t.get('level', '0'), a, f'osm relation {e["id"]}')
    elif e['type'] == 'way' and t.get('railway') == 'platform' and t.get('ref') == '3' and t.get('level') == '0':
        a = np.array([nodes[n] for n in e['nodes'] if n in nodes]); add('3', '0', a, f'osm way {e["id"]}')
for p in out['platforms']:
    refs = p['ref'].split(';'); lvl = p['level']
    w = p['width_m']
    for k, r in enumerate(refs):
        if len(refs) == 2:
            c = p['edge_sw_c'] - 1.9 if k == 0 else p['edge_ne_c'] + 1.9
        else:  # Aussenperron: track 3 on the north-east side of perron 3, track 18 on the south-west side of perron 18
            c = p['edge_ne_c'] + 1.9 if r == '3' else p['edge_sw_c'] - 1.9
        out['tracks'].append({'track': int(r), 'level': lvl, 'c': round(float(c), 1), 'head_d': p['head_d'],
                              'buffer_stop': np.round(p['head_d'] * D + c * Cc, 1).tolist(), 'platform': p['ref']})
out['tracks'].sort(key=lambda t: (t['level'] != '0', t['track']))
out['platforms'].sort(key=lambda t: (t['level'] != '0', t['ref']))
sbb = json.load(open(ROOT + 'data/raw/sbb/hb_records.json'))
out['sbb_perron'] = [{k: r.get(k) for k in ('bps_name', 'perrontyp', 'p_nr', 'p_lange', 'perronflach_brutto_m2')} for r in sbb['perron']]
out['sbb_langshallen'] = sorted({(r['kundengleisnummer'], r['montage_an']) for r in sbb['sektortafel'] if r['bps_name'] == 'Zurich HB' and 'Langshalle' in r['montage_an']}, key=lambda x: int(x[0]) if x[0].isdigit() else 0)
json.dump(out, open(ROOT + 'research/hb/tracks.json', 'w'), indent=1, ensure_ascii=False)
for p in out['platforms']: print(p['ref'], p['level'], p['head_d'], p['edge_sw_c'], p['edge_ne_c'], p['width_m'], p['head_centre'])
print(len(out['tracks']), 'tracks;', out['sbb_langshallen'][:30])

# ---- OSM rail ends near the platform heads (buffer stops) -> osm_rail_ends
ends = []
for e in els:
    t = e.get('tags', {})
    if e['type'] == 'way' and t.get('railway') == 'rail' and not t.get('tunnel') and t.get('service') in (None, 'yard'):
        pts = np.array([nodes[n] for n in e['nodes'] if n in nodes])
        if len(pts) < 2: continue
        dd = (pts - np.array([1760.0, -650.0])) @ D; cc = (pts - np.array([1760.0, -650.0])) @ Cc
        i = int(np.argmax(dd))
        if -75 < dd[i] < -30 and -85 < cc[i] < 70:
            ends.append({'osm_way': e['id'], 'd': round(float(dd[i]), 1), 'c': round(float(cc[i]), 1), 'xy': np.round(pts[i], 1).tolist(), 'ref': t.get('ref')})
ends.sort(key=lambda r: r['c'])
out['osm_rail_ends'] = ends
json.dump(out, open(ROOT + 'research/hb/tracks.json', 'w'), indent=1, ensure_ascii=False)
print(len(ends), 'OSM rail ends at the heads;', [(r['c'], r['d']) for r in ends][:20])
