# Grosse Strassenmöbel – Varianten (Kreis 3/4/5/9)

Quellen: ewz-Beleuchtung (`geo_oeffentliche_beleuchtung_der_stadt_zuerich__ewz_brennstelle_p.geojson`), OSM `shop=kiosk` (`data/raw/osm/part_pois_r.json`), VBZ-Plakatstelle, Sammelstellen (`data/raw/stadtzh_extra/sammelstellen.geojson`, 179 Punkte stadtweit, 0 in Kreis 3/4/5/9). Zahlen: `variant_counts.json`.

| Variante | Anzahl (Daten) | Zuordnungsmerkmal | Form, Masse (geschätzt) | Material / Farbe (Richtwert) | Beispiel-Foto-IDs |
|---|---|---|---|---|---|
| **M1 Kandelaber / Seilleuchte (Strassenlampe)** | 12 554 (ewz-Brennstellen in Gebiet) | nur `art_txt` = «Beleuchtung», `orientierung` (Azimut). Keine Typ-Angabe | Mast 5–8 m, Kopf 0.6–1.0 m; Seilleuchte = Leuchte an Quertrage zwischen Häusern, Höhe 6–8 m | Mast anthrazit #3a3f44, Leuchtglas warmweiss | nicht gesichert. Foto-Befund ≤ 12 m: keine eindeutige Lampe. Varianten (Kandelaber vs. Seil) nur mit Fotos je Punkt |
| **M2 Kiosk** | 47 (OSM `shop=kiosk`, 8 mit Name, z. B. «k kiosk», «Kiosk Alexsa») | OSM-Tags `shop=kiosk`, `brand` | Kabine 2.5 × 2.5 m, Höhe 2.8 m, Vordach/Markise, Auslage | Kiosk-Farben je Marke (keine Farbangabe, nicht geprüft) | keine sicher. Fotos ≤ 12 m zeigen Strassen, Kiosk nicht im Bild |
| **M3 Plakatstelle VBZ** (Säule/Stele an Haltestelle) | 402 | nur ID `plakatstellenrvbz`, `orientierung` | Stele 1.8 × 1.2 m, Höhe 2.2 m (Richtwert) | Metall anthrazit / Plakat weiss | nicht gesichert (Plakatstelle nicht als Einzelobjekt auf Fotos) |
| **M4 Plakatsäule / Plakatwand (frei)** | 0 | kein Datensatz in Kreis 3/4/5/9 gefunden | – | – | keine Daten. Nur Wildplakate aus `pipeline/gen_wildposters.py` |
| **M5 Sammelstelle** | 0 im Gebiet | `kategorie` = «Sammelstelle» (stadtweit 179) | – | – | – |

## Befunde
- Die ewz-Leuchten sind ein Punkt je Leuchte ohne Typ. Eine Variantenzuordnung braucht Fotos je Punkt. 3 924 Leuchten haben ein Foto ≤ 25 m, aber ≤ 12 m zeigen die Bilder meist keine erkennbare Lampe.
- Kioske: 47 Punkte, im Foto ≤ 12 m nicht sichtbar. Ein Kiosk-Katalog braucht Commons-Fotos mit Namen (gezielte Suche) oder Vor-Ort-Stichproben.
- Plakatsäulen als Kategorie gibt es in den Daten nicht. Die VBZ-Plakatstellen sind an Haltestellen. Freie Plakatsäulen und -wände wären eine Foto-Aufgabe.
- Keine Assign-Hints für Möbel.
- Abgebrochen: Kleinkram nach Auftrag nicht bearbeitet.
