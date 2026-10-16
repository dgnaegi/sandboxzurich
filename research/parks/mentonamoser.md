# Mentona-Moser-Anlage (mentonamoser)
OSM way [4592592] | 1738 m2 | Fotos: 21 (Bogen preview/ref_parks_mentonamoser.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Mentona-Moser-Anlage: kleine Quartieranlage, Kieswege, Rasen, Bänke, Spielgeräte aus OGD.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'domestica': 10, 'tomentosa': 3, 'torminalis': 2, 'pomifera': 2, 'occidentalis': 2, 'padus': 2, 'bignonioides': 2, 'dioica': 1}
- OSM-Punkte: {'leisure=playground': 1, 'leisure=picnic_table': 1, 'amenity=recycling': 1, 'amenity=toilets': 1, 'amenity=waste_basket': 1, 'amenity=vending_machine': 1}
