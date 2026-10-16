# QA-Review (2026-10-16)

Strenge Testrunde wie von einer Erstspielerin auf iPhone (390x844 / 844x390, Touch) und PC (1280x720). Es wurde kein Code geändert. Getestet gegen einen eingefrorenen Snapshot des Dev-Servers (`web/src` um ca. 09:00 kopiert, weil parallele Agents per HMR laufend Seiten-Reloads auslösen) plus Stichproben gegen die Live-URL. Headless Chromium auf einem Mac (schnelle GPU); Handy-Werte mit 4x CPU-Drosselung, also nur Richtwerte, kein echtes iOS.

## Gesamturteil
Die Welt sieht für ein Browserspiel erstaunlich gut aus (Strassenzüge, Ladenfronten, Abendlicht an der Langstrasse), Ladezeit ist kurz (live 2.3 s Handy / 4.2 s PC bis spielbar, 16 / 26 MB) und der PC läuft stabil mit 60 FPS ohne Konsolenfehler. Die Bewegung ist aber **nur gegen Gebäudegrundrisse kollisionssicher**: Bäume, parkierte Autos, Trams, NPCs, Zäune und Mobiliar sind für Figur und Velo Luft, die Kamera steckt beim Gehen entlang von Fassaden in rund jedem vierten Messpunkt in der Wand. Das grösste Risiko für das iPhone ist ein **JS-Heap, der bei jedem Ortswechsel um 50–80 MB wächst und nie zurückkommt** (PC 320 → 1050 MB nach 9 Sprüngen, Handy 140 → 450 MB), dazu 35–45 FPS mit vielen Rucklern (>50 ms) im Handy-Modus. Auf der Karte gibt es Sprungziele, bei denen man im Bauwerk oder auf Gleisland landet (Hardbrücke-Preset: Figur unsichtbar im Betonbau). Spielerisch fehlt nach dem Herumlaufen jeder Anlass weiterzumachen: keine Ziele, keine Reaktion der Welt (Autos/NPCs weichen nicht aus, Autoklau ohne Folgen), Autos bleiben in den Parkreihen stecken.

## Die 10 wichtigsten nächsten Verbesserungen fürs Spielgefühl
1. **Speicher-Leck beheben** (Blocker fürs iPhone): Beim Kachelwechsel werden Pfade/Rasenspots/NPC-Spots/Collider offenbar jedes Mal neu angehängt, nie entfernt; Tile-Unload muss alle Callback-Daten (`onPaths`, `onLawn`, `onSpots`, `colliders.add`) wieder freigeben.
2. **Kollision für Hindernisse ausserhalb der Gebäude**: Bäume, Laternen, Bänke, parkierte Autos, Trams, Terrassenmöbel als Kreise/Kapseln in `Colliders` (Figur, Velo), sonst läuft man durch alles Kleine.
3. **Kamera-Kollision**: Strahl gegen Gebäude reicht nicht (Kamera in Wänden, Terrassen, unter Brücken). Kamera-Kugel (r ~0.5 m) gegen Footprints und Landmarks, bei Annäherung Spieler-Ausblenden/Pitch anheben.
4. **Sprungziele prüfen**: jeder Kartensprung und jedes Preset muss auf begehbarem Boden (nicht in Landmarks, Bahnland, Brücken-Unterbau, ausserhalb des Zauns) enden; Hardbrücke-Preset korrigieren.
5. **Auto-Fahrgefühl**: Parkreihen sind Sackgassen (Auto steht zwischen zwei Autos, kommt ohne Rückwärtsgang nicht raus, Schaden häuft sich); Hinweis «S = rückwärts», sanftes Wegschieben parkierter Autos oder Ausparkhilfe.
6. **Handy-Performance**: 35–45 FPS, 15–24 Ruckler pro 40 s; Drawcalls/Dreiecke (bis 1.4 M) und Hitches beim Kachelladen glätten (Ladearbeit auf mehrere Frames verteilen).
7. **Touch-Steuerung**: Joystick hat keine Totzone, Radius nur 50 px, und «Rennen» fällt bei jedem Loslassen des Sticks zurück (muss jedes Mal neu getippt werden). Totzone ~10 %, Radius 60–70 px, Rennen automatisch ab ~90 % Auslenkung.
8. **Erste Minuten**: Kein Ziel, keine Orientierung. Das Spiel startet auf Tramgleisen vor einem Tram; Ladebildschirm zeigt nur Balken ohne Text. Ein sichtbarer Hinweis («Tippe auf den Radar», «E: Velo nehmen») und ein sanfter Spawn auf dem Trottoir.
9. **Lebendige Welt**: NPCs/Autos reagieren nicht auf den Spieler (kein Ausweichen, Hupen, Schimpfen); im Auto-Crash gibt es keine Fussgänger-Reaktion. 9 von 25 NPCs stehen/laufen in Gebäudegrundrissen.
10. **Lesbarkeit der UI**: Uhr-Panel-Titel «Uhrzeit» dunkel auf dunkel, Panel verdeckt im Querformat die E-/Lauf-Knöpfe; Karten-Legende überlappt im Hochformat die Zoom-Knöpfe.

