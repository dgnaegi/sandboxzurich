"""Friedhof Sihlfeld: Grabfelder (Reihen von Grabsteinen, Hecken) als eine zusammengefasste Geometrie -> k93_graves.glb.
Flaechen: OSM-Friedhofspolygon ∩ AV-Gruen (Bodenbedeckung) minus Wege (OSM footway/path/service, 1.8 m), Gebaeude, Baeume (Kachel-Meta).
Reihenrichtung = vorherrschende Wegrichtung in der Naehe. Die Menge ist auf MAXN begrenzt (Download-Budget), nach Abstand zur Mitte gewaehlt."""
import sys, os, math, json, glob, random
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import prepared
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, sources, terrain, groundcover
from k93_lib import hexc, shade
OUT = F.ROOT + "/web/public/models/landmarks/k93_graves.glb"
CEN = (-760.0, -830.0)       # centre of the modelled area (south of the old crematorium)
R = float(os.environ.get("GRAVE_R", 150))
MAXN = int(os.environ.get("GRAVE_N", 7000))
random.seed(11); rng = np.random.default_rng(11)
nodes, els = sources.osm(); W = {e["id"]: e for e in els if e["type"] == "way"}
cem = Polygon([nodes[n] for n in W[10634343]["nodes"]]).buffer(0)
area = Point(*CEN).buffer(R).intersection(cem)
G = groundcover.load(tuple(area.bounds))
green = G["green"].intersection(area)
paths = []
for e in els:
    t = e.get("tags", {})
    if e["type"] == "way" and t.get("highway") in ("footway", "path", "service", "pedestrian", "track", "residential", "unclassified") and "nodes" in e:
        pts = [nodes[i] for i in e["nodes"] if i in nodes]
        if len(pts) > 1 and LineString(pts).intersects(area): paths.append(LineString(pts))
bld = []
for e in els:
    t = e.get("tags", {})
    if e["type"] == "way" and t.get("building") and "nodes" in e:
        pts = [nodes[i] for i in e["nodes"] if i in nodes]
        if len(pts) > 3:
            g = Polygon(pts).buffer(0)
            if g.intersects(area): bld.append(g)
excl = unary_union([p.buffer(2.0) for p in paths] + [b.buffer(4.0) for b in bld] + [G["plaza"].buffer(0.8), G["gravel"].buffer(0.8)])
field = green.difference(excl)
# tree positions from the game tiles
trees = []
for f in glob.glob(F.ROOT + "/web/public/tiles/t_*.json"):
    try: tr = json.load(open(f)).get("trees", [])
    except Exception: continue
    for q in tr:
        if abs(q[0] - CEN[0]) < R + 20 and abs(q[1] - CEN[1]) < R + 20: trees.append((q[0], q[1]))
