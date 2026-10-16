"""preview/sweep_tmp/*.jpg -> preview/sweep_<type>.jpg contact sheets (3 columns, 480 px per image, caption)."""
import glob, os, re
from collections import defaultdict
from PIL import Image, ImageDraw
g = defaultdict(list)
for f in sorted(glob.glob("preview/sweep_tmp/*.jpg")):
    g[re.sub(r"_\d+\.jpg$", "", os.path.basename(f))].append(f)
for t, fs in g.items():
    ims = [Image.open(f).resize((480, 300)) for f in fs]
    cols = 3; rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (480 * cols, 300 * rows), "black")
    for i, im in enumerate(ims):
        ImageDraw.Draw(im).text((6, 4), f"{t} #{i}", fill="yellow")
        sh.paste(im, ((i % cols) * 480, (i // cols) * 300))
    sh.save(f"preview/sweep_{t}.jpg", quality=72)
    print(t, len(ims))
