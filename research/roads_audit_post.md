# Strassen-Audit (post)

Messung entlang aller OSM-Achsen (ohne Brücken/Tunnel/Service), 1-m-Schritte, Höhe = H.at wie im Build.
Schwellen: Steigung > 8% (über 4 m), Sprung > 0.25 m auf 1 m, 2. Differenz > 0.1 m über 3 m.

## Zusammenfassung

| Kennzahl | Wert |
|---|---|
| mode | post |
| axis_km | 83.9 |
| events | 32 |
| events_per_km | 0.38 |
| slope>8% | 26 |
| jump>0.25 | 10 |
| curv | 22 |
| rough_rms_mean | 0.011 |
| sharp_corners<50deg | 21 |
| holes<400m2 | 354 |
| axis_gaps | 0 |

## Top 30 Höhenstellen

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

## Spitze Polygonecken (< 50 Grad), 15 schärfste

- (452, 651) 0 Grad
- (1250, -57) 0 Grad
- (859, -431) 0 Grad
- (-12, 824) 0 Grad
- (177, -307) 0 Grad
- (-497, -641) 1 Grad
- (-540, 893) 1 Grad
- (1284, -94) 1 Grad
- (393, 735) 1 Grad
- (486, -810) 1 Grad
- (-1738, 236) 1 Grad
- (946, -916) 1 Grad
- (80, 290) 1 Grad
- (1174, 34) 1 Grad
- (-149, 869) 2 Grad

## Löcher in der Fahrbahn (< 400 m2)

- (1935, -772) 131 m2
- (1933, -764) 71 m2
- (1933, 182) 0 m2
- (1883, -756) 363 m2
- (1870, -605) 137 m2
- (1849, -592) 109 m2
- (1853, -600) 102 m2
- (1831, -940) 0 m2
- (1800, -596) 329 m2
- (1789, 450) 0 m2
- (1799, 535) 83 m2
- (1786, 26) 245 m2
- (1706, 785) 323 m2
- (1719, 755) 53 m2
- (1685, 803) 72 m2

## Achsen ohne Fahrbahn (nicht-Brücke, nach Brücken-Exklusion)

