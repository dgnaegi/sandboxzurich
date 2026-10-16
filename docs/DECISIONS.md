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
