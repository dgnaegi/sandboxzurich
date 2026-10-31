"""City-wide run: every hand and automatic site is built and scored on its own, in a scratch copy of the live tiles, and the
verdicts are counted -> research/bridges/scopes/city.md (summary table) and data/build/scopes/city/<site>.md (full reports).

  python3 pipeline/scopes/city.py [site,site,...] [--tiles web/public/tiles]
The scratch copy (data/build/scopes/city/tiles + tiles_orig) starts from the live rows; ramp_build restores every tile it does
not touch, so each site is judged against the live world, without the other sites' rows. Sites whose LiDAR grids are missing
are listed as "no LiDAR". The deployed-style integration (all sites into one tile set) stays `ramp_build.py <all> --write`.
"""
from __future__ import annotations

import contextlib
import glob
import io
import os
import re
import shutil
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import ramp_build  # noqa: E402
import score  # noqa: E402
from ramp_sites import SITES, auto_sites, site as site_cfg  # noqa: E402

OX, OY, T = 2681400, 1248700, 500
CITY = os.path.join(ROOT, "data", "build", "scopes", "city")


def scratch(src):
    """Fresh scratch tiles = live rows (tiles_orig wins over the current tiles)."""
    tdir, odir = os.path.join(CITY, "tiles"), os.path.join(CITY, "tiles_orig")
    shutil.rmtree(tdir, ignore_errors=True); shutil.rmtree(odir, ignore_errors=True)
    os.makedirs(tdir); os.makedirs(odir)
    orig = os.path.join(os.path.dirname(os.path.abspath(src)), "tiles_orig")
    for f in glob.glob(f"{src}/t_*.json") + [f"{src}/world.json"]:
        o = os.path.join(orig, os.path.basename(f))
        shutil.copyfile(o if os.path.exists(o) else f, os.path.join(tdir, os.path.basename(f)))
    return tdir


def has_lidar(cfg):
    x0, y0, x1, y1 = cfg["fetch"]
    for X in range(int((x0 + OX) // T * T), int(x1 + OX) + 1, T):
        for Y in range(int((y0 + OY) // T * T), int(y1 + OY) + 1, T):
            if not os.path.exists(os.path.join(ROOT, "data", "build", "lidar", f"g_{X}_{Y}.npz")):
                return False
    return True


def run_site(name, tdir):
    cfg = site_cfg(name)
    if not has_lidar(cfg):
        return {"site": name, "verdict": "no LiDAR", "fails": []}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ramp_build.run(tdir, [name], write=True)
        cfg, av, res = score.score_site(name, tdir, "v2")
        f = score.report(name, cfg, av, res, os.path.join(CITY, "reports"))
    txt = open(f).read()
    m = re.search(r"## Verdict for the v2 rows: (\w+)", txt)
    if m and m.group(1) != "PASS" or "--overlays" in sys.argv:      # the picture for every site a person has to look at
        import overlay
        with contextlib.redirect_stdout(io.StringIO()):
            overlay.render(name, tdir, out=os.path.join(ROOT, "preview", "scopes", "city", f"{name}.png"), label="v2")
    fails = [ln.split("|")[1].strip() for ln in txt[txt.index("## Verdict"):].splitlines() if ln.rstrip().endswith("| NO |")]
    L, P = res["live"]["sum"], res["current"]["sum"]
    return {"site": name, "verdict": m.group(1) if m else "?", "fails": fails, "iou": (L["areas"]["outline_iou"], P["areas"]["outline_iou"]),
            "width": (L["model_w"]["p50"], P["model_w"]["p50"], P["av_w"]["p50"]), "chains": len(res["current"]["chains"]),
            "piers": (P["piers"]["av_matched"], P["piers"]["under_deck"]), "res": P["res_b"]["abs95"]}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    names = args[0].split(",") if args else list(SITES) + list(auto_sites())
    tdir = scratch(src)
    os.makedirs(os.path.join(ROOT, "preview", "scopes", "city"), exist_ok=True)
    out = []
    for n in names:
        t0 = time.time()
        try:
            r = run_site(n, tdir)
        except Exception as e:  # noqa: BLE001
            r = {"site": n, "verdict": "ERROR", "fails": [f"{type(e).__name__}: {e}"]}
            traceback.print_exc(file=sys.stderr)
        r["sec"] = time.time() - t0
        out.append(r)
        print(f"{n:40s} {r['verdict']:8s} {r['sec']:5.0f} s  {'; '.join(r['fails'])[:120]}", flush=True)
    write_summary(out)


def f1(v):
    return "–" if v is None or v != v else f"{v:.2f}" if abs(v) < 2 else f"{v:.1f}"


def write_summary(out):
    import collections
    cnt = collections.Counter(r["verdict"] for r in out)
    lines = ["# City-wide run of the ramp builder", "",
             f"Generated {time.strftime('%Y-%m-%d')} by `pipeline/scopes/city.py`: every site built and scored on its own against the live "
             "world (scratch copy of the tiles); automatic sites from `pipeline/scopes/discover.py`. Full reports in "
             "`data/build/scopes/city/reports/` (not in git; rerun to regenerate).", "",
             "Count: " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()) + f" of {len(out)} sites.", "",
             "| Site | kind | verdict | outline IoU live → v2 | width live → v2 (cadastre) | piers modelled / under deck | height p95 | failing checks |",
             "|---|---|---|---|---|---|---|---|"]
    for r in out:
        kind = "hand" if r["site"] in SITES else "auto"
        if "iou" in r:
            lines.append(f"| {site_cfg(r['site'])['title']} (`{r['site']}`) | {kind} | {r['verdict']} | {f1(r['iou'][0])} → {f1(r['iou'][1])} | "
                         f"{f1(r['width'][0])} → {f1(r['width'][1])} ({f1(r['width'][2])}) m | {r['piers'][0]} / {r['piers'][1]} | {f1(r['res'])} m | {'; '.join(r['fails'])} |")
        else:
            lines.append(f"| `{r['site']}` | {kind} | {r['verdict']} | | | | | {'; '.join(r['fails'])[:160]} |")
    f = os.path.join(ROOT, "research", "bridges", "scopes", "city.md")
    open(f, "w").write("\n".join(lines) + "\n")
    print(f)


if __name__ == "__main__":
    main()
