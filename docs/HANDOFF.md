# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Stand (2026-10-15, nach 8-h-Lauf)
**Spielgebiet = ganze Kreise 4+5, Teile Kreis 9 (Hohlstrasse, Lindenplatz, Bhf Altstetten) und Kreis 3 (Bhf Wiedikon, Schmiede).** 6.44 km², 202 Spielkacheln + 77 Kulissenkacheln, Rand = Baustellenzaun («BAUSTELLE – DURCHGANG GESPERRT») mit Kollision. Keine Missionen (nur `?missions`).

### Pipeline (alles reproduzierbar)
- `pipeline/playarea.py` → `data/build/playarea.json` (Polygon, Kacheln). `config.py` liest es; `SBZ_AREA=test` = altes Testgebiet.
- `build_testarea.py` baut alle Kacheln parallel (~35–85 min, Log `logs/build_full2.log`). Einzelne Kacheln: `SBZ_TILES=ix_iy,…`. Fehler einer Kachel → «TILE FAILED» im Log, Rest läuft weiter.
- Neu eingebunden: `bridges.py` (268 Brücken, Decks + Pfeiler, Boden darunter ausgeschnitten), `plazasigns.py` (43 Widmungstafeln am vermessenen Ort + Platzschilder an Fassaden/Pfosten), `overrides/landmark_signs.json` (grosses Rosa-Luxemburg-Platz-Schild mit Nelken), `groundcover.py` (Amtliche Vermessung: Innenhöfe Rasen/befestigt, Bahnareal = Schotter tief, Gleise von `railways.py` darauf).
- Separat: `railways.py` (Gleise/Masten/Perrons → `web/public/models/trains/tiles`, `data/rail.json`), `scenes_build.py` (138 Easter Eggs/Szenen aus `overrides/scenes_src.json`), `anecdotes.py` (595 Texte inkl. 552 Strassennamen).

### Web
- `engine/grading.ts` (Neon-80er-Look: ACES + Split-Toning + Vignette), Bloom nur PC, neue Tageszeit-Keyframes.
- `world/bridges.ts` + `Tiles.groundAt()` (Spielerin läuft auf Brücken), `world/railways.ts` (S-Bahn-Züge, Fahrleitung; Handy kleinerer Radius), `world/landmarks.ts`, `world/streetsigns.ts` (Schildlänge nach Name, Widmungstafel, Pfosten).
- Tests: `web/tests/shots.mjs` (neu: `ONLY=a,b`, Punkte rosaluxemburg/altstetten/wiedikon), `look.mjs` (schnelle Einzelbilder), `raildbg.mjs`, `perf.mjs`, `gameplay.mjs`, `touch.mjs`.

### Recherche (für den nächsten Schritt «Landmarks modellieren»)
- `research/places/` (Kreis 9/3: 6 Orte) und `research/places_k45/` (21 Orte), Kontaktbögen `preview/ref_place_*.jpg`, `preview/ref_k45_*.jpg`, Lizenzen in den `places*.json`.
- Geodaten-Sweeps: `research/ogd_catalog.md` (109 Stadt-Layer), Kanton/Bund-Sweep, Fotos pro Kachel: `research/photos/by_tile.json` (807 Fotos, 273/279 Kacheln, Skript `pipeline/photos/fetch_by_tile.py`, Bögen `preview/ref_tiles_*.jpg`) → Grundlage für Fassaden-Notizen im neuen Gebiet.

### Messung (nach Fixes, 2026-10-15)
- Handy: 60 fps (4× gedrosselt), 189–231 Calls, 0.9–1.1 Mio Dreiecke. PC: 418–458 Calls, 2.1–2.9 Mio. Download prod. geschätzt ~15 MB bis spielbar.
- Fixes: LOD für Velos und parkierte Autos (Ersatzmodelle ab `Tiles.bikeRadius`), ÖV-Haltestellen nach Distanz ausgeblendet, Bahn-Radius Handy 0.62×, Meshopt-Decoder im Bahn-Loader.
- Bahnareal-Boden (Schotter tief) und Brücken begehbar geprüft (`tests/bridge.mjs`). gameplay/touch grün. Zwischenstand-Bild: `preview/zwischenstand_2026-10-15.jpg`.

