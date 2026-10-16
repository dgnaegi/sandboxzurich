# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Stand (2026-10-16 Nachmittag)
Live: https://sandboxzurich.sandboxzurich-web.workers.dev (Cloudflare Workers Static Assets). Jeder Push auf `main` deployt automatisch (`.github/workflows/deploy.yml`, ~30 s). Kacheln/Texturen sind nicht im Git: nach einem Pipeline-Build `deploy/publish_world.sh` (GitHub-Release «world-data»), dann pushen. Anleitung: `docs/DEPLOY.md`.
Spielgebiet: Kreise 4+5, Teile 9/3, Friedhof Sihlfeld, seit heute bis zum HB-Kopf (`overrides/playarea_extra.json`, 6.93 km²). Karten-Phase: keine Quests/Polizei/Sterne (DECISIONS #25/#26).

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

## Nächste Schritte
1. **Auf echten Geräten testen** (iPhone Safari, Android): Absturzfreiheit nach vielen Ortswechseln, FPS, Touch. Rückmeldungen sammeln.
2. **Handy-Perf:** unter Last gemessen teils 35–49 fps (Gleisfeld, Fluss, Stadt). Ruhige Messung nach dem Build; Hebel: Bahn-/Landmark-LOD, Leute-Dichte, Schattendistanz.
3. **Offene Kleinigkeiten:** schwebende Würfel über der Hardbrücke (Quelle: Kachel/Landmark, nicht Bahn), Brückendeck-Höhen gestuft (`world/bridges.ts`), Tram/Trolleybus nicht durch die Langstrassen-Unterführung, Tunnelbelag gestreift, Wiedikon-Perrondach flach, HB-Perrondach von innen flach, Wartende auf Perrons (`research/stations/spots_*.json` in pedspots einbinden), Durchmesserlinie fehlt im Bahngraph.
4. **Inhalt:** Wildplakate an Unterführungen/Bauzäunen, weitere Fassaden nach Fotos (am besten mit Fotos/Feedback aus dem Quartier), Grünflächen-Details (Geländer, Treppen am Fluss).
5. **Vor öffentlichem Launch:** Plakat-Freigabe, `noindex` in `web/public/_headers` entfernen.
6. Quests (M4) erst nach Entscheid des Users.

## Letzte Kontrolle
(wird nach dem Komplett-Build `logs/build_full8.log` ergänzt)


## Stand: Haltestellen-Ausstattung, Blaue Tafeln, Velopumpen, Korrekturknopf
- `pipeline/stops_equip.py` -> `web/public/data/stops_equip.json` (VBZ-OGD, CC0): echte Wartehallen, Bänke, Anzeigen, Automaten, Plakate; Laufzeit `web/src/world/stops_equip.ts` (InstancedMesh, eigene Gruppe, Dispose). Haltestellen ohne Stadtdaten behalten das Standard-Set. Schilderpfosten bleiben.
- `pipeline/ogd_extras.py` -> `ogd_extras.json`: Blaue Tafeln (Text als Fakt, Karte mit Quelle bei <7 m, `web/src/world/ogd_extras.ts`) und Velopumpen; kein Kachel-Build nötig.
- Menü-Knopf «Stimmt etwas nicht?» (`web/src/ui/report.ts`, mailto), `pipeline/apply_corrections.py`, Anleitung `research/corrections.md`.
- Tests: `web/tests/report_mailto.mjs`, `stops_equip_shots.mjs` (preview/stops_equip.jpg), `ogd_extras_shot.mjs`.
- Offen: Orientierung der Anzeigen/Plakate ist abgeleitet (Achse aus Attribut, Seite zum nächsten Gleis), Sichtprüfung vor Ort; Shelter-Typen (nur `36` im Datensatz).
