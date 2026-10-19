# Bodenschwellen-Audit (`pipeline/audit_bumps.py`)

Gemessen wird die **gerenderte** Fahrbahn: Asphalt-Dreiecke (Ebene 34) der Rohkacheln `data/build/tiles_raw/*.glb`, abgetastet alle 0.5 m entlang aller OSM-Strassenachsen
im Spielgebiet (168 km, ohne Brücken/Tunnel). Stufe: |z(s+0.75) - z(s-0.75) - 1.5 m x Steigung(±6 m)| > 8 cm. Buckel: |z - Mittel(z(s-2.5), z(s+2.5))| > 8 cm.
Rampenknick (Steigungswechsel > 10 % zwischen den 3-6 m davor/danach, Unterführungsportale) zählt nicht als Buckel. Service-Ways (Hofeinfahrten, Parkhausrampen) getrennt.
Lauf: `.venv/bin/python pipeline/audit_bumps.py [--tiles 0_1,0_0]` -> `data/build/bumps.json` (inkl. Höhenprofil je Fund).

## Ursache
`drape()` (pipeline/mesh.py) schneidet den Asphalt in Zellen und setzt **nur an Zellrändern und Polygonkanten** Eckpunkte (Höhe `H.at`). Die Strasse hatte 16-m-Zellen
(Standard): lange Dreiecke überspannten 16 m, Kuppen/Mulden/Portale des 2-m-Höhenrasters verschwanden oder wurden zu 10-30 cm tiefen Dellen
und Absätzen *zwischen* den Stützpunkten (Mesh bis 0.2 m unter `hmap`, also unter der Gehhöhe von Spieler und Fahrzeugen). Keine Fussgängerstreifen-Erhöhung,
keine Markierungsgeometrie (+8 mm) und keine Schienen sind Ursache. Kachelränder: Absätze dort sind überwiegend Messartefakt an steilen Rampen (Raster 0.5 m x Steigung 40 %).

## Fix
`ROAD_CELL` in `build_testarea.py` (Env `SBZ_ROAD_CELL`, Standard 6 statt 16 m): Asphalt-Dreiecke ~2.5x dichter, ca. +1.5k Dreiecke je Kachel (Boden 27-30k).
Versuch `road_height.snap_roads` (DTM-Spitzen im AV-Polygon einebnen): kein Gewinn (Buckel 23 -> 24), wieder entfernt.

## Zahlen (43 neu gebaute Kacheln mit Funden, gleiche Achsen, Strassen ohne Service)
| | vorher (16 m) | nachher (6 m) |
|---|---|---|
| Buckel/Stufen > 8 cm | 50 | 17 |
| davon > 15 cm | 15 | 4 |
| echte Buckel (Profil kehrt auf die Linie zurück) | 16 | 6 |
| Rampenknicke (Unterführungen, echt im DTM) | 11 | 6 |
| Service-Ways (Einfahrten) | 51 | 46 |

Gesamtgebiet vorher (alte Kacheln, 168 km): 288 Funde, davon Service 210, Rampenknicke 37, Strassenbuckel 67 (15 > 15 cm).

## Offen (Tickets T22/T23 in research/qa_round/tickets.md)
- Unterführungsportale mit 22-40 % Neigung (DTM-Graben): Badenerstrasse (178, -998), Bullingerstrasse (-527, -269), Hohlstrasse (-61, -190), Förrlibuckstrasse (-405, 837).
- Restliche Buckel 10-20 cm: Förrlibuckstrasse (-405, 837), Kornhausbrücke (1191, 135), Seebahnstrasse (219, -613) / (231, -595), Hohlstrasse (-74, -177).
- Beim Komplett-Build wirkt der Fix auf allen Kacheln (Wert ist global).
