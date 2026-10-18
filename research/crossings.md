# Fussgängerstreifen (T01) – Entscheid pro OSM-Querungsknoten

Modul `pipeline/crossings.py` (Hook `# crossings2` in `streets.markings()`), Cache `data/build/crossings_ortho.json`
(Knoten-ID -> draw / src / tag / score), Kontrollbogen `preview/crossings_check.jpg`.

## Befund
Die Ticket-Annahme «696 Knoten ohne Markierungs-Tag» stimmt nicht: von 962 Knoten sind 694 **explizit** `crossing=unmarked`
(436) oder `crossing:markings=no` (258). Gegenprobe SWISSIMAGE: von diesen 442 prüfbaren Knoten (Strasse <= 6 m) zeigen nur
ca. 8 ein gelbes Streifenmuster, davon sind bei Sichtkontrolle nur 2-3 echt (übrige: Laub, Backstein). Die Tags sind also meist richtig;
es fehlten die Zebras, deren Knoten **keinen Strassen-Way** teilt (Signalzebras u.a. Freihofstrasse, Güterbahnhof).

## Regeln
1. Tag zebra/marked/uncontrolled/traffic_signals/`crossing:markings`/`crossing_ref=zebra` -> Streifen ("tag").
2. Knoten ohne Way: nächste Fahrbahn (hw != service, Breite >= 4 m) bei Tag-Knoten <= 10 m, bei Tag-losen <= 6 m (Streifen auf die Achse gesetzt).
3. Zone 30 / Begegnungszone / Fussgängerzone: Tags allein zählen nicht (Ausnahme alte Regel: T30 signalisiert, Schulweg <= 40 m, Lichtsignal).
4. SWISSIMAGE (0.5 m, `data/raw/ortho_wms`): Gelbmaske (sonnig: gelb, R~G; Schatten: lokaler Kontrast) in einem Fenster 4.5 m x Fahrbahnbreite,
   Verschiebung +-4 m / +-1.5 m. Score = Anteil gelber Pixel x Querabdeckung. Score >= 0.7 beweist Streifen ("ortho"), auch in Zonen oder gegen ein `no`-Tag.
   0.5-0.7 ist Vegetation/Backstein (Sichtkontrolle), daher nicht genug. Die Streifen (0.5 m) sind bei 0.5 m/px nur als Gelbton sichtbar, nicht zählbar.
5. Im gemessenen Langstrasse-Bereich (`markings_langstrasse.json` Region) werden keine Ortho-Streifen ergänzt (markings_override zeichnet sie).

## Zahlen (962 Knoten im Spielgebiet)
| | vorher | nachher |
|---|---|---|
| gezeichnet | 173 | 234 |
| davon per Tag | 173 | 230 |
| davon per Ortho (ohne Tag) | 0 | 4 |
Nicht gezeichnet: 693 explizit unmarked/no, 35 Tag-Knoten (Zone 30 ohne Schulweg/T30 oder kein Way <= 10 m: sehr lange Zebras auf Fussweg/Parkpfad).

Grenzen: Ortho zeigt nur Knoten nahe der OSM-Achse; verschattete Zebras haben Score ~0 (Tag entscheidet trotzdem). 
