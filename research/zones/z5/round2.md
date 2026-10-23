# Zone 5 Runde 2 (Agent z5R2, 2026-10-22): Haus-Landmarks an den schwächsten Punkten

Skript `pipeline/landmarks/z5R2_houses.py` (8 Landmarks `z5R2_*`, Override `landmarks_z5R2.json`), Hausbezug nur über Footprint-Karte + Foto + freie Spielkamera (Lehre 15). Fotos: Mapillary/Panoramax/Commons (CC BY-SA), Farben nach Auge, keine Logos/Ladennamen.
Vorher `preview/zone5_r2before.jpg`. Landmarks wirken erst nach Kachel-Build (hide); bis dahin liegen sie über den alten Häusern.

| Punkt | Landmark | Befund / Beleg | Note vorher -> nachher (geschätzt, nach Build) |
|---|---|---|---|
| Hohlstrasse/Flurstrasse (Letzitürme, T-F1) | `tower_white` (F18E7438, 50 m), `tower_red_a/b` (26956397, A64F3BD7, 55 m) | Fotos Commons «Letziturm 2022», «Wohnsiedlung Letzi 2025», Mapillary 703328115763013: weisser Balkonturm + rot/weisses Turmpaar hinter der Backsteinhalle (Halle im Spiel gleiche Lage, Spielbild stimmt) | 3.5 -> 3.8 |
| Westpark | `westpark_office` (F9632E79, 29 m) | Mapillary 555853825895875 (Blick S) + Spielbild: langer Bürobau, graue Metall-/Steinfassade mit tiefen dunklen Fenstern statt hellblauem Glas | 3.0 -> 3.5 |
| Badenerstrasse West | `baden_sw_beige/orange/blau` (C57EEAD5, 2AAE4C8E, 3707C6E0), `baden_n_cream` (93B7A34F+ED032CFF) | Panoramax 0e5e3f50 + 5621d338: SW-Zeile 5 Geschosse (beige mit braunen Läden, orange, blaugrau Eck), Nordseite cremefarbener Neubau; Reihenfolge von beiden Seiten gegengeprüft | 3.0 -> 3.5 |
| Vulkanplatz, Baslerstrasse, Herdernstrasse, Hohlstrasse | nicht bearbeitet | siehe Tickets | unverändert |

Modellgrösse total ca. 700 kB (Westpark 100 kB nach Rasterverbreiterung, Türme 240 kB, Baden-Zeile 250 kB; `ls -l web/public/models/landmarks/z5R2_*`). Gemeinsame Kit-Texturen, keine eigenen Bilder.

## Zu bauende Kacheln
`t_-10_2`, `t_-9_2`, `t_-8_2` (Altstetten Baden-/Hohlstrasse, Letzitürme), `t_-1_3` (Westpark).

## Tickets
- R2-1 Vulkanplatz: Backsteinhalle «Autospenglerei» existiert (Spielbild passt), es fehlen Holztreppe/Lamellen; dunkel verkleideter Bau rechts (Foto ml_1311105446654123, ml_1420079912391278) und rosa/graue Bürobauten voraus nicht zuordenbar (Mapillary-Heading 90° falsch). Nötig: zweite Fotopose mit Adresse.
- R2-2 Westpark: roter Backsteinbau mit Balkonen + Gleisbogen-Rotweg (Fotos 0/3/4) nicht sicher einem Footprint zugeordnet (79EC0B84 27 m vermutet); Swisscom-Metallbau (Foto 5) Ort unbekannt (Förrlibuckstrasse). Rotweg = Boden-Ticket Z5c-3.
- R2-3 Baslerstrasse: Fotos zeigen 4-geschossige Balkonzeilen (beige, rote Balkonfronten) am Strassenrand und blauen Letzipark-Kopfbau; Zuordnung offen. Rote Velostreifen weiter Ticket T-B1.
- R2-4 Letzitürme: rot/weisse Streifen nur als Mischfarbe (kein Streifenmuster); Höhen aus swissBUILDINGS3D (50/55 m), Foto zeigt ~60 m für den Roten Turm.
- R2-5 Badenerstrasse: Wandbild «Shining Dog» (Luggwegstrasse-Eckhaus, grau verputzt, Fensterläden) nicht zugeordnet; Staffelgeschoss des Neubaus fehlt.
- R2-6 Hohlstrasse: Glasbürobau (Fotos 0/1 links) und Balkonbau im Bau weiter ungeklärt (Heading), Z5c-5 EGGER-Haus offen.
