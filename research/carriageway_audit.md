# Fahrbahn-Abgleich: OSM vs Amtliche Vermessung vs Orthofoto

Spielgebiet, 1203 OSM-Strassenabschnitte (ohne service), 98.8 km Achse. Skript: `pipeline/carriageway_audit.py`.

## Kennzahlen (laengengewichtet)

| | alt (OSM-Buffer) | neu (AV + kalibriert) |
|---|---|---|
| Fahrbahnbreite im Mittel | 6.80 m | 7.75 m |
| IoU Fahrbahn vs AV-Fahrbahn (Fenster um die Achse) | 0.72 | 0.91 |
| Gesamtflaeche Fahrbahn | 90.2 ha | 97.1 ha |
| AV-Fahrbahn (Referenz) | 84.4 ha | |

Breitenfehler gegen die AV-Breite auf Abschnitten, wo die AV Fahrbahn und Trottoir trennt (996 Abschnitte, 85.2 km): alt Median -1.05 m, |Fehler| p90 6.40 m; neu Median +0.00 m, p90 0.25 m.

## Nach Strassenklasse

| Klasse | km | OSM alt | AV gemessen (getrennt) | neu | IoU alt | IoU neu |
|---|---|---|---|---|---|---|
| residential | 49.2 | 6.6 | 7.6 | 7.4 | 0.74 | 0.94 |
| tertiary | 31.4 | 6.7 | 8.6 | 8.1 | 0.69 | 0.89 |
| primary | 11.6 | 7.4 | 7.8 | 7.4 | 0.69 | 0.82 |
| secondary | 3.9 | 7.8 | 10.1 | 9.9 | 0.74 | 0.88 |
| unclassified | 2.4 | 6.8 | 10.1 | 9.4 | 0.73 | 0.94 |
| tertiary_link | 0.2 | 4.2 | 6.3 | 5.7 | 0.76 | 0.92 |
| primary_link | 0.2 | 6.6 | 5.8 | 5.8 | 0.77 | 0.88 |

Kalibrierte Breiten (Median der AV-Fahrbahn dort, wo Trottoir getrennt erfasst ist): primary 7.2 m, primary_link 5.8 m, residential 6.8 m, secondary 11.0 m, secondary_link 5.2 m, tertiary 8.5 m, tertiary_link 6.5 m, unclassified 8.5 m

## Orthofoto-Kontrolle (SWISSIMAGE 0.5 m, Raster 3 m)

Asphalt ist dunkler und weniger hell als Trottoir/Platzbelag. Mittlere Helligkeit (0-255) in sich ausschliessenden Zonen:

| Zone | m2 | Helligkeit | gruenlich |
|---|---|---|---|
| AV Fahrbahn (Referenz) | 791694 | 87 | 0 % |
| AV Trottoir/Insel | 439857 | 87 | 0 % |
| alt: von OSM-Fahrbahn gebaut, nicht AV-Fahrbahn | 315765 | 91 | 0 % |
| neu: gebaute Fahrbahn, nicht AV-Fahrbahn | 284004 | 92 | 0 % |
| alt gebaut, neu entfernt | 56772 | 87 | 0 % |
| neu gebaut, alt nicht | 125604 | 91 | 0 % |
| AV Fahrbahn, alt nicht gebaut | 206181 | 93 | 0 % |
| AV Fahrbahn, neu nicht gebaut | 105588 | 95 | 0 % |

## Groesste Abweichungen (Nummern in `preview/carriageway_audit.jpg`)

| # | Strasse | Typ | Laenge | OSM alt | AV | neu | Versatz | vertrauenswuerdig |
|---|---|---|---|---|---|---|---|---|
| 1 | Limmatstrasse | residential | 374 m | 7.0 | 15.5 | 15.5 | -0.1 | 99 % |
| 2 | Hardturmstrasse | residential | 857 m | 6.4 | 14.8 | 14.8 | +2.8 | 98 % |
| 3 | Flurstrasse | unclassified | 121 m | 6.4 | 14.5 | 14.5 | -2.2 | 94 % |
| 4 | Flurstrasse | unclassified | 102 m | 6.4 | 15.0 | 14.8 | -2.9 | 81 % |
| 5 | Stauffacherstrasse | tertiary | 80 m | 6.4 | 17.0 | 16.8 | -1.1 | 86 % |
| 6 | Gessnerallee | tertiary | 160 m | 6.4 | 13.2 | 13.2 | +3.6 | 98 % |
| 7 | Pfingstweidstrasse | primary | 120 m | 6.4 | 13.2 | 13.2 | -3.7 | 100 % |
| 8 | Baslerstrasse | residential | 238 m | 6.4 | 13.0 | 13.0 | -0.6 | 100 % |
| 9 | Pfingstweidstrasse | primary | 110 m | 9.6 | 16.0 | 16.0 | -3.9 | 100 % |
| 10 | Werdstrasse | tertiary | 153 m | 3.2 | 9.0 | 9.0 | -0.1 | 100 % |
| 11 | Hardturmstrasse | primary | 84 m | 9.6 | 17.8 | 17.8 | -3.0 | 100 % |
| 12 | Hardbrücke | primary | 118 m | 9.6 | 3.9 | 4.0 | +1.1 | 77 % |
| 13 | Röntgenstrasse | residential | 93 m | 3.2 | 10.0 | 10.0 | +1.9 | 96 % |
| 14 | Hardbrücke | primary | 129 m | 9.6 | 4.4 | 4.4 | +2.2 | 56 % |
| 15 | Sportweg | residential | 120 m | 7.0 | 12.2 | 12.2 | -0.4 | 100 % |
| 16 | Hardturmstrasse | unclassified | 116 m | 6.4 | 11.8 | 11.8 | +0.2 | 100 % |
| 17 | Badenerstrasse | tertiary | 64 m | 3.2 | 13.2 | 12.9 | +2.4 | 83 % |
| 18 | Hardturmstrasse | residential | 73 m | 6.4 | 14.8 | 14.8 | +2.8 | 100 % |
| 19 | Hardbrücke | primary | 128 m | 9.6 | 4.0 | 4.6 | +1.7 | 65 % |
| 20 | Baslerstrasse | residential | 167 m | 7.0 | 12.0 | 12.0 | +0.8 | 100 % |
| 21 | Sihlfeldstrasse | residential | 156 m | 7.0 | 12.0 | 12.0 | +1.6 | 98 % |
| 22 | Hardturmstrasse | primary | 67 m | 3.2 | 12.0 | 12.0 | -4.1 | 100 % |
| 23 | Aargauerstrasse | secondary | 105 m | 6.4 | 12.0 | 12.0 | +1.2 | 96 % |
| 24 | Hallwylstrasse | residential | 100 m | 3.2 | 9.0 | 9.0 | +0.1 | 78 % |
| 25 | Zentralstrasse | residential | 249 m | 3.2 | 8.0 | 8.0 | -0.4 | 94 % |
