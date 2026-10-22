# Brücken-/Rampenfehler: Pfingstweid-Rampe (Hardbrücke), Kalkbreite, Sweep (Agent bridgeramp, 2026-10-22)

## 1. Pfingstweidstrasse-Rampe Hardbrücke (gefixt)
- Ort: Rampe 3.5 m (OSM 602621647/527811419) von der Pfingstweidstrasse (182,352) auf die Hardbrücke (62,187), daneben das Tram-Gleispaar (401789575, 401789585…) und ein Fussweg. Kacheln 0_1, 1_1 (0_0).
- Ursache: Die Tramstreifen parallel zur Rampe hatten zwei falsche Höhen. (a) Regelhöhe hob sie 3 m über die parallele Rampe (Kreuzungsregel), (b) `_lidar_decks` setzte sie auf die LiDAR-Oberfläche des Hardbrücken-Hauptdecks, das direkt darüber verläuft (-0.4 statt -7.3 m). Danach tauchte das Tram bei (150,325) mit 28 % von -0.3 auf -5.3 ab: breiter grauer Keil (Deckseitenflächen dreier Streifen im Abstand 4-7 m), geknickte Rampe, Geländer auf der Platte.
- Fix: `bridges._follow_parallel` (nach `_lidar_decks`): Tram (<= 4.6 m) / Fussweg (<= 3.0 m) parallel (< 25°) zu einem Strassendeck übernehmen die Höhe des **nächsten** parallelen Strassendecks, wenn die eigene um > 1.5 m abweicht; der Überstand über Grund klingt hinter dem letzten gefolgten Vertex über 25 m aus. 6 Ketten betroffen (Log `logs/bridgeramp_build4.log`).
- Vorher/Nachher: `preview/bridgeramp_pfingstweid.jpg` (oben vorher PC, Mitte nachher PC, unten nachher Handy). Audit: stack 0_1 19 → 15, steep/kink 0_1 Tram 2.77 → weg.
- Bäume: Baumkataster-Bäume durchstossen keine Decks (`yards.drop_deck_trees` + `audit_trees_deck.py` = 0 Konflikte); es wurden keine Bäume gelöscht.
- Kacheln gebaut: 0_1, 1_1, 0_0 (Builds 1, 2, 4), -10_4, -10_5 (Build 2; dort Ketten unverändert), 1_-6 (Build 3). Logs `logs/bridgeramp_build{1,2,3,4}.log`.
- bridges_ride (alle 97 Fahrten, nach Fix): 49 mit Problemen, stuck 14, fell 2, crashes 6 = gleich wie qa21 (49/97, stuck 14). Hardbrücke-Route allein vor/nach identisch (7/7, Sprünge nur im Norden bei (486,810)).

## 2. Kalkbreite (355,-1094) (teilweise)
- Das Deck ist `Kalkbreitestrasse` (9.6 m, (301,-1130) → (263,-1155), z 1.06–1.47), es quert einen 30 m breiten, 6–7 m tiefen Gleiseinschnitt (terrain_cut/DEM). Der Einschnitt ist breiter als das Deck, daneben liegen Fahrbahn/Geländer am Grubenboden; das Deck endet im Nordosten an einer schrägen Kante gegen grau gepflasterten Boden (dunkle Deck-Asphaltfarbe gegen Boden: sichtbare Naht), Südwestende 1.6 m über Grund (openend 6.7).
- Gefunden und gefixt: Strassenlampe (284.5,-1141) stand auf dem Grubenboden und stach 14 m hoch durch das Deck. Neu `bridges.drop_deck_props` (Hook `build_testarea` nach `meta`): Möblierung (Lampen, Abfall, Bänke, Schilder, Hydranten, Poller, Velos), deren Fuss unter dem Deck steht und deren Oberkante die Deckunterseite erreicht, oder die in einem bis zum Boden massiven Deck steckt, wird entfernt (Kachel 1_-6: 1 Stück; stadtweit nach Komplett-Build, Audit meldet 18 «buried», meist Verkehrsschilder).
- Nicht reproduziert: «Strauch auf dem Deck» (laut Bodenaudit cityprops-Bäume/Rasen 0.8 m über dem Deck, an dieser Kachel in den `yards`/`trees`-Zeilen keine Treffer im Deckstreifen ausser Fussweg-Bäume bei (308,-1150) z 1.5 neben dem Fussdeck). Verzogene Markierungen und Randstein-Waisen: Fahrbahnpolygon/Linien kommen aus `streets`/`markings`, nicht aus dem Deck; Ticket K-1.

## 3. Sweep (`pipeline/audit_decks.py`, Liste `research/bridges/ramp_fix_audit.tsv`)
`.venv/bin/python pipeline/audit_decks.py --tsv out.tsv --top 30`. Prüfungen: steep, kink, openend, stack (parallele Decks mit 1.2–8 m Höhenunterschied), buried (Möblierung im Deck), pierce (Bäume). Stand nach Fix: 326 Befunde (stack 15, kink 86, openend 48, steep 159, buried 18, pierce 0); vor Fix 363. Gefixt: Tram-Rampen (6 Ketten), hohe Möblierung durch Decks (Regel, wirkt im Komplett-Build). Rest unten, nach Sichtbarkeit (Breite x Länge + 3 bei Kamerapunkt < 70 m).

