# Baustellen (pipeline/sites.py)
Quellen (CC0, Stadt Zürich OGD, lokal in data/raw/stadtzh_all): Tiefbau-Baustellen im öffentlichen Grund (aer_baustellen_a, 37 Polygone im Spielgebiet), Hochbauprojekte in Ausführung (ahb_projekte_ogd, 33), dazu OSM building/landuse=construction. Ergebnis: 51 Strassenabschnitte, 85 Hochbau-Areale, 50 Kräne, ~11'000 Objekte, ~590 Arbeiter, 159 Kacheln.
Meta-Felder pro Kachel: `sites` [typ,x,y,z,yaw,a,b], `cranes`, `workers`; Zusatz-Gerüste via `sites.scaffold_rows`. Cache: data/build/sites.json. Info-Tafeln (echte Projektnamen, Bauende) kommen als Szenen ohne Egg aus scenes_build.py.
Darstellung: web/src/world/construction.ts (buildSites: 3 Calls pro Kachel, buildCranes: 3 Calls, Kräne immer sichtbar), Arbeiter: pedspots.ts.
