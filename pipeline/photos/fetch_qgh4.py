"""Generic Swiss/Zurich community-garden element references from Commons (CC only), appended to research/quartiergarten_hard_photos.json (kind=generic)."""
import html, json, re
import fetch_v3 as F
OUT = F.ROOT / "data" / "raw" / "photos" / "qgh"; MP = F.ROOT / "research" / "quartiergarten_hard_photos.json"
Q = ["Gemeinschaftsgarten Zürich", "Gemeinschaftsgarten Hochbeete Schweiz", "Urban Gardening Schweiz Hochbeet", "Familiengarten Zürich Gartenhaus", "Schrebergarten Schweiz Gartenhäuschen",
     "Quartiergarten Zürich", "IBC Container Regenwasser Garten", "Komposter Paletten Garten", "Pflanzgarten Zürich Wiese", "Stadtgarten Zürich Hochbeete"]
meta = json.load(open(MP)); have = {m.get("title") for m in meta}; n = 0
for q in Q:
    r = F.get("commons", F.COMMONS, {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap", "gsrlimit": 12, "prop": "imageinfo",
                                     "iiprop": "url|extmetadata|size", "iiurlwidth": 1024, "format": "json"}, pause=3.0)
    if not r: continue
    k = 0
    for pg in r.json().get("query", {}).get("pages", {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", ""); t = pg["title"]
        if k >= 3 or t in have or not ii.get("thumburl") or not t.lower().endswith((".jpg", ".jpeg")) or not re.search(r"CC|Public domain|PD", lic, re.I) or ii.get("width", 0) < 1200: continue
        au = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
        f = OUT / ("gen_" + re.sub(r"[^A-Za-z0-9]+", "_", t[5:])[:55] + ".jpg")
        if F.download(ii["thumburl"], f, "commons"):
            have.add(t); k += 1; n += 1; meta.append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=lic, author=au, url=ii.get("descriptionurl"), title=t, kind="generic", via=q))
json.dump(meta, open(MP, "w"), ensure_ascii=False, indent=1); print("added", n)