tpts = unary_union([Point(*p).buffer(1.6) for p in trees]) if trees else Polygon()
field = field.difference(tpts).buffer(-0.5).buffer(0.5)
print("field m2", round(field.area), "paths", len(paths), "trees", len(trees))
# dominant path direction (mod 90 deg) near the centre
ang = []
for p in paths:
    cs = list(p.coords)
    for a, b in zip(cs[:-1], cs[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if d > 3: ang.append((math.atan2(b[1] - a[1], b[0] - a[0]) % (math.pi / 2), d))
if ang:
    z = sum(d * np.exp(4j * a) for a, d in ang); A0 = (np.angle(z) / 4) % (math.pi / 2)
else: A0 = 0.0
print("row angle", round(math.degrees(A0), 1))
ca, sa = math.cos(A0), math.sin(A0)
fp_ = prepared.prep(field)
cands = []
DX, DY = 1.25, 2.9
x0, y0, x1, y1 = field.bounds
# grid in the rotated frame
corn = [(CEN[0] - R, CEN[1] - R), (CEN[0] + R, CEN[1] - R), (CEN[0] + R, CEN[1] + R), (CEN[0] - R, CEN[1] + R)]
us = [(x - CEN[0]) * ca + (y - CEN[1]) * sa for x, y in corn]; vs = [-(x - CEN[0]) * sa + (y - CEN[1]) * ca for x, y in corn]
ui = np.arange(min(us), max(us), DX); vj = np.arange(min(vs), max(vs), DY)
for j, v in enumerate(vj):
    for i, u in enumerate(ui):
        x = CEN[0] + u * ca - v * sa; y = CEN[1] + u * sa + v * ca
        if not fp_.contains(Point(x, y)): continue
        if rng.random() < 0.10: continue            # empty plots
        cands.append((math.hypot(x - CEN[0], y - CEN[1]), x, y, i, j))
cands.sort()
cands = cands[:MAXN]
print("graves", len(cands))
# hedges between grave groups: every 7th row, along the row, only on field
H = terrain.heights((CEN[0] - R - 5, CEN[1] - R - 5, CEN[0] + R + 5, CEN[1] + R + 5), 2.0, z_shift=-3.06)
ZO = float(H.at(*CEN))
M = L.Model(origin=(CEN[0], CEN[1], 0.0))
S = M.mat("graves", rough=0.95)
GR = [hexc(c) for c in ("#8d8b86", "#a19d94", "#6e6c68", "#b3aea2", "#47494c", "#7a6f64", "#c3beb2", "#5c5f63")]
for d, x, y, i, j in cands:
    z = float(H.at(x, y)) - ZO
    r_ = random.Random(i * 7919 + j * 104729)
    h = r_.choice((0.55, 0.7, 0.85, 0.7, 1.0, 0.45)); w = r_.choice((0.45, 0.6, 0.7, 0.5)); t = 0.12
    col = r_.choice(GR)
    yaw = A0 + r_.uniform(-0.04, 0.04)
    M.box(S, (x, y, z + h / 2), (w, t, h), col, rot=yaw, top=shade(col, 1.12))
    # grave bed: low earth/gravel rectangle in front of the stone (1.0 x 1.7 m)
    bx, by = x - sa * (-1) * 0.0, y
    ox, oy = -math.sin(yaw + math.pi / 2) * 0, 0
    nx_, ny_ = -math.sin(yaw), math.cos(yaw)
    cx_, cy_ = x + nx_ * 1.0, y + ny_ * 1.0
    bc = r_.choice((hexc("#4f4034"), hexc("#5d564b"), hexc("#3f5a38"), hexc("#7b7364")))
    ca_, sa_ = math.cos(yaw), math.sin(yaw)
    P = lambda du, dv: (cx_ + du * ca_ - dv * sa_, cy_ + du * sa_ + dv * ca_, z + 0.05)
    M.quad(S, P(-0.47, -0.85), P(0.47, -0.85), P(0.47, 0.85), P(-0.47, 0.85), bc)
# hedges: strips along rows j % 7 == 0 inside the field
HG = hexc("#2f5a2c")
for j, v in enumerate(vj):
    if j % 7 != 0: continue
    ln = LineString([(CEN[0] + u * ca - (v + 1.45) * sa, CEN[1] + u * sa + (v + 1.45) * ca) for u in (min(us), max(us))])
    seg = ln.intersection(field.buffer(-0.3))
    for g in ([seg] if seg.geom_type == "LineString" else list(getattr(seg, "geoms", []))):
        if g.length < 4 or Point(*g.centroid.coords[0]).distance(Point(*CEN)) > R * 0.9: continue
        n = max(1, int(g.length / 2.5))
        for k in range(n):
            a = np.array(g.interpolate(k / n, normalized=True).coords[0]); b = np.array(g.interpolate((k + 1) / n, normalized=True).coords[0])
            m_ = (a + b) / 2
            M.box(S, (m_[0], m_[1], float(H.at(*m_)) - ZO + 0.4), (np.hypot(*(b - a)) + 0.05, 0.55, 0.8), shade(HG, random.uniform(0.85, 1.15)), rot=math.atan2(b[1] - a[1], b[0] - a[0]), top=shade(HG, 1.25))
os.makedirs(os.path.dirname(OUT), exist_ok=True); M.write(OUT)
print("graves tris", M.tris(), "origin", CEN, "z", round(ZO, 2))
