"""usage: ortho.py id x y  -> data/raw/ortho_places/ortho_<id>.jpg (140 m square, same format as the others) + centers.json entry"""
import sys, json
sys.path.insert(0, "pipeline")
from pathlib import Path
import numpy as np
from PIL import Image
import streets_ortho as SO
pid, x, y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
m = SO._mosaic(x - 70, y - 70, x + 70, y + 70)
rgb, xs, ys = m
im = Image.fromarray(rgb)
print(im.size, xs[0], xs[-1], ys[0], ys[-1])
side = 140.0; ppm = 2
# resample exactly 140 m
W = int(side * ppm)
X = np.linspace(x - 70, x + 70, W); Yv = np.linspace(y + 70, y - 70, W)
ix = np.clip(np.searchsorted(xs, X), 0, len(xs) - 1); iy = np.clip(np.argmin(np.abs(ys[None, :] - Yv[:, None]), axis=1), 0, len(ys) - 1)
out = rgb[iy][:, ix]
Image.fromarray(out).save(f"data/raw/ortho_places/ortho_{pid}.jpg", quality=92)
cp = Path("data/raw/ortho_places/centers.json"); c = json.load(open(cp)); c[pid] = [x, y]; json.dump(c, open(cp, "w"))
