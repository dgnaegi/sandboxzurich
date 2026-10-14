# Datenquellen und Lizenzen

Jede Quelle, die ins Spiel einfliesst, steht hier mit Lizenz. Neue Quellen zuerst hier eintragen, dann verwenden.

## Erlaubt: Daten, die ins Spiel kommen
| Quelle | Inhalt | Lizenz / Pflicht |
|---|---|---|
| OpenStreetMap (Overpass API) | Strassen, Velowege, Tram, POIs (Läden, Cafés), Parks | ODbL, Namensnennung «© OpenStreetMap-Mitwirkende» |
| swisstopo swissBUILDINGS3D | Gebäude LOD2 | OGD swisstopo, Quellenangabe |
| swisstopo SWISSIMAGE | Orthofoto (Bodentexturen, Kontrolle) | OGD swisstopo, Quellenangabe |
| swisstopo swissALTI3D | Gelände | OGD swisstopo, Quellenangabe |
| Stadt Zürich Open Data (data.stadt-zuerich.ch) | Stadtkreise, Velovorzugsrouten, Velonetz, Baumkataster, Brunnen, Tempo-30-Zonen, Parkplätze u.a. | Meist CC0 oder CC BY, **pro Datensatz prüfen** |
| amtliche Gebäudeadressen (GWR / swisstopo) | Hausnummern | OGD, Quellenangabe |
| Mapillary | Strassenfotos als Referenz, eventuell Texturen | CC BY-SA 4.0, Namensnennung |
| Panoramax | Strassenfotos | meist CC BY-SA, pro Bild prüfen |
| Wikimedia Commons | Fotos von Landmarks | pro Bild, siehe `../research/credits*` |
| Eigene Fotos des Users | Fassaden, Läden | frei |

## Nur zur Inspiration: nie herunterladen oder übernehmen
- **Google Street View, Google Maps, Google Images:** anschauen, um Farben, Ladenfronten und Stimmung zu verstehen. Keine Bilder speichern, keine Texturen ableiten, keine Geometrie daraus rekonstruieren (Nutzungsbedingungen von Google).
- Websites und Instagram von Läden: Name, Öffnungsstatus und Adresse dürfen als Fakten übernommen werden. **Logos und Fotos nicht.**

## Läden und Logos
- Ladennamen sind Fakten und dürfen als Text auf einem Schild erscheinen (Schrift aus `../assets/fonts`).
- Echte Logos und Markenschriften nur mit Erlaubnis. Ohne Erlaubnis: Name in einer neutralen Schrift.
- Ein Laden erscheint nie als Gegner oder als Ziel von Zerstörung (siehe `CONTENT_GUIDELINES.md`).

## Wiederverwendung aus dem Reel
- `../data/` enthält OSM, LOD2, Ortho und DEM für ein kleineres Gebiet (Kreis 4/5).
- Skripte zum Wiederverwenden: `../src/fetch_osm.py`, `../src/parse_citygml.py`, `../src/fetch_ortho.py`, `../src/prep_osm.py`.
- Recherche zu Orten: `../research/locations.md`.
