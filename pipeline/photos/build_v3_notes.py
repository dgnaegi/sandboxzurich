"""Render research/v3/<id>.md, places_v3.json and CREDITS.md from research/v3/src/<id>.json + photos.json.
Also flags byte-identical duplicate photos (photos.json 'dup_of' = index) without changing indices."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
V3 = ROOT / "research" / "v3"
DEV = {
    "prime_tower": ["Modell (237 Dreiecke) kennt die versetzten, schräg geschnittenen Volumen nur grob; Referenz: 5 verdrehte Quader, Glas #2f6f73, Schriftzug PRIME TOWER weiss hinterleuchtet auf dem Sockeldach."],
    "toni_areal": ["Turm-Orientierung bisher nur aus Daten; Fassade real dunkles Streckmetall (#5a5850) mit Fensterbändern, Freitreppe + Schriftfeld TONI-/AREAL am Eingang, Bistro-Ecke."],
    "bhf_hardbruecke": ["Laut research/landmarks_k45.md 'offen': Bahnhof Hardbrücke noch nicht modelliert (Perron-Betondach mit Lichtbändern, rote Rückwand, Veloparking)."],
    "kalkbreite": ["Laut landmarks_k45.md 'Kalkbreite-Detail offen'; Fotos fehlen, vor Ausbau eigene Referenz holen."],
    "viadukt": ["Modell hat 40 Bögen aus OSM-Einheiten; Referenz: Ladenfronten mit hellen Alu-Bändern + Hausnummern (z. B. '...10'), Stahlfachwerkbrücke grüngrau, Josefwiese-Pappelallee."],
    "krematorium_sihlfeld": ["Grabfelder, Hecken, Alleen und Brunnen laut landmarks_k93.md offen."],
    "krematorium_haupttor": ["Tor: Schwarz mit goldenen Kreisornamenten, Bruchstein-Pfeiler mit Sphinx/Löwenfigur; Modell hat nur Pfeiler + Mauer."],
    "bhf_wiedikon": ["Terrain unter dem Reiterbahnhof ist im Spiel gefüllt (Ausschnitt nötig); Fassade real sandgelb mit 5 hohen Pfeilerfenstern, Fries ZÜRICH-WIEDIKON-SBB, Uhr mit römischen Ziffern."],
    "bhf_altstetten": ["Modell 'Hochhaus, IBM-Stengel'; Referenz: blaue Treppe, Perrondach, Bahnhofplatz Kies mit Bäumen, Tram 4 Endhaltestelle."],
    "letzigrund": ["Nur 8-18 Fotos; Dachuntersicht rotbraun, Sitze rot, Laufbahn #b4553a als Textur prüfen."],
}


def md(site, d, photos):
    L = [f"# {site['name']} ({site['id']})", f"Typ: {site['kind']} | lat/lon {site['lat']}, {site['lon']} | Fotos: {len(photos)} (Bogen preview/ref_v3_{site['id']}.jpg, Nummern = Index in photos.json)", ""]
    L.append(f"**Grundform/Massen:** {d['form']}")
    L.append(f"**Geschosse:** {d['storeys']}")
    f = d["facade"]
    L.append(f"**Fassade:** {f['material']}; Farben {', '.join(f['colors'])}. {f['notes']}")
    w = d["windows"]
    L.append(f"**Fenster:** {w['raster']}; Rahmen {w['frame']}")
    L.append(f"**Dach:** {d['roof']}")
    L.append(f"**Erdgeschoss/Eingänge:** {d['ground_floor']}")
    L.append("**Beschriftungen:** " + ("; ".join(f"«{s['text']}» {s['color']}, {s['position']}" for s in d["signage"]) or "keine"))
    L.append("**Details:**")
    L += [f"- {x}" for x in d["details"]]
    L.append(f"**Boden:** {d['ground']}")
    L.append("**Möblierung:** " + ", ".join(d["furniture"]))
    L.append(f"**Nacht:** {d['night']}")
    L.append("**Referenzfotos (Index):** " + ", ".join(str(i) for i in d["key_photos"]))
    if d.get("gaps"):
        L.append(f"**Lücken:** {d['gaps']}")
    L.append("")
    L.append("## Abweichungen zum jetzigen Spiel")
    L += [f"- {x}" for x in DEV.get(site["id"], ["Keine Abgleichdaten in research/ gefunden; Spielstand vor Umbau im Spiel prüfen."])]
    return "\n".join(L) + "\n"


def main():
    sites = {s["id"]: s for s in json.load(open(V3 / "sites.json"))}
    meta = json.load(open(V3 / "photos.json"))
    out, credits, seen = [], {}, {}
    for sid, site in sites.items():
        d = json.load(open(V3 / "src" / f"{sid}.json"))
        photos = meta[sid]["photos"]
        for i, p in enumerate(photos):
            fp = ROOT / p["file"]
            if not fp.exists():
                continue
            h = hashlib.md5(fp.read_bytes()).hexdigest()
            if h in seen and seen[h][0] == sid:
                p["dup_of"] = seen[h][1]
            seen.setdefault(h, (sid, i))
        (V3 / f"{sid}.md").write_text(md(site, d, photos), encoding="utf-8")
        rec = {"id": sid, "name": site["name"], "kind": site["kind"], "lat": site["lat"], "lon": site["lon"],
               "radius_m": site["radius"], "n_photos": len(photos), "deviations_from_game": DEV.get(sid, [])}
        rec.update({k: v for k, v in d.items() if k != "id"})
        out.append(rec)
        credits[sid] = photos
    (V3 / "photos.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    (V3 / "places_v3.json").write_text(json.dumps({"_doc": "Aus Foto-Recherche v3; Farben Hex, Masse in m; key_photos = Index in photos.json[id].photos", "sites": out}, ensure_ascii=False, indent=1))
    C = ["# Credits Foto-Recherche v3", "", "Referenzbilder nur zur Recherche (data/raw/photos/v3/), nicht für Spieltexturen. Mapillary: CC BY-SA 4.0, Namensnennung des Autors (Benutzername). Commons: Lizenz pro Datei. Panoramax: Lizenz pro Bild.", ""]
    for sid, photos in credits.items():
        C.append(f"## {sid}")
        for i, p in enumerate(photos):
            C.append(f"- #{i} {p['source']} | {p['license']} | {p['author']} | {p['url']}")
        C.append("")
    (V3 / "CREDITS.md").write_text("\n".join(C), encoding="utf-8")
    print(len(out), "sites;", sum(len(v) for v in credits.values()), "photos")


if __name__ == "__main__":
    main()
