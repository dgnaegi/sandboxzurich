# Boden-/Strassen-Audit stadtweit (agent groundaudit, 2026-10-22)
Skript `pipeline/audit_ground_city.py` (der Name `audit_ground.py` war schon vergeben: Zonen-Audit AV vs OSM, unverändert). Liest nur `web/public/tiles/t_*.json`, Verkehrsraster, `data/cache/props_road_zone.wkb`, LiDAR-Raster; keine Builds. Volle Liste: `research/ground_audit/findings.tsv` (x, y, class, magnitude, source, street, score; Score = Klasse x Betrag x Sichtbarkeit, Kameras/Spawns x3 / x2).

## Klassen und Zahlen (307 Kacheln)
| Klasse | n | Ursache / Modul |
|---|---|---|
| hmap_pit (Boden-Loch >0.7 m gegen Nachbarn UND >0.6 m gegen LiDAR-DTM) | 124 | rohes swissALTI3D (`terrain.heights`): 1-3-Zellen-Brunnen 1-4 m tief auf flachen Strassen, LiDAR zeigt nichts |
| hmap_spike (Gegenstück nach oben) | 5 | gleiche Ursache |
| hmap_step (>1.5 m zwischen zwei Fahrbahnzellen) | 14 | Rampen/Brücken (Freischützgasse 1322,-632; Gallusstrasse 1622,66) -> Brücken-Agent |
| lidar_dz (20-m-Blöcke |dz|>1 m) | 96 | grossteils kein Bodenfehler: LiDAR-Klasse 2 enthält Bahn-/Strassenbrücken (DTM 3-6 m über Spielboden darunter, 6 von 8 geprüft); Rest Brückenrampen und terrain_cuts (910,-330 Spiel -8.4 gegen DTM -2.3, Gleisgraben, plausibel) |
| shrub_on_road (Strauch-Mittelpunkt auf Fahrbahn) | 12 Raster / 93 gegen Fahrbahnpolygon | `yards.py`-Sträucher; `props_road.fix_meta` kannte `yards.bushes/hedges` nicht |
| shrub_edge_road (Strauch ragt in Fahrbahn) | 125 | gleiche Quelle, nicht behoben (Radius 1-1.7 m, nur Randüberlappung) |
| trees_on_road | 62 | `cityprops.lane_fix` (max 2.5 m) reicht nicht; viele am Spielfeldrand/Brücken. Ticket |
| lawn_on_road | 1 | (616,-1092) Badenerstrasse. Ticket |
| road_hole (Null-Flächen-Innenring im Fahrbahnpolygon) | 13 in `S['roads']` | `streets.tidy_roads` (simplify/set_precision); `curb_faces` baute daraus Ringe schwebender Randsteinwände |
| road_sliver (<4 m2) | 36 | nur in der Zone nach Abzug Plaza/Fussgängerzone/Decks (`props_road.zone`), nicht in `S['roads']`; kein Handlungsbedarf |
Orphan-Randsteine: Randstein = Rand von `S['roads']` (`build_testarea.curbs`), echte Waisen entstehen daher nur dort, wo das Fahrbahnpolygon mitten im Nichts endet (Brückendeck-Abzug -> Brücken-Agent) und an den 13 Pinholes (behoben). Markierungen entstehen als Schnitt mit dem Fahrbahnpolygon, liegen konstruktionsbedingt innerhalb. Kalkbreite (355,-1094): kein Strauch in `yards`, nur Bäume/Rasen aus cityprops (0.8 m über Deck) -> Brückenfall.

