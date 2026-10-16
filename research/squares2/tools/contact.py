"""contact.py id [from to] -> research/squares2/contact_<id>.jpg (numbered thumbs, 5 cols)"""
import json, sys
from PIL import Image, ImageDraw
pid = sys.argv[1]
ph = json.load(open("research/squares2/photos.json"))[pid]["photos"]
a = int(sys.argv[2]) if len(sys.argv) > 2 else 0; b = int(sys.argv[3]) if len(sys.argv) > 3 else len(ph)
w, h, cols = 310, 232, 5
n = b - a; rows = (n + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "white"); d = ImageDraw.Draw(S)
for k, i in enumerate(range(a, b)):
    try: im = Image.open(ph[i]["file"]).convert("RGB").resize((w - 4, h - 4))
    except Exception: continue
    S.paste(im, ((k % cols) * w + 2, (k // cols) * h + 2)); d.rectangle([(k % cols) * w + 2, (k // cols) * h + 2, (k % cols) * w + 34, (k // cols) * h + 18], fill="black"); d.text(((k % cols) * w + 6, (k // cols) * h + 5), str(i), fill="yellow")
S.save(f"research/squares2/contact_{pid}.jpg", quality=80)
