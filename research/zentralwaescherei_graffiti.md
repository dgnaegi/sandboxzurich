# Zentralwaescherei: Graffiti-Referenz und Umsetzung

Stand 2026-10-18. Umsetzung: **Variante (b)**, die Wandbilder sind eigene prozedurale Nachzeichnungen (`pipeline/landmarks/zw_graffiti.py`, Parameter in `pipeline/overrides/zw_graffiti.json`). Aus den Fotos wird **kein Pixel** uebernommen.

Begruendung: `docs/DATA_SOURCES.md` erlaubt Commons/Mapillary/Panoramax-Fotos nur pro Bild und (HB-Regel) nur als Referenz, nie als Textur; ausserdem sind Graffitis urheberrechtlich geschuetzte Werke der Sprayenden, eine entzerrte Foto-Textur wuerde sie kopieren. Slogans/politische Parolen (z.B. grosse Streik-Schrift, Plakattexte) sind bewusst weggelassen; Buchstaben sind erfundene Fantasiewoerter (FLOW, DREH, SOLO ...). Keine Google-/Instagram-Bilder verwendet.

Kontaktbogen: `preview/ref_zw_graffiti.jpg` (Nummern = Index in `research/v3/photos_k4w4_zw.json`, Dateien in `data/raw/photos/v3/zentralwaescherei/`, Lizenz je Bild unten und in `research/v3/CREDITS_k4w4.md`). Vergleich Foto | Spiel: `preview/zw_graffiti_cmp.jpg`.

## Wandkartierung (Foto -> Spielwand)

| Wand (Atlas-Name) | Ort | Grösse | Hauptfarben | Stil | Foto |
|---|---|---|---|---|---|
| kiosk | Eckkiosk Neue Hard, Strassenseiten | 3 Segmente à 3.4 x 3.4 m | Rosa #e8a2b0, Schwarz/Weiss, Gelb/Blau | Plakate (Konzert-/Bandplakate), Sticker, kleine Tags | #34 #35 |
| wall_r | Mauer rechts des Kiosks | 10 x 2.5 m | Grau, Schwarz/Weiss, Rot | Plakate, S/W-Fotoplakate, Tags | #34 |
| wall_l | Mauer links des Kiosks | 10 x 2.5 m | Hellblau/Mint, Orange, Gruen, Pink | gestapelte Bubble-Pieces, Farbfelder | #33 #35 |
| mural | Wandbild an Hauptbau-Sockel (Strassenseite) | 18 x 3 m | Orange, Gelb, Blau, Pink auf Hellgrau | Wildstyle-/Bubble-Pieces mit weissen Outlines | #37 (Hardbruecke), #108 |
| passage | Eingangsdurchgang (Kioskecken) | 3 x 2 m | Weiss, Olive/Schwarz, Rot | ein grosses Piece, viele Tags | #7 |
| pink | pink beleuchteter Durchgang (Kioskecken) | 3 x 2 m | Magenta, Violett, Rosa | Pieces mit Schwuengen | #132 |
| klein | Kleinwaescherei-Mauer (im Atlas, noch nicht platziert) | 10 x 1.7 m | Grau, Pink, Tuerkis, Schwarz | Bubble-Piece, Figur | #128 |

## Lizenzen der Referenzfotos (nur Referenz)

