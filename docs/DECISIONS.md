# Entscheidungslog

Format: Nummer, Datum, Status (vorgeschlagen / bestätigt / ersetzt durch #N), Entscheid, Grund. Alte Einträge nie umschreiben.

## #1 – 2026-10-14 – bestätigt
Eigenes Unterprojekt `game/`, getrennt vom Reel. Daten und Skripte des Reels werden gelesen, aber nicht verändert.

## #2 – 2026-10-14 – vorgeschlagen
Stack: Three.js + TypeScript + Vite + Rapier; Pipeline in Python. Grund: gut für AI-getriebene Entwicklung, läuft im Browser auf dem Handy, Reel-Pipeline ist Python.

## #3 – 2026-10-14 – ersetzt durch #6
Hosting: Scalingo nur für die App, Kartenkacheln auf Object Storage mit CDN. Grund: Begrenzte Image-Grösse, schnelle Deploys, virale Last landet beim CDN.

## #4 – 2026-10-14 – bestätigt
Google Street View und Google Images nur zur Inspiration. Ist ein Laden nicht eindeutig dokumentiert: echter Name auf neutraler Fassade.

## #5 – 2026-10-14 – bestätigt
Gleiches Koordinatensystem wie das Reel (LV95-Ursprung 2681400/1248700, z0 = 408), damit Daten wiederverwendbar sind.

## #6 – 2026-10-14 – bestätigt (ersetzt #3)
Hosting auf Scalingo optimiert: Static-Buildpack (nginx), App und Kacheln zusammen per Archiv-Deploy (`scalingo deploy`), Build lokal. CDN/S3 erst als Stufe 2, umschaltbar über `TILE_BASE_URL`. Grund: Wunsch des Users, alles auf Scalingo; einfacher Betrieb, grosse Kacheln trotzdem nicht im Git.

## #7 – 2026-10-14 – bestätigt
Handy und PC sind gleichwertige Zielplattformen. Eingabe-Abstraktion (Tastatur/Maus, Touch, Gamepad), Grafikstufen low/medium/high mit Auto-Wahl, Tests in beiden Viewports.

## #8 – 2026-10-14 – bestätigt
Projekt liegt in `/Users/danielgnagi/sandboxzurich` (eigenes Repo, neben `../gta6`). Grund: Die lange Reel-CLAUDE.md wird nicht mehr bei jeder Anfrage mitgeladen (Token-Budget).

## #9 – 2026-10-14 – bestätigt
Lizenz WTFPL für Code und Doku, öffentliches Repo. Daten Dritter (OSM/ODbL, swisstopo, Stadt ZH) behalten ihre Lizenz; keine proprietären Fonts oder Logos im Repo.

## #10 – 2026-10-14 – vorgeschlagen
Karten-Durchstich mit den Reel-Daten (`../gta6/data`, read-only) statt neuer Downloads. Kacheln als eigene minimale glb-Dateien (Python-Writer `pipeline/glb.py`, eine Primitive pro Ebene, Vertexfarben, keine Texturen). Grund: schnell lauffähig, wenige Draw Calls (≈5 pro Kachel); Texturen/KTX2 und gltfpack kommen, wenn das Aussehen steht.

## #11 – 2026-10-14 – vorgeschlagen
Kollision vorerst 2D: Kreis gegen Gebäudegrundrisse (`web/src/player/collision.ts`), Höhe aus dem Raster in `world.json`. Rapier erst, wenn Physik gebraucht wird (Zerstörung, Fahrzeuge, M3). Grund: kein WASM-Download, reicht fürs Laufen.

## #12 – 2026-10-14 – bestätigt
Playwright-Skripte liegen in `web/tests/` (statt `tests/`), weil Node-Module nur von dort aufgelöst werden.

## #13 – 2026-10-14 – vorgeschlagen (ersetzt den Textur-Teil von #10)
Alle Kachelgeometrie nutzt ein gemeinsames Textur-Array (`DataArrayTexture`, 512² pro Ebene) mit Ebenen-Index pro Vertex und Einfärbung über eine Maske. So bleiben es 2 Draw Calls pro Kachel. Facade-Texturen stammen aus den prozeduralen Reel-Texturen; Ladenfronten ohne Text, echte Namen werden zur Laufzeit als Schilder gezeichnet. Die Fahrbahn liegt 12 cm tiefer als das Trottoir (Randsteine); für die Höhe der Spielfigur gibt es eine 1-m-Fahrbahnmaske pro Kachel.

## #14 – 2026-10-14 – vorgeschlagen
Freie Schriften (OFL: Anton, Barlow) liegen in `web/public/fonts`, nicht von Google ausgeliefert (kein Drittanbieter-Request). Pricedown nicht.

## #15 – 2026-10-14 – bestätigt (User: «optimiere von Anfang an, auch für Handys»)
Performance ist Teil jedes Schritts: Meshopt-Kompression der Kacheln, 1 Mesh für Stadtmobiliar pro Kachel, Instancing für Autos/Bäume, Entladen ferner Kacheln, automatische Qualitätsregelung, Handy-Messung mit gedrosselter CPU (`web/tests/perf.mjs`) nach jeder sichtbaren Änderung.

## #16 – 2026-10-15 – vorgeschlagen
Ton wird prozedural mit WebAudio erzeugt (keine Audiodateien, kein Download, keine Lizenzfragen). Echte Aufnahmen (Tramglocke, Durchsagen) später nur mit freier Lizenz.

## #17 – 2026-10-15 – vorgeschlagen
Spielzeit: 1 Spielminute = 1 Echtsekunde, 7-Tage-Kalender für wiederkehrende Anlässe. ÖV und Verkehr laufen in Echtzeit (sonst rasen sie). Fassaden-Quellen und Rohkacheln liegen in `data/build/`, nur gepackte Dateien in `web/public/`.

## #18 – 2026-10-15 – bestätigt (User: «vergrössere Map … Ende mit Baustelle versperrt»)
Spielgebiet = Kreis 4 + 5, Teile Kreis 9 (Hohl-/Badenerstrasse-Korridor, Lindenplatz, Bahnhof Altstetten) und Kreis 3 (Bahnhof Wiedikon, Schmiede Wiedikon): Polygon `data/build/playarea.json` (6.44 km², 202 Spielkacheln + 77 Kulissenkacheln). Rand = Bauzaun mit Kollision; dahinter Kulissenkacheln nur mit Gebäuden/Boden/Bäumen. Höhen pro Kachel (2 m, int16) statt globalem Raster; global nur 8-m-Raster. Build parallel (fork, alle Kerne), Testgebiet weiter per `SBZ_AREA=test`, einzelne Kacheln per `SBZ_TILES=ix_iy,…`.

## #19 – 2026-10-15 – bestätigt (User: «Platztafeln … real platziert und real aussehen wie Zürich-Schilder»)
Strassen- und Platzschilder: Alle Widmungstafeln (OGD-Punkte, 43 im Spielgebiet) stehen an ihrem vermessenen Ort, das blaue Namensschild darüber. Plätze/Anlagen aus dem Strassennamenverzeichnis bekommen bis 3 Schilder an der nächsten Fassade, ohne Fassade in Reichweite auf einem Pfosten (doppelseitig). Schildlänge folgt dem Namen. Rosa-Luxemburg-Platz zusätzlich als grosses freistehendes Schild mit roten Nelken (`pipeline/overrides/landmark_signs.json`). Code: `pipeline/plazasigns.py`, `web/src/world/streetsigns.ts`, `web/src/world/landmarks.ts`.

## #20 – 2026-10-15 – vorgeschlagen
Bodenbelag: Innenhöfe und Vorgärten nach Amtlicher Vermessung (Kanton ZH, bodenbedeckung_f): Grün → Rasen, befestigt → Hofbelag; Rest wie bisher. Fahrbahn bleibt vorerst OSM, weil die AV in der Innenstadt Trottoirs oft in «Strasse, Weg» einschliesst (Vergleich ausstehend, research/groundcover.md).

## #21 – 2026-10-15 – bestätigt (User: «Letzigrund fehlt … solche Sachen sollen nicht passieren», «Toni-Areal super realistisch»)
Landmarks als eigene GLB-Modelle (`pipeline/landmarks/`, `web/src/world/landmarks3d.ts`, Manifest `web/public/data/landmarks.json` aus `pipeline/overrides/landmarks_*.json`). Die ersetzten swissBUILDINGS3D-Gebäude werden über `hide`-Punkte im Build entfernt. Tram-/Bus-Wartehallen aus swissBUILDINGS3D (< 5 m hoch, an Haltestellen) werden verworfen; Wartehallen zeichnet `world/stops.ts`.

## #22 – 2026-10-15 – vorgeschlagen
Gebäudestand aktualisieren: swissBUILDINGS3D ist von 2019 (die Ausgabe 2026 gibt es nur als 14-GB-Gesamtdatei). `pipeline/osm_buildings.py` zieht Neubauten aus OSM hoch (IoU < 0.4 mit 2019 und GWR-Baujahr ≥ 2019 oder kaum überdeckt) und entfernt 2019-Gebäude darunter bzw. ohne OSM-Gegenstück (nur im Spielgebiet).

## #23 – 2026-10-15 – vorgeschlagen
Dachfarben aus dem Orthofoto SWISSIMAGE (swisstopo, offene Daten, WMS 0.5 m/px, `pipeline/ortho_roofs.py`): Median der helleren Hälfte der Dachpixel → Tönung einer neutralen Ziegel-Ebene `roof_tiles_grey` bzw. Kies. Orthofoto nur als Messquelle, nicht als Textur im Spiel.

## #24 – 2026-10-15 – bestätigt (User: Friedhof Sihlfeld mit Krematorium)
Spielgebiet um den Friedhof Sihlfeld + Verbindungsstreifen durch das Sihlfeld-Quartier erweitert (6.88 km², 219 Spielkacheln). Gelände-Korrekturen (Bahneinschnitt unter Gebäuden) in `pipeline/overrides/terrain_cuts.json`. Spielplätze aus OSM + Stadt-OGD (`pipeline/playgrounds.py`, `world/playgrounds.ts`).

## #25 – 2026-10-15 – bestätigt (User: «deaktiviere alle Quests», «Ladebildschirm ganz neutral, nur loading...»)
Quests/Missionen fest aus (`QUESTS = false` in main.ts, auch `?missions` wirkt nicht mehr); Code bleibt für später. Ladebildschirm neutral (nur «loading...»), kein Startbildschirm mehr; Ton startet bei der ersten Eingabe.

## #26 – 2026-10-15 – bestätigt (User: «keine Polizei, keine Meldungen wie Velo-Infrastruktur … geht erstmal um Map»)
Karten-Phase: `GAMEPLAY = false` in main.ts → keine Polizei (auch keine Polizeiautos im Verkehr), keine Sterne beim Velo-Klauen, keine Einblendungen (Easter Eggs, Anekdoten/Strassennamen, Velo-Infrastruktur, Ereignisse). Velos klauen/fahren, Velo-Tempo-Bonus und Karte bleiben. Code bleibt für später.

## #27 – 2026-10-15 – vorgeschlagen (Strassen v2)
Decal-UV war gespiegelt/verdreht: Alle Boden-Decals nutzen jetzt eine Zuordnung (Canvas oben = Fahrtrichtung, links = links der Fahrenden); das Velo-Piktogramm ist ein aufrechtes Seitenbild (gelbe Linien, Fahrer:in), Atlas 4×4. Neue Pfeile pro Spur (Kinds 7–10, `pipeline/streets_arrows.py`: OSM `turn:lanes`, sonst aus der Knoten-Topologie). Rote Fahrbahnflächen aus SWISSIMAGE (`streets_ortho.py`, nur innerhalb der Strassenfläche, Autos/Dächer gefiltert), Tramhaltestellen-Inseln mit Kante und Tastband aus OSM-Plattformen (`streets_islands.py`), Sperrflächen nur aus OSM `area:highway=traffic_island` (kaum Daten). Baustellen: `roadgraph.py` schneidet Auto-/Velospuren, die durch Gräben, Absperrungen, Zäune oder Bagger/Container führen (`sites.blocked_zones()`), Sackgassen werden bereinigt.

## #28 – 2026-10-15 – Karte als Vektordaten statt Raster; Spielzeit einstellbar
Stadtkarte und Radar zeichnen Vektordaten (`pipeline/mapdata.py` -> `data/map/vec.json`, 0.5-m-Quantisierung, Delta-Kodierung, 250-m-Zellen mit Path2D) statt des 2-m/px-Rasters (`map.webp` entfällt; ersetzt den Raster-Teil von #-Karte). Gründe: scharfe Gebäudegrundrisse bei jedem Zoom, Strassennamen und Beschriftung kollisionsfrei im Client, ähnliche Grösse (0.7 MB gz). Die Spielzeit liegt in `ui/clock.ts` (`GameClock`: Uhrzeit, Wochentag, Tempo 1/10/60×, Pause), Wahl in localStorage `sbz-clock`, URL-Parameter `?t=`/`?day=` haben Vorrang.

## #29 – 2026-10-15 – vorgeschlagen (User: «Laufen ist super unrealistisch»)
Menschen-Animationen aus echtem Motion Capture statt prozeduraler Sinus-Clips: CMU Graphics Lab Motion Capture Database (frei für jede Nutzung, BVH von cgspeed), Rohdaten `data/raw/mocap/`, Aufbereitung `pipeline/mocap/prep.py`, Retargeting auf das MPFB-Rig `pipeline/blender/mocap_retarget.py`. Zwei Gangarten-Sets, gemessene Clip-Geschwindigkeit pro Figur im Manifest (`clip_speed`), Überblenden idle/walk_slow/walk/run nach Tempo (humans.ts). Spielerin: Gehen 1.55, Rennen 4.5 m/s, begrenzte Drehgeschwindigkeit, Kurvenneigung beim Rennen. `stand_phone` bleibt prozedural. Details: research/humans.md (R6).

## #30 – 2026-10-15 – bestätigt (User: «Mach, dass man auch Autos klauen kann», «Auto und Velo müssen realistischer werden»)
Autos klauen und fahren: parkierte Autos (Registry `world/parkedcars.ts`, von `props.ts` befüllt) und Autos im Verkehr (`Traffic.findCar(…, take)`, Fahrer:in steigt aus und geht weg, keine Gewalt) mit E/Touch-Knopf E. Fahrphysik `player/drive.ts` (Gas/Bremse/Rückwärts, Lenkwinkel durch Grip begrenzt = Wenderadius wächst mit Tempo, seitlicher Schlupf, Federung/Neigung, 3 Kollisionskreise gegen `tiles.colliders` und Boxen gegen Verkehr/Trams/Parkierte, Boden per `groundAt` je Rad = Randsteine und Brücken). Modelle: `pipeline/cars/build_car.py -- <typ> drive` erzeugt `<typ>_drive.glb` (Karosserie ohne Räder, 4 Radknoten, Scheinwerfer/Rücklichter getrennt) für Raddrehung, Lenkeinschlag, Brems-/Rückfahr-/Blinklichter; Lack als Clearcoat mit prozeduraler Umgebung. Verkehr bekommt Lichter per Overlay (`world/trafficlights.ts`) und weicheres Anfahren/Bremsen (Ruckbegrenzung). Wanted-Sterne docken später an `CarUse.onTheft` an (main.ts: `onCarTheft`, nur bei GAMEPLAY). Schweizer Flottenmix und Lackanteile in `world/cars.ts`.
Velo: Fahrmodell und Neigung in `world/bikerig.ts` (leistungsbegrenzt, weiches Anfahren, geglättete Lenkung, Neigung aus Gierrate, Freilauf), Modell zur Laufzeit nach Position in Rahmen, 2 Räder und Kurbel zerlegt (Manifest `rig`). Fahrerin: `world/ridepose.ts` setzt Becken auf den Sattel, Hände an den Lenker, Beine per IK auf die echten Pedalpositionen; unabhängig von der Ruhepose des Skeletts (wichtig, da Mocap-Rig sich ändert).

## #31 – 2026-10-15 – bestätigt (Autos v3)
Autos v3: Karosserie weiterhin ein Loft (jetzt 8-Punkt-Querschnitt mit Schweller, Schulterkante, Tumblehome), Greenhouse mit dunkler Fensterkante, schwarzen B-Säulen, Scheiben bis zur A-Säule, Glasdach (Elektro-Limousine), Radläufe nur innen dunkel, Türfugen/Griffe als flache Quads, Kontrollschild (weiss, Ziffernblöcke, neutrales Wappenquadrat), Spiegel, Lampengehäuse, Stahl- oder 5-Speichen-Felgen. Neue Typen `csuv` (Kompakt-SUV) und `taxi` (Dachschild, eigenes GLB). ~2.6k Tris/Auto. `_paint` codiert die Oberfläche (1 Lack, 0.3 Glas, 0.15 Chrom/Alu, 0 matt): `carMaterial` (Lambert, instanziert) addiert eine billige Himmel/Boden-Spiegelung mit Fresnel (Uniform `carDay`, Nacht dunkler); das gefahrene Auto teilt die Geometrie nach Oberfläche in Lack (MeshPhysical, Clearcoat), Glas, Chrom, matt. Fussgänger:innen weichen dem gefahrenen Auto seitlich aus (`Pedestrians.dodge`, nie Verletzung); Bremslicht auch beim Ausrollen (+0.3 s Halten). Testbogen: `web/tests/cars_sheet.mjs` -> `preview/cars_v3.jpg`.

## #32 – 2026-10-15 – Fassaden v3 (neutrale Putzebenen, exakte Farbe)
Neue Textur-Ebenen `g3_*`, `e3_*`, `n3_*`, `k3_*` (`gen_facades3.py`, 25 Stück, hinten an den Atlas angehängt, eigener Normalmap-Bereich `normals3`, `facades3` in `layers.json`). Wand = helles Neutral mit Maske 255, Vertex-Tint wird per `styles.exact_tint()` aus dem gemessenen Basis-Mittel (`data/build/facades/base_means.json`) und Shader-Gain 1.35 berechnet, damit die beobachtete Farbe getroffen wird. Läden-Farbe = eigene Ebene (grün/grau/braun/blau). Klinker/Sandstein als tintbare Ebenen. 3D: Dachgesims und Erker (`facade_trim.py`, nur v3-Altbauten). Notizen `visual_notes_v3.json` (Mapillary, von Hand gelesen) schlagen v1/v2; v2-Freitext wird per `parse_text` auf die v3-Felder abgebildet. Fix «graues Fensterraster»: `neubau_b` war feste graue Platte (Maske 0) und wurde bei jedem dritten Neubau gewählt; jetzt tintbar und seltener. Nebenbei: `shops2` in `layers.json` schloss `roof_tiles_grey` ein und liess Dächer nachts leuchten; korrigiert.

## #33 Rendering v3: PBR + IBL nur am PC (2026-10-15)
Tile-Material am PC = MeshStandardMaterial (Rauheit pro Layer: Asphalt 0.93 und 30 % dunkler, Fassade 0.82, Glas 0.16 + metalness 0.4), `scene.environment` = PMREM (64 px) aus dem Himmel (`engine/env.ts`, Neuaufbau alle 12 Spielminuten, Intensität je Tageszeit), Hemisphärenlicht auf Tiles auf 0.4 skaliert (`hemiK`). Handy bleibt Lambert ohne IBL. Autos: Fake-Reflexion nutzt jetzt die Live-Himmelsfarben. Nachtfenster: nur neutrale/blaue dunkle Texel gelten als Glas (dunkle Backsteinwand leuchtete als beige Block), nur Fensteröffnung, warm und ~3x schwächer. SMAA nicht nötig: PC-Target hat MSAA x4.

## #34 – 2026-10-15 – Landmarks Kreis 9/3 v3 (User: «Details wie auf Fotos»)
Die k93-Landmarks sind aus Fotos/Recherche (`research/v3/*.md`) detailliert nachgebaut: `pipeline/landmarks/k93_kit.py` (prozedurale Texturen: Fenster mit Laibung/Sprossen/Sims, Stein, Putz, Ziegel, Schiefer, Holzlamellen, Beton; Schrift mit freien Fonts aus `web/public/fonts`; Uhren; Wandbänder mit echtem Achsabstand, Walm-/Satteldächer mit Ziegel-UV). Nachtlicht über `emissiveTexture` (Mat.emis in `k93_lib.py`; `landmarks3d.ts` skaliert sie mit dem Nachtfaktor). Keine Fotos als Textur. Friedhof-Grabfelder (`k93_graves.py`): ca. 7000 Grabsteine + Hecken als eine zusammengefasste Geometrie (1.1 MB), Flächen = OSM-Friedhof ∩ AV-Grün minus Wege/Gebäude/Bäume. Weil `osm_buildings.update` die OSM-Grundrisse versteckter Landmarks wieder hochzieht, filtert `build_testarea.py` die `hide`-Punkte nach dem Update erneut; `k93_all.py` ergänzt OSM-Hide-Punkte automatisch (plus `OSM_HIDE` für Stadion/Krematorium). Temporäre Hilfen: `web/lmview.html` + `pipeline/landmarks/view.mjs` (Modell allein), `free_shot.mjs` (freie Kamera im Spiel).

## #35 – 2026-10-15 – Plätze/Parks v3: eigene Detailstufe `places_detail` (User: «Röntgenplatz etc. viel realistischer»)
- Neue Pipeline-Stufe `pipeline/places_detail.py` + Override-Dateien `pipeline/overrides/places_detail*.json` (pro Platz: Koordinaten relativ zum Zentrum, Quelle im Feld `src`). Hooks: `ground()` in `build_testarea._ground_tile`, `tile_meta()` → `meta["places"]` (Objekte, Linien, Dachplatten, Sitzplätze für Leute), Kollider.
- Boden: `ortho_ground` klassiert SWISSIMAGE (0.5 m/px, `streets_ortho._mosaic`) in Rasen/Kies/Belag innerhalb einer Zone (Strassen ausgenommen); explizite Flächen (`ground`: rect/poly/pxpoly/circle/line/osm/grid/rings/dots) liegen darüber. Lifts 3–11 cm, weil `drape()` das Terrain nur an Zellecken abtastet (dünnere Lagen z-fighten am Hang); explizite Flächen werden aus den Ortho-Flächen ausgeschnitten.
- `convert`: OGD-Möblierung (Masten, Brunnen, Bänke, Kübel) in einer Zone wird durch den Platz-Typ ersetzt (Bogenmasten, Pilzleuchten, Kugelleuchten, Hundebrunnen …). `scatter` streut Objekte auf einem Raster (Gartentische, Stände).
- Laufzeit `web/src/world/places_detail.ts`: ein gemergtes Vertexcolor-Mesh pro Kachel (1 Draw Call, keine Texturen), ~45 Objekttypen.
- Platzmittelpunkte: OSM/Fotos statt `places_v3.json` (dessen lat/lon liegen bei Escher-Wyss/Idaplatz/Kaserne/Limmatplatz bis 350 m daneben). Neue Zentren in `data/raw/ortho_places/centers.json`.
- Hilfen: `places_detail.py sheet <id> <Fenster_m>` (Ortho + OGD + Fotopositionen + Raster, zum Abmessen), `web/tests/plaza.mjs` + `plaza_sheet.py` (Foto ↔ Spiel), `plaza_top.py` (Ortho ↔ Spiel von oben).

## #36 – 2026-10-15 – Menschen v4: Animationsbibliothek, Situations-Clips, Laufzeit-Kleidung (User: «bessere Bewegung, Details wie auf Fotos»)
Zusätzliche CMU-Takes (frei, Quelle wie #29) als gemeinsame Bibliothek `web/public/models/humans/anims_<A|B>_<young|old>.glb` (4 Dateien à ca. 0.4 MB, nur Rig + Clips) statt in jedem NPC-GLB: `pipeline/blender/animlib_clips.py` via `build_animlib.sh`. Laufzeit hängt die Clips an jede Figur der Klasse (Becken-Translation mit Körpergrösse skaliert), Actions werden lazy erzeugt (`Human.ensure`). Clip-Familien (`FAMILY` in humans.ts): idle (Gewicht verlagern, Umschauen, Arme verschränkt, Hände in Taschen), wait, talk/listen/argue, text/call (Handy-Fit je Clip), sit/sit_talk/sit_chat (Mocap statt prozeduraler Sitzpose). Pedspots/Lawns/Haltestellen wählen Clips je Situation, Phase zufällig. Kleidung: `world/tint.ts` färbt Jacke/Hose/Schuhe per Shader um (Zonen aus Bone-Weights und Höhe, Luma-erhaltend, Material pro Person geklont), plus Schal. Details und Takes: research/humans.md R7.


## #37 – 2026-10-16 – vorgeschlagen (Nachtlauf, Hauptsession)
Nachtlicht ohne echte PointLights: die nächsten Laternen/Läden (PC 20, Handy 10) und Autoscheinwerfer (PC 8, Handy 4) als Uniform-Arrays im Welt-Material (`world/night_lights.ts`), Stärke ×0.6 (sonst überstrahlte Trottoirs). Download: Handy lädt `atlas_n_half.webp` (0.7 statt 3.7 MB) und nur eine Baum-Variante pro Art; weitere NPC-Modelle erst 8 s nach dem Start. Build: 1 BLAS-Thread pro Worker. Besichtigungsschlangen-Szenen nur um die Zeit auf ihrem Schild.

## #38 – 2026-10-16 – Crash-Physik und Fahrzeugschaden (User: «Man soll crashen können, Auto geht irgendwann kaputt»)
`player/drive.ts`: Bewegung in Scheiben von höchstens 0.2 m (kein Tunneln), zwei Kreisspalten über die ganze Karosseriebreite, Kontaktpunkt/Normale je Treffer, Drehimpuls (`yawKick`) bei Treffer am Eck, Reibung entlang der Wand, `damage` 0..1 (`0.012*(Aufprall-2)^1.25`), ab 50 % schwächerer Motor, bei 1 `dead` (nur Bremse wirkt). Optik: `Rig.dent` (Vertex-Verschiebung), `setDamage` (Scheiben milchig, Scheinwerfer aus), Rauch ab 50 %/85 % und Funken (`crash_fx.ts`, Sprite-Pool, kein Feuer). Getroffene Verkehrs-/Parkautos (`Obb.id`/`Obb.ref`) werden über `Traffic.findCar(…, take)` bzw. `parkedCars.take` aus dem Bestand genommen und als `Wreck` (`crash_wreck.ts`) weggeschoben; Fahrer:in steigt aus und schimpft (Sprechblase), nie Verletzte. Beschädigte Autos bleiben als Wreck stehen (>160 m weg: entfernt). Velo: Aufprall >5.5 m/s = Sturz (`Player.fallT`, `onBikeCrash`). Keine Änderung an traffic.ts.


## #39 – 2026-10-16 – Perron-Ebene der Bahnhöfe als eigene Landmark-GLBs (Agent Bahnhöfe)
Perrons, Möblierung, Dächer und Zugänge von Hardbrücke, Altstetten und Wiedikon liegen in `stp_<id>.glb` (`pipeline/landmarks/st_station.py`, Manifest `overrides/landmarks_stations.json`), getrennt vom Aufnahmegebäude-Modell und von `railways.py` (Gleise, Perronplatten aus OSM). Geometrie aus amtlichen Perronkanten (SBB BehiG, Länge/Position) + OSM-Gleisen (Kante = Gleis ∓ 1.67 m, 55 cm über Schienenkopf); Altstetten 3/4 und 6/7 fehlen in OSM und werden im GLB als Platte gebaut (`research/stations/platforms.json`, `in_osm=false`; `railways.py` darf sie nicht doppelt bauen). Begehbarkeit ohne Kachel-Neubau: `web/public/data/station_decks.json` (DeckRows wie Brücken) wird in `engine/tiles.ts` in den `BridgeIndex` geladen.

## #40 – 2026-10-16 – Zürich Hauptbahnhof: Spielgebiet erweitert, begehbare Halle, Perronhalle als Landmark-GLBs (User: «HB stimmt nicht, Innenraum bauen, Gleise ergeben keinen Sinn»)
- **Lage:** Der HB-Kopf (Haupthalle, Querhalle, Bahnhofplatz) lag 183 m östlich der alten Kante (x ≈ 1693). `pipeline/overrides/playarea_extra.json` (orientierte Rechtecke, Winkel -21° = Gleisrichtung) wird in `pipeline/playarea.py` vereinigt: +0.05 km², neue Spielkacheln `t_9_-4`, `t_9_-3`, neue Kulissenkacheln `t_9_-6`, `t_9_-5`, `t_10_-5`, `t_10_-4`, `t_10_-3`; der Bauzaun rückt an die neue Kante.
- **Modelle** (`pipeline/landmarks/hb_*.py`, Einträge `overrides/landmarks_hb.json`): `Zürich Hauptbahnhof` (Aussenhülle, Wannerhalle 133 × 42 m mit 7 Oberlichtfirsten, Süd-/Nordtrakt, Querhalle, Fassade mit Triumphbogen-Portal), `… + Innenraum` (begehbar, `load_r` 260 m, wird bei > 380 m wieder entladen), `… + Perrons` (Perrons 3–18 auf 425 m, Längshallen, `load_r` 480 m). Masse aus OSM-`building:part` und swissBUILDINGS3D-Dachhöhen, Formen aus Commons-Fotos (`research/hb/`), alle Texturen prozedural, keine Logos, keine SBB-Uhr (neutrale Zifferblätter).
- **Pipeline-Erweiterungen:** Landmark-Einträge dürfen `hide_ids` (swissBUILDINGS3D-/OSM-IDs; nötig für Dachflächen-Gebäude ohne Grundriss), `walkable` (die Footprints der versteckten Gebäude werden *nicht* mehr Collider) und `colliders` (Wandringe in lokalen Metern, in jede berührte Kachel übernommen) haben (`build_testarea.py`); `load_r` pro Eintrag in `landmarks3d.ts` (nur nah laden, fern entladen); `terrain_cuts.json` kennt jetzt `poly` + `z` (ebene Fläche, beidseitig) für den Hallenboden; `merge.py` entfernt `colliders`/`hide_ids` aus dem Laufzeit-Manifest.
- **Perrons und Gleise:** Perronoberkante = Schienenkopf + 0.55 m (wie `railways.py`, +3 cm gegen Z-Fighting); Begehbarkeit der erhöhten Perrons per DeckRows `web/public/data/hb_decks.json` (wie `station_decks.json`, Laden in `engine/tiles.ts`), am Kopf 8 Stufen hinunter auf den Querhallenboden (= Terrain, geebnet auf -2.9 m). Gleise/Schotter/Fahrleitung bleiben in `railways.py`; **`railways.py` darf die HB-Perrons nicht doppelt bauen** (OSM-Way 107555897 = Perron 3 und die Relationen 4–18 liegen im Bereich der GLBs).
- **Budget:** Nahstufe 17.5k (Hülle) + 14.4k (Innen) + 18.8k (Perrons) = 50.7k Dreiecke, ≤ 3 Materialien je GLB, Texturen 1024 × 576 (Innen) und 512 × 384 (Perrons) inkl. Emissive, Hülle nur 512 × 128 + 128².

## #41 – 2026-10-16 – NPC-Verkehr nur auf erlaubter Fläche, Testnetz `traffic_legal` (Agent Verkehrsregeln, User: «cars only drive where they're allowed to»)
- Messung: `web/tests/traffic_legal.mjs` simuliert 2 Min Spielzeit an 11 Orten und prüft Auto-Positionen gegen ein Raster (`pipeline/traffic_zones.py` → `web/tests/fixtures/traffic_zones.png`, 1 m: Fahrbahn, Brücke/Tunnel legal; Platz, Fussgängerzone, Park, Gebäude, Gleiskörper illegal). Vorher 2.4 % illegal, Ziel < 0.5 %.
- Ursache: `living_street` wird im Spiel als Platzboden (streets.PLAZA) gezeichnet, roadgraph liess dort aber Autos fahren (Eisgasse/Europaallee, Malojaweg). Jetzt keine Autokanten auf `living_street`; zudem keine Autokanten ausserhalb des gezeichneten Gebiets (AREA + 39 m).
- Parkierte Autos: `cityprops.street_parking()` lässt OGD-Parkplätze nur zu, wenn sie nicht auf Platz/Fussgängerzone/Park/Gleiskörper liegen und höchstens 4.5 m neben der Fahrbahn einer Fahrstrasse (kein service). `pipeline/park_filter.py` wendet das auf gebaute Kacheln an (ohne Komplett-Build); `build_testarea.py` tut es künftig selbst.
- OSM enthält keine restriction-Relationen (kein Abbiegeverbot-Daten); oneway/oneway:bus/Zugang wurden bereits korrekt behandelt. Tunnel (Langstrasse-Unterführung) hat keine Autokanten (Strassenpolygon fehlt), Busse fahren darin.

## #42 – 2026-10-16 – Langstrassen-Unterführung und Ole Ole Bar (Agent Unterführung, User: «man soll unten durch gehen können, links und rechts hat es einen kleinen Durchgang»)
- Gelände: neuer Eintragstyp `profile` in `pipeline/overrides/terrain_cuts.json` (Achse, Längsprofil, Halbbreite, Blend, `mode` min/set) mit `lock: true`. `terrain_cuts.apply(H, lock_only=True)` läuft in `build_testarea.py` nach `road_height.apply`, damit die Strassenglättung den Einschnitt nicht anhebt (Glättung überspringt Tunnelways, ihre Kappe an den Portalen würde sonst ca. 9 m in den Tunnel reichen).
- Bauwerk als Landmark `lu_unterfuehrung` (`pipeline/landmarks/lu_*.py`, Masse in `lu_geom.py`, Eintrag in `landmarks_lu.json`, Felder `walkable` und `colliders` = Wandringe in 20-m-Stücken). Gleise liegen weiter auf der Roh-DTM-Höhe (railways.py liest `terrain.heights` ohne Cuts) = Deck; `research/v3/langstr_unterf_deck.json` dokumentiert Polygon und Deckhöhe.
- Ole Ole Bar als Landmark `lu_oleole` (ersetzt Gebäude `ID_96E308DB`).
- Offen: NPC-Verkehr und Trolleybus durch den Tunnel (roadgraph/transit überspringen Tunnelways), Beleuchtung im Tunnel nur gebacken (Vertexfarben) plus Nacht-Emissive.

## #43 – 2026-10-16 – Wasser: Sihl, Limmat, Kanäle (Agent Wasser)
- Vorher zeichnete der Build die AV-Klasse «water» als Hof/Rasen auf DTM-Höhe (Flussbett = grüner Graben). Neu `pipeline/water.py` (Hook in `build_testarea.py`, markiert «water»): Wasserpolygon (AV + OSM natural=water, Brückenlücken über `bridges.exclusion` geschlossen) wird aus Boden/Strassen abgezogen; Wasserspiegel = geglättetes DTM im Wasser, höchstens (tiefste Uferhöhe − 0.6 m); Bett 0.9 m darunter (nur ≥ 3 m vom Ufer in `H` abgesenkt, terrain-API unverändert); Ufermauern aus DTM-Differenz (Beton Sihl, Naturstein-Granit Limmat, `overrides/water.json`); Badestellen (OSM «Flussbad …») = flache Zone mit Rampe, ohne Collider; sonst Wasserpolygon (ohne Brückendecks) als Collider.
- Laufzeit `web/src/world/water.ts`: ein Shader, Daten pro Kachel als 4-m-RGBA-Textur im Meta (Uferdistanz, Fliessrichtung, Pfeilerschaum), Flow-Map-Wellen, Fresnel-Himmel (analytisch aus Himmelsfarben, kein PMREM), Sonnenglitzer, Schaum, Nacht-Lichtreflexe der Laternen. Handy: 2 statt 3 Oktaven. Wasser-Mesh als eigener glb-Knoten mit benanntem Material «water» (sonst fasst gltfpack alles zu einem Mesh zusammen; `glb.py` ergänzt).
- Fliessrichtung: OSM-Way (Sihl), sonst `flow_ref` (Limmat nach NW). Offen: Geländer auf Mauern, Treppen-Geometrie, Wehr-Schaum, Kiesbänke. Komplett-Build nötig (Wasser in allen Kacheln).

## #44 – 2026-10-16 – Strassenhöhe geglättet, Fahrbahnpolygon bereinigt (Agent Strassen, User: «Strassen eckig, hügelig, gehen plötzlich runter»)
- Messung: `pipeline/roads_audit.py` (Achsen im Spielgebiet, 1 m-Schritte; Steigung > 8 %, Sprung > 0.25 m, 2. Differenz, Polygonspitzen, Lücken) → `research/roads_audit.md`. Vorher: 325 Höhenstellen auf 84 km (3.9/km), 1077 Polygonecken < 50 Grad; nachher 32 (0.4/km), ~21 Ecken. Rest sind echte Unterführungen (Bullinger-, Hohl-, Stauffacherstrasse).
- Höhe: neues Modul `pipeline/road_height.py`. Pro Strassenachse Längsprofil (Median 9 + Mittel 21 m, Steigung ≤ 15 %, höchstens ±1 m vom echten Gelände, Knoten mit > 1 m Höhendifferenz gelten als verschiedene Ebenen und werden nicht angeglichen, sonst Kreuzungen auf gemeinsame Höhe, Radius 18 m). Ins Raster H geschrieben (Fahrbahn + 2.5 m Blendband = Trottoir), überlappende Strassen distanzgewichtet gemittelt (kein «nearest wins», sonst Flickenteppich). H wird in `build_testarea.py` direkt nach `terrain_cuts` verändert (`S = streets.parse` dafür nach vorne gezogen), darum folgen Fahrbahn, Randstein, Trottoir, hmap (Lauf-/Fahrhöhe) und Brücken-Rampen automatisch. Schalter `SBZ_NO_ROADH=1` für A/B-Tests.
- Querwölbung nur 0.5 % (statt 2 %): das Fahrbahnmesh hat nur Randvertices, eine echte Wölbung würde die Laufhöhe über dem Asphalt schweben lassen.
- Form: `streets.tidy_roads()` – runde Caps, Schlitze < 1.6 m geschlossen, Eckausrundung r = 4 m (nur kompakte Füllungen < 45 m2, damit Inseln/Trottoirs nicht zugehen), Spitzen < 0.6 m weg.
- Brücken: Strassen, die UNTER einem Deck durchführen, behalten ihren Asphalt (`road_height.ground_exclusion`); nur die eigene Brückenkette wird ausgeschnitten (`road_height.clip_ways`). Behebt Lücken unter Bahnviadukten (Hohl-, Zwei-, Kanzleistrasse).
- Nicht gelöst: Brückendeck-Höhen im Spiel sind gestuft (Deck-Index liefert Treppenstufen von 0.25–0.7 m, siehe `BridgeIndex.heightAt`), das holpert beim Befahren von Rampen.

## #45 – 2026-10-16 – Fahrbahn aus der Amtlichen Vermessung statt OSM-Buffer (Agent Fahrbahn-Abgleich, User: «Fahrbahn Abgleich mit Satelliten»; schliesst #20 «Fahrbahn aus AV offen»)
- Messung: `pipeline/carriageway_audit.py` → `research/carriageway_audit.md`, `preview/carriageway_audit.jpg`. Ergebnis: OSM-Standardbreiten sind im ganzen Spielgebiet im Mittel 1.05 m zu schmal (nur im Testgebiet der Innenstadt zu breit, siehe `research/groundcover.md`): `lanes=1` ergibt 3.2 m, wo die AV 9–12 m Fahrbahn hat (z. B. Badenerstrasse). IoU Fahrbahn vs AV-Fahrbahn 0.72 → 0.91, Breitenfehler (dort, wo die AV Trottoir trennt) Median −1.05 m → 0.00 m, p90 6.4 m → 0.25 m.
- Neu `pipeline/carriageway.py` (aufgerufen aus `streets.parse`): Querschnitte alle 4 m senkrecht zur OSM-Achse messen den Abstand zu den AV-Fahrbahnkanten. Kante «vertrauenswürdig», wenn dahinter Trottoir/Veloweg/Grün/Bahn liegt (AV trennt dort); sonst (Trottoir in «Strasse, Weg» enthalten) wird die Breite auf den Median getrennter Strassen derselben Klasse (hw, oneway, lanes) begrenzt. Fahrbahn = AV ∩ Kappe aus den Querschnitten + Knotenscheiben; wo die AV keine Fahrbahn hat (40 von 2445 Wegen): kalibrierter OSM-Streifen. Schmale «Bahngebiet»-Streifen (< 9 m, Tramgleise in der Strasse) zählen zur Fahrbahn. Parallele Nachbarwege (Richtungsfahrbahnen als zwei Einbahn-Ways) teilen sich die AV-Fläche je zur Hälfte.
- Pro Way: `w["w"]` = gemessene Breite, `w["off"]` = seitlicher Versatz der Fahrbahnmitte zur OSM-Achse (+ = links). Markierungen, Velostreifen, Zebrastreifen, Parkplätze/Kanaldeckel/Piktogramme (`streets.mline`) sowie NPC-Spuren und Velo-Spuren in `roadgraph.py` richten sich nach der Fahrbahnmitte, nicht nach der Achse. Achsen selbst bleiben (Knoten-Konnektivität, Tramgleise, Strassenhöhe `road_height`).
- Verkehrsinseln/Mittelinseln: ergeben sich als Löcher der AV-Fahrbahn (Trottoir/«Verkehrsinsel befestigt» liegt daneben); grüne Inseln und Rasenstreifen: `_ground_base` zieht AV-Grün vom Trottoirband ab (Trottoir ist in der AV nie grün).
- Schalter: `SBZ_CARRIAGEWAY=osm|av`, Default in `carriageway.DEFAULT`. Laufzeit der Strassen-Prep steigt (Fahrbahn-Union grösser), Kachelzahl/-grösse unverändert.
- Grenzen: Orthofoto-Helligkeit trennt Asphalt und Trottoir nicht (beide ~87/255), die Orthofoto-Kontrolle ist deshalb visuell (`preview/carriageway_cmp*.jpg`); Trottoirbreite ergibt sich aus AV-Fahrbahnkante bis 6 m, AV-Trottoir wird nicht separat gezeichnet.

## #46 – 2026-10-16 – Langstrasse: Markierung aus SWISSIMAGE und Fassaden/Läden nach Fotos (Agent langA, User: «Die Langstrasse muss richtig nice werden»)
- Markierung: `pipeline/markings_ortho.py` misst Gelbmarkierungen (Zebra, Linien) aus SWISSIMAGE-WMS 0.1 m/px entlang der ganzen Langstrasse, `markings_synth.py` zieht im Nordteil die durchgehenden gelben Randlinien (±2.95 m, ~0.3 m breit, vor Querstrassen unterbrochen) und setzt Bodenzahl «30»/Velopiktogramme. Ergebnis `overrides/markings_langstrasse.json`, angewendet über `pipeline/markings_override.py` (zwei markierte Hooks in `build_testarea.py`: `apply` nach `streets.markings`, `decals` bei props). Gemessenes wird zu den gebauten Markierungen addiert (OSM-Zebra bleiben), Handkorrekturen über `add_white/add_yellow/cut`.
- Grenzen: Gelbmaske verfehlt Schattenzonen (v.a. Südteil); Weiss wird nicht gemessen.
- Fassaden/Läden: 35 Häuser in `research/buildings/notes_raw_langA_001.tsv`, 12 Ladenfronten in `shops_v3.json`, 8 Landmark-Häuser `pipeline/landmarks/langA_houses.py`. Fotos sind meist Schrägansichten (Velo-/Auto-Kameras), Farben geschätzt. Details `research/langstrasse_A.md`.

## #47 – 2026-10-16 – HB-Umfeld und Perron-Ausstattung als eigene Landmark-GLBs (Agent HBX)
`pipeline/landmarks/hbx_all.py` erzeugt `hbx_perron.glb` (Sektortafeln A-F, neutrale Anzeigen, Billettautomaten, Kübel) und `hbx_platz.glb` (Alfred-Escher-Brunnen, Velostand am Südtrakt), Manifest `overrides/landmarks_hbx.json`. Getrennt von `hb_*` (Innenraum-Agent). Details und offene Punkte: `research/hb/hbx.md`.

## #48 – 2026-10-16 – HB v3: begehbare Untergeschosse (Shopville, Museumstrasse 41-44, Löwenstrasse 31-34) (User: «Hauptbahnhof richtig realistisch, mit Mehr-Geschoss-Plan»; ergänzt #40)
- **Modell:** `hb3_under.glb` (`pipeline/landmarks/hb3_under.py`, Masse in `hb3_spec.py`, Eintrag `overrides/landmarks_hb3.json`, `load_r` 250, wird fern entladen): Shopville-Gang (-5.3 m) mit Läden und Leuchtsäulen, Zugangstreppen aus der Querhalle (S1) und vom Bahnhofplatz (S2), Treppen zu Museumstrasse (-10.5 m) und Löwenstrasse (-16 m), je 2 Inselperrons und 4 Gleise. 3.1k Dreiecke, 70 kB. Lage/Länge schematisch (Ebenen aus OSM-`level`, SBB-Plan nur angesehen), siehe `research/hb/v3.md`. Bestehende HB-Modelle bleiben (Untergeschosse sind additiv); `hb_inner` hat ein Loch im Querhallenboden für S1.
- **Begehbarkeit:** Decks unter dem Terrain (`sub: true`, `web/public/data/hb3_decks.json`; Treppen = geneigte Decks). Hooks `// hb3`: `BridgeIndex.lastSub` + `Tiles.groundAt` (Terrain gewinnt nicht gegen Untergrund-Decks), `railPush` (Tunnelwände immer, nur für Körper auf dem Deck), Spielerkamera zwischen Boden und Decke. **Keine Treppe mit flachem Anfangssegment** (der Endkappenradius eines flachen Decks hält den Spieler sonst oben fest).
- **Terrain öffnen ohne Neubau:** Stencil-Maske. Material `hb3_mask` schreibt Stencil 1 (ohne Farbe/Tiefe), das gemeinsame Kachelmaterial (`materials.ts`) zeichnet nur, wo Stencil ≠ 1. Reihenfolge: Himmel -1, Untergeschoss -0.5, Maske -0.4, Kacheln 0. Renderer und Post-Target haben dafür einen Stencil-Puffer. Offene Schächte nur an S1/S2 (die Maske verdeckt auch Kachelgeometrie hinter dem Schacht, bei flachem Blick auf die Plätze unkritisch).
- **Grenzen:** keine Collider-Ringe (sie wirken auf allen Ebenen und brauchen Kachel-Neubau); Schachtränder halten den Spieler an der Oberfläche nur optisch (Brüstung). Rolltreppen, Lifte, Ausgänge Europaallee/Sihlquai nicht modelliert. Ladenschriften bewusst keine (neutral).

## #49 – 2026-10-18 – HB-Qualitätsreview: Perron-OSM-Dachplatte, Props, Innenfarben (ergänzt #40/#47/#48)
Ursachen und Liste: `research/hb/review.md`, Bögen `preview/hb_review_before.jpg` / `_after.jpg`. (1) `railways.py` baut aus OSM-Perrondächern eine Platte auf Perron + 3.6 m: sie verdeckte die Landmark-Gewölbe von innen (graue Decke). Jetzt übersprungen, wenn der Punkt in `research/hb/prop_excl.json` liegt (erzeugt von `pipeline/landmarks/hb_propexcl.py`; Rail-Kacheln neu mit `pipeline/railways.py`). (2) Gleiche Polygone filtern in `cityprops.py` Bäume/Laternen/Bänke in Hallen und auf Perrons. (3) `hb_kit.hxw()` tönt Böden/Perronbeläge/Hallendecken warm vor (Innenräume werden nur von der blauen Himmels-IBL beleuchtet). hb3-Untergeschosse bleiben an (an der Oberfläche keine Löcher/Z-Fighting). Offen: Bauzaun c=-100 vor dem Escher-Brunnen (playarea_extra), schwebende Quader am Ostgiebel, Canvas-`arc`-Fehler.

## #50 – 2026-10-18 – Stadion Letzigrund neu: Cor-Ten-Wand statt Glashülle (ersetzt k93_stadion)
Ursache «aussen zu hoch»: Das alte Modell hatte eine 23 m hohe Fassade samt Glasband. Echt: Feld ~8 m unter Strassenniveau (swissALTI3D), Aussenwand aus Cor-Ten nur ~4.6 m über Strasse, darüber offenes dunkles Band, Dachkante ~15 m über Strasse (swissBUILDINGS3D), schlanke schräge Stützen. Neu: `pipeline/landmarks/letzigrund.py` (+ `letzigrund_all.py`: gltfpack, `landmarks_letzigrund.json`, Hide-Punkte aus `overrides/letzigrund_hide.json`), `k93_stadion.py` bleibt nur als Archiv und ist aus `k93_all.py` entfernt. Dachoberseite doppelseitig. Wandhöhe pro Strahl aus dem Terrain. Sitze rot mit weissen Diagonalen im Oberrang (eine Streifen-Textur, ~23k Tris, 790 kB). Bäume: nDSM las das alte Dach als Krone; Ausschlusszone `overrides/tree_excl_letzigrund.json` (Muster `tree_excl_*.json`, gelesen in `yards.py`). Nicht begehbar (Footprint solid), kein Durchfallen.

## #51 – 2026-10-19 – Längslinien als Ketten mit eingepassten Strichen (Auftrag L)
Mittel-/Spur-/Velolinien kommen aus `pipeline/markings_lines.py` (Ketten über Way-Grenzen, geglättet, Striche pro freiem Intervall eingepasst) statt je OSM-Way; Markierung wird mit Asphalt-Raster (`ROAD_CELL`) und 3 cm Höhe (`SBZ_LINE_LIFT`) gezeichnet. Details, Zahlen: `research/lines.md`, Audit `pipeline/audit_lines.py`.

## #52 – 2026-10-19 – Objekt-Katalog: echte Varianten statt Einheitsmodell
Brunnen, Haltestellen-Ausstattung, Plakatstellen und Kioske kommen aus einem Katalog (`pipeline/catalog/`, 21+ GLBs mit einem gemeinsamen Atlas, `web/public/models/catalog/`). Zuordnung per Datenattribut (WVZ-Brunnen `material_*`, `art`, `brunnenart`; VBZ `stops_equip`), Foto-Overrides in `pipeline/overrides/catalog_assign.json`, Ergebnis `web/public/data/catalog.json`, Laufzeit `web/src/world/catalog.ts` (InstancedMesh je Variante, A/B `?nocatalog`). Kein Kachel-Build nötig. Leuchten bewusst nicht ersetzt (kein Typ in den ewz-Daten).

## #53 – 2026-10-19 – Zonen und Bestandsaufnahme als Massstab
Spielgebiet in 5 Zonen (`pipeline/zones.py` → `pipeline/overrides/zones.json`, Zone 2 endet an der Limmat). Fortschritt wird pro Zone gegen Fotos an festen Kamerapunkten benotet (1–5; Bestandsaufnahme Ø 2.5, `research/zones/baseline.md`). Arbeit pro Nacht = eine Zone (`docs/NIGHT_PLAN.md`).

## #54 – 2026-10-19 – Tramgleise Teil der Fahrbahn
Gleiskorridore im Strassenraum werden in die Fahrbahn gemergt (`pipeline/tram_track.py`), Rillenschiene bündig (+1.2 cm), keine Randsteinwände neben dem Gleis; eigene Trassees behalten Schotterbett ohne Randstein. `SBZ_TRAM_OLD=1` für A/B.

## #55 – 2026-10-19 – Fassaden v4: Notiz-Felder steuern Geschosse/Achsen/EG
`pipeline/facade.py`: Geschosse (Konflikt GWR/OSM vs. Notiz per Geschosshöhe entschieden), Achsabstand an der Adress-Front (GWR-Eingang, Clamp 2.6–4.2 m), Rustika-EG ohne Laden, Stockwerkband, Gauben. Keine neuen Texturen/Draw Calls; `SBZ_FACADES_V4=0` schaltet ab. Grenze ist die Datenlage: Notizen aus Schrägfotos liefern selten Achsen.

## #56 – 2026-10-19 – Spawn nur an kuratierten, geprüften Orten
Start an einem Eintrag aus `web/public/data/spawns.json` (`pipeline/spawns.py`, geprüft: Trottoir/Platz, kein Wasser/Gleis/Collider/Hang, freie Kamera, Blick aufs Ziel). Gespeicherte Position und Kartensprung laufen durch dieselbe Prüfung (`player/spawn.ts`).

## #57 – 2026-10-19 – Dach-only-Objekte bekommen Stützen
swissBUILDINGS3D-Objekte ohne Grundriss (Vordächer) schwebten. Sie bekommen schlanke Stützen an Ecken/alle 8 m (`build_testarea.canopy_posts`), nie auf der Fahrbahn; am HB werden sie stattdessen versteckt (`hb_hide.canopies`).

## #58 – 2026-10-19 – HB-Haupthalle als leere Eventfläche, Arkaden mit Toren statt erfundener Läden
Keine dauerhaften Marktbuden, Kioske oder Weihnachtsbaum in der Halle. Die Bogenarkaden bekommen verglaste Eichentore, keine Ladenschilder: Der Südtrakt ist das Reisezentrum, die Nordtrakt-Läden öffnen erst 2027 (SDA 07/2026). Saisonale Märkte wären später ein Ereignis, kein festes Modell. Details: `research/hb/fix_2026-10-19.md`.

## #59 – 2026-10-19 – Zonen-Kamerapunkte von Hand, mit Blickrichtung
Die Namensabfragen in `pipeline/zones.py` trafen in Zone 1 falsche Orte (HB-Knoten am Perronende, Kamera im Volkshausdach, Sihlpost/Haltestelle daneben). Zone 1 nutzt jetzt Koordinaten aus geprüften Spawn-Orten, Adressen und OSM-Haltestellen, mit optionalem `yaw` (0 = Nord, π/2 = Ost). Vor jeder Zonen-Nacht die Vorher-Aufnahmen auf Fehlplatzierungen prüfen.

## #60 – 2026-10-19 – Keine automatische Fassadenfarbe aus Mapillary
Prototyp `pipeline/autofacade/` (Posen aus Mapillary, LOD2-Wände ins Bild projiziert, Lab-Median): gegen 436 von Hand gelesene Farben ΔE2000-Median 10.5 kalibriert, die konstante Durchschnittsfarbe schafft 11.0. Die Rangkorrelation ist schwach (0.15–0.3). Ursache ist die Pose (kein Pitch/Roll, GPS 10–30 m), nicht die Farbmessung. Nicht übernommen; Farben bleiben Handnotizen. Ein neuer Versuch lohnt sich nur mit Posen-Refinement oder Segmentierung (`research/autofacade/RESULT.txt`).

## #61 – 2026-10-19 – Mapillary-Verkehrsschilder nur als Ergänzung, standardmässig aus
`pipeline/mapillary_features.py` → `pipeline/overrides/mly_signs.json` (CC BY-SA 4.0), Hook `SBZ_MLY_SIGNS=1` in `traffic_signs.py`. Zone 4: 168 Schilder ab 2022, nur 11 decken sich mit den OSM-abgeleiteten (603). Die Abdeckung beschränkt sich auf Cluster an den Hauptachsen. Grösster Gewinn: Vortritt (44), Rad-/Fussweg, Halteverbot. Einschalten erst nach Sichtprüfung auf Testkacheln (`research/mapillary_features.md`).

## #62 – 2026-10-19 – Keine erfundenen Baugerüste mehr
`props.construction` setzte pro Kachel bis zu 6 Gerüste mit Bauzaun an Hauptstrassen (Hash-Auswahl, ohne Datengrundlage) und Gerüste an Gebäuden mit swissBUILDINGS3D-Status «Im Bau» (Stand 2019). Gefunden am Goldbrunnenplatz: Foto 2024/25 ohne Baustelle, im Spiel mit Bauzaun. Ab jetzt nur noch echte Baustellen (OGD Tief-/Hochbau, OSM, `sites.scaffold_rows`). Mit `SBZ_DECOR_SCAFFOLD=1` lässt sich das alte Verhalten wiederherstellen. Wirkt pro Kachel nach dem Neubau.

## #63 – 2026-10-20 – PJZ auf das richtige Gebäude verschoben
Das PJZ-Landmark sass auf swissBUILDINGS3D `ID_FEBC2FA3` (Neugasse 145, Kreis 5), 400 m vom echten Standort entfernt. Jetzt steht es auf `ID_3D89E8BB` (GWR Güterstrasse 33, Baujahr 2022, 16 700 m²). Die alte x-Trennung zwischen Hauptbau und Gefängnistrakt passte nur zum falschen Grundriss. Vorläufig ist der ganze Grundriss Hauptbau; den Gefängnistrakt nach Fotos neu einpassen (Ticket). Gefunden beim Prüfen der Zone-5-Kamerapunkte.

## #64 – 2026-10-20 – Rote Flächen per Override
Die automatische Rot-Erkennung aus SWISSIMAGE (`streets_ortho.red_surfaces`) verpasst Velostreifen im Schatten oder mit Belagswechsel. Neu: `add_red`-Polygone in `markings_z*.json` (auf die Fahrbahn geschnitten, `ground_paint.paint`) und Material `red` in `places_detail` für Wege und Plätze. Jede Fläche braucht einen Foto- oder Ortho-Beleg.

## #65 – 2026-10-20 – Code-Runde für Tickets aus allen Zonen
- Walm- und Satteldach (`k4w4_kit.hip_roof`): Bänder zwischen nach innen versetzten Traufkanten statt paarweiser Eckverbindung. Keine Spitzen mehr auf L-/T-/Schräg-Grundrissen, Dachfläche = Grundriss. Satteldach fällt bei weniger als 88 % Rechteckanteil auf Walm zurück. Alle Landmark-Generatoren mit hip/gable neu gelaufen; `hip_roof_v1` bleibt zum Vergleich.
- Brücken: Tram-Decks zeigen Schienen, Strassendecks Zebras aus OSM-Crossings (`bridges.py` Feld `zb`, `bridges.ts`). Brüstung 1.1 m statt 1.46 m. Rand- und Mittellinien auf Decks fehlen noch.
- Decal kind 12 = «STOP» (automatisch vor OSM-Stop-Zufahrten), Platzobjekt `parasol`, Platanenstämme dunkel gefleckt (nur Nahmodell).
- Katalog H8: Schirmdach-Haltestelle Letzigrund (Override-Schlüssel `stops` in `catalog_assign.json`).

## #66 – 2026-10-21 – Kartensterne nur für echte Wahrzeichen
- Bisher bekam jedes Landmark-Modell einen Stern (135, darunter Hausnummern, Bars, Eckhäuser, HB-Teilmodelle). Jetzt filtert `pipeline/mapdata.landmark_stars()` nach `pipeline/overrides/map_pois.json`: `hide` (exakte Namen), `hide_re` (Ziffern, Farben, Haustypen, Bars …), `merge_m` (Sterne < 60 m zusammenfassen), `rename` (kurze Anzeigenamen mit Umlauten), Schulhäuser als Schul-Punkt. Ergebnis 61 Sterne.
- «Hohlstrasse 283-305» (inkl. Nr. 291) erscheint nie auf der Karte (User 2026-10-21).

## #67 – 2026-10-21 – Nebeneinanderliegende Brückendecks verschmelzen
- Tram-Decks innerhalb oder ≤ 1.5 m neben einem Strassendeck übernehmen dessen Höhe (Δ < 1.5 m). Jede Deckseite, an der ein anderes Strassen-/Tramdeck auf gleicher Höhe (< 0.5 m) anliegt, bekommt pro Vertex ein Flag `ol`/`or` (`bridges._open_sides`); dort keine Brüstung, kein Geländer, kein Collider (`bridges.ts`, `railPush`). Grund: Tram 8 auf der Hardbrücke lief zwischen Mauern wie auf einer eigenen Brücke. 40 Kacheln neu gebaut (`logs/tramdeck_build2.log`).

## #68 – 2026-10-21 – Karte im GTA-Pausenkarten-Stil
- Neues Theme `GTA` (`map_render.ts`) für grosse Karte und Radar: gedämpftes Land, Parks, tiefblaues Wasser mit Uferkante, Häuser mit Schatten, Vignette/Körnung nur im gecachten Kartenhintergrund. Blips in `map_blips.ts` (Wahrzeichen, Schule, Kirche, Spital, Kultur, Behörde, S-Bahn, Tram), Legende einklappbar. Tram dünn dunkelrot erst ab mittlerem Zoom.
- Kreis-Namen 3/4/5/9 dezent (Alpha 0.72, 18–30 px) an `map.json` → `kreis_at` (Pol der Unzugänglichkeit des Kreisteils im Spielgebiet, `build_map.kreis_anchor`).
- Rathaus Hard (Bullingerkirche) nach Fotos neu (`pipeline/landmarks/rathaus_hard.py`), mit Betonlöwin von Mickry 3 (2023, Kunst am Bau Kanton ZH; Quellen `research/rathaus_hard/notes.md`).
