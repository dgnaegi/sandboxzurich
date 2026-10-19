# Fassaden v4: Notizen statt generisch

## Wie Fassaden entstehen (Ist)
- `pipeline/facade.py` `add_building` -> `_wall`: jede senkrechte Wand wird mit UV auf eine Atlas-Schicht (512 px, `web/public/tex/atlas.webp`) gemappt.
  Eine Schicht = 4 Geschosse x 4 Fensterachsen. u = Achsen/4 pro Wandlänge (ganzzahlig, Raster 3.0 m), v = -(z-z0)/tile_h, tile_h = 4*Traufhöhe/Geschosse.
- Geschosse: GWR/OSM `levels`, sonst Traufhöhe/3.1 m. EG mit Laden: 4 m Schaufensterschicht (`shop_layer`), Rest Wand. Sockel: 0.7 m dunkler Streifen.
- Stil/Farbe: `pipeline/styles.py` `building_style` -> `v3_layer_name` (Schicht aus Material/Fenster/Läden/Stil der Notiz) + exakter Vertex-Tint. Notizen: `visual_overrides.load_v3()` (`research/buildings/visual_notes_v3.json`), landen in `osm["_visual"]["v3"]`.
- Shader: `web/src/engine/materials.ts` multipliziert Atlas x Vertex-Tint (Maske); keine Änderung nötig.
- Notiz-Felder (1716 Häuser): geschosse 582, achsen 47, details (balkon 874, rustika 247, erker 96, gesims 54, gauben 23, mansarde 11), fenster, laeden (= Fensterläden).

## Neu (v4, Schalter `SBZ_FACADES_V4=0` = alt)
Keine neuen Texturen, kein neuer Draw-Call (alles im Tile-Mesh, gleicher Atlas).
- **Geschosse:** Notiz-`geschosse` zählt, wenn GWR/OSM keine Zahl haben; Plausibilität Geschosshöhe 2.6-4.6 m (auch für GWR/OSM, sonst Ableitung aus Höhe).
- **Achsen:** Notiz-`achsen` / Breite der Hauptfront (strassenseitig, breiteste Wand) = Achsabstand (2.2-6 m), gilt für alle Wände des Hauses. Ohne Notiz: Gründerzeit-/Altbau-Schichten 3.3 m statt 3.0 m.
- **Rustika-EG** (Detail `rustika`, ohne Laden): EG-Zone in Sandstein-Grau-Beige getönt, Sockel dunkler, Putz darüber.
- **Stockwerkband** (Detail `gesims`/`rustika`, >= 3 Geschosse): schmales Band (4 Dreiecke je Wand) über dem EG.
- **Gauben** (Detail `gauben`/`mansarde`) auf geneigten, strassenseitigen Dachflächen: Front mit Fensterachse aus dem Atlas, Wangen, Flachdach (~10 Dreiecke je Gaube).
- Fensterform (hoch/Bogen/Band/Verdachung): wie bisher über Schichtwahl (`v3_layer_name`), kein neuer Code.

## Messung (8 Testkacheln: Z4 `-1_-7,-2_-8,-3_-9,0_-5,0_-6,2_-9` + Langstrasse `3_-4,3_-3`, 0 Fehler)
- perf Handy (4x CPU): vorher 58 fps / 266 Calls / 589k Tris, nachher 58 fps / 265 Calls / 564k Tris (Kachelinhalt der Testkacheln weicht vom Komplett-Build ab, Tris nicht direkt vergleichbar). Texturen unverändert (Langstrasse 157 MB, HB 145, Hardbrücke 98; Geometrie 38/46/21 MB).
- Reichweite (Kacheln -2_-8, 0_-6: 143 Häuser, 62 mit Foto-Notiz): Achsabstand 3.3 m bei 33 Altbauten, Rustika-EG 3, Gauben-Versuche 5. Grund: Die meisten Notizen-Häuser haben Läden im EG (Schaufenster ersetzt die Rustika-Zone), `achsen` gibt es nur bei 47 Notizen.
- Vergleich: `preview/facades_v4_before_top.jpg` (V4=0) / `facades_v4_after_top.jpg` (V4=1), Gauben `facades_v4_after_mans.jpg`; Skript `web/tests/facades_v4_cmp.mjs` (freie Kamera 4.5 m über Boden, ENV `ADDR`, `OUTN`). Die sechs Standardhäuser sehen vorher/nachher gleich aus (kein Rustika/Gauben/Achsen-Detail bei diesen Notizen oder Laden im EG).
- Debug: `SBZ_V4_LOG=<datei>` schreibt je Haus Geschosse/Achsabstand/Rustika/ext.

## Offen / nächste Hebel
- Notizen-Daten sind dünn: `achsen` 47, `geschosse` 582 von 1716. Mehr Felder per Foto nachtragen (Notiz-Inhalte, nicht dieser Auftrag).
- Balkone als Geometrie (874 Notizen): Atlas-Schichten malen Balkone schon, Geometrie müsste deckungsgleich platziert werden.
- Fensterform über Atlas-Spalte, Hochparterre/höheres EG bei Altbau, Rustika-Fugen als Textur: nicht umgesetzt.
- Wirkt erst nach Komplett-Build (bisher nur Testkacheln neu gebaut; Weltdaten nicht veröffentlicht).
