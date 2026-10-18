# Strassen Runde 2 (2026-10-18): Rampen, Wasser, Gleise, traffic_legal, Bahnhofplatz

Bilder: `preview/roads_fix.jpg` (oben je Paar vorher/nachher: Seebahnstr./Kanzlei, Hardplatz, Badenerstr.-Brücke, Tramrampe; unten Bahnhofplatz).

## 1 Rampen Badenerstrasse/Seebahnstrasse
Ursache (zwei Teile, beide in der Pipeline):
1. `road_height.apply` blendete das geglättete Profil in alle Zellen im Streifen um jede Strasse. Neben Einschnitten (Bahngraben unter der Badenerstrasse-Brücke, Kaimauern, Dämme) füllte oder rasierte das die Zellen um bis zu +36.8 / -34.6 m. Der Graben unter der Brücke bei (200, -1005) war von -6.4 auf -3.0 m aufgefüllt.
2. `bridges.bridge_ways` misst die Lichte (Tram 6.5 m, Strasse 7 m) ab `H` (geglättet). Mit dem aufgefüllten Graben hob es das Tram-/Strassendeck auf 6.4 m über das Strassenniveau, mit 6-7 % Rampen auf beiden Seiten (Kette 1.2 km lang, `max_el` 10.4 m). Das waren die «weirden Rampen».

