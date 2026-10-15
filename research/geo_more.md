# D2: Bundes-, Kantons- und Stadt-Geodaten (Gebiet Kreis 3/4/5/9)

Gebiet: LV95 2678800–2683100 / 1246900–1249900 (WGS84 ca. 8.44–8.55 E, 47.36–47.40 N).
Skript: `pipeline/fetch_geo_more.py` (Steps `sbb wfs stadt stac clip pv`). Rohdaten: `data/raw/geo_more/`, Zuschnitt: `data/raw/geo_more/clipped/`.

| Quelle | Datensatz | Inhalt | Features im Gebiet | Nutzen | Lizenz | Datei |
|---|---|---|---|---|---|---|
| geo.admin.ch STAC | swissTLM3D 2026-02 (gpkg, national 4.8 GB) | Gebäude-Footprints | 16972 | Gebäudegrundrisse (Abgleich LOD2) | OGD swisstopo, Quellenangabe (STAC-Feld «proprietary», Praxis prüfen) | `clipped/tlm_tlm_bauten_gebaeude_footprint.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Einzelbäume | 20011 | Bäume im Spiel (Kronen-Ersatz) | wie oben | `clipped/tlm_tlm_bb_einzelbaum.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Bahn (Eisenbahn) | 1802 | Bahngeleise | wie oben | `clipped/tlm_tlm_oev_eisenbahn.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Haltestellen | 168 | ÖV-Haltestellen | wie oben | `clipped/tlm_tlm_oev_haltestelle.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Strassen (Achsen) | 6830 | Strassennetz (Abgleich Roadgraph) | wie oben | `clipped/tlm_tlm_strassen_strasse.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Strasseninfo | 4777 | Strassenklassen/Attribute | wie oben | `clipped/tlm_tlm_strassen_strasseninfo.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Verkehrsbauten (Plan/Linie) | 18 + 1 | Brücken/Unterführungen (Teilweise) | wie oben | `clipped/tlm_tlm_bauten_verkehrsbaute_ply.gpkg`, `..._lin.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Bauten Sportbauten, Staubauten, Versorgungsbauten, Verbauung | 66 / 3 / 41 / 6 / 43 | Sport- und Versorgungsbauten | wie oben | `clipped/tlm_tlm_bauten_*.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Bodenbedeckung | 97 | Flächen | wie oben | `clipped/tlm_tlm_bb_bodenbedeckung.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Fliessgewässer / stehende Gewässer | Layer vorhanden | Wasser | wie oben | `clipped/tlm_tlm_gewaesser_*.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Namen (Siedlung, Flur, Gelände) | 1187840 B / 52 / 4 / 107 | Ortsnamen, Quartiernamen | wie oben | `clipped/tlm_tlm_namen_*.gpkg`, `tlm_tlm_name_gelaendename.gpkg` |
| geo.admin.ch STAC | swissTLM3D | Mauern, Treppen, Brunnen (Layer `tlm_bauten_mauer`, `tlm_bauten_leitung`) | 0 | Im Gebiet keine Mauer-Objekte in TLM; Treppen/Brunnen nicht separat vorhanden | wie oben | – |
| geo.admin.ch STAC | Solarkataster Dächer (SOLKAT, generalisiert, gpkg) | Dachflächen mit Potenzial | 121391 | Solarpotenzial (Dachfarbe/Panels, Realismus) | BFE OGD, Quellenangabe | `clipped/solar_daecher.gpkg` |
| geo.admin.ch STAC | Elektrizitätsproduktionsanlagen (BFE, CSV) | PV und andere Anlagen | 530 | Echte PV-Anlagen als Dachdetail / Quest-Material (Energiewende) | BFE OGD, Quellenangabe | `clipped/pv_anlagen.csv` |
| geo.admin.ch STAC | Strassenlärm Tag (COG-Tiff, 553 MB) | Lärmexposition | nicht geladen | Lärm-Thema für Wohnen/Verkehr-Quest; Raster | OGD swisstopo/BAFU | `data/raw/geo_more/noise/` (Download nicht gestartet) |
| SBB Open Data | perron | Perrons | 31 | Bahnhofsperrons im Gebiet | SBB Open Data, Lizenz pro Datensatz prüfen | `sbb/perron.geojson` |
| SBB Open Data | perronoberflache | Perronoberflächen | 60 | Perronbeläge | wie oben | `sbb/perronoberflache.geojson` |
| SBB Open Data | haltestelle-haltekante | Haltekanten | 355 | Haltekanten | wie oben | `sbb/haltestelle-haltekante.geojson` |
| SBB Open Data | larmschutzwand | Lärmschutzwand Bahn | 20 | 3D-Wände entlang Bahn (Modellierung) | wie oben | `sbb/larmschutzwand.geojson` |
| SBB Open Data | larmschutzwall | Lärmschutzwall Bahn | 0 | – | wie oben | `sbb/larmschutzwall.geojson` |
| SBB Open Data | brucken | Brücken Bahn | 74 | Bahnbrücken | wie oben | `sbb/brucken.geojson` |
| SBB Open Data | bahnubergang | Bahnübergänge | 5 | Schranken | wie oben | `sbb/bahnubergang.geojson` |
| SBB Open Data | tunnel | Bahntunnel | 9 | Hinweis (oberirdisch irrelevant) | wie oben | `sbb/tunnel.geojson` |
| Kanton ZH OGD-WFS | ogd-0415 Gebäudealter | Gebäudealter je Gebäude | 11791 | Altbau/Neubau-Look, Quest Wohnen | CC0 (OGD ZH) | `wfs/gebaeudealter.geojson` |
| Kanton ZH OGD-WFS | ogd-0272 Gebäude Hauptadresse | Gebäude mit Bauperiode, EFH/MFH | 1338 | Gebäudetyp | CC0 | `wfs/gebaeude_ha.geojson` |
| Kanton ZH OGD-WFS | ogd-0248 Gebäudevolumen | Volumen je Hektare | 705 | Dichte | CC0 | `wfs/gebaeude_volumen.geojson` |
| Kanton ZH OGD-WFS | ogd-0368 Denkmalschutzobjekte (Punkte) | Denkmalschutz | 161 | Denkmal-Markierung | CC0 | `wfs/denkmal_punkte.geojson` |
| Kanton ZH OGD-WFS | ogd-0140 ZVV-Haltestellen | ÖV-Haltestellen | 99 | Haltestellen (Abgleich SBB/TLM) | CC0 | `wfs/zvv_haltestellen.geojson` |
| Kanton ZH OGD-WFS | ogd-0108 S-Bahn-Linien | Linien | 20 | ÖV-Linien | CC0 | `wfs/sbahn_linien.geojson` |
| Kanton ZH OGD-WFS | ogd-0597 Grünflächen 2024 | Grünflächen (Klima) | 472 | Grün/Park im Spiel | CC0 | `wfs/gruenflaechen_2024.geojson` |
| Kanton ZH OGD-WFS | ogd-0547 LSW-Status (Lärmschutzwand) | Lärmschutzwand-Status | 3 | Lärmschutzwände Strasse | CC0 | `wfs/laermschutzwand_status.geojson` |
| Kanton ZH OGD-WFS | ogd-0288 Brückenbereich | Brückenbereich Strasse | 1 | Brücken | CC0 | `wfs/strassen_brueckenbereich.geojson` |
| Kanton ZH OGD-WFS | ogd-0202 Velonetz Kanton | Velonetz | 12 | Velowege (Abgleich Stadt) | CC0 | `wfs/velonetz_kanton.geojson` |
| Stadt ZH OGD-WFS | Verkehrsknoten mit Lichtsignalanlage | Lichtsignal-Knoten | 144 | Ampeln im Spiel | CC0 | `stadt/lichtsignal_knoten.geojson` |
| Stadt ZH OGD-WFS | Denkmalpflege-Inventar | Inventarobjekte | 2577 | Schützenswerte Bauten | CC0 | `stadt/denkmalpflege_inventar.geojson` |
| Stadt ZH OGD-WFS | LBK Lärmschutzwand | Lärmschutzwand Stadt | 7 | Wandobjekte | CC0 | `stadt/laermschutzwand_stadt.geojson` |
| Stadt ZH OGD-WFS | Alleenkonzept | Baumreihen | 1515 | Baumreihen (Strassenbäume) | CC0 | `stadt/alleen.geojson` |
| Stadt ZH OGD-WFS | Bauten Blockmodell 2D | Gebäude-Blöcke | 16174 | Gebäude-Footprints mit Höhe (Alternative zu LOD2) | CC0 | `stadt/bauten_blockmodell.geojson` |

