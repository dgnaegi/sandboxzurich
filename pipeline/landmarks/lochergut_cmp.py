"""Photo | game comparison sheet for the Lochergut. Usage: python lochergut_cmp.py -> preview/lochergut_cmp.jpg (game shots from free_shot.mjs: preview/loch_cmp_<i>.jpg)"""
import json, sys
from PIL import Image, ImageDraw
ROOT = "/Users/danielgnagi/sandboxzurich/"
idx = json.load(open(ROOT + "data/raw/photos/lochergut/index.json"))
PH = [47, 52, 70, 22, 72, 49, 27, 56]
W, H = 400, 250
sh = Image.new("RGB", (W * 4, H * 4), "#222"); d = ImageDraw.Draw(sh)
for i, ph in enumerate(PH):
    a = Image.open(ROOT + idx[ph]).convert("RGB"); g = Image.open(ROOT + f"preview/loch_cmp_{i}.jpg").convert("RGB")
    for k, im in enumerate((a, g)):
        im.thumbnail((W, H)); col = (i % 2) * 2 + k; row = i // 2
        sh.paste(im, (col * W, row * H)); d.text((col * W + 3, row * H + 3), ("Foto %d" % ph) if k == 0 else "Spiel", fill="yellow")
sh.save(ROOT + "preview/lochergut_cmp.jpg", quality=80); print("ok")
