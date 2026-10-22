# Zone 4 Landmark-Runde an den Kamerapunkten (Agent z4L, 2026-10-22)

Alle 16 Punkte (Wiedikon). Werkzeug: Fotos `data/raw/photos/z4/*` (Mapillary CC BY-SA, Commons), Spielbild von der Fotopose (`free_shot.mjs`), Grundrisskarten pro Punkt mit swissBUILDINGS3D-Id-Kuerzeln (Skripte im Scratchpad), Vorher-Bogen `preview/zone4_before2.jpg`.
Code: `pipeline/landmarks/z4L_houses.py` -> `pipeline/overrides/landmarks_z4L.json` (10 Landmarks, 972 kB GLB). Bogen (nur Landmarks, Kachelhaeuser/Boden ausgeblendet): `preview/z4L_landmarks.jpg`.
**Wichtig:** Landmarks z-fighten im Dev-Spiel mit den Kachelhaeusern (Lehre 14); sauber erst nach dem Build der Kacheln unten. Hausbezug ueber Footprint-Karte + Foto (Heading bis 90 Grad falsch, Lehre 15); Farben aus den Fotos geschaetzt.

| Punkt | Foto-Befund | Fix | Note vorher -> nachher (geschaetzt) |
|---|---|---|---|
| 1 Idaplatz Mitte | Idaplatz 1 (schon Landmark) stimmt, Fassade gegenueber gelb mit Laeden, im Spiel aehnlich | keiner | 3.3 -> 3.3 |
| 2 Idaplatz Nord | Eckhaus links mit rundem Erker, aprikose/lachsrosa; Spiel weiss | `z4L_berta_corner` (73CE65F7) | 3.0 -> 3.4 |
| 3 Idastrasse Sued | gelb/ocker Eckhaeuser, Spiel in Farbe aehnlich, Bauzaun/Gerueste im Foto | keiner | 3.2 -> 3.2 |
| 4 Bertastrasse | Kreuzung: Nordecke aprikose mit Erkerturm, Spiel weisser Block | `z4L_berta_corner` | 3.0 -> 3.4 |
| 5 Gertrudstrasse | Kirche (Landmark), Ostseite mint/violettgrau statt Spiel gelb/rot (Hex-Fix war Absicht, Foto-Zuordnung unsicher) | keiner (Ticket Z4L-3) | 3.0 -> 3.0 |
| 6 Aemtler/Wiesendanger | nur ein Foto (Dashcam, Baumallee, Sandsteinmauer), kein Haus zuordenbar | keiner | 3.0 -> 3.0 |
| 7 Zentralstrasse | links korallrosa Eckhaus mit Laden, rechts hellgrauer Putzbau mit Vordach; im Spiel grauer Kasten | keiner (Ticket Z4L-4) | 3.0 -> 3.0 |
| 8 Zurlindenstr. West | links cremefarbenes Eckhaus mit rotbraunen Fensterladen + Mansarde, rechts langer cremefarbener Putzbau mit Fensterband; Spiel: bunte Fassade, grauer Block mit schiefen Fenstern | `z4L_zurl_cream` (E8B3B705, EE5026FA), `z4L_zurl_hall` (E0E3141D) | 3.0 -> 3.6 |
| 9 Zurlindenstr. Ost | orange Balkonblocks (Spiel schon orange), weissgrauer Putzbau mit grauen Laeden | keiner | 3.2 -> 3.2 |
| 10 Thomasweg | NO-Zeile lachsrosa Gruenderzeit mit hellem EG, SW 1960er-Block creme/grau mit gestapelten Balkonen; Spiel: weiss bzw. blaugrau | `z4L_thomas_pink`, `z4L_thomas_pink2`, `z4L_thomas_slab` (FF32AF40, 0A1E597D / 8B58C21D, 3047D6E4 / 77853EEB) | 3.0 -> 3.5 |
| 11 Schmiede | grauweisser Balkonblock ueber dem Migros-EG (Mapillary 2024/25) | `z4L_migros_block` (F1D13DBA, 13D1BD0B, 4FF1E905) | 3.0 -> 3.3 |
| 12 Bahnhof Vorplatz | nur Commons-Fotos ohne Heading (Tram-Schleife, hellgruenes Haus mit dunklen Laeden) | keiner (Ticket Z4L-5) | 3.0 -> 3.0 |
| 13 Goldbrunnenplatz | creme Haeuser mit roten Markisen/Balkonen, Spiel creme-weiss; OGD-Baustelle im Spiel (T-S3) | keiner | 3.0 -> 3.0 |
| 14 Friedhof Sihlfeld | Sandsteinmauer mit Pfeilern und Eisengitter (Fotos 1/2), Spiel: keine Mauer | keiner (Ticket Z4L-1) | 3.0 -> 3.0 |
| 15 Ortsmuseum | geschwungene braun-orange Wohnbloecke (Neues Bauen, Bandbalkone) beidseits der Steinstrasse; Spiel rosa/gelb | `z4L_curved_stein`, `z4L_curved_stein_w` (39E73AF7, 3C0C73EF, 294CDD5E, 212C768A / F8D774F8, F5A9251E, B056B3A7, F939C481) | 3.2 -> 3.7 |
| 16 Kalkbreite | freistehendes weisses Haus mit dunklen Fensterladen und steilem Dach am Tramknoten (Commons 16.2); gruengrauer Block (96B0) stimmt schon | `z4L_kalk_house` (9C8144E4) | 3.0 -> 3.4 |

