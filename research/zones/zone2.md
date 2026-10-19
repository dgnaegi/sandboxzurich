# Zone 2 Kreis 5 Industrie: Inventar Auftrag Z0 (Stand 2026-10-19)

Quellen: `research/zones/zone2_facades.json` (Fassaden, Auszug aus `research/buildings/visual_notes_v3.json`), `research/zones/zone2_facades_missing.json` (OSM-Adressen ohne Notiz), `research/zones/zone2_shops.json` (Laeden/Beizen), `research/zones/zone2_photos.json` + `zone2_sites.json` (Lueckenfotos, `pipeline/photos/fetch_z2.py`), `research/zones/zone2_sheet_index.json` (Bogen-Index), OSM (`data/raw/osm/part_*.json`, ODbL), `research/pois_kreis5.csv` + `pois_kreis5_osm.csv` (Ladenpruefung), Katalog `web/public/data/catalog.json`.
Polygon: `pipeline/overrides/zones.json` (Zone 2, 1 Rechteck x -250..2000, y -300..1300, 16 Kamerapunkte, 67 Kacheln).

Achtung Polygon: Das Rechteck enthaelt auch Adressen aus Quartieren ausserhalb des Kern-Industriequartiers (u.a. Nordstrasse 165, Seminarstrasse 71, Roetelstrasse 69, Imfeldstrasse 63, Rousseaustrasse 62). Diese Strassen haben KEINE Fassadennotiz. Entscheid fuer Nachbau: Prioritaet auf Kamerapunkte und Hauptstrassen im Kern (Viadukt, Josefstrasse, Limmatstrasse, Heinrichstrasse, Escher-Wyss, Hardbrücke).

## Haeuser
- 3 021 OSM-Adressen im Polygon (Strassen mit >= 20 Adressen: Nordstrasse 165, Limmatstrasse 74, Seminarstrasse 71, Josefstrasse 70, Roetelstrasse 69, Heinrichstrasse 68, Imfeldstrasse 63, Rousseaustrasse 62, Hoenggerstrasse 61, Rotbuchstrasse 61, Schaffhauserstrasse 59, Weinbergstrasse 56, Breitensteinstrasse 52, Stuessistrasse 52, Wasserwerkstrasse 49, Hofwiesenstrasse 48, Neugasse 47, Viaduktstrasse 41, Scheuchzerstrasse 40, Gasometerstrasse 38, Im Eisernen Zeit 37, Rothstrasse 37, Beckenhofstrasse 35, Habsburgstrasse 35, Lindenbachstrasse 35).
- 188 davon haben Fassadennotizen (Hex, Material, Stil, teils Geschosse/Dach/Fenster). Verteilung: Josefstrasse 31, Heinrichstrasse 30, Limmatstrasse 18, Rest verteilt.
- 2 833 ohne Notiz: Liste in `zone2_facades_missing.json`. Fassaden-Erfassung aus Fotos NOCH OFFEN.
- Dach: flach 28, Mansard 15, Sattel 3, ohne Angabe 141. Geschosse/Fenster nur teilweise.

## Plaetze und Orte (Kamerapunkte, Radius 60 m, OSM + Katalog)
### Escher-Wyss-Platz (448/696)
- Boden: Asphalt (48 Flaechen), Beton 1, Pflaster 1. Strassenbahn- und Bahnquerungen, Weichen (17 Tram, 11 Weichen).
- Baeume: keine in 60 m. Haltestellen: Katalog H5/H6/H1/H2 in 38-40 m (Gesamtposition nicht einzeln nach Foto geprueft).
- Brunnen: Katalog V2 (Trogbrunnen Stein) bei 31 m und 67 m. Variante per Foto PRUEFEN.
- Fotos: 5 lokale Fotos im 60-m-Radius (vorher duenn), Lueckenfotos geholt.

