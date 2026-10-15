"""Facade layers v3: neutral plaster (tint = exact observed colour) in shutter-colour / window-style variants,
plus Klinker (brick) and Sandstein (ashlar) walls tinted the same way.

All plaster / brick / stone wall pixels carry mask = 255, so the vertex tint of a building decides the wall colour.
Because the base is a bright neutral, `styles.exact_tint()` can compute a tint that reproduces an arbitrary colour
(measured per layer from the albedo/mask PNGs -> data/build/facades/base_means.json).
Shutters, window frames, stone trim, balconies keep their own baked colour (mask 0) -> one layer per shutter colour.

Usage: .venv/bin/python pipeline/gen_facades3.py [name ...]   (writes data/build/facades/<name>_*.png, base_means.json)
"""
import json
import sys

import numpy as np
from PIL import Image

import gen_facades as G
from gen_facades import F32, STONE, WHITE, ANTH, band, pl

NEUT = (.94, .93, .91)          # bright neutral plaster, tinted per house
SHUT = {"n": None, "g": (.20, .36, .24), "s": (.56, .58, .58), "b": (.36, .21, .14), "u": (.28, .37, .50), "r": (.50, .22, .17)}
SANDSTONE = (.78, .70, .56)


def shut(k, p=.8, closed=.06):
    return dict(col=SHUT[k], p=p, closed=closed) if SHUT[k] else None


def std(name, seed, shutter="n", **P):
    """gen_facades.standard() with the neutral wall and optional shutters."""
    P.setdefault("wall", pl(NEUT, .9))
    if shutter != "n":
        P["shut"] = shut(shutter)
    return G.standard(name, seed, P)


# Gründerzeit: strong cornice bands every floor, tall windows 1.15 x 2.0, optional hoods (Verdachungen)
def gz(name, seed, shutter, win="plain", bal=True):
    wp = dict(w=1.15, h=2.0, cols=2, rows=3, sur=.13, flowers=.25, bar=.03)
    if win == "hood":
        wp.update(cap="tri", sur=.14)
    if win == "arch":
        wp.update(arch=1, w=1.2, h=1.95, sur=.11)
    P = dict(gs=dict(th=.26, prot=.1, col=STONE), win=wp, sillh=.85)
    P["bal"] = dict(floors=[1, 2], axes=[1, 2], w=2.7, kind="bars", dw=1.05, dh=2.2, flowers=.6) if bal else dict(floors=[], axes=[], w=1)
    return std(name, seed, shutter, **P)


def gen(name, seed, shutter):  # Genossenschaft / Heimatstil 1920-50: smaller windows, thin bands
    return std(name, seed, shutter, gs=dict(th=.08, prot=.015, col=(.9, .88, .8), m=1),
               win=dict(w=1.2, h=1.45, cols=2, rows=3, bar=.022, flowers=.25), sillh=.95,
               bal=dict(floors=[1, 3], axes=[0, 2], w=1.7, kind="bars", dw=.95, dh=2.1, flowers=.7))


def nk50(name, seed, shutter):  # 1950-70 plaster block, white frames, solid balconies
    return std(name, seed, shutter, gs=dict(th=.1, prot=.02, col=(.7, .7, .68)),
               win=dict(w=1.35, h=1.4, cols=2, rows=2, bar=.04, frame=WHITE, d=.1, flowers=.15, sillcol=(.62, .62, .6)),
               sillh=.9, bal=dict(floors=[0, 1, 2, 3], axes=[0, 2], w=2.0, kind="solid", col=(.78, .78, .74), dw=1.0, dh=2.1, flowers=.4))


def band60(name, seed):  # 1960-75 ribbon windows with parapet bands (neutral plaster, tinted)
    return std(name, seed, "n", wall=pl(NEUT, .7), parapet=dict(col=(.62, .64, .64), y_from=1.0, y_to=.14),
               win=dict(w=2.7, h=1.3, cols=3, rows=1, bar=.05, frame=(.75, .75, .73), d=.1, sillcol=(.6, .6, .58), sill=False),
               sillh=1.0, bal=dict(floors=[], axes=[], w=1))


def brick_wall(c, cols=((.92, .92, .92), (.74, .74, .74), (.6, .6, .6)), mortar=(.98, .97, .94), bw=.25):
    G.wall_brick(c, cols, mortar=mortar, bw=bw)
    c.m[:] = 1  # tintable: neutral grey bricks take the observed colour
    c.dirt[:] *= .8


