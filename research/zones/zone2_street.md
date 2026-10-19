# Zone 2 Kreis 5 Industrie: Strassenraum (Auftrag Z2B, 2026-10-19)

## Boden
- Audit verallgemeinert: `pipeline/audit_ground.py --zone N [min_area]` (ersetzt `audit_ground_z4.py`; zählt nur das Spielgebiet der Zone, Ausgabe `logs/audit_ground_z<N>.json`).
- Zone 2 (im Spielgebiet): AV-Fahrbahn ohne OSM-Strasse 14 400 m2 in 44 Flecken >= 60 m2 (grösster 3 070 m2 bei (20,658) = Turbinenplatz-Ost, sonst Vorplätze/Parkplätze), OSM-Strasse auf AV-Grün/Gebäude 2 290 m2 in 8 Flecken (grösster 560 m2 bei (107,374), Rest < 160 m2: Strassenachse über Park-/Hofrand, keine sichtbare Lücke).
- AV-befestigt, aber als Hof/Rasen gezeichnet wäre: 54 700 m2 in 82 Flecken (Turbinenplatz 8 300, Josefwiese/Josefareal 4 600 + 4 300, Schützeareal 2 600 …). Das behebt der globale Fix aus Zone 4 (`S["av_paved_ext"]` in `_ground_base`) schon: dort wird nichts mehr als Rasen gezeichnet, kein Zone-2-Sonderfall nötig.
- `places_detail_z2.json`: 2 Plätze, deren OSM-Fläche als Standard-Pflaster lief (Puls-5-Vorplatz (64,736), Platz Quellen-/Josef-/Motorenstrasse (853,58)), Boden aus SWISSIMAGE klassiert (Rasen / Kies / befestigt = Beton bzw. Asphalt nach OSM-`surface`). Keine Objekte ohne Foto.
- `markings_z2.json`: leer (Hook liest die Datei). Die automatische Gelb-Messung ist wie in Zone 4 nicht belastbar; Velostreifen/Parkfelder ohne Foto mit Position nicht erfunden.

