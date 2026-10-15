# Roadmap

Jedes Milestone endet mit etwas, das der User im Browser (auch auf dem Handy) ausprobieren kann.

## M0 – Projektstruktur ✅
- [x] Unterordner `game/` mit Projektbeschreibung und Doku-Struktur
- [x] Git-Repo `dgnaegi/sandboxzurich`, Lizenz WTFPL
- [x] OSM-Bestandsaufnahme (`research/osm_stats.md`)
- [ ] Scalingo: separater Schritt (später)

## M1 – Karte und Herumlaufen (nächster Auftrag)
**Ziel:** Ein Gebiet in Kreis 4/5 originalgetreu, darin frei herumlaufen, flüssig auf dem Handy.
- [x] Gebiet und Kachelraster festlegen; Rohdaten für alle vier Kreise laden (Spielgebiet K4/K5 + Teile K9/K3, 279 Kacheln, Baustellenzaun)
- [ ] POI-Recherche: OSM-Läden und -Cafés exportieren, per Web prüfen, `research/pois_*.csv`
- [ ] Velo-Daten: Velovorzugsrouten und Velonetz (Stadt ZH OGD)
- [x] Strassen v2: Decal-Ausrichtung korrigiert, Velo-Piktogramm neu, Spurpfeile, rote Flächen (Orthofoto), Tram-Inseln, Baustellen sperren Spuren
- [x] Pipeline: Gebäude, Boden, Strassen inkl. Markierungen, Tram, Bäume → Kacheln (+ Brücken, Bahn, Amtliche Vermessung, Platz-/Strassenschilder)
  - [x] Arcade-Look: Textur-Array, Fassaden, Randsteine, Markierungen, Autos, Lampen
  - [x] Durchstich Testgebiet Langstrasse/Helvetiaplatz (Gebäude, Boden, Strassen, Tram, Bäume; ohne Markierungen)
- [x] Web-App: Kachel-Streaming, Third-Person-Kamera, Laufen (Tastatur und Touch-Joystick), Kollision (Touch noch auf echtem Gerät testen)
- [ ] Ladenschilder mit echten Namen (Code fertig, wartet auf vollständige OSM-POIs)
- [x] Radar/Minimap und Stadtkarte mit Sprungpunkten
- [x] Performance-Messung gegen die Budgets (2026-10-15: Handy ≤231 Calls, ≤1.1 Mio; PC ≤458 Calls, ≤2.9 Mio)
- [ ] Screenshots an Landmarks → `preview/`, QA gegen Referenzfotos
- [ ] Deploy auf Scalingo (Testlink)

## M2 – Lebendige Stadt
- [x] Trams und Busse auf echten Linien (Testgebiet)
- [x] Autos, Velos, Fussgänger:innen (Testgebiet)
- [x] Tag/Nacht, Licht
- [ ] Kreis 3 und 9 in voller Ausdehnung

## M3 – Gameplay-Grundlagen
- [ ] Zerstörbare Objekte
- [x] Sterne-System, Polizei (comichaft)
- [x] Velo fahren (klauen, fahren, absteigen)
- [x] Auto klauen und fahren (parkiert + Verkehr, Physik, Kollision, Lichter), Auto-/Velo-Realismus v2 (DECISIONS #30)
- [x] HUD wie im Reel, Menüs, Credits, Impressum (Impressum-Verantwortliche TODO)

## M4 – Quests
- [ ] Q1–Q3 ausarbeiten und umsetzen, danach weitere
- [ ] Kandidierende als NPCs (nach Einwilligung)

## M5 – Launch
- [ ] Tests auf echten Geräten, Ladezeit, Feinschliff
- [ ] Inhaltliche Abnahme durch die Kampagne
- [ ] Launch vor den Wahlen 2027 (Datum prüfen)
