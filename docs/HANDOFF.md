# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Stand (2026-10-15, nach 8-h-Lauf)
**Spielgebiet = ganze Kreise 4+5, Teile Kreis 9 (Hohlstrasse, Lindenplatz, Bhf Altstetten) und Kreis 3 (Bhf Wiedikon, Schmiede).** 6.44 km², 202 Spielkacheln + 77 Kulissenkacheln, Rand = Baustellenzaun («BAUSTELLE – DURCHGANG GESPERRT») mit Kollision. Keine Missionen (nur `?missions`).

### Pipeline (alles reproduzierbar)
- `pipeline/playarea.py` → `data/build/playarea.json` (Polygon, Kacheln). `config.py` liest es; `GTZ_AREA=test` = altes Testgebiet.
- `build_testarea.py` baut alle Kacheln parallel (~35–85 min, Log `logs/build_full2.log`). Einzelne Kacheln: `GTZ_TILES=ix_iy,…`. Fehler einer Kachel → «TILE FAILED» im Log, Rest läuft weiter.
- Neu eingebunden: `bridges.py` (268 Brücken, Decks + Pfeiler, Boden darunter ausgeschnitten), `plazasigns.py` (43 Widmungstafeln am vermessenen Ort + Platzschilder an Fassaden/Pfosten), `overrides/landmark_signs.json` (grosses Rosa-Luxemburg-Platz-Schild mit Nelken), `groundcover.py` (Amtliche Vermessung: Innenhöfe Rasen/befestigt, Bahnareal = Schotter tief, Gleise von `railways.py` darauf).
- Separat: `railways.py` (Gleise/Masten/Perrons → `web/public/models/trains/tiles`, `data/rail.json`), `scenes_build.py` (138 Easter Eggs/Szenen aus `overrides/scenes_src.json`), `anecdotes.py` (595 Texte inkl. 552 Strassennamen).

### Web
- `engine/grading.ts` (Vice-City-Look: ACES + Split-Toning + Vignette), Bloom nur PC, neue Tageszeit-Keyframes.
- `world/bridges.ts` + `Tiles.groundAt()` (Spielerin läuft auf Brücken), `world/railways.ts` (S-Bahn-Züge, Fahrleitung; Handy kleinerer Radius), `world/landmarks.ts`, `world/streetsigns.ts` (Schildlänge nach Name, Widmungstafel, Pfosten).
- Tests: `web/tests/shots.mjs` (neu: `ONLY=a,b`, Punkte rosaluxemburg/altstetten/wiedikon), `look.mjs` (schnelle Einzelbilder), `raildbg.mjs`, `perf.mjs`, `gameplay.mjs`, `touch.mjs`.

### Recherche (für den nächsten Schritt «Landmarks modellieren»)
- `research/places/` (Kreis 9/3: 6 Orte) und `research/places_k45/` (21 Orte), Kontaktbögen `preview/ref_place_*.jpg`, `preview/ref_k45_*.jpg`, Lizenzen in den `places*.json`.
- Geodaten-Sweeps: `research/ogd_catalog.md` (109 Stadt-Layer), Kanton/Bund-Sweep, Fotos pro Kachel: `research/photos/by_tile.json` (807 Fotos, 273/279 Kacheln, Skript `pipeline/photos/fetch_by_tile.py`, Bögen `preview/ref_tiles_*.jpg`) → Grundlage für Fassaden-Notizen im neuen Gebiet.

### Messung (nach Fixes, 2026-10-15)
- Handy: 60 fps (4× gedrosselt), 189–231 Calls, 0.9–1.1 Mio Dreiecke. PC: 418–458 Calls, 2.1–2.9 Mio. Download prod. geschätzt ~15 MB bis spielbar.
- Fixes: LOD für Velos und parkierte Autos (Ersatzmodelle ab `Tiles.bikeRadius`), ÖV-Haltestellen nach Distanz ausgeblendet, Bahn-Radius Handy 0.62×, Meshopt-Decoder im Bahn-Loader.
- Bahnareal-Boden (Schotter tief) und Brücken begehbar geprüft (`tests/bridge.mjs`). gameplay/touch grün. Zwischenstand-Bild: `preview/zwischenstand_2026-10-15.jpg`.

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

## Offen / Nächstes
1. Landmarks verfeinern: Prime Tower, Schiffbau, Lochergut, St. Jakob, Kalkbreite, Bullingerkirche, Kanzlei noch grob; Hardau-Farben geschätzt; Grabfelder Sihlfeld fehlen. Offen Strassen: rote Velofurten, Sperrflächen, Abbiegepfeile, Tramhaltestellen-Inseln (research/streets_audit.md). Autos fahren durch Baustellen.
2. Kanzlei-Flohmarkt steht auf Rasen (sollte Asphalt-Schulhof sein) → Parks/AV-Grün dort prüfen.
3. Gebäude mit grauem Fensterraster (z. B. neben Rosa-Luxemburg-Platz) → Stil-Zuordnung prüfen.
4. Fahrbahn aus Amtlicher Vermessung? (DECISIONS #20, Bildvergleich nötig).
5. Build dauerte 86 statt 32 min → Profiling (vermutlich Groundcover-Verschnitt).
6. Spawn auf Brücke per Teleport landet unten (groundAt braucht z) – bei Bedarf Deck-Suche beim Teleport.
7. Commit: noch nie committet; User fragen.