---

## Blocker
**B1. Speicher wächst bei jedem Ortswechsel (iOS-Absturzgefahr)**
- Was: JS-Heap nach `gc()` steigt pro Teleport um ca. 50–80 MB, kein Plateau. PC: 320 → 538 → 607 → 681 → 720 → 771 → 954 → 1001 → 1050 MB (9 Sprünge A→B→C→A…). Handy-Modus: 142 → 450 MB. Texturen (≈145 → 313) und Geometrien (≈300 → 395) plateauieren, das Leck liegt also in JS-Daten.
- Reproduzieren: `web/tests/qa_leak.mjs [BASE] [pc|phoneL]`.
- Vermutung: Callbacks `tiles.onPaths/onLawn/onSpots/onSchools/onFountains` und `colliders.add` (`src/engine/tiles.ts:197`, `src/main.ts` ca. 70–80) hängen bei jedem Kachel-Load Daten an Listen an (crowd.addPaths, lawns.add, pedspots), beim Unload wird nur Geometrie/Material freigegeben (`tiles.ts` ca. 125–137), Collider-Grid und Crowd-Daten bleiben.
- Kontrolle nötig auf echtem iPhone (reiner Spaziergang durch 3–4 Kreise). Ziel laut ARCHITECTURE-Budget prüfen.

**B2. Hardbrücke-Sprungziel: Figur im Betonbau, Kamera in Geometrie**
- Wo: `?at=58.5,116.7,0` (Place «Hardbrücke» in `public/map/map.json`), auch `?at=58.5,118,1&t=21:00`.
- Was: Figur nicht sichtbar, Bild zeigt nur eine flache Fläche/Treppenunterbau. Jedes Handy-Spielen, das über die Karte «Hardbrücke» wählt, startet blind.
- Bild: `preview/qa_review_spot_hardpop.jpg`, `preview/qa_review_night_sheet.jpg` (3. Bild).
- Vermutung: Place-Koordinate liegt auf der Bahnhofs-/Brücken-Landmark-Treppe; `jump()` prüft nur `colliders.inside`, nicht Landmarks/Brückenunterbau.

## Hoch
**H1. Figur und Velo laufen durch alles ausser Gebäude**
- Was: `Colliders` kennt nur Gebäude-Footprints (`src/player/collision.ts`, einzige Quelle `tiles.ts:197`). Parkierte Autos, fahrende Autos (zu Fuss), Trams (Foto `preview/qa_review_spot_tram.jpg`: Figur steht an/in der Tramwand), Bäume, Laternen, Bänke, Gartenzäune, Terrassenmöbel sind nicht solide. Auch Brunnen, Wasser, Treppen/Randsteine ohne Wirkung. Velo-Crash-Logik greift deshalb nur an Hauswänden.
- Reproduzieren: zu Fuss/Velo in ein parkiertes Auto oder Baum laufen; `tests/qa_obst.mjs`.
- Nachweis: Codepfad `Player.update` ruft nur `tiles.colliders.resolve`. Der automatische Lauftest (136 Läufe à 5 s) fand deshalb nur 0 Wand-Durchdringungen und 0 Hänger, was auch heisst, dass nichts anderes bremst.

