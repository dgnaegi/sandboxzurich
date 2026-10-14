# OSM-Bestand Kreise 3, 4, 5, 9 (Abfrage 2026-10-14)

OSM-Relationen: Kreis 3 = 1694010, Kreis 4 = 1694184, Kreis 5 = 1695424 («Industriequartier»), Kreis 9 = 1701558.
Vereinfachte Polygone (WGS84, lat/lon): `kreise_poly_simplified.json`.
Gesamt-BBox: 47.3364–47.4039 N, 8.4480–8.5390 E.

| | K3 | K4 | K5 | K9 | Total |
|---|---:|---:|---:|---:|---:|
| Fläche km² | 8.65 | 2.90 | 1.99 | 12.07 | 25.6 |
| Gebäude | 5532 | 2275 | 1395 | 6897 | 16099 |
| Läden (shop=*) | 440 | 524 | 293 | 340 | 1597 |
| Gastro (Café/Rest./Bar/Pub/Take-away/Glace/Club) | 210 | 403 | 239 | 140 | 992 |
| davon amenity=cafe | 36 | 45 | 32 | 24 | 137 |
| Strassen-Ways | 711 | 546 | 410 | 751 | 2418 |
| Velostreifen-Ways (cycleway=lane/track) | 200 | 202 | 123 | 205 | 730 |
| Velowege (highway=cycleway) | 113 | 40 | 68 | 135 | 356 |
| Tramgleis-Ways | 61 | 126 | 50 | 75 | 312 |
| Einzelbäume | 3972 | 2437 | 1687 | 4642 | 12738 |
| Fussgängerstreifen | 717 | 485 | 300 | 728 | 2230 |
| Lichtsignale | 109 | 101 | 88 | 132 | 430 |
| Brunnen (drinking_water) | 112 | 59 | 32 | 99 | 302 |
| Bänke | 992 | 449 | 453 | 934 | 2828 |
| Laternen | 400 | 101 | 23 | 297 | 821 |
| Adressen | 5705 | 3491 | 2097 | 6707 | 18000 |

## Folgerungen
- Läden und Gastro sind gut erfasst; fast alle Läden haben einen Namen. Cafés sind oft anders getaggt, deshalb ist ein Web-Abgleich nötig.
- Laternen sind lückenhaft erfasst und werden prozedural entlang der Strassen gesetzt.
- Velovorzugsrouten fehlen in OSM als eigene Kategorie. Sie kommen aus dem Datensatz «Velonetzplanung» der Stadt Zürich (opendata.swiss, JSON/GPKG/WFS).
- Kreis 3 und 9 enthalten Wald und Hänge (Friesenberg, Uetliberg-Fuss). Dort ist nur Kulisse nötig.
