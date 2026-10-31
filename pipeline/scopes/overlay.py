"""Top-down overlay of a ramp site: SWISSIMAGE crop, cadastre (Scope B), LiDAR bridge-class mask (Scope A), modelled rows.

Two panels, live rows (left) and pilot rows (right), same extent (site `view` box, game metres), written to
preview/scopes/<site>_overlay.png (images stay out of git). The orthophoto comes from the swisstopo WMS
(ch.swisstopo.images-swissimage, free use with source credit) and is cached under data/build/scopes/.
Usage:  python3 pipeline/scopes/overlay.py <site>[,<site>] [--tiles web/public/tiles] [--res 0.2]
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import lidar  # noqa: E402
from ramp_sites import site as site_cfg  # noqa: E402
from rows import Rows, clip_box  # noqa: E402
import scope_av  # noqa: E402

OX, OY = 2681400.0, 1248700.0
WMS = "https://wms.geo.admin.ch/"
CACHE = os.path.join(ROOT, "data", "build", "scopes")
OUT = os.path.join(ROOT, "preview", "scopes")

STYLE = {   # group -> (edge colour, face colour, line width, z order, legend label)
    "deck": ("#00e5ff", (0, 0.9, 1, 0.10), 1.6, 5, "AV Brücke/Passerelle"),
    "pier": ("#ff00c8", (1, 0, 0.78, 0.75), 0.8, 7, "AV Pfeiler"),
    "wall": ("#ff9100", (1, 0.57, 0, 0.75), 0.8, 6, "AV Mauer"),
    "stairs": ("#ffee00", (1, 0.93, 0, 0.55), 0.8, 6, "AV Treppe"),
    "underpass": ("#ffffff", "none", 1.0, 5, "AV Unterführung"),
    "shelter": ("#bbbbbb", (0.7, 0.7, 0.7, 0.35), 0.6, 4, "AV Unterstand"),
    "carriageway": ("#ffffff", "none", 0.6, 3, "AV Strasse, Weg"),
    "footway": ("#d0d0d0", "none", 0.5, 3, "AV Trottoir"),
}


def ortho(name, box, res=0.2):
    """Orthophoto for a game-metre box as (RGB array, extent); cached per box and resolution."""
    os.makedirs(CACHE, exist_ok=True)
    key = "_".join(f"{v:.0f}" for v in box) + f"_{res}"
    f = os.path.join(CACHE, f"{name}_ortho_{key}.jpg")
    from PIL import Image
    if not os.path.exists(f):
        import requests
        x0, y0, x1, y1 = box
        w, h = int(round((x1 - x0) / res)), int(round((y1 - y0) / res))
        p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "ch.swisstopo.images-swissimage", "STYLES": "",
             "SRS": "EPSG:2056", "BBOX": f"{OX + x0},{OY + y0},{OX + x1},{OY + y1}", "WIDTH": w, "HEIGHT": h, "FORMAT": "image/jpeg"}
        r = requests.get(WMS, params=p, timeout=120, headers={"User-Agent": "sandboxzurich/0.1 (research)"})
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image"):
            raise RuntimeError(r.text[:300])
        open(f, "wb").write(r.content)
        time.sleep(1.0)
    im = np.asarray(Image.open(f).convert("RGB"))
    return im, (box[0], box[2], box[1], box[3])


def lidar_mask(box, res=0.5):
    """Class-17 (bridge deck) cells inside the box as a boolean grid (rows south->north) plus extent."""
    x0, y0, x1, y1 = box
    xs = np.arange(x0 + res / 2, x1, res); ys = np.arange(y0 + res / 2, y1, res)
    X, Y = np.meshgrid(xs, ys)
    b = lidar.bridge(X.ravel(), Y.ravel()).reshape(X.shape)
    return ~np.isnan(b), (x0, x1, y0, y1)


def draw_geom(ax, g, edge, face, lw, z, ls="-"):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    geoms = getattr(g, "geoms", [g])
    for q in geoms:
        if q.geom_type == "Polygon":
            verts, codes = [], []
            for ring in [q.exterior] + list(q.interiors):
                c = np.asarray(ring.coords)
                verts += c.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=face, edgecolor=edge, lw=lw, zorder=z, ls=ls))
        elif q.geom_type == "LineString":
            c = np.asarray(q.coords); ax.plot(c[:, 0], c[:, 1], color=edge, lw=lw, zorder=z, ls=ls)
        elif hasattr(q, "geoms"):
            draw_geom(ax, q, edge, face, lw, z, ls)


def panel(ax, name, cfg, av, R, chains, img, ext, mask, mext, colour, label):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.imshow(img, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
    rgba = np.zeros(mask.shape + (4,)); rgba[mask] = (0.25, 0.45, 1.0, 0.40)
    ax.imshow(rgba, extent=mext, origin="lower", interpolation="nearest", zorder=2)
    handles = [Patch(facecolor=(0.25, 0.45, 1.0, 0.4), edgecolor="none", label="LiDAR class 17 (bridge deck)")]
    for grp, (edge, face, lw, z, lab) in STYLE.items():
        for g in av.geoms(grp):
            draw_geom(ax, g, edge, face, lw, z, ls="--" if grp == "underpass" else "-")
        if av.geoms(grp):
            handles.append(Patch(facecolor=face if face != "none" else (0, 0, 0, 0), edgecolor=edge, label=lab))
    for c in chains:
        fp = c.footprint()
        draw_geom(ax, fp, colour, (*_rgb(colour), 0.22), 1.8, 9)
        st = c.stations(2.0)
        inside = clip_box(st["xy"], cfg["view"])
        for k in range(0, len(st["s"]), 10):   # a tick every 20 m, labelled with the station (m from the chain start)
            if not inside[k]:
                continue
            p = st["xy"][k]; n = st["nrm"][k]; hw = max(st["wl"][k], st["wr"][k]) + 1.5
            ax.plot([p[0] - n[0] * hw, p[0] + n[0] * hw], [p[1] - n[1] * hw, p[1] + n[1] * hw], color=colour, lw=0.6, zorder=10)
            ax.text(p[0] + n[0] * (hw + 1), p[1] + n[1] * (hw + 1), f"{st['s'][k]:.0f}", color=colour, fontsize=5, zorder=11,
                    ha="center", va="center", path_effects=_halo(), clip_on=True)
        ax.plot(c.P[:, 0], c.P[:, 1], color=colour, lw=0.7, ls=":", zorder=10)
        for end in (0, -1):
            if clip_box(c.P[[end], :2], cfg["view"])[0]:
                ax.text(c.P[end, 0], c.P[end, 1], c.ends[end], color=colour, fontsize=6, zorder=11, ha="left", va="bottom", path_effects=_halo(), clip_on=True)
    handles.append(Patch(facecolor=(*_rgb(colour), 0.22), edgecolor=colour, label=f"{label} rows (footprint, 20 m stations)"))
    pq = R.site_piers(chains)
    if pq:
        ax.scatter([q[0] for q in pq], [q[1] for q in pq], s=14, marker="s", facecolor="none", edgecolor=colour, lw=0.9, zorder=12)
        handles.append(Line2D([], [], marker="s", ls="none", markerfacecolor="none", markeredgecolor=colour, label=f"{label} piers (tile rows)"))
    x0, y0, x1, y1 = cfg["view"]
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.plot([x1 - 30, x1 - 10], [y0 + 6, y0 + 6], color="white", lw=3, zorder=20, solid_capstyle="butt")
    ax.text(x1 - 20, y0 + 9, "20 m", color="white", fontsize=7, ha="center", zorder=20, path_effects=_halo())
    ax.set_title(f"{cfg['title']} — {label} rows", fontsize=9, loc="left")
    ax.tick_params(labelsize=6)
    ax.legend(handles=handles, fontsize=5.5, loc=cfg.get("legend", "upper left"), framealpha=0.85)


def _rgb(c):
    from matplotlib.colors import to_rgb
    return to_rgb(c)


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=1.5, foreground="black")]


def render(name, tiles_dir, res=0.2, out=None, box=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cfg = site_cfg(name)
    if box:
        cfg["view"] = tuple(box)
    av = scope_av.load(name)
    img, ext = ortho(name, cfg["view"], res)
    mask, mext = lidar_mask(cfg["view"])
    x0, y0, x1, y1 = cfg["view"]
    w_in = 7.5; h_in = w_in * (y1 - y0) / (x1 - x0) + 0.6
    fig, axes = plt.subplots(1, 2, figsize=(2 * w_in + 0.6, h_in), dpi=160)
    for ax, (variant, colour) in zip(axes, (("live", "#ff3b30"), ("pilot", "#4cff4c"))):
        R = Rows(tiles_dir, variant)
        panel(ax, name, cfg, av, R, R.site_chains(cfg), img, ext, mask, mext, colour, variant)
    fig.text(0.01, 0.005, "Orthophoto: SWISSIMAGE © swisstopo. Cadastre: Amtliche Vermessung, Kanton Zürich (OGD). LiDAR: Kanton Zürich 2021/22 (OGD).", fontsize=5.5)
    os.makedirs(OUT, exist_ok=True)
    out = out or os.path.join(OUT, f"{name}_overlay.png")
    fig.tight_layout(rect=(0, 0.01, 1, 1))
    fig.savefig(out)
    plt.close(fig)
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tiles = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    res = float(sys.argv[sys.argv.index("--res") + 1]) if "--res" in sys.argv else 0.2
    box = [float(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")] if "--box" in sys.argv else None
    for n in (args[0].split(",") if args else ["gerold", "duttweiler"]):
        print(render(n, tiles, res, out=(os.path.join(OUT, f"{n}_zoom.png") if box else None), box=box))
