"""Campaign posters of the Alternative Linke (portrait F4, 0.895 m x 1.28 m), in the style of the AL posters:
pink field with 'radikal sozial' in huge condensed black type, centred; white band with 'Alternative Linke'.
Own typesetting (Anton, OFL), no copied artwork or logo. Output: web/public/tex/posters.webp + posters.json.
"""
import json

from PIL import Image, ImageDraw, ImageFont

from config import ROOT

OUT = ROOT / "web" / "public" / "tex"
FONT = ROOT / "web" / "public" / "fonts" / "Anton-Regular.ttf"
W, H = 512, 732  # 0.895 m x 1.28 m
PINK, BLACK, WHITE = (238, 62, 128), (16, 16, 16), (248, 246, 244)
VARIANTS = 1


def font(size):
    return ImageFont.truetype(str(FONT), size)


def fit(d, lines, maxw, start):
    s = start
    while s > 20 and max(d.textbbox((0, 0), t, font=font(s))[2] for t in lines) > maxw:
        s -= 2
    return font(s)


def poster():
    im = Image.new("RGB", (W, H), PINK)
    d = ImageDraw.Draw(im)
    band = int(H * 0.14)
    pink_h = H - band
    lines = ["radikal", "sozial"]
    f = fit(d, lines, W - 60, 220)
    boxes = [d.textbbox((0, 0), t, font=f) for t in lines]
    lh = [b[3] - b[1] for b in boxes]
    gap = 14
    y = (pink_h - sum(lh) - gap) / 2
    for t, b, h in zip(lines, boxes, lh):
        d.text(((W - (b[2] - b[0])) / 2 - b[0], y - b[1]), t, font=f, fill=BLACK)
        y += h + gap
    d.rectangle([0, pink_h, W, H], fill=WHITE)
    f2 = fit(d, ["Alternative Linke"], W - 60, 80)
    b = d.textbbox((0, 0), "Alternative Linke", font=f2)
    d.text(((W - (b[2] - b[0])) / 2 - b[0], pink_h + (H - pink_h - (b[3] - b[1])) / 2 - b[1]), "Alternative Linke", font=f2, fill=BLACK)
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    im = poster()
    im.save(OUT / "posters.webp", quality=90)
    json.dump({"w": W, "h": H, "count": VARIANTS, "size_m": [0.895, 1.28]}, open(OUT / "posters.json", "w"))
    im.resize((W // 2, H // 2)).save(ROOT / "preview" / "posters.png")
    print("poster ok")


if __name__ == "__main__":
    main()
