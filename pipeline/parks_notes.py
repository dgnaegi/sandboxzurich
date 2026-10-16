"""research/parks/<id>.md from parks.json (hand observations), OSM (object counts), Baumkataster (species) and photo credits.
Run: .venv/bin/python pipeline/parks_notes.py"""
import collections, json
from shapely.geometry import Point, Polygon
from config import ROOT
import sources, trees_dims

D = ROOT / "research" / "parks"
nodes, els = sources.osm()
ways = {e["id"]: e for e in els if e["type"] == "way" and "nodes" in e}
cat = trees_dims.catalog()
try:
    ph = json.load(open(D / "photos.json"))
    v3 = json.load(open(ROOT / "research/v3/photos.json"))
except Exception:
    ph, v3 = {}, {}
credits = ["# Credits Parkfotos\n\nReferenzbilder nur zur Recherche (data/raw/photos/parks/, v3), nicht als Spieltextur. Mapillary CC BY-SA 4.0; Commons/Panoramax Lizenz pro Datei.\n"]
for p in json.load(open(D / "parks.json"))["parks"]:
    shp = Polygon([nodes[n] for n in ways[p["osm"][0]]["nodes"] if n in nodes]).buffer(0)
    zone = shp.buffer(3)
    sp = collections.Counter((s or "?")[:28] for (x, y), (s, yr) in cat.items() if zone.contains(Point(x, y)))
    cnt = collections.Counter()
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node" and e["id"] in nodes and t and zone.contains(Point(nodes[e["id"]])):
            for k in ("leisure", "amenity", "sport", "barrier"):
                if k in t and t[k] not in ("kerb", "bench"):
                    cnt[f"{k}={t[k]}"] += 1
    src = p.get("photos_from")
    photos = (v3[src.split(":")[1] if ":" in src else p["id"]] if src else ph.get(p["id"], {"photos": []}))["photos"]
    credits.append(f"\n## {p['id']}")
    for i, f in enumerate(photos):
        credits.append(f"- #{i} {f['source']} | {f['license']} | {f['author']} | {f['url']}")
    md = [f"# {p['name']} ({p['id']})", f"OSM way {p['osm']} | {int(shp.area)} m2 | Fotos: {len(photos)} (Bogen preview/ref_parks_{p['id']}.jpg, Nummern = Index in photos.json) | Referenzbilder: {p.get('ref')}", "",
          "## Beobachtung (Fotos)", p["obs"], "",
          "## Umsetzung im Spiel", f"- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = {p['paved']}) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).",
          "- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.",
          "- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.", "",
          "## Daten", f"- Bäume im Park (Kataster, Gattung): {dict(sp.most_common(8)) or 'keine'}", f"- OSM-Punkte: {dict(cnt) or 'keine'}", ""]
    (D / f"{p['id']}.md").write_text("\n".join(md))
(D / "CREDITS.md").write_text("\n".join(credits))
print("ok")
