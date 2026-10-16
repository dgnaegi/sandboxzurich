"""Horizon ridge profile + tower impostor list from swissALTI3D -> web/public/data/skyline.json.
Per 1 degree azimuth (seen from the local origin) the highest-angle terrain point in distance bands.
Layers: near (1.2-4 km), far (4-12 km), all (max of both; phones draw only this one)."""
import glob, json, math, re
import numpy as np
from PIL import Image

ORI = (2681400.0, 1248700.0); Z0 = 408.0; BLK = 40   # 0.5 m px -> 20 m cells
tiles = {}
for f in glob.glob('data/raw/alti3d/swissalti3d_*_0.5_*.tif'):
    m = re.search(r'_(\d{4})-(\d{4})_0\.5', f)
    a = np.asarray(Image.open(f), dtype=np.float32)
    a = np.where(a < -1000, np.nan, a)
    a = np.nanmean(a.reshape(2000 // BLK, BLK, 2000 // BLK, BLK), axis=(1, 3))
    tiles[(int(m[1]), int(m[2]))] = a
xs = [k[0] for k in tiles]; ys = [k[1] for k in tiles]
x0, y0 = min(xs), min(ys); nx, ny = max(xs) - x0 + 1, max(ys) - y0 + 1
n = 2000 // BLK; cell = 1000.0 / n
G = np.full((ny * n, nx * n), np.nan, np.float32)
for (tx, ty), a in tiles.items():
    # tile name = lower-left corner (km); raster rows run north -> south
    r = (y0 + ny - 1 - ty) * n; c = (tx - x0) * n
    G[r:r + n, c:c + n] = a
def elev(E, N):
    c = int((E - x0 * 1000) / cell); r = int(((y0 + ny) * 1000 - N) / cell)
    if 0 <= r < G.shape[0] and 0 <= c < G.shape[1]: return float(G[r, c])
    return float('nan')

bands = {'near': (1200, 4000), 'far': (4000, 12000)}
out = {'near': [], 'far': [], 'all': [], 'towers': []}
for az in range(360):
    s, co = math.sin(math.radians(az)), math.cos(math.radians(az))   # az 0 = north, 90 = east
    best = {}
    for name, (d0, d1) in bands.items():
        b = (-9, 0, 0, 0)
        d = d0
        while d < d1:
            e = elev(ORI[0] + s * d, ORI[1] + co * d)
            if e == e:
                ang = math.atan2(e - Z0 - 1.7, d)
                if ang > b[0]: b = (ang, s * d, co * d, e - Z0)
            d += 20
        best[name] = b
    for k in ('near', 'far'): out[k].append([round(best[k][1]), round(best[k][2]), round(best[k][3], 1)])
    m = max(best.values(), key=lambda t: t[0])
    out['all'].append([round(m[1]), round(m[2]), round(m[3], 1)])
# fill gaps (no data): copy neighbour
for k in ('near', 'far', 'all'):
    arr = out[k]
    for i, v in enumerate(arr):
        if v[0] == 0 and v[1] == 0:
            arr[i] = arr[i - 1]

# tower impostors: x, y(north), height above ground, width.  Landmark positions from landmarks.json.
T = [('Prime Tower', 45.0, 222.6, 126, 38), ('Hardau II', -516.5, -321.0, 95, 70), ('Mobimo Tower', -181.5, 447.4, 81, 28),
     ('Swissmill', 778.4, 624.7, 118, 30), ('Pfingstweid', -492.6, 725.5, 81, 28), ('Migros Limmatplatz', 1128.6, 187.8, 60, 40),
     ('James', -1584.2, -300.3, 62, 30), ('Altstetten', -2082.0, 738.0, 85, 30),
     ('ETH Hauptgebaeude', 1650.0, -820.0, 38, 130), ('Universitaet', 1740.0, -980.0, 42, 120)]
for nm, x, y, h, w in T:
    e = elev(ORI[0] + x, ORI[1] + y)
    out['towers'].append({'n': nm, 'x': x, 'y': y, 'g': round(float(e) - Z0 if e == e else 0, 1), 'h': h, 'w': w})
# Uetliberg tower on the highest cell in the SW quadrant
best = (0, 0, 0)
for d in range(1500, 6000, 20):
    for az in range(180, 280, 1):
        e = elev(ORI[0] + math.sin(math.radians(az)) * d, ORI[1] + math.cos(math.radians(az)) * d)
        if e == e and e > best[0]: best = (e, math.sin(math.radians(az)) * d, math.cos(math.radians(az)) * d)
out['towers'].append({'n': 'Uetliberg Turm', 'x': round(best[1]), 'y': round(best[2]), 'g': round(float(best[0]) - Z0, 1), 'h': 30, 'w': 5})
json.dump(out, open('web/public/data/skyline.json', 'w'), separators=(',', ':'))
mx = max(out['all'], key=lambda v: v[2])
print('tiles', len(tiles), 'max ridge', mx, 'uetli', out['towers'][-1])
