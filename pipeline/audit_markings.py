"""Audit of the road markings in the built tiles against SWISSIMAGE (data/raw/ortho_wms, 0.5 m/px).
usage: .venv/bin/python pipeline/audit_markings.py [--sheet N]  -> research/markings_audit.md, data/build/markings_audit.json, preview/markings_audit.jpg
Game side: the vertex-coloured marking triangles (ground layer 39: white/yellow/blue/red/green) and asphalt (layer 34) of data/build/tiles_raw/*.glb,
rasterised at 0.5 m. Ortho side: yellow mask (crossings._tile, sunlit only) and white mask (bright thin structures on asphalt).
Per 10 m cell: missing = evidence in the ortho but nothing in the game within 1.5 m; extra = game marking in a sunlit cell without ortho evidence.
White lines (0.12 m) are barely visible at 0.5 m/px: white 'extra' needs a lot of game paint, yellow is reliable. Decks are skipped."""
import glob, json, math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import crossings  # noqa: E402

RAW, ORT, TILE, CELL = R / "data/build/tiles_raw", R / "data/raw/ortho_wms", 500, 20  # CELL in px (10 m)
CLS = {(109, 109, 114): 7, (3, 3, 3): 7, (218, 218, 206): 2, (235, 147, 3): 3, (5, 26, 147): 4, (114, 13, 9): 5, (12, 78, 19): 6}  # vertex colours (sRGB->linear of the drape colours)
NAMES = {2: "white", 3: "yellow", 4: "blue", 5: "red", 6: "green"}


def read_ground(path):
    b = open(path, "rb").read()
    jl, _ = struct.unpack("<II", b[12:20]); j = json.loads(b[20:20 + jl]); bin_ = b[20 + jl + 8:]
    for n in j["nodes"]:
        if n.get("name") != "ground":
            continue
        at = j["meshes"][n["mesh"]]["primitives"][0]

        def acc(i):
            a = j["accessors"][i]; v = j["bufferViews"][a["bufferView"]]
            dt = {5126: "<f4", 5125: "<u4", 5121: "u1"}[a["componentType"]]; nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
            return np.frombuffer(bin_, dt, a["count"] * nc, v.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, nc)
        A = at["attributes"]
        return acc(A["POSITION"]), acc(A["COLOR_0"]), acc(A["TEXCOORD_1"])[:, 0], acc(at["indices"]).ravel()
    return None


def game_raster(ix, iy):
    return game_win(ix * TILE, (iy + 1) * TILE, TILE, 4, 2)


