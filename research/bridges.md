# Brücken (pipeline/bridges.py, web/src/world/bridges.ts)

Quelle: OSM `data/raw/osm/kreise.json` (Ways mit bridge=yes/viaduct/..., ohne Gebäude), Gelände swissALTI3D (z_shift -3.06).

## Annahmen
- Art: road (Strassen), foot (Fuss-/Rad-/Pfad), tram, rail. Treppen und Perrons ausgenommen.
- Lichtraum über Hindernis (nur Ways mit kleinerem `layer`, ohne gemeinsame Knoten; Tunnel zählen nicht):
  Strassendeck über Bahn 7.0, Tram 6.0, Strasse 5.0, Fussweg 3.2, Gewässer 3.5. Fussdeck: Bahn 6.5, Strasse 5.0.
  Bahndeck über Strasse 5.5. OSM-Tags `clearance`/`bridge:clearance`/`height` überschreiben.
- Ohne erkanntes Hindernis (und Höhe < 1.2 m über Gelände) wird keine Brücke gebaut: bleibt Strasse am Boden.
- Höhenprofil: flachste Kurve über allen Anforderungen mit max. Steigung (Strasse 6 %, Fuss 8 %, Tram 7 %, Bahn 15 %),
  an den Enden auf Geländehöhe gezwungen. Reicht die Länge nicht, wird die Steigung bis 2x erhöht (Strasse max. 12 %).
- Rampen: Brücke wird über die fortsetzenden Nicht-Brücken-Ways verlängert (bis 260 m, nur über Knoten mit Grad 2).
  Teile mit < 0.12 m Höhe werden abgeschnitten. Angrenzende Brücken-Chains teilen die Höhe am gemeinsamen Knoten (4 Iterationen).
- Boden unter dem Deck: Boden-Wege (darunter) bleiben gezeichnet, nur Deck-Fussabdruck (> 0.3 m über Gelände) wird ausgeschlossen.
- Untersicht: Platte 0.6-1.1 m; bei < 3.5 m Höhe ohne Hindernis massive Stützwand bis zum Gelände. Pfeiler alle 22 m (Fuss 16 m),
  ab 2.2 m Höhe, nicht auf Hindernisse.
- Gelände-Untergrenze: Deck folgt dem Gelände nie steiler als die Steigungsgrenze (Brückenköpfe können leicht im Hang liegen).

## Ergebnis (Spielgebiet, 268 Brücken-Chains, ~730 Pfeiler, max. Deckhöhe 11.8 m über Gelände)
Hardbrücke (mehrere Chains, 5-8.4 m), Duttweilerbrücke (7.3 m, 12 % da kurz), Kornhausbrücke 8.1 m, Europabrücke,
Sihlhölzlibrücke 7 m, Stauffacherbrücke, Negrellisteg (11.8 m, 16 % Rampe: Länge 162 m reicht nicht), Wipkinger-/Rosengartenbrücke,
Tram- und Bahnviadukte.

## Bekannte Schwächen
- Wo OSM keinen Hindernis-Way unter der Brücke hat (z.B. Gleisfeld nur als Fläche), bleibt die Brücke flach/ungebaut.
- Fuss-Rampen an Negrellisteg/Hardbrücke ohne Treppen/Lifte; Rampensteigung dort > 6 %.
- Keine Geländer-Kollision, Spielerin kann seitlich vom Deck springen/fallen (BridgeIndex gibt dann null).
