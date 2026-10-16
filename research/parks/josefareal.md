# Quartierpark Josef-Areal (josefareal)
OSM way [1145622518] | 6296 m2 | Fotos: 23 (Bogen preview/ref_parks_josefareal.jpg, Nummern = Index in photos.json) | Referenzbilder: [14, 19, 21]

## Beobachtung (Fotos)
Josef-Areal: Gartenwirtschaft auf Kiesplatz (rote Tische/Schirme), Pappelreihe (Pyramidenpappeln) und Liegewiese dahinter, kleines Holzhaus mit Walmdach, Kamin KVA rot-weiss, Viadukt-Bögen. Kies Pfütze-anfällig; Pilzlampen.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): keine
- OSM-Punkte: {'barrier=block': 5, 'amenity=waste_basket': 11, 'amenity=vending_machine': 2}
