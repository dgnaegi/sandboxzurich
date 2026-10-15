# Railways (Gleisfeld, Bahnhoefe, S-Bahn)
Quellen: OSM (railway=rail/platform, building=roof, railway=stop; ODbL) via pipeline/sources.py, Gelaende swissALTI3D (z_shift -3.06).
Pipeline: `python3 pipeline/railways.py` -> web/public/models/trains/tiles/r_{ix}_{iy}.glb (1 Mesh/Kachel, Weltmaterial), web/public/data/rail.json
(Drahtlaeufe, Schild-/Uhr-Anker, Routen). Zuege: `blender -b -P pipeline/trains/build_trains.py` (Kopf 970 / Mittel 1070 Tris, 26.4 m, 5 Wagen = 132 m),
Kontaktbogen `blender -b -P pipeline/trains/render_sheet.py`.
Annahmen: Weichen = Ueberlagerung der OSM-Gleise; Masten ca. alle 60 m (Quertragwerk ab 3 Gleisen); Perron 55 cm ueber SOK; Perrondaecher aus building=roof
(koennen mit swissBUILDINGS3D-Daechern doppelt sein). Routen: Altstetten-Hardbruecke-HB (Rand) und Wiedikon-HB (Rand), beide Richtungen, Takt 240/270 s.
Zuege ohne Logo, weiss/rot/blau, Anmutung S-Bahn Zuerich.
