# Park Museum für Gestaltung (gestaltung)
OSM way [495443771] | 4511 m2 | Fotos: 24 (Bogen preview/ref_parks_gestaltung.jpg, Nummern = Index in photos.json) | Referenzbilder: [21, 26, 28]

## Beobachtung (Fotos)
Park Museum für Gestaltung: siehe Klingenpark; Rasenstreifen, Betonmauern, grosse Platanen vor dem Museum.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = pave) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): keine
- OSM-Punkte: {'amenity=drinking_water': 1}
