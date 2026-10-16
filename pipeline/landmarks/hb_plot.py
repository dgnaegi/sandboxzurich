"""Plot OSM features around HB (PIL). usage: hb_plot.py x0 y0 x1 y1 out.png [px_per_m]"""
import json, sys
from PIL import Image, ImageDraw
x0, y0, x1, y1 = map(float, sys.argv[1:5]); out = sys.argv[5]; s = float(sys.argv[6]) if len(sys.argv) > 6 else 2.0
o = json.load(open('/Users/danielgnagi/sandboxzurich/research/hb/osm.json'))
W, H = int((x1 - x0) * s), int((y1 - y0) * s)
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
T = lambda p: ((p[0] - x0) * s, H - (p[1] - y0) * s)
for gx in range(int(x0 // 50 * 50), int(x1) + 1, 50):
    d.line([T((gx, y0)), T((gx, y1))], fill=(225, 225, 225)); d.text(T((gx + 1, y0 + 8)), str(gx), fill=(120, 120, 120))
for gy in range(int(y0 // 50 * 50), int(y1) + 1, 50):
    d.line([T((x0, gy)), T((x1, gy))], fill=(225, 225, 225)); d.text(T((x0 + 2, gy + 1)), str(gy), fill=(120, 120, 120))
for w in o:
    t = w['tags']; pts = [T(p) for p in w['pts']]
    if t.get('railway') == 'rail': d.line(pts, fill=(0, 0, 0), width=1)
    elif t.get('railway') == 'tram': d.line(pts, fill=(0, 150, 0), width=1)
    elif t.get('railway') == 'platform' or t.get('public_transport') == 'platform':
        d.line(pts, fill=(0, 0, 255), width=2)
        if t.get('ref'): d.text(pts[0], 'P' + t['ref'], fill=(0, 0, 255))
    elif 'indoor' in t: d.line(pts, fill=(255, 0, 0), width=1)
    elif 'building' in t: d.line(pts, fill=(110, 110, 110), width=1)
    elif 'highway' in t: d.line(pts, fill=(255, 150, 0), width=1)
pa = json.load(open('/Users/danielgnagi/sandboxzurich/data/build/playarea.json'))['polygon']
d.line([T(p) for p in pa], fill=(255, 0, 255), width=3)
im.save(out)
