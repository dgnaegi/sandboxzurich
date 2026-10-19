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

## T22 / T23 Nachtrag (Agent Z2B, 2026-10-19)
Messung wie oben auf den Testkacheln mit Funden (9 Kacheln: Hohl-/Bullinger-/Förrlibuck-/Seebahn-/Badenerstrasse, Kornhausbrücke; 16 km Achsen), vorher = Build 14, nachher = Testkacheln mit den Fixes (`audit_bumps.py --tiles … --out`):
| | vorher | nachher |
|---|---|---|
| Strassenbuckel > 8 cm | 9 | 7 |
| davon > 15 cm | 3 | 1 (Kornhausbrücke 20 cm) |
| Rampenknicke auf Strassen (Portale) | 3 (27/25/19 cm) | 0 |
Höhenraster nach `road_height` (Achsen, Stufe > 22 % auf 3 m, Spielgebiet): 16 Stellen -> 10 (Bullinger, Kanzleistrasse, Sihlbrücke, Duttweilerbrücke verschwinden; Rest sind Brücken-/Brückenrampen).
- **T22 Ursache:** die 35 m lange Bullingerstrasse zwischen (-549,-257) und (-492,-290) ist in OSM nicht als Tunnel getaggt, geht aber unter dem Bahndamm durch (Strasse -3.0 m, DTM +4.2 m, Klippen 3-6 m). `road_height` hielt das Profil innerhalb ±1 m am Gelände, `MAX_FILL`/`MAX_SHAVE` kappten die Zellen -> Rampe über den Damm mit 64-100 % Neigung. Fix: `pipeline/underpass_infer.py` (Plateau <= 90 m, >= 1.2 m über beiden Portalen, Klippen >= 1.5 m / 3 m, zusammengefügte Strassenzüge) + `road_height.carve_underpasses` (Gelände auf die Gerade zwischen den Portalhöhen, Korridor Fahrbahn + 1 m, 2 m Wand, nur absenken, vor der Profilglättung). Erkannt im ganzen Gebiet: Bullingerstrasse 40 m, Wasserwerkstrasse (1604,81) 20 m, (1702,-25) 9 m, Ackersteinstrasse (-1114,1740) 10 m. Schienen sind unabhängig (`rail_z`, nicht `H`).
  Nicht behoben: Badenerstrasse (178,-998) war ein T23-Fall (0.24 m Delle -> 0.03, siehe unten); echte Mulden unter Brücken (Seebahnstrasse (219,-613), Stauffacherstrasse, Kanzleistrasse (198,-734), Sihlbrücke): die Strasse läuft dort ohne OSM-Brückentag über einen Graben; ein Damm würde die Gleise darunter verschütten, es braucht ein Brückendeck (bridges.py). Neigung dort 0.57 -> 0.32.
- **T23 Ursache (anders als im Ticket vermutet, nicht die DTM-Spitzen):** der Asphalt wird pro 6-m-Zelle nur mit den Eckpunkten des Fahrbahnpolygons trianguliert (`mesh.drape`, earcut ohne Innenpunkte). Die Höhe an der Polygonkante kam aus `road_height.apply`, wo `MAX_FILL = 1.2 m` Zellen neben einer Mulde / einem Einschnitt nicht bis Strassenniveau füllen liess (Hohlstrasse: Kante 20-42 cm tiefer als Strassenmitte). Folge: schräge Dreiecke und 10-20-cm-Dellen an der Achse. Fix: `MAX_FILL_IN = 3.0` m für Zellen innerhalb der Fahrbahn (`cov > 0.9`), ausserhalb bleibt 1.2 m (Brückenschutz aus roads2). Zusätzlich ist der Korridor jetzt so breit wie das gezeichnete Fahrbahnpolygon (`_local_halfwidth`, Raster-EDT, höchstens +5 m über der OSM-Breite). Kante-minus-Achse an der Hohlstrasse: -0.42…-0.04 m -> -0.01…0.00 m. Der Fix gilt für den ganzen Build.
- Rest: Kornhausbrücke (1191,135) 20 cm (Brückenrampe, DTM-Absatz), Förrlibuckstrasse (-405,837) 14-15 cm und (-475,849) 11 cm (Einmündung Servicestrasse, Strassen auf anderem Niveau überlappen), Seebahnstrasse (231,-595) 14 cm.
