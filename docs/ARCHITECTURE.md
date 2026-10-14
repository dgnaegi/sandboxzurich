# Architektur

Stand: Vorschlag. Entscheide werden in `DECISIONS.md` bestätigt.

## Überblick
```
Rohdaten (OSM, swisstopo, Stadt ZH OGD, POI-Recherche)
   │  pipeline/  (Python, lokal auf dem Mac, reproduzierbar)
   ▼
Kacheln 200×200 m: glb (meshopt) + KTX2-Texturen + JSON (POIs, Wege, Graphen)
   │  zusammen mit web/dist in ein Archiv gepackt
   ▼
Scalingo-App (nginx, statisch)  ──  scalingo deploy release.tar.gz
   │  ab viel Traffic optional: Kacheln auf S3-Storage mit CDN (nur TILE_BASE_URL ändern)
   ▼
Browser (Handy und PC)
```

## Tech-Stack
| Bereich | Wahl | Grund |
|---|---|---|
| Rendering | Three.js (WebGL2, später optional WebGPU) | Verbreitet, gut dokumentiert, AI kennt es gut |
| Sprache | TypeScript, strict | Weniger Laufzeitfehler bei AI-generiertem Code |
| Build | Vite | Schnell, einfach |
| Physik | Rapier (WASM) | Character Controller, Kollision, zerbrechliche Objekte |
| Pipeline | Python 3 (venv `../.venv` wiederverwenden), gltfpack, toktx | Reel-Pipeline ist schon Python |
| Tests | Vitest (Logik), Playwright (Screenshots, FPS-Messung) | AI kann selbst prüfen |
| Hosting | Scalingo, Static-Buildpack (nginx), Archiv-Deploy | Siehe Abschnitt «Scalingo» |

## Geplante Ordnerstruktur
```
game/
  CLAUDE.md  README.md
  docs/                 Projektdokumente
  research/             POI-Listen, Quellenlinks, Notizen zu Orten
  pipeline/             Python: fetch_*, build_*, overrides/
    overrides/          Manuelle Korrekturen (JSON, versioniert)
  data/raw/             Heruntergeladene Rohdaten (nicht im Repo)
  data/build/           Erzeugte Kacheln (nicht im Repo, wird hochgeladen)
  deploy/               scalingo.json, servers.conf.erb, release.sh
  web/                  Vite-App
    src/engine/         Renderer, Kachel-Streaming, LOD, Kamera
    src/world/          Strassen, Gebäude, Tram, Verkehr, Fussgänger:innen
    src/input/          Eingabe-Abstraktion (Tastatur/Maus, Touch, Gamepad → Aktionen)
    src/player/         Character Controller, Kamera-Folgen
    src/gameplay/       Sterne, Polizei, Zerstörung, Quests
    src/ui/             HUD, Radar, Menüs (Stil wie im Reel)
  tests/                Playwright-Szenarien, feste Kamerapunkte
  preview/              Screenshots für den User
  logs/                 Logs langer Läufe
```

## Scalingo
Grundsatz: Das Spiel läuft komplett im Browser. Scalingo liefert nur statische Dateien aus, also zustandslose Container, die sich beliebig horizontal skalieren lassen.

- **Buildpack:** Static (nginx). Ausgeliefert wird `web/dist/` inklusive `tiles/`. Konfiguration über `scalingo.json`, `Procfile` (falls nötig) und `servers.conf.erb` für nginx.
- **Kein Build auf Scalingo:** Pipeline (Python, gltfpack, toktx) und `vite build` laufen lokal. Gründe: zu schwer für den Builder, kein Python- oder Blender-Setup dort nötig, reproduzierbar.
- **Deploy per Archiv statt Git-Push:** `pipeline/release.sh` baut `release.tar.gz` (App und Kacheln) und lädt es mit `scalingo --app <app> deploy release.tar.gz` hoch. So kommen die grossen Kacheln nie ins Git-Repo.
- **Image-Grösse:** Scalingo begrenzt die Image-Grösse (Limit beim Einrichten in der Doku prüfen und hier eintragen). Budget für alle Kacheln aller vier Kreise: ≤ 600 MB. Wird es knapp, kommt Stufe 2.
- **Caching (nginx):**
  - Dateinamen mit Inhalts-Hash (`tiles/v{hash}/…`, Vite-Assets)
  - `Cache-Control: public, max-age=31536000, immutable`
  - `index.html` mit `no-cache`
  - vorkomprimierte `.gz`-Dateien (`gzip_static`); glb und KTX2 sind schon komprimiert
