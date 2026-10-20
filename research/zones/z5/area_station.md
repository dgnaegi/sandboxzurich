# Zone 5, Gebiet Bahnhof Altstetten (Agent z5a, 2026-10-20)

Bögen: `preview/z5a_before_1/2.jpg` (Foto | Spiel vorher), `preview/z5a_after_1.jpg` (nachher, **ohne Kachel-Build**: die neuen Landmarks überdecken die alten
Häuser erst nach dem nächsten Build, weil `hide` beim Kachelbau wirkt), Fotos `preview/z5a_ph_*.jpg`, Karten `preview/z5a_map_*.jpg`, Einzelmodelle `preview/z5a_lm_sheet1-3.jpg`.

## Hauptbefund: Kamerapunkte und Blickrichtung stimmen nicht (Lehre 11 bestätigt)
Mapillary-Heading liegt hier bis 90° daneben (Fotos zeigen Altstetterstrasse nach WEST, Heading sagt 187–190°). Gegenprobe mit `yaw`-Variation im Spiel:
| Punkt | zones.json heute | Vorschlag (Ticket Z5a-1) |
|---|---|---|
| Vorplatz | (-2179, 748), kein yaw | (-2183, 764), yaw 4.6 (Blick WSW, Aktiv Fitness/ABZ-Bau wie Foto Mapillary #4/#0) |
| Perron | (-2072, 774), kein yaw | liegt auf dem Bahnhofvorplatz/Taxi, nicht am Perron: Foto-Pose (-2040, 747), yaw 6.1 (Blick N auf Aufnahmegebäude, Mapillary 2019 #6) |
| Vulkanplatz | (-1988, 892), kein yaw | Foto-Pose (-1972, 925), yaw 4.9 (Blick WNW auf Backsteinhalle + Bäume) |
| Badenerstrasse West | (-1945, 463) | Foto-Pose (-1934, 441), yaw 5.15 (Panoramax 2025 #2); Position ±20 m unsicher |

## Protokoll je Kamerapunkt
**Bahnhof Altstetten Vorplatz** (Fotos Mapillary 2025 #0/#4/#5, 2016 #1/#9, Commons Altstetterplatz, Panoramax #19). Note vorher 2 (Spiel zeigt wegen Fehl-yaw eine leere Platzfläche), geschätzt nachher 3.5.
- Befund: (1) Betonvordächer des Busbahnhofs fehlen komplett (OSM `building=roof` + `amenity=shelter`, 32×4.6 m und 2× 13×2.5 m); (2) Aktiv-Fitness-/Migros-Bau (swissB3D A35B08F6, 8 Geschosse) beige mit bunten Paneelen statt hellgrauem Betonbau mit Fensterbändern; (3) ABZ-Backsteinbau (2B880E23, 5 Geschosse, Stahlgalerien) nur generisch; (4) Boden Platz asphaltbraun statt hellgraue Betonplatten; (5) weisse Schleifen-Linien auf der Fahrbahn (kein Foto-Beleg).
- Fix: `pipeline/landmarks/z5a_canopy.py` (Betondach mit Dachbegrünung, Pfeiler, Vitrinenwand, Bank), `z5a_houses.py` (migros, abz), `pipeline/overrides/places_detail_z5a.json` (SWISSIMAGE-Boden «concrete» im Radius 48 m um den Platz; wirkt erst im Kachelbau).
- Ticket Z5a-2: weisse Schleifen/Inseln auf der Fahrbahn am Platz (Generator der Verkehrsinseln/Busbuchten prüfen); Tramschienen der Altstetterstrasse im Spiel kaum sichtbar.
**Bahnhof Altstetten Perron** (Mapillary 2015 #1/#7, 2019 #2–#6, Commons 2024 Perron/Balkone). Vorher 2.5, geschätzt nachher 3.5.
- Befund: Aufnahmegebäude (swissB3D 3A9B8AC4, 7.9 m, ~140 m lang) im Spiel hoch und blau verglast mit Fantasie-Türen; Original eingeschossig, weisse Betonscheibe als Dach, dunkel verglaste Ladenzeile. Helvetia-Glasbau gegenüber stimmt grob. Parkplatz ohne Taxis/Autos.
- Fix: `pipeline/landmarks/z5a_station.py` (Fassade 5.9 m, weisse Dachscheibe, dunkle Verglasung). Der Eingang der Riegel-Ladenzeile (Caffè Spettacolo, AMAVITA-Schild) bleibt aus dem bestehenden Landmark.
- Offen: Apotheke: Foto 2019 zeigt AMAVITA, OSM (neuer) BENU Apotheke am selben Ort (-2078,773); Spiel zeigt BENU. Nicht geändert.
**Vulkanplatz** (Mapillary 2024/25 #0–#9). Vorher 3 (bei richtiger Blickrichtung), geschätzt nachher 3 (unverändert).
- Befund: Bei Foto-Pose (-1972,925) yaw 4.9 stimmen Backsteinhalle mit Sprossenfenstern/Schild «Autospenglerei», Strassenbäume, Tram. Abweichung: Halle im Spiel ohne Holzstützen/Lamellen, Dach flacher. Hausbezug nur über Peilung von 3 Fotos (±15 m, Lehre 11) → kein Landmark gebaut (der erzeugte `z5a_hall` wurde wieder entfernt).
**Badenerstrasse West** (Panoramax 2024/25 #2/#3, nur 4 Fotos). Vorher 3, geschätzt nachher 3.
- Befund: Spiel zeigt eine Baustelle (Calanda-/Luggwegstrasse bis 12/2026, Baslerstrasse Betriebs-/Gestaltungskonzept 9/2026–2028 laut Stadt-OGD in `data/build/sites.json`): **echt, kein Fehler**, Fotos 2024/25 sind älter. Häuser: Foto zeigt links Altbauzeile (grau/rosa/ocker), rechts hellen Neubau mit Staffelgeschossen; Spiel generische Beige-Zeile. Kein sicherer Hausbezug (Pose ±20 m) → nur Ticket.

## Tickets
- Z5a-1 Kamerapunkte in `pipeline/overrides/zones.json` korrigieren (Tabelle oben; Datei gehört nicht diesem Agent).
- Z5a-2 Fahrbahnschleifen Altstetterplatz; Schienen sichtbar machen.
- Z5a-3 Nach dem nächsten Kachelbau Landmarks `z5a_*` im Spiel prüfen (Hide-Punkte, z-Fighting mit Generator-Haus), dann `places_detail_z5a` (Boden) beurteilen.
- Z5a-4 Badenerstrasse/Luggweg: Häuser nach Fotos, sobald zweite Fotoposition mit Adresse vorliegt.
- Z5a-5 Vordach-Modell: Glaswand/Vitrinen nur schematisch; Details (Moos-Kante hängend) fehlen.
Quellen der Fotos: Mapillary CC BY-SA 4.0 (ids in `research/zones/zone5_cam_photos.json`), Wikimedia Commons, Panoramax.
