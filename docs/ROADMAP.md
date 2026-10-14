# Roadmap

Jedes Milestone endet mit etwas, das der User im Browser (auch auf dem Handy) ausprobieren kann.

## M0 – Projektstruktur ✅
- [x] Unterordner `game/` mit Projektbeschreibung und Doku-Struktur
- [x] Git-Repo `dgnaegi/gtazurich`, Lizenz WTFPL
- [x] OSM-Bestandsaufnahme (`research/osm_stats.md`)
- [ ] Scalingo: separater Schritt (später)

## M1 – Karte und Herumlaufen (nächster Auftrag)
**Ziel:** Ein Gebiet in Kreis 4/5 originalgetreu, darin frei herumlaufen, flüssig auf dem Handy.
- [ ] Gebiet und Kachelraster festlegen; Rohdaten für alle vier Kreise laden
- [ ] POI-Recherche: OSM-Läden und -Cafés exportieren, per Web prüfen, `research/pois_*.csv`
- [ ] Velo-Daten: Velovorzugsrouten und Velonetz (Stadt ZH OGD)
- [ ] Pipeline: Gebäude, Boden, Strassen inkl. Markierungen, Tram, Bäume → Kacheln
- [ ] Web-App: Kachel-Streaming, Third-Person-Kamera, Laufen (Tastatur und Touch-Joystick), Kollision
- [ ] Ladenschilder mit echten Namen
- [ ] Radar/Minimap
- [ ] Performance-Messung gegen die Budgets
- [ ] Screenshots an Landmarks → `preview/`, QA gegen Referenzfotos
- [ ] Deploy auf Scalingo (Testlink)

## M2 – Lebendige Stadt
- [ ] Trams und Busse auf echten Linien
- [ ] Autos, Velos, Fussgänger:innen
- [ ] Tag/Nacht, Licht
- [ ] Kreis 3 und 9 in voller Ausdehnung

## M3 – Gameplay-Grundlagen
- [ ] Zerstörbare Objekte, Sterne-System, Polizei
- [ ] Velo fahren
- [ ] HUD wie im Reel, Menüs, Credits, Impressum

## M4 – Quests
- [ ] Q1–Q3 ausarbeiten und umsetzen, danach weitere
- [ ] Kandidierende als NPCs (nach Einwilligung)

## M5 – Launch
- [ ] Tests auf echten Geräten, Ladezeit, Feinschliff
- [ ] Inhaltliche Abnahme durch die Kampagne
- [ ] Launch vor den Wahlen 2027 (Datum prüfen)
