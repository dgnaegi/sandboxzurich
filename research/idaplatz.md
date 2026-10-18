# Idaplatz-Quartier (Kreis 3, Sihlfeld/Wiedikon): Realitaets-Notizen

Stand 2026-10-18. Quellen: 169 Referenzfotos (Mapillary 106, Commons 63; `research/v3/photos_ida.json`, Index `research/v3/ida_index.json`, Kontaktbogen `preview/ref_ida_*.jpg`, Credits `research/idaplatz_CREDITS.md`),
93 Fassaden-Crops (`research/buildings/ida/photos.json`, Bogen `preview/ref_ida_fac_*.jpg`), OSM, OGD (Baum-, Sitzbank-, Brunnenkataster), SWISSIMAGE (`preview/sheet_idaplatz.jpg`), swissBUILDINGS3D.

## Wichtig: Platzmitte
Der Idaplatz liegt bei OSM-Koordinate (-125, -1115) bzw. Platzmitte rund (-135, -1102) in lokalen Metern (WGS84 47.3741, 8.5148). `places.json` (ll 47.3709 / 8.5195, also x 237 / y -1465) und die Fotoliste v3 lagen bis 350 m daneben (siehe DECISIONS #113). Der Spawn nutzt den OSM-Namen und ist korrekt; das alte Ziel (237/-1465) ist Bahnhof Wiedikon-Nahe.
Vor der Erweiterung lag der Platz 197 m ausserhalb des Spielgebiets (nicht, wie angenommen, 186 m innen).

## Spielgebiet
Neues Rechteck 800 x 800 m um (-125, -1115) in `pipeline/overrides/playarea_extra.json` (Zurlinden-, Berta-, Gertrud-, Aemtler-, Eschwiesen-, Idastrasse, Sihlfeld-/Weststrasse). Zweierstrasse liegt ~650 m ostwaerts und ist nicht Teil davon.
Fläche 6.93 -> 7.27 km2, 221 -> 227 Spielkacheln (neu: -4_-8, -3_-8, -2_-8, -2_-7, -1_-7, -1_-6; -4_-9 wird Kulisse).

## Platz (nach Fotos #0 #1 #4 #13 #37 #47 #81 und Orthofoto)
- Rautenfoermiger Kiesplatz (sandfarben, kein Pflaster) zwischen Zurlindenstrasse (NO), Bertastrasse (NW), Idastrasse/Idaplatz (SW); Randsteine aus Granit.
- ~14 Platz- und Randbaeume (Kirschpflaumen, Zier-Kirschen, Spitzahorn laut Baumkataster, 2005-2023 gepflanzt), davon viele mit roten Blaettern (Blutpflaume) entlang Bertastrasse.
- Trinkbrunnen mit Schwan (OGD/OSM) bei (-142, -1095), 17 Baenke (OGD) in der Platzmitte.
- Sehr viele Velostaender (Fotos #4 #49 #52 #116 #120): Reihen am SW-Rand und an der Bertastrasse; Velo-/E-Bike-Verleih.
- Gastro-Aussensitze: Bottega Berta (Metalltische auf Kies, rote Neonlinie), Calvados, Babette (rote/blaue Tische, rote Markise) an der Zentralstrasse.
- Hängende Strassenlampen an Querseilen, Baustellenzaun mit Plakaten am Platzrand (2025, bewusst nicht uebernommen).

## Haeuser (Notizen in `research/buildings/notes_raw_ida_00*.tsv`)
- Platzhaeuser Gruenderzeit (Idaplatz 1-10), 7-8 Geschosse: ockergelb/beige/hellgrau, EG Laeden mit grossen Schaufenstern, Wandbild/Graffiti an Idaplatz 1.
- Genossenschaftsbloecke 1910-1932 (Weststrasse, Sihlfeldstrasse, Idastrasse, Eschwiesenstrasse): hellgrauer Rauhputz, graugruene Balkonbruestungen, beigegraue Lamellenladen, Hecken; Eschwiesen-/Gertrud-/Kalkbreitestrasse orange-ocker mit durchlaufenden Betonbalkonen.
- Zurlindenstrasse: beige bis weisse Putzbauten mit braunen Laeden, Rundbogenportale.
- Aemtlerstrasse: Trolleybus-Fahrleitung, Haltestelle mit Glasdach, weisse/cremefarbene Haeuser mit Balkonen.

## Landmarks (`pipeline/landmarks/ida_*.py`, `pipeline/overrides/landmarks_ida.json`)
- Herz-Jesu-Kirche Wiedikon (914B47B7, 1921): beiger Putz, Satteldach, Turm mit Pyramidenhelm (Commons-Foto #38).
- Idaplatz 1, 8, 9, 10 (Platzhaeuser) als Blockmodelle mit EG-Laeden.

## Laeden (`research/shops_v3/ida_entries.json`)
Nur Eintraege mit sicherem Foto: Bottega Berta, pompon. Alle anderen OSM-POIs (Le Calvados, Berta Bar, Chornlade, Smoking Kiosk, Tapas & Friends, La Piccola Trattoria, Gertrudhof, Beke ...) haben noch keine Fassadenfotos in der noetigen Naehe; sie bekommen den Laufzeit-Stil. Babette (Zentralstrasse, gemäss Foto #11) ist nicht in OSM.

## Offen
- Schwarzer Neubau mit weissen Fensterrahmen (Commons #5/#41, Eschwiesen-/Gertrudstrasse) nicht verortet.
- Laden-Fotos fuer die Gastro-Betriebe rund um den Platz (Panoramax lieferte beim Lauf HTTP 500).

## Korrekturrunde 2026-10-18 (Idaplatz 2)
- Mintgruene Westzeile: Aemtlerstrasse 82 (OSM-Gebaeude ohne addr-Tags) bekam keine Notiz und fiel auf die Fallback-Palette (210,219,207). Systemischer Fix in `pipeline/build_testarea.py`: Notiz per GWR-Eingangsadresse (im Footprint) zuordnen, wenn OSM keine Adresse traegt. Betrifft ~416 Gebaeude im Spielgebiet (346 mit Foto-Notiz).
- `notes_raw_ida_001..003.tsv`: 31 Zeilen hatten einen Trenner zu viel (Spalten verschoben: Erker/Balkon/Stil gingen verloren); korrigiert.
- Herz-Jesu-Kirche: Putz warm aprikosenbeige (#cdb48e statt Cremeweiss), Giebeldreiecke/Gesims mit Putztextur (flaches Trim-Material war weiss), Dach dunkelbraun (#4f3c36), Turmhelm rotbraun, ein Band kleiner Rundbogenfenster statt vierreihiger Hochfenster.
- Veloständer: `bikerack`-Objekte mit `"bikes": 0.7` (Fuellgrad) stellen in `places_detail.tile_meta` parkierte Velos (Kachel-Zeilen `bikes`, gleiches System wie OGD-Staender) in die Buegel.
