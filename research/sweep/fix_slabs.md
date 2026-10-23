# Fix Slabs (Agent slabs, 2026-10-23)

Geaenderte Dateien: `pipeline/bridges.py` (neu `_split_flat`, `FLAT_SPLIT`), `web/src/world/bridges.ts` (Brüstung waechst mit Hoehe ueber Boden). Sonst nichts.
Gebaute Kacheln: 0_-4, 1_-4 (`logs/slabs_build1.log`), -1_-1 (`logs/slabs_build2.log`).

## #2 Seebahnstrasse (186,-666) - BEHOBEN
Ursache: kein Bahneinschnitt. Ein Fussweg-Kettenglied (OSM 1133554766 ...) verband zwei Bruecken (y=-725 und (231,-616)); `bridge_ways` kuerzt nur die Enden, nicht den flachen Mittelteil: 60-100 m Deck mit el = 0.00, gerendert als graue Platte mit Brüstung ueber Radstreifen/Mittelinsel.
Fix: `_split_flat(prep)` schneidet Ketten an inneren Flachstuecken (el <= 0.12 ueber > 10 m); je ein flacher Eckpunkt bleibt als Deck-Ende. Ketten 281 -> 322.
Vorher/nachher: `preview/slabs_2_before.jpg`, `preview/slabs_2_after.jpg`.
Noch zu bauen (gleiche Ursache, Kacheln mit altem Datenstand, 29): -10_5 -1_-1(gebaut) -1_0 -2_4 -3_1 -3_2 -4_2 -5_3 -7_3 -8_3 -9_4 0_1 1_-1 1_-7 2_-4 2_-7 2_-8 2_1 3_-2 4_-9 4_2 4_3 5_0 6_-6 6_-7 6_0 6_1 7_-5 9_-4 -> Komplett-Build ohnehin faellig. Betroffen auch Rail-Decks (flache Mittelstuecke werden zu Bodengleis).

## #1 Brauerstrasse West (376,-480) - TEILWEISE
Ursache: echte Brueckenrampe Hohlstrasse (Fussweg-Deck 4 + Strassendecks, el 0 -> 7 m). Der Eindruck "lose Platte/Trog" kam von der 0.38 m hohen Brüstung + 0.3 m Randstreifen schon bei el 0.1 m.
Fix (nur Client, kein Build): `bridges.ts` Brüstungshoehe 0.12 m bei el <= 0.3 m, waechst linear auf 0.38 m bei el >= 1.0 m. Rampen am Boden haben nur noch einen niedrigen Randstein.
Rest: Fussweg-Rampe steigt 0.5 m ueber flachem Platz, Aussenwand bleibt sichtbar (Boden daneben nicht angehoben). Nur mit Boeschung/Terrain-Anhebung loesbar.

## #3 Hardbrücke Nord (498,834)/(515,863) - BEHOBEN (Runde 2)
Deck liegt jetzt hoch ueber dem Boden (kein Deck-Problem mehr). Die weissen Wände sind Baustellen-Absperrungen (`construction`/sites, Ticket #19), kein Brückenteil.

## Hardbrücke West (-67,-48) - NICHT BEHOBEN
Kette `[365613466]` (road, 3.2 m, "Hardbrücke", 5 Punkte, (-67,-48)->(-58,-30)) liegt auf z = 0.1 zwischen Rampenenden auf +3.9 / +4.0; Boden -5.8 -> schwebt 5.9 m, Tram (-77,-63)->(-45,-17) folgt mit Buckel auf +0.1. Versuch: LiDAR-Wert bei kurzen Verbindungsketten verwerfen (Rule-Hoehe der Nachbarn passt) - kein Effekt, also stammt 0.1 NICHT aus `_lidar_decks`, sondern aus der Regelhoehe (`_envelope`/`req`, vermutlich Mindesthoehe ueber dem Tram/Gleis darunter, 6 m ab Boden -5.8) bzw. dem Joint-Mittelwert. Versuch zurueckgenommen. Naechster Schritt: in `bridge_ways` fuer ch 365613466 `req`/`z` vor und nach `_lidar_decks` ausgeben (Lauf ~6 min).

## #5 Vulkanplatz, #13 Idaplatz - Ursache gefunden, nicht bearbeitet (yards.py gesperrt)
Beides sind Zufalls-Mäuerchen aus `pipeline/yards.py::_front_walls` (Typ 0 = niedrige Mauer): Idaplatz Kachel -1_-6 `walls [0, -126.42, -1115.31, 3.12, 0.701, 8.08]` = die weisse Bahn (Ausblenden von `yards` laesst sie verschwinden); Vulkanplatz Kachel -10_4 `[0, -1974.56, 933.72, -13.15, -0.37, 12.7]` (12.7 m). Die Mauer entsteht an der Grenze "Gehsteig-Streifen / Hof", ohne Plausibilitaetspruefung ob dort wirklich ein Vorgarten liegt (auf Plaetzen/Plazas falsch). Vorschlag fuer den Facades-Agenten: Typ-0-Mauern nur, wenn `S["plaza"].buffer(3)` den Mittelpunkt nicht trifft und der Streifen an ein Gebaeude grenzt (< 6 m), oder Mauerlaenge <= 8 m und vorhandener OSM-Zaun/Mauer als Beleg.

## #10 (-1097,117) - nicht reproduzierbar
Kein Balken sichtbar in vier Blickrichtungen (PC). Naechstes Objekt: instanzierte Mesh (Roller/Fahrrad, 468 Vertices) am Spawn; yards `walls [2 Hecke]` + `drying` Wäscheständer bei (-1109,119) sind moegliche Quellen.

## #14 Turbinenplatz (-4,633) - Ursache gefunden, nicht behoben
Bodengitter (5 m) hat bei x = 0 eine Kante: z -8.33 (x<=-5) -> -9.17..-9.48 (x=0), also 0.85-1.15 m Absenkung (Beetkante / Terrain-Cut) ueber ein 5-m-Dreieck. Das helle Dreieck ist diese schraege Bodenflaeche mit Plattenfarbe. Fix gehoert in Terrain/Cut (`terrain_cuts.py` / Boden-Mesh-Aufloesung am Beet), nicht Deck.

## T-G3 (1322,-632), (1622,66), (-548,1236), (1550,124), (1504,175) - nicht bearbeitet
Schon in `research/bridges/round2.md` als echte Hang-/Boeschungsstufen (road_height/Terrain) eingeordnet, kein Deck-Problem.

## DECISIONS-Entwurf
**#79 - Flache Mittelstuecke aus Deck-Ketten schneiden, Brüstung waechst mit Hoehe.** `bridges._split_flat` trennt Ketten an inneren Stuecken mit el <= 0.12 m ueber > 10 m (FLAT_SPLIT); Teile mit el < 1.2 m fallen weg. `bridges.ts`: Brüstung 0.12 -> 0.38 m zwischen el 0.3 und 1.0 m.

## bridges_ride
Siehe `logs/slabs_ride.log` (Ergebnis im Bericht).
