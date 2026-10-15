# Menschenmodelle (GLB)

Quelle: MakeHuman/MPFB-Assets (CC0), erzeugt per `pipeline/blender/build_humans.sh` (Blender 5.2, MPFB, game_engine-Rig, 53 Bones, identische Namen). Pro Datei 1 SkinnedMesh, 1 Material (gebackener Atlas, JPEG), Animationen idle (3.2 s), walk (1.0 s), run (0.7 s), in-place, loopend. Keine Hüte/Brillen/Taschen. Kontaktbogen: `preview/humans_sheet.jpg`.

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