| # | Ort (x,y) | Kachel | Befund | Vermutung |
|---|---|---|---|---|
| T1 | (49,122) / (24,130) Hardbrücke Fussweg | 0_0 | Fusssteg springt 3.8 m senkrecht (1.2 → -2.6) | Treppe (`highway=steps` ausgeschlossen) zwischen Brücke und Boden; Fussweg-Ende braucht Treppenrampe |
| T2 | (509,871), (479,822) Hardbrücke Nord / Wipkingerbrücke | 2_4, 2_3 | Tram/Strasse 8 m übereinander (Stack), openend (583,999) 1.1 m | gleiche Klasse wie Pfingstweid; nach Komplett-Build erneut prüfen (Ketten (470,773), (539,917) ändern sich) |
| T3 | (-1810,977) Europabrücke Fussweg | -10_4 | Fussweg 7 m neben Fahrbahndeck; (-1801,1103) Bändlistrasse 5.6 m offenes Ende, (-1829,1003) kink 1.35 | Wege unter der Brücke bzw. Treppen; bewusst nicht von `_follow_parallel` erfasst (Fussweg > 3 m) |
| T4 | (-64,-149), (-55,-167), (-148,-177) Hardbrücke West/Tram | -1_-1 | Fusswegknicke 0.2–0.4, Tram-Ende 0.6 m über Grund | LiDAR/Regel-Mischung am Kettenende |
| T5 | (1113,-1435) Stauffacherbrücke Fussweg, (1115,-1428) 4.7 m offen | 5_-8 | Fusssteg-Stack dz 4.6, offenes Ende | Treppe zur Sihl |
| T6 | (336,114) Lettenviadukt, (969,480) | 1_0, 4_2 | kink 1.09 / 0.12 (Bahn) | Bahndecks nicht von LiDAR korrigiert |
| T7 | (240,-603) Fussweg | 1_-4 | 2.9 m offenes Ende | Treppe |
| T8 | (1322,-632) Freischützgasse, (1622,66) Gallusstrasse, (-548,1236), (1550,124), Park (1504,175) | | Stufen > 1.5 m zwischen Fahrbahnzellen an Brücken/Rampen (Boden-Audit T-G3) | Bodenhöhe vs. Deck, nicht bearbeitet |
| K-1 | Kalkbreite (263..301,-1155..-1130) | 1_-6 | Deck breit schmaler als Einschnitt, Naht Deck/Boden, schräge Kante, Markierungen verzogen, Randstein-Waisen | terrain_cut breiter als Deckfootprint; Fahrbahnpolygon-Abzug endet im Nichts (`road_height.clip_ways`); nächster Schritt: terrain_cut auf Deckbreite + 2 m begrenzen oder Strassenpolygon bis Deckkante führen |
| Z2b-2 | Heinrichstr./Limmatstr. Viadukt (398,229)–(759,474) | 2_1, 3_1, 3_2 | Stahlfachwerk-Bahnbrücken nur graue Platten | Kette `rail` 4.6 m breit, 5.5–5.8 m über Grund; `bridges.py` kennt keinen Brückentyp (`bridge:structure=truss` wird nicht gelesen), Fachwerk/Bogen sind Modellierungsaufgabe (Landmark), kein einfacher Fix |
| Z2c-2 | Limmatufer-Viadukt (1220,200) | | dunkles Betondeck statt Steinbogen | nur Ticket (wie Z2b-2) |

## 4. Noch neu zu bauen (wegen der Codeänderungen)
Komplett-Build ohnehin (Möblierungsfilter wirkt auf alle Kacheln mit Decks). Mindestens wegen `_follow_parallel`: -1_-1 (Hardbrücke West, Ketten (-125,-138), (-74,-58)), -1_-2 (Fussweg (-24,-219)), 2_3 und 2_4 (Tram (470,773), (539,917)), 8_-9 (Tram/Fusswege (1638,-1654), (1628,-1652)), 7_-9 (Fussweg (1543,-1744)). Bereits neu: 0_0, 0_1, 1_1, 1_-6, -10_4, -10_5.

## 5. Entwurf DECISIONS-Eintrag
**#75 – Tram-/Fussstreifen folgen der Rampe daneben, Möblierung nicht durch Decks.** `bridges._follow_parallel`: Tram (<= 4.6 m) bzw. Fussweg (<= 3 m) parallel neben einem Strassendeck übernehmen bei > 1.5 m Abweichung die Höhe des nächsten parallelen Strassendecks (LiDAR sieht bei übereinanderliegenden Decks nur die oberste Fläche: Hardbrücke-Rampe bekam die Höhe des Hauptdecks, Tram tauchte mit 28 % ab). `bridges.drop_deck_props` entfernt Möblierung, die unter einem Deck steht und es durchstösst oder in einem massiven Deck steckt (Kalkbreite). Werkzeug `pipeline/audit_decks.py`.
