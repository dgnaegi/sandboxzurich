# HB Qualitaets-Review (2026-10-18)

Kontaktbogen vorher/nachher: `preview/hb_review_before.jpg`, `preview/hb_review_after.jpg` (Foto | Spiel an 12 Stellen; Skript `pipeline/landmarks/hb_review.py`, Einzelansichten mit `hb_review_shot.mjs`, Dev-Server-Port per `PORT=`).

## Befunde (schlimmste zuerst) mit Ursache

| # | Befund | Ursache | Status |
|---|---|---|---|
| 1 | In Querhalle, Perronhallen und auf den Perrons hängt eine **flache graue Decke** ~4 m über dem Perron (Dach, Rippen und Lampen des Landmark-Modells unsichtbar) | `pipeline/railways.py` `add_platforms()` baut aus den OSM-Dachpolygonen (Perrondächer) eine Platte auf Perron + 3.6 m (Unterseite hellgrau, im Schatten flach grau). Sie verdeckt die Tonnengewölbe aus `hb_perron.py` | behoben: Dächer, deren Punkt in `research/hb/prop_excl.json` liegt, werden übersprungen (Kacheln neu gebaut) |
| 2 | Böden (Haupthalle, Querhalle, Perrons) **blau/navy**, Haupthalle-Schachbrett fast schwarz-blau | Landmark-Materialien (Lambert) werden nur von der blauen Himmels-IBL + Hemisphärenlicht beleuchtet (Dach wirft Schatten, Sonne fehlt); neutrale Grautöne kippen ins Blaue | behoben: `hxw()` (hb_kit.py) = warm vorgetönte Vertex-Farben für Böden, Perron-Beläge, Querhalle-Decke, Perron-Dachinnenseite |
| 3 | **Bäume, Bänke, Laternen stehen auf den Perrons und in den Hallen** (Stadtbaumkataster + OSM-Props) | `cityprops.city_props()` filtert nur die Langstrassen-Unterführung | behoben: Ausschlusspolygone `research/hb/prop_excl.json` (von `pipeline/landmarks/hb_propexcl.py`), von `cityprops.py` gelesen |
| 4 | Escher-Brunnen und der südliche Bahnhofplatz hinter einem **«BAUSTELLE – DURCHGANG GESPERRT»-Bauzaun** (c ≈ -100), Platzmitte nicht erreichbar | Spielgebiet-Rand `overrides/playarea_extra.json` (c -100..72) endet 25 m südlich der Fassade; echter Platz reicht bis c ≈ -150 | nur dokumentiert (Strassen-/Bahnhofplatz-Agent bzw. nächste Runde: `c0` auf -150 setzen, Kulissenkachel `t_8_-5`/`t_7_-5` zu Spielkacheln) |
| 5 | Perronhalle von oben: Dachglas **weiss-hellblau** statt dunkler Stahl/Glas; Perron-Dachkante Nordhalle braun | `GLASS_O` #9eb3bd in `hb_perron.py` ist im Spiel durch Sonne + IBL fast weiss | offen (Farbe im Foto-Vergleich nachprüfen) |
| 6 | **Schwebende graue Quader** über dem Ostgiebel der Haupthalle (vom Bahnhofquai gesehen, ~25 m hoch) | nicht der Gebaeude-Layer (`nob` ändert nichts), nicht aus hb_*; Quelle unbekannt (Kandidat: fremdes Landmark/Dachaufbau) | offen |
| 7 | Haupthalle-Ostgiebel: grosse Rundbogenfenster als flache graue Flächen ohne Sprossen | `hb_shell.py` Gable nutzt `mf` (flat) ohne Glas-Atlas | offen (klein) |
| 8 | Hecke aus grossen grünen Kugeln vor dem Ostgiebel (Bahnhofquai) | Hofstrauch-Kacheln (`yards.py`), nicht HB | offen, gehört zu Yards |
| 9 | Konsolenfehler `arc ... radius provided (-2) is negative` bei jedem Laden (~2x) | ein Canvas-`arc()`/`roundRect()` mit negativem Radius in der Web-App, Quelle ausserhalb der hb-Dateien | offen, nur gemeldet |
| 10 | Untergeschosse (hb3): an der Oberfläche **keine Löcher, kein Z-Fighting** gefunden. Schacht S2 (Bahnhofplatz) offen mit Brüstung, stimmt | – | hb3 bleibt eingeschaltet |

## Nicht gefunden / geprüft
- Fassade Bahnhofplatz: Masse/Proportionen passen (Mittelportal, Mansarde, Flügel), Portal-Tunnel innen braun = bewusst (kassettierte Decke nach Foto).
- Gleise/Perrons: Lage und Nummern stimmen mit `tracks.json`; Gleisvorfeld als dunkle Schotterbahn, Perrons hell.
- Rasen statt Pflaster am Bahnhofplatz: Rasen liegt nur im Hof innerhalb der Südtrakt-Grundfläche und an der Ostseite (Bahnhofquai); der Platz vor der Fassade ist Pflaster. Boden macht ein anderer Agent.
