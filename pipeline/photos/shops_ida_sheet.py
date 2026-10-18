"""Idaplatz venues: best photos from research/v3/ida_index.json (<=35 m, looking at the venue) -> preview/ref_ida_shops_N.jpg (label = venue)."""
import json, math
from pathlib import Path
from PIL import Image, ImageDraw
from pyproj import Transformer
ROOT = Path(__file__).resolve().parent.parent.parent
T = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
V = {"n3010412639": ("Le Calvados", -164, -1108), "n345525376": ("Beke", -109, -1029), "n906856274": ("Berta Bar", -169, -1079), "n1434789864": ("Bottega Berta", -211, -1113),
     "n3210925379": ("Chornlade", -157, -1068), "n8071658525": ("pompon", -100, -1087), "n4993486522": ("Smoking Kiosk", -107, -1115), "n2463374628": ("Restaurant Gertrudhof", -49, -1133),
     "n2463374534": ("Hotel Gertrud", -19, -1107), "n3689198434": ("La Piccola Trattoria", -204, -1141), "n7204669291": ("Tapas & Friends", -198, -1151), "n6718125166": ("WheelHouse", -118, -1037),
     "n10244452409": ("Liquid Hair Saloon", -95, -1126), "n10946043352": ("Garde Manger", -67, -1033), "n10946043353": ("Babus Bakery", -58, -1043), "n3110688142": ("Da Michelangelo", -90, -1196),
     "n3514833394": ("Poli", -148, -1217), "n335568984": ("Mobility Idaplatz", -167, -1125), "n11850092277": ("Kaelin Mueller", -105, -1058), "n10856053174": ("Duplikat Buch", -71, -1029)}
idx = json.load(open(ROOT / "research/v3/ida_index.json"))
P = []
for k, p in idx.items():
    if p["lat"] and p["heading"] is not None:
        e, n = T.transform(p["lon"], p["lat"]); P.append((int(k), e - 2681400, n - 1248700, p["heading"], p["file"]))
out = {}
for vid, (nm, x, y) in V.items():
    c = []
    for i, px, py, hd, f in P:
        d = math.hypot(x - px, y - py)
        if d < 6 or d > 38: continue
        br = math.degrees(math.atan2(x - px, y - py)) % 360
        df = abs((br - hd + 180) % 360 - 180)
        if df < 30: c.append((d * 0.1 + df * 0.5, i, f, round(d)))
    c.sort(); out[vid] = c[:2]
items = [(vid, V[vid][0], c) for vid, cs in out.items() for c in cs]
W, H = 400, 300
for s in range(0, len(items), 12):
    sh = Image.new("RGB", (4 * W, 3 * H), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for k, (vid, nm, c) in enumerate(items[s:s + 12]):
        im = Image.open(ROOT / c[2]).convert("RGB"); im.thumbnail((W - 4, H - 4)); sh.paste(im, ((k % 4) * W + 2, (k // 4) * H + 2))
        d.rectangle([(k % 4) * W, (k // 4) * H, (k % 4) * W + 260, (k // 4) * H + 14], fill=(0, 0, 0)); d.text(((k % 4) * W + 3, (k // 4) * H + 1), f"{nm} #{c[1]} {c[3]}m", fill=(255, 220, 0))
    sh.save(ROOT / f"preview/ref_ida_shops_{s // 12}.jpg", quality=80)
print({V[v][0]: len(c) for v, c in out.items()}, len(items))
