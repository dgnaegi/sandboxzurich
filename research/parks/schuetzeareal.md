# Schütze-Areal (schuetzeareal)
OSM way [29349058] | 6157 m2 | Fotos: 16 (Bogen preview/ref_parks_schuetzeareal.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Schütze-Areal: Park vor Wohnbauten, Rasenflächen mit jungen Bäumen, Asphaltweg; Spielgeräte aus OGD.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'sylvestris': 15, 'paniculata': 14, 'avium': 14, 'cerris': 14, 'pendula': 5, 'alba': 5, 'tataricum': 4, 'nigra': 4}
- OSM-Punkte: {'barrier=gate': 1, 'leisure=playground': 1, 'amenity=toilets': 2, 'amenity=waste_basket': 1}