**H2. Kamera steckt oft in Wänden/Terrassen**
- Was: Beim Gehen entlang von Fassaden liegt die Kamera in 16–28 % der Messpunkte innerhalb eines Gebäude-Footprints oder <0.45 m von der Wand (Langstrasse 53/192, Helvetiaplatz 38/192, Kanzlei 47/192, Hohlstrasse 42/192, Lochergut 40/192, Josefwiese 16/192). Zu sehen: Kamera mitten in Café-Terrasse, Kopf einer sitzenden NPC ragt ins Bild, Schaufenster füllt das Bild.
- Bilder: `preview/qa_review_cam_sheet.jpg`; Test `tests/qa_cam.mjs`.
- Ursache: `freeFraction` prüft nur die Mittellinie Spieler→Kamera gegen Footprints (`player.ts` Kamerablock); Mindestdistanz 1.6 m, keine Kugel, nichts für Terrassen/Trams/Brücken. `camera.position.y` wird gegen `tiles.ground` geklemmt, nicht gegen Brückendecks.

**H3. Auto: Fahrt blockiert in Parkreihen, Auto landet in Gebäude/ausserhalb**
- Was: Beim Auto-Klau in einer Parkreihe (Langstrasse 842,-483; Helvetiaplatz; Albisriederplatz; Josefwiese) steht man 1.3 s Rückwärtsfahrt lang vor dem nächsten parkierten Auto; in unseren 35-s-Fahrten war das Auto 60–65 von 70 Messungen praktisch stehend, Schaden steigt (0.1–0.25, Kalkbreite 0.97 = Wrack). Ohne Hinweis, dass Rückwärts mit S geht.
- Auto-Klau am Lochergut (`?at=65,-937`, nächstes Auto bei 80,-994) liefert ein Auto ausserhalb des Spielgebiets und innerhalb eines Footprints: dauerhaft eingeklemmt (70/70 Messungen `inside`+`outside play`). Bild-Test: `tests/qa_drive.mjs`.
- Ursache: Parkplatz-Slots nicht gegen Zaun-Polygon/Footprints gefiltert (`parkedcars.ts`/Pipeline).

**H4. Handy-FPS und Ruckler**
- Was (Handy-Modus, 4x CPU-Drosselung, 40 s Gehen je Ort): Helvetiaplatz 34.6 FPS (p99 66 ms, 24 Frames >50 ms, max 833 ms), Langstrasse 39.3, Limmatplatz 38.2, Albisriederplatz 42.3, Altstetten 39.0, Hardbrücke 48.9. Dreiecke pro Frame bis 1.4 M, Drawcalls bis 200. Auf einem echten iPhone mit 4x langsamerem Ladepfad wären die Hitches (Kachelwechsel, 250–830 ms) deutlich sichtbar.
- PC (ungedrosselt, 60 s je Ort): 58–60 FPS, p99 16.8 ms, pro Ort 0–3 Frames >50 ms, Spitzen 267 / 183 / 133 ms (beim Kachel-/Modell-Nachladen). Drawcalls bis 546, Dreiecke bis 3.2 M, Texturen 253 → 492, JS-Heap 380 → 670 MB (siehe B1).
- Test: `tests/qa_perf.mjs [BASE] [pc|phoneL] [Sekunden]`.

**H5. Touch: Rennen-Schalter fällt bei jedem Loslassen**
- `src/input/touch.ts` `end()` ruft `setRun(false)` bei Loslassen des Sticks. Wer rennen will, muss vor jeder Bewegung ⇧ neu tippen. Zusätzlich: Joystick-Radius 50 px, keine Totzone (jede Mini-Bewegung > 0.05 läuft), Kamera-Wischen nutzt in Hochformat nur die schmale rechte Hälfte (195 px).

