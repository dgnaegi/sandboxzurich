"""SWISSIMAGE 10 cm reference crops (swisstopo OGD, free use with source credit) for street audits.

Cut-outs are fetched from the swisstopo WMS (layer ch.swisstopo.images-swissimage, EPSG:2056) per control
point and cached in data/raw/ortho/ as ortho_<name>.jpg (160 m window, 0.1 m/px -> 1600 px).
Local metres: LV95 E = 2681400 + x, N = 1248700 + y.

  python pipeline/ortho.py            # fetch all control points (throttled, cached)
  python pipeline/ortho.py list       # print resolved points
Sources: swisstopo SWISSIMAGE (OGD), see docs/DATA_SOURCES.md.
"""
import json
import sys
import time
from collections import defaultdict

import requests

from config import ROOT

OUT = ROOT / "data" / "raw" / "ortho"
WIN = 160.0
WMS = "https://wms.geo.admin.ch/"
# control points: name -> (street A, street B) junction in OSM, or explicit (x, y) in local metres
POINTS = {
    "helvetiaplatz": ("Badenerstrasse", "Langstrasse"),
    "stauffacher": ("Stauffacherstrasse", "Badenerstrasse"),
    "langstrasse_zwingli": ("Langstrasse", "Zwinglistrasse"),
    "hohlstrasse_langstrasse": ("Hohlstrasse", "Langstrasse"),
    "militaerstrasse_langstrasse": ("Militärstrasse", "Langstrasse"),
    "hardbruecke": ("Hardbrücke", "Hardstrasse"),
    "wiedikon": ("Birmensdorferstrasse", "Seebahnstrasse"),
    "lindenplatz": ("Lindenplatz", None),
    "limmatplatz": ("Limmatplatz", None),
    "albisriederplatz": ("Albisriederstrasse", "Badenerstrasse"),
    "josefstrasse_hardstr": ("Josefstrasse", "Hardstrasse"),
    "seebahnstrasse_kalkbreite": ("Seebahnstrasse", "Kalkbreitestrasse"),
    "birmensdorferstrasse_weststrasse": ("Birmensdorferstrasse", "Weststrasse"),
    "quartier_kernstr": ("Kernstrasse", "Stauffacherstrasse"),
    "escher_wyss": ("Hardstrasse", "Pfingstweidstrasse"),
    "bahnhof_hardbruecke": ("Bahnhof Hardbrücke", None),
    "kalkbreite": ("Kalkbreitestrasse", "Badenerstrasse"),
    "zweierstrasse": ("Zweierstrasse", "Badenerstrasse"),
    "seebahn_badener": ("Seebahnstrasse", "Badenerstrasse"),
    "sihlfeld_badener": ("Sihlfeldstrasse", "Badenerstrasse"),
    "langstrasse_dienerstr": ("Langstrasse", "Dienerstrasse"),
    "langstrasse_roentgen": ("Langstrasse", "Röntgenstrasse"),
    "idaplatz": ("Idaplatz", "Zurlindenstrasse"),
    "birmensdorfer_zurlinden": ("Birmensdorferstrasse", "Zurlindenstrasse"),
}


def junctions():
    """name pair -> list of (x, y) where ways with both names share a node (local metres)."""
    sys.path.insert(0, str(ROOT / "pipeline"))
    import sources
    nodes, els = sources.osm()
    by_node = defaultdict(set)
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and "highway" in t and t.get("name"):
            for n in e["nodes"]:
                by_node[n].add(t["name"])
    return nodes, by_node


def resolve():
    nodes, by_node = junctions()
    out = {}
    for k, v in POINTS.items():
        if isinstance(v[0], (int, float)):
            out[k] = v
            continue
        a, b = v
        c = [nodes[n] for n, s in by_node.items() if a in s and (b is None or b in s) and n in nodes]
        if c and b is None:
            c = c[:1]
        if c:
            out[k] = (sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c))
        else:
            print("not found:", k, v)
    return out


def fetch(name, x, y, win=WIN, px=1600):
    f = OUT / f"ortho_{name}.jpg"
    if f.exists():
        return f
    OUT.mkdir(parents=True, exist_ok=True)
    e0, n0 = 2681400 + x - win / 2, 1248700 + y - win / 2
    p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "ch.swisstopo.images-swissimage",
         "STYLES": "", "SRS": "EPSG:2056", "BBOX": f"{e0},{n0},{e0 + win},{n0 + win}", "WIDTH": px, "HEIGHT": px,
         "FORMAT": "image/jpeg"}
    r = requests.get(WMS, params=p, timeout=90, headers={"User-Agent": "gtazurich-audit/1.0 (research)"})
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(r.text[:200])
    f.write_bytes(r.content)
    time.sleep(1.5)  # throttle
    return f


def sheet(names, out, crop=120.0, px=760):
    """Contact sheet: one row per point, game render (left) next to the orthophoto (right)."""
    from PIL import Image, ImageDraw
    rows = []
    for n in names:
        g, o = ROOT / "data" / "build" / "ortho_game" / f"{n}.png", OUT / f"ortho_{n}.jpg"
        if not (g.exists() and o.exists()):
            continue
        gi = Image.open(g).convert("RGB").resize((px, px), Image.LANCZOS)
        oi = Image.open(o).convert("RGB")
        m = int(oi.width * (1 - crop / WIN) / 2)
        oi = oi.crop((m, m, oi.width - m, oi.height - m)).resize((px, px), Image.LANCZOS)
        r = Image.new("RGB", (px * 2 + 6, px), "white")
        r.paste(gi, (0, 0)); r.paste(oi, (px + 6, 0))
        ImageDraw.Draw(r).text((8, 8), f"{n}  game | SWISSIMAGE", fill="red")
        rows.append(r)
    if rows:
        s = Image.new("RGB", (rows[0].width, sum(r.height + 4 for r in rows)), "white")
        y = 0
        for r in rows:
            s.paste(r, (0, y)); y += r.height + 4
        s.save(out, quality=85)
    return len(rows)


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "sheet":
    print(sheet(sys.argv[3:], sys.argv[2]))
    sys.exit()

if __name__ == "__main__":
    pts = resolve()
    json.dump(pts, open(OUT.parent.parent / "build" / "ortho_points.json", "w"), indent=1)
    for k, (x, y) in pts.items():
        print(f"{k:34s} {x:9.1f} {y:9.1f}")
        if len(sys.argv) < 2 or sys.argv[1] != "list":
            fetch(k, x, y)
