"""Build all Kreis 9/3 landmark GLBs, compress with gltfpack and write pipeline/overrides/landmarks_k93.json.
Run: .venv/bin/python pipeline/landmarks/k93_all.py"""
import sys, os, json, subprocess, shutil
import numpy as np
from shapely.geometry import Polygon, Point
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import k93_find as F, terrain
ROOT = F.ROOT; D = ROOT + "/web/public/models/landmarks/"
for s in ("k93_altstetten.py", "k93_kirchen.py", "k93_wiedikon.py", "k93_sihlfeld.py", "k93_graves.py"):
    subprocess.run([sys.executable, os.path.join(HERE, s)], check=True)

def hide_pts(ids, near):
    out = []
    for i in ids:
        o = [o for o in F.near(*near[i], 40) if o["id"][3:11] == i or o["id"].startswith("ID_" + i)][0]
        best = None
        for k, q in o["polys"]:
            if k == 0 and len(q) >= 3:
                pg = Polygon(q[:, :2]).buffer(0)
                if pg.area > 0.5 and (best is None or pg.area > best.area): best = pg
        pt = best.representative_point(); out.append([round(pt.x, 1), round(pt.y, 1)])
    return out

def gz(x, y):
    return round(float(terrain.heights((x - 20, y - 20, x + 20, y + 20), 2.0, z_shift=-3.06).at(x, y)), 2)

NEAR = {"C1FCBE2D": (-970, -165), "6F9D632D": (-2082, 738), "3A9B8AC4": (-2106, 788), "96D18134": (-2388, 254), "82C92B3A": (-2425, 245), "756BF729": (457, -1185), "BE5BEAB6": (544, -1403), "52331290": (-703, -761), "212CBA16": (-718, -776), "CFDCE1DD": (-729.5, -766.5), "086A0A17": (-740, -788), "8CEA5295": (-679.2, -757.7)}
SITES = [
    ("Bahnhof Altstetten (Hochhaus, IBM-Stengel)", "k93_altstetten.glb", (-2082.0, 738.0), ["6F9D632D", "3A9B8AC4"]),
    ("Alte Kirche und Kirche Altstetten", "k93_kirche_altstetten.glb", (-2405.0, 250.0), ["96D18134", "82C92B3A"]),
    ("Dreifaltigkeitskirche Wiedikon", "k93_dreifaltigkeit.glb", (457.0, -1185.0), ["756BF729"]),
    ("Bahnhof Wiedikon (Reiterbahnhof)", "k93_wiedikon.glb", (544.1, -1403.4), ["BE5BEAB6"]),
    ("Altes Krematorium Sihlfeld, Haupttor, Kapellen", "k93_krematorium.glb", (-704.0, -757.0), ["52331290", "212CBA16", "CFDCE1DD", "086A0A17", "8CEA5295"]),
    ("Loewenbrunnen Schmiede Wiedikon", "k93_schmiede.glb", (314.2, -1561.5), []),
    ("Friedhof Sihlfeld Grabfelder", "k93_graves.glb", (-760.0, -830.0), []),
]
# OSM building ways that the build re-adds after hiding swissBUILDINGS3D footprints (osm_buildings.update): hide them explicitly
OSM_HIDE = {"Stadion Letzigrund": [1274254437, 1274254438, 1274254439, 1274254440, -22495740],
            "Altes Krematorium Sihlfeld, Haupttor, Kapellen": [211144771, 37007820, 212107152, 212107150, 36997317]}
import sources, osm_buildings
_n, _e = sources.osm(); OSMFP = {oid: g for oid, g, t in osm_buildings._osm_footprints(_n, _e)}

def osm_hide(name, swiss_pts):
    pts = []
    fps = [Polygon(p) for p in []]
    for oid, g in OSMFP.items():
        explicit = oid in OSM_HIDE.get(name, [])
        auto = any(g.buffer(0.5).contains(Point(*p)) for p in swiss_pts)   # an OSM footprint over a hidden swiss building
        if explicit or auto: pts.append([round(g.representative_point().x, 1), round(g.representative_point().y, 1)])
    return pts

lm = []
for name, f, (x, y), ids in SITES:
    src = D + f; tmp = D + "_tmp.glb"
    r = subprocess.run(["npx", "-y", "gltfpack", "-cc", "-i", src, "-o", tmp], capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(tmp): shutil.move(tmp, src)
    else: print("gltfpack failed", f, r.stderr[-200:])
    lm.append({"name": name, "model": "/models/landmarks/" + f, "x": x, "y": y, "z": gz(x, y), "heading": 0, "hide": (lambda h: h + [p for p in osm_hide(name, h) if p not in h])(hide_pts(ids, NEAR))})
    print(f, os.path.getsize(src) // 1024, "kB", lm[-1]["z"], lm[-1]["hide"])
json.dump({"landmarks": lm}, open(ROOT + "/pipeline/overrides/landmarks_k93.json", "w"), indent=1, ensure_ascii=False)
