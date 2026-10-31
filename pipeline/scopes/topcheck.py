"""Top-down check: the decks as the game draws them, seen from above, against the cadastre, LiDAR and SWISSIMAGE.

The scorer (score.py) measures the deck rows; this check measures what the client renders and walks on. web/tests/deck_top.mjs
renders the site's view box orthographically from the running dev server (photo, drawn deck surface heights, tile mesh
height) and samples the client's collision functions at every cell; topcheck_find.py turns the cells into numbered findings
(holes against the AV bridge outline, drawn surface below the LiDAR surface on traffic areas, steps, invisible walls,
sinking). Verdict PASS when no finding passes the gate (topcheck_find.GATE).

  python3 pipeline/scopes/topcheck.py [<site>[,<site>...]] [--base http://localhost:5190] [--res 0.5] [--no-render]
needs the dev server with the built tiles (cd web && npm run dev, or the VITE_WORLD_PROXY variant); no site = all sites.
Output: data/build/scopes/topcheck/<site>.png (SWISSIMAGE | game | findings) and <site>.json; summary table
research/bridges/scopes/topcheck.md.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import scope_av  # noqa: E402
import topcheck_find as F  # noqa: E402
from ramp_sites import site as site_cfg  # noqa: E402

OX, OY = 2681400.0, 1248700.0
OUT = os.path.join(ROOT, "data", "build", "scopes", "topcheck")
RAW = os.path.join(OUT, "raw")
ORTHO = os.path.join(ROOT, "data", "raw", "ortho_sites")
REPORT = os.path.join(ROOT, "research", "bridges", "scopes", "topcheck.md")
CHUNK = 300.0          # m, render box per page load (tiles load 450 m around the player)
MARGIN = 30.0          # m around the site's view box: bridge heads and approaches sit at its edge
PLANES = ["deck", "rail", "glb", "walk", "feet", "ground", "push"]
# findings panel colours (legend below the sheet)
COL = {"covered": (60, 170, 60), "above": (0, 170, 150), "sink": (255, 255, 255), "blocked": (255, 220, 0), "step": (255, 0, 255),
       "below": (220, 0, 110), "rail_low": (105, 50, 85), "rhole": (160, 110, 60), "edge": (255, 150, 40), "interior": (255, 40, 40)}
LEGEND = ("cyan AV road bridge  lavender AV rail bridge  blue AV bridge not modelled  red hole in deck  orange deck narrower than bridge  "
          "crimson below LiDAR surface  dark rose rail deck below LiDAR (not gating)  brown rail-bridge hole  magenta step  yellow invisible wall  white sink  green terrain over deck  "
          "teal above LiDAR")


def chunks(box, res):
    x0, y0, x1, y1 = box
    nx, ny = max(1, math.ceil((x1 - x0) / CHUNK)), max(1, math.ceil((y1 - y0) / CHUNK))
    sx = math.ceil((x1 - x0) / nx / res) * res
    sy = math.ceil((y1 - y0) / ny / res) * res
    return [(i, j, (x0 + i * sx, y1 - (j + 1) * sy, x0 + (i + 1) * sx, y1 - j * sy)) for j in range(ny) for i in range(nx)], (nx * sx, ny * sy)


def render(name, box, res, base, need):
    """Render the chunks that touch `need` (shapely geometry); returns the stitched planes and the photo."""
    os.makedirs(RAW, exist_ok=True)
    from shapely.geometry import box as sbox
    cl, wh = chunks(box, res)
    jobs = [{"id": f"{name}_{i}_{j}", "box": list(b), "res": res} for i, j, b in cl if need.intersects(sbox(*b))]
    jf = os.path.join(RAW, f"{name}_jobs.json")
    json.dump(jobs, open(jf, "w"))
    if jobs:
        subprocess.run(["node", "tests/deck_top.mjs", jf, RAW, base], cwd=os.path.join(ROOT, "web"), check=True)
    return stitch(name, box, res, cl, {j["id"] for j in jobs}, wh)


def stitch(name, box, res, cl, ids, wh):
    x0, y1 = box[0], box[3]
    W, H = round(wh[0] / res), round(wh[1] / res)
    A = {k: np.full((H, W), np.nan, np.float32) for k in PLANES}
    photo = Image.new("RGB", (2 * W, 2 * H), (40, 40, 40))
    missing = []
    for i, j, b in cl:
        cid = f"{name}_{i}_{j}"
        if cid not in ids:
            continue
        m = json.load(open(os.path.join(RAW, f"{cid}.json")))
        a = np.fromfile(os.path.join(RAW, f"{cid}.bin"), dtype="<f4").reshape(len(m["planes"]), m["H"], m["W"])
        c0, r0 = round((b[0] - x0) / res), round((y1 - b[3]) / res)
        for n, k in enumerate(m["planes"]):
            A[k][r0:r0 + m["H"], c0:c0 + m["W"]] = a[n]
        photo.paste(Image.open(os.path.join(RAW, f"{cid}_photo.png")).convert("RGB"), (2 * c0, 2 * r0))
        missing += m["missing"]
    return A, photo, (x0, y1 - H * res, x0 + W * res, y1), sorted(set(missing))


def ortho(name, box, shape):
    """SWISSIMAGE crop of the box (swisstopo WMS, cached)."""
    os.makedirs(ORTHO, exist_ok=True)
    x0, y0, x1, y1 = box
    f = os.path.join(ORTHO, f"{name}_{x0:.0f}_{y0:.0f}_{x1:.0f}_{y1:.0f}.jpg")
    if not os.path.exists(f):
        import requests
        H, W = shape
        k = min(1.0, 2000 / max(W, H))
        p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "ch.swisstopo.images-swissimage", "STYLES": "",
             "SRS": "EPSG:2056", "BBOX": f"{OX + x0},{OY + y0},{OX + x1},{OY + y1}", "WIDTH": int(W * k), "HEIGHT": int(H * k),
             "FORMAT": "image/jpeg"}
        r = requests.get("https://wms.geo.admin.ch/", params=p, timeout=120, headers={"User-Agent": "sandboxzurich-audit/1.0 (research)"})
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image"):
            raise RuntimeError(r.text[:200])
        open(f, "wb").write(r.content)
    return Image.open(f).convert("RGB")


def sheet(R, photo, orth, out):
    """SWISSIMAGE | game from above | findings, labelled with the finding ids of the json."""
    M = R["_masks"]
    H, W = M["deck"].shape
    S = min(1.0, 900 / max(2 * W, 2 * H))           # panel scale (photo has 2 px per cell)
    pw, ph = int(2 * W * S), int(2 * H * S)
    base = np.array(photo.convert("L").convert("RGB").resize((W, H)), np.float32) * 0.45
    base[M["deck"]] = base[M["deck"]] * 0.5 + 75
    base[M["rail"]] = base[M["rail"]] * 0.5 + np.array([85, 75, 60])
    base[M["unmodelled"] & ~M["deck"]] = [40, 70, 140]
    for key in ("covered", "above", "sink", "blocked", "below", "step"):
        base[M[key]] = COL[key]
    base[M["rhole"]] = COL["rhole"]
    for c in R["below"]:
        if c["drawn"] == "rail deck too low":      # reported, not gating: muted
            base[c["rc"]] = COL["rail_low"]
    for h in R["holes"]:
        base[h["rc"]] = COL[h["kind"]]
    for key, col in (("req", (0, 220, 255)), ("rreq", (180, 170, 230))):
        base[M[key] & ~ndimage.binary_erosion(M[key])] = col
    diag = Image.fromarray(base.astype(np.uint8)).resize((pw, ph), Image.NEAREST)
    d = ImageDraw.Draw(diag)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except OSError:
        font = ImageFont.load_default()
    x0, y1, res = R["box"][0], R["box"][3], R["res"]
    gate = {i for v in R["gating"].values() for i in v}
    for c in R["holes"] + R["below"] + R["steps"] + R["blocked"] + R["sinks"]:
        if c["id"] in gate:
            px, py = (c["x"] - x0) / res * pw / W, (y1 - c["y"]) / res * ph / H
            d.text((px + 4, py - 7), c["id"], fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    top = 26
    img = Image.new("RGB", (3 * pw + 20, ph + top + 40), (20, 20, 20))
    dd = ImageDraw.Draw(img)
    for k, (im, lab) in enumerate(zip([orth.resize((pw, ph)), photo.resize((pw, ph)), diag], ["SWISSIMAGE", "game, from above", "findings"])):
        img.paste(im, (k * (pw + 10), top))
        dd.text((k * (pw + 10) + 4, 6), lab, fill=(230, 230, 230), font=font)
    dd.text((4, ph + top + 4), f"{R['site']}  {R['verdict']}  {', '.join(R['fails'])}", fill=(230, 230, 230), font=font)
    dd.text((4, ph + top + 21), LEGEND, fill=(170, 170, 170), font=font)
    img.save(out, quality=88)


def report(R):
    """One row per site in the summary table (rows of other sites are kept)."""
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    rows = {}
    if os.path.exists(REPORT):
        for line in open(REPORT):
            if line.startswith("| ") and not line.startswith("| site"):
                rows[line.split("|")[1].strip()] = line
    G = R["gating"]
    by = {c["id"]: c for k in ("holes", "below", "steps", "blocked", "sinks") for c in R[k]}
    cell = lambda k, f="m2": f"{len(G[k])} / {sum(by[i][f] for i in G[k]):.0f}" if G[k] else "–"  # noqa: E731
    rows[R["site"]] = (f"| {R['site']} | {R['verdict']} | {R['av_covered']:.0%} | {cell('interior holes')} | {cell('edge holes')} | "
                       f"{cell('below LiDAR') if R['lidar_share'] > 0.2 else 'no LiDAR'} | {cell('steps', 'len')} | {cell('blocked')} | "
                       f"{cell('sink')} | {R['covered_m2']:.0f} | {len(R['rail_holes'])} | {len(R['unmodelled'])} |\n")
    L = ["# Top-down check (`pipeline/scopes/topcheck.py`)\n\n",
         f"Last run {dt.date.today().isoformat()} on the integrated dev tiles. Drawn decks from above against the cadastre bridge "
         "outlines and the LiDAR surface; sheets in `data/build/scopes/topcheck/<site>.png`, finding ids and positions in "
         "`<site>.json`. Gating findings as count / m² (steps: count / m).\n\n",
         "| site | verdict | AV bridge covered | interior holes | edge holes | below LiDAR | steps | invisible walls | sink | terrain over deck m² | rail-bridge holes | AV bridges not modelled |\n",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"]
    L += [rows[k] for k in sorted(rows) if not k.startswith("---")]
    open(REPORT, "w").write("".join(L))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = lambda k, d: next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == k), d)  # noqa: E731
    base, res = opt("--base", "http://localhost:5190"), float(opt("--res", "0.5"))
    os.makedirs(OUT, exist_ok=True)
    import shapely
    from ramp_sites import SITES, auto_sites
    for name in (args[0].split(",") if args else list(SITES) + list(auto_sites())):
        av = scope_av.load(name)
        x0, y0, x1, y1 = (float(v) for v in site_cfg(name)["view"])
        box = (x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN)
        if "--no-render" in sys.argv:
            cl, wh = chunks(box, res)
            ids = {f"{name}_{i}_{j}" for i, j, _ in cl if os.path.exists(os.path.join(RAW, f"{name}_{i}_{j}.json"))}
            P, photo, gbox, missing = stitch(name, box, res, cl, ids, wh)
        else:
            need = shapely.union_all(av.geoms("deck")).buffer(20) if av.geoms("deck") else shapely.Polygon()
            P, photo, gbox, missing = render(name, box, res, base, need)
        R = F.analyse(name, P, gbox, res, av)
        R["missing_tiles"] = missing
        sheet(R, photo, ortho(name, gbox, P["deck"].shape), os.path.join(OUT, f"{name}.png"))
        json.dump(F.clean(R), open(os.path.join(OUT, f"{name}.json"), "w"), indent=1, ensure_ascii=False)
        report(R)                                  # row by row: a crash later keeps the sites done so far
        G = R["gating"]
        print(f"{name}: {R['verdict']}  AV covered {R['av_covered']:.0%}, LiDAR on {R['lidar_share']:.0%} of the traffic area; "
              + "; ".join(f"{k} {' '.join(v[:6])}" for k, v in G.items() if v)
              + (f"  MISSING TILES {' '.join(missing)}" if missing else ""), flush=True)


if __name__ == "__main__":
    main()
