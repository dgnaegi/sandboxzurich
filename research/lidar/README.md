# LiDAR Kanton Zürich 2021/22: Zugang und Format (Pilot 2026-10-21)

Datensatz: https://data.stadt-zuerich.ch/dataset/ktzh_lidar_laserscanning_punktwolke___2021_bis_2022__ogd_  (CC0, Stand 30.04.2022, GIS-ZH Nr. 557)

## Zugang
- CKAN-Resource ist nur ein Link auf `https://www.ogd.stadt-zuerich.ch/geodaten/download/557?format=61` (Angular-Seite, kein Direktdownload).
- Der Download läuft über den Bestelldienst des Geoportals: `POST https://www.ogd.stadt-zuerich.ch/geoportal_order/` mit
  `{"order":{"geoportal_id":"557","geoportal_name":"...","stzh":false,"email":"","extent_name":"bbox","extent":[[[E,N]x5 geschlossener Ring LV95]],"selected_format":{"id":61,"name":"LAZ (.laz)"},"geodatensatz_id":null,"paket_id":null}}`
  -> `{job_id, download_url}`; Status `GET .../geoportal_order/<job_id>`; nach ca. 15 s `SUCCESS`, dann ZIP von `geoservices.zh.ch/geoshopapi/v1/orders/<job_id>/download` (E-Mail nicht nötig, max. 4 km2 pro Bestellung).
  Geliefert werden **ganze Kacheln** (nicht zugeschnitten) plus Produktblatt und Lieferschein.
- Die Claude-Code-Sandbox hat die zweite und dritte Bestellung (Kacheln für Hardbrücke und Velotunnel) **nicht erlaubt** (Bestellung = POST an einen Fremddienst). Bestellskript: Scratchpad `order.py`, trivial nachzubauen.
- Alternative Potree-2.0-Kopie: `https://maps.zh.ch/lidar/ALS/KTZH/2022/` (metadata.json, hierarchy.bin, octree.bin, BROTLI, 72 Mrd. Punkte, 362 GB). **Nicht brauchbar:** Der Server liefert Range-Requests nur bis ca. 17.05 GB, alle Knoten im Stadtgebiet liegen dahinter (leere Antworten). Bei Gelegenheit erneut testen.

## Format
- Kacheln 500 x 500 m, Name = SW-Ecke LV95 (`2682000_1248000.laz`), LAS 1.4, Point Format 6, LAZ, ~6.7 Mio. Punkte pro Kachel (~27 Pkt/m2 im Mittel, 32 Pkt/m2 in Area a), **36 MB pro Kachel = ca. 143 MB/km2**.
- CRS: LV95 (EPSG:2056) + LN02-Höhen (EPSG:5728). Das Spiel liegt wegen `terrain.heights(z_shift=-3.06)` 3.06 m tiefer: `z_game = Z - 408 - 3.06` (verifiziert: Median LiDAR-Boden minus Spiel-Boden = 0.000 m).
- Felder: X Y Z, intensity (uint16, vorhanden), return_number/number_of_returns, classification, scan_angle, gps_time, point_source_id.
- Klassen (Daten, nicht Doku): 1 übrig, 2 Boden, 3/4/5 Vegetation tief/mittel/hoch, 6 Gebäude, 7 Ausreisser, 12 Streifenrand, 15 Freileitungen/Masten, **17 Brücken** (Doku sagt 10). Achtung: Bahnbrücken und -dämme sind oft Klasse 2 (Boden), Brücken-Klasse 17 ist selten (1274 von 1.05 Mio. Punkten in Area a).

## Tools
`pipeline/lidar.py` (load / grids / profile / intensity_raster, Crop-Cache in `data/raw/lidar/crops/`). Reader: `laspy[lazrs]`, `brotli`, `scipy`, `matplotlib` in `requirements.txt`.
