"""Wide photo search for the Zentralwaescherei (Neue Hard 12): Commons text + geo search, Mapillary (wide, loose bearing), Panoramax.
Writes data/raw/photos/v3/zentralwaescherei/ and research/v3/photos_k4w4_zw.json (key zentralwaescherei)."""
import html, json, math, re, sys
from datetime import datetime, timezone
import fetch_v3 as F
from fetch_v3 import get, log, metres, bearing, adiff, download, local_ll, ROOT, OUT_DIR, token, COMMONS, ML, PANO

X, Y = 293, 360
LAT, LON = local_ll(X, Y)
D = OUT_DIR / "zentralwaescherei"
META = ROOT / "research" / "v3" / "photos_k4w4_zw.json"


def commons_all():
    titles = {}
    for q in ["Zentralwäscherei Zürich", "Zentralwaescherei", "Neue Hard 12", "Zentralwäscherei Neue Hard", "Bitwäscherei", "Zentralwäscherei Josefstrasse Hardturm"]:
        r = get("commons", COMMONS, {"action": "query", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": 40, "format": "json"}, pause=2.0)
        if r:
            for h in r.json().get("query", {}).get("search", []):
                titles[h["title"]] = None
    r = get("commons", COMMONS, {"action": "query", "list": "geosearch", "gscoord": f"{LAT}|{LON}", "gsradius": 250, "gsnamespace": 6, "gslimit": 100, "format": "json"}, pause=2.0)
    geo = {}
    if r:
        for h in r.json().get("query", {}).get("geosearch", []):
            geo[h["title"]] = h; titles[h["title"]] = h
    for cat in ["Category:Zentralwäscherei (Zürich)", "Category:Zentralwäscherei Zürich", "Category:Neue Hard (Zürich)", "Category:Zürich-Industriequartier"]:
        r = get("commons", COMMONS, {"action": "query", "list": "categorymembers", "cmtitle": cat, "cmtype": "file", "cmlimit": 60, "format": "json"}, pause=2.0)
        if r:
            for h in r.json().get("query", {}).get("categorymembers", []):
                titles[h["title"]] = None
    ts = [t for t in titles if t.lower().endswith((".jpg", ".jpeg", ".png"))]
    log(f"commons candidates {len(ts)}")
    out = []
    for i in range(0, len(ts), 40):
        r2 = get("commons", COMMONS, {"action": "query", "titles": "|".join(ts[i:i + 40]), "prop": "imageinfo|coordinates", "iiprop": "url|extmetadata|size",
                                      "iiurlwidth": 1024, "format": "json"}, pause=2.0)
        if not r2:
            continue
        for p in r2.json().get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if not ii.get("thumburl") or not re.search(r"CC|Public domain|PD|CC0", lic, re.I) or ii.get("width", 0) < 800:
                continue
            desc = html.unescape(re.sub(r"<[^>]+>", "", md.get("ImageDescription", {}).get("value", "")))[:140]
            blob = (p["title"] + " " + desc).lower()
            h = geo.get(p["title"])
            rel = h is not None and h.get("dist", 999) < 200 or any(k in blob for k in ("wäscherei", "waescherei", "neue hard", "zentralw"))
            if not rel:
                continue
            author = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
            date = re.sub(r"<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))
            out.append(dict(title=p["title"], url=ii["thumburl"], page=ii.get("descriptionurl"), license=lic, author=author, desc=desc,
                            lat=(h or {}).get("lat"), lon=(h or {}).get("lon"), dist=(h or {}).get("dist", 999), year=int(date[:4]) if date[:4].isdigit() else 0))
    return out


def ml_all(tok, rad=170):
    dlat, dlon = rad / 110574, rad / (111320 * math.cos(math.radians(LAT)))
    r = get("ml", ML, {"access_token": tok, "bbox": f"{LON-dlon:.6f},{LAT-dlat:.6f},{LON+dlon:.6f},{LAT+dlat:.6f}",
                       "fields": "id,thumb_1024_url,compass_angle,computed_geometry,captured_at,creator,is_pano", "limit": 3000}, pause=0.3)
    c = []
    for im in (r.json().get("data", []) if r else []):
        if not im.get("thumb_1024_url") or not im.get("computed_geometry"):
            continue
        ilon, ilat = im["computed_geometry"]["coordinates"]
        dx, dy = metres(LAT, LON, ilat, ilon); d = math.hypot(dx, dy)
        if d < 8 or d > rad:
            continue
        diff = adiff(im.get("compass_angle", 0), bearing(dx, dy))
        if diff > 55 and not im.get("is_pano"):
            continue
        yr = datetime.fromtimestamp(im["captured_at"] / 1000, timezone.utc).year
        c.append(dict(id=im["id"], url=im["thumb_1024_url"], lat=ilat, lon=ilon, d=d, diff=diff, heading=im.get("compass_angle"), year=yr,
                      night=F.is_night(im["captured_at"]), pano=bool(im.get("is_pano")), sector=int(bearing(-dx, -dy) // 30),
                      score=(0 if yr >= 2019 else 30) + diff * 0.4 + abs(d - 60) * 0.1, author=(im.get("creator") or {}).get("username", "unknown")))
    c.sort(key=lambda x: x["score"])
    log(f"mapillary candidates {len(c)}")
    ch = []
    for s in range(12):
        for x in c:
            if x["sector"] == s and x not in ch and not x["night"]:
                ch.append(x); break
    for x in c:
        if len(ch) >= 34: break
        if x not in ch and all(math.hypot(*metres(x["lat"], x["lon"], y["lat"], y["lon"])) > 6 or adiff(x["heading"] or 0, y["heading"] or 0) > 25 for y in ch):
            ch.append(x)
    return ch


def pano_all(rad=130):
    dlat, dlon = rad / 110574, rad / (111320 * math.cos(math.radians(LAT)))
    r = get("pano", PANO, {"bbox": f"{LON-dlon:.6f},{LAT-dlat:.6f},{LON+dlon:.6f},{LAT+dlat:.6f}", "limit": 200})
    out, used = [], []
    for f in (r.json().get("features", []) if r else []):
        a = f.get("assets", {}); href = (a.get("sd") or a.get("hd") or {}).get("href"); hd = f.get("properties", {}).get("view:azimuth")
        if not href or hd is None: continue
        ilon, ilat = f["geometry"]["coordinates"]; dx, dy = metres(LAT, LON, ilat, ilon)
        if adiff(hd, bearing(dx, dy)) > 55 or math.hypot(dx, dy) < 8 or any(adiff(hd, u[0]) < 25 and math.hypot(*metres(ilat, ilon, u[1], u[2])) < 12 for u in used): continue
        used.append((hd, ilat, ilon)); p = f["properties"]
        out.append(dict(id=f["id"], url=href, lat=ilat, lon=ilon, heading=hd, license=p.get("license", ""), author=p.get("geovisio:producer", "unknown"), date=p.get("datetime", "")[:10]))
        if len(out) >= 14: break
    log(f"panoramax {len(out)}")
    return out


def main():
    photos = []
    for c in commons_all():
        f = D / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
        if download(c["url"], f, "commons"):
            photos.append(dict(file=str(f.relative_to(ROOT)), source="commons", license=c["license"], author=c["author"], url=c["page"], title=c["title"], desc=c["desc"], lat=c["lat"], lon=c["lon"], heading=None, year=c["year"], night=False, dist_m=round(c["dist"])))
    for c in ml_all(token()):
        f = D / f"ml_{c['id']}.jpg"
        if download(c["url"], f, "ml"):
            photos.append(dict(file=str(f.relative_to(ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"], url=f"https://www.mapillary.com/app/?pKey={c['id']}", lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"], night=c["night"], dist_m=round(c["d"])))
    for c in pano_all():
        f = D / f"px_{c['id'][:12]}.jpg"
        if download(c["url"], f, "pano"):
            photos.append(dict(file=str(f.relative_to(ROOT)), source="panoramax", license=c["license"], author=c["author"], url="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"], lat=c["lat"], lon=c["lon"], heading=c["heading"], year=int(c["date"][:4]) if c["date"][:4].isdigit() else 0, night=False, dist_m=None))
    META.write_text(json.dumps({"zentralwaescherei": dict(name="Zentralwaescherei (Neue Hard 12)", kind="landmark", lat=LAT, lon=LON, photos=photos)}, ensure_ascii=False, indent=1))
    log(f"total {len(photos)}")


if __name__ == "__main__":
    main()
