"""Address -> building mapping and image selection (K best Mapillary images per target building).
Outputs research/autofacade/targets.json (addr -> building idx, zone, in_val) and data/raw/autofacade/sel.json (building idx -> [image ids]),
data/raw/autofacade/imgs_needed.json (id -> url).
Usage: python select_imgs.py [K]"""
import glob
import json
import math
import pickle
import sys
from datetime import datetime, timezone

import numpy as np
from scipy.spatial import cKDTree
from shapely import STRtree
from shapely.geometry import Point

from common import CACHE, OUT, ROOT, ZONES, ll2xy


def in_zone(x, y):
    for z, (x0, y0, x1, y1) in ZONES.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return z
    return 0


def load_meta():
    ims = {}
    for f in glob.glob(str(CACHE / "meta" / "*.json")):
        for im in json.load(open(f)):
            if im.get("is_pano") or im.get("camera_type") != "perspective" or not im.get("computed_geometry") or not im.get("camera_parameters"):
                continue
            if not im.get("thumb_1024_url"):
                continue
            ims[im["id"]] = im
    return ims


def is_night(ts):
    d = datetime.fromtimestamp(ts / 1000, timezone.utc)
    h = (d.hour + (2 if 4 <= d.month <= 10 else 1)) % 24
    return h >= 19 or h < 7


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    G = pickle.load(open(CACHE / "geom.pkl", "rb"))
    B = G["b"]
    tree = STRtree([b["fp"] for b in B])
    notes = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    gwr = json.load(open(ROOT / "data/build/gwr_kreise.json"))
    tg = {}
    for g in gwr:
        z = in_zone(g["x"], g["y"])
        if not z:
            continue
        addr = f"{g['street']} {g['nr']}"
        p = Point(g["x"], g["y"])
        i = int(tree.nearest(p))
        d = B[i]["fp"].distance(p)
        if d > 8:
            continue
        tg[addr] = dict(b=i, zone=z, d=round(d, 1), hand=bool(isinstance(notes.get(addr), dict) and notes[addr].get("hex")))
    for z in (1, 4):
        for a, v in json.load(open(ROOT / f"research/zones/zone{z}_facades.json"))["entries"].items():
            if a in tg or not v.get("xy"):
                continue
            p = Point(*v["xy"])
            i = int(tree.nearest(p))
            if B[i]["fp"].distance(p) <= 8:
                tg[a] = dict(b=i, zone=z, d=round(B[i]["fp"].distance(p), 1), hand=True)
    json.dump(tg, open(OUT / "targets.json", "w"), ensure_ascii=False)
    print("targets", len(tg), "hand", sum(v["hand"] for v in tg.values()), "buildings", len({v["b"] for v in tg.values()}))

    ims = load_meta()
    ids = list(ims)
    pos = np.array([ll2xy(*ims[i]["computed_geometry"]["coordinates"]) for i in ids])
    hd = np.array([ims[i].get("computed_compass_angle", ims[i].get("compass_angle", 0)) for i in ids])
    yr = np.array([datetime.fromtimestamp(ims[i]["captured_at"] / 1000, timezone.utc).year for i in ids])
    night = np.array([is_night(ims[i]["captured_at"]) for i in ids])
    kd = cKDTree(pos)
    sel = {}
    need = set()
    for bi in sorted({v["b"] for v in tg.values()}):
        b = B[bi]
        c = np.array(b["c"])
        cand = []
        for j in kd.query_ball_point(c, 55):
            if night[j] or yr[j] < 2017:
                continue
            p = Point(*pos[j])
            if b["fp"].contains(p):
                continue
            d = b["fp"].distance(p)
            if d < 5 or d > 40:
                continue
            ang = math.degrees(math.atan2(c[0] - pos[j][0], c[1] - pos[j][1])) % 360
            diff = abs((ang - hd[j] + 180) % 360 - 180)
            if diff > 35:
                continue
            cand.append((d * 0.4 + diff * 0.5 + max(0, 2023 - yr[j]) * 1.0, j))
        cand.sort()
        ch = []
        for s, j in cand:
            if all(np.hypot(*(pos[j] - pos[k])) > 7 or abs((hd[j] - hd[k] + 180) % 360 - 180) > 25 for k in ch):
                ch.append(j)
            if len(ch) >= K:
                break
        sel[bi] = [ids[j] for j in ch]
        need.update(sel[bi])
    json.dump(sel, open(CACHE / "sel.json", "w"))
    json.dump({i: ims[i]["thumb_1024_url"] for i in need}, open(CACHE / "imgs_needed.json", "w"))
    json.dump({i: {k: ims[i].get(k) for k in ("computed_geometry", "computed_compass_angle", "camera_parameters", "width", "height", "captured_at")} for i in need}, open(CACHE / "imgs_pose.json", "w"))
    n0 = sum(1 for v in sel.values() if not v)
    print("buildings with sel", len(sel) - n0, "without", n0, "images", len(need))


if __name__ == "__main__":
    main()
