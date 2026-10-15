# Soziale Infrastruktur und Strassenmobiliar: Stadt Zürich OGD

Stand: 2026-10-14. Download per `pipeline/fetch_stadtzh_extra.py` (CKAN package_show, WFS GetFeature).
Koordinaten: EPSG:2056 (LV95), im GeoJSON per `crs`-Member deklariert. Metadaten pro Datei in `data/raw/stadtzh_extra/manifest.json`.
Multi-Layer-Pakete: nur die `*_view`-Layer (Punkt-POIs) wurden übernommen; jedes Feature trägt `properties.layer`. `*_att` (Attributtabellen) und `*_l`/`*_p` (Linien/Flächen) wurden ausgelassen.

| Datensatz | Datei | Anzahl Features | Lizenz | Quell-URL | Bemerkung |
|---|---|---|---|---|---|
| Kindertagesstätten (Kitas) | data/raw/stadtzh_extra/kitas.geojson | 342 | CC0 (cc-zero) | https://data.stadt-zuerich.ch/dataset/geo_kindertagesstaette | Punkte, Adresse, Name, Behindertenparkplatz, Hindernisfreiheit. Attribut `gvidk_kita` (Ja/nein) je nach Schreibweise uneinheitlich. |
| Schulanlagen: Kindergarten | data/raw/stadtzh_extra/schulanlagen.geojson (Layer `poi_kindergarten_view`) | 358 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_schulanlagen | Kindergärten sind hier verortet, nicht im Kita-Datensatz. |
| Horte (Kinderhort) | data/raw/stadtzh_extra/schulanlagen.geojson (Layer `poi_kinderhort_view`) | 532 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_schulanlagen | Eigener Datensatz nicht gefunden; Horte stecken im Schulanlagen-Paket. Anzahl wirkt hoch, evtl. Mehrfachzählung pro Standort prüfen. |
| Schulhäuser (Volksschule) | data/raw/stadtzh_extra/schulanlagen.geojson (Layer `poi_volksschule_view`) | 127 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_schulanlagen | Volksschulstandorte. |
| Sonderschulen | data/raw/stadtzh_extra/schulanlagen.geojson (Layer `poi_sonderschule_view`) | 4 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_schulanlagen | Nur zur Vollständigkeit der Schulanlagen-Datei. |
| Spielplätze | data/raw/stadtzh_extra/spielplaetze.geojson | 188 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_poi_oeffentliche_spielplaetze | Attribut `eignung` (Altersgruppe) teils uneinheitlich formatiert. |
| Gemeinschaftszentren | data/raw/stadtzh_extra/gemeinschaftszentren.geojson | 26 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_gemeinschaftszentrum | Punkte. |
| Quartiertreffs (Zusatz) | data/raw/stadtzh_extra/quartiertreffs.geojson | 30 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_quartiertreff | Nicht verlangt, aber thematisch nah an Gemeinschaftszentren. |
| Züri-WC | data/raw/stadtzh_extra/zueri_wc.geojson (Layer `poi_zueriwc_view`, `_rs_view`, `_mobil_view`, `_mobil_rs_view`) | 139 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_zueri_wc | Fest (`zueriwc_view`/`rs_view`) und mobil (`mobil_view`/`mobil_rs_view`) in einer Datei; über `layer` trennbar. |
| Sportanlagen (Sport) | data/raw/stadtzh_extra/sport.geojson | 175 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_sport | 18 Layer: Sporthallen (32), Fussball (21), Schulschwimmanlagen (18), Zuerifit (12), Tennis (8), Skateranlagen (8) u. a. |
| Badeanlagen | data/raw/stadtzh_extra/sport.geojson (Layer `poi_freibad_view`, `hallenbad_view`, `flussbad_view`, `seebad_view`, `planschbecken_view`, `schulschwimmanlage_view`) | 7 + 7 + 6 + 6 + 13 + 18 = 57 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_sport | Keine eigene Badi-Datensatz; Badeanlagen sind Layer im Sport-Paket. |
| Erholungs- und Sporteinrichtungen | data/raw/stadtzh_extra/erholungs_sporteinrichtungen.geojson | 197 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_erholungs__und_sporteinrichtungen | Picknickplätze (99), Aussichtspunkte (47), Waldhütten (16), Waldlauf (14), Finnenbahn, Vitaparcours, MTB. |
| Abfallgefässe (Hundekot-/Abfallkübel) | data/raw/stadtzh_extra/abfallgefaesse.geojson | 4074 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_abfallgefaesse | Typ: Abfallhai 2275, Zürikübel 1358, Robidog (Hundekotbeutel-Spender) 187. Attribute `gefaesstyp_txt`, `auspraegung_*_txt`. |
| Hundezonen (Zusatz) | data/raw/stadtzh_extra/hundezonen.geojson | 728 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_hundezonen | Flächen (MultiPolygon). Hundeverbot 652, Leinenpflicht 69, Freilaufzone 7. Nicht verlangt, aber Hundekot-Thema. |
| Sammelstellen (Glas/Alu etc.) | data/raw/stadtzh_extra/sammelstellen.geojson (Layer `poi_sammelstelle_view`) | 179 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_sammelstelle | Wertstoff-Sammelstellen. Materialtyp in Attributen prüfen. |
| Kehrichtcontainer im öffentlichen Raum (Zusatz) | data/raw/stadtzh_extra/kehrichtcontainer.geojson | 365 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_erz_kehrichtcontainer_im_oeffentlichen_raum | Nicht verlangt. Container 770 l (293), Haushalt/Betrieb/Bio/Papier. |
| Velo-/Zweirad-Abstellplätze | data/raw/stadtzh_extra/zweiradparkierung.geojson | 2866 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_zweiradparkierung | Velo 1935, Velo/Motorrad 595, Motorrad 307. Gebührenpflichtig nur 40. |
| Sitzbänke | data/raw/stadtzh_extra/sitzbaenke.geojson | 7267 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_sitzbankkataster_ogd | Nur Punkte, keine weiteren Attribute in der Auswahl. |
| Brunnen (inkl. Trinkbrunnen) | data/raw/stadtzh_extra/brunnen.geojson | 1287 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_brunnen | Kein eigenes Trinkbrunnen-Attribut. `art`: öffentlich 1021, privat 256, Notwasserbrunnen 10. Trinkwasser-Eignung über `wasserart` (Züriwasser 817, Quellwasser 435) nur indirekt. Entspricht dem Datensatz «Brunnen», nicht doppelt geladen. |
| Kunst im Stadtraum | data/raw/stadtzh_extra/kunst_im_stadtraum.geojson (Layer `view_kioer`, `view_kub`) | 421 | CC0 | https://data.stadt-zuerich.ch/dataset/geo_kunst_im_stadtraum | 395 Punkte, 26 Features ohne Geometrie (Attribut-only), vor Verwendung filtern. |

