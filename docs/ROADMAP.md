# Roadmap

Jedes Milestone endet mit etwas, das der User im Browser (auch auf dem Handy) ausprobieren kann.

## M0 – Projektstruktur ✅
- [x] Unterordner `game/` mit Projektbeschreibung und Doku-Struktur
- [x] Git-Repo `dgnaegi/sandboxzurich`, Lizenz WTFPL
- [x] OSM-Bestandsaufnahme (`research/osm_stats.md`)
- [x] Hosting: Cloudflare Workers, Auto-Deploy bei Push (`docs/DEPLOY.md`, 2026-10-16)

## M1 – Karte und Herumlaufen (nächster Auftrag)
**Ziel:** Ein Gebiet in Kreis 4/5 originalgetreu, darin frei herumlaufen, flüssig auf dem Handy.
- [x] Gebiet und Kachelraster festlegen; Rohdaten für alle vier Kreise laden (Spielgebiet K4/K5 + Teile K9/K3, 279 Kacheln, Baustellenzaun)
- [x] POI-Recherche: `research/pois_*.csv`, Lokale mit Foto-Notizen `research/shops_v3/` (349 von 1100)
- [ ] Velo-Daten: Velovorzugsrouten und Velonetz (Stadt ZH OGD)
- [x] Strassen v2: Decal-Ausrichtung korrigiert, Velo-Piktogramm neu, Spurpfeile, rote Flächen (Orthofoto), Tram-Inseln, Baustellen sperren Spuren
- [x] Pipeline: Gebäude, Boden, Strassen inkl. Markierungen, Tram, Bäume → Kacheln (+ Brücken, Bahn, Amtliche Vermessung, Platz-/Strassenschilder)
  - [x] Arcade-Look: Textur-Array, Fassaden, Randsteine, Markierungen, Autos, Lampen
  - [x] Durchstich Testgebiet Langstrasse/Helvetiaplatz (Gebäude, Boden, Strassen, Tram, Bäume; ohne Markierungen)
- [x] Web-App: Kachel-Streaming, Third-Person-Kamera, Laufen (Tastatur und Touch-Joystick), Kollision (Touch noch auf echtem Gerät testen)
- [x] Ladenschilder mit echten Namen, Fronten nach Fotos (Ladenfronten v3)
- [x] Radar/Minimap und Stadtkarte mit Sprungpunkten
- [x] Performance-Messung gegen die Budgets (2026-10-15: Handy ≤231 Calls, ≤1.1 Mio; PC ≤458 Calls, ≤2.9 Mio)
- [x] Screenshots an Landmarks → `preview/`, QA gegen Referenzfotos (`preview/lm3_*`, `lm4_*`, `lm5_*`, `qa_night*`)
- [x] Plätze/Parks v3: Bodenbelag, Möblierung, Brunnen/Kiosk/Fahnenmasten an 15 Plätzen (`places_detail`, `preview/plaza3_*.jpg`)
- [x] Deploy (Testlink): https://sandboxzurich.sandboxzurich-web.workers.dev

## M2 – Lebendige Stadt
- [x] Trams und Busse auf echten Linien (Testgebiet)
- [x] Autos, Velos, Fussgänger:innen (Testgebiet)
- [x] Tag/Nacht, Licht
- [ ] Kreis 3 und 9 in voller Ausdehnung

## M3 – Gameplay-Grundlagen
- [ ] Zerstörbare Objekte
- [x] Sterne-System, Polizei (comichaft)
- [x] Velo fahren (klauen, fahren, absteigen)
- [x] Autos v3 (Loft, Scheiben, Kontrollschild, csuv/taxi, Ausweichen) – DECISIONS #31
- [x] Auto klauen und fahren (parkiert + Verkehr, Physik, Kollision, Lichter), Auto-/Velo-Realismus v2 (DECISIONS #30)
- [x] HUD wie im Reel, Menüs, Credits, Impressum (Impressum-Verantwortliche TODO)

## M4 – Quests
- [ ] Q1–Q3 ausarbeiten und umsetzen, danach weitere
- [ ] Echte Personen als NPCs (nur nach schriftlicher Einwilligung)

## M5 – Launch
- [ ] Tests auf echten Geräten, Ladezeit, Feinschliff
- [ ] Inhaltliche Abnahme
- [ ] Launch (Datum offen)
