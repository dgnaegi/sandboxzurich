"""Contact sheet of images: python schlachthof_sheet.py out.jpg cols w img1 img2 ..."""
import sys
from PIL import Image
out, cols, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in fs]; ims = [i.resize((W, int(i.height * W / i.width))) for i in ims]
H = max(i.height for i in ims); rows = (len(ims) + cols - 1) // cols
s = Image.new("RGB", (cols * W, rows * H), (25, 25, 25))
for k, i in enumerate(ims): s.paste(i, ((k % cols) * W, (k // cols) * H))
s.save(out, quality=84)
