# shops_v3: Foto-Recherche Ladenfronten

Methode: `pipeline/photos/fetch_shops.py` nimmt OSM-Lokale (Restaurant/Cafe/Bar/Pub/Fast-Food/Eisdiele und alle shop=* ausser Coiffeur/Beauty/Garage etc.) im Spielgebiet, sortiert nach Naehe zu Ankerpunkten (Langstrasse, Helvetiaplatz, Baeckeranlage, Josefstrasse, Badenerstrasse, Idaplatz, Hohlstrasse, Kalkbreite, Lochergut, Viadukt, Europaallee), nimmt die ersten 1100 (`candidates.json`) und holt per Mapillary Graph API Bilder im Umkreis von 4-26 m, Blickrichtung max. 25 Grad von der Richtung zum Lokal, keine Panoramen, bevorzugt neuere Bilder (max. 3 pro Lokal, thumb_1024). Bilder: `data/raw/photos/shops/<osm_id>_<n>.jpg`, Metadaten `photos.json`. Adressen aus `pois_kreis*.csv`/`gastro_match.csv` (Namensabgleich, teils leer/mit Hinweistext). Panoramax wurde nicht ergaenzt.
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
