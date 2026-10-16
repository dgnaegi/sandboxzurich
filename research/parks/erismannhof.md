# Erismannhof (erismannhof)
OSM way [952626973] | 5419 m2 | Fotos: 36 (Bogen preview/ref_parks_erismannhof.jpg, Nummern = Index in photos.json) | Referenzbilder: [24, 26, 27, 28, 29]

## Beobachtung (Fotos)
Genossenschafts-Innenhof Erismannhof: gelb-ockerne Blockrandbauten (Fensterläden grün-grau, Walmdächer) umschliessen Höfe mit Rasen, Kieswegen, Durchgängen (Torbögen mit Kugelaufsatz), Kinderspielplatz mit Sandkasten und Rundbrunnen (Kindergarten-Pavillon mit Vordach). Bäume: Linden, Ahorn, Pappel an der Strasse. Hecken niedrig entlang Zäunen.

## Umsetzung im Spiel
- Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = sidewalk) per `ortho_ground` in pipeline/overrides/places_detail_parks.json (Generator pipeline/parks_gen.py).
- Objekte an echten OSM-Positionen: Picknicktische (tbench), Grill/Feuerstelle (grill), Trinkwasser, Fitness, Pingpong, Unterstand, WC.
- Bäume: Baumkataster/OSM (Spielgeometrie unverändert); Spielplatzgeräte: pipeline/playgrounds.py.

## Daten
- Bäume im Park (Kataster, Gattung): {'serrulata': 37}
- OSM-Punkte: {'leisure=pitch': 2, 'sport=table_tennis': 2, 'leisure=playground': 1, 'amenity=waste_basket': 2}
