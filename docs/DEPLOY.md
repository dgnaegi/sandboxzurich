# Deploy über ein CDN (Anleitung)

Das Spiel ist eine rein statische Website: HTML, JavaScript und Dateien (Kacheln, Modelle, Texturen). Es braucht keinen Server-Code, keine Datenbank und kein Login. Jedes CDN bzw. jeder statische Host funktioniert (z. B. Cloudflare Pages, Bunny.net, Netlify).

Stand 2026-10-15: ca. 900 Dateien, ca. 120 MB gesamt, keine Datei über 10 MB. Beim ersten Besuch lädt ein Handy rund 15–40 MB (nur Kacheln in der Nähe), danach kommt fast alles aus dem Cache.

## 1. Vorher: Inhalt freigeben
Erst öffentlich machen, wenn erledigt:
- Impressum mit verantwortlicher Person (Menü «Impressum»).
- Kennzeichnung als politische Werbung (Spiel und Website).
- Kampagne hat die AL-Plakate und die Event-Plakate gesehen (`research/posters/README.md`, Freigabeliste).
- Bis dahin nur als **geheimer Testlink** (siehe Schritt 5).

## 2. Bauen (lokal, auf deinem Mac)
Die Kartendaten (Kacheln) sind schon gebaut und liegen in `web/public/tiles/`. Nur neu bauen, wenn sich die Karte geändert hat (dauert ca. 30–75 min):
```
.venv/bin/python pipeline/build_testarea.py > logs/build.log 2>&1
```
Dann die Website bauen:
```
cd web
npm ci
npm run build          # Typprüfung + Vite → Ordner web/dist/
npx vite preview --host  # lokal testen: http://localhost:4173
```
`web/dist/` ist das Einzige, was hochgeladen wird. Darin liegen `index.html`, `assets/` (Code, Dateinamen mit Hash) und alles aus `public/` (tiles, models, tex, data, fonts, map).

Kurztest vor dem Upload (Dev-Server muss laufen: `npx vite --port 5173`):
```
node tests/gameplay.mjs && node tests/touch.mjs
```

## 3. Hochladen
**Cloudflare Pages** (einfachste Variante, gratis-Stufe reicht vermutlich):
```
npx wrangler pages deploy dist --project-name sandboxzurich
```
Limits prüfen: max. 20'000 Dateien und 25 MB pro Datei (wir: ~900 Dateien, < 10 MB).

**Bunny.net / anderes CDN mit Storage:** Inhalt von `web/dist/` in die Storage-Zone kopieren (FTP, rclone oder deren CLI), Pull-Zone davor.

**Kacheln getrennt hosten** (optional, wenn die Website woanders liegt): Kacheln auf das CDN legen und beim Bauen die Adresse mitgeben:
```
VITE_TILE_BASE_URL=https://cdn.example.ch/tiles npm run build
```
Dann muss das CDN CORS erlauben (`Access-Control-Allow-Origin: *` für `/tiles/*`).

## 4. Header (wichtig für Ladezeit)
| Pfad | Cache-Control | Grund |
|---|---|---|
| `/index.html` | `no-cache` | neue Version sofort sichtbar |
| `/assets/*` | `public, max-age=31536000, immutable` | Dateiname enthält Hash |
| `/tiles/*`, `/models/*`, `/tex/*`, `/data/*`, `/map/*`, `/fonts/*` | `public, max-age=86400, stale-while-revalidate=604800` | Namen ohne Hash; nach einem Update höchstens 1 Tag alt |

Typen (MIME), falls das CDN sie nicht kennt: `.glb` → `model/gltf-binary`, `.webp` → `image/webp`, `.json` → `application/json`, `.ttf` → `font/ttf`.
Komprimierung (Brotli oder gzip) einschalten für `.js`, `.json`, `.html`, `.css`, `.glb`. Bei Cloudflare ist das Standard.

Beispiel Cloudflare Pages: Datei `web/public/_headers` (wird mit hochgeladen):
```
/index.html
  Cache-Control: no-cache
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/tiles/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/models/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/tex/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/data/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
```

## 5. Geheimer Testlink (vor dem Launch)
- Nicht verlinken und Suchmaschinen sperren: Header `X-Robots-Tag: noindex` für `/*` oder `robots.txt` mit `Disallow: /`.
- Besser mit Passwort: z. B. Cloudflare Access (gratis bis 50 Personen, Login per E-Mail-Code).
- Den Link nur an Testpersonen geben.

## 6. Kontrolle nach dem Upload
1. Auf dem Handy öffnen (iPhone und Android, WLAN und Mobilnetz): lädt es, läuft es flüssig, gehen Joystick, ⇧ und E?
2. Am PC in den Entwicklerwerkzeugen (F12 → Netzwerk): keine roten 404-Fehler, `.glb` kommen komprimiert bzw. aus dem Cache beim zweiten Laden.
3. Konsole: keine Fehler.
4. Ein zweites Mal laden: es muss deutlich schneller gehen (Cache wirkt).

## 7. Update
Neu bauen (Schritt 2) und `web/dist/` erneut hochladen. Wegen `no-cache` auf `index.html` sehen alle sofort den neuen Code; Kacheln/Modelle aktualisieren sich spätestens nach einem Tag. Soll eine Kartenänderung sofort sichtbar sein: im CDN den Cache leeren («Purge»).

## Nicht nötig
Keine Datenbank, keine Cookies, kein Tracking, keine API-Keys im Frontend. `.env` (Mapillary-Token) wird nur für die Pipeline gebraucht und nie hochgeladen.
