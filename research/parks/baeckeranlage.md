# Bäckeranlage (baeckeranlage)
OSM way [4743823] | 13825 m2 | Fotos: 21 (Bogen preview/ref_parks_baeckeranlage.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Handgebaut: pipeline/overrides/places_detail_baeckeranlage.json (siehe research/v3/baeckeranlage.md).

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'hippocastanum': 28, 'japonica': 13, 'styraciflua': 5, 'saccharinum': 5, 'cappadocicum': 5, 'pseudoplatanus': 4, 'cordata': 3, 'campestre': 3}
- OSM-Punkte: {'barrier=gate': 1, 'amenity=restaurant': 1, 'amenity=social_centre': 1, 'amenity=drinking_water': 2, 'amenity=toilets': 3, 'amenity=waste_basket': 2, 'amenity=vending_machine': 1}
