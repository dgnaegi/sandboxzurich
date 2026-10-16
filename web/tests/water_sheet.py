"""Contact sheet of water shots: python web/tests/water_sheet.py before|after [more tags...] -> preview/water_<tag>.jpg"""
import sys
from PIL import Image
P = "preview/"
S = ["sihlhoelzli", "sihl_k4", "limmat_wipkinger", "limmat_hardbr"]
def sheet(tags, out):
    rows = []
    for t in tags:
        for suf in ("", "_top", "_n"):
            fs = [f"{P}water_{t}_{s}{suf}.png" for s in S]
            try: rows.append([Image.open(f).convert("RGB") for f in fs])
            except FileNotFoundError: pass
    W, H = 400, 225
    im = Image.new("RGB", (W * 4, H * len(rows)))
    for r, row in enumerate(rows):
        for c, i in enumerate(row):
            i.thumbnail((W, H)); im.paste(i, (c * W, r * H))
    im.save(out, quality=82)
if __name__ == "__main__":
    t = sys.argv[1:]
    sheet(t, f"{P}water_{t[0]}.jpg")
