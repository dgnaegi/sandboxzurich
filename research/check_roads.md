# Check Fahrbahn / Glättung / Brücken (16.10., nach Absturz)

Gemeinsam: tsc --noEmit sauber. Im Build-Log (build_full9) nur ein Fehlertyp, siehe "Bug".

## BUG (gefixt, wirkt erst im nächsten Build)
`TILE FAILED t_-15..-12_*` (17+ Kacheln, AttributeError 'NoneType'.buffer in build_testarea._ground_base Z.168):
`S["roads"].boundary` ist None, wenn S["roads"] eine GeometryCollection ist (Mischtypen nach difference/union_all
mit EXR, Wasser oder parking_bays). Fix: nach `S["roads"] = union_all([... parking_bays ...])` auf Polygon/MultiPolygon
filtern (build_testarea.py, direkt nach dieser Zeile). Der laufende Build liefert diese Kacheln NICHT (Backdrop-Kacheln am Westrand
fehlen/alt) -> nach Build 9 betroffene Kacheln neu bauen. Ursache der GC nicht sicher (Verdacht: carriageway/EXR); Fix macht es robust.

## 1 Fahrbahn-Abgleich (carriageway.py, streets.py, roadgraph.py)
Fertig: carriageway.py (AV-kalibrierte Breiten, Default "av", SBZ_CARRIAGEWAY=osm = alt), in streets.py Z.142 eingehängt,
Audit-Skript + research/carriageway_audit.md (IoU 0.72 -> 0.91). Halb: Orthofoto-Kontrolle, cmp*.py sind reine Hilfsskripte.
Kein toter Pfad im Build gefunden. Nächster Schritt: nach Build die GC-Ursache prüfen, Screenshots (web/tests/carriageway_shots.sh).

## 2 Strassenglättung (road_height.py, terrain_cuts.py)
Fertig: road_height-Änderung (ground_exclusion/clip_ways) im Build aktiv, road_smooth_audit.py + research/road_smooth.md (Top-30 Problemstellen
Seebahnstrasse/Bullingerstrasse/Norastrasse). Fehlt: pipeline/overrides/road_height.json existiert NICHT (kein Hook, der sie braucht -> kein Fehler).
Nächster Schritt: Top-Stellen nach Build erneut auditieren, ggf. Override anlegen.

## 3 Brücken befahrbar (bridge_routes.py, decktrack.py, bridges.ts)
Fertig: bridges.save_chains/load_chains (data/build/deck_chains.json, frisch 15:50), DeckTrack liest den Cache (roadgraph/transit/rail_net),
logs/bridge_routes.json vorhanden, bridges_ride.mjs vorhanden. Risiko: Cache nur bei H_given geschrieben; ist er veraltet/fehlt, fällt
DeckTrack auf alte Pfade zurück (kein Crash). Halb: Ride-Test nie gegen neuen Build gelaufen (braucht Browser). Nächster Schritt: nach Build
`node web/tests/bridges_ride.mjs` laufen lassen.

## Änderungen von mir
Nur pipeline/build_testarea.py (GeometryCollection-Filter, +2 Zeilen). py_compile wurde vom Classifier blockiert -> Syntax der Module nicht compiliert geprüft.