## Nicht gefunden (Stand 2026-10-14)

- **Bibliotheken (PBZ):** kein Geo-Datensatz im Katalog (Suche «Bibliothek», Paketliste mit Filter `bibli`). Adressen evtl. über andere Quellen (PBZ-Website, OSM) zu holen.
- **Pingpong-Tische:** nicht im Katalog. Auch nicht als Layer in Sport oder Erholungs-Paketen.
- **Boccia:** nicht im Katalog; keine Layer-Entsprechung.
- **Plakatstellen:** nicht im Katalog (Suche «Plakat»).
- **Horte als eigener Datensatz:** nicht vorhanden. Horte sind Layer `poi_kinderhort_view` im Paket `geo_schulanlagen` (siehe oben).
- **Trinkbrunnen als eigene Kategorie:** nicht vorhanden. Nur im Paket `geo_brunnen` ohne Trinkbrunnen-Flag.

## Nicht geladen (bewusst)

- `ktzh_veloparkierungsanlagen__ogd_`: kantonaler Datensatz, nicht Stadt; falls gewünscht nachladen.
- `geo_standorte_zuerivelo`, `geo_veloverleih`, `geo_velopumpstationen`: Velo-Infrastruktur, nicht verlangt, bei Bedarf gleiches Muster.
- `geo_kunstbauteninventar`: Ergänzung zu «Kunst im Stadtraum», nicht verlangt.
- Layer `*_att`, `*_l`, `*_p` in den Multi-Layer-Paketen: Attribut-Tabellen oder Linien/Flächen, nicht als Punkte verwendet.

## Hinweise

- Lizenz aller Stadt-Zürich-Geodaten dieser Liste: CC0 (cc-zero) laut CKAN. Quellenangabe trotzdem im Spiel führen (siehe `DATA_SOURCES.md`).
- Die Datei `data/raw/stadtzh/` (anderer Pfad, anderer Agent) enthält `geo_brunnen__wvz_brunnen.geojson`, `geo_abfallgefaesse__...` und `geo_zueri_wc__...`. Die neuen Dateien in `stadtzh_extra/` sind bewusst separat, nicht zusammengeführt.
- Zeitstempel `metadata_modified` ist bei allen Paketen 2026-10-14 (CKAN-Stand beim Abruf).
