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
| Mapillary Map Features (Graph API `map_features`, Schilder-Positionen/-Klassen aus Objekterkennung) | Position und Klasse echter Verkehrsschilder (`pipeline/mapillary_features.py`, `pipeline/overrides/mly_signs.json`); keine Bilder, nur Koordinaten und Klassen | CC BY-SA 4.0 (Mapillary-Daten inkl. abgeleiteter Map Features, https://www.mapillary.com/terms und https://www.mapillary.com/developer/api-documentation), Namensnennung «© Mapillary-Mitwirkende, CC BY-SA 4.0», Share-Alike gilt für die abgeleitete Datei mly_signs.json |
| Panoramax | Strassenfotos | meist CC BY-SA, pro Bild prüfen |
| Wikimedia Commons | Fotos von Landmarks | pro Bild, siehe `../gta6/research/credits*` (lokal) |
| Eigene Fotos des Users | Fassaden, Läden | frei |

## Nur zur Inspiration: nie herunterladen oder übernehmen
- **Google Street View, Google Maps, Google Images:** anschauen, um Farben, Ladenfronten und Stimmung zu verstehen. Keine Bilder speichern, keine Texturen ableiten, keine Geometrie daraus rekonstruieren (Nutzungsbedingungen von Google).
- Websites und Instagram von Läden: Name, Öffnungsstatus und Adresse dürfen als Fakten übernommen werden. **Logos und Fotos nicht.**

## Läden und Logos
- Ladennamen sind Fakten und dürfen als Text auf einem Schild erscheinen (Schriften mit freier Lizenz, z.B. Google Fonts. Pricedown aus `../gta6/assets/fonts` nur nach Lizenzprüfung und nie ins Repo).
- Echte Logos und Markenschriften nur mit Erlaubnis. Ohne Erlaubnis: Name in einer neutralen Schrift.
- Ein Laden erscheint nie als Gegner oder als Ziel von Zerstörung (siehe `CONTENT_GUIDELINES.md`).

## Wiederverwendung aus dem Reel (Ordner `../gta6`, nur lokal beim Autor)
- `../gta6/data/` enthält OSM, LOD2, Ortho und DEM für ein kleineres Gebiet (Kreis 4/5).
- Skripte zum Wiederverwenden: `../gta6/src/fetch_osm.py`, `../gta6/src/parse_citygml.py`, `../gta6/src/fetch_ortho.py`, `../gta6/src/prep_osm.py`.
- Recherche zu Orten: `../gta6/research/locations.md`.

## Heruntergeladen (Stand 2026-10-14, Details in `research/raw_inventory.md`)
Skripte: `pipeline/fetch_osm.py`, `fetch_swisstopo.py`, `fetch_stadtzh.py`; Ablage `data/raw/` (nicht im Repo).

| Datensatz | Ablage | Lizenz |
|---|---|---|
| OSM Gesamtabfrage Kreise 3/4/5/9 + 300 m | `data/raw/osm/kreise.json` | ODbL, © OpenStreetMap-Mitwirkende |
| swissALTI3D 0.5 m (GeoTIFF) | `data/raw/alti3d/` | OGD swisstopo, Quellenangabe |
| swissBUILDINGS3D 3.0 (CityGML, 2 Blätter nur FileGDB) | `data/raw/sb3d/` | OGD swisstopo, Quellenangabe |
| SWISSIMAGE 10 cm: nur Item-Liste, keine Bilder | `data/raw/swissimage_items.json` | OGD swisstopo, Quellenangabe |
| Stadt Zürich: Baumkataster, Brunnen, Velonetzplanung, Fuss- und Velowegnetz, Verkehrszonen, Stadtkreise, öffentliche Beleuchtung (ewz), Sitzbankkataster, Abfallgefässe, ZüriWC, Strassenparkplätze (OGD + DAV) | `data/raw/stadtzh/*.geojson` | je CC0 (laut CKAN `license_id`), Quelle «Stadt Zürich» angeben |
| Fussgängerstreifen, Tempo-30 (Kanton ZH, OGDZHWFS) | nicht geladen (OSM liefert Fussgängerstreifen, Tempo-30 über `geo_verkehrszonen`) | CC0 |
| SBB Open Data «BehiG Haltekantesegment» (data.sbb.ch, `21197_behig-haltekantesegment`): Perron-Nr., Typ, Kantenlänge, Gleisachsen-Position (nur Zürich-Bahnhöfe, 203 Zeilen) | `data/raw/stations/behig_seg_zh.json` (Abruf 2026-10-16) | SBB Open-Data-Lizenz (https://data.sbb.ch/page/licence): Nutzung frei inkl. kommerziell, Quellenangabe «Quelle: SBB». Nur Zahlen, keine Pläne/Logos. Bahnhofplan-PDFs von sbb.ch nur angeschaut, nicht übernommen |

## Zürich HB (2026-10-16, Details `research/hb/README.md`)
| Datensatz | Ablage | Lizenz |
|---|---|---|
| SBB Open Data (data.sbb.ch): `perron`, `perronoberflache`, `sektortafel`, `haltestelle-uhr`, `billetautomat`, `mobiliar-im-bahnhof` im 450-m-Umkreis des HB (Perrontyp/-länge/-fläche, Längshallen-Zuordnung der Sektortafeln) | `data/raw/sbb/hb_records.json` | SBB Open Data, https://data.sbb.ch/page/licence (Quellenangabe «SBB»); nur Fakten, kein SBB-Logo, keine SBB-Uhr |
| OSM `building:part` (Wannerhalle, Nord-/Südtrakt), `railway=platform`-Relationen 3–18/31–34/41–44, `indoor=*` | `research/hb/osm.json`, `osm_platforms.json`, `tracks.json` | ODbL |
| Referenzfotos HB (Wikimedia Commons Kategorie «Zürich Hauptbahnhof» + Unterkategorien, Mapillary, Panoramax), 632 Dateien | `data/raw/photos/hb/`, Lizenz je Bild in `research/hb/CREDITS.md` | CC BY / CC BY-SA / CC0 / PD; nur Referenz, nie Textur oder Rekonstruktionsvorlage |
| Stadt Zürich / VBZ-Infrastruktur OGD (`geo_vbz_infrastruktur_ogd`): `haltestellen_wartehalle`, `_sitzgelegenheit`, `_dfi_anzeiger`, `_ticketautomat`, `_plakatstelle`, `_haltebalken`, `_infosystem` → echte Haltestellen-Ausstattung (`pipeline/stops_equip.py` → `web/public/data/stops_equip.json`) | `data/raw/stadtzh_all/geo_vbz_infrastruktur_ogd__haltestellen_*.geojson` | CC0 (CKAN `license_id` = `cc-zero`, geprüft 2026-10-16); Quelle «Stadt Zürich / VBZ» |
| Stadt Zürich: Liste der Informationstafeln an Denkmalschutzobjekten (`blaue_tafeln_p`; Text als Fakt, auf die echte Fassade gesetzt) und Velopumpstationen (`velopumpstationen_p`) → `pipeline/ogd_extras.py` → `web/public/data/ogd_extras.json` | `data/raw/stadtzh_all/geo_liste_der_informationstafeln_*`, `geo_velopumpstationen__*` | CC0 (`cc-zero`, geprüft 2026-10-16); Quelle im Spiel eingeblendet |
| Stadt Zürich: Hochhäuser (`geo_hochhaeuser__alle_hochhaeuser`), noch nicht verwendet | `data/raw/stadtzh_all/geo_hochhaeuser__*` | CC0 (`cc-zero`, geprüft 2026-10-16) |

## Zentralwaescherei-Graffiti (2026-10-18, Details `research/zentralwaescherei_graffiti.md`)
Fotos aus `research/v3/` (Commons/Mapillary/Panoramax, Lizenz je Bild) nur als Referenz; die Wandbilder im Spiel sind eigene prozedurale Nachzeichnungen (`pipeline/landmarks/zw_graffiti.py`), ohne Foto-Pixel, ohne Slogans.

## LiDAR-Punktwolke Kanton Zürich 2021/22 (Pilot, 2026-10-21, Details `research/lidar/README.md`)
| Quelle | Ablage | Lizenz |
|---|---|---|
| Kanton Zürich, Amt für Raumentwicklung (Geoinformation): LIDAR Laserscanning-Punktwolke 2021 bis 2022 (OGD, GIS-ZH Nr. 557, Stand 30.04.2022), ~16 bis 30 Pkt/m², LAZ, LV95/LN02, Klassen und Intensität. Bezug über die Bestellung auf stadt-zuerich.ch/geodaten (Kachel 500 m, ca. 36 MB) → `pipeline/lidar.py` | `data/raw/lidar/<E>_<N>.laz` | CC0 (`cc-zero`, geprüft 2026-10-21); Quellenangabe «Kanton Zürich, Geoinformation» höflich |
