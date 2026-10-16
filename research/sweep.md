# Sweep (Vorher)

306 Kacheln, 10685 Cluster. Fehler beim Laden: 0. Quelle: `web/tests/sweep.mjs` (Szene-Abfragen, 1-m-Raster pro Kachel), `pipeline/audit_props.py` (Prop-Zeilen), `pipeline/sweep_report.py`.

## Haeufigkeit nach Typ (Cluster / Zellen m2)

| Typ | Cluster | Flaeche m2 | Ursache |
|---|---|---|---|
| ground_mismatch | 2959 | 815331 | Visible ground differs 0.25-0.7 m from tiles.ground(): player floats/sinks. Rail land: ballast drape at -0.45 (build_testarea.py _ground_base) but hmap/ground() unchanged. |
| building_no_collider | 2528 | 116839 | Roof >3.5 m above ground without footprint collider: walk through house (pipeline colliders from footprints / landmark colliders). |
| ground_hole | 1973 | 158289 | Terrain mesh (mesh_0) has no up-face within 0.7 m of tiles.ground (hmap): mesh and walk height differ, or no ground (build_testarea.py ground_tile / drape). |
| collider_no_building | 1666 | 617660 | Footprint collider without visible roof (invisible wall). |
| floating_component | 610 | 5765 | Welded mesh part of mesh_0 whose lowest vertex is >0.6 m above any support (floating geometry). |
| zfight_ground_ground | 441 | 8469 |  |
| building_on_road | 395 | 10186 | Building roof on the carriageway mask (mask vs footprint overlap). |
| buried_component | 80 | 1790 | Mesh part entirely below ground. |
| floating_over_deck | 29 | 203 | As floating_component but over a bridge deck row (deck index) - may be the bridge itself. |
| zfight_bridges_ground | 2 | 20 |  |
| zfight_ground_bridges | 2 | 24 |  |

### ground_mismatch (Top 12)

- t_2_-1 (498.9, -95.4) {'n': 33107, 'maxdz': 0.66}
- t_-5_2 (-901.6, 492.3) {'n': 32086, 'maxdz': 0.7}
- t_-1_0 (-104.6, 96.2) {'n': 30996, 'maxdz': 0.7}
- t_1_-1 (307.2, -71.2) {'n': 25587, 'maxdz': 0.7}
- t_-4_1 (-702.3, 321.2) {'n': 24620, 'maxdz': 0.7}
- t_-2_0 (-285.8, 135.8) {'n': 23189, 'maxdz': 0.7}
- t_-3_1 (-485.8, 288) {'n': 19947, 'maxdz': 0.7}
- t_-6_2 (-1085.5, 515.6) {'n': 19461, 'maxdz': 0.7}
- t_-4_2 (-712.1, 464.6) {'n': 19226, 'maxdz': 0.7}
- t_0_0 (86.4, 58.7) {'n': 18690, 'maxdz': 0.7}
- t_3_-1 (680.1, -148) {'n': 18367, 'maxdz': 0.7}
- t_-7_2 (-1311, 532.7) {'n': 17034, 'maxdz': 0.7}

### building_no_collider (Top 12)

- t_-8_1 (-1439.5, 277.1) {'n': 4656, 'h': 22.83}
- t_-5_3 (-950.8, 666.5) {'n': 1248, 'h': 14.55}
- t_-6_3 (-1074.4, 757.5) {'n': 948, 'h': 20.57}
- t_-6_3 (-1027.1, 788) {'n': 930, 'h': 11.74}
- t_-4_0 (-782.2, 100.7) {'n': 867, 'h': 10.55}
- t_0_1 (27.7, 334.8) {'n': 867, 'h': 13.33}
- t_-7_2 (-1289.4, 456.6) {'n': 824, 'h': 13.48}
- t_2_-2 (570.9, -289) {'n': 769, 'h': 9.89}
- t_-3_-2 (-415.8, -280.7) {'n': 736, 'h': 10.72}
- t_4_2 (889.5, 418.1) {'n': 641, 'h': 19.2}
- t_1_1 (246, 239.5) {'n': 594, 'h': 23.2}
- t_-3_0 (-507, 143.2) {'n': 570, 'h': 13}

### ground_hole (Top 12)

