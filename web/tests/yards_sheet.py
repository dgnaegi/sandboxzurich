# contact sheet of preview/yards_shots -> preview/yards_v1.jpg (top row: game top-downs, ≤1600 px wide)
import glob, sys
from PIL import Image
fs = sorted(glob.glob('preview/yards_shots/top_*.png')) + sorted(glob.glob('preview/yards_shots/*_e.png'))
im = [Image.open(f).convert('RGB').resize((400, 400)) for f in fs]
W = 4; rows = (len(im) + W - 1) // W
S = Image.new('RGB', (400 * W, 400 * rows), 'white')
for i, a in enumerate(im): S.paste(a, ((i % W) * 400, (i // W) * 400))
S.save('preview/yards_v1.jpg', quality=82); print(len(im), 'images')