Fix:
- `road_height.py`: pro Zelle `MAX_FILL = 1.2 m` hoch, `MAX_SHAVE = 2.0 m` runter.
- `bridges.py`: neuer Parameter `H_raw`; liegt die Glättung > 1 m über dem Rohgelände, zählt die Lichte ab dem Rohgelände. Der Ketten-Cache `deck_chains.json` wird nur noch vom echten Build geschrieben (`H_raw` gesetzt), nicht mehr von Audits.
- `build_testarea.py` (# roads2): `H_raw` = Kopie vor der Glättung.

Zahlen (Gesamtgebiet, `road_smooth_audit.py`, `logs/roads2_audit.log`):

| | vorher | nachher |
|---|---|---|
| Zellen um > 1.2 m gehoben | 5556 | 0 (267 Rundung bei 1.2) |
| Zellen um > 2 m gesenkt | 2579 | 0 |
| grösste Änderung hoch / runter | +36.8 / -34.6 m | +1.2 / -2.0 m |
| Audit post (Steigung/Knick/Quer/Kachel/Trottoir) | 10/12/65/1/271 laut älterem Lauf: 352 total (4.31/km) | 359 total (4.08/km, 87.9 km) |
| Brücken-Ketten mit `max_el` > 1 m tiefer | | 30 (6 davon > 3 m, u. a. Tram Badenerstr. 10.4 → 6.7 m, Lichte jetzt ab Grabensohle, Deck auf Strassenniveau) |

Der Audit misst Steigung/Knick/Quer, nicht Deckhöhen; die Deck-Prüfung steht in `research/roads_round2.md` (dieses Skript: Vergleich alte/neue Ketten, Scratch, nicht im Repo).
Offen: Testkacheln zeigen die Brücke flach (Strasse auf Terrainniveau, Graben darunter). Ob das Deck dort noch Brückenwände/Pfeiler bekommen soll, ist Geschmack; Kaimauer-Stufen neben Strassen bleiben nun als Gelände stehen.

## 2a Autos im Wasser
Kein Auto-/Velo-Graph-Kantenpunkt liegt im offenen Wasser (AV-Wasser + OSM-Wasser, 61 ha): 17 Auto-Kanten kreuzen Wasser, alle mit Deckhöhe `z`. Parkautos: 0 im Wasser. Wahrscheinlichste Ursachen der Meldung: (1) alte Kacheln aus dem Browser-Cache gemischt mit neuen Daten (HANDOFF Punkt 1), (2) Graph und Decks aus verschiedenen Kettenständen: `roads.json` bekam `z` aus einem Cache, den Audits mit ungeglätteter `H` überschrieben hatten. 3 Kanten (1376, -1516), (1360, -1537), (1600, -1691) hatten `z`, aber kein Deck in den Kacheln (Stand Build 10). Gegenmassnahmen: Cache nur noch vom Build (s. o.); `pipeline/road_exclude.py` + roadgraph entfernt jede Kante mit ≥ 2 m in offenem Wasser/auf Boden-Gleis ohne Deck (aktuell 0 Kanten betroffen, Sicherung). Kacheln: Objekte (Velos, Ständer, Roller, Mopeds, Mülleimer, Bänke, Arbeiter, Parkautos) in Wasser/Bahnland ohne Deck werden beim Kachelbau entfernt (Trockenlauf über alle Kacheln: 523 Objekte, 0 danach; in den 6 Testkacheln schon aktiv).
Nach dem nächsten Komplett-Build `roadgraph.py` + `transit.py` neu laufen lassen (Deckhöhen aus dem frischen Cache; ist für diesen Stand schon passiert).

## 2b Gleise
`audit_rail.py` meldete Auto-/Velo-Kanten auf «Bahnfläche» (45 / 65). Befund: Falsch-Positive. Die AV-Klasse «Bahngebiet» deckt auch Strassen unter Viadukten (Kante 1096 = Hardturmstrasse, 858 m; 1090 = Aargauerstrasse) und Industrie-Anschlussgleise in der Strasse (Hardstrasse, Gerstenstrasse, Naphtastrasse). Der Audit prüft Kanten jetzt gegen echte Boden-Gleisachsen (rail/light_rail/narrow_gauge ohne bridge/tunnel/service/industrial, 2.3 m) und Gewässer abzüglich Decks: Auto 45 → 1 (Limmat-Kai (1597, -481), 3 m), Velo 65 → 0. `rail_excl.json` hat jetzt `allow`-Boxen (Langstrassen-Unterführung unter dem Gleis).
Objekte auf Bahnfläche (Velos 186, Ständer 122, Roller 84, Arbeiter 17 ...): Filter `road_exclude.filter_meta` im Kachelbau (railzone.json + Wasser minus alle Decks). Wirkt erst nach Kachelbau (Audit-Zahlen für Objekte ändern sich erst nach dem nächsten Komplett-Build).

## 2c traffic_legal
Ursache: Fahrspuren folgen der OSM-Achse (+ AV-Versatz), die AV-Fahrbahn weicht an Kreuzungsecken, Inseln und Plätzen ab. `road_exclude.snap_to_roads` zieht die Spurpunkte in die um 0.8 m verkleinerte Fahrbahn (6402 Punkte verschoben, 10332 Zwischenpunkte). Ergebnis `node web/tests/traffic_legal.mjs`: Autos 0.32 % (Escher-Wyss-Platz 1.58 %) → **0.01 %** (12/99378), Parkautos 0.17 %, Busse 0.00 %.

## 2d Bahnhofplatz
Grünfläche = Boden unter Gebäuden, die ein Landmark ausblendet (HB, Habis Royal): Rest-Hof > 60 m² wurde Rasen. Fix in `_ground_base`: Hof-Rest innerhalb AV-«Gebäude» wird gepflastert (`S["av_bld"]`). Rest: ein kleiner AV-Grünstreifen am Tramoval bleibt (laut AV).

## Tests
`tsc --noEmit` sauber; `traffic_legal.mjs` OK; `drive.mjs`: ein FAIL «touch: braked to -5.9 m/s» (Fahrzeugphysik, nicht Teil dieser Änderung); `audit_rail.py` neu; Testkacheln 0_-6, 1_-6, 0_-5, 1_-4, 0_-4, 8_-4 neu gebaut.
Neues Testskript `web/tests/roads_obl.mjs` (Schrägansichten an Punkten).
