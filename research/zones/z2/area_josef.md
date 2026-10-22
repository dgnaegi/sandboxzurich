# Zone 2 Gebiet Josef (Agent z2b, 2026-10-22)

Punkte 7, 8, 10, 12, 13, 14 der Zone 2 (Josefwiese, Viadukt/Markthalle, Röntgenplatz, Josefstrasse, Heinrichstrasse, Fabrikstrasse).
Werkzeug: Fotos `data/raw/photos/z2/*` (Mapillary CC BY-SA, Panoramax, Commons), Spielbilder per `pipeline/landmarks/free_shot.mjs` von der Fotopose aus, Grundrisskarten mit swissBUILDINGS3D-Ids (Skripte im Scratchpad). Bogen `preview/z2b_cmp.jpg` (Foto | Spiel, nur Landmark sichtbar, weil die Kachelhäuser dafür ausgeblendet wurden).
Code: `pipeline/landmarks/z2b_markthalle.py`, `z2b_houses.py` -> `pipeline/overrides/landmarks_z2b.json` (5 Landmarks).
**Wichtig:** Landmarks z-fighten im Dev-Spiel mit den noch vorhandenen Kachelhäusern (Lehre 14). Die neuen Häuser sind erst nach dem Build der unten genannten Kacheln sauber (hide-Punkte gesetzt).

| Punkt | Foto-Befund | Fix | Note vorher -> nachher (geschätzt) |
|---|---|---|---|
| 7 Josefwiese | 10-geschossiger blaugrauer Plattenbau mit Treppenband und Balkonbändern (Commons Max Vogt 2024, Mapillary), niedriger Anbau mit Fensterband; Pavillon am Viaduktfuss einstöckig, weiss verputzt, dunkles Walmdach; Spiel: beiges Karo-Hochhaus, zweistöckiger grauer Kasten | Landmarks `z2b_josef_slab` (2FD78AE0, Farbe #b7c0cb, Bänder), `z2b_josef_pavilion` (9EE8989A, Walmdach dunkelbraun) | 3.0 -> 3.5 |
| 8 Viadukt (Markthalle) | Steinerne Rundbogenreihe mit Glasfronten (Restaurant Markthalle, Pie Shop), Deck oben mit Geländer; Spiel: gewöhnlicher Block mit Mural-Fassade und Fake-Läden unter grauem Deck (der Bogen-Landmark `k45_viadukt` endet bei den Einheiten an der Viaduktstrasse, das OSM-Gebäude «Markthalle Im Viadukt» fehlte) | Landmark `z2b_markthalle` (Bogenreihe aus dem OSM-Umriss, ~6.6 m je Bogen, gleicher Look wie Im Viadukt, Steinseiten, Deckgeländer, Fahrleitungsmasten) | 2.5 -> 4.0 |
| 10 Röntgenplatz | Westseite orange-ocker mit braunen Balkonen und rotbraunem Walmdach (Mapillary 0/1/5/6/10, Panoramax); Spiel: fliederfarbener Block; Ostseite rotes Randbau-Landmark bleibt (Fotos 11/12 rot) | Landmark `z2b_roent_west` (3236D5D0, 03CFE3C7, FAD7E0C1, #e0b77a, Walmdach #8f4b38) | 3.2 -> 3.7 |
| 12 Josefstrasse | Rechts dunkelbrauner Block mit Läden, links cremefarbener Block mit Fensterbändern (CB0B1A01), rechts Gründerzeithäuser aus Sandstein; Spiel stimmt in Farbe/Höhe (Abgleich aus den Fotoposen 1, 4, 6), nur Ornament (Balkone, Erker) fehlt | keiner (zu wenig Beleg für Einzelhäuser, siehe Z2b-4) | 3.5 -> 3.5 |
| 13 Heinrichstrasse | Links grosser cremefarbener Steinblock mit hohen Glasstreifen und dunkelgrünen Toren im EG (Panoramax 2024); Spiel: grauer Block mit blauem Fensterraster; Viadukt-Eisenbrücke über der Strasse im Spiel nur graue Platte | Landmark `z2b_heinrich_cream` (38F02D4E, #e8e2d4, EG dunkelgrün, gestufte Dachhöhen 10–28 m aus 3D-Daten) | 3.0 -> 3.8 |
| 14 Fabrikstrasse | Commons-Fotos (Geotags ungenau, kein Heading) zeigen gelbe Balkonscheibe mit Graffitisockel («Neugasse»), nicht eindeutig einem Haus zuordenbar; Spiel: rosa-rote Blöcke mit grünen Läden, pastellfarbene Nachbarn (Farbe nahe an Foto «Neugasse im Kreis 5») | keiner (Identität offen, siehe Z2b-5) | 3.0 -> 3.0 |

## Tickets
- Z2b-1 **Kacheln neu bauen** (Hide wirkt erst dann): t_3_1, t_3_2 (Markthalle, Heinrichstrasse), t_2_0 (Josefwiese Plattenbau), t_2_1 (Josefwiese Pavillon, Heinrichstrasse West), t_2_2 (Heinrichstrasse Randlage), t_3_0 (Röntgenplatz West). Zur Sicherheit Nachbarn t_2_0..t_3_2.
- Z2b-2 Viadukt Ost: Stahlfachwerkbrücken über Heinrichstrasse (Fotos Heinrichstrasse 3/5/6/7) und Limmatstrasse (Viadukt 10/14) fehlen bzw. sind graue Platten (Brücken-Code, `k45_viadukt` zeichnet nur Lücken 14–60 m zwischen Einheiten). Markthalle-Dach (schwarz, runde Oberlichter, Gitterzaun auf dem Deck, Fotos 7/8/11) nicht modelliert.
- Z2b-3 Josefwiese: Restaurant-Pavillon mit roten Sonnenschirmen/Aussensitzen (Commons Josefswiese.jpg) – kein Parasol-Objekt (wie Z3b-7). KVA-Hochhaus: Fensterschlitze statt Raster wären nötig (Kit hat nur Rasterfenster).
- Z2b-4 Josefstrasse: für Erker/Balkone der Gründerzeithäuser (SW-/NO-Seite) braucht es Fensterachsen-Zählung; Fotos nur schräg (Lehre 1/6).
- Z2b-5 Fabrikstrasse/Neugasse: Standort der gelben Balkonscheiben mit Graffitisockel klären (Commons «Zürich (48677544496/586/371)», vermutlich Neugasse/Hardau), dann 3–4 Blöcke (21–25 m, 6BA65396, 0850CB37, B75A07E8, 7A9881C8) auf Gelb/Grau-Balkonbänder umfärben (`floor_bands` im Kit).
- Z2b-6 Röntgenplatz: Brunnenrinne (lange Wasserrinne mit Steinrand, Mapillary 3/5/6) fehlt im Platz; Spiel-Pavillon (blaue Box) im Foto ein dunkles Flachdach auf Stützen.
- Z2b-7 Heinrichstrasse Fassade: runde Reliefknöpfe auf dem Steinblock (Panoramax 2024) nicht abbildbar ohne eigene Textur.

## Kacheln zum Neubau (Hides)
t_3_1, t_3_2 (Markthalle 719/413; Heinrichstrasse 604/385), t_2_0 (467/141), t_2_1 (482/232), t_3_0 (717/126), dazu Nachbarn t_2_2 falls der Heinrichstrassen-Block Teile in y > 400 hat.
