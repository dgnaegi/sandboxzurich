from PIL import Image
import sys
d = sys.argv[1]
def L(n): return Image.open(f"{d}/{n}.png").convert("RGB")
H = 520
def fit(im, h=H): return im.resize((int(im.width * h / im.height), h))
row1 = [fit(L("desktop_map")), fit(L("desktop_zoom"))]
row2 = [fit(L("phone_map")), fit(L("phone_zoom")), fit(L("desktop_radar"), 260), fit(L("phone_radar"), 200)]
W = 1600
def strip(ims):
    w = sum(i.width for i in ims); s = min(1, W / w)
    ims = [i.resize((int(i.width * s), int(i.height * s))) for i in ims]
    im = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)), (30, 30, 30)); x = 0
    for i in ims: im.paste(i, (x, 0)); x += i.width
    return im
a, b = strip(row1), strip(row2)
sheet = Image.new("RGB", (max(a.width, b.width), a.height + b.height), (30, 30, 30)); sheet.paste(a, (0, 0)); sheet.paste(b, (0, a.height))
sheet.save(sys.argv[2], quality=82)
