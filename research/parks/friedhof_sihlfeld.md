# Friedhof Sihlfeld (friedhof_sihlfeld)
OSM way [10634343] | 258668 m2 | Fotos: 22 (Bogen preview/ref_parks_friedhof_sihlfeld.jpg, Nummern = Index in photos.json) | Referenzbilder: [2, 3, 12, 14, 15, 17]

## Beobachtung (Fotos)
Friedhof Sihlfeld: Kieswege (hell, chaussiert), gepflegter Rasen, geschnittene Eiben/Buchshecken (1.5 m), hohe Koniferen und Platanen, grüne Parkbänke, Urnenbrunnen als flache Betonschale mit Kupferdach (Ø 2 m), Kriegsgräberreihen, Grabskulpturen (Bronze/Stein), Glockenmast, Brunnen mit Ringbecken. Krematorium: eigener Landmark.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = gravel) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'hippocastanum': 170, 'abies': 147, 'betulus': 122, 'pendula': 82, 'plicata': 68, 'x europaea': 66, 'nigra': 64, 'pseudoacacia': 60}
- OSM-Punkte: {'barrier=gate': 27, 'barrier=entrance': 7, 'barrier=lift_gate': 1, 'amenity=toilets': 5, 'amenity=drinking_water': 12, 'amenity=waste_basket': 2, 'amenity=public_bookcase': 5, 'amenity=bicycle_parking': 1, 'amenity=events_venue': 1}
