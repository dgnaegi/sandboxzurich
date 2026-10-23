# Zone 3, Runde 2 (Agent z3R2, 2026-10-22): schwache Kamerapunkte, Haeuser

Werkzeug: Fotos `data/raw/photos/z3/*`, Fussabdruckkarte (swissBUILDINGS3D-Ids, Skript im Scratchpad), Spielbild von der Fotopose (`free_shot.mjs`, Variante mit Isolation: nur Landmarks sichtbar, weil die Kachelhaeuser bis zum Build mit den Landmarks z-fighten, Lehre 14). Bogen `preview/z3R2_vergleich.jpg` (links Foto, rechts Landmark isoliert), Vorher-Bogen `preview/zone3_r2before.jpg`.
Skript `pipeline/landmarks/z3R2_houses.py` (8 Landmarks, Kit `k4w4_kit.block_model`), Ausgabe `pipeline/overrides/landmarks_z3R2.json`, GLBs `web/public/models/landmarks/z3R2_*.glb`. `merge.py` und `apply_names.py` gelaufen.

## Landmarks (Quelle: Mapillary/Panoramax-Fotos, CC BY-SA, Farben geschaetzt, keine Logos)
| Landmark | Ids | Befund Foto | Fix | GLB |
|---|---|---|---|---|
| `z3R2_brau_n` | 2D0EE768 02E63929 FCCA3186 0CAB36AA 4E17324F B7092D2D | Brauerstrasse-Bogen: cremeweisser Putz, durchlaufende geschwungene Balkonplatten, Rundecke, verglastes EG, Flachdach mit Abtreppung. Spiel: blaugrauer Altbau-Raster mit bunten Ladenstreifen | Landmark mit Balkonbaendern (`floor_bands`), LiDAR-Staffelung, Glas-EG | 252 kB |
| `z3R2_brau_s` | 8A4DC12B CFB8EB2D 5B218972 | Suedlicher Bogen, gleiche Machart | wie oben, etwas heller | 149 kB |
| `z3R2_brau_row` | F64C47E7 D8B9722B DD9D80A9 917BF92B | Weisse Zeile SW der Strasse mit Balkonen (Mapillary 364198516329610) | wie oben, near-white | 107 kB |
| `z3R2_eris_w` / `_e` / `_n` | W: E00341F6 459BC898 4928F4C9 E519C7CB 9213CCA0 6E3465BC; O: B100545B 2327183A 1DFDAA59 D930E6B4 04A411BD FFE80347; N: 4714C360 8DC0297D 48D49CB0 ADD4C771 | Erismannhof (Genossenschaft, 1920er): ockergelber Putz, graublaue Fensterlaeden, dunkelrote Walmdaecher, 4 Geschosse + Dach. Spiel: gruenlich-blasser Putz, dunkelgruene Laeden | Landmarks: warmes Ocker (#e4c688), Rahmenfarbe graublau (Ersatz fuer Laeden), Walmdach #8c4a3a mit 6 m Anstieg | 149 / 151 / 112 kB |
| `z3R2_zyp_nw` | FC00114C 58A9E0BF 37B723BB | Zypressenstrasse NW-Zeile: beiger Putz, graugruene Erker/Laeden (Mapillary 783653180485285, 2425725217612512) | beige Zeile, Walmdach niedrig | 91 kB |
| `z3R2_zyp_yellow` | D9D49985 | gelbes Haus rechts vom roten Backstein-Eckhaus (Mapillary 698579288902806, Platz-Blick) | gelber Putz, Walmdach | 55 kB |

Summe GLB: ca. 1.07 MB (Texturen je 128x128 + 1024x128 Atlas, wenige kB; Vermeiden von Texturspeicher: gleiche Seeds innerhalb einer Familie moeglich, Laufzeit teilt aber nicht).

## Noten (geschaetzt, vorher -> nachher)
| Punkt | vorher | nachher | Bemerkung |
|---|---|---|---|
| Brauerstrasse West | 3.0 | 3.8 | Haeuser stimmen jetzt (Farbe, Balkonbaender, Rundecke); Bruecke/Gleise/Bueroglasbau offen (R2-1, R2-2) |
| Erismannhof | 3.8 | 4.2 | Farbe/Dach/Raster; Laeden nur als Rahmenfarbe (R2-3) |
| Zypressenstrasse | 3.4 | 3.8 | NW-Zeile + gelbes Haus, Ostseite weiter unklar (Z3b-4) |
| Bullingerplatz, Albisriederplatz, Hardstrasse/Bullingerstrasse, Seebahnstrasse, Sihlfeldstrasse | | unveraendert | Runde-1-Landmarks gegen Fotos geprueft (Farben stimmen); keine neue Evidenz |
| Hohlstrasse/Hardstrasse, Hardplatz | | unveraendert | Fotos zeigen vor allem Bruecke/Trog (Z3c-1), keine Hausfrage |

## Zu bauende Kacheln
`t_-1_-3 t_0_-3 t_1_-3 t_2_-3` (Landmarks verdecken die Kachelhaeuser erst nach dem Build, hide-Punkte gesetzt). Danach `python pipeline/zones/zone_cmp.py 3 after`.

## Tickets
- R2-1 Bueroglasbau Hardbruecke/Brauerstrasse (anthrazitgraue Rasterfassade mit dunklen Fenstern, ca. 70 m lang, auf Fotos 2/3/4/5 von der Bruecke; im Spiel hellgrau-weiss): Zuordnung zu F8335B5F/79F9/68B9 nicht gesichert (Fussabdruck 626 m2 passt nicht zur Laenge), nicht angefasst. Mit Orthofoto klaeren.
- R2-2 Brauerstrasse-Bruecke: Rampen/Bruestung (grosse graue Brocken im Kamerapunkt-Bild, Tramgleise fehlen) bleibt Bruecken-/Gleiscode (siehe Z3b-6).
- R2-3 Fensterlaeden (Erismannhof, Zypressenstrasse): im Kit nur Rahmenfarbe; echte Laden-Quads (hz_kit `shutter_quad`) wuerden den Eindruck heben, brauchen `block_model`-Hook auf Fensterposition.
- R2-4 Silberglas-Bandfensterhaus Zypressenstrasse/Sihlfeldstrasse (Mapillary ml_1121408482694988 rechts, Kandidat 0A0F, 26 m): Zuordnung nur aus einer Fotopose, nicht gebaut.
- R2-5 Sihlfeldstrasse Ostseite orange-braunes Balkonhaus mit Laeden (Mapillary 4672603846102916): Id weiter offen (Z3b-4).
- R2-6 Gelbes Haus Zypressenstrasse (D9D49985) aus Platz-Blick abgeleitet; Foto ml_783653180485285 (Strassenblick) widerspricht evtl. in der Reihenfolge Rot/Gelb (Mapillary-Heading unzuverlaessig).
- R2-7 Server-Last: Dev-Server war lange nicht erreichbar (mehrere Playwright-Browser parallel, Load 27).
