# Startorte (Spawns)

Stand 2026-10-19. Problem (User): der Spieler landete nach Neustart/Kartensprung teils an merkwuerdigen Orten (Fahrbahnmitte, Hang, Dach, Platz hinter Zaun).

## Regeln (`web/src/player/spawn.ts`)
- `validSpot(env, x, y, pavement=true)`: im Spielgebiet, nicht in Collidern/Gebaeuden, nicht Bahnland (`railzone.json`), nicht Gleis (Tram-Mittellinie +-2.3 m), nicht Wasser, 0.5 m Abstand zu Waenden, nicht auf der Fahrbahn (`onRoad`), nicht an Boeschungen (Gefaelle > 0.3 auf 3 m), nicht auf Dach/Deck-Ebene (> 2.5 m ueber Terrain) und nicht unter Bruecke/Decke (< 4.5 m), nicht in Landmark-Innenraeumen (`solidAt`).
- `findGoodSpot`: naechster solcher Punkt (Spirale bis 250 m), sonst Rueckfall auf den alten, lockeren `findSpot` (nur frei stehen).
- Kartensprung und Zufallsstart benutzen `findGoodSpot`; explizites `?at=` bleibt wie vorher (nur raus aus Wand/Wasser/Gleis, `?exact` unveraendert).
- Frischer Start (kein `?at`, keine Speicherung): zufaelliger Eintrag aus `web/public/data/spawns.json`. Gespeicherte Position: nur uebernommen, wenn `validSpot(..., true)`; sonst naechster kuratierter Ort.

## Liste (`pipeline/spawns.py`, 25 Orte)
Seeds + Blickziel stehen in `pipeline/spawns.py`. `spawns.py --snap http://localhost:5173` (Dev-Server noetig) laesst `web/tests/qa_spawn.mjs --snap` jeden Seed auf den naechsten gueltigen Punkt (<= 70 m) mit freier Sicht (14 m voraus, 5 m zurueck, +-1 m seitlich frei von Collidern), ohne Fahrbahn im Umkreis 2 m, nicht in einer Senke (z.B. Stadion-Rasen) schieben und das Yaw auf das Blickziel richten.

| Ort | x | y |
|---|---|---|
| Ni-Una-Menos-Platz | 784 | -886 |
| Langstrasse Mitte | 833 | -487 |
| Langstrasse Brauerstrasse | 718 | -687 |
| Idaplatz | -125 | -1117 |
| Bullingerplatz | -41 | -496 |
| Stauffacher | 933 | -1219 |
| Escher-Wyss-Platz | 452 | 750 |
| Turbinenplatz | -4 | 633 |
| Josefwiese | 486 | 201 |
| Lochergut | 68 | -971 |
| Roentgenplatz | 758 | 126 |
| Letzigrund | -1060 | -240 |
| Kasernenareal | 1117 | -840 |
| Kanzlei | 693 | -973 |
| Baeckeranlage | 528 | -693 |
| Limmatplatz | 1130 | 60 |
| Hardplatz | -108 | -195 |
| Albisriederplatz | -472 | -671 |
| Hohlstrasse Kollerhof | 737 | -739 |
| Lindenplatz Altstetten | -2345 | 352 |
| Bahnhof Wiedikon | 455 | -1441 |
| Schlachthof Herdernstrasse | -776 | 35 |
| Freitag-Turm | 203 | 135 |
| HB Bahnhofplatz | 1735 | -700 |
| HB Europaallee | 1330 | -560 |

## Tests
`node web/tests/qa_spawn.mjs http://localhost:5173 pc`: alle Spawns (gueltig, freie Sicht, nicht Fahrbahn/Senke/Wasser), 30 Zufalls-Teleports (gueltig, im Spielgebiet, nicht Wasser/Collider), Frischstart ohne `?at`, danach die alten Problemstellen. Kontaktbogen: `preview/spawns_sheet.jpg`.
