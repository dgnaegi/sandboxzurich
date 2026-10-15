# Rohdaten-Inventar (Stand 2026-10-14)

Gebiet: Kreise 3, 4, 5 (Industriequartier), 9 + 300 m Puffer; WGS84-BBox 8.4441,47.3337 - 8.5430,47.4066 (`pipeline/area.py`). Alles in `data/raw/` (nicht im Repo).

## OSM (Overpass)
- `osm/kreise.json` (104.1 MB, merged aus `osm/part_*.json`, 256 MB total inkl. Teile)
- Elemente: {'node': 922346, 'way': 158606, 'relation': 924}
- Tagged nach Schlüssel: highway 47567, building 33208, amenity 26111, natural 20787, barrier 9350, railway 5441, leisure 3446, shop 2977, landuse 2599, public_transport 1476, man_made 1358, tourism 1223, waterway 1164, office 859, building:part 466, route 303, craft 188, advertising 107
- Lizenz: ODbL, «© OpenStreetMap-Mitwirkende». Abdeckung: BBox-Kacheln (nicht Polygon, da `poly:` 504 lieferte), Ecken ausserhalb der Kreise inklusive. Overpass-Mirrors waren überlastet (504); automatische Quadtree-Aufteilung.

## swisstopo
- `alti3d/`: 52 GeoTIFF-Kacheln 0.5 m (1 km, neuester Jahrgang), 884 MB. Lizenz OGD swisstopo (Quellenangabe). EPSG:2056, LN02/LHN95 Höhen.
- `sb3d/`: swissBUILDINGS3D 3.0, 9 Blätter, 7250 MB (zip + entpackt). Lizenz OGD swisstopo.
  - swissbuildings3d_3_0_2019_1091-12_2056_5728.citygml.zip (29.0 MB)
  - swissbuildings3d_3_0_2019_1091-13_2056_5728.gdb.zip (24.9 MB)
  - swissbuildings3d_3_0_2019_1091-14_2056_5728.citygml.zip (87.6 MB)
  - swissbuildings3d_3_0_2019_1091-23_2056_5728.citygml.zip (190.9 MB)
  - swissbuildings3d_3_0_2019_1091-31_2056_5728.gdb.zip (8.0 MB)
  - swissbuildings3d_3_0_2019_1091-32_2056_5728.citygml.zip (53.6 MB)
  - swissbuildings3d_3_0_2019_1091-34_2056_5728.citygml.zip (2.0 MB)
  - swissbuildings3d_3_0_2019_1091-41_2056_5728.citygml.zip (251.4 MB)
  - swissbuildings3d_3_0_2019_1091-43_2056_5728.citygml.zip (38.9 MB)
- Blätter 1091-13 und 1091-31 (Westrand, Kreis 9 Altstetten/Albisrieden) gibt es nur als FileGDB (kein CityGML) -> braucht GDAL/pyogrio oder DWG. Blatt 1091-21/33 geschnitten nicht mit dem Gebiet.
- `swissimage_items.json`: nur Item-/URL-Liste SWISSIMAGE 10 cm (0.0 MB), keine Bilder. Lizenz OGD swisstopo.

## Stadt Zürich OGD (WFS -> GeoJSON, WGS84)
Alle Datensätze CC0 (`stadtzh/_licenses.json`), Quelle «Stadt Zürich, Geomatik + Vermessung / Open Data Zürich». Ganze Stadt, nicht zugeschnitten.

