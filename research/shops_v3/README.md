# shops_v3: Foto-Recherche Ladenfronten

Methode: `pipeline/photos/fetch_shops.py` nimmt OSM-Lokale (Restaurant/Cafe/Bar/Pub/Fast-Food/Eisdiele und alle shop=* ausser Coiffeur/Beauty/Garage etc.) im Spielgebiet, sortiert nach Naehe zu Ankerpunkten (Langstrasse, Helvetiaplatz, Baeckeranlage, Josefstrasse, Badenerstrasse, Idaplatz, Hohlstrasse, Kalkbreite, Lochergut, Viadukt, Europaallee), nimmt die ersten 1100 (`candidates.json`) und holt per Mapillary Graph API Bilder im Umkreis von 4-26 m, Blickrichtung max. 25 Grad von der Richtung zum Lokal, keine Panoramen, bevorzugt neuere Bilder (max. 3 pro Lokal, thumb_1024). Bilder: `data/raw/photos/shops/<osm_id>_<n>.jpg`, Metadaten `photos.json`. Adressen aus `pois_kreis*.csv`/`gastro_match.csv` (Namensabgleich, teils leer/mit Hinweistext). Panoramax: siehe Runde 2.
Kontaktbögen (12 Lokale, `sheets/sheet_NN.jpg`, Zuordnung `sheets/index.json`), manuelle Sichtung in `annotations.jsonl`, zusammengeführt per `pipeline/photos/shops_build_json.py` zu `shops_v3.json`.

## Abdeckung
- 1100 Kandidaten, 585 mit mindestens einem Mapillary-Bild nach Filter.
- Gesichtet: Sheets 1-21 (252 Lokale, die priorisierten Gebiete). Davon nur 38 mit verwertbaren Angaben (`photo_ok=true`); 214 `false` (Lokal nicht erkennbar: Fahrzeugkamera, zu weit, verdeckt, Nachtbild, falsches Haus). Sheets 22-49 (333 Lokale) sind nicht gesichtet (`photo_ok=null`, Bilder liegen vor).
- Einige Angaben sind mit "Identitaet unsicher" markiert: Die Fassade ist sicher, die Zuordnung zum Namen nicht. Viadukt-Bogen gleichen sich (weisses Schild mit Bogennummer, Naturstein, Glasfront).

## Felder (shops_v3.json)
id, name, address, kind, area, x/y (lokale Meter), photos[], sheet, photo_ok, facade_color, fascia {bg,text,style}, awning {color,stripes}|null, shopwindow (gross/klein/Sprossen), door (mitte/corner/unsicher), seating, plants, neon (optional), notes. Unsichere Felder fehlen bzw. sind "unsicher"/null.

## Lücken
- Mapillary ist meist Fahrzeug-/Velokamera auf der Strasse: Schilder und Fassadenfarben sind selten lesbar. Bessere Quellen: eigene Fotos des Users, Panoramax-Nahaufnahmen.
- Schildfarben sind aus Entfernung geschätzt (Hex ungefähr).

