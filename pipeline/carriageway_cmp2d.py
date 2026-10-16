"""2D comparison: orthophoto | old OSM carriageway outline | new carriageway outline (+ AV carriageway) at the 10 check places.

  .venv/bin/python pipeline/carriageway_cmp2d.py   -> preview/carriageway_cmp2d_<place>.jpg
Independent of the tile build (uses streets.parse with SBZ_CARRIAGEWAY=osm / av)."""
import os
import sys
from pathlib import Path

import numpy as np
import shapely
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import groundcover  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
from carriageway_audit import rgb_at  # noqa: E402
from config import AREA, ROOT  # noqa: E402

PLACES = {  # name: (x, y) local metres (as in web/tests/plaza.mjs)
    "langstrasse": (753, -557), "helvetiaplatz": (785, -885), "stauffacher": (960, -1245), "albisriederplatz": (-495, -668),
    "hardplatz": (-110, -175), "escher_wyss": (455, 715), "lochergut": (81, -958), "idaplatz": (-140, -1135),
    "bullingerplatz": (-41, -522), "lindenplatz": (-2395, 350),
}
SIZE, PX = 120.0, 720
PLACES = {k: tuple(min(max(v, (v // 200) * 200 + SIZE / 2), (v // 200) * 200 + 200 - SIZE / 2) for v in xy) for k, xy in PLACES.items()}  # view window inside one 200 m tile (only the test tiles are rebuilt)



def outline(d, geom, bounds, col, w=2):
    x0, y1 = bounds
    k = PX / SIZE
    for p in shapely.get_parts(geom.intersection(shapely.box(x0, y1 - SIZE, x0 + SIZE, y1))):
        if p.geom_type != "Polygon":
            continue
        for ring in [p.exterior, *p.interiors]:
            d.line([((x - x0) * k, (y1 - y) * k) for x, y in ring.coords], fill=col, width=w)


def main():
    from carriageway_audit import parse_both  # --cached reuses data/build/carr_audit_parse.pkl
    So, Sn = parse_both()
    G = groundcover.load((AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260))
    for name, (cx, cy) in PLACES.items():
        x0, y1 = cx - SIZE / 2, cy + SIZE / 2
        xs = x0 + (np.arange(PX) + 0.5) * SIZE / PX
        ys = y1 - (np.arange(PX) + 0.5) * SIZE / PX
        X, Y = np.meshgrid(xs, ys)
        rgb = rgb_at(X.ravel(), Y.ravel()).reshape(PX, PX, 3)
        base = Image.fromarray(np.nan_to_num(rgb).astype(np.uint8))
        out = Image.new("RGB", (PX * 3, PX))
        out.paste(base, (0, 0))
        for i, (S, col) in enumerate(((So, (255, 60, 40)), (Sn, (40, 230, 255))), 1):
            im = base.copy()
            d = ImageDraw.Draw(im)
            outline(d, G["carriageway"], (x0, y1), (255, 255, 0), 1)
            outline(d, S["roads"], (x0, y1), col, 2)
            out.paste(im, (PX * i, 0))
        ImageDraw.Draw(out).text((8, 8), f"{name}  Orthofoto | alt (rot) | neu (cyan); gelb = AV-Fahrbahn", fill=(255, 255, 255))
        out.resize((PX * 3 * 2 // 3, PX * 2 // 3)).save(ROOT / "preview" / f"carriageway_cmp2d_{name}.jpg", quality=85)
        print(name)


if __name__ == "__main__":
    main()
