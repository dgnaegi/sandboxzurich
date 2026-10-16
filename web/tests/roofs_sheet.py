"""Orthophoto | before | after per spot -> preview/roofs_v2.jpg  (run from repo root)"""
import sys
sys.path.insert(0, 'pipeline')
import numpy as np
from PIL import Image
import ortho_roofs
S = {"hardbruecke": (28, 112), "prime": (45, 222), "lochergut": (105, -891), "helvetia": (800, -850)}
rows = []
for n, (x, y) in S.items():
    T = 500; ix, iy = int(x // T), int(y // T); im = ortho_roofs._tile(ix, iy)
    cx, cy = int((x - ix * T) * 2), int(((iy + 1) * T - y) * 2)
    o = Image.fromarray(im[max(0, cy - 130):cy + 130, max(0, cx - 130):cx + 130]).resize((520, 520))
    r = Image.new('RGB', (520 + 800 * 2 // 2, 520))
    a = Image.open(f'preview/roofs_{n}_before.png').convert('RGB').resize((520, 338)); b = Image.open(f'preview/roofs_{n}_after.png').convert('RGB').resize((520, 338))
    r = Image.new('RGB', (1560, 520)); r.paste(o, (0, 0)); r.paste(a, (520, 90)); r.paste(b, (1040, 90)); rows.append(r)
W = Image.new('RGB', (1560, 520 * len(rows)))
for i, r in enumerate(rows): W.paste(r, (0, 520 * i))
W.resize((1200, 400 * len(rows))).save('preview/roofs_v2.jpg', quality=82)