## Runde 2 (Panoramax + Mapillary-360°)
Skripte: `pipeline/photos/shops_r2_fetch.py` (Download + Ausschnitte), `shops_r2_sheets.py` (Kontaktbögen), `shops_r2_ann.py` (Annotationen anhängen), Merge weiterhin `shops_build_json.py`.
- Quellen: Panoramax-STAC-Suche (api.panoramax.xyz, Bbox ±30 m um das Lokal) und Mapillary-Panoramen (is_pano, thumb_2048). Pro Lokal bis 2 Bilder (2.5-25 m Distanz, nur CC-BY/CC-BY-SA/CC0; alle Panoramax-Treffer waren CC-BY-SA-4.0).
- 360°-Bilder: perspektivischer Ausschnitt FOV 60°, 1024x768, Blickrichtung = Peilung Bildposition -> Lokal (Bild-Azimut aus Panoramax `view:azimuth` bzw. Mapillary `computed_compass_angle`). Normale Bilder: nur mit Blickrichtung <= 30° zum Lokal, 4:3-Ausschnitt um die Lokalrichtung (angenommenes Sichtfeld 110°).
- Cache/Bilder: `data/raw/photos/shops_r2/` (`_api` Antworten, `_src` Originale, `<id>_<n>.jpg` Ausschnitte); Metadaten `photos_r2.json`; Bögen `sheets_r2/` (58 Bögen, zuerst Lokale ohne photo_ok, dann R1-Bögen 22+ ohne R2-Bild); Notizen `annotations_r2.jsonl`.
- Ergebnis: 1100 Kandidaten, 577 mit R2-Bild (Panoramax-Flachbilder 423, Mapillary-360° 113, Panoramax-360° 41 als Hauptbild). In `shops_v3.json` haben Lokale mit R2-Bild das Feld `photos_r2` und bei Annotation `annotated_from` ("r2:panoramax"/"r2:mapillary"). R1-Annotationen wurden nicht überschrieben. R1-Bögen 22-49 wurden zusammen mit den R2-Bögen gesichtet (Lokale ohne R2-Bild und ohne Erkennung bleiben `photo_ok=null`/false).
- Grenzen: Viele Panoramax-Bilder sind ebenfalls Fahrrad-/Auto-Kameras, die Front ist nur am Rand sichtbar. Farben/Hex sind Schätzungen. Unsichere Zuordnungen (Viaduktbogen, gleiche Häuser) sind in den notes markiert.

## Runde 3 (Fassadennormale, 40 m, ungesehene Bilder)
Skripte: `pipeline/photos/shops_r3_fetch.py`, `shops_r3_sheets.py` (Bögen `sheets_r3/`, Variante `alt` = zweites Bild), `shops_r3_ann.py` (-> `annotations_r3.jsonl`); Merge wie bisher `shops_build_json.py` (Feld `photos_r3`, `annotated_from` = "r3:mapillary"/"r3:panoramax"). Bilder `data/raw/photos/shops_r3/`, Metadaten `photos_r3.json` (inkl. Commons-Geosuche je Lokal, nur als Kandidatenliste; nicht gesichtet).
- Nur Lokale ohne photo_ok. Bereits in R1/R2 gesichtete Bild-IDs sind ausgeschlossen. Radius 2.5-40 m (Panoramax-Bbox ±40 m, Mapillary Flach- UND 360°-Bilder).
- Fassadennormale: Strahl Kamera->Lokal wird mit dem OSM-Gebäudeumriss (`part_buildings_r.json`, Kante ≤ 8 m vom Lokal) geschnitten; Schrägwinkel (obliq) = Winkel zur Kantennormale, > 62° verworfen, kleiner Winkel bevorzugt. 360°-Ausschnitt zeigt auf den Auftreffpunkt (FOV 60°, ab 20 m 45°). Flachbilder nur ≤ 28° Blickabweichung, engerer Ausschnitt ab 20 m.
- Fussgänger/Handkamera bevorzugt: Mapillary-Sequenzgeschwindigkeit < 2.5 m/s bekommt Bonus (Dashcams/Autos nicht). Camera-Typ/Make/Model wird in `photos_r3.json` (cam) mitgespeichert.
- Ergebnis: 894 offene Lokale, 730 mit neuem Bild; 61 Bögen gesichtet, 143 Lokale neu annotiert (112 Mapillary, 31 Panoramax). Gesamt photo_ok = 349 von 1100 (Ziel ≥ 320). Viele R3-Treffer sind mit "Identität unsicher" markiert (Fernaufnahme, Nachbarlokal, Viaduktbögen).
- Nicht umgesetzt: (d) gemeinsame Ausschnitte pro Fassade (Nachbarlokale erscheinen aber oft mit demselben Bild; Fassade-Notes entsprechend), Commons-Bilder wurden nicht gesichtet.
