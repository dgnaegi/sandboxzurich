"""Photo (800x600) with pixel grid for reading object pixel positions. usage: fidelity_grid.py out.jpg ids..."""
import json, sys
from PIL import Image, ImageDraw
out, ids = sys.argv[1], [int(i) for i in sys.argv[2:]]
cand = {c['id']: c for c in json.load(open('research/fidelity_cand.json'))}
W, H = 800, 600
sh = Image.new('RGB', (2 * W, ((len(ids) + 1) // 2) * H))
for j, i in enumerate(ids):
    im = Image.open(cand[i]['file']).convert('RGB').resize((W, H)); d = ImageDraw.Draw(im)
    for x in range(100, W, 100): d.line((x, 0, x, H), fill=(255, 255, 255), width=1); d.text((x + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(100, H, 100): d.line((0, y, W, y), fill=(255, 255, 255), width=1); d.text((2, y + 2), str(y), fill=(255, 255, 0))
    d.text((6, 14), f'#{i}', fill=(0, 255, 255)); sh.paste(im, ((j % 2) * W, (j // 2) * H))
sh.save(out, quality=72)
