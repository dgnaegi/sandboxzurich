# LiDAR-Audit (pipeline/audit_lidar.py)

## b) Brueckendecks: 263 Chains, 223 mit LiDAR-Messung, 195 mit Klasse-17-Flaeche
- mittlere |dz| je Chain: Median 0.16 m, >0.5 m: 58 Chains, >1 m: 36; max|dz| >2 m: 60 Chains; Punkte >1 m: 1285
- 1369 Deckpunkte in 57 Chains ohne LiDAR-Ebene innerhalb 4 m der Spielhoehe (audit_b_far.tsv: Ebene ueber/unter, oder Spiel stark falsch)
- schlechteste Chains (mean|dz|, max, name, worst x,y):
  #23 Würzgrabenstrasse: mean 3.59 max 3.59 bei (-1777.4,994.6) bias -3.59 (1/11 Punkte)
  #99 foot: mean 3.58 max 3.98 bei (1196.0,-1206.0) bias -0.40 (2/6 Punkte)
  #232 rail: mean 3.58 max 3.92 bei (313.8,64.5) bias -3.58 (30/30 Punkte)
  #233 rail: mean 3.55 max 3.98 bei (308.2,53.3) bias -3.55 (22/30 Punkte)
  #42 Hönggerrampe: mean 3.50 max 3.50 bei (-1755.0,1089.0) bias -3.50 (1/8 Punkte)
  #230 rail: mean 3.19 max 3.22 bei (317.8,-59.6) bias -3.19 (4/4 Punkte)
  #216 rail: mean 2.84 max 4.00 bei (314.1,83.6) bias -0.03 (22/121 Punkte)
  #214 rail: mean 2.81 max 4.00 bei (-158.7,194.6) bias -2.39 (83/197 Punkte)
  #225 rail: mean 2.64 max 3.97 bei (-414.8,391.3) bias -1.52 (96/240 Punkte)
  #221 rail: mean 2.58 max 3.58 bei (-352.0,962.4) bias +2.58 (7/34 Punkte)
  #111 road: mean 2.24 max 3.70 bei (-862.1,699.4) bias +2.24 (8/33 Punkte)
  #254 rail: mean 2.22 max 3.91 bei (363.8,-285.7) bias -2.18 (110/166 Punkte)

