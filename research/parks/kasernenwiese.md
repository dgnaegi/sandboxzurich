# Kasernenwiese (kasernenwiese)
OSM way [4533222, 28943682] | 11460 m2 | Fotos: 37 (Bogen preview/ref_parks_kasernenwiese.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Handgebaut: places_detail_kaserne.json (siehe research/v3/kaserne.md).

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'hippocastanum': 43}
- OSM-Punkte: {'barrier=gate': 1, 'amenity=waste_basket': 1, 'amenity=recycling': 1}
