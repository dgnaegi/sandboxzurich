# Park Stauffacherstrasse (stauffacherpark)
OSM way [27435515] | 7850 m2 | Fotos: 25 (Bogen preview/ref_parks_stauffacherpark.jpg, Nummern = Index in photos.json) | Referenzbilder: [17, 5, 6]

## Beobachtung (Fotos)
Kieshof/Schulhof an der Kanzleistrasse (OSM-Park): grauer Kiesplatz (chaussiert), einzelne grosse Kastanien/Linden, Spielgerät-Reck, Bänke bunt gestrichen, Pyramide aus Granit (Kunst) am Rand. Volkshaus und Stauffacher in der Nähe.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'x europaea': 19, 'hippocastanum': 11, 'betulus': 3, 'truncatum': 3, 'sanguinea': 2, 'spec.': 1, 'cordata': 1, 'saccharinum': 1}
- OSM-Punkte: {'barrier=gate': 2, 'leisure=pitch': 2, 'sport=table_tennis': 2, 'amenity=pub': 1, 'amenity=bicycle_parking': 2, 'amenity=cinema': 1, 'amenity=bicycle_repair_station': 1, 'amenity=fountain': 1, 'amenity=drinking_water': 1, 'amenity=toilets': 1, 'amenity=vending_machine': 1}
