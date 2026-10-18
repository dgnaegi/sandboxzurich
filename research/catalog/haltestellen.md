# Haltestellen – Ausstattung (Kreis 3/4/5/9)

Quelle: VBZ-Infrastruktur-OGD (`data/raw/stadtzh_all/geo_vbz_infrastruktur_ogd__haltestellen_*.geojson`, CC0), gefiltert auf Kreis 3/4/5/9 (`research/kreise_poly_simplified.json`). Zahlen aus `variant_counts.json`. Fotos: `research/catalog/objects.json`. Masse aus `web/public/data/stops_equip.json` (abgeleitet), Richtwerte für Farbe.

Es gibt keinen Datensatz für Haltestellenmasten mit Fahne und keinen für Bodenmarkierungen «BUS»/Kap. Die Haltebalken (150 Punkte) sind nur Koordinaten.

| Variante | Anzahl (Daten) | Zuordnungsmerkmal | Form, Masse | Material / Farbe (Richtwert) | Beispiel-Foto-IDs |
|---|---|---|---|---|---|
| **H1 Glaswartehalle Standard** (neuer Typ, Stahl/Glas, Pultdach) | 243 | `wartehalle.einbaudatum` = 2018 (Typ-Feld `typ` = 36 für alle 358) | Längen in stops_equip (120 Stk.): 7 m (37), 10–11 m (13 bzw. 19), Ausreisser ab 70 m (Polygone); Tiefe 1.4 m (61) oder 2.2 m (21); Dachhöhe ca. 2.5 m | Stahl anthrazit #3a3f44, Glas grünlich getönt #b9c9c4, Dach leicht geneigt | WH-240, WH-723, WH-116, WH-761 (Glas, Pultdach, Bank im Innern) |
| **H2 Wartehalle älter / unbekannt** | 115 | `einbaudatum` = 2000 (19) oder leer (86) | wie H1, Dachform nicht sicher geprüft | Stahl grau, Glas klar | keine sicher gesehen |
| **H3 Ticketautomat Typ 20** | 210 | `ticketautomat.typtext` = «Ticketautomat Typ 20» (einziger Typ) | Säule/Kasten ca. 1.3 m hoch, 0.5 m breit, in der Wartehalle oder am Mast | grau/anthrazit #55595e | nicht sicher. Fotos zeigen Haltestellen, nicht den Automaten (Ausnahme unklar) |
| **H4 DFI-Anzeiger Wand** (Info Smart) | 54 | `dfi_anzeiger.typ` = «Info Smart» | Bildschirm ca. 0.6 × 0.4 m, Wandmontage ca. 2.5 m | Gehäuse anthrazit, Display dunkel | keine sicher gesehen |
| **H5 DFI-Anzeiger Decke** (Info Smart, an Decke montiert) | 29 | `dfi_anzeiger.typ` = «Info Smart an Decke montiert» | wie H4, hängend unter Dachkante | wie H4 | WH-3 (Bahnhof-Überdachung, Anzeige unter Dach, unsicher) |
| **H6 Sitzbank in Wartehalle kurz** | 155 | `sitzgelegenheit.typ` = «Bank in WH kurz» | Länge ca. 1.5–2 m, Tiefe 0.4 m, Sitzhöhe 0.45 m | Holzlatten hell #b08a5a, Stahl anthrazit | WH-116, WH-761 (Bank im Glasunterstand, Foto unscharf, unsicher) |
| **H7 Sitzbank in Wartehalle lang** | 93 | `typ` = «Bank in WH lang» | Länge 3–4 m | wie H6 | keine sicher |
| **H8 Bank Code 137 / 138 / 139 / 136** | 118 / 63 / 5 / 11 | `typ` als Zahl, keine Klartext-Bezeichnung in den Daten | nicht geprüft | nicht geprüft | Zuordnung zu Typen unklar, Foto nötig |
| **H9 Stehhilfe / Bank frei** | 26 (Stehhilfe) + 33 (Bank) | `typ` = «Bank Stehhilfe» / «Bank» | Stehhilfe Lehnbügel ca. 0.8 m über Boden | Metall anthrazit | keine sicher |

Weitere Ausstattung (Zähler, nicht als Variante geführt): Plakatstelle VBZ 402 (kein Typ-Feld, Foto nötig), Infosystem 574, Haltebalken 150, Papierkorb (nicht in Kreis 3/4/5/9 geprüft).

## Befunde
- Typ-Felder sind bei Wartehallen einheitlich (`typ` = 36). Die Unterscheidung in H1/H2 beruht nur auf dem Einbaudatum, das nicht die Form zeigt. Unterschiedliche Dachformen sind auf Fotos sichtbar, aber nicht in den Daten.
- Im Foto-Befund (≤ 12 m) sind Wartehallen gut erkennbar (WH-240, WH-723, WH-116, WH-761 zeigen Glas mit Pultdach). Die meisten Fotos zeigen aber nur die Strasse.
- Ticketautomat: keine Form-Varianz in den Daten; der Automat ist auf den Fotos zu klein, um ihn zu erkennen.
- Die Längen aus `stops_equip.json` sind geometrisch abgeleitet und gelten für die Länge des Wartehallen-Polygons, nicht für die Kabine.

## Assign-Hints
Keine für Haltestellen. Die wenigen sicheren Fälle (WH-240 usw.) sind nur Beispiele. Eine verlässliche Zuordnung je Objekt bräuchte Fotos mit Haltestelle im Bild (Commons/Mapillary gezielt pro Haltestelle).
