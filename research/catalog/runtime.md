# Katalog zur Laufzeit (K3)

Zuordnung: `python3 pipeline/catalog/assign.py` -> `web/public/data/catalog.json` (35 KB, Zeilen `[Variante, x, y, yaw, sx, dy, kind]`). Korrekturen: `pipeline/overrides/catalog_assign.json` (brunnen / exclude / rot), davor `research/catalog/assign_hints.json`.
Laufzeit: `web/src/world/catalog.ts` (`loadCatalog` beim Start, `CatalogLayer.update` pro Frame, Handy: `atlas_256.png`, Radius 160 m, PC 220 m). Eine InstancedMesh pro Variante und Material (opak / Blend), Kollider-Kreise je 64-m-Chunk beim Betreten des Radius, Entfernen beim Verlassen.

Verteilung (Spielgebiet +50 m): Brunnen 185 = V1 19, V2 110 (inkl. V10-Fallback), V3 3, V4 12, V5 8, V6 17 (V7 2, V8 14, V9 0 im Gebiet). Haltestellen: H1 118, H2 123 (lange Polygone in Segmente zu 7 m geteilt), H3 129, H4 51, H5 28, H6 205, H7 60. Stehhilfen und Einzelsitze (stops_equip kind 1/2) und Plakatstellen bleiben die alten Boxen.

Ersetzt: generische Brunnen (props.ts, `meta.fountains`) und OSM-`dwater` (details.ts), wenn ein Katalogbrunnen <= 3 m entfernt ist; Wartehallen, Automaten, DFI, Banken (kind 0) in stops_equip.ts. pedspots (Leute am Brunnen) unveraendert. `?nocatalog` in der URL schaltet den Katalog ab (A/B-Test).
Abweichung vom Auftrag: z wird nicht in catalog.json gespeichert, sondern zur Laufzeit aus `Tiles.ground()` (Haltestellen: Bahnsteighoehe aus stops_equip) gelesen, damit Fahrbahn-Absenkung und Kachel-Hoehenkarten stimmen. Kollider nur fuer Brunnen (Haltestellenobjekte waren auch bisher begehbar).
Test: `web/tests/catalog_shots.mjs` -> `preview/catalog_cmp.jpg` (oben ohne, unten mit Katalog).

## Auftrag M (Moebel M2/M3)
- M3 Plakatstelle: alle 264 `pl`-Eintraege aus stops_equip.json (Lage/Richtung 1:1 wie die alten Boxen, kind 1, Bahnsteighoehe) -> catalog.json; die alten Poster-Boxen in stops_equip.ts entfallen, wenn der Katalog geladen ist. (Die 402 stammen stadtweit, 264 im Gebiet.)
- M2 Kiosk: `pipeline/catalog/assign_kiosk.py`. Von 35 OSM-Kiosken im Gebiet liegen 31 in Gebaeude-Footprints (Laeden im Haus), 2 auf anderem Level, 2 sind schon frei stehende Tile-Kioske. Freie Standorte: 0. Daher ersetzt M2 die 4 in den Kacheln eingebackenen Box-Kioske (details_osm, Position/Richtung 1:1, kind 3, Skip in details.ts via `catalogKioskNear`, Tile-Collider bleibt). Kind 2 (Kiosk mit Collider-Kreis, max 1.7 m) ist in catalog.ts vorbereitet, im Moment ungenutzt. Kleine Pavillons im Haus-Footprint (z. B. Quellenstrasse, Limmatplatz) wuerden Kachel-Builds brauchen.
- M1/M1b Leuchten: weggelassen. ewz-Brennstellen haben keinen Typ (Kandelaber vs. Seilleuchte nicht ableitbar), Modelle sind geraten (siehe models.md), Ersatz der heutigen Lampen-Objekte waere nicht eindeutig.
- Test: `web/tests/catalog_shots.mjs` -> `preview/catalog_cmp3.jpg`. Perf Handy-Profil (4x CPU): mit Katalog 263 Calls / 59 fps, `?nocatalog` 255 / 58 fps (Richtwert, Mac ausgelastet).
