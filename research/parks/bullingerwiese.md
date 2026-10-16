# Bullingerhof / Bullingerwiese (bullingerwiese)
OSM way [37065137] | 19914 m2 | Fotos: 24 (Bogen preview/ref_parks_bullingerwiese.jpg, Nummern = Index in photos.json) | Referenzbilder: [16, 22, 24]

## Beobachtung (Fotos)
Wege/Belag: grau-beiger Kies (Chaussierung) fast flächig unter Platanen/Rosskastanien, Böschung mit Ahorn; Rasen nur randlich. Bäume: alte Platanen und Kastanien in Reihen (laubfrei im Frühjahr). Spielplatz Bullingerhof OSM 104060770. Zäune: Strassenseite niedrige Metallbügel. Beleuchtung: Pilzleuchte. Bänke: einfache Holzbänke. Umgebung: Siedlung Bullingerhof (ockergelb, Läden grün), Bullingerkirche.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'x hispanica': 36, 'orientalis': 10, 'cerasus': 2, 'alba': 1, 'pendula': 1, 'japonicum': 1, 'regia (S)': 1}
- OSM-Punkte: {'leisure=picnic_table': 6, 'leisure=pitch': 2, 'sport=table_tennis': 1, 'sport=basketball': 1, 'amenity=drinking_water': 3, 'amenity=waste_basket': 5, 'amenity=recycling': 5}
