# Strassen-Audit: vorher / nachher

Skript: `pipeline/roads_audit.py` (`--post` = mit `road_height.py`, Brücken-Exklusion mit Durchfahrten, `streets.tidy_roads`). Messung entlang aller OSM-Achsen im Spielgebiet (ohne Brücken/Tunnel/Service), 1-m-Schritte. Schwellen: Steigung > 8 % (über 4 m), Sprung > 0.25 m auf 1 m, 2. Differenz > 0.10 m über 3 m.

| Kennzahl | vorher | nachher |
|---|---|---|
| axis_km | 83.9 | 83.9 |
| events | 325 | 32 |
| events_per_km | 3.88 | 0.38 |
| slope>8% | 24 | 26 |
| jump>0.25 | 10 | 10 |
| curv | 318 | 22 |
| rough_rms_mean | 0.0397 | 0.011 |
| sharp_corners<50deg | 1077 | 21 |
| holes<400m2 | 607 | 354 |
| axis_gaps | 20 | 0 |

Hinweis: «holes<400m2» zählt auch echte Verkehrsinseln/Häuserblöcke in der Strassenfläche (nicht nur Fehler). «axis_gaps» nachher ohne Brückenketten gezählt (vorher mit).

Karte: `preview/roads_audit_map.jpg` (vorher), `preview/roads_audit_map_post.jpg` (nachher); rot = Score > 2, blau = spitze Ecke.

Fahrtest (`web/tests/roads_ride.mjs`, 8 m/s, vertikale Beschleunigung der Fahrhöhe, nur Bodenabschnitte): Bullingerstrasse rms 17.2 → 4.2 m/s2 (max 96 → 20), Zweierstrasse 0.38 → 0.28 (flach, vorher OK), Hohlstrasse nur Brücke/Unterführung (keine Bodenstrecke).

## Top 30 vorher

| # | x | y | Strasse | Art | Score | Steigung | Sprung | d2 |
|---|---|---|---|---|---|---|---|---|
| 1 | -546 | -258 | Bullingerstrasse | slope+jump+curv | 55.7 | 70.5% | 0.26 | -5.57 |
| 2 | 1172 | -1177 | Sihlbrücke | slope+jump+curv | 32.8 | 47.9% | 0.73 | -3.28 |
| 3 | 451 | -1341 | Zweierstrasse | slope+jump+curv | 32.5 | 65.6% | 0.89 | -3.25 |
| 4 | 357 | -483 | Hohlstrasse | slope+jump+curv | 26.5 | 31.9% | 0.30 | -2.65 |
| 5 | 203 | -736 | Kanzleistrasse | slope+curv | 22.7 | 42.4% | 0.15 | -2.27 |
| 6 | -605 | 142 | Duttweilerbrücke | slope+curv | 20.6 | 34.8% | 0.03 | +2.06 |
| 7 | -601 | 138 | Duttweilerbrücke | slope+curv | 20.3 | 42.2% | 0.15 | -2.03 |
| 8 | 320 | -459 | Hohlstrasse | slope+curv | 19.4 | 25.9% | 0.01 | -1.94 |
| 9 | 1088 | -14 | Heinrichstrasse | jump+curv | 18.6 | 5.1% | 0.36 | -1.86 |
| 10 | 183 | -1000 | Badenerstrasse | slope+jump+curv | 16.3 | 37.2% | 0.28 | -1.63 |
| 11 | 324 | -445 | Hohlstrasse | slope+jump+curv | 15.8 | 19.4% | 0.32 | -1.58 |
| 12 | 894 | -1653 | Manessestrasse | slope+curv | 15.2 | 13.7% | 0.08 | -1.52 |
| 13 | 360 | -469 | Hohlstrasse | slope+jump+curv | 15.0 | 85.1% | 0.99 | +1.50 |
| 14 | 170 | -719 | Kanzleistrasse | slope+curv | 15.0 | 21.9% | 0.00 | -1.50 |
| 15 | -552 | -255 | Bullingerstrasse | curv | 14.2 | 0.4% | 0.00 | +1.42 |
| 16 | 231 | -608 | Stauffacherstrasse | slope+jump+curv | 13.0 | 33.3% | 0.41 | -1.30 |
| 17 | 933 | -276 | Langstrasse | curv | 12.9 | 6.2% | 0.06 | +1.29 |
| 18 | 261 | -1157 | Kalkbreitestrasse | slope+curv | 11.2 | 12.2% | 0.16 | -1.12 |
| 19 | -516 | -276 | Bullingerstrasse | curv | 10.8 | 0.5% | 0.00 | +1.08 |
| 20 | -523 | -272 | Bullingerstrasse | curv | 8.5 | 0.5% | 0.03 | -0.85 |
| 21 | 260 | -623 | Stauffacherstrasse | slope+jump | 8.5 | 68.0% | 0.68 | +0.06 |
| 22 | 1168 | -1186 | Sihlbrücke | curv | 8.0 | 3.0% | 0.01 | -0.80 |
| 23 | 1392 | -834 | Gessnerbrücke | curv | 7.8 | 6.2% | 0.01 | -0.78 |
| 24 | -410 | 582 | Duttweilerbrücke | curv | 6.3 | 1.2% | 0.01 | -0.63 |
| 25 | 424 | -944 | Schreinerstrasse | curv | 3.9 | 1.1% | 0.08 | -0.39 |
| 26 | -200 | -145 | Hardbrücke | curv | 3.7 | 2.8% | 0.06 | -0.37 |
| 27 | 877 | -1364 | Werdgässchen | curv | 3.6 | 1.5% | 0.01 | +0.36 |
| 28 | 268 | -627 | Stauffacherstrasse | curv | 3.6 | 0.6% | 0.00 | -0.36 |
| 29 | 485 | 806 | Wipkingerbrücke | curv | 3.5 | 3.4% | 0.03 | -0.35 |
| 30 | 216 | -1011 | Badenerstrasse | curv | 3.4 | 2.9% | 0.00 | -0.34 |