## Nicht gefunden
- Gründächer, Fassadenbegrünung: weder im Kanton-OGD-WFS (`maps.zh.ch/wfs/OGDZHWFS`, 518 Layer) noch im Stadt-CKAN gefunden. Websuche bestätigt keinen OGD-Datensatz.
- Strassenbeläge (Kanton/Stadt): kein passender OGD-Layer im Gebiet gefunden (Kanton: `larmarme-strassenbelage` nur als Verweis).
- Lichtsignal Kanton (`ogd-0523`): 0 Features im Gebiet.
- Stadt-Downloadportal (gpkg): für Skripte gesperrt (HTML); Ausweg über WFS auf `www.ogd.stadt-zuerich.ch/wfs/geoportal/`.
- Mauern, Treppen, Brunnen aus swissTLM3D: im Gebiet keine Objekte in den entsprechenden Layern.

## Hinweise
- swissTLM3D (4.8 GB) und Solarkataster (1.1 GB) liegen in `data/raw/geo_more/tlm/` und `solar/`: Zip-Gross-Downloads, nicht im Repo. Clip ist reproduzierbar.
- Einige TLM-Layer ohne Geometrie werden im Clip übersprungen (FeatureError).
- Quellenangaben und Lizenzen in `docs/DATA_SOURCES.md` nachtragen (nicht Teil dieses Auftrags).
