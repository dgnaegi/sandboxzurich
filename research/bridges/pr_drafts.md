# PR-Entwürfe für `dgnaegi/sandboxzurich` (nicht eröffnet; der User entscheidet)

Zwei getrennte PRs, in dieser Reihenfolge. Beide tragen Code, Tests, Research-Protokolle; nichts unter `docs/`, keine
Kachel-JSON (der Maintainer baut selbst), keine Bilder. Zahlen und Stand: `research/bridges/scopes/README.md`.

## PR A: Brückenfahrt als Release-Gate, Dev-Proxy für Live-Weltdaten (klein, heute reif)

**Was:** `node tests/bridges_ride.mjs qa --gate` vergleicht den Lauf fahrtweise mit `web/tests/fixtures/bridges_ride_baseline.json`
und schlägt nur bei Regression fehl (`--accept` schreibt eine neue Baseline, `qa_all.sh` ruft das Gate auf). `web/vite.config.ts`
liefert mit `VITE_WORLD_PROXY=<Deploy-URL>` Kacheln, Texturen, Karte und Ladebilder der Live-Seite aus, lokal vorhandene
`tiles/*.json` gewinnen (Forks ohne gebaute Weltdaten können den Client testen). Ohne die Variable unverändert.

**Warum:** Roadmap-Fokus «Brücken-, Rampen- und Geländefehler stadtweit» braucht ein Gate, das Verbesserungen von Regressionen
trennt; der bekannte Rückstand (48 von 97 Fahrten mit Befund) soll neue Brüche nicht verdecken.

**Testen:** `cd web && VITE_WORLD_PROXY=https://sandboxzurich.sandboxzurich-web.workers.dev npx vite --port 5190`, dann
`node tests/bridges_ride.mjs qa "" car,bike,foot http://localhost:5190 --gate` → `GATE PASS` gegen die mitgelieferte Baseline.

**Entscheid-Vorschlag:** R1 in `research/bridges/ramps_decisions_proposed.md`.

## PR B (Draft / RFC): Rampen aus Referenz-Scopes bauen und messen (`pipeline/scopes/`)

**Was:** Je Rampe werden die Deck-Zeilen aus der Amtlichen Vermessung (OGD-WFS: Brückenpolygone, dünne Randpolygone, Mauern,
Pfeiler) und den LiDAR-Rastern neu gebaut (`ramp_build.py`), und jede Rampe bekommt einen Report mit Zahlen je Scope, Overlay
und PASS/REVIEW gegen feste Schwellen (`score.py`, `overlay.py`). Übergänge zu Hauptdecks werden geöffnet (`join.py`), Pfeiler
stehen an Kataster-Positionen, Böschungen und Widerlager werden massiv, Landungen folgen dem Strassengraph bis zum Boden.
Protokolle: `research/bridges/scopes/README.md` (Einstieg, Status je Vektor, Zahlen, Einordnung), `<site>.md` je Rampe,
`ramps_handoff.md` (Sitzungen), `ramps_decisions_proposed.md` (R2, R3).

**Stand bei Eröffnung:** drei Rampen (Geroldrampe, Duttweilerbrücke Süd, Hohlstrasse/Brauerstrasse); Zahlen im README.
Arbeitet heute auf den gebauten Kachel-JSON (Post-Processing), weil der Fork keine Rohdaten hat. Vorschlag zur Integration:
Stufe nach `bridges.py` im Komplett-Build (AV und LiDAR sind dort vorhanden), Reports als `research/bridges/scopes/<site>.md`,
Gate-Baseline mit den neuen Zeilen akzeptieren.

**Was es nicht ist:** kein Vision-Helfer (Scope C bleibt Vorschlag in `scopes_plan.md`), keine Site-Erkennung (Liste in
`ramp_sites.py`), kein Geländepass (Residuen werden nur ausgewiesen).

**Warum als Draft:** die Regelmenge ist auf drei Rampen gewachsen; «alle Rampen» ist erst belegt, wenn weitere Rampen ohne neue
Regel durchlaufen. Rückmeldung erwünscht zu: Integrationsstufe, Schwellen, Stil der Reports.

### Englische Kurzfassung (Entwurf des Users, sachlich abgeglichen am 2026-11-01)

A helper tool: a builder for bridge ramps. The builder script combines the available reference data (Kanton Zürich cadastre via
OGD-WFS for the outline, piers and walls; the Kanton Zürich LiDAR for heights; the OSM axis stays for traffic) into a good-enough
ramp, and a scorer measures every build against the same data so that future builds can be rated without an agent in the loop:
PASS ships unseen, REVIEW names the failing measure for a person. Claude built the builder on two example ramps, comparing each
build against the sources and refining builder and scorer together, then ran it unchanged on a third ramp.

- V1, LiDAR only: heights are right, but a ramp's outline, its supports and its landing cannot be read from LiDAR alone; the
  result was only slightly better than the live rows.
- V2, cadastre added: the big step. Outline, piers, walls and landings come from the cadastre, heights from LiDAR; outline IoU
  0.35 → 0.91, 0.43 → 0.99, 0.53 → 0.99 on the three ramps, all cadastre piers at their real positions, the ride gate improves
  city-wide (stuck 14 → 12, fell 2 → 1).
- V2 joins: the pipeline only joined side-by-side decks; a ramp meeting a deck at an angle was cut by the deck's parapet. The
  builder now opens the main deck over the ramp mouth and joins fork branches as one surface; cars drive up the Geroldrampe
  onto the Hardbrücke without a crash.
- Status: two of three ramps PASS, one REVIEW for a named reason (the deck area between diverging branches); eight builder
  rules were added on the first two ramps, none on the third. Not included: the vision helper (documented proposal), automatic
  site discovery (a hand list), the terrain pass (residuals are reported).
