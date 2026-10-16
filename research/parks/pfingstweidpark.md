# Pfingstweidpark (pfingstweidpark)
OSM way [22944392] | 13279 m2 | Fotos: 27 (Bogen preview/ref_parks_pfingstweidpark.jpg, Nummern = Index in photos.json) | Referenzbilder: [0, 3, 4, 24, 25]

## Beobachtung (Fotos)
Wege/Belag: helle Betonwege, rote Stützmauern/Brüstungen (ca. 1 m), Hügelrasen; junge Bäume mit Pfählen (Gleditsia/Ginkgo/Linde), Ziergräser. Spielplatz mit Schaukelgestell, Sitzblöcke Beton, runde Pilzleuchten, rote Fussgängerbrücke (Pfingstweid). Hochhäuser (Pfingstweid) im Hintergrund.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = concrete) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'cordata': 38, 'campestre': 22, 'x europaea': 15, 'biloba': 12, 'robur': 11, 'betulus': 11, 'glutinosa': 11, 'biloba (w)': 6}
- OSM-Punkte: {'leisure=pitch': 2, 'sport=table_tennis': 2, 'leisure=picnic_table': 5, 'amenity=toilets': 2, 'amenity=drinking_water': 1, 'amenity=fountain': 1, 'amenity=waste_basket': 13, 'amenity=bicycle_parking': 1, 'amenity=bbq': 5}
