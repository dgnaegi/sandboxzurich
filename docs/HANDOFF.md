# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Linien (Auftrag L, 19.10.)
Längslinien neu (`pipeline/markings_lines.py`, Eingriffe in `streets.markings/junction_gaps`, `build_testarea._ground_base` LINE_LIFT/ROAD_CELL); wirkt erst im nächsten Komplett-Build (Build 14 lief mit altem Code). Zahlen `research/lines.md`.

## Stand 2026-10-19 mittags (Build 15, Release 4) – ZUERST LESEN
Sondernacht 18.10. 22:00 – 19.10. 16:00 abgeschlossen: 4 Releases (Builds 12–15). Build 15: `logs/build_full15.log` 0 Fehler, 50 min; QA `logs/qa15.log` **alles grün** (tsc, gameplay, touch, crash, drive, knock, traffic_legal 0.01 %, move_quality, qa_spawn 26/26, qa_leak +25 MB); perf Handy 58 fps / 262 Calls / 579k Tris / 4.3 s. Sicht `preview/qa15_sheet.jpg`. DECISIONS #51–#57.
**Seit Release 2 neu (Releases 3+4):** Fassaden v4 (`pipeline/facade.py`: Geschosse, Achsen an Adress-Front, Rustika-EG, Band, Gauben; #55) · Spawn nur an 25 geprüften Orten (`spawns.json`, #56) · HB: schwebende Dach-only-Platten versteckt, sonst keine offenen Räume gefunden (`research/hb/fix_2026-10-19.md`) · Dach-only-Objekte stadtweit mit Stützen (#57) · Schlachthof Runde 4 (Backstein, echte Tore + Innenhalle, Restaurant-Dach) · Strassenlinien als Ketten (#51, Stummel 47 → 19) · Zebras aus Ortho 211 → 403 (Recall ~93 %, Precision ~80–90 % geschätzt, Regler `markings_ortho25.STRIPE_MIN`) · 4 ungetaggte Unterführungen abgesenkt (Bullingerstrasse u. a., `pipeline/underpass_infer.py`) · Fahrbahn-Fill innerhalb der Fahrbahn bis 3 m (Restbuckel) · **Zone 2**: Grenze an der Limmat, 307 Notizen, 6 Haus-Landmarks (`z2_houses.py`), Plätze · Katalog: 264 Plakatstellen + 4 Kioske.
**Nächste Nacht:** laut `docs/NIGHT_PLAN.md` Zone 1 (HB/Langstrasse). Zone 2 ist zu ~70 % erledigt (Rest: Escher-Wyss/Hardbrücke-Häuser ohne Fotos, Läden, Haltestellen).
**Lehren für alle weiteren Zonen (wichtig):**
1. Fotos sind fast nur Schrägaufnahmen (Dashcam/Mapillary): Farbe/Material/Geschosse gehen, **Fensterachsen/Erker/Ladenschilder kaum** (N4: nur 15 von 200 Häusern zählbar). Grösster Hebel: frontale Fotos (User gefragt) oder Achsen aus Fassadenbreite ableiten.
2. Notizen immer mit allen v4-Feldern erfassen (geschosse, achsen, gesims/rustika, gauben/mansarde, erker, laden), sonst wirkt der Generator nicht.
3. Nach `facades_notes.py` immer `pipeline/zones/merge_notes.py --zone z2|z4` (und `--fields`) neu laufen lassen.
4. Agents hinterlassen `until …; sleep`-Warteschleifen → am Ende `ps -eo pid,command | grep "until \[ -s logs/agent"` prüfen und per PID beenden.
**Offene Fragen an den User:** frontale Fotos aus dem eigenen Quartier? · 3 Laden-Umbenennungen ohne Quelle (Felice Pizza, Blumenhaus Sihlfeld, Duplikat) · Wasserwerkstrasse (1604,81) als Unterführung erkannt – echt? · Farbe Schlachthof-Nordblöcke · Ni-Una-Menos nur als Platzname (Haltestelle bleibt Helvetiaplatz) ok? · iPhone-Test Langstrasse/HB/Idaplatz.
**Offene Tickets:** T21 (Fahrbahn an breiten Knoten zu schmal), Mulden unter Brücken ohne OSM-Brückentag (Seebahn-, Kanzleistrasse, Sihlbrücke), Restbuckel Kornhausbrücke 20 cm, FGG-Hecke Eingang, Katalog V9 ohne Foto, Leuchten nicht im Katalog, Läden Zone 4/2 meist Default-Schilder, Zone-4-Achsen nur 54 Häuser. Langstrassen-Unterführung: Agent U lief bis 12:30 (Ergebnis siehe unten bzw. `research/v3/langstr_unterf.md`).

## Stand 2026-10-19 morgens (Build 13, Release 2) – zuerst lesen
Build 13: `logs/build_full13.log` 0 Fehler, 49 min; Weltdaten `logs/publish13.log`. QA `logs/qa13.log`: tsc, gameplay, touch, crash, drive, traffic_legal (0.01 %, Parkautos 0.17 %), move_quality, qa_spawn 26/26, qa_leak +25 MB, perf Handy 58 fps / 270 Calls / 583k Tris / 4.3 s. Rot: knock.mjs – Ziel-Pfosten (884.4,-834.6) kippt, Auto stoppt 3 m dahinter an hartem Objekt (884.7,-831.3) – Testziel-Auswahl robuster machen (Ziele ohne harte Nachbarn ≤ 5 m). Sicht `preview/qa13_sheet.jpg`.
**Seit Release 1 neu:**
- Bestandsaufnahme (`research/zones/baseline.md`): Ø **2.5/5** über 15 Orte; Häuser: Höhe/Farbe plausibel, **Fassaden generisch** (kein Ort ≥ 4). Zonen-Reihenfolge neu: 4 → 2 → 1 → 5 → 3 (`docs/NIGHT_PLAN.md`). Zonen `pipeline/overrides/zones.json` (`pipeline/zones.py`, grob als Rechtecke), Shots `web/tests/zone_shots.mjs <N> before|after`.
- **Zone 4 Wiedikon (= Nacht 1 vorgezogen):** 248 neue Fassadennotizen (`pipeline/photos/facades_z4_*.py`, Merge `pipeline/zones/merge_notes.py` – nach `facades_notes.py` immer neu laufen lassen!), 8 Häuser als Landmarks (`pipeline/landmarks/z4_houses.py`), Plätze-Boden nach Ortho (`places_detail_z4.json`), hellere Trottoirkanten (CURB_TOP_W), Ladens-Overrides `storefronts_z*.json` (Name, Notizen, `"closed": true` → kein Schild; Hook `shopfronts_v3.py`), Namensprüfung 79 Läden (`research/zones/zone4_namecheck.md`; 3 Umbenennungen ohne belastbare Quelle NICHT übernommen). Global: AV-befestigte Flächen nicht mehr als Rasen (~25 600 m² allein in Z4).
- Tickets: T10 Linien am Spielgebiet geclippt (53 statt 64), T11 Kamera ignoriert Footprints < 20 m², Katalog: V3/V7/V8 nach Fotos, VBZ-Fahnen, DFI-Abfahrtstext zurück.
- Zone 2 Inventar vorbereitet (`research/zones/zone2*`, 265 Fotos `data/raw/photos/z2`). **Zone-2-Rechteck reicht über die Limmat (Nord-, Röthelstrasse) → vor Nacht 2 in `zones.py` enger ziehen.**
**Wichtigster Hebel für alle Zonen:** Der Fassadengenerator nutzt aus den Notizen nur Farbe/Stil – Fensterachsen, Sockel, Gesimse, Erker, Dachgauben, EG-Ladenzone werden nicht umgesetzt. Darum wirken auch korrekt gefärbte Häuser generisch (`preview/z4_houses_cmp.jpg`).
**Offen Zone 4:** 223 Häuser ohne Notiz (155 ohne brauchbares Foto), Ladenschilder/Markisen fast alle Default (Fotos zeigen kaum lesbare Fronten), Velostreifen/Parkfelder/«30», Haltestelle Goldbrunnenplatz (Glasdach, Uhr), Mansarden/Läden Birmensdorferstr. 299–303, CREDITS für Mapillary/Panoramax-IDs der Notizen.

## Stand 2026-10-19 früh (Build 12, Release 1 der Sondernacht) – zuerst lesen
Sondernacht 18.10. 22:00 – 19.10. 16:00 (`docs/NIGHT_PLAN.md`). Build 12: `logs/build_full12.log`, 0 Fehler, 48 min; Weltdaten `logs/publish12.log`.
**Neu (Commits 10cee4d … 6491887):**
- Landmarks nach Fotos: **Schlachthof** (`pipeline/landmarks/schlachthof*.py`, Portale NW/SE verschieden, Uhr SE, Kamin, Restaurant), **Letzipark** neu aus swissBUILDINGS3D + «LETZ(Palme)»-Fassade, **Frau Gerolds Garten** (Container, Stände, Tor), **Letzigrund** 11 begehbare Tore, Quartiergarten Hard Tor geprüft. Abnahme: Schlachthof 4, Letzipark 4, FGG 3 (`preview/*_cmp3.jpg`, `fgg_cmp2.jpg`).
- **Objekt-Katalog** (Nacht 0 vorgezogen): 21 Modelle (`pipeline/catalog/`, `web/public/models/catalog/`), Zuordnung `web/public/data/catalog.json` (185 Brunnen nach Material/Art, 714 Haltestellen-Objekte nach VBZ-Daten), Laufzeit `web/src/world/catalog.ts`, A/B mit `?nocatalog`. Doku `research/catalog/`.
- **Fahren:** Phantom-Collider der 4076 Seilleuchten entfernt (Crashes/km 5.5 → 2.2), Schilder/Poller/Velobügel/Abfalleimer kippen beim Anfahren (`web/src/world/knockable.ts`, `research/driving_round3.md`).
- **Strasse:** Tramschienen bündig im Asphalt, keine Randstein-Mäuerchen (`pipeline/tram_track.py`, `research/tram_tracks.md`, 22 km → 0 m erhöht); Fahrbahn-Drape 16 → 6 m (Buckel > 8 cm 50 → 17 in Testkacheln, `research/bumps.md`); Bäume unter/auf Decks gefiltert (`yards.drop_deck_trees`); Strassenbäume auf der Fahrbahn an die Kante geschoben (`cityprops.lane_fix`); Fussgängerstreifen aus SWISSIMAGE 0.25 m (234 → 962 im Build, `pipeline/markings_ortho25.py`, Cache `data/raw/ortho_025`); Baustellen nur, wenn am Build-Tag aktiv (`sites.py`).
- **Namen:** Helvetiaplatz heisst im Spiel «Ni-Una-Menos-Platz» (Karte, Quartieranzeige, Orte; `pipeline/overrides/names.json`, `pipeline/names.py`); Haltestelle/Adressen/Amtshaus bleiben «Helvetiaplatz» (keine offizielle Umbenennung gefunden). Lochergut-Leuchtschrift über dem Coop.
- Skyline-Vorhang-Lücken (T04) behoben, Fassaden Weststrasse 177/180 (T05).
**QA Build 12:** tsc, gameplay, touch, drive, traffic_legal (0.02 %, Parkautos 0.17 %), move_quality, qa_spawn 26/26 (Port 5173 angeben!), qa_leak +25 MB PASS; perf Handy 57 fps, 273 Calls, 596k Tris, Laden 4.4 s. **Rot:** knock.mjs – 1 von 5 Pfosten (679,-708) crasht an hartem Objekt bei (683.5,-708.2), Ursache offen; crash.mjs touch «no corner inside a building» wackelt (bekannt). Sicht `preview/qa12_sheet.jpg`.
**Offen (Tickets `research/qa_round/tickets.md`):** T10 Busse ausserhalb Spielgebiet (transit.py clippt auf bbox statt Polygon), T11 Kamera in Baustellen-Collider (-2053,696), T19–T23 (Zebra-Recall ~50 %, Weisslinien, Fahrbahn an breiten Knoten zu schmal, steile Unterführungsportale, Restbuckel), FGG: OSM-Hecke beim Eingang Geroldstrasse, Container ohne Details; Katalog: Fahnen/Kiosk ohne Fotobeleg, DFI-Abfahrtstext weg, Brunnen V3/V7/V8/V9 ohne Fotos; Tram-Rest 2 km Randstein neben Gleis (vermutlich echt, ungeprüft).

## Stand 2026-10-18 Abend (Build 11) – zuerst lesen
Ziel weiterhin **Qualität und echtere Karte**. Arbeitsweise: max. ~4 Agents, Testkachel-Builds nur mit globalem Lock (`until mkdir logs/.tilebuild.lock …; rmdir …`), nie `pkill`, Komplett-Build allein (Mac 16 GB, 2× abgestürzt).

**Heute erledigt** (Details in den Abschnitten unten / research-Dateien / DECISIONS #49–#50):
- Handy: Schilder-/Label-Canvas halbe Auflösung, Landmark-Texturen ≤ 512 px, Plakat/Graffiti halbiert → Langstrasse 448 → ~190 MB Texturen (`web/tests/mem_phone.mjs`). Cache: `?v=<build>` an allen Weltdaten-URLs (`web/src/engine/assetver.ts`, `web/vite.config.ts`). Noch NICHT auf echtem iPhone bestätigt.
- Bewegung (`research/movement_round2.md`, `web/tests/move_quality.mjs`): Gleiten an Pfosten, weiche Kollisionen, NPC-Verkehr bremst vor Hindernissen.
- Strassen (`research/roads_round2.md`): künstliche Rampen weg (Badener-/Seebahnstr.; Ursache `road_height` füllte Bahngraben, Brücken zu hoch), Objekte in Wasser/Bahnland entfernt, Verkehr an AV-Fahrbahn geschnappt, Bahnhofplatz gepflastert. Schwebende Stege: `pipeline/audit_float.py`, `overrides/bridges_excl.json`. Fussgängerstreifen 173 → 234 (`pipeline/crossings.py`, `research/crossings.md`).
- Orte: Lochergut v4 (Passerelle weg, Ladenzeile, Leuchtschrift mit Farbwechsel `// lochergut-neon`), Calvados Bar, Idaplatz-Quartier (Spielgebiet +800×800 m; Fassaden; Kirche; Velos), Zentralwäscherei (nachgemalte Graffiti `zw_graffiti.py`, Schild um die Ecke, Pflanzen), HB-Review (#49), Letzigrund neu (#50), Quartiergarten Hard (`qgh.py`), 4 Plätze (`places_detail_sq3_*`), Hecken-Shader (`web/src/world/foliage.ts`), Asphalt ohne Rechteck-Flicken.
- Systemisch: Gebäude ohne OSM-Adresse holen Fassaden-Notiz über GWR-Eingang (+~416 Häuser); yards-Absturz (GeometryCollection) behoben.

**Build 11 live (2026-10-18, 21:47):** `logs/build_full11.log` 0 Fehler, 229 Spiel- + 78 Randkacheln, 7.29 km²; Weltdaten veröffentlicht. QA: tsc, gameplay, touch, crash, qa_spawn 26/26, qa_leak +25 MB PASS, traffic_legal Busse 0 %, Parkautos 0.17 %; perf Handy 4×: 57 fps, 260 Calls, 608k Tris, Laden 4.6 s; mem_phone Texturen Langstrasse 190 / HB 179 / Hardbrücke 129 MB. drive.mjs «touch: braked to -4.8 m/s» wackelt (Auto fährt nach Stillstand rückwärts, Test-Timing). Sichtkontrolle `preview/qa11_sheet.jpg`.

**Nächste Schritte (Priorität):**
1. Auf echtem iPhone testen (Langstrasse, HB, Idaplatz), Speicher/FPS; Hecken-Shader auf Handy messen (perf 51 fps unter Last gemessen).
2. Realitäts-Tickets `research/qa_round/tickets.md` abarbeiten (T04 blasse Flächen Toni/Schiffbau, T05 Fassaden-Notizen Weststr., T08 Velostreifen Stauffacherstr., T10 schwebender Bus (-1716,-663), T11 Kamera in Gebäude (-2053,699), T18 Landesmuseum fehlt); vorbereitete Overrides `research/qa_round/proposed_*.json`.
3. Letzigrund: Aussenwand 4.6 m verdeckt die Sitze – mit Fotos prüfen und ggf. absenken; Flutlicht nachts schwach. Lochergut: Hof Rasen statt Pflaster, Hochhausfassade zu glatt. Calvados: Schrift gerade statt geschwungen, Extra-Tür. Zentralwäscherei: Eingangskorridor, Kiosk-Grundriss, Lage der Graffiti-Wand. Idaplatz: ein mintgrünes Haus aus Foto #0 nicht zugeordnet (`SBZ_STYLE_LOG`), Kirchendach einseitig. HB: schwebende Kisten Ostgiebel, flache Ostfenster.
4. **Letzipark** (Einkaufszentrum Baslerstrasse, User-Wunsch 2026-10-18): Lage im Spielgebiet prüfen, Fotos, Modell + Ladenfronten. Letzigrund: Portale dunkel/rost statt weiss-rosa, Flutlichtmasten, Strassenansicht mit Abstand.
5. Plätze ohne neue Objekte (Helvetia-, Röntgen-, Bullinger-, Lindenplatz …): Spielgeräte, Bank-Typen, Baumarten. Ernst-Nobs-Platz/Kalkbreite-Hof ohne Belege.
6. Vor öffentlichem Launch: Plakat-Freigabe, `noindex` entfernen.

## NACHTPLAN (ab 2026-10-18)
Realismus-Woche: 7 Nächte à 8 h, siehe `docs/NIGHT_PLAN.md` (Nacht 0: Cache-/Speicherfix + Objekt-Katalog Brunnen/Haltestellen/Möbel, dann je eine Zone). Start: «Lies docs/NIGHT_PLAN.md und führe die nächste offene Nacht aus.»

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

## Nächste Schritte vom 2026-10-16 (teils erledigt, siehe oben)
1. **Gleise/Brücken bereinigen** (`research/audit_rail.md`, Skript `pipeline/audit_rail.py`): 45 Auto- und 65 Velo-Kanten über Bahnfläche ohne Deck (u. a. Kante 1096 bei (-4, 922), 684 m; 1090 bei (-1629, 869)), 186 Velos/122 Ständer/84 Roller/17 Arbeiter in Bahnfläche, 21 Haltestellendächer; Spawn unter Brücken kann aufs Gleis führen. Vorschläge in `pipeline/overrides/rail_excl.json` (noch nicht angewendet).
2. **Strassen glätten fertig machen:** Audit nach Build 10 neu laufen lassen (`road_smooth_audit.py`), Problemstellen Seebahn-, Bullinger-, Norastrasse; Bridges-Ride-Test (`web/tests/bridges_ride.mjs`) gegen Build 10.
3. **Langstrasse:** Sichtkontrolle der 42 Häuser tags/nachts, Farben geschätzt bei Kir Royal, Peeeng, Rasputin, Midway, Monroe (`research/langstrasse_C.md`); Weissmarkierungen Süd prüfen.
4. **HB:** Untergeschosse zu hell/flach, Rolltreppen/Lifte, Ausgänge Europaallee/Sihlquai, Perrons nach SBB-Plan (`research/hb/v3.md`); wartende Personen auf Perrons (neue Spot-Art); Velotunnel: Stufe 2.4 m am Portal, Velo-Piktogramme, Nordhälfte (`research/hb/velotunnel.md`).
5. **PJZ:** Höhen/Eingang an Fotos prüfen (`preview/pjz_cmp.jpg`, `research/pjz.md`).
6. **Fehler-Sweep:** Nachher-Lauf gegen Build 10 (`web/tests/sweep.mjs`, vorher 10 685 Cluster).
7. Auf echten Geräten testen (iPhone Safari): HB-Untergeschosse nutzen Stencil-Maske – Handy-Speicher/FPS messen.
8. Vor öffentlichem Launch: Plakat-Freigabe, `noindex` in `web/public/_headers` entfernen. Quests erst nach Entscheid des Users.
9. **TODO Spawn (User 2026-10-18):** nur auf Strasse/Trottoir landen, nie in Flüssen, auf Gleisen o. Ä.; bevorzugt an einem guten Ort im Umkreis ~100 m um eine Landmark, Karte aber nicht darauf einschränken (`player/spawn.ts`).
10. **TODO Bus/Tram fahren (User 2026-10-18):** einsteigen wie beim Auto; Bus lenkbar, Tram nur Gas/Bremse und fährt automatisch auf seiner Linie.
11. **TODO Musik/Radio (User 2026-10-18):** Radio in Fahrzeugen mit Senderwechsel, Musik ausbauen (`audio_music.ts`, Idee 33 in `IDEAS_GAMEPLAY.md`); nur frei lizenzierte Musik (`research/music.md`).
12. **TODO Ni-Una-Menos-Platz (User 2026-10-18):** Helvetiaplatz im Spiel umbenennen (Platzname, Karte, Sprungpunkte, Texte). Prüfen, ob Haltestelle/Adressen weiter «Helvetiaplatz» heissen; offizielle Quelle der Stadt Zürich festhalten.

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

## Lochergut v4 (Agent, 2026-10-18)
Coop/Sockel/Platz: `pipeline/landmarks/lochergut_v2.py` (ersetzt k45_lochergut als Generator, reg=False), `pipeline/overrides/places_detail_lochergut.json`, Passerelle-Ausschluss `lochergut_excl.json`, Neon-Hook in landmarks3d.ts. Details und Fotolizenzen: `research/lochergut.md`; Vergleich `preview/lochergut_cmp.jpg`, Nacht `preview/lochergut_neon.jpg`. Offen: Farbfolge der Leuchtschrift unbelegt; GLB 25k Tris.

## Plätze-Details sq3 (Agent-Lauf 2026-10-18)
- Notizen und Fotobogen: `research/squares3/<platz>.md`, `preview/ref_sq3_<platz>.jpg` (Fotos aus research/v3, parks, squares2 wiederverwendet, je ≥12-37).
- Neu gebaut (Overrides `pipeline/overrides/places_detail_sq3_*.json`, Kacheln 5_0, 2_-4, 2_1, -3_-4): Limmatplatz (Tellerbrunnen + Bronze-Trinkbrunnen auf OGD-Positionen), Albisriederplatz (8 Hochbeete Tram-Insel), Josefwiese (Säulenbrunnen, 3 Tischtennis + Kicker aus OSM), Bäckeranlage (Betonbecken + Granit-Trog auf OGD-Brunnen; Formzuordnung geraten).
- Übrige Plätze (Helvetia, Röntgen, Bullinger, Linden, Brupbacher, Escher-Wyss) waren schon dicht ausgestattet; keine weiteren belegten Objekte gefunden. Ernst-Nobs-Platz: nicht in OSM gefunden. Kalkbreite-Hof: keine Hof-Fotos.

- Quartiergarten Hard (Bullingerstrasse 90, Kreis 4): Aussenansicht als Landmark `pipeline/landmarks/qgh.py` (+`qgh_plants.py`, Override `landmarks_qgh.json`, `yards_excl_qgh.json`/`tree_excl_qgh.json`, Filter `_apply_excl` in `yards.py`), Notizen/Lizenzen `research/quartiergarten_hard.md`, Fotos `preview/ref_qgh.jpg`, Vergleich `preview/qgh_cmp.jpg`. Kacheln t_-4_-1/t_-3_-1 müssen neu gebaut sein, damit Familiengarten-Hütten/Hecken im Garten verschwinden und das Chalet (ID_8D055786) versteckt wird.
