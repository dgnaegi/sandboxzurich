# Dachaufbauten (pipeline/rooftops.py, web/src/world/rooftops.ts)

Ziel: Dächer von Brücken/Hochhäusern aus glaubwürdig (Gauben, Dachfenster, PV, Lift-/Lüftungsaufbauten, Dachterrassen, Antennen, Gründächer).

Quellen (alle Open Data, keine Texturen kopiert):
- swissBUILDINGS3D Dachflächen: Neigung/Azimut/Fläche -> Gauben (Neigung > 34 Grad, Fläche > 45 m2, Breite > 8 m), Dachfenster, Terrassen (flache Teilfläche > 2.8 m unter dem First).
- swissSURFACE3D (data/raw/surface3d, 0.5 m, DSM) minus sb3d-Dachebene: Aufbauten > 0.8 m (Lift/Treppenhaus > 2.1 m, Lüftung, Antennen bei 1-2 Pixeln). Hinweis: data/build/ndsm hat Gebäude auf NaN (nur Bäume), deshalb das Roh-DSM.
- SWISSIMAGE (ortho_wms, 0.5 m): grün (g > r+8, g > b+16) auf flachem Dach mit DSM-Streuung < 0.9 m = Gründach (facade.py: Layer grass); dunkelblau (b > r+12, lum < 105, nicht > 85 % der Fläche = Schatten) = Photovoltaik. Teal/blaugrüne Farbdächer zählen nicht als grün.
- OSM roof:shape / Stadt-ZH-Dachmodell LoD2: nicht verwendet (sb3d reicht, Lizenz 2011/13 unklar).

Laufzeit: Meta-Feld "roofs" pro Kachel, Zeilen [typ, x, y, z, w, d, h, azimut, neigung, farbe]; 2 InstancedMesh (Box, Giebelprisma) pro 100-m-Chunk, geteilte Geometrie/Material, Sichtweite tiles.roofRadius (PC 250 m, Handy 150 m). Dispose über Tile-Gruppe.
Wenn nDSM-Aufbauten gefunden werden (flags.real_units), entfällt das zufällige roof_units in facade.py.
Test: web/tests/roofs_shots.mjs + roofs_sheet.py -> preview/roofs_v2.jpg.
