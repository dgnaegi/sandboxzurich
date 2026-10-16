"""Photo | game | isolated-model comparison rows for the wave-4 landmarks -> preview/lm7_<id>.jpg and preview/lm7_all.jpg.
Usage: python k4w4_compare.py [id,id,...]   (game shot needs the dev server on :5173; tiles are NOT rebuilt, so the game may still show the old buildings)"""
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from common import ll, ROOT

PREV = ROOT / "preview"; WEB = ROOT / "web"
LM = {e["name"]: e for e in json.load(open(ROOT / "web/public/data/landmarks.json"))["landmarks"]}
M = json.load(open(ROOT / "research/v3/photos_k4w4.json"))
M["zw"] = json.load(open(ROOT / "research/v3/photos_k4w4_zw.json"))["zentralwaescherei"]
# id: (title, [(site, photo idx, target_h)])
SPECS = {
    "zentralwaescherei": ("Zentralwaescherei (Kulturhaus Neue Hard)", [("zw", 108, 9), ("zw", 78, 8), ("zw", 35, 7)]),
    "johanneskirche": ("Johanneskirche Limmatplatz", [("johanneskirche", 2, 18), ("johanneskirche", 10, 18)]),
    "limmathaus": ("Limmathaus Limmatplatz", [("limmathaus", 23, 10), ("limmathaus", 9, 10)]),
    "houdini": ("Block Kino Houdini Hohlstrasse", [("idaplatz_block", 10, 12), ("idaplatz_block", 4, 12)]),
    "langstrasse_blau": ("Langstrasse Eckhaus blau", [("langstrasse_nord", 9, 12), ("langstrasse_nord", 10, 12)]),
    "wiedikon_block": ("Wiedikon-Platz Wohn- und Geschaeftshaus", [("wiedikon_platz", 11, 14), ("wiedikon_platz", 2, 14)]),
    "roentgen_zeile": ("Roentgenstrasse Zeile Ocker", [("roentgen_zeile", 14, 9), ("roentgen_zeile", 1, 9)]),
    "docks": ("The Docks Langstrassen-Unterfuehrung", [("docks_langstrasse", 17, 9), ("docks_langstrasse", 16, 9)]),
    "swissmill_turm": ("Swissmill Tower Silo", [("swissmill", 7, 35), ("swissmill", 14, 35)]),
    "stadtmuehle": ("Stadtmuehle Swissmill Altbau", [("swissmill", 1, 12), ("swissmill", 7, 12)]),
    "stjoseph": ("Pfarrkirche St. Joseph Roentgenstrasse", [("st_joseph", 2, 14), ("st_joseph", 11, 14)]),
    "kw_letten": ("Wasserkraftwerk Letten", [("kw_letten", 10, 9)]),
    "james": ("James Hochhaus Albisrieden", [("james_hochhaus", 1, 15), ("james_hochhaus", 3, 15)]),
}


def cam_for(entry, ph, th):
    bx, by = entry["x"], entry["y"]
    if ph.get("heading") is None or ph["source"] == "commons":
        d = (-0.5, -0.86); dist = 55
        return (bx + d[0] * dist, by + d[1] * dist), (bx, by)
    x, y = ll(ph["lat"], ph["lon"])
    return (x, y), (bx, by)


def run(ids):
    for sid in ids:
        title, rows = SPECS[sid]; e = LM[title]; views = []; mviews = []
        for site, idx, th in rows:
            ph = M[site]["photos"][idx]; (cx, cy), (tx, ty) = cam_for(e, ph, th)
            if site == "zw" and idx in (108, 35, 78): tx, ty = {108: (259, 313), 35: (252, 320), 78: (334, 277)}[idx]
            if site == "zw" and idx == 35: cx, cy = 238.0, 306.0
            views.append(dict(p=[round(cx, 1), round(cy, 1), 1.9], l=[round(tx, 1), round(ty, 1), th], fov=55, t="12:00", w=640, hh=480, wait=6000))
            mviews.append(f"{cx - e['x']:.1f},{cy - e['y']:.1f},1.9,{tx - e['x']:.1f},{ty - e['y']:.1f},{th},55")
        subprocess.run(["node", str(ROOT / "pipeline/landmarks/free_shot.mjs"), str(PREV / f"_cmp_{sid}"), json.dumps(views)], cwd=WEB, capture_output=True, timeout=600)
        subprocess.run(["node", str(ROOT / "pipeline/landmarks/view_shot.mjs"), str(PREV / f"_cmpm_{sid}"), title, *mviews], cwd=WEB, capture_output=True, timeout=600)
        out = Image.new("RGB", (1920, 480 * len(rows)), (20, 20, 20))
        for i, (site, idx, th) in enumerate(rows):
            ph = M[site]["photos"][idx]
            a = Image.open(ROOT / ph["file"]).convert("RGB"); a.thumbnail((640, 480))
            out.paste(a, (0, i * 480))
            for k, f in enumerate((PREV / f"_cmp_{sid}_{i}.jpg", PREV / f"_cmpm_{sid}_{i}.jpg")):
                try: b = Image.open(f).convert("RGB").resize((640, 480)); out.paste(b, ((k + 1) * 640, i * 480))
                except Exception as ex: print("missing", f, ex)
            d = ImageDraw.Draw(out); d.rectangle([0, i * 480, 330, i * 480 + 16], fill=(0, 0, 0))
            d.text((4, i * 480 + 3), f"photo {site}#{idx} | game | model", fill=(255, 220, 0))
        out.save(PREV / f"lm7_{sid}.jpg", quality=84); print("lm7", sid)
        for f in PREV.glob(f"_cmp*_{sid}_*.jpg"): f.unlink()


def sheet():
    fs = sorted(PREV.glob("lm7_*.jpg")); fs = [f for f in fs if f.name != "lm7_all.jpg"]
    cols = 3; W = 1000; Hh = 340
    s = Image.new("RGB", (cols * W, ((len(fs) + cols - 1) // cols) * Hh), (20, 20, 20))
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGB"); im = im.crop((0, 0, im.width, min(im.height, 480))); im.thumbnail((W, Hh)); s.paste(im, ((i % cols) * W, (i // cols) * Hh))
    s.thumbnail((2400, 4000)); s.save(PREV / "lm7_all.jpg", quality=80); print("sheet", len(fs))


if __name__ == "__main__":
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "sheet" else list(SPECS)
    if not (len(sys.argv) > 1 and sys.argv[1] == "sheet"): run(ids)
    sheet()
