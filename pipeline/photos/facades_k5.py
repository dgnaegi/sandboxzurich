"""Kreis 5 / 3-West / 9 facade photos: Panoramax + Mapillary panos (frontal 360 crops) -> candidates_k5.json, contact sheets in sheets_k5/.
Own output files (no clash with candidates.json). Usage: facades_k5.py fetch | sheets"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shapely.geometry import Point, Polygon
sys.path.insert(0, str(Path(__file__).parent))
import facades_px as P  # noqa
import fetch_v3 as F  # noqa
import shops_r2_fetch as R  # noqa
from PIL import Image, ImageDraw, ImageFont

ROOT = F.ROOT
D = ROOT / "research/buildings/sheets_k5"; D.mkdir(exist_ok=True)
CAND = D / "candidates_k5.json"
STREETS = ("Limmatstrasse Josefstrasse Heinrichstrasse Ausstellungsstrasse Röntgenstrasse Klingenstrasse Konradstrasse Neugasse Hardstrasse Hardturmstrasse "
           "Pfingstweidstrasse Förrlibuckstrasse Birmensdorferstrasse Zurlindenstrasse Weststrasse Aemtlerstrasse Bremgartnerstrasse Goldbrunnenstrasse "
           "Schlossgasse Hohlstrasse Badenerstrasse Albisriederstrasse Herdernstrasse Eglistrasse Lindenplatz Altstetterstrasse").split()
def nrn(nr):
    n = "".join(c for c in nr if c.isdigit()); return int(n) if n else 0
def targets():
    poly = Polygon(json.load(open(ROOT / "data/build/playarea.json"))["polygon"])
    out = []
    for r in json.load(open(ROOT / "data/build/gwr_kreise.json")):
        s = r["street"]
        if s not in STREETS or not poly.contains(Point(r["x"], r["y"])): continue
        if s == "Hohlstrasse" and nrn(r["nr"]) <= 250: continue
        if s == "Badenerstrasse" and nrn(r["nr"]) < 200: continue
        if r["class"] in (1251, 1252) or (r["floors"] or 0) < 2 and (r["area"] or 0) < 150: continue
        out.append(dict(addr=f"{s} {r['nr']}", street=s, nr=r["nr"], x=r["x"], y=r["y"], year=r["year"], floors=r["floors"], period=r["period"], cls=r["class"], prio=STREETS.index(s)))
    out.sort(key=lambda t: (t["prio"], nrn(t["nr"]), t["nr"])); return out
TOK = None
def work(t):
    global TOK
    try:
        lat, lon = F.local_ll(t["x"], t["y"])
        imgs = list(P.px(lat, lon) or [])
        key = f"k5_{round(lat,4)}_{round(lon,4)}"
        imgs += R.mly(dict(id=key, lat=lat, lon=lon), TOK) or []
        b = P.pick(t, imgs)
        if not b: return t["addr"], None
        _, d, brg, diff, im = b
        f = R.source(im)
        if f is None: return t["addr"], None
        if im["pano"]: c = R.crop(f, brg, im["az"], fov=75, W=640, H=640)
        else: c = R.flat(f, (brg - im["az"] + 180) % 360 - 180, hfov=75, W=640).crop((0, 0, 640, 480)).resize((640, 640))
        slug = t["addr"].replace(" ", "_").replace("/", "-")
        c.save(P.CROPS / f"{slug}.jpg", "JPEG", quality=85)
        return t["addr"], dict(id=im["id"], by=im["creator"], year=int(im["date"][:4]), d=round(d, 1), diff=round(diff), file=f"crops/{slug}.jpg", src=im["src"])
    except Exception as e:
        R.log("ERR", t["addr"], repr(e)[:80]); return t["addr"], None
def fetch():
    global TOK
    TOK = R.token(); T = targets(); cand = json.load(open(CAND)) if CAND.exists() else {}
    todo = [t for t in T if t["addr"] not in cand]; R.log(len(T), "targets", len(todo), "todo")
    n = 0
    with ThreadPoolExecutor(8) as ex:
        for addr, rec in ex.map(work, todo):
            t = next(x for x in T if x["addr"] == addr)
            cand[addr] = dict(t, imgs=[rec] if rec else []); n += 1
            if n % 100 == 0: json.dump(cand, open(CAND, "w"), ensure_ascii=False); R.log(n, sum(1 for v in cand.values() if v["imgs"]))
    json.dump(cand, open(CAND, "w"), ensure_ascii=False)
    R.log("done", len(cand), sum(1 for v in cand.values() if v["imgs"]))
def sheets():
    cand = json.load(open(CAND)); W, H, LAB = 400, 400, 22
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    sf = D / "sheets.json"; sheets = json.load(open(sf)) if sf.exists() else {}
    seen = {a for v in sheets.values() for a in v}
    items = [(k, v) for k, v in cand.items() if v["imgs"] and k not in seen]
    items.sort(key=lambda kv: (kv[1]["prio"], nrn(kv[1]["nr"]), kv[1]["nr"]))
    base = len(sheets)
    for i in range(0, len(items), 12):
        grp = items[i:i + 12]; sh = Image.new("RGB", (4 * W, 3 * (H + LAB)), (24, 24, 24)); dr = ImageDraw.Draw(sh)
        for j, (a, v) in enumerate(grp):
            x, y = (j % 4) * W, (j // 4) * (H + LAB)
            sh.paste(Image.open(P.RAW / v["imgs"][0]["file"]).resize((W - 2, H - 2)), (x + 1, y + LAB + 1))
            dr.text((x + 4, y + 2), f"{a}  {v['year'] or '?'}  {v['floors'] or '?'}G", fill=(255, 230, 0), font=font)
        name = f"{base + i // 12 + 1:03d}.jpg"; sh.save(D / name, "JPEG", quality=82); sheets[name] = [k for k, _ in grp]
    json.dump(sheets, open(sf, "w"), ensure_ascii=False, indent=0); print(len(items), "houses,", len(sheets), "sheets")

def fetchml():
    """Second pass: Mapillary perspective images (facades_fetch logic) for k5 targets without photo."""
    import facades_fetch as FF
    from collections import defaultdict
    tok = F.token(); T = targets(); cand = json.load(open(CAND))
    by = defaultdict(list)
    for r in json.load(open(ROOT / "data/build/gwr_kreise.json")): by[r["street"]].append((r["x"], r["y"]))
    v3 = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    todo = [t for t in T if not cand.get(t["addr"], {}).get("imgs") and not cand.get(t["addr"], {}).get("imgs_old") and t["addr"] not in v3]
    cells = sorted({(int(t["x"] // FF.CELL), int(t["y"] // FF.CELL)) for t in todo}); R.log(len(todo), "todo,", len(cells), "cells")
    with ThreadPoolExecutor(8) as ex: list(ex.map(lambda c: FF.cell_images(c[0], c[1], tok), cells))
    ok = 0
    for t in todo:
        t = dict(t, sdir=FF.street_dir(by[t["street"]], t["x"], t["y"]))
        ims = FF.cell_images(int(t["x"] // FF.CELL), int(t["y"] // FF.CELL), tok) or []
        seen, uniq = set(), []
        for im in ims:
            if im["id"] not in seen: seen.add(im["id"]); uniq.append(im)
        for im in FF.best(t, uniq)[:1]:
            r = F.get("dl", im["u"], pause=0.1)
            if not r: continue
            c = FF.crop(r.content, im["rel"], im["f"], im["d"])
            if c is None: continue
            slug = t["addr"].replace(" ", "_").replace("/", "-")
            c.save(P.CROPS / f"{slug}.jpg", "JPEG", quality=85)
            cand[t["addr"]] = dict({k: v for k, v in t.items() if k != "sdir"}, imgs=[dict(id=im["id"], by=im["by"], year=im["year"], d=im["d"], diff=im["diff"], file=f"crops/{slug}.jpg", src="mapillary")]); ok += 1
    json.dump(cand, open(CAND, "w"), ensure_ascii=False); R.log("done", ok)


if __name__ == "__main__":
    {"fetch": fetch, "sheets": sheets, "fetchml": fetchml}[sys.argv[1]]()
