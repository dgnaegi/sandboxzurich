"""OGD art (Kunst im Stadtraum) and public toilets as local points: [(x, y, kind, title)]."""
import json
from config import ROOT
import sources


def load():
    out = []
    for fn, kind in (("kunst_im_stadtraum", "art"), ("zueri_wc", "wc")):
        for f in json.load(open(ROOT / f"data/raw/stadtzh_extra/{fn}.geojson"))["features"]:
            g = f.get("geometry")
            if not g:
                continue
            c = g["coordinates"]
            while isinstance(c[0], list):
                c = c[0]
            x, y = (c[0] - 2681400, c[1] - 1248700) if c[0] > 1e5 else sources.geo.to_local(c[0], c[1])
            pr = f["properties"]
            title = str(pr.get("titel") or pr.get("name") or "")
            if kind == "wc" and "Pissoir" in title:
                continue
            out.append((float(x), float(y), kind, title))
    return out
