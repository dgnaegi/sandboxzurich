# Klingenpark (klingenpark)
OSM way [24593473] | 5605 m2 | Fotos: 30 (Bogen preview/ref_parks_klingenpark.jpg, Nummern = Index in photos.json) | Referenzbilder: [16, 19, 21, 26, 27, 29]

## Beobachtung (Fotos)
Klingenpark (Ausstellungsstrasse, Museum für Gestaltung): runder Brunnen (Ø ca. 12 m, Granitrand) mit Brunnenfiguren (Bronze, sitzend, auf Sockeln), polygonale Natursteinplatten (Bündner Gneis) rund um den Brunnen, Kieswege, Rasenbänder mit Hecken (1 m) vor dem Museum, alte Platanen/Linden, lange niedrige Holzbänke im Halbrund; Trinkbrunnen aus Stein (Kubus) am Weg.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = pave) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'platanoides': 11, 'x hispanica': 8, 'robur': 4, 'glabra': 1}
- OSM-Punkte: {'barrier=gate': 3, 'leisure=playground': 1, 'amenity=drinking_water': 1, 'amenity=waste_basket': 9, 'amenity=vending_machine': 1}
