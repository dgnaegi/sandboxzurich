"""Photo research for Kreis 3/9 landmark wave 3. Own metadata file research/v3/photos_k39w3.json (no clash with other agents).
Usage: python fetch_v3_k39.py [id,id]"""
import json, re, sys
import fetch_v3 as F

SITES = {  # id: (name, local x, local y, radius)
    "letzipark": ("Letzipark Baslerstrasse 50", -1318, 236, 150),
    "bethaus_wiedikon": ("Bethaus Wiedikon Schlossgasse 10", 254, -1640, 70),
    "aemtler_schule": ("Schulhaus Aemtler Aemtlerstrasse 101", -317, -1114, 80),
    "crowne_plaza": ("Crowne Plaza Badenerstrasse 420", -767, -428, 80),
    "schimmeltor_korn": ("Haus zum Schimmeltor / Haus zum Korn Wiedikon", 590, -1458, 80),
    "schule_albisrieder": ("Schule Albisriederplatz", -603, -458, 80),
    "froschauer": ("Zum Froschauer Wiedikon", 433, -1639, 80),
    "wiedinghof": ("Wiedinghof Wiedikon", 32, -1389, 70),
    "hochhaus_altst80": ("Hochhaus Altstetten 80 m", -1886, 816, 90),
    "hochhaus_altst64": ("Hochhaus Altstetten 64 m", -1723, 439, 90),
    "zwinglihaus": ("Zwinglihaus Aemtlerstrasse 25", -84, -1372, 70),
    "kirche_buehl": ("Kirche Buehl Goldbrunnenstrasse 54", 37, -1797, 70),
    "andreaskirche": ("Andreaskirche Brahmsstrasse 106", -1113, -613, 70),
    "st_konrad": ("Kirche St. Konrad Fellenbergstrasse 231b", -1518, -1138, 70),
    "heilig_kreuz": ("Kath. Kirche Heilig Kreuz Saumackerstrasse 81b", -2138, -10, 70),
    "lindenplatz_krone": ("Restaurant Krone Lindenplatz Altstetten", -2445, 395, 70),
}
META = F.ROOT / "research" / "v3" / "photos_k39w3.json"

def main():
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(SITES)
    meta = json.load(open(META)) if META.exists() else {}
    tok = F.token()
    for sid in ids:
        if sid in meta: continue
        name, x, y, rad = SITES[sid]
        lat, lon = F.local_ll(x, y)
        F.log(f"== {sid}")
        photos = []; d = F.OUT_DIR / sid
        for c in F.mapillary(sid, lat, lon, rad, tok):
            f = d / f"ml_{c['id']}.jpg"
            if F.download(c["url"], f, "ml"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"],
                    url=f"https://www.mapillary.com/app/?pKey={c['id']}", lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"], night=c["night"], dist_m=round(c["d"])))
        for c in F.commons(lat, lon, rad):
            f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
            if F.download(c["url"], f, "commons"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=c["license"], author=c["author"], url=c["page"],
                    title=c["title"], lat=c["lat"], lon=c["lon"], heading=None, year=c["year"], night=False, dist_m=round(c["dist"])))
        for c in F.panoramax(lat, lon, rad):
            f = d / f"px_{c['id'][:12]}.jpg"
            if F.download(c["url"], f, "pano"):
                photos.append(dict(file=str(f.relative_to(F.ROOT)), source="panoramax", license=c["license"], author=c["author"],
                    url="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"], lat=c["lat"], lon=c["lon"], heading=c["heading"],
                    year=int(c["date"][:4]) if c["date"][:4].isdigit() else 0, night=False, dist_m=None))
        meta[sid] = dict(name=name, kind="landmark", lat=round(lat, 6), lon=round(lon, 6), photos=photos)
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        F.log(f"  -> {len(photos)} photos")

if __name__ == "__main__":
    main()
