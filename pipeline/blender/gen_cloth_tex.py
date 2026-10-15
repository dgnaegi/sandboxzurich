"""Pre-step (system python): MakeHuman logo removal + per-figure recolour of the CC0 clothes diffuse textures.

Writes data/cache/humans/clean/_logo_<tex>.png (logo-free originals, used for npc_00..15 with their hue tint)
and clean/npc_NN_<tex>.png (recoloured: shirt colour, jeans variant) for npc_16+.
"""
import os, sys, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import human_specs as S
SRC = "/Users/danielgnagi/Library/Application Support/Blender/5.2/extensions/.user/user_default/mpfb/data/clothes"
OUT = "/Users/danielgnagi/gtazurich/data/cache/humans/clean"
K = 2048 / 500.0
# logo clone-outs in 500px coords: (x0,y0,x1,y1, dx,dy) = copy the patch shifted by (dx,dy) over the rect
CLONE = {
 "female_casualsuit01": [(350, 62, 458, 168, -245, 0)],
 "female_casualsuit02": [(350, 65, 448, 165, -245, 0)],
 "male_casualsuit02": [(235, 38, 335, 128, -205, 0)],
 "male_casualsuit04": [(222, 38, 318, 132, -205, 0)],
 "male_casualsuit06": [(205, 52, 325, 102, 0, 90), (100, 58, 145, 90, 0, 90), (358, 72, 385, 96, 0, 90)],
}
CORNER = (385, 466, 500, 500, 0, -38)      # www.makehuman.org watermark
REG = {  # shirt rects / jeans rects (500px coords); None = hue-class split for jackets
 "female_casualsuit01": ([(0, 0, 500, 215), (365, 285, 500, 425)], [(0, 215, 365, 500)]),
 "female_casualsuit02": ([(0, 0, 500, 215), (365, 285, 500, 425)], [(0, 200, 365, 500)]),
 "female_sportsuit01": ([(0, 0, 500, 215), (365, 285, 500, 425)], [(0, 215, 365, 500)]),
 "male_casualsuit02": ([(0, 0, 500, 205), (370, 0, 500, 500)], [(0, 205, 370, 500)]),
 "male_casualsuit04": ([(0, 0, 500, 205)], [(0, 205, 500, 500)]),
 "male_casualsuit06": ([(0, 0, 500, 215)], [(0, 215, 500, 500)]),
}
def rect(a, r):
    x0, y0, x1, y1 = [int(v * K) for v in r[:4]]; return a[y0:y1, x0:x1]
def clean(name):
    f = glob.glob(f"{SRC}/{name}/{name}_diffuse.png")[0]
    a = np.array(Image.open(f).convert("RGB"))
    for r in CLONE.get(name, []) + [CORNER]:
        x0, y0, x1, y1 = [int(v * K) for v in r[:4]]; dx, dy = int(r[4] * K), int(r[5] * K)
        a[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return a
def mask_of(shape, rects):
    m = np.zeros(shape[:2], bool)
    for r in rects:
        x0, y0, x1, y1 = [int(v * K) for v in r]; m[y0:y1, x0:x1] = True
    return m
def lum(a): return a @ np.array([0.3, 0.59, 0.11])
def recolor_flat(a, m, c, lo=0.55, hi=1.35):
    af = a.astype(np.float32) / 255; L = lum(af); Lm = max(L[m].mean(), 1e-3)
    f = np.clip(L / Lm, lo, hi)[..., None]
    out = af.copy(); out[m] = np.clip(np.array(c, np.float32) * f[m] * 1.0, 0, 1) ** (1 / 1.0)
    return (out * 255).astype(np.uint8)
def jeans(a, m, var):
    af = a.astype(np.float32) / 255
    k = {"natural": 1.0, "dark": 0.55, "black": 0.22, "light": 1.25}[var]
    if var == "black":
        L = lum(af)[..., None]; af2 = L * np.array([0.5, 0.5, 0.55]) * 0.6
    else:
        af2 = af * k
        if var == "light": af2 = af2 * 0.8 + lum(af)[..., None] * 0.2 * 1.25
    af[m] = np.clip(af2[m], 0, 1)
    return (af * 255).astype(np.uint8)
def hue_jeans_mask(a):
    h = np.array(Image.fromarray(a).convert("HSV")).astype(np.float32) / 255
    return (h[..., 0] > 0.50) & (h[..., 0] < 0.72) & (h[..., 1] > 0.1)
def build(spec, idx):
    name = spec["outfit"]; a = clean(name); col = S.C[spec["shirt"]]
    if name in REG:
        sr, jr = REG[name]; sm = mask_of(a.shape, sr); jm = mask_of(a.shape, jr)
        if name == "female_sportsuit01": a = recolor_flat(a, jm & (lum(a.astype(np.float32) / 255) < 0.5), (0.1, 0.1, 0.11)); jm = jm & False
        a = recolor_flat(a, sm & ~jm, col)
        if jm.any(): a = jeans(a, jm, spec["jeans"])
    else:   # jackets: non-jeans pixels recoloured, jeans by hue class
        jm = hue_jeans_mask(a); lm = lum(a.astype(np.float32) / 255) > 0.04
        a = recolor_flat(a, ~jm & lm, col, 0.4, 1.8); a = jeans(a, jm, spec["jeans"])
    return a
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n in sorted(set(["female_casualsuit01", "female_casualsuit02", "female_elegantsuit01", "female_sportsuit01"] + [os.path.basename(p) for p in glob.glob(f"{SRC}/male_*")])):
        Image.fromarray(clean(n)).save(f"{OUT}/_logo_{n}.png")
    for i, sp in enumerate(S.SPECS):
        Image.fromarray(build(sp, i)).save(f"{OUT}/npc_{S.FIRST + i:02d}_{sp['outfit']}.png")
    print("cloth tex ok")
