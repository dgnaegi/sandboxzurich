# Kollerwiese (kollerwiese)
OSM way [121536711] | 6977 m2 | Fotos: 9 (Bogen preview/ref_parks_kollerwiese.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Kollerwiese: Rasen mit Baumgruppen, Asphaltwege, Spielplatz (OGD), Sitzbänke.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'x europaea': 7, 'platyphyllos': 6, 'campestre': 5, 'betulus': 4, 'libani': 3, 'ilex': 2, 'regia (S)': 2, 'avium': 2}
- OSM-Punkte: {'amenity=drinking_water': 1, 'amenity=waste_basket': 1, 'amenity=toilets': 2}
