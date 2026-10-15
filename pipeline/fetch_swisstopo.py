"""Fetch swisstopo OGD via STAC: swissALTI3D 0.5 m, swissBUILDINGS3D 3.0 (CityGML, gdb fallback),
SWISSIMAGE item list only. Skips existing files. Usage: python pipeline/fetch_swisstopo.py"""
import json
import re
import sys
import zipfile
from pathlib import Path

import requests
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).parent))
import area  # noqa: E402

STAC = "https://data.geo.admin.ch/api/stac/v0.9/collections"
RAW = area.ROOT / "data" / "raw"
H = {"User-Agent": "sandboxzurich/0.1"}


def items(coll):
    w, s, e, n = area.bbox_wgs84()
    url = f"{STAC}/{coll}/items?bbox={w},{s},{e},{n}&limit=100"
    out = []
    while url:
        d = requests.get(url, headers=H, timeout=60).json()
        out += d["features"]
        url = next((l["href"] for l in d.get("links", []) if l["rel"] == "next"), None)
    return out


def download(url, dest: Path):
    if dest.exists():
        print("skip", dest.name)
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers=H, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for c in r.iter_content(1 << 20):
                f.write(c)
    tmp.rename(dest)
    print("got", dest.name, dest.stat().st_size, flush=True)


def newest_per_tile(feats, tile_re):
    best = {}
    for f in feats:
        m = tile_re.search(f["id"])
        if not m:
            continue
        year, tile = m.group(1), m.group(2)
        if tile not in best or year > best[tile][0]:
            best[tile] = (year, f)
    return {t: f for t, (y, f) in best.items()}


def alti():
    out = RAW / "alti3d"
    out.mkdir(parents=True, exist_ok=True)
    poly = area.area_lv95()
    best = newest_per_tile(items("ch.swisstopo.swissalti3d"), re.compile(r"swissalti3d_(\d{4})_(\d+-\d+)$"))
    n = 0
    for tile, f in sorted(best.items()):
        x, y = (int(v) * 1000 for v in tile.split("-"))
        if not poly.intersects(box(x, y, x + 1000, y + 1000)):
            continue
        a = next((v for k, v in f["assets"].items() if k.endswith("_0.5_2056_5728.tif")), None)
        if a:
            download(a["href"], out / Path(a["href"]).name)
            n += 1
    print("alti3d tiles", n)


def sb3d():
    out = RAW / "sb3d"
    out.mkdir(parents=True, exist_ok=True)
    poly = area.area_wgs84()
    feats = [f for f in items("ch.swisstopo.swissbuildings3d_3_0") if re.search(r"_\d{4}_1091-\d\d$", f["id"])]
    best = newest_per_tile(feats, re.compile(r"_(\d{4})_(1091-\d\d)$"))
    # prefer newest sheet that has a citygml asset; else newest with gdb
    allf = {}
    for f in feats:
        m = re.search(r"_(\d{4})_(1091-\d\d)$", f["id"])
        allf.setdefault(m.group(2), []).append((m.group(1), f))
    for tile, lst in sorted(allf.items()):
        lst.sort(key=lambda t: t[0], reverse=True)
        f = lst[0][1]
        if not poly.intersects(box(*f["bbox"])):
            continue
        for ext in ("citygml", "gdb"):
            a = next((v for k, v in f["assets"].items() if k.endswith(f".{ext}.zip")), None)
            if a:
                break
        dest = out / Path(a["href"]).name
        download(a["href"], dest)
        d = out / dest.name.replace(".zip", "")
        if not d.exists():
            with zipfile.ZipFile(dest) as z:
                z.extractall(d)
        print("sb3d", tile, ext)


def swissimage():
    dest = RAW / "swissimage_items.json"
    if dest.exists():
        return
    fs = items("ch.swisstopo.swissimage-dop10")
    best = newest_per_tile(fs, re.compile(r"swissimage-dop10_(\d{4})_(\d+-\d+)$"))
    res = {t: {"id": f["id"], "assets": {k: v["href"] for k, v in f["assets"].items()}} for t, f in best.items()}
    dest.write_text(json.dumps(res, indent=1))
    print("swissimage items", len(res))


if __name__ == "__main__":
    for fn in (swissimage, sb3d, alti):
        try:
            fn()
        except Exception as e:
            print("ERROR", fn.__name__, repr(e), flush=True)
