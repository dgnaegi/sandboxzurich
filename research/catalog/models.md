# Katalog-Modelle (K2)

Generator: `pipeline/catalog/models.py` (+ `model_core.py`, `model_brunnen.py`, `model_stops.py`, `model_moebel.py`, `model_sheet.py`). Aufruf `python3 pipeline/catalog/models.py`. Ausgabe `web/public/models/catalog/*.glb`, `index.json` (Variante, Datei, Dreiecke, `radius` = Collider-Footprint, `size`, `bbox`), `atlas.png` (512, 128 Farben) und `atlas_256.png` (Handy). Vorschau `preview/catalog_models.jpg`.

Konvention: Meter, y oben, Ursprung Mitte Grundriss am Boden, Front = +z. H5 und M1b haben den Ursprung an der Aufhaengung (Oberkante). Alle GLB teilen denselben Atlas (eingebettet, ca. 25 KB pro Datei); zwei Primitives: opak und `BLEND` (Glas, Wasser, Wasserstrahl).
Masse der Wartehalle: H1 7.0 x 1.6 m, H2 6.0 x 1.5 m, laengs in x, auf andere Laengen per x-Skalierung (Pfosten verzerren leicht). 
Fallback: V7 (Wandbrunnen) und V10 (ohne Angabe) -> V2 (`fallback` in index.json).

Unsicher: Haltestellenfahne (Farbe/Piktogramm Tram vs. Bus nur nach Gedaechtnis), Ticketautomat-Frontbild, Kiosk (keine Fotos, neutrale graugruene Kabine), Mastleuchte M1 und Seilleuchte M1b (Fotos nicht eindeutig, Typ geraten), V3/V8/V9 ohne Fotobeleg, Plakatmotive sind Platzhalter (poster_a/b, spaeter durch Plakat-Textur ersetzbar).
