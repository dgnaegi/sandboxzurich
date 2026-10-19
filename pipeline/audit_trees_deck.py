"""Audit: trees poking through / standing on bridge decks (built tiles). Usage: .venv/bin/python pipeline/audit_trees_deck.py [--list]
A tree conflicts with a deck if its trunk (or half crown) lies in the deck footprint and its top (ground + height) reaches the deck
underside, or its ground is at deck level (on the deck). Prints counts + worst places (<= 30 lines)."""
import glob, json, sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

R = Path(__file__).resolve().parent.parent


def load():
    decks, trees = [], []
    for f in glob.glob(str(R / "web/public/tiles/t_*.json")):
        m = json.load(open(f))
        for d in m.get("bridges", {}).get("decks", []):
            p = d["p"]
            for i in range(len(p) - 1):
                if min(p[i][2] - d["g"][i], p[i + 1][2] - d["g"][i + 1]) < 0.3:
                    continue
                decks.append((LineString([q[:2] for q in p[i:i + 2]]).buffer(d["w"] / 2 + 0.3, cap_style="flat"),
                              (p[i][2], p[i + 1][2], d["b"][i], d["b"][i + 1]), d["kind"], d["name"]))
        trees += m.get("trees", [])
    return decks, trees


def conflicts(decks, trees):
    st = STRtree([d[0] for d in decks])
    out = []
    for t in trees:
        x, y, z, _, dc, h = t[:6]
        pt = Point(x, y)
        for j in st.query(pt.buffer(dc * 0.25)):
            g, (z0, z1, b0, b1), kind, name = decks[j]
            if not g.intersects(pt.buffer(dc * 0.25)):
                continue
            under = min(b0, b1)
            top = z + h
            if z > under - 0.5:
                out.append((x, y, "on-deck", kind, name, round(z - under, 1)))
            elif top > under - 0.1:
                out.append((x, y, "pierce", kind, name, round(top - under, 1)))
            break
    return out


if __name__ == "__main__":
    decks, trees = load()
    c = conflicts(decks, trees)
    from collections import Counter
    print(f"{len(trees)} trees, {len(decks)} deck segments: {len(c)} conflicts "
          f"({dict(Counter(k[2] for k in c))}) by name {dict(Counter(k[4] or k[3] for k in c).most_common(8))}")
    if "--list" in sys.argv:
        for k in c[:25]:
            print(k)