def klinker(name, seed, win="plain", era="gz"):
    """Brick facade with sandstone trim (surrounds, sills, bands), windows 1.15 x 2.0."""
    wp = dict(w=1.15, h=2.0, cols=2, rows=3, sur=.12, surc=SANDSTONE, surm=0, flowers=.15, bar=.03, sillcol=SANDSTONE)
    if win == "arch":
        wp.update(arch=1, w=1.2, h=1.9)
    if win == "hood":
        wp.update(cap="flat")
    if era == "50":
        wp = dict(w=2.4, h=1.3, cols=3, rows=1, bar=.05, frame=(.78, .78, .76), d=.12, sillcol=(.6, .6, .58), sill=False)
    return std(name, seed, "n", wall=brick_wall, gs=dict(th=.2 if era == "gz" else .08, prot=.07, col=SANDSTONE),
               win=wp, sillh=.85 if era == "gz" else 1.0,
               bal=dict(floors=[2], axes=[1, 2], w=2.6, kind="bars", dw=1.05, dh=2.2, flowers=.5) if era == "gz" else dict(floors=[], axes=[], w=1))


def sandstein(name, seed, win="hood"):
    def wall(c):
        G.wall_panel(c, [(.93, .93, .93), (.85, .85, .85), (.78, .78, .78), (.9, .9, .9)], 1.0, .5, .014, mask=1)
        c.dirt[:] *= 1.1
    wp = dict(w=1.15, h=2.1, cols=2, rows=3, sur=.12, surc=(.85, .85, .83), surm=1, flowers=.15, bar=.03)
    if win == "hood":
        wp.update(cap="tri")
    if win == "arch":
        wp.update(arch=1)
    return std(name, seed, "n", wall=wall, gs=dict(th=.28, prot=.1, col=(.86, .86, .84), m=1), win=wp, sillh=.85,
               bal=dict(floors=[1], axes=[1, 2], w=2.6, kind="bars", dw=1.05, dh=2.2, flowers=.5))


V3 = {}
for i, (k, nm) in enumerate([("n", "none"), ("g", "green"), ("s", "grey")]):
    V3[f"g3_hood_{k}"] = lambda k=k, i=i: gz(f"g3_hood_{k}", 301 + i, k, "hood")
for i, k in enumerate("ngsbu"):
    V3[f"g3_plain_{k}"] = lambda k=k, i=i: gz(f"g3_plain_{k}", 311 + i, k, "plain")
for i, k in enumerate("ng"):
    V3[f"g3_flat_{k}"] = lambda k=k, i=i: gz(f"g3_flat_{k}", 321 + i, k, "plain", bal=False)
    V3[f"g3_arch_{k}"] = lambda k=k, i=i: gz(f"g3_arch_{k}", 331 + i, k, "arch")
for i, k in enumerate("ngbu"):
    V3[f"e3_gen_{k}"] = lambda k=k, i=i: gen(f"e3_gen_{k}", 341 + i, k)
for i, k in enumerate("ns"):
    V3[f"n3_50_{k}"] = lambda k=k, i=i: nk50(f"n3_50_{k}", 351 + i, k)
V3["n3_band60"] = lambda: band60("n3_band60", 361)
V3["k3_klinker_a"] = lambda: klinker("k3_klinker_a", 371, "plain")
V3["k3_klinker_b"] = lambda: klinker("k3_klinker_b", 372, "arch")
V3["k3_klinker_c"] = lambda: klinker("k3_klinker_c", 373, "hood")
V3["k3_klinker_50"] = lambda: klinker("k3_klinker_50", 374, era="50")
V3["k3_sand_a"] = lambda: sandstein("k3_sand_a", 381, "hood")
V3["k3_sand_b"] = lambda: sandstein("k3_sand_b", 382, "arch")
FACADES3 = list(V3)


def lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)


def measure(name):
    """Mean linear albedo (RGB) over the tintable (mask) pixels of a layer."""
    al = np.asarray(Image.open(G.OUT / f"{name}_albedo.png").convert("RGB"), np.float64) / 255
    m = np.asarray(Image.open(G.OUT / f"{name}_mask.png").convert("L"), np.float64) / 255 > .5
    return lin(al[m]).mean(0).tolist()


def build(name):
    c = V3[name]()
    G.finish(c, name)


def main(names):
    f = G.OUT / "base_means.json"
    means = json.load(open(f)) if f.exists() else {}
    for n in names or FACADES3:
        build(n)
        means[n] = measure(n)
        print("ok", n, [round(v, 2) for v in means[n]], flush=True)
    json.dump(means, open(f, "w"))
    cols = 6
    W = 256
    rows = (len(FACADES3) + cols - 1) // cols
    img = Image.new("RGB", (cols * W, rows * W))
    for i, n in enumerate(FACADES3):
        p = G.OUT / f"{n}_albedo.png"
        if p.exists():
            img.paste(Image.open(p).convert("RGB").resize((W, W), Image.LANCZOS), ((i % cols) * W, (i // cols) * W))
    img.save(G.ROOT / "preview" / "facades_v3_layers.jpg", quality=85)


if __name__ == "__main__":
    main(sys.argv[1:])