## Top 30 nachher (alle übrigen sind echte Unterführungen/Rampen)

| # | x | y | Strasse | Art | Score | Steigung | Sprung | d2 |
|---|---|---|---|---|---|---|---|---|
| 1 | -546 | -259 | Bullingerstrasse | slope+jump+curv | 18.3 | 51.4% | 0.65 | -1.83 |
| 2 | 357 | -483 | Hohlstrasse | slope+jump+curv | 14.8 | 34.9% | 0.41 | -1.48 |
| 3 | -516 | -276 | Bullingerstrasse | slope+jump+curv | 13.0 | 29.3% | 0.38 | +1.30 |
| 4 | 324 | -445 | Hohlstrasse | slope+jump+curv | 7.7 | 22.5% | 0.28 | -0.77 |
| 5 | 1171 | -1176 | Sihlbrücke | slope+curv | 6.8 | 17.9% | 0.21 | -0.68 |
| 6 | 323 | -461 | Hohlstrasse | slope+jump+curv | 6.3 | 38.6% | 0.39 | -0.63 |
| 7 | 359 | -468 | Hohlstrasse | slope+jump | 6.1 | 49.0% | 0.52 | +0.08 |
| 8 | 231 | -608 | Stauffacherstrasse | slope+jump+curv | 5.7 | 33.6% | 0.35 | -0.57 |
| 9 | 262 | -624 | Stauffacherstrasse | slope+jump | 5.2 | 41.8% | 0.42 | +0.01 |
| 10 | 261 | -1157 | Kalkbreitestrasse | slope+jump+curv | 4.9 | 22.1% | 0.26 | -0.49 |
| 11 | -553 | -254 | Bullingerstrasse | slope+curv | 4.9 | 14.8% | 0.12 | +0.49 |
| 12 | 202 | -735 | Kanzleistrasse | slope+curv | 4.3 | 24.1% | 0.21 | -0.43 |
| 13 | 1168 | -1186 | Sihlbrücke | slope+curv | 4.2 | 13.2% | 0.06 | -0.42 |
| 14 | -602 | 140 | Duttweilerbrücke | slope+jump | 3.7 | 29.4% | 0.27 | -0.05 |
| 15 | -607 | 136 | Duttweilerbrücke | slope+curv | 3.4 | 16.6% | 0.18 | -0.34 |
| 16 | 269 | -628 | Stauffacherstrasse | slope+curv | 3.1 | 10.2% | 0.08 | -0.31 |
| 17 | 166 | -716 | Kanzleistrasse | slope+curv | 2.9 | 13.1% | 0.11 | -0.29 |
| 18 | 451 | -1340 | Zweierstrasse | slope | 2.4 | 19.4% | 0.21 | +0.00 |
| 19 | 1392 | -834 | Gessnerbrücke | slope+curv | 2.4 | 14.2% | 0.12 | -0.24 |
| 20 | 366 | -478 | Hohlstrasse | curv | 2.2 | 1.2% | 0.03 | -0.22 |
| 21 | 316 | -446 | Hohlstrasse | curv | 2.1 | 4.6% | 0.10 | -0.21 |
| 22 | 98 | -1735 | Schlossgasse | slope | 1.6 | 12.8% | 0.13 | +0.00 |
| 23 | 83 | -1739 | Wiedingstrasse | slope+curv | 1.5 | 9.3% | 0.08 | +0.15 |
| 24 | 58 | -1712 | Zweierstrasse | slope | 1.5 | 12.2% | 0.12 | -0.00 |
| 25 | 315 | -440 | Hohlstrasse | curv | 1.5 | 1.5% | 0.02 | -0.15 |
| 26 | 82 | -1761 | Wiedingstrasse | slope | 1.3 | 10.7% | 0.11 | +0.01 |
| 27 | 180 | -999 | Badenerstrasse | slope | 1.3 | 10.1% | 0.10 | +0.02 |
| 28 | 227 | -601 | Seebahnstrasse | curv | 1.2 | 2.3% | 0.03 | -0.12 |
| 29 | 222 | -610 | Seebahnstrasse | curv | 1.2 | 2.0% | 0.01 | -0.12 |
| 30 | 216 | -1011 | Badenerstrasse | slope | 1.1 | 8.5% | 0.09 | +0.02 |

Hinweis: Hohl-/Bullinger-/Stauffacherstrasse und Kalkbreite sind echt abgesenkte Unterführungen (swissALTI3D); das geglättete Profil darf höchstens 1 m vom Gelände abweichen, damit die Unterführung bleibt.
