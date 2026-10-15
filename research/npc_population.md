# NPC-Bevölkerung Kreis 4 (Aussersihl: Werd, Langstrasse, Hard) und Kreis 5

Stand: 2026-10-15. Basisjahr 2025, sofern nicht anders angegeben. Maschinenlesbar: `research/npc_population.json`. Rohdaten: `data/raw/stats/`. Auswertungsskripte: `research/work_stats/`.

## Quellen (alle Stadt Zürich OGD, CKAN-Download per Python)
- Bevölkerung nach Alter, Herkunft, Quartier (BEV390OD3903), Stichtag 2025. Einzelalter, daraus die Gruppen 0-5, 6-12, 13-19, 20-39, 40-64, 65+.
- Bevölkerung nach Nationalität und Quartier (BEV336OD3361), 2025.
- Privathaushalte nach Haushaltsform und Haushaltsgrösse (BEV380OD3805/3806), 2025.
- Hundebestand der Stadt Zürich (KUL100OD1001), Stichtag 2025-12-31. Dies ist das städtische Hunderegister, Zuordnung über Wohnort der Halter:innen.
- Bevölkerungsbefragung ab 2019 (BEV473OD4732), Jahre 2023-2025 gepoolt, gewichtet mit Personengewicht. Kreis 4: n=837, Kreis 5: n=487 (klein).
- Wochenaufenthalter:innen (BEV358OD3582), 2025.
- Hotelgäste Stadt Zürich (WIR110OD1104, BFS), 2025.
- Fuss-/Velozählung (ted_taz, Viertelstunden, 2025), Standorte aus Koordinaten im Datensatz abgeleitet.
- Arbeitsstätten/Beschäftigte nach Quartier (wirtschaft-arbeitsstaetten-beschaeftigte-jahr-quartier-noga): nur Jahre 2001, 2005, 2008 vorhanden.
- Web-Suche (3 von 20 Anfragen verwendet): Pendelzahlen 2020 (Stadt Zürich/BFS, Originalseite nicht abgerufen).

## Ergebnisse

**Altersstruktur 2025** (Anteil Wohnbevölkerung)

| Gebiet | 0-5 | 6-12 | 13-19 | 20-39 | 40-64 | 65+ |
|---|---|---|---|---|---|---|
| Stadt | 5.3 % | 6.2 % | 5.7 % | 36.4 % | 32.5 % | 13.9 % |
| Kreis 4 | 3.9 % | 3.4 % | 3.3 % | 47.1 % | 33.1 % | 9.2 % |
| Kreis 5 | 4.7 % | 4.5 % | 3.9 % | 41.7 % | 36.1 % | 9.1 % |
| Kreis 3 (Vergleich) | 4.8 % | 6.3 % | 6.3 % | 38.6 % | 32.1 % | 11.9 % |
| Kreis 9 (Vergleich) | 5.9 % | 6.2 % | 5.3 % | 35.0 % | 33.0 % | 14.5 % |

Kinderanteil 0-12: Kreis 4 7.3 %, Kreis 5 9.2 %, Stadt 11.5 %. Kreis 4 hat mit 20-29 Jahren 19.5 % den höchsten Anteil der Stadt (Stadt 15.9 %).

**Ausländeranteil und Nationalitäten 2025**: Kreis 4 37.8 % (Stadt 33.9 %), Kreis 5 32.0 %. Häufigste Nationalitäten Kreis 4: Schweiz 62 %, Deutschland 7.7 %, Italien 5.1 %, Spanien 3.0 %, Portugal 2.7 %, Frankreich 1.6 %. Kreis 5 ähnlich: Deutschland 8.0 %, Italien 4.1 %.

**Haushalte 2025**

| Gebiet | Einpersonen | Familien mit Kindern (Anteil Haushalte) |
|---|---|---|
| Kreis 4 | 49.8 % | 13.3 % |
| Kreis 5 | 45.4 % | 17.0 % |
| Stadt | 44.0 % | 22.9 % |

Familienhaushalte sind in Kreis 4 seltener als im Stadtschnitt. Kreis 4 ist ein Einpersonen-Quartier.

