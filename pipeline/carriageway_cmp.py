"""Compose preview/carriageway_cmp_<place>.jpg = orthophoto | before | after (game top-down, web/tests/carriageway_shots.mjs)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carriageway_audit import rgb_at  # noqa: E402
from carriageway_cmp2d import PLACES, SIZE  # noqa: E402
from config import ROOT  # noqa: E402

PV = ROOT / "preview"
PX = 720
for name, (cx, cy) in PLACES.items():
    a, b = PV / f"_carr_before_{name}.png", PV / f"_carr_after_{name}.png"
    if not (a.exists() and b.exists()):
        print("missing", name)
        continue
    xs = cx - SIZE / 2 + (np.arange(PX) + 0.5) * SIZE / PX
    ys = cy + SIZE / 2 - (np.arange(PX) + 0.5) * SIZE / PX
    X, Y = np.meshgrid(xs, ys)
    o = Image.fromarray(np.nan_to_num(rgb_at(X.ravel(), Y.ravel())).reshape(PX, PX, 3).astype(np.uint8))
    out = Image.new("RGB", (PX * 3, PX))
    for i, im in enumerate((o, Image.open(a).convert("RGB").resize((PX, PX)), Image.open(b).convert("RGB").resize((PX, PX)))):
        out.paste(im, (i * PX, 0))
    ImageDraw.Draw(out).text((8, 8), f"{name}: Orthofoto | vorher | nachher", fill=(255, 255, 0))
    out.resize((PX * 2, PX * 2 // 3)).save(PV / f"carriageway_cmp_{name}.jpg", quality=85)
