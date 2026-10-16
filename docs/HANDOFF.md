# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## NÄCHSTE RUNDE: QUALITÄT VOR NEUEM (User 2026-10-16 Abend)
User nach Build 10: «very buggy … cars in water, HB looks really off». Nächste Runde **keine neuen Inhalte**, sondern Qualität und viele Realitäts-Checks mit mehreren Agents (max. 3 gleichzeitig, siehe Arbeitsweise).
1. **Zuerst Cache ausschliessen:** Browser hält Kacheln/Modelle/data bis 1 Tag (+7 Tage stale) – alte Kacheln + neue `landmarks.json` mischen sich. Fix: Versions-Parameter (`?v=<commit>`) an alle Daten-/Kachel-/Modell-URLs; danach erst Bugs beurteilen (privates Fenster).
2. **Autos im Wasser:** Verkehrsgraph/Parkautos/Brücken gegen `water.py`-Polygone prüfen (Skript analog `pipeline/audit_rail.py`), Ursache vermutlich neue AV-Fahrbahn (#45) oder Brücken-Ausschluss.
3. **HB:** Gesamtbild prüfen (Halle, Perrondächer neue Farbe, Untergeschosse/Stencil-Schnitt #48, Escher-Platz/Rasen statt Pflaster). Notfalls Untergeschosse per Manifest abschalten.
4. **Realitäts-Checks:** feste Kamerapunkte (Foto | Spiel) an 30+ Orten, je Agent ein Gebiet; jede Abweichung als Ticket in `research/qa_round/` mit Ursache und Fix; Fixes nur über Pipeline/Overrides; nach jedem Fix Testkacheln + Vergleichsbild.
5. Erst wenn die Liste leer ist: neue Häuser/Details.

## Abend 2026-10-16 (Build 10) – kurz
Ziel weiterhin: **mehr Details, echtere Karte**. Heute neu (Details in den Abschnitten unten und DECISIONS #45–#48):
- Langstrasse: 42 Häuser als Landmarks nach Fotos (langA 8, langB 19, langC 15: u. a. Klaus, Rothaus, Longstreet, Fat Tony), Markierung aus SWISSIMAGE (`markings_override.py`).
- HB: begehbare Untergeschosse (Shopville, Museumstrasse 41–44, Löwenstrasse 31–34, #48), Perron-Ausstattung, Escher-Brunnen, Velostation Europaplatz (#47), Perrondach-Innenfarbe dunkler; Velotunnel Stadttunnel Südhälfte begehbar (`pipeline/landmarks/velotunnel.py`, `velotunnel_decks.json`, `research/hb/velotunnel.md`).
- PJZ als Landmark (`pjz_v2.py`, Höhen geschätzt), 9 Schulhäuser + Ortsmuseum Wiedikon (`k4w6_*`).
- Fahrbahn aus Amtlicher Vermessung (#45, IoU 0.72 → 0.91), Strassenglättung teilweise (`research/road_smooth.md`), Strassendetails aus OSM (`details_osm.py`), Höfe/Vorgärten (+11k Hofbäume), Dächer, Parks/Plätze, Hausnummern/Pfostenschilder, Licht/Skyline/Blob-Schatten.
- UI: Impressum schlicht + Datenschutz, Credits zeilenweise + Repo-Link, Grafik immer automatisch, Bauzaun-Textbanner entfernt.
- Arbeitsweise: **max. 3 Agents gleichzeitig, nie parallel zu einem Komplett-Build Kacheln bauen** – der Mac (16 GB) ist heute 2× abgestürzt.

## Stand (2026-10-16 Nachmittag)
Live: https://sandboxzurich.sandboxzurich-web.workers.dev (Cloudflare Workers Static Assets). Jeder Push auf `main` deployt automatisch (`.github/workflows/deploy.yml`, ~30 s). Kacheln/Texturen sind nicht im Git: nach einem Pipeline-Build `deploy/publish_world.sh` (GitHub-Release «world-data»), dann pushen. Anleitung: `docs/DEPLOY.md`.
Spielgebiet: Kreise 4+5, Teile 9/3, Friedhof Sihlfeld, seit heute bis zum HB-Kopf (`overrides/playarea_extra.json`, 6.93 km²). Karten-Phase: keine Quests/Polizei/Sterne (DECISIONS #25/#26).

### HB v3 Untergeschosse (2026-10-16, Agent HB3)
Shopville + Bahnhöfe Museumstrasse/Löwenstrasse als begehbare Landmark-GLB `hb3_under.glb` (Details: DECISIONS #HB3, `research/hb/v3.md`, Vergleich `preview/hb3_cmp.jpg`, 72 Referenzfotos `preview/ref_hb3_0..5.jpg`). Treppen S1 (Querhalle) und S2 (Bahnhofplatz) hinunter/hinauf getestet (`pipeline/landmarks/hb3_walk.mjs`). Nächster Schritt: Look verbessern (Boden/Wände zu hell und flach, Schilder, Lichtfarben nach den Fotos), Rolltreppen, Ausgänge, Perronlängen mit SBB-Plan abgleichen, Terrain-Schacht an weiteren Zugängen.

### Was heute dazukam (Details: DECISIONS #37–#44, Abschnitte in den genannten research-Dateien)
- **Handy/iOS:** halbe Atlas-/Masken-/Normal-Auflösung auf Handys, JS-Kopien nach GPU-Upload frei, kleinerer Kachelradius, Speicherleck beim Kachel-Entladen behoben (`Tiles.disposeTile`, purge*-APIs; +720 → +31 MB nach 9 Sprüngen, Test `web/tests/qa_leak.mjs`). Modelle per Meshopt gepackt (`pipeline/pack_models.py`; NICHT Bäume/Autos/Velos – gltfpack verliert dort Daten).
- **UI:** Ladebildschirm mit Fortschritt, Einstellungen (Grafik/Ton/Musik/Kamera/Joystick), Steuerungshilfe beim ersten Start, Impressum (Daniel Gnägi), Karte im alten dunklen Look ohne Sprungpunkte (überall hintippen), Sterne ausgeblendet.
- **Spielen:** sichere Spawn-Suche (`player/spawn.ts`), Kamera-Sweep (nicht mehr in Wänden), Kreis-Collider für Bäume/Laternen/Bänke, Landmark-Footprints als Collider (begehbare Landmarks mit eigenen Wandringen: Feld `walkable`/`colliders`), Touch-Rennen bleibt an, Totzone.
- **Fahrzeuge:** Crashes ohne Durchdringen, Schaden/Dellen/Rauch/Wracks, Velo-Sturz (#38). Verkehr nur auf erlaubten Strassen inkl. Begegnungszonen-Ausschluss, Parkautos nur an Fahrbahnen (#41, Test `traffic_legal.mjs`: 0.00 %). Fahrzeuge/Haltestellen auf Brückendecks (`pipeline/decktrack.py`). Tram 2000, Trams/Busse v2.
- **Leute:** CMU-Mocap + Clip-Bibliothek, Look-Kit (Brillen, Bärte, Mützen, Westen), Rollen (Bau, Büro, Kurier, Trolley), keine Fussgänger:innen auf Bahnland (`pipeline/railzone.py`), Bank-Sitze korrekt.
- **Bahn:** Bahnnetz v2 aus OSM (Gleisachsen, Weichen, Signale, Joche, abgestellte Züge, texturierter Schotter), Bahnhöfe Hardbrücke/Altstetten/Wiedikon nach SBB-Perronkanten (#39), Zürich HB mit begehbarer Halle und Perrons 3–18 (#40, `research/hb/`).
- **Stadt:** Landmarks-Wellen 3–5 + Spezialbauten (82+ Einträge in `web/public/data/landmarks.json`, u. a. Zentralwäscherei, Swissmill, Kraftwerk Letten, Westpark, Egli-Siedlung/Hohlstrasse 283–305, Langstrassen-Unterführung (#42) und Ole Ole Bar). Strassen geglättet (`pipeline/road_height.py`, #44). Sihl/Limmat mit Wasser (`pipeline/water.py`, #43). Foto-Abgleich (`research/fidelity.md`): Boden, grüne Velostreifen (Foto-belegt), Poller/Veloständer/Roller aus Daten, Blaue-Zone-Tafeln, Bodenzahlen 30/20.
- **Ton:** Stadt-Ambience prozedural (`audio_amb.ts`), Hip-Hop-Musik CC BY (`audio_music.ts`, `research/music.md`).

### Pipeline-Reihenfolge (Komplett-Build)
1. Nur bei Bedarf: Texturen (`gen_facades.py neubau_b`, `gen_facades3.py`, `gen_textures.py`, `gen_wildposters.py`), Modelle (Blender-Skripte, danach `pack_models.py`), Landmarks (`k*_*.py`, `merge.py`), Bahn (`railways.py`).
2. `playarea.py` → `roadgraph.py` → `transit.py` → `decktrack.py` → `railzone.py`.
3. `.venv/bin/python pipeline/build_testarea.py > logs/build_fullN.log 2>&1` (~55–60 min; einzelne Kacheln `SBZ_TILES=ix_iy,…`).
4. `deploy/publish_world.sh`, Commit, Push.

### Tests (web/tests)
gameplay, touch, drive, crash, clock, music, traffic_legal, qa_leak, qa_spawn, perf (Handy 4×), perf_pc, shots (Kontaktbogen per PIL), look, topdown, fidelity_shots. Regeln für Agents: keine Warteschleifen mit `pgrep -f build_testarea` (matchen sich selbst), nie `git stash`, nie `pkill -f build_testarea` (bricht fremde Builds ab).

## Nächste Schritte (Priorität)
1. **Gleise/Brücken bereinigen** (`research/audit_rail.md`, Skript `pipeline/audit_rail.py`): 45 Auto- und 65 Velo-Kanten über Bahnfläche ohne Deck (u. a. Kante 1096 bei (-4, 922), 684 m; 1090 bei (-1629, 869)), 186 Velos/122 Ständer/84 Roller/17 Arbeiter in Bahnfläche, 21 Haltestellendächer; Spawn unter Brücken kann aufs Gleis führen. Vorschläge in `pipeline/overrides/rail_excl.json` (noch nicht angewendet).
2. **Strassen glätten fertig machen:** Audit nach Build 10 neu laufen lassen (`road_smooth_audit.py`), Problemstellen Seebahn-, Bullinger-, Norastrasse; Bridges-Ride-Test (`web/tests/bridges_ride.mjs`) gegen Build 10.
3. **Langstrasse:** Sichtkontrolle der 42 Häuser tags/nachts, Farben geschätzt bei Kir Royal, Peeeng, Rasputin, Midway, Monroe (`research/langstrasse_C.md`); Weissmarkierungen Süd prüfen.
4. **HB:** Untergeschosse zu hell/flach, Rolltreppen/Lifte, Ausgänge Europaallee/Sihlquai, Perrons nach SBB-Plan (`research/hb/v3.md`); wartende Personen auf Perrons (neue Spot-Art); Velotunnel: Stufe 2.4 m am Portal, Velo-Piktogramme, Nordhälfte (`research/hb/velotunnel.md`).
5. **PJZ:** Höhen/Eingang an Fotos prüfen (`preview/pjz_cmp.jpg`, `research/pjz.md`).
6. **Fehler-Sweep:** Nachher-Lauf gegen Build 10 (`web/tests/sweep.mjs`, vorher 10 685 Cluster).
7. Auf echten Geräten testen (iPhone Safari): HB-Untergeschosse nutzen Stencil-Maske – Handy-Speicher/FPS messen.
8. Vor öffentlichem Launch: Plakat-Freigabe, `noindex` in `web/public/_headers` entfernen. Quests erst nach Entscheid des Users.

## Letzte Kontrolle
Build 10 (`logs/build_full10.log`): alle Kacheln, 0 Fehler, 49 min. Weltdaten veröffentlicht (`logs/publish10.log`).
- Tests: touch, drive, qa_spawn (26/26), qa_leak (+30 MB, PASS) OK. perf Handy 4×: 58 fps, 246 Calls, 566k Tris, 189 MB JS, Laden 4.3 s.
- gameplay: Velo fährt nur 3.2 m (Testvelo bei (785,-606) steht jetzt 3.5 m vor einem Collider – vermutlich neues Langstrassen-Landmark; Test robuster machen).
- traffic_legal: 0.02–1.15 % ausserhalb der Fahrbahn (vorher 0.00 %) – Folge der neuen AV-Fahrbahn (#45); Escher-Wyss-Platz 1.15 % am höchsten. Graph an AV-Fläche anpassen.
- Sicht (`preview/qa10_sheet.jpg`): Langstrasse, PJZ, Velotunnel-Rampe ok; **Bahnhofplatz zeigt Rasen statt Pflaster** (Boden-Klassifikation am Rand der Spielgebiets-Erweiterung prüfen).


## Stand: Haltestellen-Ausstattung, Blaue Tafeln, Velopumpen, Korrekturknopf
- `pipeline/stops_equip.py` -> `web/public/data/stops_equip.json` (VBZ-OGD, CC0): echte Wartehallen, Bänke, Anzeigen, Automaten, Plakate; Laufzeit `web/src/world/stops_equip.ts` (InstancedMesh, eigene Gruppe, Dispose). Haltestellen ohne Stadtdaten behalten das Standard-Set. Schilderpfosten bleiben.
- `pipeline/ogd_extras.py` -> `ogd_extras.json`: Blaue Tafeln (Text als Fakt, Karte mit Quelle bei <7 m, `web/src/world/ogd_extras.ts`) und Velopumpen; kein Kachel-Build nötig.
- Menü-Knopf «Stimmt etwas nicht?» (`web/src/ui/report.ts`, mailto), `pipeline/apply_corrections.py`, Anleitung `research/corrections.md`.
- Tests: `web/tests/report_mailto.mjs`, `stops_equip_shots.mjs` (preview/stops_equip.jpg), `ogd_extras_shot.mjs`.
- Offen: Orientierung der Anzeigen/Plakate ist abgeleitet (Achse aus Attribut, Seite zum nächsten Gleis), Sichtprüfung vor Ort; Shelter-Typen (nur `36` im Datensatz).

## Stand: Höfe/Vorgärten/Vegetation (yards)
- `pipeline/yards.py` (Hooks `# YARDS` in build_testarea.py): nDSM-Hofbäume (+11k in `C["trees"]`, ~1.5 min Prep), Sträucher/Hecken (nDSM+Ortho+Grünflächen-Pflegeeinheiten), Vorgarten-Mäuerchen/Zäune, Hofinventar, Familiengarten-Häuschen; Laufzeit `web/src/world/yards.ts`. Doku `research/yards.md`. Nur 6 Testkacheln gebaut, Rest erst im Komplett-Build. Shots: `web/tests/yards_shots.mjs`, `yards_sheet.py` -> `preview/yards_v1.jpg`.

## Parks und Grünflächen (Sub-Agent)
- Neu: `research/parks/parks.json` (Parkliste + Optionen) -> `pipeline/parks_gen.py` erzeugt `pipeline/overrides/places_detail_parks.json` (Boden Rasen/Kies/befestigt per SWISSIMAGE-`ortho_ground`, Objekte an OSM/OGD-Positionen: Picknicktische, Grill, Trinkwasser, Fitness, Pingpong, Unterstand, WC, Kunstwerke). `pipeline/parks_notes.py` schreibt `research/parks/<id>.md` + `CREDITS.md`; Fotos: `pipeline/photos/fetch_parks.py` (data/raw/photos/parks/, research/parks/photos.json), Bögen `parks_sheet.py` -> preview/ref_parks_<id>.jpg; Vergleich preview/parks_<id>.jpg, parks_all.jpg.
- places_detail: neuer Platz-Schlüssel `reach` (Radius, Default 150), neue Typen grill, fitness, ysculpt, pyramid (web/src/world/places_detail.ts).
- Ausserhalb des Spielgebiets (nicht umgesetzt): Fritschiwiese, Sihlhölzli, Lettenareal/Wipkingerpark. Hardturm-Wiese ohne Fotos. Noch offen: rote Mauern Pfingstweidpark, Urnenbrunnen Friedhof Sihlfeld (Positionen), Handarbeit pro Park nach Fotos.


## Stand: Langstrasse Nord (langA)
- Fotos 212 Ausschnitte (`research/langstrasse_A_photos.json`, Bögen `preview/ref_langA_*.jpg`), 35 Fassadennotizen, 12 Ladenfronten, 8 Landmark-Häuser (`langA_houses.py`), Markierungs-Override (`markings_ortho.py`, `markings_synth.py`, `markings_override.py`, DECISIONS #46). Kontrolle `preview/langA_cmp.jpg`, `preview/langA_markings.jpg`.
- Test-Kacheln 5_-1, 5_0, 4_-1, 4_-3, 3_-5 neu gebaut; Rest der Langstrasse (Süd, Gelbmaske im Schatten schwach) bei Komplett-Build; `markings_ortho.py` danach erneut laufen lassen, falls Überschreibung nötig. Nächster Schritt: Weissmarkierungen (Haltelinien, Parkfelder) messen.

## HBX (HB-Umfeld, 2026-10-16)
Erledigt: `hbx_perron`/`hbx_platz` (siehe `research/hb/hbx.md`, Vergleich `preview/hbx_cmp.jpg`). Offen: wartende Personen auf Perrons (neue Spot-Art in `pedspots.ts`), Europaallee-Passerelle/Velostation, Sihlquai-Carterminal, Kachel-Neubau für den Escher-Collider.
