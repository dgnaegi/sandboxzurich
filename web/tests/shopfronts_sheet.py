"""Contact sheet: per row photo | game shot of the same front, two columns -> preview/shopfronts_v3b.jpg (<=1600 px wide)."""
import json
from PIL import Image, ImageDraw
pick = json.load(open('logs/shopfronts_pick.json'))
W1, W2, H = 260, 520, 195
sheet = Image.new('RGB', (2 * (W1 + W2), ((len(pick) + 1) // 2) * H), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, o in enumerate(pick):
    x0, y0 = (i % 2) * (W1 + W2), (i // 2) * H
    ph = Image.open(o['photo']).convert('RGB'); ph.thumbnail((W1, H)); sheet.paste(ph, (x0, y0))
    g = Image.open(f'logs/sf_shots/{i:02d}.png').convert('RGB').resize((W2, H)); sheet.paste(g, (x0 + W1, y0))
    d.rectangle([x0 + W1, y0, x0 + W1 + 150, y0 + 11], fill=(0, 0, 0)); d.text((x0 + W1 + 2, y0), o['name'][:28], fill=(255, 255, 255))
sheet.save('preview/shopfronts_v3b.jpg', quality=82)
print(sheet.size)
