# Deploy (Cloudflare Pages)

Das Spiel ist eine rein statische Website (HTML, JavaScript, Kacheln, Modelle). Kein Server, keine Datenbank, kein Login; einzige Ausnahme ist die winzige Worker-Route `/api/report` für «Fehler melden» (Abschnitt unten). Cloudflare liefert alles über sein CDN aus; Scalingo wird nicht gebraucht.

Stand 2026-10-16: `web/dist/` = 141 MB, 961 Dateien, keine Datei über 5 MB (Cloudflare-Limits: 20'000 Dateien, 25 MB pro Datei). Download bis spielbar ca. 21 MB (14 MB komprimiert).

**Wichtig:** Die Kartenkacheln (`web/public/tiles/`) und Texturen (`web/public/tex/`) sind nicht im Git-Repo, sie werden lokal von der Pipeline erzeugt. Deshalb immer von diesem Mac aus bauen und hochladen, nicht über eine automatische GitHub-Verbindung.

## Einmalig einrichten
1. Konto anlegen: https://dash.cloudflare.com/sign-up (Gratis-Plan reicht).
2. Im Terminal anmelden (öffnet den Browser zum Bestätigen):
   ```
   cd ~/sandboxzurich/web
   npx wrangler login
   ```
3. Projekt anlegen (Name = Teil der Adresse, z. B. `sandboxzurich.pages.dev`):
   ```
   npx wrangler pages project create sandboxzurich --production-branch main
   ```

## Jedes Mal: bauen und hochladen
```
cd ~/sandboxzurich/web
npm run build
npx wrangler pages deploy dist --project-name sandboxzurich --branch main
```
- `npm run build` prüft die Typen und schreibt `web/dist/` (inkl. Kacheln, Modelle, `_headers`).
- Der Upload dauert beim ersten Mal einige Minuten, danach werden nur geänderte Dateien hochgeladen.
- Am Ende steht die Adresse, z. B. `https://sandboxzurich.pages.dev`.

Nur zum Testen ohne die Hauptadresse zu ändern: `--branch test` statt `--branch main` → eigene Vorschau-Adresse (`https://test.sandboxzurich.pages.dev`).

Hat sich die Karte geändert, vorher die Pipeline laufen lassen (siehe `docs/HANDOFF.md`, «Pipeline-Reihenfolge»), nach neuen Modellen `.venv/bin/python pipeline/pack_models.py`.

## Vorher lokal prüfen (empfohlen)
```
cd ~/sandboxzurich/web
npx vite preview --host        # http://localhost:4173 – genau das, was hochgeladen wird
npx vite --port 5173           # zweites Terminal: Dev-Server für die Tests
node tests/gameplay.mjs && node tests/touch.mjs && node tests/drive.mjs
```

## Cache und Suchmaschinen
`web/public/_headers` wird automatisch mitgeliefert:
- `index.html` wird nie gecacht → neuer Code ist sofort sichtbar.
- `assets/` (Dateinamen mit Hash) ein Jahr gecacht; Kacheln/Modelle/Texturen einen Tag (danach im Hintergrund aktualisiert).
- `X-Robots-Tag: noindex` hält die Seite während der Testphase aus Suchmaschinen. **Vor dem öffentlichen Launch diese Zeile (und `/*` darüber) entfernen.**

Soll eine Kartenänderung sofort überall sichtbar sein: Cloudflare-Dashboard → Caching → «Purge Everything» (nur falls eine eigene Domain mit Cloudflare-Cache verbunden ist; `*.pages.dev` aktualisiert sich mit jedem Deploy).

## Zugang beschränken (Testphase, optional)
Dashboard → Workers & Pages → Projekt → Settings → «Access Policy» aktivieren. Unter Zero Trust die E-Mail-Adressen der Testpersonen eintragen; sie erhalten beim Öffnen einen Code per Mail (gratis bis 50 Personen).

## Eigene Domain (optional, später)
Dashboard → Projekt → Custom domains → Domain eintragen und den angezeigten DNS-Eintrag bei deinem Domain-Anbieter setzen (oder die Domain zu Cloudflare umziehen).

## Kontrolle nach dem Upload
1. Auf dem Handy öffnen (iPhone und Android, WLAN und Mobilnetz): lädt in wenigen Sekunden, läuft flüssig, Joystick/⇧/E funktionieren, Karte und Uhr gehen auf.
2. Am PC: F12 → Netzwerk: keine roten Fehler (404); beim zweiten Laden kommen die meisten Dateien aus dem Cache.
3. F12 → Konsole: keine Fehlermeldungen.

## Vor dem öffentlichen Launch
- Impressum im Spiel (Menü) und auf der Website.
- Freigabe der Plakat-Inhalte (`research/posters/README.md`, Freigabeliste).
- `noindex` in `web/public/_headers` entfernen, neu bauen und hochladen.

## Probleme
- `wrangler: not logged in` → `npx wrangler login` wiederholen.
- Seite lädt, Welt bleibt leer → wurde `web/public/tiles/` gebaut? (`ls web/public/tiles | wc -l` sollte ~600 zeigen).
- Alte Version sichtbar → Browser hart neu laden (Cmd+Shift+R); `index.html` ist nicht gecacht.

## Fehler melden: GitHub-Token für den Worker
Menü → «Fehler melden» → «Absenden» schickt den Bericht an `POST /api/report`. Das ist ein kleines Worker-Script (`web/worker/index.ts`), das `wrangler deploy` automatisch neben den statischen Dateien mitnimmt (`web/wrangler.jsonc`: `main`, `assets.run_worker_first`). Es legt das Issue mit einem GitHub-Token an, das nur auf dem Worker liegt, nie im Browser. Ohne Token antwortet die Route 503 und das Spiel zeigt stattdessen den vorausgefüllten GitHub-Link; sonst ändert sich nichts.

1. **Token erstellen:** https://github.com/settings/personal-access-tokens/new → Fine-grained token, Resource owner `dgnaegi`, **Only select repositories → sandboxzurich**, Repository permissions → **Issues: Read and write** (sonst nichts). Ablaufdatum merken und rechtzeitig erneuern (Schritt 2 wiederholen). Die Issues erscheinen unter diesem Konto; die erste Zeile («Aus dem Spiel gemeldet») und das Label `bug` kennzeichnen sie. Wer das nicht will, nimmt ein eigenes Bot-Konto mit Schreibrecht auf das Repo.
2. **Token hinterlegen,** eine der beiden Varianten:
   - GitHub Actions: Repo → Settings → Secrets and variables → Actions → New repository secret `REPORT_GITHUB_TOKEN`. Der Deploy-Workflow schreibt es nach jedem Deploy mit `wrangler secret put` in den Worker (Schritt «Report token»; ohne Secret wird er übersprungen). Nächster Push auf `main` oder «Run workflow» aktiviert es.
   - Lokal: `cd web && npx wrangler secret put REPORT_GITHUB_TOKEN` (Token einfügen). Secrets überleben spätere Deploys.
3. **Prüfen:** Spiel öffnen → Menü → Fehler melden → kurzer Text → Absenden. Es erscheint «Danke! Dein Bericht ist jetzt Fehler #N» mit Link; das Issue steht unter https://github.com/dgnaegi/sandboxzurich/issues.

Missbrauchsschutz: nur Anfragen von der eigenen Seite (Origin), höchstens 16 KB, 3 Meldungen pro Minute und IP, 20 pro Minute insgesamt (Rate-Limit-Bindings in `wrangler.jsonc`, pro Cloudflare-Standort gezählt). Reicht das nicht, Cloudflare Turnstile vor den Knopf setzen oder das Secret löschen (`npx wrangler secret delete REPORT_GITHUB_TOKEN`): Dann gilt sofort wieder nur der GitHub-Link.

Lokal testen (Wrangler braucht Node ≥ 22): `cp web/.dev.vars.example web/.dev.vars`, Token eintragen (für Tests besser `REPORT_REPO=<eigener Fork>` dazu), dann `cd web && npm run build && npx wrangler dev` → http://localhost:8787. Der Vite-Dev-Server (`npm run dev`) hat die Route nicht; dort zeigt «Absenden» den Fehler und den GitHub-Link. Tests: `node tests/report_api.mjs` (Worker mit gestubbter GitHub-API, ohne Cloudflare) und `node tests/report_ui.mjs` (Seite im Spiel, Route gemockt).
