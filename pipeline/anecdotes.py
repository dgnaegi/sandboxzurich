"""Turn research/easter_eggs_testarea.md into located anecdotes (only entries marked «heikel: nein»).
Location: «Strasse 12» via OSM addresses, else a named street/place/feature inside the area.
Output: web/public/data/anecdotes.json [{id, title, text, x, y, r}]."""
import json
import re

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box

import sources
from config import AREA, ROOT


def main():
    md = (ROOT / "research" / "easter_eggs_testarea.md").read_text()
    nodes, els = sources.osm()
    area = box(*AREA)
    addr, names = {}, {}
    for e in els:
        t = e.get("tags", {})
        pts = [nodes[e["id"]]] if e["type"] == "node" and e["id"] in nodes else [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if not pts:
            continue
        geom = Point(pts[0]) if len(pts) == 1 else (Polygon(pts) if pts[0] == pts[-1] and len(pts) > 3 else LineString(pts))
        if not geom.is_valid or not geom.intersects(area.buffer(80)):
            continue
        c = geom.representative_point() if geom.geom_type == "Polygon" else geom.interpolate(0.5, normalized=True) if geom.geom_type == "LineString" else geom
        if t.get("addr:street") and t.get("addr:housenumber"):
            addr[f"{t['addr:street']} {t['addr:housenumber']}".lower()] = (c.x, c.y)
        if t.get("name"):
            names.setdefault(t["name"].lower(), []).append((c.x, c.y))
    places = json.load(open(ROOT / "pipeline" / "overrides" / "anecdote_places.json"))["places"]
    out = []
    for block in re.split(r"\n### ", md)[1:]:
        title = block.split("\n", 1)[0].split(". ", 1)[-1].strip()
        heikel = re.search(r"\*\*heikel:\*\*\s*(\w+)", block)
        if not heikel or heikel.group(1).lower() != "nein":
            continue
        ort = (re.search(r"\*\*Ort:\*\*\s*(.+)", block) or [None, ""])[1]
        idea = (re.search(r"\*\*Spiel-Idee:\*\*\s*(.+)", block) or [None, ""])[1]
        q = re.search(r"«([^»]{8,})»", idea)
        if not q:
            continue
        pos, r = None, 14
        for m in re.finditer(r"([A-ZÄÖÜ][\wäöüé-]+(?:strasse|gasse|platz|weg|anlage|areal))\s+(\d+[a-z]?)", ort):
            pos = addr.get(f"{m.group(1)} {m.group(2)}".lower())
            if pos:
                r = 9
                break
        if not pos:  # named street / place / feature, pick the occurrence closest to the area centre
            cx, cy = (AREA[0] + AREA[2]) / 2, (AREA[1] + AREA[3]) / 2
            for word in re.findall(r"[A-ZÄÖÜ][\wäöüé-]+(?:\s[A-ZÄÖÜ][\wäöüé-]+)?", ort):
                cand = [p for p in names.get(word.lower(), []) if area.contains(Point(p))]
                if cand:
                    pos = min(cand, key=lambda p: np.hypot(p[0] - cx, p[1] - cy))
                    r = 20
                    break
        ov = next((v for k, v in places.items() if title.startswith(k)), None)
        if isinstance(ov, dict):
            pos, r = addr.get(ov["addr"].lower()), ov.get("r", 12)
            if not pos:
                continue  # verified address not found in OSM: drop rather than guess
        elif ov:
            pos, r = (ov[0], ov[1]), ov[2]
        if not pos:
            continue
        if any(np.hypot(pos[0] - o["x"], pos[1] - o["y"]) < 12 for o in out):
            continue  # no shared default points: without an own, certain position the anecdote is dropped
        title = title.replace("«", "").replace("»", "")  # the HUD font has no guillemets
        out.append({"id": f"a{len(out)}", "title": title[:60], "text": q.group(1), "x": round(pos[0], 1), "y": round(pos[1], 1), "r": r})
    # official street-name explanations (Strassennamenverzeichnis + Widmungstafeln, Stadt Zürich OGD, CC0)
    raw = ROOT / "data" / "raw" / "stadtzh_more"
    expl = {}
    for ft in json.load(open(raw / "geo_strassennamenverzeichnis__sv_str_lin.geojson"))["features"]:
        pr = ft["properties"]
        if pr.get("snb_erlaeuterung") and pr["snb_erlaeuterung"] != "None":
            expl[pr["str_name"]] = pr["snb_erlaeuterung"].strip()
    for ft in json.load(open(raw / "geo_widmungstafel__v_widmungstafel_geoserver.geojson"))["features"]:
        pr = ft["properties"]
        if pr.get("strasse") and pr.get("widmungstext"):
            expl.setdefault(pr["strasse"], " ".join(pr["widmungstext"].split()))
    done = set()
    for e in els:
        t = e.get("tags", {})
        nm = t.get("name")
        if e["type"] != "way" or "highway" not in t or nm not in expl or nm in done:
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) < 2:
            continue
        ln = LineString(pts)
        if not area.contains(ln.interpolate(0.5, normalized=True)):
            continue
        done.add(nm)
        txt = expl[nm]
        txt = txt if len(txt) <= 230 else txt[:227].rsplit(" ", 1)[0] + " …"
        c = ln.interpolate(0.5, normalized=True)
        out.append({"id": f"s{len(done)}", "kind": "street", "title": nm, "text": txt, "x": round(c.x, 1), "y": round(c.y, 1), "r": 10})
    json.dump({"anecdotes": out}, open(ROOT / "web" / "public" / "data" / "anecdotes.json", "w"), ensure_ascii=False, indent=0)
    print(len(out), "anecdotes located,", len(done), "street names")


if __name__ == "__main__":
    main()
