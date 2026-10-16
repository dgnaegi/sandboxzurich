"""Overlay GWR address points on photo + game shot to read addresses of visible facades.
usage: fidelity_labels.py out_prefix ids...   (uses research/fidelity_cand.json, preview/fid_before)"""
import json, math, sys
from PIL import Image, ImageDraw
out, ids = sys.argv[1], [int(i) for i in sys.argv[2:]]
cand = {c['id']: c for c in json.load(open('research/fidelity_cand.json'))}
gwr = json.load(open('data/build/gwr_kreise.json'))
W, H = 800, 600
VF = math.radians(80); f = (H / 2) / math.tan(VF / 2)
def labels(c):
    hd = math.radians(c['heading']); fx, fy = math.sin(hd), math.cos(hd); rx, ry = fy, -fx
    res = []
    for g in gwr:
        dx, dy = g['x'] - c['x'], g['y'] - c['y']
        d = dx * fx + dy * fy
        if d < 6 or d > 70: continue
        r = dx * rx + dy * ry
        u = W / 2 + f * r / d
        if not 0 < u < W: continue
        h = (g.get('floors') or 4) * 3.0 * 0.5 - 1.6
        v = H / 2 - f * h / d
        res.append((d, u, v, g))
    res.sort(key=lambda t: t[0])
    return res
def draw(im, c):
    dr = ImageDraw.Draw(im); used = []
    for d, u, v, g in labels(c):
        if any(abs(u - a) < 70 and abs(v - b) < 14 for a, b in used): continue
        used.append((u, v)); v = min(max(v, 10), H - 10)
        dr.ellipse((u - 3, v - 3, u + 3, v + 3), fill=(255, 0, 0))
        dr.text((u + 5, v - 5), f"{g['street'][:14]} {g['nr']} {g.get('floors') or '?'}G", fill=(255, 255, 0))
    return im
for s in range(0, len(ids), 4):
    ch = ids[s:s + 4]; sh = Image.new('RGB', (2 * W, 2 * H))
    for j, i in enumerate(ch):
        c = cand[i]; im = Image.open(c['file']).convert('RGB').resize((W, H)); draw(im, c)
        ImageDraw.Draw(im).text((4, 4), f'#{i}', fill=(0, 255, 255))
        sh.paste(im, ((j % 2) * W, (j // 2) * H))
    sh.save(f'{out}_{s // 4 + 1}.jpg', quality=70)