def game_win(x0, y1, size, S, pool):
    """dict name -> bool (n,n) rasters of the window [x0,x0+size] x [y1-size,y1] at S px/m, max-pooled by `pool`:
    road, white, yellow, blue, red, green, rail (rail heads / tram grooves)"""
    n = int(size * S)
    imgs = {k: Image.new("L", (n, n), 0) for k in range(1, 8)}
    dr = {k: ImageDraw.Draw(v) for k, v in imgs.items()}
    for tx in range(math.floor(x0 / 200), math.floor((x0 + size) / 200) + 1):
        for ty in range(math.floor((y1 - size) / 200), math.floor(y1 / 200) + 1):
            f = RAW / f"t_{tx}_{ty}.glb"
            g = read_ground(f) if f.exists() else None
            if g is None:
                continue
            pos, col, lay, idx = g
            X, Y = (pos[:, 0] - x0) * S, (y1 + pos[:, 2]) * S
            for t in idx.reshape(-1, 3):
                L = int(lay[t[0]])
                if L == 34:
                    k = 1
                elif L == 39:
                    k = CLS.get(tuple(int(v) for v in col[t[0], :3]))
                    if k is None:
                        continue
                else:
                    continue
                dr[k].polygon([(X[i], Y[i]) for i in t], fill=255)
    out = {}
    for k, nm in ((1, "road"), (2, "white"), (3, "yellow"), (4, "blue"), (5, "red"), (6, "green"), (7, "rail")):
        a = np.asarray(imgs[k])
        out[nm] = a.reshape(n // pool, pool, n // pool, pool).max(axis=(1, 3)) > 0
    out["road"] |= out["white"] | out["yellow"] | out["blue"] | out["red"] | out["green"]
    return out


def ortho_masks(ix, iy, road, rail):
    f = ORT / f"r_{ix}_{iy}.jpg"
    if not f.exists():
        return None
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
    lum = a.mean(2); r, gg, b = a[..., 0], a[..., 1], a[..., 2]
    yel = crossings._tile(ix, iy) == 1.0
    yel = ndi.binary_opening(yel, structure=np.ones((2, 2))) & ~ndi.binary_dilation(rail, iterations=6)
    roadd = ndi.binary_erosion(road, iterations=1)
    med = ndi.median_filter(np.where(roadd, lum, np.nan_to_num(lum, nan=0))[::2, ::2], size=11)
    med = np.kron(med, np.ones((2, 2), np.float32))[:1000, :1000]
    bright = roadd & (lum - med > 34) & (np.abs(r - b) < 34) & ((r + gg) / 2 - b < 14) & (lum > 120)
    big = ndi.binary_opening(bright, structure=np.ones((5, 5)))     # cars, light patches: wider than 2.5 m
    wht = bright & ~ndi.binary_dilation(big, iterations=3)
    wht = ndi.binary_opening(wht, structure=np.ones((2, 2))) | (ndi.binary_dilation(wht, iterations=0) & False)
    sun = roadd & (lum > 85) & (med > 85)
    return dict(yellow=yel & roadd, white=wht, sun=sun, lum=lum)


def cells(game, ort, deck):
    out = []
    d3 = lambda m: ndi.binary_dilation(m, iterations=3)
    gy, gw = game["yellow"], game["white"] | game["blue"]
    oy, ow = ort["yellow"] & ~deck, ort["white"] & ~deck
    miss_y, miss_w = oy & ~d3(gy), ow & ~d3(game["white"] | gy)
    ex_y, ex_w = gy & ~d3(oy) & ort["sun"] & ~deck, game["white"] & ~d3(ow | oy) & ort["sun"] & ~deck
    for name, m, thr in (("missing_yellow", miss_y, 30), ("extra_yellow", ex_y, 40)):  # white lines are not measurable at 0.5 m/px
        c = m.reshape(1000 // CELL, CELL, 1000 // CELL, CELL).sum(axis=(1, 3))
        for r, k in zip(*np.nonzero(c >= thr)):
            out.append((name, int(r), int(k), int(c[r, k])))
    return out


def main():
    import shapely
    from shapely.strtree import STRtree
    segs = deck_segments()
    tr = STRtree(segs)
    res, tot = [], {}
    for f in sorted(ORT.glob("r_*_*.jpg")):
        _, ix, iy = f.stem.split("_"); ix, iy = int(ix), int(iy)
        if not any((RAW / f"t_{tx}_{ty}.glb").exists() for tx in range(math.floor(ix * TILE / 200), math.floor((ix * TILE + TILE) / 200) + 1)
                   for ty in range(math.floor(iy * TILE / 200), math.floor((iy * TILE + TILE) / 200) + 1)):
            continue
        game = game_raster(ix, iy)
        if not game["road"].any():
            continue
        ort = ortho_masks(ix, iy, game["road"], game["rail"])
        if ort is None:
            continue
        deck = Image.new("L", (1000, 1000), 0); dd = ImageDraw.Draw(deck)
        for j in tr.query(shapely.box(ix * TILE, iy * TILE, ix * TILE + TILE, iy * TILE + TILE)):
            g = segs[j]
            dd.polygon([((x - ix * TILE) * 2, ((iy + 1) * TILE - y) * 2) for x, y in g.exterior.coords], fill=255)
        deck = np.asarray(deck) > 0
        for nm, r, c, n in cells(game, ort, deck):
            res.append(dict(kind=nm, n=n, x=ix * TILE + (c + .5) * CELL / 2, y=(iy + 1) * TILE - (r + .5) * CELL / 2))
        for k in ("yellow", "white"):
            tot[f"game_{k}_m2"] = tot.get(f"game_{k}_m2", 0) + int(game[k].sum()) / 4
        tot["road_m2"] = tot.get("road_m2", 0) + int(game["road"].sum()) / 4
        print(f"tile {ix},{iy}: {len(res)} cells so far", flush=True)
    res += hires()
    (R / "data/build/markings_audit.json").write_text(json.dumps(dict(totals=tot, cells=res)))
    summarize(res, tot)



# ----------------------------------------------------------------------------------------------- 0.1 m windows (white + yellow)
def hires_windows():
    """(name, ortho path, centre x, centre y, size m): 27 control points (160 m) + Langstrasse boxes (100 m), SWISSIMAGE 0.1 m/px"""
    import markings_ortho as MO
    w = []
    for nm, (x, y) in json.load(open(R / "data/build/ortho_points.json")).items():
        f = R / f"data/raw/ortho/ortho_{nm}.jpg"
        if f.exists():
            w.append((nm, f, x, y, 160.0))
    for i, (x, y) in enumerate(MO.boxes()):
        f = MO.D / f"ls_{i:02d}.jpg"
        if f.exists():
            w.append((f"ls_{i:02d}", f, x, y, 100.0))
    return w


def hires_masks(a, road, rail, deck):
    import markings_ortho as MO
    lum = a.mean(2); r, b = a[..., 0], a[..., 2]
    rd = ndi.binary_dilation(road, iterations=6) & ~deck & ~ndi.binary_dilation(rail, iterations=15)
    rf = road.astype(np.float32)
    mean = ndi.uniform_filter(lum * rf, 31) / np.maximum(ndi.uniform_filter(rf, 31), 1e-3)
    yel = MO.yellow_mask(a) & rd
    yel = ndi.binary_opening(yel, structure=np.ones((2, 2)))
    br = rd & (lum > 150) & (lum - mean > 38) & (np.abs(r - b) < 40) & ~ndi.binary_dilation(yel, iterations=2)
    big = ndi.binary_opening(br, structure=np.ones((15, 15)))   # cars, light patches (> 1.5 m wide)
    wht = ndi.binary_opening(br & ~ndi.binary_dilation(big, iterations=8), structure=np.ones((2, 2)))
    sun = rd & (ndi.uniform_filter(lum * rf, 31) / np.maximum(ndi.uniform_filter(rf, 31), 1e-3) > 95)
    return dict(yellow=yel, white=wht, sun=sun)


def hires_cells(game, ort, cell=80, tol=4):
    out = []
    for k in ("yellow", "white"):
        g, o = game[k] & game["road"], ort[k]
        dm = lambda m: ndi.binary_dilation(m, iterations=tol)
        miss, ex = o & ~dm(g | (game["yellow"] if k == "white" else False)), g & ~dm(o) & ort["sun"]
        n = g.shape[0] // cell
        cs = lambda m: m[: n * cell, : n * cell].reshape(n, cell, n, cell).sum(axis=(1, 3))
        mc, ec, gc, oc = cs(miss), cs(ex), cs(g), cs(o)
        for r, c in zip(*np.nonzero((mc >= (150 if k == "yellow" else 220)) & (mc > .6 * oc))):
            out.append((f"missing_{k}", int(r), int(c), int(mc[r, c])))
        for r, c in zip(*np.nonzero((gc >= (60 if k == "yellow" else 40)) & (ec > .75 * gc))):
            out.append((f"extra_{k}", int(r), int(c), int(ec[r, c])))
    return out


def hires():
    segs = deck_segments()
    res = []
    for nm, f, cx, cy, size in hires_windows():
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        n = a.shape[0]
        S = n / size
        x0, y1 = cx - size / 2, cy + size / 2
        game = game_win(x0, y1, size, S, 1)
        deck = deck_mask(segs, x0, y1, size, n)
        ort = hires_masks(a, game["road"], game["rail"], deck)
        cs = [c for c in hires_cells(game, ort)]
        for k, r, c, v in cs:
            res.append(dict(kind=k, n=v / 100.0 * 4, x=x0 + (c + .5) * 80 / S, y=y1 - (r + .5) * 80 / S, win=nm, hires=True))
        print(f"hires {nm}: {len(cs)} cells", flush=True)
    return res


def deck_segments():
    from shapely.geometry import LineString
    segs = []
    for f in glob.glob(str(R / "web/public/tiles/t_*.json")):
        for d in json.load(open(f)).get("bridges", {}).get("decks", []):
            p = d["p"]
            segs += [LineString([q[:2] for q in p[i:i + 2]]).buffer(d["w"] / 2 + 1.5) for i in range(len(p) - 1)
                     if min(p[i][2] - d["g"][i], p[i + 1][2] - d["g"][i + 1]) > 0.3]
    return segs


def deck_mask(segs, x0, y1, size, n):
    import shapely
    from shapely.strtree import STRtree
    im = Image.new("L", (n, n), 0); dd = ImageDraw.Draw(im); k = n / size
    for j in STRtree(segs).query(shapely.box(x0, y1 - size, x0 + size, y1)):
        dd.polygon([((x - x0) * k, (y1 - y) * k) for x, y in segs[j].exterior.coords], fill=255)
    return np.asarray(im) > 0


def merge(res):
    """merge neighbouring cells of one kind to places"""
    byk, out = {}, []
    for c in res:
        byk.setdefault(c["kind"], []).append(c)
    for k, cs in byk.items():
        pts = np.array([[c["x"], c["y"]] for c in cs]); lab = -np.ones(len(cs), int); nl = 0
        for i in range(len(cs)):
            if lab[i] >= 0:
                continue
            st = [i]; lab[i] = nl
            while st:
                a = st.pop()
                for b in np.nonzero((lab < 0) & (np.abs(pts - pts[a]).max(1) < 16))[0]:
                    lab[b] = nl; st.append(b)
            nl += 1
        for l in range(nl):
            m = [cs[i] for i in range(len(cs)) if lab[i] == l]
            n = sum(c["n"] for c in m) / 4
            out.append(dict(kind=k, hires=any(c.get('hires') for c in m), win=next((c['win'] for c in m if c.get('win')), ''), m2=round(n, 1), x=round(float(np.average([c["x"] for c in m], weights=[c["n"] for c in m])), 1),
                            y=round(float(np.average([c["y"] for c in m], weights=[c["n"] for c in m])), 1), cells=len(m)))
    return sorted(out, key=lambda p: -p["m2"])


def summarize(res, tot):
    pl = merge(res)
    (R / "data/build/markings_places.json").write_text(json.dumps(pl))
    from collections import Counter
    cnt = Counter(p["kind"] for p in pl)
    print(tot, dict(cnt))
    L = ["# Markierungs-Audit gegen SWISSIMAGE (`pipeline/audit_markings.py`)", "",
         f"Spiel: {tot.get('road_m2', 0):.0f} m² Fahrbahn, {tot.get('game_yellow_m2', 0):.0f} m² Gelb, {tot.get('game_white_m2', 0):.0f} m² Weiss.", "",
         "Orte (zusammengelegte 10-m-Zellen) nach Art: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())), "",
         "Weisse Linien (12 cm) sind bei 0.5 m/px kaum messbar: «missing_white/extra_white» nur grobe Hinweise; Gelb (Zebra, Randlinien) ist belastbar.", "",
         "| Art | Fläche m² | x | y |", "|---|---|---|---|"]
    for p in pl[:60]:
        L.append(f"| {p['kind']} | {p['m2']} | {p['x']} | {p['y']} |")
    (R / "research/markings_audit.md").write_text("\n".join(L) + "\n")


def sheet(n=12, cap=4, half=20, up=3, kinds=None, out="markings_audit"):
    """preview/markings_audit.jpg: ortho | game (white/yellow/blue/red/green on asphalt) at the n worst places (40 m windows)"""
    pl = json.load(open(R / "data/build/markings_places.json"))
    wins = hires_windows()
    pick, per = [], {}
    for p in pl:
        if p["hires"] and (kinds is None or p["kind"] in kinds) and per.get(p["kind"], 0) < cap and p["m2"] >= 3:
            pick.append(p); per[p["kind"]] = per.get(p["kind"], 0) + 1
    pick = sorted(pick, key=lambda p: -p["m2"])[:n]
    W = 2 * half * up * 2
    cols, rows = 3, math.ceil(len(pick) / 3)
    img = Image.new("RGB", (cols * (2 * W + 6), rows * (W + 18)), "black"); d = ImageDraw.Draw(img)
    pal = {"road": (70, 70, 74), "white": (240, 240, 235), "yellow": (250, 200, 20), "blue": (60, 100, 220), "red": (200, 40, 30), "green": (30, 150, 50), "rail": (110, 110, 118)}
    for i, p in enumerate(pick):
        nm, f, cx, cy, size = next(w for w in wins if w[0] == p["win"])
        o = Image.open(f).convert("RGB"); k = o.size[0] / size
        box_ = (int((p["x"] - half - (cx - size / 2)) * k), int((cy + size / 2 - p["y"] - half) * k))
        box_ = (max(0, min(o.size[0] - int(2 * half * k), box_[0])), max(0, min(o.size[0] - int(2 * half * k), box_[1])))
        oc = o.crop((*box_, box_[0] + int(2 * half * k), box_[1] + int(2 * half * k))).resize((W, W), Image.BICUBIC)
        x0, y1 = cx - size / 2 + box_[0] / k, cy + size / 2 - box_[1] / k
        game = game_win(x0, y1, 2 * half, 10, 1)
        g = np.zeros((20 * half, 20 * half, 3), np.uint8) + 25
        for kk in ("road", "rail", "blue", "green", "red", "white", "yellow"):
            g[game[kk]] = pal[kk]
        x, y = (i % cols) * (2 * W + 6), (i // cols) * (W + 18)
        img.paste(oc, (x, y + 16)); img.paste(Image.fromarray(g).resize((W, W), Image.NEAREST), (x + W, y + 16))
        d.text((x + 2, y + 2), f"{i + 1} {p['kind']} {p['m2']}m2 ({p['x']:.0f},{p['y']:.0f}) {p['win']}", fill="yellow")
    img.save(R / f"preview/{out}.jpg", quality=80)
    print(f"sheet {img.size}; picks:", [(i + 1, p["kind"], round(p["x"]), round(p["y"]), p["m2"]) for i, p in enumerate(pick)])


# ----------------------------------------------------------------------------------------------- zebras per window
def _zebras(mask, S):
    """centres (m, window-local, north-up rows) of zebra-sized yellow blobs: stripes merged (closing 0.5 m), >= 7 m2, short side >= 2.4 m"""
    k = max(2, int(0.35 * S))   # stripes are 0.5 m wide, kerb/edge lines 0.12-0.3 m: opening keeps the stripes only
    m = ndi.binary_opening(mask, structure=np.ones((k, k)))
    m = ndi.binary_closing(m, structure=np.ones((3, 3)), iterations=int(0.5 * S) + 1)
    lab, n = ndi.label(m)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        sub = lab[sl] == i
        area = sub.sum() / S ** 2
        h, w = (sl[0].stop - sl[0].start) / S, (sl[1].stop - sl[1].start) / S
        if area < 7 or min(h, w) < 2.4 or max(h, w) > 20 or area / (h * w) < 0.25:
            continue
        cy, cx = ndi.center_of_mass(sub)
        out.append(((sl[1].start + cx) / S, (sl[0].start + cy) / S))
    return out


def zebra_check(tiles=None):
    """per 0.1 m window (not the Langstrasse boxes, whose yellow is drawn from the ortho): zebras seen in the ortho vs zebras in the game"""
    import markings_ortho as MO
    tot = dict(ortho=0, matched=0, game=0, game_unmatched=0)
    rows = []
    segs = deck_segments()
    for nm, f, cx, cy, size in hires_windows():
        if nm.startswith("ls_"):
            continue
        if tiles is not None and f"{math.floor(cx / 200)}_{math.floor(cy / 200)}" not in tiles:
            continue
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        n = a.shape[0]; S = n / size
        x0, y1 = cx - size / 2, cy + size / 2
        game = game_win(x0, y1, size, S, 1)
        deck = deck_mask(segs, x0, y1, size, n)
        oy = MO.yellow_mask(a) & ndi.binary_dilation(game["road"], iterations=6) & ~deck & ~ndi.binary_dilation(game["rail"], iterations=15)
        oz, gz = _zebras(oy, S), _zebras(game["yellow"], S)
        mo = [any(math.hypot(p[0] - q[0], p[1] - q[1]) < 5 for q in gz) for p in oz]
        mg = [any(math.hypot(p[0] - q[0], p[1] - q[1]) < 5 for q in oz) for p in gz]
        tot["ortho"] += len(oz); tot["matched"] += sum(mo); tot["game"] += len(gz); tot["game_unmatched"] += len(gz) - sum(mg)
        rows.append((nm, len(oz), sum(mo), len(gz), len(gz) - sum(mg)))
    return tot, rows


def zebra_sheet(names=("seebahn_badener", "kalkbreite", "quartier_kernstr", "limmatplatz"), px=560, out="markings_zebras"):
    """preview/markings_zebras.jpg: whole 160 m window, ortho | game markings, for the given control points"""
    W = {w[0]: w for w in hires_windows()}
    img = Image.new("RGB", (2 * px + 4, len(names) * (px + 14)), "black"); d = ImageDraw.Draw(img)
    pal = {"road": (70, 70, 74), "white": (240, 240, 235), "yellow": (250, 200, 20), "blue": (60, 100, 220), "red": (200, 40, 30), "green": (30, 150, 50), "rail": (110, 110, 118)}
    for i, nm in enumerate(names):
        _, f, cx, cy, size = W[nm]
        o = Image.open(f).convert("RGB").resize((px, px), Image.BICUBIC)
        game = game_win(cx - size / 2, cy + size / 2, size, 8, 1)
        g = np.zeros((int(size * 8), int(size * 8), 3), np.uint8) + 25
        for kk in ("road", "rail", "blue", "green", "red", "white", "yellow"):
            g[game[kk]] = pal[kk]
        y = i * (px + 14)
        img.paste(o, (0, y + 14)); img.paste(Image.fromarray(g).resize((px, px), Image.NEAREST), (px + 4, y + 14))
        d.text((3, y + 1), f"{nm} ({cx:.0f},{cy:.0f}) {size:.0f} m: SWISSIMAGE 0.1 m | game", fill="yellow")
    img.save(R / f"preview/{out}.jpg", quality=80)
    print("sheet", img.size)


if __name__ == "__main__":
    if "--zsheet" in sys.argv:
        zebra_sheet()
    elif "--zebras" in sys.argv:
        t = set(open(sys.argv[sys.argv.index("--zebras") + 1]).read().split(",")) if len(sys.argv) > sys.argv.index("--zebras") + 1 else None
        tot, rows = zebra_check(t)
        print(tot, f"recall {tot['matched'] / max(tot['ortho'], 1):.0%}, game zebras without ortho zebra {tot['game_unmatched']}/{tot['game']}")
        for r in rows:
            print(r)
    elif "--sheet" in sys.argv:
        if "--kinds" in sys.argv:
            sheet(kinds=sys.argv[sys.argv.index("--kinds") + 1].split(","), cap=6, out="markings_extra")
        else:
            sheet()
    elif "--summary" in sys.argv:
        d = json.load(open(R / "data/build/markings_audit.json")); summarize(d["cells"], d["totals"])
    else:
        main()



