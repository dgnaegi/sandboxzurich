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
KEEP = "## Ride gate with all"   # sections from here on are written by hand and kept


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


def has_lidar(cfg, tdir):
    """LiDAR grids exist for every tile under the site's rows (with a 40 m margin), not for its whole bounding box."""
    from rows import Rows
    need = set()
    for c in Rows(tdir, "live").site_chains(cfg):
        for x, y in c.P[:, :2]:
            for dx in (-40, 40):
                for dy in (-40, 40):
                    need.add((int((x + dx + OX) // T * T), int((y + dy + OY) // T * T)))
    return all(os.path.exists(os.path.join(ROOT, "data", "build", "lidar", f"g_{X}_{Y}.npz")) for X, Y in need)


def run_site(name, tdir):
    cfg = site_cfg(name)
    if not has_lidar(cfg, tdir):
        return {"site": name, "verdict": "no LiDAR", "fails": []}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ramp_build.run(tdir, [name], write=True)
        cfg, av, res = score.score_site(name, tdir, "v2")
        f = score.report(name, cfg, av, res, os.path.join(CITY, "reports"))
    findings = [ln.split("FINDING:", 1)[1].strip() for ln in buf.getvalue().splitlines() if "FINDING:" in ln]
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
            "piers": (P["piers"]["av_matched"], P["piers"]["under_deck"]), "res": P["res_b"]["abs95"], "findings": findings,
            "shape": cfg.get("shape", "ramp")}


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


def top_down(name):
    """Last top-down check of the integrated tiles (pipeline/scopes/topcheck.py), or None if it was not run for the site."""
    f = os.path.join(ROOT, "data", "build", "scopes", "topcheck", f"{name}.json")
    return __import__("json").load(open(f)) if os.path.exists(f) else None


def write_summary(out):
    import collections
    for r in out:                                  # the scorer's PASS needs the top-down check of the drawn decks too
        t = top_down(r["site"])
        r["top"] = "–" if t is None else t["verdict"] + (f" ({', '.join(t['fails'])})" if t["fails"] else "")
        if t is not None and t["verdict"] == "FAIL" and r["verdict"] == "PASS":
            r["verdict"] = "FAIL (top-down)"
    cnt = collections.Counter(r["verdict"] for r in out)
    lines = ["# City-wide run of the ramp builder", "",
             f"Generated {time.strftime('%Y-%m-%d')} by `pipeline/scopes/city.py`: every site built and scored on its own against the live "
             "world (scratch copy of the tiles); automatic sites from `pipeline/scopes/discover.py`. Full reports in "
             "`data/build/scopes/city/reports/` (not in git; rerun to regenerate).", "",
             "Count: " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()) + f" of {len(out)} sites"
             + (f"; REVIEW at helices (parking-garage spirals, out of scope for a bridge-ramp builder): {sum(1 for r in out if r.get('shape') == 'helix' and r['verdict'] == 'REVIEW')}" ) + ".", "",
             "Top-down: `pipeline/scopes/topcheck.py` on the integrated dev tiles (holes against the cadastre bridge outline, steps, "
             "invisible walls, sinking); – = not run for the site.", "",
             "| Site | kind | verdict | outline IoU live → v2 | width live → v2 (cadastre) | piers modelled / under deck | height p95 | top-down | failing checks |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in out:
        kind = ("hand" if r["site"] in SITES else "auto") + (", helix" if r.get("shape") == "helix" else "")
        if "iou" in r:
            lines.append(f"| {site_cfg(r['site'])['title']} (`{r['site']}`) | {kind} | {r['verdict']} | {f1(r['iou'][0])} → {f1(r['iou'][1])} | "
                         f"{f1(r['width'][0])} → {f1(r['width'][1])} ({f1(r['width'][2])}) m | {r['piers'][0]} / {r['piers'][1]} | {f1(r['res'])} m | {r['top']} | {'; '.join(r['fails'])} |")
        else:
            lines.append(f"| `{r['site']}` | {kind} | {r['verdict']} | | | | | {r['top']} | {'; '.join(r['fails'])[:160]} |")
    fnd = [(r["site"], x) for r in out for x in r.get("findings", [])]
    if fnd:
        lines += ["", "## Findings for other decks (not the ramp's error)", ""] + [f"- `{s_}`: {x}" for s_, x in fnd]
    f = os.path.join(ROOT, "research", "bridges", "scopes", "city.md")
    keep = ""
    if os.path.exists(f):                          # hand-written sections after the marker survive a rerun
        old = open(f).read(); m = old.find(KEEP)
        keep = old[m:] if m >= 0 else ""
    open(f, "w").write("\n".join(lines) + "\n\n" + keep)
    print(f)


if __name__ == "__main__":
    main()