### Bahnhof Hardbruecke Perron (28/111) und Hardbruecke Fahrbahn (28/40)
- Boden: Asphalt (42), Pflaster (9), Kleinsteinpflaster/Sett (5). Treppen (24), Lift (7), Automat (5), Bushaltestelle (4).
- Gleise (Bahn, 16 Fahrbahn), Weichen (11). Keine Baeume.
- Fotos: 108 Fotos im 60-m-Radius (Prime-Tower-Fuss und Perron).

### Turbinenplatz (-3/634)
- Boden: Beton (3), Asphalt (2), Feinkies (1). Baeume: 39 (OSM, Platzbaeume). Baenke: 18. Velo-Parkierung 2. Abfallkoerbe 2. Gras 2 Flaechen.
- Brunnen: Katalog V4 (Beton) bei 42 m. PRUEFEN (Beton-Variante ggf. nicht am Platz).
- Haltestelle: keine in 60 m.
- Fotos: 38 im 60-m-Radius.

### Schiffbau (231/430)
- Boden: Asphalt (25), Pflaster (3), Sett (1). Bushaltestellen 4, Plattformen 4, Fussgaengerstreifen 7.

### Prime Tower Fuss (42/155)
- Boden: Asphalt (52), Pflaster (9), Sett (5). Treppen 23, Lift 7, Automaten 6, Baeume 4.
- Fotos: 119 im 60-m-Radius (gut abgedeckt).

### Josefwiese (506/187)
- Boden: Feinkies (3), Asphalt (1), Pebblestone (1). Baeume: 42 (OSM, Park). Baenke 4. Spielplatz 1, Toilette 2, Park 1.
- Brunnen: Katalog V6 (Figurenbrunnen) bei 72 m, V4 bei 114 m. PRUEFEN: welcher Brunnen steht wirklich auf der Wiese.
- Fotos: 20 im 60-m-Radius, mit Lueckenfotos ergaenzt.

### Viadukt Markthalle (704/399)
- Boden: Asphalt (25), Beton (2), Pflaster (2). Baeume: 18. Baenke: 4. Fussgaenger 17, Parkplaetze 4.
- Brunnen: Katalog V8 (Notwasser) bei 46 m. PRUEFEN.
- Fotos: 6 im 60-m-Radius (duenn), Lueckenfotos geholt. Viaduktboegen mit Laeden: in `zone2_shops.json` (Viaduktstrasse 41 Adressen).

### Limmatplatz (1131/74)
- Boden: Asphalt (66), Pflaster 6, Sett 2. Tramschlaufe (8 Tram-Querungen), Fussgaengerstreifen 20, Velo-Parkierung 7, Automat 6.
- Haltestellen: Katalog H5 (5 m), H3 (6 m), H6 (7 m). Brunnen: Katalog V2 bei 11 m, V8 bei 54 m. PRUEFEN.
- Fotos: 70 im 60-m-Radius.

### Roentgenplatz (759/126)
- Boden: Asphalt (14), Pebblestone 1. Baeume: 28. Baenke: 8. Picknicktische 3. Parkplaetze 8.
- Brunnen: Katalog V2 bei 24 m. PRUEFEN.
- Fotos: 37 im 60-m-Radius.

### Limmatstrasse/Konradstrasse (1286/-229)
- Boden: Asphalt (31), Kies 2, Pflaster 1. Parkplaetze 9, Restaurant 6 Eintraege, Velo-Parkierung 4.
- Brunnen: Katalog V1 (Saeule/Trog) bei 53 m. PRUEFEN.
- Fotos: nur 1 im 60-m-Radius (LUECKE), Lueckenfotos geholt.

### Josefstrasse (520/279)
- Boden: Asphalt (12), Beton (6), Betonplatten 1. Baeume 31. Velo-Parkierung 8. Baenke 4. Treppen 3.
- Brunnen: Katalog V6 bei 67 m. PRUEFEN.
- Fotos: 31 im 60-m-Radius.

### Heinrichstrasse (642/398)
- Boden: Asphalt (28), Beton (3). Baeume 16. Velo-Parkierung 6. Fussgaengerstreifen 4. Wohnstrasse (living_street) 4.
- Brunnen: Katalog V8 bei 55 m. PRUEFEN.
- Fotos: 11 im 60-m-Radius (duenn).

