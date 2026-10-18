"""Reference photos Quartiergarten Hard (Bullingerstrasse 90). Reuses fetch_v3 (Mapillary/Commons/Panoramax); output data/raw/photos/qgh/,
metadata research/quartiergarten_hard_photos.json. Photos are reference only (never texture)."""
import html, json, re
import fetch_v3 as F

F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "qgh"
F.META = F.ROOT / "research" / "quartiergarten_hard_photos.json"
QUERIES = ["Quartiergarten Hard Zürich", "Hardau Gemeinschaftsgarten", "Urban Gardening Zürich Gemeinschaftsgarten", "Hardau Familiengarten Zürich",
           "Gartenareal Hard Zürich", "Bullingerstrasse Zürich Hardau Garten", "Gemeinschaftsgarten Zürich Hochbeete", "Pflanzblätz Zürich"]


def main():
    tok = F.token()
    lat, lon = F.local_ll(-640, -120)
    photos, d = [], F.OUT_DIR
    for rad in (140,):
        for c in F.mapillary("qgh", lat, lon, rad, tok):
            f = d / f"ml_{c['id']}.jpg"
            if F.download(c["url"], f, "ml"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"],
                                   url=f"https://www.mapillary.com/app/?pKey={c['id']}", lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"]))
        for c in F.commons(lat, lon, 250):
            f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
            if F.download(c["url"], f, "commons"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=c["license"], author=c["author"], url=c["page"], title=c["title"], lat=c["lat"], lon=c["lon"], year=c["year"]))
        for c in F.panoramax(lat, lon, rad):
            f = d / f"px_{c['id'][:12]}.jpg"
            if F.download(c["url"], f, "pano"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="panoramax", license=c["license"], author=c["author"], url="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"], lat=c["lat"], lon=c["lon"], heading=c["heading"]))
    have = {x.get("title") for x in photos}
    for q in QUERIES:
        r = F.get("commons", F.COMMONS, {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap", "gsrlimit": 25,
                                         "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": F.MAX_SIDE, "format": "json"}, pause=3.0)
        if not r: continue
        for pg in r.json().get("query", {}).get("pages", {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", ""); t = pg["title"]
            if t in have or not ii.get("thumburl") or not t.lower().endswith((".jpg", ".jpeg")) or not re.search(r"CC|Public domain|PD", lic, re.I) or ii.get("width", 0) < 1000: continue
            au = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
            f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", t[5:])[:60] + ".jpg")
            if F.download(ii["thumburl"], f, "commons"):
                have.add(t); photos.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=lic, author=au, url=ii.get("descriptionurl"), title=t, via="search:" + q))
    F.META.write_text(json.dumps(photos, ensure_ascii=False, indent=1)); F.log(f"-> {len(photos)} photos")


if __name__ == "__main__":
    main()
