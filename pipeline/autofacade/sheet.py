"""Validation sheet: photo crop of the sampled wall | hand hex | auto hex. Usage: python sheet.py out.jpg [--n 24] [--seed 1] [--zone 4] [--cal]"""
import argparse
import json
import random

import numpy as np
from PIL import Image, ImageDraw

import extract as X
from aggregate import combine
from common import CACHE, OUT, ROOT, de2000, hex2rgb, lab2rgb, rgb2hex, rgb2lab

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--n", type=int, default=24); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--zone", type=int, default=0); ap.add_argument("--cal", action="store_true"); ap.add_argument("--cols", type=int, default=4)
a = ap.parse_args()
bc = combine(0.0)
tg = json.load(open(OUT / "targets.json"))
notes = {}
for z in (1, 4):
    notes.update(json.load(open(ROOT / f"research/zones/zone{z}_facades.json"))["entries"])
cal = json.load(open(OUT / "calibration.json")) if a.cal else None
cands = [k for k, t in tg.items() if k in notes and notes[k].get("hex") and t["b"] in bc and bc[t["b"]]["ids"] and (not a.zone or t["zone"] == a.zone)]
random.seed(a.seed)
pick = random.sample(cands, min(a.n, len(cands)))
pose = json.load(open(CACHE / "imgs_pose.json"))
CW, CH = 380, 150
cols = a.cols
rows = (len(pick) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (CW + 8), rows * (CH + 22)), (30, 30, 30))
dr = ImageDraw.Draw(sheet)
for n, ad in enumerate(pick):
    b = tg[ad]["b"]
    c = bc[b]
    lab = np.array(c["lab"])
    if cal:
        lab = lab @ np.array(cal["M"]).T + np.array(cal["t"])
    ah = rgb2hex(lab2rgb(lab))
    hh = notes[ad]["hex"]
    de = de2000(lab, rgb2lab(hex2rgb(hh)))
    x0, y0 = (n % cols) * (CW + 8), (n // cols) * (CH + 22)
    iid = c["ids"][0]
    try:
        res, rgb, idm, (xs, ys, sel, bi) = X.process(iid, pose[iid], dbg=True)
        m = sel & (bi == b)
        im = Image.fromarray(rgb.astype(np.uint8))
        if m.sum():
            ax0, ax1, ay0, ay1 = xs[m].min(), xs[m].max(), ys[m].min(), ys[m].max()
            pad = 20
            box = (max(0, ax0 - pad), max(0, ay0 - pad), min(im.width, ax1 + pad), min(im.height, ay1 + pad))
            im = im.crop(box)
            d2 = ImageDraw.Draw(im)
            for xx, yy in list(zip(xs[m], ys[m]))[::23]:
                d2.point((xx - box[0], yy - box[1]), fill=(255, 0, 255))
            d2.rectangle([0, 0, 3, 3], fill=(255, 0, 255))
        sc = min((CW - 90) / im.width, CH / im.height); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))))
        sheet.paste(im, (x0, y0 + 20))
    except Exception as e:
        dr.text((x0, y0 + 30), str(e)[:40], fill=(255, 80, 80))
    dr.rectangle([x0 + CW - 86, y0 + 20, x0 + CW - 44, y0 + 20 + CH - 1], fill=tuple(int(v) for v in hex2rgb(hh)))
    dr.rectangle([x0 + CW - 42, y0 + 20, x0 + CW - 2, y0 + 20 + CH - 1], fill=tuple(int(v) for v in hex2rgb(ah)))
    dr.text((x0 + 2, y0 + 4), f"{ad[:24]} dE{de:.0f} n{c['n_imgs']} {hh}>{ah}", fill=(230, 230, 230))
sheet.thumbnail((1600, 1600))
sheet.save(a.out, quality=82)
print(sheet.size)
