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
