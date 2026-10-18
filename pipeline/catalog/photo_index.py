"""Build a flat index of local photos with coordinates from research/ metadata JSONs.

Output: research/catalog/photo_index.json  [{file, lat, lon, source, license, author, url, heading, origin}]
Only entries with a usable file path and WGS84 lat/lon are kept.
"""
import json, os, glob, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "research", "catalog", "photo_index.json")
LAT_KEYS = ("lat", "latitude", "Lat")
LON_KEYS = ("lon", "lng", "longitude", "Lon")


def num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def walk(node, origin, parent_geo, out):
    if isinstance(node, dict):
        geo = parent_geo
        lat = next((num(node[k]) for k in LAT_KEYS if k in node), None)
        lon = next((num(node[k]) for k in LON_KEYS if k in node), None)
        if lat is not None and lon is not None:
            geo = (lat, lon)
        f = node.get("file")
        if isinstance(f, str) and f.startswith("data/raw/photos") and geo:
            ilat = num(node.get("lat", geo[0]))
            ilon = num(node.get("lon", geo[1]))
            out.append({
                "file": f,
                "lat": ilat if ilat is not None else geo[0],
                "lon": ilon if ilon is not None else geo[1],
                "source": node.get("source"),
                "license": node.get("license"),
                "author": node.get("author"),
                "url": node.get("url"),
                "heading": node.get("heading"),
                "origin": origin,
            })
        for v in node.values():
            walk(v, origin, geo, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, origin, parent_geo, out)


def main():
    out, seen = [], set()
    files = glob.glob(os.path.join(ROOT, "research", "**", "*.json"), recursive=True)
    for p in files:
        if "/catalog/" in p:
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        rel = os.path.relpath(p, ROOT)
        tmp = []
        walk(data, rel, None, tmp)
        for e in tmp:
            key = (e["file"], round(e["lat"], 6), round(e["lon"], 6))
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
    # keep only files that exist on disk
    out = [e for e in out if os.path.exists(os.path.join(ROOT, e["file"]))]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"json files scanned: {len(files)}; geo photos indexed: {len(out)}; "
          f"distinct files: {len({e['file'] for e in out})}")
    from collections import Counter
    print("by top dir:", Counter(e["file"].split("/")[3] if len(e["file"].split("/")) > 3 else "?" for e in out).most_common(20))


if __name__ == "__main__":
    main()
