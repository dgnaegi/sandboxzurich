# Katalog-Modelle (K2)

Generator: `pipeline/catalog/models.py` (+ `model_core.py`, `model_brunnen.py`, `model_stops.py`, `model_moebel.py`, `model_sheet.py`). Aufruf `python3 pipeline/catalog/models.py`. Ausgabe `web/public/models/catalog/*.glb`, `index.json` (Variante, Datei, Dreiecke, `radius` = Collider-Footprint, `size`, `bbox`), `atlas.png` (512, 128 Farben) und `atlas_256.png` (Handy). Vorschau `preview/catalog_models.jpg`.

Konvention: Meter, y oben, Ursprung Mitte Grundriss am Boden, Front = +z. H5 und M1b haben den Ursprung an der Aufhaengung (Oberkante). Alle GLB teilen denselben Atlas (eingebettet, ca. 25 KB pro Datei); zwei Primitives: opak und `BLEND` (Glas, Wasser, Wasserstrahl).
Masse der Wartehalle: H1 7.0 x 1.6 m, H2 6.0 x 1.5 m, laengs in x, auf andere Laengen per x-Skalierung (Pfosten verzerren leicht). 
Fallback: V7 (Wandbrunnen) und V10 (ohne Angabe) -> V2 (`fallback` in index.json).

Unsicher: Haltestellenfahne (Farbe/Piktogramm Tram vs. Bus nur nach Gedaechtnis), Ticketautomat-Frontbild, Kiosk (keine Fotos, neutrale graugruene Kabine), Mastleuchte M1 und Seilleuchte M1b (Fotos nicht eindeutig, Typ geraten), V3/V8/V9 ohne Fotobeleg, Plakatmotive sind Platzhalter (poster_a/b, spaeter durch Plakat-Textur ersetzbar).

## Auftrag H (Fotobelege, DFI)
Fotos: `pipeline/photos/fetch_catalog.py` (Commons + Panoramax, Lizenz/Autor je Datei in `research/catalog/photos_extra.json`, Bilder lokal in `data/raw/photos/catalog/`, nicht im Repo; Kontaktbogen `preview/ref_cat_extra.jpg`, `ref_cat_extra2.jpg`). Nur zur Ansicht, nichts wird als Textur verwendet.
- V8 Notwasserbrunnen: bestaetigt (Commons: Hardplatz, Baeckerstrasse 18, Ottostrasse, Bändlistrasse, Haldenstrasse). Form: bronzebrauner Zylinder mit schraeg geschnittener Trinkschale und seitlicher Ablage. Zuordnung: Feld `brunnenart` = Notwasserbrunnen (27 Objekte) statt `art` (2); V8 im Spielgebiet: 14.
- V3 Bronzeguss: Fotos zeigen Granittrog (lang, rechteckig) mit Bronzefiguren (Tiere) auf Sims einer Stele. Modell neu (V3: Trog + Stele + 3 Tiere).
- V7 Wandbrunnen: Bogennische mit Tierkopf-Speier und achteckigem Becken (Commons). Neues Modell V7, Zuordnung per Foto (BR-111/BR-260, im Spielgebiet 2).
- V9 Holz: kein Foto gefunden (Wald-Standorte, nur Wanderweg-Bilder). Modell bleibt unbelegt.
- VBZ-Fahne: Fotos (Commons) zeigen kleines Querformat-Schild, blaues Feld mit weissem Haltestellennamen. Fahne jetzt Querformat 0.66 x 0.50 m, blau/weiss, Piktogramm Tram/Bus, weisse Liniensteine unten (Linienfarben nicht belegt).
- Kiosk: "k kiosk"-Pavillons, dunkles Holz/Glas, weisse Wortmarke auf dunkler Blende. Koerper jetzt dunkelbraun mit Blende (Textur `kiosk_sign`); Form bleibt vereinfacht.
- DFI: `stops_equip.ts` zeichnet wieder den orangen Abfahrtstext (geteilte Canvas-Textur je Linienset, 256x128, Handy 128x64) auf die Katalog-Anzeigen H4/H5.
