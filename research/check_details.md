# Check Detail-Pakete (2026-10-16, nur lesend, keine Code-Aenderung)

| Paket | Stand | Naechster Schritt |
|---|---|---|
| Langstrasse A (8 Landmarks) / B (19) | halb-fertig: GLBs alle vorhanden (574-4283 Tris), Overrides valide, hide-Punkte je 1-4 Stueck [x,y]. Kein Duplikat zu lu_*/langstr_*/k4w* (kein anderes Landmark < 15 m). Ole Ole = lu_oleole, nicht in A/B. | merge.py laufen lassen, dann Sichtkontrolle; HANDOFF/ROADMAP nachtragen |
| Markierungs-Override (markings_override.py + json) | Hook in build_testarea aktiv (Zeilen 22/272/485), JSON valide (doc,yellow,region,add_*,cut). Ob es die Tile-Fehler verursacht: nein, Fehler liegt davor (roads) | im naechsten gelungenen Build Langstrasse-Ground pruefen |
| Dachaufbauten | fertig: tsc sauber, Hook mit try/except, Geometrie/Material geteilt, disposeTile (tiles.ts 216ff) deckt InstancedMesh ab | nach Build roofs-Screenshot (roofs_shots.mjs) |
| Parks / Plaetze | Overrides valide (places_detail_parks/squares2), research/parks + squares2 vorhanden | im Build-Ergebnis stichprobenweise ansehen |
| Namen (names_inst/names_audit) | im Build eingehaengt (add_institutions, fallback, gwr_numbers, junction_poles); Build lief bis Kachelphase | Audit nach erfolgreichem Build |
| Fehler-Sweep | Vorher-Messung vorhanden (306 Kacheln, 10685 Cluster); sweep.json == sweep_before.json (gleiche Groesse): Nachher-Lauf fehlt | nach Build sweep.mjs erneut, Vergleich |

## KRITISCH: Build full9
Alle Kacheln "TILE FAILED" (13+ bis 15:54): build_testarea.py:168 `S["roads"].boundary.buffer` -> `.boundary` ist None, d.h. S["roads"] ist eine GeometryCollection (nicht Polygon/MultiPolygon). Verdacht: Zeile 308 `union_all([roads, cityprops.parking_bays(...)])` oder EXR/Wasser-difference. Fix-Vorschlag direkt nach Zeile 308 (und nach 254/262): S["roads"] = shapely.union_all([g for g in shapely.get_parts(S["roads"]) if g.geom_type in ("Polygon","MultiPolygon")]). Build abbrechen, nicht deployen.