## Top-Stellen (Score)
- -1390.0,   390.0 lidar_dz        -6.48 terrain(swissALTI/park) Mürtschenstrasse [36.0]
- 910.0,  -350.0 lidar_dz        -4.77 terrain_cuts           Lagerstrasse [36.0]
- 1322.0,  -632.0 hmap_step        2.85 road_height            Freischützgasse [34.2]
- -130.0,  -150.0 lidar_dz        -3.37 terrain(swissALTI/park) 1 [30.3]
- 1230.0,   170.0 lidar_dz        -3.34 terrain(swissALTI/park) Kornhausbrücke [30.1]
- -150.0,  -150.0 lidar_dz        -3.17 terrain(swissALTI/park) Hardstrasse [28.5]
- 990.0, -1202.0 hmap_pit        -1.62 terrain                Stauffacherstrasse [24.3]
- 350.0,  -130.0 lidar_dz         -7.7 terrain(swissALTI/park)  [24.0]
- -1390.0,   370.0 lidar_dz        -6.51 terrain(swissALTI/park) Mürtschenstrasse [24.0]
- 910.0,  -330.0 lidar_dz        -6.02 terrain_cuts           Lagerstrasse [24.0]
- 930.0,  -290.0 lidar_dz        -6.02 terrain_cuts           Zollstrasse [24.0]
- -1350.0,   350.0 lidar_dz         -5.7 terrain(swissALTI/park) Mürtschenstrasse [24.0]
- 910.0,  -310.0 lidar_dz        -4.53 terrain_cuts           Zollstrasse [24.0]
- 290.0, -1530.0 lidar_dz        -4.26 terrain(swissALTI/park) Zurlindenstrasse [24.0]
- 90.0,  -910.0 lidar_dz        -4.14 terrain(swissALTI/park) 0 [24.0]
- 432.0,   132.0 hmap_pit        -2.33 terrain                Viaduktstrasse [23.3]
- -60.0,  -284.0 hmap_pit         -2.3 terrain                Hirzelstrasse [23.0]
- 70.0,  -910.0 lidar_dz        -3.57 terrain(swissALTI/park) Hildastrasse [21.4]
- -296.0,  -902.0 hmap_pit        -2.13 terrain                Fritschistrasse [21.3]
- 1622.0,    66.0 hmap_step        3.37 road_height            Gallusstrasse [20.2]
Hinweis: hmap_pit-Beispiele ohne LiDAR-Gegenstück sind echte swissALTI-Artefakte, z. B. (990,-1202) Stauffacherstrasse -2.3 m (roh -2.7 in der Quelle, LiDAR -0.4), (932,-1338) -4.1 m, (1476,-708) -1.8 m, (20,-708) -2.6 m.

## Fixes (Dateien)
1. `pipeline/terrain.py`: neue `despike()` in `heights()` (nach Cache-Lesen/-Schreiben, Cache bleibt roh). Ersetzt Zelle durch 5x5-Median nur wenn: >0.7 m vom Median, LiDAR-DTM widerspricht (>0.6) und stützt den Median (<0.6), DTM selbst flach (4 m Kreuz <0.5), kein Gebäude/Brücke <3 m. Ohne LiDAR-Raster oder z_shift != -3.06 keine Wirkung. Trockenlauf Gesamtraster: 539 Zellen, 325 im Spielgebiet (Median 1.3 m, max 5.3 m), Stichproben bestätigt (Einzelpunkte).
2. `pipeline/props_road.py`: `fix_meta` ruft neu `_yard_greens`: yards.bushes mit Mittelpunkt auf Fahrbahn werden gestrichen (93 im Trockenlauf), yards.hedges wenn Enden+Mitte drauf (0).
3. `pipeline/streets.py`: `tidy_roads` -> `_drop_pinholes` (Innenringe <0.5 m2 weg; 13 gefunden).
4. Neu: `pipeline/audit_ground_city.py`.

## Rebuild
Wirkt erst im nächsten Build (nicht gestartet). Betroffen: alle Kacheln mit einem der 129 Pit/Spike-Punkte (`findings.tsv`, Klassen hmap_pit/spike, Kachel = floor(x/200), floor(y/200)); Kacheln der Büsche-Funde; die 13 Pinhole-Kacheln. Praktisch Komplett-Build (terrain/streets sind global). Nach dem Build `audit_ground_city.py` erneut: hmap_pit/spike und shrub_on_road sollten 0 werden.

## Tickets (nicht behoben)
- T-G1 trees_on_road 62 + lawn_on_road 1: `cityprops.lane_fix` Reichweite/Brückenausnahme prüfen (Liste in findings.tsv).
- T-G2 shrub_edge_road 125: Büsche randscharf am Kerb kürzen/verschieben (yards.py, Kerb-Abstand r).
- T-G3 hmap_step Freischützgasse (1322,-632) 2.9 m, Gallusstrasse (1622,66) 3.4 m, (-548,1236): road_height/Brücke, übergeben an bridgeramp.
- T-G4 lidar_dz-Blöcke Mürtschenstrasse (-1390,390), Hardstrasse/Zollstrasse (-130,-150), (910,-330): DTM-Klasse 2 enthält Brückendecks; audit_lidar a sollte Bereiche mit DTM-Stufen >2 m ausschliessen, sonst Fehlalarme.
- T-G5 HANDOFF-Cluster (-2120,120), (-1495,500), (71,-906): sind Einzelpunkte unter Brücken (DTM = Deck bzw. Graben), kein Geländefehler; (1550,124)/(1504,175) Hanglage mit DTM-Stufe, Brückenfall (Kornhaus/Wipkingen).
