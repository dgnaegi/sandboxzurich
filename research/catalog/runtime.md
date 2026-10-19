# Katalog zur Laufzeit (K3)

Zuordnung: `python3 pipeline/catalog/assign.py` -> `web/public/data/catalog.json` (35 KB, Zeilen `[Variante, x, y, yaw, sx, dy, kind]`). Korrekturen: `pipeline/overrides/catalog_assign.json` (brunnen / exclude / rot), davor `research/catalog/assign_hints.json`.
Laufzeit: `web/src/world/catalog.ts` (`loadCatalog` beim Start, `CatalogLayer.update` pro Frame, Handy: `atlas_256.png`, Radius 160 m, PC 220 m). Eine InstancedMesh pro Variante und Material (opak / Blend), Kollider-Kreise je 64-m-Chunk beim Betreten des Radius, Entfernen beim Verlassen.

Verteilung (Spielgebiet +50 m): Brunnen 185 = V1 19, V2 110 (inkl. V10-Fallback), V3 3, V4 12, V5 8, V6 17 (V7 2, V8 14, V9 0 im Gebiet). Haltestellen: H1 118, H2 123 (lange Polygone in Segmente zu 7 m geteilt), H3 129, H4 51, H5 28, H6 205, H7 60. Stehhilfen und Einzelsitze (stops_equip kind 1/2) und Plakatstellen bleiben die alten Boxen.

Ersetzt: generische Brunnen (props.ts, `meta.fountains`) und OSM-`dwater` (details.ts), wenn ein Katalogbrunnen <= 3 m entfernt ist; Wartehallen, Automaten, DFI, Banken (kind 0) in stops_equip.ts. pedspots (Leute am Brunnen) unveraendert. `?nocatalog` in der URL schaltet den Katalog ab (A/B-Test).
Abweichung vom Auftrag: z wird nicht in catalog.json gespeichert, sondern zur Laufzeit aus `Tiles.ground()` (Haltestellen: Bahnsteighoehe aus stops_equip) gelesen, damit Fahrbahn-Absenkung und Kachel-Hoehenkarten stimmen. Kollider nur fuer Brunnen (Haltestellenobjekte waren auch bisher begehbar).
Test: `web/tests/catalog_shots.mjs` -> `preview/catalog_cmp.jpg` (oben ohne, unten mit Katalog).