- `stadtzh/geo_abfallgefaesse__abfallgefaess_p.geojson` 2.9 MB, 4074 Features
- `stadtzh/geo_baumkataster__baumkataster_baumstandorte.geojson` 46.2 MB, 81142 Features
- `stadtzh/geo_brunnen__wvz_brunnen.geojson` 1.3 MB, 1287 Features
- `stadtzh/geo_fuss__und_velowegnetz__tbl_routennetz.geojson` 18.1 MB, 40467 Features
- `stadtzh/geo_fuss__und_velowegnetz__tbl_routennetz_abbiegeverbote.geojson` 0.3 MB, 1023 Features
- `stadtzh/geo_oeffentlich_zugaengliche_parkplaetze_dav__oeff_strassen_gueterumschlag_p.geojson` 0.2 MB, 1169 Features
- `stadtzh/geo_oeffentlich_zugaengliche_parkplaetze_dav__oeff_strassenp_dav_opu_mit_l_p.geojson` 1.9 MB, 6035 Features
- `stadtzh/geo_oeffentlich_zugaengliche_parkplaetze_dav__oeff_strassenparkierung_dav_l.geojson` 2.5 MB, 5933 Features
- `stadtzh/geo_oeffentlich_zugaengliche_parkplaetze_dav__oeff_strassenparkierung_dav_p.geojson` 7.1 MB, 13222 Features
- `stadtzh/geo_oeffentlich_zugaengliche_parkplaetze_dav__oeff_strassenparkierung_spuzpu.geojson` 1.0 MB, 1396 Features
- `stadtzh/geo_oeffentlich_zugaengliche_strassenparkplaetze_ogd__view_pp_ogd.geojson` 12.1 MB, 46282 Features
- `stadtzh/geo_oeffentliche_beleuchtung_der_stadt_zuerich__ewz_brennstelle_p.geojson` 10.8 MB, 42433 Features
- `stadtzh/geo_sitzbankkataster_ogd__bankstandorte_ogd.geojson` 1.8 MB, 7267 Features
- `stadtzh/geo_stadtkreise__adm_stadtkreise_a.geojson` 0.4 MB, 12 Features
- `stadtzh/geo_stadtkreise__adm_stadtkreise_beschr_p.geojson` 0.0 MB, 12 Features
- `stadtzh/geo_stadtkreise__adm_stadtkreise_v.geojson` 0.4 MB, 12 Features
- `stadtzh/geo_velonetzplanung__view_gs_umsetzungsstrecken.geojson` 0.2 MB, 36 Features
- `stadtzh/geo_velonetzplanung__view_velonetz.geojson` 2.0 MB, 4701 Features
- `stadtzh/geo_verkehrszonen__view_geoserver_zonen_ist.geojson` 0.6 MB, 366 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_att.geojson` 0.0 MB, 26 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_mobil_rs_view.geojson` 0.0 MB, 3 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_mobil_view.geojson` 0.0 MB, 20 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_rs_att.geojson` 0.0 MB, 91 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_rs_view.geojson` 0.2 MB, 91 Features
- `stadtzh/geo_zueri_wc__poi_zueriwc_view.geojson` 0.1 MB, 25 Features

## Gesamt: 8.51 GB in data/raw/

## Probleme und Hinweise
- Overpass: `poly:`-Abfrage und Mehrfach-Abfragen lieferten 504/502 auf allen Mirrors; Lösung: BBox-Abfrage in 5 Teilen (`part_*_r.json`), in `kreise.json` dedupliziert. Ränder ausserhalb des Polygons müssen beim Bauen mit `pipeline/area.py` geclippt werden.
- Baumkataster: Layer `baumkataster_kronendurchmesser` (427 MB) und `baumstandorte_k` (505 MB) bewusst nicht behalten (redundant, `SKIP` in `fetch_stadtzh.py`); `baumkataster_baumstandorte` (81'142 Bäume) genügt.
- Nicht geladen: Kantons-Layer Fussgängerstreifen / Tempo-30 (OGDZHWFS, ganzer Kanton); Fussgängerstreifen stehen in OSM, Tempo-30 / Begegnungszonen in `geo_verkehrszonen`. Blaue Zone: `strassenparkplaetze_ogd` (Feld Parkplatzart prüfen).
- swissBUILDINGS3D: Blätter 1091-13 und -31 nur als FileGDB; ältere Jahrgänge pro Blatt sind 2019 (Blatt 1091-33: neuer Jahrgang 2024 existiert, schneidet das Gebiet aber nicht).
- sb3d entpackt ist gross (CityGML ~6.8 GB); nach dem Parsen können die entpackten Ordner gelöscht werden (zips bleiben).
- `data/raw/stadtzh_extra/` stammt nicht aus diesen Skripten.