## Strassen v2 (2026-10-15, Agent)
Decals (`decals.ts`): einheitliche UV (oben = Fahrtrichtung), Velo neu, Pfeile 7–10. Neu: `streets_arrows.py`, `streets_ortho.py` (rote Flächen aus Orthofoto), `streets_islands.py` (Tram-Inseln, Sperrflächen), `ground_paint.py`, `roadgraph.py`+`sites.blocked_zones()` (Baustellen sperren Spuren). Für Komplettbuild: `pipeline/roadgraph.py` (schon gelaufen) + alle Kacheln (Decals und Boden ändern sich). Test-Skripte: `web/tests/streets_decal.mjs`, `streets_face.mjs`.

## Neu (2026-10-15): Karte v2 + Uhr-Panel
- Karte: `pipeline/mapdata.py` -> `web/public/data/map/vec.json` (1.9 MB, 0.7 MB gz; OSM-Gebäude, Strassen nach Klasse, Namen, Tram/Bahn, Haltestellen, Parks/Wasser, Plätze, POIs). `build_map.py` schreibt nur noch `map.json` (Sprungpunkte, Kreise), `map.webp` entfällt. Client: `ui/map_data.ts` (250-m-Zellen mit Path2D), `map_render.ts` (Themes hell/dunkel), `map_labels.ts` (kollisionsfreie Beschriftung, Strassennamen entlang der Linie), `map.ts` (UI, Zoom/Pan/Pinch, Velo-Schalter, Standort-Knopf, Pins = Sprungpunkte). Radar dunkel, dreht mit Blickrichtung, Nordmarke.
- Uhr: `ui/clock.ts` (GameClock: min/day/rate 1/10/60/paused, localStorage `sbz-clock`; URL `?t=`/`?day=` hat Vorrang). Klick/Tap auf die Uhr oben rechts öffnet das Panel. Tests: `web/tests/clock.mjs`, Bilder `web/tests/map_v2.mjs` + `map_v2_sheet.py` -> `preview/map_v2.jpg`.
- Offen: Tram-Liniennummern auf der Karte, Velo-Overlay nur im Spielgebiet (Daten veloinfra.json).

