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
Projekt liegt in `/Users/danielgnagi/gtazurich` (eigenes Repo, neben `../gta6`). Grund: Die lange Reel-CLAUDE.md wird nicht mehr bei jeder Anfrage mitgeladen (Token-Budget).

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
Spielgebiet = Kreis 4 + 5, Teile Kreis 9 (Hohl-/Badenerstrasse-Korridor, Lindenplatz, Bahnhof Altstetten) und Kreis 3 (Bahnhof Wiedikon, Schmiede Wiedikon): Polygon `data/build/playarea.json` (6.44 km², 202 Spielkacheln + 77 Kulissenkacheln). Rand = Bauzaun mit Kollision; dahinter Kulissenkacheln nur mit Gebäuden/Boden/Bäumen. Höhen pro Kachel (2 m, int16) statt globalem Raster; global nur 8-m-Raster. Build parallel (fork, alle Kerne), Testgebiet weiter per `GTZ_AREA=test`, einzelne Kacheln per `GTZ_TILES=ix_iy,…`.

## #19 – 2026-10-15 – bestätigt (User: «Platztafeln … real platziert und real aussehen wie Zürich-Schilder»)
Strassen- und Platzschilder: Alle Widmungstafeln (OGD-Punkte, 43 im Spielgebiet) stehen an ihrem vermessenen Ort, das blaue Namensschild darüber. Plätze/Anlagen aus dem Strassennamenverzeichnis bekommen bis 3 Schilder an der nächsten Fassade, ohne Fassade in Reichweite auf einem Pfosten (doppelseitig). Schildlänge folgt dem Namen. Rosa-Luxemburg-Platz zusätzlich als grosses freistehendes Schild mit roten Nelken (`pipeline/overrides/landmark_signs.json`). Code: `pipeline/plazasigns.py`, `web/src/world/streetsigns.ts`, `web/src/world/landmarks.ts`.

## #20 – 2026-10-15 – vorgeschlagen
Bodenbelag: Innenhöfe und Vorgärten nach Amtlicher Vermessung (Kanton ZH, bodenbedeckung_f): Grün → Rasen, befestigt → Hofbelag; Rest wie bisher. Fahrbahn bleibt vorerst OSM, weil die AV in der Innenstadt Trottoirs oft in «Strasse, Weg» einschliesst (Vergleich ausstehend, research/groundcover.md).