- t_5_-3 (1109.6, -441.6) {'n': 4521, 'nearest': -0.7}
- t_2_-2 (500.6, -298.2) {'n': 3672, 'nearest': -0.7}
- t_3_-2 (684.6, -278.5) {'n': 3594, 'nearest': 0.7}
- t_3_-2 (702, -309.6) {'n': 3346, 'nearest': -1}
- t_5_-2 (1131.7, -353) {'n': 3132, 'nearest': -0.7}
- t_-6_2 (-1144, 529.1) {'n': 2538, 'nearest': 0.7}
- t_4_-2 (930.8, -328.7) {'n': 2092, 'nearest': -0.8}
- t_2_-2 (572.2, -288.9) {'n': 2005, 'nearest': -1}
- t_2_-2 (446.3, -232.4) {'n': 1801, 'nearest': 0.7}
- t_0_-1 (144.5, -65.3) {'n': 1782, 'nearest': -0.9}
- t_0_0 (145.6, 39.6) {'n': 1779, 'nearest': -0.7}
- t_2_-7 (459.6, -1311.2) {'n': 1716, 'nearest': 0.7}

### collider_no_building (Top 12)

- t_-5_-1 (-937.3, -124.6) {'n': 19330}
- t_-2_3 (-352, 734.3) {'n': 12443}
- t_-7_1 (-1319.3, 246.5) {'n': 12358}
- t_0_4 (109.4, 958.4) {'n': 9799}
- t_0_3 (80.6, 720.3) {'n': 9009}
- t_1_4 (293.5, 893.1) {'n': 8902}
- t_0_3 (171.7, 682.1) {'n': 8660}
- t_7_-4 (1512.2, -733.8) {'n': 8411}
- t_5_1 (1128.8, 327.6) {'n': 8265}
- t_-3_-2 (-521.7, -345.5) {'n': 8097}
- t_-6_-1 (-1034.7, -148.6) {'n': 7987}
- t_-1_5 (-90.5, 1049.9) {'n': 7113}

### floating_component (Top 12)

- t_-11_4 (-2001.2, 864.7) {'n': 10, 'above': 60, 'size': 1.4, 'hgt': 0.9, 'z': 47.9}
- t_-11_4 (-2001.2, 869) {'n': 10, 'above': 58.7, 'size': 1.4, 'hgt': 0.9, 'z': 46.4}
- t_-10_2 (-1844.9, 534.4) {'n': 10, 'above': 50.1, 'size': 2.4, 'hgt': 2.2, 'z': 39.2}
- t_5_-3 (1070.1, -458.3) {'n': 10, 'above': 44, 'size': 2.4, 'hgt': 2.2, 'z': 41}
- t_5_-3 (1068.1, -460.7) {'n': 10, 'above': 43.8, 'size': 1.4, 'hgt': 0.9, 'z': 41}
- t_6_-3 (1213.8, -498) {'n': 10, 'above': 41.1, 'size': 2.4, 'hgt': 2.2, 'z': 35.6}
- t_3_1 (749.5, 390.3) {'n': 10, 'above': 33.8, 'size': 1.4, 'hgt': 0.9, 'z': 26.7}
- t_2_2 (465.2, 517.7) {'n': 10, 'above': 33.5, 'size': 2.4, 'hgt': 2.2, 'z': 25.5}
- t_1_2 (395.2, 536.7) {'n': 10, 'above': 33.3, 'size': 2.4, 'hgt': 2.2, 'z': 25.5}
- t_-1_1 (-135.4, 339) {'n': 10, 'above': 33, 'size': 1.4, 'hgt': 0.9, 'z': 25.1}
- t_-1_1 (-116.6, 317.6) {'n': 10, 'above': 32.9, 'size': 2.4, 'hgt': 2.2, 'z': 25.1}
- t_-1_1 (-158.7, 236.9) {'n': 10, 'above': 32.8, 'size': 2.4, 'hgt': 2.2, 'z': 25.1}

### zfight_ground_ground (Top 12)

- t_-1_4 (-157.9, 918.5) {'n': 397, 'pair': 'ground/ground'}
- t_1_-7 (389.3, -1209.6) {'n': 191, 'pair': 'ground/ground'}
- t_2_-4 (490, -675.4) {'n': 165, 'pair': 'ground/ground'}
- t_2_-4 (518, -675.6) {'n': 155, 'pair': 'ground/ground'}
- t_-1_-1 (-104.7, -187.5) {'n': 140, 'pair': 'ground/ground'}
- t_-5_-1 (-874, -55.5) {'n': 132, 'pair': 'ground/ground'}
- t_2_-6 (409.8, -1187.7) {'n': 126, 'pair': 'ground/ground'}
- t_0_3 (11.5, 696.7) {'n': 117, 'pair': 'ground/ground'}
- t_-12_2 (-2372.2, 427.6) {'n': 111, 'pair': 'ground/ground'}
- t_6_-1 (1392.4, -122.1) {'n': 100, 'pair': 'ground/ground'}
- t_6_-1 (1392.2, -141.9) {'n': 93, 'pair': 'ground/ground'}
- t_6_-1 (1369.7, -142.4) {'n': 85, 'pair': 'ground/ground'}

### building_on_road (Top 12)

