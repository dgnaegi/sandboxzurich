"""Before/after sheet: for each 60 m cell game(before) | game(after) | ortho (SWISSIMAGE 0.25 m), 4 px/m, 2 cells per row.
usage: .venv/bin/python pipeline/markings_plaus_cmp.py <dir_before_glbs> "x,y;x,y;..." <out.jpg> [dir_after_glbs]   (after default data/build/tiles_raw)"""
import sys, math
from pathlib import Path
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import markings_plaus as MP

before, spec, out = sys.argv[1], sys.argv[2], sys.argv[3]
after = sys.argv[4] if len(sys.argv) > 4 else str(R / "data/build/tiles_raw")
cells = [tuple(map(float, c.split(","))) for c in spec.split(";")]
n = MP.CELL * MP.PX
S = Image.new("RGB", (2 * (3 * n + 8) + 4, math.ceil(len(cells) / 2) * (n + 14)), (255, 255, 255)); d = ImageDraw.Draw(S)
for i, (cx, cy) in enumerate(cells):
    r, c = divmod(i, 2); ox, oy = c * (3 * n + 8) + 4, r * (n + 14)
    MP._cache.clear()
    S.paste(MP.render_game(before, cx, cy), (ox, oy + 14))
    MP._cache.clear()
    S.paste(MP.render_game(after, cx, cy), (ox + n + 2, oy + 14))
    S.paste(MP.render_ortho(cx, cy), (ox + 2 * n + 4, oy + 14))
    d.text((ox, oy), f"#{i} {cx:.0f},{cy:.0f}   before | after | ortho (SWISSIMAGE)", fill=(0, 0, 0))
S = S.resize((1600, int(S.height * 1600 / S.width))); S.save(out, quality=88); print(out)
