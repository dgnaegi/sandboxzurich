"""Contact sheets for the Idaplatz photos: preview/ref_ida_<site>_<n>.jpg (12 per sheet, 4x3, 400x300 cells, labelled with global index).
Writes research/v3/ida_index.json (index -> file, source, lat, lon, heading). Usage: python sheet_ida.py [site,site]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
meta = json.load(open(ROOT / "research/v3/photos_ida.json"))
only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
idx, items = {}, []
for sid, m in meta.items():
    for p in m["photos"]:
        i = len(idx); idx[i] = dict(site=sid, **{k: p.get(k) for k in ("file", "source", "author", "license", "url", "lat", "lon", "heading", "year")})
        if not only or sid in only: items.append((i, sid, p))
json.dump(idx, open(ROOT / "research/v3/ida_index.json", "w"), ensure_ascii=False)
W, H = 400, 300
by = {}
for i, sid, p in items: by.setdefault(sid, []).append((i, p))
for sid, L in by.items():
    for s in range(0, len(L), 12):
        sh = Image.new("RGB", (4 * W, 3 * H), (25, 25, 25)); d = ImageDraw.Draw(sh)
        for k, (i, p) in enumerate(L[s:s + 12]):
            try:
                im = Image.open(ROOT / p["file"]).convert("RGB"); im.thumbnail((W - 4, H - 4))
                sh.paste(im, ((k % 4) * W + 2, (k // 4) * H + 2))
            except Exception: pass
            d.rectangle([(k % 4) * W, (k // 4) * H, (k % 4) * W + 44, (k // 4) * H + 16], fill=(0, 0, 0))
            d.text(((k % 4) * W + 3, (k // 4) * H + 2), f"#{i}", fill=(255, 220, 0))
        sh.save(ROOT / f"preview/ref_ida_{sid}_{s // 12}.jpg", quality=78)
print(len(idx), "photos;", sum((len(v) + 11) // 12 for v in by.values()), "sheets")