- t_-4_3 (-713.5, 674.8) {'n': 2646, 'h': 23.44}
- t_-10_0 (-1937.3, 160.3) {'n': 743, 'h': 21.14}
- t_0_1 (106.9, 374.3) {'n': 567, 'h': 25.39}
- t_-2_4 (-289.8, 832.5) {'n': 176, 'h': 10.18}
- t_-4_-2 (-718.3, -222.4) {'n': 137, 'h': 13.37}
- t_6_-1 (1293.1, -172.4) {'n': 125, 'h': 21.54}
- t_-6_1 (-1021.3, 299.2) {'n': 117, 'h': 14.15}
- t_0_2 (163.3, 412.6) {'n': 113, 'h': 8.48}
- t_-3_3 (-591.9, 758.5) {'n': 107, 'h': 29}
- t_-2_4 (-275.3, 924) {'n': 107, 'h': 26.22}
- t_-2_4 (-282.3, 908.7) {'n': 106, 'h': 30.04}
- t_3_-7 (718.7, -1294) {'n': 100, 'h': 9.36}

### buried_component (Top 12)

- t_-8_-5 (-1480.5, -891.8) {'n': 144, 'below': 2.6, 'hgt': 2.1}
- t_-8_0 (-1470.7, 140.4) {'n': 131, 'below': 6.3, 'hgt': 2.8}
- t_7_0 (1415.7, 132.5) {'n': 91, 'below': 3.2, 'hgt': 2}
- t_7_0 (1415.7, 132.5) {'n': 91, 'below': 2.8, 'hgt': 2}
- t_4_3 (800, 693.6) {'n': 65, 'below': 1.3, 'hgt': 0.3}
- t_6_-6 (1392.8, -1086.1) {'n': 60, 'below': 2.1, 'hgt': 1.6}
- t_2_3 (591.8, 680.6) {'n': 44, 'below': 6.4, 'hgt': 3.8}
- t_-7_-3 (-1375.2, -558.2) {'n': 43, 'below': 2.3, 'hgt': 1.7}
- t_2_3 (593.6, 678.8) {'n': 42, 'below': 6.2, 'hgt': 3.8}
- t_2_3 (583.8, 683.9) {'n': 41, 'below': 7.1, 'hgt': 3.8}
- t_2_3 (589.9, 692.7) {'n': 39, 'below': 7.9, 'hgt': 1}
- t_6_-1 (1240.3, -142.6) {'n': 38, 'below': 2.2, 'hgt': 0.8}

### floating_over_deck (Top 12)

- t_0_0 (24.1, 139.1) {'n': 2, 'above': 17.2, 'size': 3.4, 'hgt': 0.1, 'z': 11}
- t_0_0 (19, 131.9) {'n': 2, 'above': 16.6, 'size': 3.8, 'hgt': 0.1, 'z': 11.2}
- t_-1_0 (-1.5, 127.7) {'n': 8, 'above': 12.4, 'size': 0.8, 'hgt': 2.4, 'z': 5.6}
- t_0_0 (32.8, 100.8) {'n': 2, 'above': 12.4, 'size': 0.6, 'hgt': 0, 'z': 12.9}
- t_1_-7 (345.1, -1243.2) {'n': 10, 'above': 9, 'size': 2.4, 'hgt': 2.2, 'z': 10.2}
- t_0_0 (68.2, 111.7) {'n': 8, 'above': 8.7, 'size': 0.6, 'hgt': 2.6, 'z': 5.4}
- t_-1_0 (-27.6, 151.3) {'n': 10, 'above': 8.3, 'size': 2.4, 'hgt': 2.2, 'z': 1.5}
- t_-1_0 (-20.5, 146.3) {'n': 10, 'above': 8.2, 'size': 1.4, 'hgt': 0.9, 'z': 1.5}
- t_-1_0 (-22.9, 146.3) {'n': 10, 'above': 8.1, 'size': 1.4, 'hgt': 0.9, 'z': 1.5}
- t_-1_0 (-27.6, 151.3) {'n': 10, 'above': 8, 'size': 2.4, 'hgt': 2.2, 'z': 1.2}
- t_-1_0 (-20.5, 146.3) {'n': 10, 'above': 7.9, 'size': 1.4, 'hgt': 0.9, 'z': 1.2}
- t_-1_0 (-22.9, 146.3) {'n': 10, 'above': 7.8, 'size': 1.4, 'hgt': 0.9, 'z': 1.2}

### zfight_bridges_ground (Top 12)

- t_-3_1 (-404.8, 313.6) {'n': 12, 'pair': 'bridges/ground'}
- t_-2_0 (-204.9, 172.5) {'n': 8, 'pair': 'bridges/ground'}

### zfight_ground_bridges (Top 12)

