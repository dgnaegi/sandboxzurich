# Verkehr: Annahmen und Grenzen

## Daten (`pipeline/roadgraph.py` -> `web/public/data/roads.json`)
- Quelle OSM (`data/raw/osm/kreise.json`), Gebiet = Testgebiet + 150 m. Fahrbar: primary, secondary, tertiary, residential, unclassified, living_street, *_link. `service` fehlt bewusst (Hinterhöfe, Parkplätze). Tunnel, private Zufahrten und `motor_vehicle=no` fehlen.
- Kanten werden an Knoten gesplittet, die in mindestens zwei Ways vorkommen. Ergebnis: ca. 458 Auto-Kanten (27 km), 473 Velo-Kanten (27 km), 236 Knoten, 97 KB.
- Rechtsverkehr: Zweirichtungsstrassen = zwei Kanten, je w/4 rechts der Achse; Einbahn mittig (auf der Achse). Breite wie `streets.py` (`width`/`lanes`/WIDTH).
- Tempo: Haupt 50, Quartier 30, Begegnungszone 20, `maxspeed` überschreibt (20..50).
- Velo: `highway=cycleway` (Mitte, beide Richtungen ausser oneway) plus rechter Rand jeder Strasse (w/2 - 0.8). primary/secondary ohne cycleway-Tag werden für Velos ausgelassen.
- Einbahn rückwärts (`oneway=-1`) und Kreisel (`junction=roundabout`) sind berücksichtigt.

## Simulation (`web/src/world/traffic.ts`)
- Autos: Folgemodell nach Krauss (sicherer Abstand, B=4.5, Reaktion 0.7 s), Abbremsen vor Kurven (Rechts 4 m/s, Links 5 m/s), Zufallswahl der Weiterfahrt (geradeaus bevorzugt, kein U-Turn ausser Sackgasse).
- Vortritt: Hauptstrasse vor Nebenstrasse, sonst Rechtsvortritt; Linksabbieger weicht dem Gegenverkehr; Einmündende Spuren: näheres Auto zuerst. Wer 5 s steht, fährt trotzdem (verhindert Deadlocks). Die Kreuzung wird nicht betreten, wenn die Ausfahrt belegt ist.
- `avoid`-Kreise (Spieler, Fussgänger) vor dem Auto in Fahrtrichtung -> Bremsen bis Stillstand.
- Spawn im Ring 120–250 m um die Spielerin, Despawn > 280 m. Dichte per `maxCars`/`maxBikes` (Handy 20/8, PC 45/20).
- Messung (Node-Simulation 3 min, 45 Autos + 20 Velos, ohne Rendering): stabil, volle Dichte; ca. 1.5 % der Frames mit zwei Autos < 2 m (Spawn/Kreuzungsränder).
- Rendering: 1 InstancedMesh pro Autotyp (Kapazität 64), Velos = 3 Meshes (Körper + zwei Beine, Beine pedalieren). Max. ca. 10 Draw Calls.

## Grenzen
- Keine Ampeln, Tramhaltestellen, Fussgängerstreifen-Vortritt (Fussgänger nur über `avoid`).
- Autos sehen Velos nicht, Velos weichen Autos nicht aus (nur Spielerin/`avoid`). Velos haben keine Vortrittsregel.
- Keine Spurwechsel/Überholen, keine Parkplatzsuche; parkierte Autos (`cityprops`) sind unabhängig und können mit fahrenden überlappen, wenn eine Spur belegt ist.
- Fahrbahnhöhe = `ground(x,y) - 0.12`, keine Neigung (Nick) der Autos.
- Offset-Sprung an Kreuzungen wird über 0.5 s geglättet; Kurven folgen der OSM-Polylinie (eckig bei grober Geometrie).
- Netz endet 150 m ausserhalb des Testgebiets: am Rand sind weniger Autos sichtbar.
- Sackgassen am Datenrand: Autos fahren dort bis zum Ende und verschwinden.
