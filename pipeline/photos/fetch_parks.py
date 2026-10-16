"""Reference photos for parks (research/parks/parks.json). Reuses fetch_v3 (Mapillary/Commons/Panoramax); output
data/raw/photos/parks/<id>/, metadata research/parks/photos.json. Parks with photos_from=v3 are not fetched.
Usage: python fetch_parks.py [id,id]"""
import json
import re
import sys

import fetch_v3 as F

F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "parks"
F.META = F.ROOT / "research" / "parks" / "photos.json"
SPEC = json.load(open(F.ROOT / "research" / "parks" / "parks.json"))["parks"]


def main():
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    meta = json.load(open(F.META)) if F.META.exists() else {}
    tok = F.token()
    for p in SPEC:
        sid = p["id"]
        if p.get("photos_from") or (only and sid not in only) or (sid in meta and not only):
            continue
        lat, lon = F.local_ll(*p["c"])
        rad = p["r"] + 30
        F.log(f"== {sid}")
        photos, d = [], F.OUT_DIR / sid
        for c in F.mapillary(sid, lat, lon, rad, tok):
            f = d / f"ml_{c['id']}.jpg"
            if F.download(c["url"], f, "ml"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"],
                                   url=f"https://www.mapillary.com/app/?pKey={c['id']}", lat=c["lat"], lon=c["lon"],
                                   heading=c["heading"], year=c["year"], night=c["night"], dist_m=round(c["d"])))
        for c in F.commons(lat, lon, rad):
            f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
            if F.download(c["url"], f, "commons"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=c["license"], author=c["author"],
                                   url=c["page"], title=c["title"], lat=c["lat"], lon=c["lon"], heading=None, year=c["year"],
                                   night=False, dist_m=round(c["dist"])))
        for c in F.panoramax(lat, lon, rad):
            f = d / f"px_{c['id'][:12]}.jpg"
            if F.download(c["url"], f, "pano"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="panoramax", license=c["license"], author=c["author"],
                                   url="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"], lat=c["lat"], lon=c["lon"],
                                   heading=c["heading"], year=int(c["date"][:4]) if c["date"][:4].isdigit() else 0, night=False,
                                   dist_m=None))
        # Commons text search (finds files without coordinates)
        r = F.get("commons", F.COMMONS, {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": p["q"] + " filetype:bitmap",
                                         "gsrlimit": 40, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": F.MAX_SIDE,
                                         "format": "json"}, pause=3.0)
        have = {x.get("title") for x in photos}
        n = 0
        if r:
            import html
            for pg in r.json().get("query", {}).get("pages", {}).values():
                ii = (pg.get("imageinfo") or [{}])[0]
                md = ii.get("extmetadata", {})
                lic = md.get("LicenseShortName", {}).get("value", "")
                t = pg["title"]
                if n >= 12 or t in have or not ii.get("thumburl") or not t.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                if not re.search(r"CC|Public domain|PD", lic, re.I) or ii.get("width", 0) < 1000:
                    continue
                au = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
                f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", t[5:])[:60] + ".jpg")
                if F.download(ii["thumburl"], f, "commons"):
                    photos.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=lic, author=au, url=ii.get("descriptionurl"),
                                       title=t, lat=None, lon=None, heading=None, year=0, night=False, dist_m=None, via="search"))
                    n += 1
        meta[sid] = dict(name=p["name"], kind="park", lat=round(lat, 6), lon=round(lon, 6), photos=photos)
        F.META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        F.log(f"  -> {len(photos)} photos")


if __name__ == "__main__":
    main()
