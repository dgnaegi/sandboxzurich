"""Fictional graffiti tags (spray-paint look with drips), RGBA atlas 4x4 for wall decals in Kreis 4.
No real artists' works, no insults. Output: web/public/tex/graffiti.png"""
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import ROOT

F = ROOT / "web" / "public" / "fonts"
WORDS = ["8004", "K4", "AXS", "ZÜRI", "LOVE", "SIHL", "ROXY", "TANK", "MOSH", "OKAY", "BLAU", "NOVA", "ZACK", "KREIS4", "HOI", "TAKE"]
COLS = [(230, 40, 120), (30, 30, 30), (250, 210, 30), (40, 170, 230), (255, 255, 255), (230, 80, 30), (90, 200, 90), (150, 60, 200)]
S = 256


def tag(i, rnd):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    word = WORDS[i % len(WORDS)]
    col = rnd.choice(COLS)
    outline = (20, 20, 20) if sum(col) > 300 else (250, 250, 250)
    font = ImageFont.truetype(str(F / rnd.choice(["Anton-Regular.ttf", "ArchivoBlack-Regular.ttf", "BarlowCondensed-Bold.ttf"])), 80)
    tw = d.textlength(word, font=font)
    scale = min(1.0, (S - 30) / max(tw, 1))
    font = ImageFont.truetype(font.path, int(80 * scale))
    tw = d.textlength(word, font=font)
    x, y = (S - tw) / 2, S / 2 - 50
    if i % 3 == 0:  # bubble style piece with outline
        d.text((x, y), word, font=font, fill=col, stroke_width=6, stroke_fill=outline)
    else:          # quick tag: thin, slanted
        d.text((x, y), word, font=font, fill=col)
    a = np.array(im)
    # drips under the letters
    for _ in range(rnd.randint(2, 7)):
        cx = rnd.randint(int(x), int(x + tw))
        ys = np.nonzero(a[:, cx, 3])[0]
        if len(ys):
            y0, L = ys.max(), rnd.randint(8, 40)
            a[y0:min(S, y0 + L), max(0, cx - 1):cx + 2] = (*col, 230)
    im = Image.fromarray(a).rotate(rnd.uniform(-8, 12), resample=Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(0.8))  # sprayed edges
    alpha = np.array(im)[..., 3].astype(np.float32) * rnd.uniform(0.75, 0.95)  # weathered
    out = np.array(im); out[..., 3] = alpha.astype(np.uint8)
    return Image.fromarray(out)


def main():
    rnd = random.Random(8004)
    sheet = Image.new("RGBA", (S * 4, S * 4), (0, 0, 0, 0))
    for i in range(16):
        sheet.paste(tag(i, rnd), ((i % 4) * S, (i // 4) * S))
    sheet.save(ROOT / "web" / "public" / "tex" / "graffiti.png", optimize=True)
    bg = Image.new("RGBA", sheet.size, (200, 195, 185, 255)); bg.alpha_composite(sheet)
    bg.convert("RGB").resize((512, 512)).save(ROOT / "preview" / "graffiti.png")
    print("graffiti ok")


if __name__ == "__main__":
    main()
