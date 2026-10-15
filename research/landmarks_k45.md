# Landmark-Modelle Kreis 4/5 (pipeline/landmarks/)

## Format (stabil, geteilt mit landmarks_k93.json)
`pipeline/overrides/landmarks_*.json`: `{"landmarks":[{"name","model":"/models/landmarks/x.glb","x","y","z","heading":0,"hide":[[x,y],...]}]}`
x, y = lokale Meter (Ursprung des Modells), z = Bodenhöhe dort, heading = Rotation um Hochachse (rad; die Modelle haben die echte Ausrichtung eingebacken, daher 0).
`hide` = Punkte innerhalb der Grundrisse der swissBUILDINGS3D-Gebäude, die das Modell ersetzt (Hook in build_testarea.py).
`pipeline/landmarks/merge.py` (läuft automatisch bei jedem `finish()`) schreibt alle Overrides nach `web/public/data/landmarks.json`.
Modellraum: x Ost, y Nord, z oben, Ursprung = Anker; Skirt bis -3 m unter Boden. Laden: `Landmarks3D` (web/src/world/landmarks3d.ts), Radius 600 m, Nacht-Emissive über `nightUniform`.

## Bauen
`cd pipeline/landmarks && ../../.venv/bin/python k45_<name>.py` (Toni, Volkshaus, Hardau, Prime, Kva, Viadukt, Schiffbau; `k45_misc.py` = Lochergut, Kalkbreite, St. Jakob, Bullingerkirche, Kanzlei). Kit: `lm.py` (Mesh/Texturen/GLB), `tex.py` (Fassadenpainter), `common.py` (Footprints, Boden). Rein Python/numpy/PIL, gltfpack `-cc`. Vorschau: `lmtest.html` nach web/public kopieren, `shot.mjs`.

## Stand (Dreiecke, alle weit unter 15k)
Toni-Areal 186 (Haupttrakt 34 m + Turm 76 m, Streckmetall/Sichtbeton; echte IDs 5CEB50B3/195ECD88), Volkshaus 344 (Schriftzug), Hardau II 4 Türme 1056 (Höhen 70-97 m aus swissBUILDINGS3D), Prime Tower + Platform 237, KVA-Kamin 374 (überlagert den swissB3D-Stachel, kein hide), Im Viadukt 40 Bögen 480 (aus OSM-Einheiten, kein hide; Viadukt-Deck kommt aus der Bahn-Ebene), Schiffbau + Kamin 116, Lochergut 2311, Kalkbreite 167, St. Jakob 144, Bullingerkirche 114, Kanzlei-Schulhaus 188.
Offen: Bahnhof Hardbrücke, Toni-Rampe, Kalkbreite-Detail, Dachlandschaft; Orientierung des Toni-Turms nur aus Daten.

## Detailrunde 2 (Geometrie-Details, `detail.py`)
Neu: `detail.py` (eingezogene Fenster mit Laibungen/Sims, Bandfenster pro Geschoss, Balkonplatten, Gesimse, Glas-Atlas mit Vorhängen/Sprossen + Nacht-Emissive, Schriftfeld). Dreiecke: Toni-Areal 8374 (Ramp, Eingang mit Vordach und Schriftzug TONI-AREAL, Dachaufbauten, Turm-Krone), Volkshaus 7600 (Rundbogen-EG, Laibungen, Gesimse, Lisenen, Mansarde mit Gauben, plastisches Schriftfeld, Vordach), Hardau II 13024 (Balkonplatten mit Farbfronten, Sockelbau 11 m, Eckfinnen), Bahnhof Hardbrücke 1546 (Perrondächer, Stützen, Bänke, Glas-Treppentürme; Perronhöhe z=0.9 aus Schienenkacheln geschätzt).
Vorschau: preview/landmarks_k45_detail.jpg. Keine Normal-/Alpha-Maps (Streckmetall nur als Textur).
