# Menschenmodelle (GLB)

Quelle: MakeHuman/MPFB-Assets (CC0), erzeugt per `pipeline/blender/build_humans.sh` (Blender 5.2, MPFB, game_engine-Rig, 53 Bones, identische Namen). Pro Datei 1 SkinnedMesh, 1 Material (gebackener Atlas, JPEG), Animationen (seit R6: Motion-Capture, siehe unten) idle, walk, run, in-place, loopend. Keine Hüte/Brillen/Taschen. Kontaktbogen: `preview/humans_sheet.jpg`.

| Datei | Tris | KB | Textur KB | Lizenz |
|---|---|---|---|---|
| npc_00.glb | 4496 | 373 | 71 | CC0 |
| npc_01.glb | 4496 | 363 | 53 | CC0 |
| npc_02.glb | 4493 | 369 | 56 | CC0 |
| npc_03.glb | 4492 | 348 | 52 | CC0 |
| npc_04.glb | 4495 | 358 | 62 | CC0 |
| npc_05.glb | 4495 | 333 | 50 | CC0 |
| npc_06.glb | 4494 | 375 | 55 | CC0 |
| npc_07.glb | 4495 | 364 | 67 | CC0 |
| npc_08.glb | 4493 | 356 | 50 | CC0 |
| npc_09.glb | 4495 | 364 | 52 | CC0 |
| npc_10.glb | 4494 | 382 | 62 | CC0 |
| npc_11.glb | 4496 | 352 | 54 | CC0 |
| npc_12.glb | 4495 | 382 | 67 | CC0 |
| npc_13.glb | 4495 | 381 | 64 | CC0 |
| npc_14.glb | 4493 | 365 | 59 | CC0 |
| npc_15.glb | 4497 | 336 | 49 | CC0 |
| player.glb | 11988 | 794 | 206 | CC0 |

Summe: 6595 KB. Hinweis: Weights als uint8 normalisiert, konstante Translation/Scale-Kanäle entfernt (`glb_compact.py`).

## R5 Ergänzung (npc_16..npc_39, Accessoires)
- Build: `bash pipeline/blender/build_humans.sh [ids]` (Specs: `pipeline/blender/human_specs.py`, Texturen: `gen_cloth_tex.py`). Alle 40 NPCs 3.4k bis 4k Tris, max 377 KB, Humans gesamt ca. 14.8 MB. Kontaktbögen `preview/humans_sheet.jpg` (npc_00..15), `humans_sheet2.jpg` (npc_16..39), `humans_sheet_acc.jpg` (Accessoires).
- MakeHuman-Logo: aus den Kleidungs-Diffuse-Texturen herausgeklont (`gen_cloth_tex.py`, auch npc_00..15 neu gebaut). Neue NPCs: Hemdfarbe und Jeans-Variante pro Figur umgefärbt statt Hue-Tint.
- Manifest: `age` child|young|mid|old, `sex`, `height` (m), `walk_speed` (Hinweis-Multiplikator), `anims`, `props` (cane/walker), `needs_adult` bei Kindern. 24 neue: 12 young, 3 mid, 5 old (3 mit cane/walker-Prop), 4 Kinder (Alter 0.10-0.17 MPFB, ca. 6-12 J.). Herkunftsmix per Rassen-Blend.
- Neue Clips für alle NPCs (nicht player): `walk_slow` (1.5 s), `stand_phone` (3.2 s, Phone-Accessoire passt dazu). Alte NPCs: gebeugte Haltung in idle/walk. Kinder: eigener Walk (kürzere Schritte, schneller). Export per ACTIONS (NLA-Export hatte Frame-0-Fehler).
- Hüte: Mütze/Cap pro Figur (6 NPCs), eigene Geometrie auf Kopf-Bone gebunden. Einschränkung: keine Hoodies/Mäntel/Brillen/Taschen im Körper-Mesh; Jacken sind getönte MakeHuman-Jacken, Mantel nur als Blazer/Jacke.
- Accessoires: `web/public/models/accessories/*.glb` + `manifest.json` (Vertex Colors, <=222 Tris, 3-21 KB). `bone` + `offset` (m) + `rotation` (Euler XYZ rad) gelten als Kind des Bones (Three.js), gemessen an npc_01; `bone:null` = relativ zum Figuren-Root (stroller, walker, dog_*). `tint` = Vorschlag, Material.color multipliziert die Vertex Colors (klonen!). Dogs haben Clip `walk` (1 s Loop). `phone` nur mit `stand_phone`. Kinder: Accessoires mit height/1.75 skalieren. Prüf-Viewer: `pipeline/blender/check/measure_attach.mjs` (Playwright mit Route-Mock, kein Server nötig).

