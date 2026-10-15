"""Contact sheet: python sheet.py out.jpg cols tile_w img1 img2 ...   (uses .venv PIL)"""
import sys
from PIL import Image
out, cols, tw, *ims = sys.argv[1:]; cols = int(cols); tw = int(tw)
im = [Image.open(p).convert("RGB") for p in ims]; th = int(im[0].height * tw / im[0].width)
rows = (len(im) + cols - 1) // cols; S = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
for i, x in enumerate(im): S.paste(x.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
S.save(out, quality=82)