## Plätze, Brunnen, Haltestellen
- Katalog-Brunnen doppelt gezeichnet: an sechs Stellen steht ein Brunnen aus `places_detail_*` (`convert` der WVZ-Brunnen, exakt gleiche Koordinate, < 0.5 m) UND der Katalog-Trog/die Katalog-Figur obendrauf. In `catalog_assign.json` ausgeschlossen (`exclude`, Hinweis `_z2`), `catalog.json` neu erzeugt (V2 -3, V6 -1, V8 -2):
  | WVZ | Ort | gezeichnet wird (places_detail) |
  |---|---|---|
  | BR-1245 (419,706), BR-1248 (448,763) | Escher-Wyss-Platz | Betonkübel-Brunnen «bucket» (Fotos Commons #25/#26, `research/v3/escher_wyss_platz.md`) |
  | BR-246 (462,244) | Josefwiese | `rfount` (sq3_josefwiese) |
  | BR-401 (1136,83), BR-188 (1113,23) | Limmatplatz | Tellerbrunnen, Trinkbrunnen (sq3_limmatplatz) |
  | BR-189 (-90,-221) | Hardplatz | Trinkbrunnen (hardplatz) |
- Nicht angefasst (Doppelung möglich, aber ohne `convert` käme der generische Brunnen zurück): Röntgenplatz BR-259 (Katalog V2 und eigenes `basin` 1.7 m daneben), Park-Brunnen BR-1257/BR-258/BR-441/BR-704 (`dfount`/`rfount` als Objekte). Entscheid braucht ein Foto, das den echten Brunnen zeigt.
- Escher-Wyss-Platz und Limmatplatz Haltestellen: die 28 Escher-Wyss-Fotos in `data/raw/photos/z2` sind Autokamera-Fahrten auf dem Hardbrückendeck (Bus-Haltestelle auf der Brücke sichtbar, keine Plattformdetails); am Limmatplatz sind H5/H3/H6 aus den VBZ-Daten schon korrekt platziert. Keine Haltestellen-Änderung ohne belastbares Foto (Typ/Lage unverändert).

## T19 Fussgängerstreifen (Recall)
Ursache des Recall ~50 % (Messung auf dem 0.25-m-Ortho, 1 025 gelbe Blobs auf der Fahrbahn): 339 echte Streifen scheiterten am Richtungsfilter (die Blob-Hauptachse eines 3 x 4 m grossen Blobs ist bis 90 Grad falsch), weitere 300 am Abstand zur nächsten Achse (Streifen am Knotenmund gehören zur Nebenstrasse, nicht zur nächsten Achse der Hauptstrasse) und am Breitenfilter (Schatten schneidet den Streifen).
Änderungen (`pipeline/markings_ortho25.py`, `pipeline/crossings.py::_scan25`):
1. Streifenrichtung aus der Periodizität (1.0 m = 0.5 m Farbe + 0.5 m Lücke) über 24 Winkel statt aus der Blob-Kovarianz; Ausdehnung aus Perzentilen der Maskenpixel.
2. Abgleich mit ALLEN Achsen im Umkreis (Richtung <= 50 Grad, Abstand <= 0.5 w + 8 m), Mindestbreite 35 % der Fahrbahn; Breite des Streifens = max(Blob, 70 % der Fahrbahn).
3. Zweites Closing (leichter) trennt Streifen, die am Knoten mit Haltelinien/Nachbarn verschmolzen sind.
4. Ausschuss: ganzer Blob auf der Fahrbahn (>= 70 %), Mindestfläche 9 m2, Streifenlänge >= 3.2 m, Füllgrad <= 0.93, mittleres Gelb < 52 (gelbe Taxis/Lieferwagen sind gesättigt), dunkle Blobs (Baumkronen) nur mit Rhythmus.
5. Zweite Meinung (`_rescue`): gelbe Blobs in Streifengrösse ohne messbare Geometrie (zerfranst/verschmolzen) bekommen den 0.5-m-Streifentest entlang der Strassenrichtung (`ortho_score >= STRONG 0.7`, dieselbe Messlatte wie für ungetaggte OSM-Knoten).
Zahlen (Spielgebiet, `crossings._scan25` vor Dedup / nach Dedup im Build):
| | vorher | nachher |
|---|---|---|
| Streifen aus dem Scan (Kandidaten) | 265 | 506 (351 gemessen + 155 per Streifentest gerettet) |
| im Build gezeichnet (Scan, nach Dedup gegen OSM-Knoten/Eigenabstand) | 211 | 403 (`logs/agentZ2B_tiles3.log`) |
| Recall gegen «Wahrheit» (41 OSM-getaggte Streifen im Spielgebiet, durch Ortho bestätigt, Abstand <= 7 m) | 68 % | 93 % |
Precision (Sichtprobe je 33 Ausschnitte `preview/z2_street_*`-Bogen, nicht archiviert): Blobs mit Streifenmass >= 0: ca. 80 %; gerettete Blobs ca. 90 % (Fehler: gelber Lieferwagen, Schattenränder). Vorher laut Doku ~90 %. Die Schwelle `STRIPE_MIN` (-0.1) ist der Regler: -0.2 gibt +40 % Kandidaten bei ca. 10 Punkten weniger Precision.
Offen: Streifen in Tiefschatten (Knoten Seebahn-/Badenerstrasse, Tramhaltestellen) und Knoten, an denen 3-4 Streifen und Haltelinien zu einem Blob verschmelzen; ein echter Matched-Filter (Schablone 4 Streifen x 3.5 m, 24 Winkel, FFT) wäre der nächste Schritt (~9 min Zusatzzeit im Build).

## T22 / T23 (Details `research/bumps.md`)
- T22: Bullingerstrasse (-549,-257)..(-492,-290) ist eine ungetaggte Unterführung (Strasse -3.0 m, DTM +4.2 m = Bahndamm, Klippen 3-6 m): die Strasse kletterte mit 64-100 % Neigung über den Damm. `pipeline/underpass_infer.py` erkennt solche Abschnitte (Plateau <= 90 m, >= 1.2 m über beiden Portalen, Klippen >= 1.5 m/3 m), `road_height.carve_underpasses` senkt das Gelände auf die Linie zwischen den Portalhöhen. 4 Fälle im Gebiet (Bullinger 40 m, Wasserwerkstrasse (1604,81) 20 m, (1702,-25) 9 m, Ackersteinstrasse (-1114,1740) 10 m).
- T23: Ursache der 10-20-cm-Dellen = `MAX_FILL` (1.2 m) in `road_height.apply`: Zellen am Fahrbahnrand neben einer Mulde/Einschnitt (Hohlstrasse, Seebahn-/Badenerstrasse) konnten nicht bis Strassenniveau gefüllt werden; der Asphalt hat Eckpunkte genau auf der Polygonkante und kippt dort. Innerhalb der Fahrbahn gilt jetzt `MAX_FILL_IN` = 3.0 m.

## Prüfung
- `web/tests/traffic_legal.mjs` (nach den Änderungen, Testkacheln im Dev-Server): grün, Escher-Wyss-Platz 0.00 % (vorher 0.02 % in qa14, früher 1.15 %), Langstrasse 0.09 %, Unterführung 0.05 %, übrige 0 % (`logs/agentZ2B_traffic_legal.log`).
- Testkachel-Läufe: `logs/agentZ2B_tiles.log`, `_tiles2.log`, `_tiles3.log` (11 Kacheln, Bullinger/Hohl/Förrlibuck/Seebahn/Badener/Kornhaus + 2 in Zone 2); die übrigen Kacheln bekommen alles erst im nächsten Komplett-Build.
- Zu prüfen bei der Abnahme: die vier erkannten Unterführungen (v. a. Wasserwerkstrasse (1604,81): echte Unterführung oder Brückenrampe?), Bild-Abnahme der Streifen nach dem Komplett-Build.