- #1 commons | CC BY 4.0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Bitwaescherei_Balcony,_Zurich,_2025-03-26_(1).png
- #2 commons | CC BY 4.0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Bitwaescherei_Balcony,_Zurich,_2025-03-26_(2).png
- #5 commons | CC BY-SA 4.0 | Medea7 | https://commons.wikimedia.org/wiki/File:Bitw%C3%A4scherei_Flur.jpg
- #6 commons | CC BY-SA 4.0 | Medea7 | https://commons.wikimedia.org/wiki/File:Bitw%C3%A4scherei_Treppenhaus.jpg
- #7 commons | CC BY-SA 4.0 | Medea7 | https://commons.wikimedia.org/wiki/File:Bitw%C3%A4scherei_Z%C3%BCrich_Eingang.jpg
- #15 commons | CC BY 4.0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Fridge,_Bitwaescherei,_2025-03.png
- #17 commons | CC BY 2.0 | Thomas8047 | https://commons.wikimedia.org/wiki/File:In_any_wind_and_weather_(14342870911).jpg
- #33 commons | CC BY 4.0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Zentralwaescherei_3rd_floor_elevator.png
- #34 commons | CC BY-SA 4.0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Zentralw%C3%A4scherei,_Z%C3%BCrich.jpg
- #35 commons | CC0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Zentralw%C3%A4scherei,_Z%C3%BCrich.png
- #36 commons | CC0 | OpenCatMap | https://commons.wikimedia.org/wiki/File:Zentralw%C3%A4scherei_3rd_floor_balcony_view.jpg
- #37 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_(48677545001).jpg
- #63 commons | CC BY 2.0 | Thomas8047 | https://commons.wikimedia.org/wiki/File:Serenading_(14303662557).jpg
- #64 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_(48677545356).jpg
- #65 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_(48677717622).jpg
- #66 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_(48677717837).jpg
- #67 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_(48705024698).jpg
- #68 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_-_Freitag_Flagship_Store_Z%C3%BCrich_(48677206908).jpg
- #69 commons | CC BY 2.0 | Fred Romero from Paris, France | https://commons.wikimedia.org/wiki/File:Z%C3%BCrich_-_Freitag_Flagship_Store_Z%C3%BCrich_(48677543516).jpg
- #108 panoramax | CC-BY-SA-4.0 | paulb_imagery | https://api.panoramax.xyz/#focus=pic&pic=3b890687-0e30-400b-b9f3-820dca2fabf8
- #109 panoramax | CC-BY-SA-4.0 | paulb_imagery | https://api.panoramax.xyz/#focus=pic&pic=401a54e5-cd37-4400-ae5d-e6f43258d5ad
- #110 panoramax | CC-BY-SA-4.0 | paulb_imagery | https://api.panoramax.xyz/#focus=pic&pic=9ce7ebb0-8a08-42ba-90a2-4826edea03e7
- #128 mapillary | CC BY-SA 4.0 | openrailme | https://www.mapillary.com/app/?pKey=750816057971318
- #129 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=141863624621192
- #130 mapillary | CC BY-SA 4.0 | sp8962de | https://www.mapillary.com/app/?pKey=280511530392125
- #132 mapillary | CC BY-SA 4.0 | opencatmap | https://www.mapillary.com/app/?pKey=1153273949762080
- #134 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=1164900187669835
- #135 mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=1481112272469593
- #136 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=496521771489314
- #137 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=5725609364175861
- #138 mapillary | CC BY-SA 4.0 | fcignat | https://www.mapillary.com/app/?pKey=1369576414320125
- #139 mapillary | CC BY-SA 4.0 | fcignat | https://www.mapillary.com/app/?pKey=1004805148534973
- #141 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=228573209064284
- #142 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=1685565814962772
- #144 mapillary | CC BY-SA 4.0 | fcignat | https://www.mapillary.com/app/?pKey=755912283534038
- #145 mapillary | CC BY-SA 4.0 | fcignat | https://www.mapillary.com/app/?pKey=3457826357692010
- #146 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=1671211826601784
- #147 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=285897976539385
- #148 mapillary | CC BY-SA 4.0 | fcignat | https://www.mapillary.com/app/?pKey=730048446380983
- #126 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=668090843983828
- #127 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=174866614512653
- #125 mapillary | CC BY-SA 4.0 | till | https://www.mapillary.com/app/?pKey=380365809857103
- #13 commons | CC BY-SA 3.0 | Roland zh | https://commons.wikimedia.org/wiki/File:Escher_Wyss_-_Schiffbau_2011-08-08_13-50-40_ShiftN2.jpg
- #12 commons | CC BY-SA 4.0 | Medea7 | https://commons.wikimedia.org/wiki/File:Editathon_Bitw%C3%A4scherei.jpg

Weitere Fotos im Kontaktbogen von `research/v3/` (149 total, Liste in `CREDITS_k4w4.md`).

## Technik

- Atlas 2048x1024 -> `web/public/tex/zw_graffiti.webp` (+ `_half.webp` 1024x512). Im Modell eingebettet: 1536x768 (Material «graf», ersetzt die frueheren Zufalls-Graffitis); Landmark-GLB +290 kB.
- Platzierung: `pipeline/landmarks/k4w4_zentralwaescherei.py` (Kioskkanten, Mauern beidseits, Mural am Hauptbau). Rebuild: `cd pipeline/landmarks && ../../.venv/bin/python k4w4_zentralwaescherei.py` (schreibt auch landmarks.json via merge). Keine Kachel-Neuberechnung noetig, Landmark ist ein separates GLB.
## Stand zweite Runde (2026-10-18)
- Malstil dichter: Wildstyle (3D-Block, dicke Outline, Verlauf, Highlight, Sterne), Chrome-Throw-ups, Tags (Schwarz/Rot/Blau, Drips), Sticker, helle Papier-Plakate mit Rissen (schwarze Blöcke waren Plakate mit dunkler Palettenfarbe als Papier, jetzt immer helles Papier). Wand «klein» und Seiten-/Rückwände/Sockel des Hauptbaus als Decals.
- Pflanzen: `pipeline/landmarks/zw_plants.py`, Kreuz-Alpha-Karten (Atlas 512x256, Alpha-Test): Efeu über Mauern, Gras/Unkraut am Mauerfuss, Büsche in Kästen (Dach, Vorplatz), Bäume hinter den Mauern.
- Schild «Zentralwäscherei»: auf Kioskkanten begrenzt (max. 5.6 m, innerhalb der Kante).
- GLB: Graffiti-Atlas 2048x1024 als JPEG (q80) statt PNG, Gesamt ca. 1.06 MB (vorher 1.64 MB). lm.py: optionales `_jpeg_q` und `alpha_mask`; landmarks3d.ts: alphaTest-Material (Pflanzen) bleibt erhalten, Handy verkleinert via shrink().
- Offen: Türen/Rollläden/Rohre nicht einzeln bemalt; Ort der Decals am Hauptbau nicht verifiziert.
