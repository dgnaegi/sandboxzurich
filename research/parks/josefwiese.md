# Josefwiese (josefwiese)
OSM way [28054989] | 20472 m2 | Fotos: 30 (Bogen preview/ref_parks_josefwiese.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Handgebaut: places_detail_josefwiese.json (siehe research/v3/josefwiese.md).

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'nigra': 69, 'platyphyllos': 38, 'x europaea': 34, 'communis': 5, 'nigra subsp. Laricio': 4, 'nivalis': 3, 'dioica': 1}
- OSM-Punkte: {'barrier=cycle_barrier': 1, 'leisure=playground': 3, 'leisure=pitch': 4, 'sport=table_tennis': 3, 'sport=table_soccer': 1, 'amenity=fast_food': 1, 'amenity=toilets': 2, 'amenity=bbq': 1, 'amenity=drinking_water': 1, 'amenity=public_bookcase': 1, 'amenity=bicycle_parking': 2, 'amenity=food_sharing': 1}