## Mittel
**M1. Sprungziel auf Bahnland**: Kartenklick landet bei (-448.5, 316.2) und (512.9, -19.3) laut `railzone.json` auf Gleis-/Bahnland (Boden ~8 m tiefer, z -8.4 / -5.6, sieht nach Gleisgraben aus). `?at=-448,316,0`, Bild `qa_review_spot_rail.jpg`. Das ist genau die offene Todo-Linie «Figuren nicht auf Bahnland».
**M2. Kartenklick in Portrait**: 0 von 10 Taps auf die Karte lösten einen Sprung aus (Querformat 6/20, PC 8/20; viele Klicks lagen ausserhalb des Spielgebiets, das ist erwartet). Im Hochformat ist die Karte beim Öffnen auf das Spielgebiet nicht zentriert/zu klein: Spielgebiet nur ein kleiner Fleck in der Mitte, Legende («Irgendwo im Spielgebiet hintippen…») läuft unter die Zoom-Knöpfe `+`/`−`. Bild: `qa_review_ui_sheet2.jpg`. Test wiederholen mit gezieltem Tap auf Pin (`tests/qa_ui.mjs`).
**M3. NPCs in Gebäude-Footprints**: Innerhalb von 150 m um die Hotspots standen/gingen pro 30 s: Langstrasse 9 von 25, Albisriederplatz 9 von 15, Limmatplatz 7 von 22, Altstetten 5 von 11, Helvetiaplatz 3 von 18. Beispielpunkte: (804,-544.7), (810,-549.2), (-1993.8,691.1), (693.7,483.8). Teils gewollte Eingangs-/Laden-NPCs, teils echte Durchläufer; Footprints gegen `pedspots` prüfen. `tests/qa_npc.mjs`. Keine NPCs auf Bahnland gemessen (0 überall).
**M4. Autos fahren durch Gebäude-Footprints**: Verkehr-Autos mit Mittelpunkt in einem Footprint: Langstrasse-Umfeld 9 verschiedene (632.6,-568.7), (668.5,-490.9), (606,-548.4), (613.8,-554.3); Hardbrücke (119,213), (127.8,256.1); Albisriederplatz (-529,-723); Kalkbreite (370.6,-1336.6), (367.2,-1339.4). Teils Hofdurchfahrten/Unterführungen, teils zu breite Footprints. Einmal im Betrieb gegenprüfen. Ausserdem einmal Auto-Überlappung gemessen (129,231 bei Hardbrücke).
**M5. Höhensprung beim Betreten der Hardbrücke**: Beim Rennen von (58,117) in Nord/West/Südwest springt `player.z` bis 0.76 m innerhalb von 50 ms (`bridges.heightAt`); in `Player.update` wird zwar mit dt*15 geglättet, aber bei 0.6–0.76 m Stufe wirkt es wie ein Ruck.
**M6. Spawn auf Tramgleis**: Standard-Spawn (760,-905) steht auf Gleisen vor einem Tram (`qa_review_boot_sheet.jpg`). Für Neulinge verwirrend und gefährlich wirkend.
**M7. Karten-Seite**: Uhr-Panel (`#clockpanel`) Titel «Uhrzeit» ist dunkel auf dunklem Grund (kaum lesbar), im Querformat überdeckt das Panel die Knöpfe ⇧/E (`qa_review_ui_sheet1.jpg`).
**M8. Tram-Optik**: Tram ist ein flacher blauer Quader mit Linienschild; Spieler steht an der Seite innerhalb der Tramwand (siehe H1).

