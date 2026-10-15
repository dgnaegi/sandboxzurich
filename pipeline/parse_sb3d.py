"""Stream-parse swissBUILDINGS3D CityGML tiles of the whole game area into local-metre pickles.

Output: data/build/bld/<tile>.pkl, same format as ../gta6/data/bld/*.pkl
(list of {id, h, type, polys: [(kind 0=ground/1=wall/2=roof, Nx3 float32)]}).
Usage: python pipeline/parse_sb3d.py [tile-substring ...]
"""
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "sb3d"
DST = ROOT / "data" / "build" / "bld"
ORIGIN = (2681400.0, 1248700.0, 408.0)
AREA = (-2600.0, -2900.0, 1900.0, 1300.0)  # local metres, centroid filter
NS = {"gml": "http://www.opengis.net/gml", "bldg": "http://www.opengis.net/citygml/building/2.0",
      "core": "http://www.opengis.net/citygml/2.0", "gen": "http://www.opengis.net/citygml/generics/2.0"}
KIND = {"GroundSurface": 0, "WallSurface": 1, "RoofSurface": 2}
X0, Y0, X1, Y1 = AREA


def parse(src, dst):
    out, n = [], 0
    for _, el in etree.iterparse(str(src), tag="{%s}cityObjectMember" % NS["core"], huge_tree=True):
        b = el.find("bldg:Building", NS)
        n += 1
        if n % 20000 == 0:
            print(f"  {src.parent.name}: {n} seen, {len(out)} kept", flush=True)
        if b is not None:
            polys = []
            for kind, k in KIND.items():
                for surf in b.iter("{%s}%s" % (NS["bldg"], kind)):
                    for pl in surf.iter("{%s}posList" % NS["gml"]):
                        polys.append((k, np.array(pl.text.split(), dtype=np.float64).reshape(-1, 3)))
            if polys:
                allp = np.concatenate([p for _, p in polys])
                cx, cy = allp[:, 0].mean() - ORIGIN[0], allp[:, 1].mean() - ORIGIN[1]
                if X0 <= cx <= X1 and Y0 <= cy <= Y1:
                    h = b.find("bldg:measuredHeight", NS)
                    objart = None
                    for sa in b.findall("gen:stringAttribute", NS):
                        if sa.get("name") == "OBJEKTART":
                            objart = sa.findtext("gen:value", namespaces=NS)
                    loc = [(k, np.column_stack([p[:, 0] - ORIGIN[0], p[:, 1] - ORIGIN[1], p[:, 2] - ORIGIN[2]]).astype(np.float32))
                           for k, p in polys]
                    out.append({"id": b.get("{%s}id" % NS["gml"]), "h": float(h.text) if h is not None else None,
                                "type": objart, "polys": loc})
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
    pickle.dump(out, open(dst, "wb"))
    return n, len(out)


def main(filters):
    DST.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.glob("*.citygml/**/*.gml")):
        tile = f.stem.split("_")[-1]
        if filters and not any(s in f.name for s in filters):
            continue
        t = time.time()
        n, k = parse(f, DST / f"{tile}.pkl")
        print(f"DONE {tile}: {k}/{n} buildings, {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
