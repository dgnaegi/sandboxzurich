"""Wild posters v2: pasted poster walls with real past culture events (research/posters/events.json, only approval_needed=false).
Own designs (wildposter_styles), free fonts, no logos/photos. Output: web/public/tex/wildposters.webp (2048x2048 RGBA,
4x4 wall pieces of 1.5 x 1.5 m) + wildposters.json (pieces with venue positions for 'nearby' selection)."""
import json
import random
import zlib

import numpy as np
from PIL import Image

import wildposter_data as D
import wildposter_styles as S
import wildposter_wall as W
from config import ROOT

OUT = ROOT / "web" / "public" / "tex"
CELL, N = 512, 4


def main():
    events, src = D.load()
    rnd = random.Random(11)
    rendered = {e["id"]: S.render(e, random.Random(zlib.crc32(e["id"].encode())), 500, 714) for e in events}
    pos = {e["id"]: D.xy(e) for e in events}
    atlas = Image.new("RGBA", (CELL * N, CELL * N), (150, 145, 135, 0))
    pieces = []
    for k in range(N * N):
        anchor = events[k % len(events)] if k < len(events) * 2 else rnd.choice(events)
        pa = pos[anchor["id"]]
        near = sorted(events, key=lambda e: (np.hypot(pos[e["id"]][0] - pa[0], pos[e["id"]][1] - pa[1]) if pa and pos[e["id"]] else 5000) + rnd.uniform(0, 900))
        chosen = near[:rnd.randint(3, 6)]
        rnd.shuffle(chosen)
        chosen = [c for c in chosen if c is not anchor] + [anchor]   # anchor on top
        im = W.piece(chosen, rnd, rendered)
        atlas.paste(im.resize((CELL, CELL), Image.LANCZOS), ((k % N) * CELL, (k // N) * CELL))
        pieces.append({"top": anchor["id"], "events": [c["id"] for c in chosen], "xy": pa})
    atlas.save(OUT / "wildposters.webp", quality=82, method=6)
    json.dump({"cols": N, "rows": N, "count": N * N, "size_m": [1.5, 1.5], "source": src, "pieces": pieces}, open(OUT / "wildposters.json", "w"))
    prev = ROOT / "preview"
    prev.mkdir(exist_ok=True)
    bg = Image.new("RGBA", atlas.size, (120, 118, 112, 255))
    bg.alpha_composite(atlas)
    bg.convert("RGB").resize((1600, 1600)).save(prev / "wildposters_v2_atlas.jpg", quality=85)
    print("wild poster pieces", N * N, "events", len(events), src, "atlas KB", (OUT / "wildposters.webp").stat().st_size // 1024)


if __name__ == "__main__":
    main()