- t_-3_1 (-404.3, 314.6) {'n': 14, 'pair': 'ground/bridges'}
- t_-2_0 (-203, 172.5) {'n': 10, 'pair': 'ground/bridges'}

## Landmarks (Sockel/Fahrbahn), 423 von 606 auffaellig

- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Kirche Buehl Wiedikon (36.9, 21.2): Unterkante 28.03 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Zwinglihaus Aemtlerstrasse (-84.2, 1.9): Unterkante 8.77 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Loewenbrunnen Schmiede Wiedikon (314.2, 3): Unterkante 8.31 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.91 m ueber tiefstem Boden, Boden-Spanne 3.7 m, 0 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.91 m ueber tiefstem Boden, Boden-Spanne 3.7 m, 12 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.91 m ueber tiefstem Boden, Boden-Spanne 3.7 m, 12 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.91 m ueber tiefstem Boden, Boden-Spanne 3.7 m, 12 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.91 m ueber tiefstem Boden, Boden-Spanne 3.7 m, 12 % der Fusspunkte auf Fahrbahn
- Friedhof Sihlfeld Grabfelder (-767.5, 1.3): Unterkante 7.67 m ueber tiefstem Boden, Boden-Spanne 3.4 m, 0 % der Fusspunkte auf Fahrbahn
- Zürich Hauptbahnhof + Perrons (1526.7, -2): Unterkante 7.46 m ueber tiefstem Boden, Boden-Spanne 25.6 m, 7 % der Fusspunkte auf Fahrbahn
- Zürich Hauptbahnhof + Perrons (1526.7, -2): Unterkante 7.46 m ueber tiefstem Boden, Boden-Spanne 25.7 m, 10 % der Fusspunkte auf Fahrbahn
- Zürich Hauptbahnhof + Perrons (1526.7, -2): Unterkante 7.46 m ueber tiefstem Boden, Boden-Spanne 25.7 m, 10 % der Fusspunkte auf Fahrbahn
- Zürich Hauptbahnhof + Perrons (1526.7, -2): Unterkante 7.46 m ueber tiefstem Boden, Boden-Spanne 25.7 m, 10 % der Fusspunkte auf Fahrbahn
- Zürich Hauptbahnhof + Perrons (1526.7, -2): Unterkante 7.46 m ueber tiefstem Boden, Boden-Spanne 25.7 m, 10 % der Fusspunkte auf Fahrbahn
- Kirche St. Konrad Albisrieden (-1518.8, 2.9): Unterkante 6.63 m ueber tiefstem Boden, Boden-Spanne 0.3 m, 6 % der Fusspunkte auf Fahrbahn
- Kirche St. Konrad Albisrieden (-1518.8, 2.9): Unterkante 6.63 m ueber tiefstem Boden, Boden-Spanne 0.3 m, 6 % der Fusspunkte auf Fahrbahn
- Kirche St. Konrad Albisrieden (-1518.8, 2.9): Unterkante 6.63 m ueber tiefstem Boden, Boden-Spanne 0.3 m, 6 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Ortsmuseum Wiedikon (236.4, 0.1): Unterkante 6.28 m ueber tiefstem Boden, Boden-Spanne 0.0 m, 0 % der Fusspunkte auf Fahrbahn
- Bethaus Wiedikon (249.9, 0): Unterkante 6.19 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn
- Bethaus Wiedikon (249.9, 0): Unterkante 6.19 m ueber tiefstem Boden, Boden-Spanne 0.1 m, 0 % der Fusspunkte auf Fahrbahn

## Akteure in Gebaeuden (Stichproben je Kachelmitte)

{'npc_in_building': 57, 'traffic_in_building': 475}
- npc_in_building t_-14_3 (-2554.1, 747.7)
- npc_in_building t_-14_3 (-2555.7, 748.4)
- npc_in_building t_-13_-1 (-2523, 8.7)
- npc_in_building t_-13_-1 (-2522.3, 8.4)
- npc_in_building t_-13_0 (-2524.9, 4.5)
- npc_in_building t_-13_0 (-2524.2, 4.3)
- npc_in_building t_-13_0 (-2522.1, 10.7)
- npc_in_building t_-13_0 (-2521.4, 10.3)
- traffic_in_building t_-13_0 (-2307.3, 39.2)
- npc_in_building t_-13_1 (-2409.7, 325.7)
- traffic_in_building t_-13_1 (-2490.6, 111.2)
- traffic_in_building t_-13_1 (-2547.4, 134.9)
- traffic_in_building t_-13_2 (-2445.2, 325.3)
- traffic_in_building t_-13_2 (-2351.2, 431.6)
- traffic_in_building t_-13_2 (-2435.8, 516.8)

## Props: Hoehe gegen Terrain/Deck (Daten, `audit_props.py`)

| Art | Typ | Anzahl |
|---|---|---|