- **Konfiguration per Umgebungsvariable:** `TILE_BASE_URL` (Standard: `/tiles`) wird beim Start in `config.js` geschrieben. Damit lässt sich ohne Code-Änderung auf Stufe 2 wechseln.
- **Stufe 2 (erst bei viel Traffic):** Kacheln auf S3-kompatiblen Storage mit CDN (z.B. Infomaniak Swiss Backup/Public Cloud oder Cloudflare R2), CORS auf die Spiel-Domain beschränkt. Scalingo liefert dann nur noch die App aus.
- **Skalierung:** Start mit 1 Container Grösse S. Vor dem Launch und bei viralen Spitzen `scalingo scale web:3:M`.
- **Region:** osc-fr1 (Paris), DSGVO/DSG-konform.
- **Testlinks:** Review Apps pro Branch oder Pull Request (Scalingo-GitHub-Integration). Für jeden Stand gibt es eine URL, die sich auf dem Handy testen lässt.
- **Backend später, optional:** Highscores oder Statistik als eigene kleine Node-App mit Postgres-Add-on. Getrennt von der statischen App, damit diese nie ausfällt.
- **Domain:** Custom Domain mit Let's Encrypt (bei Scalingo eingebaut).

## Plattformen: Handy und PC gleichwertig
- **Eingabe:**
  - **PC:** Tastatur und Maus (WASD, Maus für die Kamera mit Pointer Lock, E für Aktion) und Gamepad (Gamepad API)
  - **Handy:** Touch mit virtuellem Joystick links, Kamera-Wischen rechts, Aktions-Buttons
  - Die Erkennung läuft automatisch, ein Wechsel ist jederzeit möglich. Die Eingabe wird abstrahiert (`input/actions.ts`), damit Gameplay-Code nie direkt Tasten oder Touch abfragt.
- **Grafikstufen:** `low` (alte Handys), `medium` (Handy-Standard), `high` (PC). Sie unterscheiden sich in Sichtweite, Schatten, Pixel-Ratio-Deckel, Dichte der NPCs und Dichte der Deko. Die Stufe wird anhand der gemessenen FPS automatisch gewählt und lässt sich manuell überschreiben.
- **UI:** Ein einziges HUD, das für Hochformat und Querformat skaliert. Im Hochformat auf dem Handy die Safe Areas beachten (`env(safe-area-inset-*)`). Auf dem Handy wird Querformat empfohlen, Hochformat soll aber auch funktionieren.
- **Tests:** Jeder Playwright-Screenshot läuft zweimal: im Desktop-Viewport (1920×1080) und im Handy-Viewport (iPhone-Emulation).

## Kacheln (Streaming)
- Raster 200×200 m in lokalen Metern, Name `t_{ix}_{iy}`.
- Pro Kachel: `geo.glb` (Gebäude, Boden, Strassen, Möbel, zusammengefasst nach Material), `lod1.glb` (vereinfacht), `meta.json` (POIs, Beschriftungen, Kollision, Spawnpunkte).
- Global, einmal geladen: Strassen-, Velo- und Tramgraph (für NPC-Verkehr und Navigation), Radar-Karte, Texturatlas.
- Geladen wird im Radius um den Spieler: nah volle Detailtiefe, mittel LOD1, fern nur Silhouette und Nebel.

## Performance-Budgets (verbindlich)
Referenzgeräte: iPhone 12 bzw. ein mittleres Android-Handy (Stufe `medium`) und ein Laptop mit integrierter Grafik (Stufe `high`).

| Messgrösse | Handy (medium) | PC (high) |
|---|---|---|
| Download bis spielbar | ≤ 20 MB | ≤ 20 MB |
| Einzelne Kachel | ≤ 1.5 MB | ≤ 1.5 MB |
| Draw Calls pro Frame | ≤ 250 | ≤ 600 |
| Sichtbare Dreiecke | ≤ 1.5 Mio. | ≤ 4 Mio. |
| GPU- und JS-Speicher | ≤ 700 MB (iOS-Safari-Absturzgrenze ~1–1.5 GB) | ≤ 1.5 GB |
| Framerate | ≥ 30 fps | ≥ 60 fps |

Hilfsmittel: Instancing (Bäume, Laternen, Velos, Autos), Material-Atlas, KTX2-Texturen, Frustum- und Distanz-Culling, Physik nur nahe beim Spieler.

## Koordinaten
Lokale Meter, Ursprung LV95 (2681400, 1248700), z0 = 408 (wie das Reel). Umrechnung nach Three.js: `(x, y, z)_lokal → (x, z, -y)`.
