# Grünzeug auf der Fahrbahn (T-G1, T-G2) – Protokoll roadgreen

## T-G1 trees_on_road 62 + lawn_on_road 1
Ursache: grösstenteils Audit-Artefakt, kein Datenfehler. `cityprops.lane_fix` setzt Bäume auf Fahrbahnrand + 0.4 m; das 1-m-Verkehrsraster (`traffic_zones.png`) rundet diese Stämme auf «Fahrbahn». Gegen das Fahrbahnpolygon (`data/cache/props_road_zone.wkb`) liegen 59 von 63 ausserhalb (0.0 bis 1.0 m vom Rand), alle echte Katasterbäume bzw. nDSM-Bäume, nicht verschoben, nicht gelöscht.
Ausreisser:
- Solisweg (-1571.7, 357.3): einziger Stamm, den die Zone (Strassen minus Plätze/Decks) um einen Span noch enthält. Neu: `props_road._trees` (aus `fix_meta`) verschiebt solche Stämme bis 2 m an den Rand + 0.4 m, löscht nie.
- Engelstrasse (469.3,-958.0), (474.2,-951.6), (474.0,-959.5): 10 bis 18 m von der Zone entfernt, also in Fuss-/Begegnungszone bzw. Platz; Raster zählt das als Strasse. Bleiben (echte Bäume).
- Lawn (615.9,-1092.5) Badenerstrasse: Mittelpunkt 0.6 m neben der Zone, ausserhalb. Bleibt.
Audit angepasst: Bäume/Rasen werden gegen das Polygon (Puffer -0.15 m) geprüft. Neuer Stand Trockenlauf: trees_on_road 62 -> 0, lawn_on_road 1 -> 0.

## T-G2 shrub_edge_road 125
Ursache: AV-Grünpolygon und OSM-Fahrbahn überlappen leicht; Büsche (yards.bushes) mit Radius bis 2 m reichen über den Rand.
Fix: `props_road._bush_edge` (aus `_yard_greens`): Busch zuerst bis max(0.6 r, 0.8 m) vom Rand weg verschoben, dann Radius auf (Abstand - 0.3 m) gekürzt (min 0.25 m). Löscht nichts; Mittelpunkt auf Fahrbahn (93) bleibt wie vorher gestrichen.
Trockenlauf (alle 307 Kacheln, Polygon-Abstand): 768 Büsche mit Blattrand < 0.3 m vom Polygon (Audit-Raster fand nur 125) -> 1 bleibt knapp (Abstand 0.35, r 0.24, bewusst belassen). 93 mit Mittelpunkt auf Fahrbahn werden gestrichen (separater Fix).

## Geänderte Dateien
`pipeline/props_road.py` (`_trees`, `_bush_edge`, Aufruf in `fix_meta`/`_yard_greens`), `pipeline/audit_ground_city.py` (Polygon-Test, Dry-run-Zeile). `cityprops.py`, `yards.py` unverändert.

## Neu zu bauen
Wirkt nur im nächsten Build (props_road.fix_meta läuft pro Kachel). Betroffen: Kacheln mit Büschen am Rand, Solisweg-Kachel. Praktisch Komplett-Build. Danach `audit_ground_city.py`: shrub_on_road/edge sollten ~0 werden.