### Fabrikstrasse (710/86)
- Boden: Asphalt (9), Pebblestone 1. Baeume 12. Picknicktische 3. Baenke 2.
- Brunnen: Katalog V2 bei 43 m. PRUEFEN.
- Fotos: 7 im 60-m-Radius, Lueckenfotos geholt.

### Sihlquai (1550/-92)
- Boden: Asphalt (7). Strasse mit Parkplaetzen 2, Trinkwasserbrunnen 1 (OSM drinking_water), Hochschule/College 1.
- Brunnen: Katalog V6 bei 57 m. PRUEFEN.
- Fotos: 12 im 60-m-Radius.

### Limmatufer (1250/250)
- Boden: Asphalt (6), Kompaktiert 1. Slipway 1, Treppen 1, Velo- und Bahnquerung 1.
- Fotos: 3 im 60-m-Radius (LUECKE), Lueckenfotos geholt.

## Haltestellen (Zone 2, Katalogzaehler)
H1 Wartehalle 34, H2 22, H3 Ticketautomat 29, H4 Anzeigewand 32, H5 28, H6 Bank kurz 57, H7 Bank lang 16. Positionen pro Haltestelle nicht einzeln nach Foto geprueft (auch nicht Escher-Wyss oder Limmatplatz).

## Laeden und Beizen (`zone2_shops.json`)
- 361 Eintraege (OSM-Gastro und Shops im Polygon, ohne Coiffeur/Beauty/Kleider/Schmuck, Banken, Buero/Freizeit/Museen). Gastro: 104 Restaurants, 31 Fast-Food, 24 Bars, 20 Cafés, 12 Nachtclubs. Shops: 16 Convenience, 8 Baeckerei, 7 Supermarkt, 7 Velo, 6 Kiosk.
- 266 mit Adresse. Webpruefung aus `research/pois_kreis5.csv`: 106 Eintraege (55 ok, 46 unclear, 3 moved, 2 renamed). `unclear` = Name nicht bestaetigt, nicht als Laden-Name verwenden ohne Pruefung.
- Schild (Farbe/Schrift), Markise, Aussensitze, Hauptfarbe: NOCH OFFEN (keine Fotopruefung).

## Fotos (Lueckenholung, `pipeline/photos/fetch_z2.py`, Log `logs/photos_z2.log`)
- 11 Orte, 265 neue Fotos in `data/raw/photos/z2/` (Mapillary, Commons, Panoramax; Lizenz/Autor in `research/zones/zone2_photos.json`): Escher-Wyss 28, Hardbruecke Perron 26, Turbinenplatz 26, Josefwiese 12, Viadukt 26, Limmatplatz 25, Roentgenplatz 20, Konradstrasse 22, Fabrikstrasse 9, Limmatufer 24, Sihlquai 27.
- Kontaktbogen: `preview/ref_z2_gaps_1..4.jpg` (je 8 Fotos, beschriftet mit Ort und Quelle), Index `research/zones/zone2_sheet_index.json`.
- Josefwiese nur 12 Fotos (Mapillary dort duenn); Fabrikstrasse 9.

## Luecken (Stand dieser Session)
1. Fassaden: 2 833 Adressen ohne Notiz, grossteils ausserhalb des Kern-Industriequartiers (siehe Polygon-Hinweis). Fotoerfassung fehlt.
2. Laden-Schilder/Markisen: 0 von 361 fotografisch geprueft.
3. Brunnen-Varianten: Katalog-Zuordnung an Escher-Wyss, Turbinenplatz, Josefwiese, Viadukt, Limmatplatz, Roentgenplatz, Fabrikstrasse, Josefstrasse, Heinrichstrasse, Sihlquai, Konradstrasse nicht bestaetigt.
4. Haltestellen-Positionen nicht einzeln nach Foto geprueft.
5. Lueckenfotos geholt (265), aber noch nicht fotografisch ausgewertet. Nur Bogen gebaut, Bilder nicht gegengeprueft.
