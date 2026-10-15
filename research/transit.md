# ÖV im Testgebiet

Quelle: OpenStreetMap (ODbL), `data/raw/osm/kreise.json`, Route-Relationen route=tram/bus/trolleybus. Aufbereitung: `pipeline/transit.py` -> `web/public/data/transit.json`.

Linien (Gebiet + 300 m): Tram 8 (Stauffacher - Helvetiaplatz - Bäckeranlage), Trolleybus 31 (Sihlpost/HB), Trolleybus 32 (Kalkbreite - Kernstrasse - Helvetiaplatz). Je beide Richtungen.
Nachtlinien (N...) und Linien ohne Haltestelle im Ausschnitt werden weggelassen; mehrere Varianten pro Richtung: es gilt die mit den meisten Haltestellen.

Annahmen: Takt 7.5 min pro Linie und Richtung (Richtwert, nicht der echte Fahrplan), Tram 8 m/s, Bus 7 m/s, 20 s Halt, Versatz pro Linie per Hash. Haltestellen nur, wenn der Stop-Node <= 30 m von der zugeschnittenen Linie liegt.