## Niedrig
- **N1. Ladebildschirm** zeigt nur Titel + Balken, `#ld-msg` bleibt leer; Balken springt nach 0.6 s nur auf ~35 %. Kein «Tipp» und keine Rückmeldung, falls es hängt.
- **N2. Hilfe-Karte** erscheint nur ohne WebDriver (`?help` zum Testen). Hochformat: Hinweiszeile «WASD laufen …» auf Handy nie sichtbar, ok. Hilfe-Text wirkt ordentlich: «So geht's», Rechtschreibung stimmt.
- **N3. Konsole/Netz**: Live: 0 Fehler, 0 404/5xx in allen drei Viewports; einzige Warnung «THREE.Clock: This module has been deprecated. Please use THREE.Timer instead.» Auf dem Dev-Server tauchte mehrfach «Unexpected token '<'» aus GLTFLoader auf: `models/trains/tiles/r_*.glb` lieferte kurz HTML-Fallback, weil die Dateien gerade von einem parallelen Agent neu erzeugt wurden (danach vorhanden). Kein Live-Problem, aber unbehandelter `pageerror` (Promise-Rejection im Railways-Loader) → der Fehlerfall sollte abgefangen werden.
- **N4. Zeit läuft sehr schnell** (Uhr springt in Minuten von 12:00 auf 12:49 bei Normalrate 1x = 1 Spielminute pro Sekunde). Absichtlich, doch für Tag/Nacht-Zyklus und Screenshot-Tests merken. Tageslicht 07:00 sehr dunkel (Sonnenaufgang laut Code ~8:00).
- **N5. Nacht**: Langstrasse 22:00 sehr gut (Lichtkegel, Schaufenster). Helvetiaplatz 23:00 flach dunkelblau, fast keine Lampen auf dem Platz (`qa_review_night_sheet.jpg`).
- **N6. Einstellungen**: sinnvoll (Grafik Auto/Akku/Hoch, Kamera-Empfindlichkeit, Ton, Joystick links/rechts). Grafik-Hinweistext ist nur beim gewählten Modus gesetzt. Kein Defekt gefunden. Texte: kein ß, keine englischen Strings gefunden (Toast-Kicker «EASTER EGG»/«ZÜRICH-WISSEN»/«STRASSENNAME» im Code teils englisch: `main.ts` `EASTER EGG ${n}/${total}`; Toasts sind aktuell aus).
- **N7. Mobil Querformat**: Hinweis für Wisch-Kamera ist nur in der Hilfekarte; keine zweite Erinnerung.

## Nicht gefunden / ok
- Stecken bleiben: in 136 Läufen (17 Orte × 8 Richtungen × 5 s Rennen) kein Hänger an Kanten ausser an Gebäudewänden (Stillstand 2–3.5 s bei Albisriederplatz yaw 2.36/5.5, Altstetten yaw 3.14 sind Wände); niemand lief in ein Gebäude oder ausserhalb des Zauns.
- Laufen/Rennen, Velo (aufsteigen/fahren/absteigen mit E, Crash ab 5.5 m/s), Auto-Einstieg/Aussteigen (E) funktionieren mit Tastatur und Touch (`gameplay.mjs`, `touch.mjs`, `drive.mjs`: bis auf die geplante Wrack-Prüfung alle OK; `FAIL touch: no stars, car left standing (0 near)` ist ein veralteter Test, weil beschädigte Autos jetzt als Wrack stehen).
- Karte (Radar-Tap, Zoom +/−, M-Taste, Schliessen), Menü (Weiter/Karte/Einstellungen/Credits/Impressum), Uhr-Panel (Tag, Tageszeit, Pause, 1×/10×/60×) öffnen und schliessen sauber.
- Keine NPCs auf Bahnland, keine T-Posen in den Screenshots, keine NPC-Stauung (kein NPC > 20 s starr).
- Audio nicht beurteilbar (headless).

## Testskripte (neu, `web/tests/`)
`qa_lib.mjs` (Helfer), `qa_boot.mjs` (Start/Ladebildschirm, lokal+live), `qa_ui.mjs` (Hilfe/Menü/Einstellungen/Uhr/Karte/Sprünge), `qa_walk.mjs` (8 Richtungen an allen Orten), `qa_cam.mjs` (Kamera an Fassaden), `qa_npc.mjs` (NPC/Verkehr-Audit), `qa_obst.mjs` (Hindernisse), `qa_drive.mjs` (Autofahrt), `qa_perf.mjs` (FPS/Speicher), `qa_leak.mjs` (Leck), `qa_spots.mjs` (Screenshots an Koordinaten, `VP=phoneL`), `qa_sheet.py` (Kontaktbogen). Aufruf Beispiel: `node tests/qa_leak.mjs http://localhost:5173 phoneL`. Wegen paralleler Agents am besten gegen einen eingefrorenen Snapshot (anderer Vite-Port) laufen lassen, sonst reloaded HMR die Seite mitten im Test.

## Bilder (`preview/qa_review_*`)
`boot_sheet`, `ui_sheet1` (Querformat), `ui_sheet2` (Hochformat + PC Karte), `cam_sheet`, `spots_a` (Auto/NPC in Gebäude, Gleis, Lochergut, Hardbrücke), `night_sheet` (Nacht, Morgen, Tram) sowie die Einzelbilder `qa_review_*_*.jpg`.
