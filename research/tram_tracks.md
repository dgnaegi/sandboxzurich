# Tramschienen (Agent D, 2026-10-19)

Meldung: «Tramschienen zum Teil weird, mit Maeuerchen links und rechts und etwas abgehoben.»

## Ursache (build_testarea._ground_base, vorher)
- Tramgleise sind kein eigenes Mesh, sondern `drape`-Streifen auf dem Boden (Schienen, Rillen, Gleisbett).
- Fahrbahn = `S["roads"]` (AV-Fahrbahn). Wo die AV die Tramspur als eigenen «Bahngebiet»-Streifen fuehrt (breiter als ~9 m, Luecke zwischen Fahrbahn und Tramstreifen, Streifen neben Platz), liegt das Gleis ausserhalb der Fahrbahn.
  Dort: Fahrbahn bei -12 cm, Gleisbett bei +1.5 cm, Schienen bei +7 cm. `curb_faces` setzt an jeder Fahrbahnkante eine 12-cm-Bordsteinwand: links und rechts vom Gleis = «Maeuerchen», Schienen 5.5-7 cm ueber dem Bett = «abgehoben» (19 cm ueber der Fahrbahn nebenan).
- Weitere Ursache der Hoehe: Schienen mit `cell=10` trianguliert, Asphalt mit 16 m -> unterschiedliche Interpolation.

## Fix (pipeline/tram_track.py, neu; Hooks in build_testarea.py nur Gleisteil)
- `merge_into_roads`: Gleise im Strassenraum gehoeren zur Fahrbahn (Gleisband 1.45 m, Luecken <= 2 m zur Fahrbahn und Plaetzchen unter dem Gleis geschlossen). Plaza wird um die neue Fahrbahn gekuerzt. Folge: keine Bordsteinwand mehr neben den Schienen.
- Rillenschiene buendig im Asphalt: Kopf +1.2 cm ueber Asphalt (vorher +1.2 cm, aber nur in der Fahrbahn), Rille dunkel, `cell=4` fuer saubere Hoehe.
- Eigenes Trassee (kein Strassenraum): Schotterbett nur dort (nicht auf Platzpflaster/Rasen), +1.2 cm ueber der Umgebung (im AV-Bahngebiet auf Schotterhoehe -8 cm +1.2), Schienenkopf +2.5 cm ueber dem Bett. Kein Randstein.
- Robuste Overlays (`_op`, 1-cm-Snap-Retry), Gleisgeometrie auf 5 mm gerundet.
- `SBZ_TRAM_OLD=1` baut die alte Geometrie (fuer Audit/Vorher-Bilder).

## Audit (pipeline/audit_tramtracks.py, Achsen alle 2 m, ganzes Spielgebiet + Randring, 72.9 km)
| Messwert | vorher | nachher |
|---|---|---|
| Schienenkopf > 3 cm ueber eigener Oberflaeche (m) | 22022 | 0 |
| ... unter (m) | 0 | 0 |
| Bordstein <= 1.2 m neben der Achse (m) | 8338 | 2086 |
| davon ausserhalb der Fahrbahn (m) | 2682 | 1396 |
| Kopf > 3 cm ueber der Fahrbahn nebenan (Gleis beim Strassenrand, m) | 4656 | 2122 |
| p95 Kopfhoehe ueber Oberflaeche (cm) | 5.5 | 2.5 |
Rest (~2.1 km): Gleise am Rand der Fahrbahn auf eigenem Trassee / Plattform-Rand, ein echter Randstein auf einer Seite; kein Hotspot (76 Zellen a 100 m verteilt). Pruefen: Haltestellen-Inseln (OSM-Plattformen), Tram auf Plaetzen.
Grenzen: Audit rechnet aus Geometrie + Hoehenmodell (Offsets der drape-Aufrufe), nicht aus dem fertigen GLB; Bruecken-Gleise sind ausgenommen (`bridges.exclusion`).

## Bilder
`preview/tram_tracks_cmp.jpg` (oben vorher, unten nachher: Helvetiaplatz/Langstrasse, Stauffacher, Albisriederplatz, Escher-Wyss/Hardstrasse), Skript `web/tests/tram_shots.mjs`. Testkacheln 3_-5, 4_-6, 5_-6, -3_-4, 1_2, 2_3 sind neu gebaut (nachher-Stand). Der Unterschied ist von Fussgaengerhoehe aus klein; er liegt in den Kanten/Hoehen (Audit-Zahlen).
