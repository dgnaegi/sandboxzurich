"""Zone 1: houses that already have a note (visual_notes_v3.json) but no geschosse -> photos (looser selection) + contact sheets for fields_z1.tsv.
Writes research/zones/z1/fields/{targets,photos}.json and sheets/NNN.jpg + index.json. Usage: python facades_z1_fields.py [--sheets]"""
import json, math, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parent.parent))
from zones import inside
import fetch_v3 as F, facades_fetch as ff, facades_k4_fetch as K
from PIL import Image, ImageDraw, ImageFont
ROOT = K.ROOT; Z = ROOT / "research/zones/z1/fields"; Z.mkdir(parents=True, exist_ok=True)
CR = ROOT / "data/raw/photos/facades/z1/crops_f"; CR.mkdir(parents=True, exist_ok=True); K.CR = CR
K.DMAX, K.DIFF, K.OBL = 60, 60, 85
def targets():
    z = [v for v in json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"] if v["id"] == 1][0]
    cams = [(c["x"], c["y"]) for c in z["cams"]]; gwr = json.load(open(ROOT / "data/build/gwr_kreise.json")); by = {}
    for r in gwr: by.setdefault(r["street"], []).append((r["x"], r["y"]))
    vn = json.load(open(ROOT / "research/buildings/visual_notes_v3.json")); out = []
    for r in gwr:
        a = f"{r['street']} {r['nr']}"
        if not inside(z["polys"][0], r["x"], r["y"]) or a not in vn or "geschosse" in vn[a] and "achsen" in vn[a]: continue
        la, lo = F.local_ll(r["x"], r["y"]); dc = min(math.hypot(r["x"] - cx, r["y"] - cy) for cx, cy in cams)
        out.append(dict(sdir=ff.street_dir(by[r["street"]], r["x"], r["y"]), addr=a, street=r["street"], nr=r["nr"], x=r["x"], y=r["y"], lat=la, lon=lo,
                        year=r["year"], floors=r["floors"], period=r["period"], cls=r["class"], dcam=round(dc), has_g="geschosse" in vn[a]))
    out.sort(key=lambda t: t["dcam"]); return out
def main():
    T = targets(); json.dump(T, open(Z / "targets.json", "w"), ensure_ascii=False); print(len(T), "targets")
    mf = Z / "photos.json"; meta = json.load(open(mf)) if mf.exists() else {}; tok = K.R.token()
    todo = [(i, t) for i, t in enumerate(T) if t["addr"] not in meta]
    with ThreadPoolExecutor(6) as ex: list(ex.map(lambda it: K.work(1400000 + it[0], it[1], tok, meta), todo))
    json.dump(meta, open(mf, "w"), ensure_ascii=False); print(sum(1 for m in meta.values() if m["photos"]), "with photos")
def sheets():
    T = json.load(open(Z / "targets.json")); P = json.load(open(Z / "photos.json"))
    items = [(t, P[t["addr"]]["photos"][0]) for t in T if (P.get(t["addr"]) or {}).get("photos")]
    SH = Z / "sheets"; SH.mkdir(exist_ok=True); font = ImageFont.load_default(size=16); idx = {}
    for s in range(0, len(items), 16):
        sh = Image.new("RGB", (1600, 1200), "white"); d = ImageDraw.Draw(sh); names = []
        for j, (t, ph) in enumerate(items[s:s + 16]):
            im = Image.open(ROOT / ph["file"]).convert("RGB").resize((400, 300)); x, y = (j % 4) * 400, (j // 4) * 300
            sh.paste(im, (x, y)); d.rectangle([x, y, x + 399, y + 20], fill=(0, 0, 0))
            d.text((x + 4, y + 2), f"{j+1} {t['addr']} ({t['year'] or '?'}, {t['floors'] or '?'}G)", fill=(255, 255, 0), font=font)
            d.line([x + 200, y + 20, x + 200, y + 34], fill=(255, 0, 0), width=2); names.append(t["addr"])
        n = s // 16 + 1; sh.save(SH / f"{n:03d}.jpg", quality=78); idx[f"{n:03d}"] = names
    json.dump(idx, open(Z / "index.json", "w"), ensure_ascii=False); print(len(items), "houses,", len(idx), "sheets")
if "--sheets" in sys.argv: sheets()
else: main()