**Hunde 2025-12-31** (Hunde pro 100 Einwohner): Kreis 4 1.75 (515 Hunde), Kreis 5 2.19 (350), Kreis 3 1.86, Kreis 9 2.10, Stadt 2.23 (10 091).

**Modalsplit**: Kein Stadt- oder Kreiswert zum Modalsplit der Wege gefunden. Der Mikrozensus Mobilität ist nur kantonal publiziert (Web-Suche). Ersatzweise Nutzungshäufigkeit aus der Bevölkerungsbefragung (täglich bis 2-5 Mal pro Woche):

| Gebiet | Velo | ÖV | Auto |
|---|---|---|---|
| Kreis 4 | 43 % | 69 % | 11 % |
| Kreis 5 | 43 % | 73 % | 14 % |
| Stadt | 30 % | 71 % | 20 % |

Das ist Nutzungshäufigkeit, kein Wegeanteil. Kreis 4 und 5 haben nach dieser Befragung eine höhere Velo-Nutzung als der Stadtschnitt.

**Pendeln und Arbeitsplätze**: Die letzten Quartiers-Beschäftigtendaten stammen aus 2008 (Kreis 4: 28 005 Beschäftigte, 1.02 pro Einwohner:in 2008; Kreis 5: 32 640, 2.57 pro Einwohner:in). Das ist veraltet, aber für die Lage (Arbeitsgebiete in Kreis 5) brauchbar. Für 2020 gilt laut Web-Suche: rund 320 000 Personen arbeiten in der Stadt Zürich, 62 % davon pendeln ein.

**Wochenaufenthalter:innen 2025**: Kreis 4 1 132, Kreis 5 458, Stadt 13 650.

**Tourismus**: Stadt Zürich 4 179 908 Logiernächte 2025 (rund 11 450 pro Tag). Monatsverteilung: Jun-Aug zusammen rund 28 %, Jan-Feb rund 12 %. Anteil Kreis 4/5 ist nicht belegt.

**Nachtleben**: Keine belegbaren Besucherzahlen für die Langstrasse gefunden (Web-Suche). Ersatzweise Velozählungen in Kreis 4 (8 Zähler, 2025): Freitag/Samstag liegen ab 22 Uhr klar über Montag-Donnerstag (22-23 Uhr: 3.5 % gegenüber 1.8 % der Tageswerte).

## Tagesgang (Annahme)

`day_night_factor_by_hour` in der JSON ist eine ANNAHME. Basis: Velozähler in Kreis 4, gewichtet 5/7 Mo-Do und 2/7 Fr/Sa, auf Maximum 1 normiert. Einschränkungen:
- Velos sind kein Mass für Passanten. Nachts fehlen Velos, daher ist der Nachtwert unterschätzt.
- Die Zähler sind nicht über ihren Namen einer Strasse zugeordnet (Standortliste nicht abrufbar, Geodatenportal liefert HTML). Ob die Zähler an der Langstrasse liegen, ist ungeprüft.
- Stundenwerte 0-5 Uhr sind sehr niedrig (0.02-0.07), 17-18 Uhr ist der Peak (1.0 bzw. 0.98).

## Offene Lücken
1. Modalsplit der Wege für Stadt/Kreise: Stadt Zürich oder Kanton (Mikrozensus Mobilität) anfragen.
2. Beschäftigte nach Quartier aktuell: Die aktuelle Erhebung scheint nicht als OGD-Quartierdatensatz zu existieren.
3. Nachtleben-Besucher:innen: keine Quelle gefunden. Vorschlag: Polizei- oder Lärmdaten, Gastwirtschaftsbetriebe (`sid_wipo_gastwirtschaftsbetriebe_od1111`) als Proxy für Bar-Dichte.
4. Standortnamen der Fuss-/Velozähler: Standortdatensatz nicht abrufbar (Geodatenportal liefert HTML). Ein Versuch über den Browser oder das WFS mit anderer URL könnte helfen.
5. Anteil Touristen an Kreis 4: nicht belegt.