Durchschnitt geschaetzt 3.1 -> 3.3 (Kachelbau noetig, sonst Z-Fighting). Keine Ladennamen verwendet.

## Tickets
- Z4L-1 Friedhof Sihlfeld: Sandsteinmauer mit Pfeilern/Eisengitter laengs der Aemtlerstrasse (Mapillary 14.1/14.2) und Haupteingang-Portal (T-S7) – braucht Linien-Landmark (Mauer entlang Polygon), kein Haus-Kit.
- Z4L-2 Haeuser ohne gesicherte Zuordnung wegen Foto-Heading (Lehre 15): Idaplatz Nord SO-Seite (Eckhaus Chorlama-Ecke, graue Steinfassade mit Eisenbalkonen), Zurlindenstr. West Gebaeude mit Giebel (8.3 rechts), Thomasweg weisser Eckblock mit Glas-EG (10.1) – mit Hausnummernfoto oder zwei sich deckenden Fotos nachziehen.
- Z4L-3 Gertrudstrasse: Spiel zeigt rotes/gelbes Eckhaus, Fotos (Dashcam 5.1/5.2) mintweiss + violettgrau; erst klaeren, ob Hex-Fix (Lachsrot) das richtige Haus trifft.
- Z4L-4 Zentralstrasse Punkt: kleiner grauer Kasten (63CC, 5 m) im Spiel vs. Foto 7.0 (heller Putzbau mit Vordach); Eckhaus korallrosa links (F4A0/B006?). Kit kennt keine Vordaecher.
- Z4L-5 Bahnhof Wiedikon: Aufnahmegebaeude (T-S2) im Footprint-Datensatz nicht auffindbar (Courtyard-Karte zeigt nur Wohnbloecke); Tram-Schleife und hellgruenes Haus (Commons) ohne Pose.
- Z4L-6 Erker/Mansarden/Dachgauben nicht im Kit (berta_corner, zurl_cream): runde Erkertuerme sind schlichte Quader.
- Z4L-7 Kalkbreite: Uto-Kino-Haus (graue Fassade, Vordach) und Glasbau; Hausbezug offen.

## Kacheln zum Neubau (Hides, Kachelgroesse 200 m, t_<floor(x/200)>_<floor(y/200)>)
t_-1_-6 (Berta-Ecke, Zurlindenstr. West), t_0_-6 (Putzbau), t_-1_-5 (Thomasweg), t_1_-6 (Kalkbreite), t_1_-9, t_1_-8 (Birmensdorferstr. Migros, Steinstrasse O), t_0_-9 (Steinstrasse W). Zur Sicherheit Nachbarn t_-1_-7, t_0_-5.
