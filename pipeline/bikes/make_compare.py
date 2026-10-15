"""preview/bikes_compare.jpg: reference photo (left, inspiration only) vs. side render (right). Needs renders from render_sheet.py 'each' mode.
usage: python3 make_compare.py <renders_dir>"""
import sys, glob, os
from PIL import Image, ImageDraw
R = "/Users/danielgnagi/gtazurich"; D = f"{R}/data/raw/photos/bikes"; rd = sys.argv[1]
pairs = [("131570544", "road"), ("73205588", "city"), ("75188048", "cargo"), ("81907949", "rental")]
def find(k):
    for f in os.listdir(D):
        if f.startswith(k + "_"): return f"{D}/{f}"
    raise SystemExit("no ref " + k)
W, H = 640, 420; S = Image.new("RGB", (2 * W, H * len(pairs)), "white"); d = ImageDraw.Draw(S)
for i, (ref, typ) in enumerate(pairs):
    a = Image.open(find(ref)).convert("RGB"); a.thumbnail((W, H)); S.paste(a, (0, i * H))
    b = Image.open(f"{rd}/{typ}.png").convert("RGB"); b = b.crop((int(b.width * .08), int(b.height * .1), int(b.width * .92), int(b.height * .9))); b.thumbnail((W, H)); S.paste(b, (W, i * H))
    d.text((W + 6, i * H + 4), typ, fill="yellow")
S.save(f"{R}/preview/bikes_compare.jpg", quality=85)
