# Landmarks Kreis 9/3 (Stand 2026-10-15)
Build: `.venv/bin/python pipeline/landmarks/k93_all.py` (Bibliothek `k93_lib.py`, Suche `k93_find.py`). Ausgabe: `web/public/models/landmarks/k93_*.glb` (gltfpack -cc, Meshopt noetig), `pipeline/overrides/landmarks_k93.json`. Modell-Origin = (x,y,z) Bodenhoehe, Three-Achsen.
| Modell | Dreiecke | Quelle |
|---|---|---|
| k93_stadion | 20k | OSM Tribünen A-D, swissBUILDINGS3D-Dach (Ring, Höhen), OSM Pitch (Achse 52.5°); Laufbahn 400 m, Rasen 105x68 per Textur |
| k93_altstetten | 0.3k | swissBUILDINGS3D-Grundrisse, OSM IBM-Stengel (Luginbühl) |
| k93_kirche_altstetten | 0.3k | swissBUILDINGS3D (Alte Kirche + Kirche Altstetten) |
| k93_dreifaltigkeit | 0.1k | OSM-Name «Dreifaltigkeitskirche» |
| k93_wiedikon | 0.1k | swissBUILDINGS3D Grundriss, Texturband «WIEDIKON» |
| k93_schmiede | 0.3k | OSM Löwenbrunnen (314,-1561) |
| k93_krematorium | 1.3k | Altes Krematorium = OSM «Aufbahrungshalle Sihlfeld» (swiss 52331290, Kuppel, Säulenhalle zum Tor), Kapelle D, Kapelle Aufbahrung, Haupttor D (-706.8,-745.3) mit Pfeilern, Mauer, Figurengruppe (Markwalder) |
| k93_wiedikon (v2) | 0.2k | Reiterbahnhof als Brücke: Öffnung 18 m über dem Einschnitt (Schienenniveau -7.8 m, Unterseite -1.5 m), Stützmauern; Terrain unter dem Gebäude ist im Spiel gefüllt, bräuchte einen Ausschnitt |
| k93_altstetten (v2) | 1.2k | Geschossplatten, Fenster-Bänder, Betonlamellen, Treppenkerne, Läden im EG mit Markisen |

## Grabfelder Friedhof Sihlfeld (offen, nicht modelliert)
Friedhof = OSM way 10634343 (cemetery), Haupttore C/D/... als OSM-barrier=gate, Wege als footway im OSM. Fehlt: Gräberreihen (Grabsteine in Reihen je Feld), Hecken, Baumalleen, Brunnen (OSM drinking_water «Friedhofbrunnen», Pilgerbrunnen), Kunstwerke (Erwachende -684,-896; Die Kniende -783,-766; Grabdenkmal Dunant -767.5,-746). Vorschlag: Instanzmesh Grabsteine aus Rasterreihen im Friedhofspolygon, ausserhalb der Wege.
