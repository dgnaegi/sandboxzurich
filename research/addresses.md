# Hausnummern und Strassenschilder

Quelle: OpenStreetMap (ODbL), `data/raw/osm/kreise.json`; Objekte mit `addr:housenumber` (Nodes, Gebäude-Ways), Strassennamen aus benannten `highway`-Ways (ohne Fuss-/Velowege, Service). Gebäudewände: swissBUILDINGS3D. Verarbeitung: `pipeline/addresses.py`.

Abdeckung Testgebiet (x 600…1200, y −1000…−400): 457 OSM-Adressobjekte, 426 Schilder, 550 Gebäude (Grundrisse) im Gebiet. Zahlen pro 8-m-Zelle: ca. 383. Grobe Abdeckung also ca. 70-75 % der Gebäude (Nachbargebäude teilen sich oft eine Nummer; Hofgebäude haben keine).
Innenliegende Adresspunkte werden an die zur Strasse gewandte Wand projiziert; Eingangs-Nodes (ohne Nummer) werden nicht verwendet.
Strassenschilder: 64 Kreuzungen, 130 Schilder an Hausecken (3.0 m), Wand möglichst parallel zur Strasse.
