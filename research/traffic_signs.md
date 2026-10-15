# Verkehrszeichen und Lichtsignale (R4)

Quelle: OSM (ODbL) `data/raw/osm/kreise.json`; Signalformen nach SSV (Signalisationsverordnung, SR 741.21), selbst gezeichnet (keine Bilder kopiert).
OSM enthaelt im Testgebiet praktisch keine `traffic_sign=*`-Tags, daher werden Schilder aus Strassen-Attributen abgeleitet.

| Code | SSV | Ableitung aus OSM |
|---|---|---|
| zone30 / zone30end | 2.59.1 / 2.59.2 | maxspeed=30 bzw. maxspeed:type=CH:zone30 gegen Nachbarstrasse mit anderem Tempo, Wegenden an Kreuzungen |
| speed50 | 2.30 | maxspeed=50 auf primary/secondary/tertiary an Tempowechsel |
| einbahn | 4.08 | oneway=yes, Wegbeginn an Kreuzung |
| einfahrt_verboten | 2.02 | oneway=yes, Wegende an Kreuzung (Gegenseite) |
| fahrverbot | 2.01 | motor_vehicle=no / access=no (nicht private) |
| radweg / fussweg | 2.60 / 2.61 | highway=cycleway (bicycle designated) / benannter highway=footway ohne Velo |
| fussgaenger | 4.11 | highway=crossing mit crossing=zebra/marked/uncontrolled |
| vortritt / stop | 3.02 / 3.01 | highway=give_way / stop (direction beachtet) |
| parkieren / blauzone | 4.17 | parking:lane=parallel.., parking:zone / parking:condition=disc |
| halteverbot | 2.50 | parking:both/parking:lane:both=no auf Hauptstrassen |
| sackgasse | 4.? | Wohnstrasse, andere Seite Sackgasse (degree 1), >40 m |

Lichtsignale: `highway=traffic_signals` (Knoten, je Zufahrtsarm Autoampel, Velo-Ampel wenn cycleway lane/track, Fussgaengerampel ab 3 Armen) und `crossing=traffic_signals` (Fussgaengerampeln beidseitig). Phase: Zyklus 40 s, Achse 0 gruen 16 s, Achse 1 um 20 s versetzt; Fussgaenger gruen, wenn Autos auf ihrer Gehrichtung-Achse gruen haben (Querverkehr rot).
Testgebiet (x 600..1200, y -1000..-400): 82 Schilder, 12 Signalobjekte (OSM-Dichte gering). Lauf: `cd pipeline && python3 traffic_signs.py`.
