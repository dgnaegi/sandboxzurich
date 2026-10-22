# Zone 2 Gebiet Hardbrücke / Escher-Wyss (Agent z2a, 2026-10-22)

Werkzeug: Fotos `data/raw/photos/z2/*` (`research/zones/zone2_cam_photos.json`), Spielbilder per `pipeline/landmarks/free_shot.mjs` (Option `nob` blendet Kachelhäuser aus), Grundrisskarten mit swissBUILDINGS3D-Ids. Code `pipeline/landmarks/z2a_houses.py` (k4w4_kit), Register `pipeline/overrides/landmarks_z2a.json`.
**Wichtig:** Landmarks z-fighten im Dev-Spiel mit den Kachelhäusern (Lehre 14): sauber erst nach dem Build der betroffenen Kacheln.
Befund: Von den 6 Punkten stehen 5 auf/unter Brücken, Gleisen oder auf Plätzen ohne Fassaden im Blick. Fotos zeigen dort Brücke/Haltestelle/Prime Tower, kaum Häuser. Landmarks daher nur dort, wo Fotos ein Haus klar zeigen.

| Punkt | Foto-Befund | Fix | Note vorher -> nachher (geschätzt) |
|---|---|---|---|
| Escher-Wyss-Platz | Offener Platz unter der Rampe; Fotos von der Rampe (Mapillary 2024, h338/340) zeigen lange cremefarbene 3-Geschosser mit blauen Markisen NW des Platzes; graues 50er-Bürohaus mit Betonvordach an der Haltestelle (Mapillary 2023 d18) nicht eindeutig lokalisierbar | Landmark `z2a_ewp_nw_row` (ID_C6E83B, creme, Walmdach, blaue Markise; Id nach Fotopose, unsicher) | 3.0 -> 3.3 |
| Bahnhof Hardbrücke Perron | Punkt steht im Spiel auf Gleisen/Zug (Spiel: blauer Zugkasten füllt das Bild); Fotos nur Commons-Gleisbilder | nichts (Gleis-/Perroncode) | 2.0 -> 2.0 |
| Hardbrücke Fahrbahn | Fotos: Perrondach-Reihe, Prime Tower, Bushaltestelle; Häuser unter der Brücke (altes Backsteindach-Haus + Flachbau westlich der Gleise) nicht lokalisierbar | nichts | 3.0 -> 3.0 |
| Turbinenplatz | Westseite Technopark: langer 6-Geschosser, blaugraue Paneele, helle Balkonplatten je Geschoss, offenes Erdgeschoss; Südseite Hotel: dunkelblaues Fassadenband, weiss gerahmte Fenster, verglastes EG. Spiel: Technopark als blaue Glasfassade, Hotel hell-graukariert | Landmarks `z2a_technopark_wing` (ID_D75595, 83k Tris, Fassadenfarbe/Bänder), `z2a_novotel` (ID_892840, Hotel, ohne Schriftzug) | 3.0 -> 4.0 |
| Schiffbau | Landmark Schiffbau steht (Backstein, Bögen), Farbe plausibel; Punkt liegt unter der Hardbrücke an der Haltestelle, umliegende Blöcke generisch (braun-graue Kästchen) ohne Fotobeleg | nichts (Schiffbau nicht falsch) | 3.3 -> 3.3 |
| Prime Tower Fuss | Prime Tower + Plattform grün-türkis, im Spiel passend; Bahnhofsdach/Brücke dominieren | nichts | 3.5 -> 3.5 |

## Tickets
- Z2a-1 Perron Hardbrücke: Kamerapunkt (150,82,z -5) liegt auf Gleisen vor/in einem Zug; Punkt versetzen auf den Mittelperron und Perronkanten/Dach prüfen (Perron-Code, `hb*`).
- Z2a-2 Brücke (Hardbrücke) Fahrbahn: Decks im Spiel als graue Kästen mit dunkler Unterseite, Brüstung fehlt/zu hoch, Trolleybus-Fahrleitungen fehlen auf dem Deck (Brücken-/Oberleitungscode).
- Z2a-3 Escher-Wyss-Platz Ost: graues Bürohaus mit Betonvordach neben der Haltestelle (Mapillary 2023 d18 h153, 1435730236793615 Umgebung) fehlt; Id klären, Fotopose ±15 m. Cremefarbenes Haus mit Walmdach an der Rampe (Mapillary 2024 h213) ebenfalls.
- Z2a-4 Kleine Altbauten westlich der Gleise bei der Hardbrücke (Commons 2019, Backstein-Walmdach + Flachbau mit Graffiti): nicht als Landmark gebaut, Standort per Foto nicht ermittelbar.
- Z2a-5 Technopark/Hotel: Schriftzüge TECHNOPARK / NOVOTEL auf dem Dach fehlen (bewusst, keine Logos); Technopark-Wing hat 83k Tris, bei Bedarf Footprint weiter vereinfachen.
- Z2a-6 Schiffbau: rote Bogenumrandungen und Ziegel-Zweifarbigkeit prüfen (Landmark nicht in meinen Dateien).
- Z2a-7 Haltestelle Schiffbau/Hardstrasse: Gleise liegen unter der Brücke, Bahnsteig fehlt im Foto-Vergleich (Haltestellencode).

## Kacheln neu bauen (Hides)
`t_-1_2` (Hotel, Hide (-20,569)), `t_-1_3` (Technopark, Hide (-63,637); Footprint reicht auch in `t_-1_2`), `t_1_4` (EWP-Zeile, Hide (363,815)). Kachelgrösse 200 m, Index = floor(x/200), floor(y/200).