## R6 Motion-Capture-Animationen (ersetzt die prozeduralen Sinus-Clips)
- **Quelle:** CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), frei für jede Nutzung (kommerziell und nichtkommerziell; Hinweis «data obtained from mocap.cs.cmu.edu, funded by NSF EIA-0196217»). BVH-Konvertierung von Bruce Hahne (cgspeed), Spiegel: github.com/una-dinosauria/cmu-mocap (`READMEFIRST.txt` liegt in `data/raw/mocap/`). Kein Mixamo, keine NC-Lizenz.
- **Genutzte Takes** (`data/raw/mocap/<subject>/`): Set A (Subject 35, grössere Statur, männliche Figuren): walk 35_01, run 35_21, slow 35_29. Set B (Subject 7/16, kleinere Statur, weibliche Figuren und Spielfigur): walk 07_09, run 16_46, slow 07_04. Idle: 49_16 / 49_15 (Stehen mit leichtem Gewichtverlagern, nur zwei ruhige Takes gefunden). CMU dokumentiert das Geschlecht der Performer nicht; Zuordnung ist eine Heuristik nach Statur.
- **Pipeline:** `pipeline/mocap/prep.py` (numpy, `.venv/bin/python -I`): BVH lesen, Gang-Zyklus per Pose-Distanz suchen (a, Periode), Schliess-Fehler linear über den Zyklus verteilen, Start auf linkem Fersenaufsetzer, Kurs auf +Z drehen, Wurzel in place (Drift raus, vertikales Wippen und seitliches Schwanken bleiben), auf 30 fps (idle 15 fps) -> `data/cache/mocap/*.npz`. `pipeline/blender/mocap_retarget.py`: Retargeting aufs 53-Bone-Rig: Weltrotations-Delta der Quelle (Rest = Identität) mal Rest-Korrektur (Segmentrichtung Ziel -> Quelle, nur Gliedmassen; Spine/Hals/Kopf/Becken behalten ihre eigene Krümmung), Hüftbewegung mit Beinlängenverhältnis skaliert, Becken so abgesenkt, dass der tiefste Fuss im Zyklus den Boden berührt. Nur 22 gemappte Bones + Becken-Location werden gekeyt (Finger/Twist bleiben Rest) -> kleine Dateien. Ältere Figuren: Rumpf-/Nackenneigung additiv; `walk` = slow-Take. stand_phone bleibt prozedural.
- **Clip-Geschwindigkeit:** aus den Standbeinen der retargeteten Figur gemessen (m/s), pro Figur im Manifest: `clip_speed {walk, run, walk_slow}`. Spielseite: Wiedergaberate = v / clip_speed, Gewichte statt harter Umschaltung (`Human.setSpeed`, phasensynchron). Typisch Spielfigur: walk 1.35, run 3.66 m/s; Kinder (Beinlänge 0.57) walk 0.87.

## R7 Animationsbibliothek und Kleidung (Menschen v4)
- **Takes** (CMU, `data/raw/mocap/`, Fenster in `pipeline/mocap/prep.py` CLIPS, Kind `pose` = Schleife schneiden, Blick auf +Z drehen, xz zentrieren): 113_21 (shift), 77_02 (stand2), 40_10 «wait for bus» (wait), 18_08 «explain with hand gestures» (talk/listen), 19_08 (talk2), 80_48 «arguing» (argue), 114_05 / 18_12 / 19_12 (sit, sit_talk, sit_chat). Verworfen: 77_01 (Hocke), 111_28 (Schwangeren-Haltung), 141_20, 49_15/16 als Basis (Kopf tief). Kein Take für Handy, Arme verschränken, Taschen, an die Wand lehnen: `crossed`/`pockets` = ruhiger Take + feste Arm-Pose (Hm.arm, Override in `build_action`), `call`/`text` = Take + Arm-Pose + Kopfneigung, `look` = Take + Kopfdrehung. Wandlehnen fehlt (kein passender Take).
- **Bibliothek:** 19 Clips je Klasse (A = männlich, B = weiblich; young/old mit Rumpfneigung), Referenzfiguren npc_01/npc_00/npc_32/npc_31 (`LIB_REF` in humans.ts), Rotationskanäle nur für die 22 gemappten Bones + Becken. Prüfbogen: `node pipeline/blender/check/anim_sheet.mjs out.jpg npc_01 A_young 1.5 [clips]` (`ZOOM=1`, `ACC=` für Handy-Fits).
- **Handy:** `PHONE_FIT` in humans.ts (hand_r; text = Fit aus R5, call = x + 5 cm). Handfläche zeigt beim Telefonieren nicht zum Ohr (nur Arm-Pose, keine Handrolle).
- **Kleidung:** `tint.ts`, Zonen: Shirt (spine/clavicle/Arme), Hose (pelvis/thigh/calf), Schuhe (unterste ~7 cm der Fussbones); Hände/Kopf nie. Paletten Herbstlook (17 Oberteile, 9 Hosen, 7 Schuhe), 25 % behalten das Original. Schal (Torus am neck_01, 22 %). Offen: Mäntel/Rucksack-Varianten über die vorhandenen Accessoires hinaus, Wandlehnen, Becher.
- **Nebenwirkung:** `stand_phone` steckt noch in den NPC-GLBs, wird aber ignoriert (Alias `stand_phone` -> `text`); beim nächsten Voll-Rebuild aus `build_human.py` streichen.

