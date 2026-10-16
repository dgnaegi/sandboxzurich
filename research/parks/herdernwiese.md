# Herdernwiese (herdernwiese)
OSM way [1373841608] | 1653 m2 | Fotos: 17 (Bogen preview/ref_parks_herdernwiese.jpg, Nummern = Index in photos.json) | Referenzbilder: []

## Beobachtung (Fotos)
Herdernwiese: kleine Wiese, Kieswege, Bäume (Linden/Ahorn), Bänke.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'communis': 5, 'domestica': 4, 'colurna': 3, 'avium': 2, 'cerasus': 1, 'betulus': 1, 'x europaea': 1}
- OSM-Punkte: {'barrier=gate': 1}