## Neu (2026-10-15, Nachmittag: Detail-Runde mit 6 Agents)
- Landmarks als GLB (`pipeline/landmarks/`, Loader `world/landmarks3d.ts`, Manifest `data/landmarks.json` via `pipeline/landmarks/merge.py`): Letzigrund, Toni-Areal, Volkshaus, Hardau II, Bhf Hardbrücke (detailliert); Prime Tower, KVA, Viadukt, Schiffbau, Lochergut, Kalkbreite, St. Jakob, Bullingerkirche, Kanzlei, Bhf Altstetten, Bhf Wiedikon (Brücke), Kirchen Altstetten/Wiedikon, Löwenbrunnen, Krematorium + Tor Sihlfeld. `hide`-Punkte entfernen swissBUILDINGS3D-Gebäude.
- Spielgebiet + Friedhof Sihlfeld (6.88 km², 219+82 Kacheln). `terrain_cuts.json` (Bahneinschnitt Wiedikon).
- Gebäude: Neubauten seit 2019 aus OSM (`osm_buildings.py`), Dachfarben aus SWISSIMAGE (`ortho_roofs.py`, Mosaik `data/raw/ortho_wms/`), Wartehallen aus swissBUILDINGS3D entfernt, Nachtfenster pro Fenster (materials.ts), Fassaden-Notizen v2 (+746 Adressen).
- Spielplätze (`playgrounds.py`, `world/playgrounds.ts`, 2572 Geräte), private Bäume aus OSM (+10'746), ruhigerer Rasen.
- Agents: Lokale v2 (`gen_shopfronts.py`, `world/storefronts.ts`, Neon, Öffnungszeiten), Baustellen aus OGD (`sites.py`, Kräne), mehr Leute (`pedspots.ts`), 212 Easter Eggs, Strassen/Signalisation nach Luftbild + OGD-Zonen (`streets_rules.py`, `research/streets_audit.md`).
- Tests: `tests/topdown.mjs` (Draufsicht vs. Orthofoto), neue Shot-Punkte (letzigrund, toni, volkshaus, hardau, sihlfeld, hof_hohlstrasse).

### Stand nach Komplett-Build 3 (2026-10-15, 14:30)
- 301 Kacheln (219 Spiel + 82 Kulisse), Build 75 min; GEOS-Fehler im Boden fallen auf OSM-Boden zurück.
- Karten-Phase: Quests, Polizei, Einblendungen aus (`QUESTS`/`GAMEPLAY` in main.ts, DECISIONS #25/#26). Ladebildschirm nur «loading...».
- Messung: Handy ≤ 251 Calls (Wiedikon), ≤ 1.27 Mio Dreiecke, 60 fps; PC ≤ 501 Calls, ≤ 3.4 Mio. Event-Requisiten werden pro Material gemergt (`world/mergestatic.ts`).
- Tests grün (gameplay prüft jetzt «Quests aus»). Bild: `preview/zwischenstand_2026-10-15b.jpg`.
- Nachtplan (wartet auf «los» des Users): Quellen-Recherche texturiertes Stadtmodell, Fassaden-Generator v3, Farb-/Stilnotizen für alle Adressen (Mapillary-Token erbeten), Bäume aus swissSURFACE3D, Strassen v2, Landmarks Runde 3, Nacht-QA.
  - Ergänzt 2026-10-15 (User): **viel detaillierter.** Für alle relevanten Gebäude (Volkshaus usw.), Plätze und Restaurants/Lokale deutlich mehr Fotos suchen und sich stärker daran orientieren. Erlaubte Quellen: Commons, Mapillary, Panoramax (mit Lizenz in `research/`). Google und Websites der Läden nur zum Anschauen, nicht herunterladen und keine Logos übernehmen (DATA_SOURCES.md). Ablauf: pro Ort einen Kontaktbogen anlegen, daraus Notizen zu Farbe, Material, Fenstern und Ladenfront schreiben und erst dann modellieren. QA durch Bildvergleich Spiel vs. Referenz.
  - Bug (User 2026-10-15): Viele Strassenmarkierungen und -objekte sind um 90° verdreht, z. B. Velo-Piktogramme. Alle Decals und Signale auf ihre Ausrichtung zur Fahrtrichtung prüfen (`streets_rules.py`, `world/decals.ts`, `world/trafficsigns.ts`) und mit Draufsicht-Screenshots kontrollieren.
  - Erledigt, noch nicht committet: Laufen überarbeitet (Gehen 1.7, Rennen 5.0 m/s, passend zu den Animationen; Beschleunigung; ⇧-Knopf auf Touch als Umschalter).

## Nachtlauf (gestartet 2026-10-15 abends, 12 h, User «los»)
Parallele Agents mit eigener Dateizuständigkeit (Aufträge siehe Ergebnisse): (A) Foto-Recherche Landmarks/Plätze → `research/v3/`; (B) Foto-Recherche Lokale → `research/shops_v3/`; (C) Strassen v2 + 90°-Bug Velo-Piktogramm (`decals.ts`) → `preview/streets_v2_*`; (D) Fassaden v3 + Bug graues Fensterraster → `research/buildings/visual_notes_v3.json`; (E) Mocap-Animationen statt Sinus-Clips (`pipeline/blender/mocap_retarget.py`, Vorher `preview/gait_before.jpg`). (F) Auto klauen/fahren + realistischere Autos/Velos (`player/drive.ts`); (G) Rendering v2 (Himmel/IBL/Schatten/Tonemapping, `preview/render_v2_*`); (H) Stadtkarte v2 + Uhrzeit per Klick auf die Uhr (`ui/clock.ts`, `pipeline/mapdata.py`). Danach: Landmarks/Plätze Runde 3 (Röntgenplatz ausdrücklich gewünscht) und Ladenfronten v3 aus A/B, Komplett-Build, QA-Kontaktbogen. Keine Quests (User).
Selbst erledigt: Laufen (Commit db8ee26); OSM-Parks nur noch Rasen, wo AV grün sagt (Kanzlei-Schulhof jetzt befestigt, `build_testarea.py`); OSM-Multipolygon-Gebäude im Abgleich (`osm_buildings.py`) → Westpark/Galaxus Pfingstweidstr. 60 und Technopark wurden fälschlich als «abgerissen» entfernt.

- (G) Rendering v2 fertig: AgX, natürliche Tageszeit-Palette, Sonnenstand Oktober, Schatten-Snapping, Nebel ab 55 m (`preview/render_v2_before/after.jpg`). Nächste Runde (nach Fassaden-Agent): MeshStandard + IBL (PMREM vom Himmel) für Glas/Fenster/Autos, Asphalt-Rauheit, SMAA am PC, Nachtfenster nicht als beige Blöcke.
## Offen / Nächstes
1. Landmarks verfeinern: Prime Tower, Schiffbau, Lochergut, St. Jakob, Kalkbreite, Bullingerkirche, Kanzlei noch grob; Hardau-Farben geschätzt; Grabfelder Sihlfeld fehlen. Offen Strassen: rote Velofurten, Sperrflächen, Abbiegepfeile, Tramhaltestellen-Inseln (research/streets_audit.md). Autos fahren durch Baustellen.
2. ~~Kanzlei-Flohmarkt auf Rasen~~ erledigt (OSM-Parks ∩ AV-grün).
3. Gebäude mit grauem Fensterraster (z. B. neben Rosa-Luxemburg-Platz) → Stil-Zuordnung prüfen.
4. Fahrbahn aus Amtlicher Vermessung? (DECISIONS #20, Bildvergleich nötig).
5. Build dauerte 86 statt 32 min → Profiling (vermutlich Groundcover-Verschnitt).
6. Spawn auf Brücke per Teleport landet unten (groundAt braucht z) – bei Bedarf Deck-Suche beim Teleport.
7. Commit: noch nie committet; User fragen.

## Neu (2026-10-15 abends): Autos klauen/fahren, Auto- und Velo-Realismus (Agent)
- Steuerung: E (Touch: E-Knopf) nimmt das nächste Auto oder Velo (je nach Distanz); Auto: WASD/Pfeile oder Joystick = Gas/Lenkung, Shift/⇧ = Turbo, E = aussteigen (bremst erst bis Stillstand). Code: `player/drive.ts`, `vehicle_model.ts`, `vehicle_player.ts` (Kamera), `vehicle_use.ts` (einsteigen/aussteigen/Fahrer), `world/parkedcars.ts`, `Traffic.findCar`, `world/trafficlights.ts`, Ton `Audio.engine/carCrash/carDoor`.
- Pipeline: `bash pipeline/cars/build_cars.sh` baut jetzt auch `*_drive.glb`; `python3 pipeline/bikes/build_bikes.py` schreibt `rig` (Achsen, Sattel) ins Manifest.
- Tests: `tests/drive.mjs` (Desktop+Touch), `tests/vehicles_sheet.mjs` (-> preview/vehicles_v2.jpg), `tests/bikes_ride.mjs`, `tests/perf_drive.mjs`. Perf Handy (4x CPU): zu Fuss 59 fps/192 Calls, im Auto 60 fps/153 Calls.
- Offen: Fussgänger:innen weichen fahrenden Autos nicht aus (fahren durch); Scheinwerferkegel/Nachtlicht am gefahrenen Auto; Tacho/HUD; Lenker der Velos dreht nicht mit; `ridePose` Fussneigung nur grob.
