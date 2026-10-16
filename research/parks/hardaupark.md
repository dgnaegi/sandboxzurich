# Hardaupark (hardaupark)
OSM way [34129797] | 8117 m2 | Fotos: 16 (Bogen preview/ref_parks_hardaupark.jpg, Nummern = Index in photos.json) | Referenzbilder: [13, 14, 15, 12]

## Beobachtung (Fotos)
Wege/Belag: grosser Asphaltplatz (Hardauplatz) mit heller Betoneinfassung, Kieswege am Rand; Wiese mit jungen Bäumen im SW. Bäume: hohe Pappeln/Platanen am Rand, junge Stangenbäume. Brunnen: runder Betonbecher-Trinkbrunnen (Ø 0.9 m). Kunst: weisse Y-Skulptur (ca. 8 m) auf dem Platz. Spielplatz Hardau OSM 334488490 (Geräte aus OGD). Umgebung: Hochhäuser Hardau I/II (ocker/orange).

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = asphalt) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'pseudoacacia': 10, 'x marschlinsii': 7, 'triacanthos': 3, 'x europaea': 2, 'decidua': 2, 'glyptostroboides': 1}
- OSM-Punkte: {'leisure=pitch': 1, 'sport=basketball': 1, 'amenity=drinking_water': 1, 'amenity=bbq': 2, 'amenity=waste_basket': 3}
