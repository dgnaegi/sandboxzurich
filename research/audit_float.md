# Audit: schwebende / versunkene Dinge

Erzeugt von `pipeline/audit_float.py` (read-only). Kachel = floor(x/200)_floor(y/200).

## 1. Brücken-Decks (OSM bridge=yes), 507 geprüft, 263 Chains im Build
- dangling: 78
- dup: 95
- no_obstacle: 105
- dup_sidewalk mit Höhen-Versatz (>=50% der Deckpunkte >1.2 m neben der Strassenbrücke): 5

Top 20 (id kind name x,y len Kachel Ursache):
- 622318251 foot «» (-1714,1331) 449m [-9_6] 1 end(s) connect to no way; 100% inside road bridge 74071551 Europabrücke
- 188867144 foot «» (-1733,1324) 420m [-9_6] 1 end(s) connect to no way; 100% inside road bridge 1027169 Europabrücke
- 1282792198 foot «» (-1871,1011) 122m [-10_5] 1 end(s) connect to no way; 100% inside road bridge 1282772919 Max-Högger-Strasse
- 623564037 foot «» (1960,-1044) 75m [9_-6] 1 end(s) connect to no way; 100% inside road bridge 332455406 Rudolf-Brun-Brücke
- 623564038 foot «» (1958,-1062) 74m [9_-6] 1 end(s) connect to no way; 100% inside road bridge 332455406 Rudolf-Brun-Brücke
- 623574796 foot «» (1976,-1543) 65m [9_-8] 1 end(s) connect to no way; 100% inside road bridge 147692714 Münsterbrücke
- 623574797 foot «» (1977,-1550) 65m [9_-8] 1 end(s) connect to no way; 100% inside road bridge 147692714 Münsterbrücke
- 186320890 foot «» (1979,-761) 63m [9_-4] 1 end(s) connect to no way; 79% inside road bridge 27410059 
- 188867156 foot «» (-1896,714) 31m [-10_3] 1 end(s) connect to no way; 100% inside road bridge 683225869 
- 89873383 foot «» (1377,-1521) 18m [6_-8] 1 end(s) connect to no way; 100% inside road bridge 8030504 Selnaubrücke
- 622318260 foot «» (-1840,1111) 91m [-10_5] nothing underneath (no lower way/water, terrain depression 1.5 m); 100% inside road bridge 9386299 Bändlistrasse
- 622318259 foot «» (-1836,1123) 90m [-10_5] nothing underneath (no lower way/water, terrain depression 1.2 m); 100% inside road bridge 9386299 Bändlistrasse
- 47122092 foot «» (88,178) 88m [0_0] nothing underneath (no lower way/water, terrain depression 0.3 m); 76% inside road bridge 550657243 Hardbrücke
- 424736273 foot «» (-169,-145) 42m [-1_-1] nothing underneath (no lower way/water, terrain depression 1.0 m); 100% inside road bridge 4310918 Hardbrücke
- 552831829 foot «» (-432,571) 42m [-3_2] nothing underneath (no lower way/water, terrain depression 1.5 m); 100% inside road bridge 965690041 Duttweilerbrücke
- 601078972 foot «» (-1810,994) 33m [-10_4] nothing underneath (no lower way/water, terrain depression 0.2 m); 92% inside road bridge 60795696 Europabrücke
- 424736279 foot «» (-154,-154) 30m [-1_-1] nothing underneath (no lower way/water, terrain depression 1.4 m); 100% inside road bridge 32391477 Hardbrücke
- 860007449 foot «» (-358,837) 27m [-2_4] nothing underneath (no lower way/water, terrain depression 0.9 m); 82% inside road bridge 306670709 
- 623552332 foot «» (657,1130) 20m [3_5] nothing underneath (no lower way/water, terrain depression 0.3 m); 80% inside road bridge 572299173 Rosengartenbrücke
- 601078975 foot «» (-1813,997) 18m [-10_4] nothing underneath (no lower way/water, terrain depression 0.1 m); 100% inside road bridge 60795696 Europabrücke

Unrealistisch hohe Decks (Chains, Freiraum > 22/14 m): 1
- foot «Negrellisteg» 16.4 m bei (1136,-448) [5_-3] ids=[39429386]

## 2. Props / Landmarks gegen Gelände (Toleranz +0.6 / -0.9 m)
- Props geprüft: 105312, auffällig: 2
- je Art: bikes 1/27153, racks 1/8408
- Landmarks: 221 geprüft, 4 mit |dz|>1.5 m

Top 20 Props (Kachel-Cluster):
- bikes x1 [-1_3] schlimmster (-41,597) dz -1.38
- racks x1 [-1_3] schlimmster (-41,597) dz -1.38

Landmarks:
- Bahnhof Wiedikon (Reiterbahnhof) (544,-1403) dz +7.9 [2_-8]
- Bahnhof Hardbruecke (28,112) dz +7.4 [0_0]
- Velotunnel Stadttunnel (1500,-680) dz +2.3 [7_-4]
- Hardau II (4 Wohntuerme) (-516,-321) dz -2.0 [-3_-2]

## 2b. Props gegen LiDAR-Boden (Klasse 2, ohne Deck/Gebaeude; Toleranz +0.6 / -0.9 m)
- Props mit LiDAR-Messung: 72838, auffällig: 1089 (trees 435, bikes 207, racks 104, decals 94, masts 79, scooters 79)
- davon steht das Prop auf dem Spielboden (|z - hmap| < 0.35 m, also Gelaende weicht von LiDAR ab, Prop ist korrekt): 1078; Prop selbst daneben: 11
- schlechteste 8 (Art x,y dz Kachel): trees (-866,1500) -9.66 [-5_7]; trees (-861,1497) -7.87 [-5_7]; trees (1604,83) -6.80 [8_0]; scooters (-1435,360) -6.71 [-8_1]; trees (-1393,342) -6.66 [-7_1]; decals (1504,169) -6.63 [7_0]; trees (-1386,339) -6.57 [-7_1]; trees (1578,248) +6.48 [7_1]

## Einordnung
- Props: praktisch sauber (nur Stichproben-Ausreisser, siehe oben); Vegetation `wild` wird nicht geprüft (z hat dort andere Bedeutung).
- Landmarks mit dz > 0: Bahnhöfe Hardbrücke/Wiedikon und Velotunnel liegen gewollt auf Viadukt bzw. im Tunnel (Gelände ist darunter); Hardau II -2 m: Gebäudesockel-Konvention (-3.06 m DTM).
- Behoben: Ausschluss `pipeline/overrides/bridges_excl.json` (Kriterium: dup_sidewalk mit Höhen-Versatz >= 100% der Deckpunkte, siehe `mismatch`).
- Nicht behoben (Beurteilung nötig): `no_obstacle` / `dangling` Stege ohne Höhenversatz. Meist echte Gehwege auf Strassenbrücken (z-fighting-frei, harmlos) oder Brücken über nicht kartierte Hindernisse (Böschung, Bach).
