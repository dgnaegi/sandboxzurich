# QA-Runde Realitaetscheck (2026-10-18): Tickets

Methode: 72 Panoramax-Fotos (CC-BY-SA, lokal gecacht `research/fidelity_photos_local.json` bzw. neu `rc_extra.json`) an ca. 60 Orten ausserhalb der von anderen Agents bearbeiteten Plaetze; Spiel-Screenshot an gleicher Position/Richtung (`web/tests/rc_shots.mjs`, 1.7 m, vfov 80, 13:00). Kontaktboegen `preview/rc_1..13.jpg` (je 6 Paare Foto|Spiel; Nummer = Shot-ID in `research/qa_round/rc_shots*.json`). Kachel = floor(x/200)_floor(y/200).
Grenzen: Foto-GPS +-5 m, Blick +-10 Grad; Nacht-/360-Fotos (04, 18, 22, 23, 30, 40, 57, 60) nur beschraenkt vergleichbar; Landmarks laden verzoegert (Wiederholung mit 10 s Wartezeit in `game2/`).

Schwere: 1 = kosmetisch, 2 = faellt auf, 3 = bricht den Realismus/Spielbarkeit.

## T01 Fussgaengerstreifen fehlen (OSM: crossing=traffic_signals + crossing:markings=zebra, gelb)
- Kategorie: Strasse/Markierung; Schwere: 3; Haeufigkeit: 10 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Freihofstrasse, (-1301, -100), -7_-1, #13
  - Sportweg/Hardturm, (-846, 799), -5_3, #20
  - Hertersteg, (522, -1861), 2_-10, #21
  - Gueterbahnhof/Hardstr., (235, -387), 1_-2, #05
  - Goldbrunnenplatz, (-183, -1546), -1_-8, #58
  - Werdplatz, (798, -1288), 3_-7, #61
  - Quellenstrasse, (876, 332), 4_1, #17
  - Hubertus, (-1312, -782), -7_-4, #71
  - Letzigrund, (-976, -355), -5_-2, #59
  - Albisrank-West, (-1651, -508), -9_-3, #66
- Vermutete Ursache: pipeline/streets.py markings(): Diagnose (parse+Regeln, Skript nachgestellt): von 962 OSM-Querungsknoten im Spielgebiet werden nur 173 gezeichnet; 696 uebersprungen weil `crossing` leer/unmarked (viele echte Zebrastreifen ohne Markierungs-Tag), 74 weil kein Strassen-Way mit w>=4 den Knoten teilt (u.a. Freihofstrasse und Gueterbahnhof, beides signalisierte Zebras), 19 wegen Zone 30/Begegnungszone. Fussgaengerstreifen ausser Langstrasse also nur ein Fuenftel der Querungen
- Fix-Vorschlag: (1) Die 74 Zebra-Knoten ohne Way: naechsten Car-Way per Abstand <8 m statt Knoten-Identitaet suchen. (2) Die 696 Knoten ohne crossing-Tag: an Kreuzungen von Fussweg-Querung und Car-Way (footway=crossing) bzw. an Lichtsignalen als Zebra zeichnen, ausserhalb Zone 30; Gegenprobe per SWISSIMAGE (markings_ortho.py, gelbe Streifen).

## T02 Hecken/Gruenstreifen als glatte, hellgruene Quader (kein Laub, kein Schatten, zu saettigt)
- Kategorie: Vegetation; Schwere: 2; Haeufigkeit: 8 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Wiedikon Hardstr.-Seite, (502, -1305), 2_-7, #00
  - Feldstrasse, (343, -912), 1_-5, #31
  - Bullingerstrasse, (-726, -146), -4_-1, #32
  - Pfingstweidstrasse W, (-932, 837), -5_4, #34
  - Heinrichstrasse, (501, 501), 2_2, #55
  - Goldbrunnenplatz (grosse gruene Ellipse), (-183, -1546), -1_-8, #58
  - Kappeli, (-1648, 25), -9_0, #69
  - Letzipark, (-1276, 371), -7_1, #70
- Vermutete Ursache: web/src/world/details.ts HEDGE-Farben (0x3f5f2e..0x8a6a2a) + places_detail.ts/yards.ts: Box mit Flat-Colour, Hoehe/Breite aus OSM; keine Textur.
- Fix-Vorschlag: Hecken: dunklere, entsaettigte Palette, Laubtextur/Noise-Normal, Hoehe-Varianz, Abrundung (Kapsel) oder Instanz mit Laubatlas wie trees.ts; Rasenboeschung (flacher Keil, Foto 34) per Rasen-Textur statt Vollfarbe.

## T03 Fahrbahn-Asphalt: grobe Rechteck-Flicken, Querstreifen, Streckung in der Ferne; Foto: glatter, einheitlicher Belag
- Kategorie: Strasse/Markierung; Schwere: 2; Haeufigkeit: 7 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Hohlstrasse, (-2509, 851), -13_4, #25
  - Hardturmstrasse, (-1096, 1073), -6_5, #41
  - Kappeli (gestreckte Textur), (-1648, 25), -9_0, #69
  - Hubertus, (-1312, -782), -7_-4, #71
  - Sportweg, (-846, 799), -5_3, #20
  - Weststrasse, (466, -1526), 2_-8, #39
  - Zurlindenstrasse, (100, -1301), 0_-7, #37
- Vermutete Ursache: pipeline/ground_tex.py asphalt() (Flickstellen-Rechtecke, Teernaht) + Anisotropie im Headless-Test (Qualitaetsstufe, engine/materials.ts Z.59).
- Fix-Vorschlag: Flicken seltener, weicher und kleiner (Konturen mit Rauschen statt Rechteck), Kontrast der Flicken halbieren; Test mit anisotropy=8 gegenpruefen, bevor die Textur angefasst wird.

## T04 Bahnland/Gleisfeld: grosse blasse, fast weisse Flaechen und senkrechte graue Wand (Haze-Farbe) statt Schotter, Boeschung und Haeuser
- Kategorie: Gebaeude-Form; Schwere: 3; Haeufigkeit: 4 Orte; SYSTEMISCH
- Status: BEHOBEN 2026-10-19 (Agent E): Ursache war nicht Bahnland, sondern der Horizont-Vorhang (web/public/data/skyline.json, Ring far): 157 Peilungen ohne Gelaendedaten standen als (0,0,0), die Schliess-Sehne ging durch das Spielgebiet = blasse Ebene/Wand. pipeline/skyline.py fuellt Luecken jetzt mit flachem Platzhalter am Bandrand; Datei neu erzeugt.
- Orte (Ort, x/y, Kachel, Shot):
  - Pfingstweidstr./Toni W, (-501, 697), -3_3, #02
  - Hardturmstrasse, (-701, 1073), -4_5, #42
  - Hardturmstrasse, (-324, 1047), -2_5, #43
  - Schiffbau/Hardbruecke, (232, 436), 1_2, #60
- Vermutete Ursache: pipeline/railways.py / railzone.py (Bahnland-Boden, OSM-Dachplatte) oder Lueckenfuellung hinter den Haeuserzeilen; die Flaeche hat Nebelfarbe -> Material ohne Textur/ausserhalb Kachelradius.
- Fix-Vorschlag: Pro Aufnahme pruefen, ob die Flaeche ein Mesh der Kachel ist (sbxScene Raycast); Bahnland-Boden mit Schotter-Textur statt Flatcolor, Fassadenzeile Hardturmstr. Sued (Foto 42/43: 4-geschossige Haeuser) pruefen: fehlen in OSM/AV-Footprints oder wurden als Bahnzone entfernt.

## T05 Fassadenfarbe/-stil weicht ab (Notiz fehlt, falsch oder wird nicht angewendet)
- Kategorie: Fassade-Farbe; Schwere: 2; Haeufigkeit: 7 Orte; lokal
- Status: TEIL-BEHOBEN 2026-10-19 (Agent E): Weststrasse 177/180 in research/buildings/visual_notes_v3.json durch proposed_facades.json ersetzt (Foto 38, Konfidenz mittel). Uebrige Orte (Foerrlibuck, Letten, Gasometer, Eisgasse, Selnau, Ankerstr.) offen.
- Orte (Ort, x/y, Kachel, Shot):
  - Weststrasse 177/180, (106, -1094), 0_-6, #38
  - Foerrlibuckstrasse (Notiz Hardturmstr. 76 = Glas, Spiel: Holzpaneele), (69, 891), 0_4, #15
  - Lettenstrasse, (1152, 737), 5_3, #16
  - Gasometerstrasse (gesaettigt gruen), (1103, 223), 5_1, #54
  - Eisgasse (mintgruene Fensterbaender), (1155, -656), 5_-4, #50
  - Selnau, (1204, -1301), 6_-7, #65
  - Bezirksgebaeude/Ankerstr., (663, -1072), 3_-6, #11
- Vermutete Ursache: research/buildings/visual_notes_v3.json: Notizen 175/177/180/181 Weststrasse haben identischen Text (Copy-Paste, widerspricht Foto 38); Foerrlibuck: Notiz vorhanden, aber Spiel zeigt anderes Fassadenmuster -> Adresse->Gebaeude-Zuordnung (pipeline/build_testarea.py ~Z.346 / styles.py Z.150).
- Fix-Vorschlag: proposed_facades.json (Weststrasse 177/180); fuer Foerrlibuck Zuordnung debuggen (GWR-Punkt in falschem Polygon?); Gasometerstr./Eisgasse: Style-Default fuer Neubau B70 entsaettigen.

## T06 Haltestellen-Unterstaende, Ueberbauungen und Mobiliar fehlen oder sind vereinfacht
- Kategorie: Moeblierung; Schwere: 2; Haeufigkeit: 5 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Goldbrunnenplatz (Glas-Unterstand + Lift), (-183, -1546), -1_-8, #58
  - Technopark (Auskragung, Poller), (-76, 549), -1_2, #08
  - Bahnhof Altstetten (Unterstand, parkierte Autos), (-2097, 714), -11_3, #03
  - Aargauerstrasse (Werbevitrine am Unterstand), (-1093, 888), -6_4, #10
  - Pfingstweidstr. (Glas-Unterstand), (-932, 837), -5_4, #34
- Vermutete Ursache: pipeline/overrides/fidelity.json / places_detail_*.json (Unterstand-Typ vorhanden, aber nur an einzelnen Orten gesetzt); Haltestellen-Kit nur aus VBZ-Haltekanten.
- Fix-Vorschlag: Haltestellen-Unterstand systematisch aus VBZ-Haltestellen (stops_equip.json) + OSM shelter=yes setzen; Technopark als Landmark-Ticket.

## T07 Bodenpfeile (Richtungspfeile, Einspurpfeile) und Velopiktogramme fehlen
- Kategorie: Strasse/Markierung; Schwere: 1; Haeufigkeit: 5 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Letzigrund, (-976, -355), -5_-2, #59
  - Wipkingerplatz, (521, 972), 2_4, #67
  - Eisgasse, (1155, -656), 5_-4, #50
  - Foerrlibuckstr. (Velo-Piktogramm), (69, 891), 0_4, #15
  - Sportweg (Velo-Piktogramm), (-846, 799), -5_3, #20
- Vermutete Ursache: pipeline/streets.py markings(): nur Linien/Zebra/Haltelinie/«30»; keine Pfeile. markings_ortho.py misst nur Langstrasse.
- Fix-Vorschlag: SWISSIMAGE-Messung (markings_ortho.py) auf weitere Achsen ausdehnen oder Pfeile an Lichtsignal-Zufahrten setzen (signal_arms).

## T08 Gruener Velostreifen fehlt trotz Eintrag/Foto
- Kategorie: Strasse/Markierung; Schwere: 2; Haeufigkeit: 2 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Bullingerstrasse, (-726, -146), -4_-1, #32
  - Stauffacherstrasse (Eintrag vorhanden!), (83, -530), 0_-3, #46
- Vermutete Ursache: pipeline/overrides/velo_green.json: Bullingerstrasse nicht erfasst; Stauffacherstrasse (83,-530) erfasst, im Spiel nicht sichtbar -> Kachel evtl. vor fid2-Build gebaut oder Streifenseite falsch.
- Fix-Vorschlag: proposed_velo_green.json (Bullingerstrasse); Kachel 0_-3 pruefen/neu bauen (nur Test, nach Freigabe).

## T09 Parkierte Autos/Roller fehlen an Kerbparkierung; blaue Zone nicht ueberall
- Kategorie: Moeblierung; Schwere: 1; Haeufigkeit: 4 Orte; SYSTEMISCH
- Orte (Ort, x/y, Kachel, Shot):
  - Bahnhof Altstetten, (-2097, 714), -11_3, #03
  - Feldstrasse (Motorroller), (343, -912), 1_-5, #31
  - Lettenstrasse (blaue Linie), (1152, 737), 5_3, #16
  - Friedhof Sihlfeld, (-419, -910), -3_-5, #63
- Vermutete Ursache: pipeline/cityprops.py (Parkautos nur auf OGD-Parkfeldern; Roller-Reihen nicht erzeugt).
- Fix-Vorschlag: Roller/Motorrad-Parkfelder (OGD strassenparkierung Kategorie Motorrad) als Zweiradreihen erzeugen.

## T10 Ausserhalb Spielgebiet: blasse Ebene ohne Boden, Wiese ohne Strasse, Bus schwebt im Nichts
- Kategorie: Verkehr; Schwere: 2; Haeufigkeit: 6 Orte; SYSTEMISCH
- Status: ERLEDIGT (Agent F, 2026-10-19): transit.py clippt jetzt aufs Spielgebiet-Polygon + 60 m Rand (64 -> 53 Linien, 0 Punkte ausserhalb); traffic_legal gruen. Vorher: pipeline/transit.py clippt die Linien auf bbox+MARGIN statt auf das Spielgebiet-Polygon (alle 64 Linien haben Punkte ausserhalb, Bus bei (-1716,-663) liegt 466 m ausserhalb); Fix: Linien am Polygon clippen / Fahrzeuge ausserhalb despawnen.
- Orte (Ort, x/y, Kachel, Shot):
  - Albisrank, (-1651, -508), -9_-3, #66
  - Siemens/Albisriederstr. (Bus schwebt), (-1716, -663), -9_-4, #68
  - Hohlstrasse W, (-2852, 742), -15_3, #24
  - Badenerstrasse W, (-2819, 702), -15_3, #27
  - Hardturmstrasse W, (-1096, 1073), -6_5, #41
- Vermutete Ursache: Spielgebiet-Polygon (map.json polygon, x_min ~ -2590); Kacheln ausserhalb haben Backdrop ohne Strassen, NPC-/Tram-/Busspuren laufen weiter (transit.json-Linien reichen weiter nach Westen).
- Fix-Vorschlag: Fahrzeuge/Tram ausserhalb des Polygons nicht spawnen und beim Verlassen despawnen; Spieler:in an der Polygongrenze stoppen (weicher Rand), Backdrop-Bodenfarbe statt Nebelweiss.

## T11 Kamera steht in Gebaeude: Gebaeude liegt auf der Strasse (Hohlstrasse/Altstetten, Foto zeigt freie Kreuzung)
- Kategorie: Gebaeude-Form; Schwere: 3; Haeufigkeit: 1 Orte; lokal
- Status: ERLEDIGT (Agent F, 2026-10-19): systemisch im Kamera-Sweep (player.ts/collision.ts: Footprints < 20 m2 werden von Kamera-freeFraction/resolve ignoriert). Vorher: kein Gebaeude. Kachel -11_3 hat bei (-2053,696) einen 14 m2-Collider aus pipeline/sites.py (Baustellen OGD, Sites bei (-2055,690)/(-2053,689)) auf der Kreuzung; SB3D/OSM-Gebaeude liegen nicht auf der Fahrbahn. Fix: Baustellen auf Fahrbahn/Kreuzung filtern.
- Orte (Ort, x/y, Kachel, Shot):
  - Hohlstr. bei Bhf Altstetten Nord, (-2053, 699), -11_3, #26
- Vermutete Ursache: Gebaeude-Footprint ueber Fahrbahn: osm_buildings.update() (Aenderungen nach 2019) oder falscher AV-Gebaeudeeintrag; Strasse aus roadgraph unter dem Haus.
- Fix-Vorschlag: Audit-Skript: Gebaeude-Polygone (Kachel -11_3) mit Fahrbahn-Polygon schneiden (>30 m2) -> Liste; Override: buildings.json hide fuer betroffene IDs.

## T12 Schwebende Teile
- Kategorie: Schweben/Versinken; Schwere: 2; Haeufigkeit: 2 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Wipkingerplatz: weisse Quader in ~20 m Hoehe, (521, 972), 2_4, #67
  - Sportweg: schwarzer T-Pfosten ohne Boden, (-846, 799), -5_3, #20
- Vermutete Ursache: unbekannt: Kran/Landmark-Teil (Wipkingen) bzw. Signal-Ausleger ohne Mast (traffic_signs.py Ampel-Arme an Knoten ohne Mast-Boden).
- Fix-Vorschlag: Wipkingerplatz: sbxScene-Raycast Mesh-Namen ausgeben; Sportweg: signal_arms()-Mast pruefen (Foto 20 hat Lichtsignal am Zebra).

## T13 Viadukte: Unterseite flach dunkelbraun, Boegen/Fussweg und Beton-Seitenwand fehlen
- Kategorie: Gebaeude-Form; Schwere: 2; Haeufigkeit: 2 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Im Viadukt Josefstrasse, (502, 293), 2_1, #51
  - Wipkingerviadukt (Betonwand rechts fehlt), (521, 972), 2_4, #67
- Vermutete Ursache: Landmark viadukt_arches.glb (465,249) deckt nur die Boegen im Westen; OSM-Bruecke ohne Textur.
- Fix-Vorschlag: Viadukt-Bogenreihe laengs der ganzen Josefstrasse (Hardbruecke bis Limmat) modellieren; Wipkingerviadukt als Landmark.

## T14 Landmarks erscheinen erst >3.5 s nach Teleport (St. Jakob, Foto 57/48): beim Blick zeigt der Platz zuerst die Platzhalterfassade
- Kategorie: Gebaeude-Form; Schwere: 1; Haeufigkeit: 2 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Stauffacher / Kirche St. Jakob, (901, -1098), 4_-6, #48
- Vermutete Ursache: web/src/world/landmarks3d.ts laedt Landmarks lazy nach den Kacheln.
- Fix-Vorschlag: Landmarks mit Prioritaet vor Sichtweite laden (preload bei Teleport/Spawn).

## T15 Kopfsteinpflaster statt Asphalt (Josefstrasse, Foto: Asphalt mit Pflanzbeeten)
- Kategorie: Strasse/Markierung; Schwere: 1; Haeufigkeit: 1 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Josefstrasse bei Josefwiese-Ost, (860, 56), 4_0, #52
- Vermutete Ursache: pipeline/groundcover.py _cobble(): vas_basis-Achsen mit Namens-/Messbereich-Ueberlappung zu grob.
- Fix-Vorschlag: Fuer Achsen mit OSM surface=asphalt (Josefstrasse) Kopfstein-Maske ausschliessen.

## T16 Hydrant mitten auf der Fahrbahn (zwischen Parkfeldern)
- Kategorie: Moeblierung; Schwere: 1; Haeufigkeit: 1 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Hardstrasse bei Bhf Hardbruecke, (124, 269), 0_1, #23
- Vermutete Ursache: pipeline/streets.py extras["hydrants"]: Punkt nicht auf Trottoir geklemmt (OSM-Hydrant am Fahrbahnrand).
- Fix-Vorschlag: Hydranten auf naechsten Trottoirpunkt >=0.3 m hinter dem Randstein verschieben.

## T17 Tramgleise in der Naehe (Foerrlibuckstrasse, Linien 8/17) im Spiel kaum sichtbar
- Kategorie: Strasse/Markierung; Schwere: 1; Haeufigkeit: 1 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Foerrlibuckstrasse, (69, 891), 0_4, #15
- Vermutete Ursache: transit.json fuehrt die Linien in 4-7 m Abstand; Gleise im Spiel nur als schwache Linie (Foto: eingelassene Schienen mit Pflasterband).
- Fix-Vorschlag: Gleis-Kontrast/Pflasterband im Tram-Gleiskoerper (ground_paint.py) erhoehen.

## T18 Landmark fehlt: Landesmuseum/Platzspitz-Eingang (Foto: Schloss-Bau, Eisentor)
- Kategorie: Gebaeude-Form; Schwere: 2; Haeufigkeit: 1 Orte; lokal
- Orte (Ort, x/y, Kachel, Shot):
  - Landesmuseum, (1866, -510), 9_-3, #19
- Vermutete Ursache: landmarks.json hat kein Landesmuseum; nur generischer Block/Glasfassade.
- Fix-Vorschlag: Landmark aus Fotos (research/photos) bauen; Prioritaet mittel.

## Top-15 (Schwere x Haeufigkeit, systemische Ursachen x1.5)

1. T01 Fussgaengerstreifen fehlen (OSM: crossing=traffic_signals + crossing:markings=zebra, gelb) (S3 x 10, systemisch)
2. T02 Hecken/Gruenstreifen als glatte, hellgruene Quader (kein Laub, kein Schatten, zu saettigt) (S2 x 8, systemisch)
3. T03 Fahrbahn-Asphalt: grobe Rechteck-Flicken, Querstreifen, Streckung in der Ferne; Foto: glat (S2 x 7, systemisch)
4. T04 Bahnland/Gleisfeld: grosse blasse, fast weisse Flaechen und senkrechte graue Wand (Haze-Fa (S3 x 4, systemisch)
5. T10 Ausserhalb Spielgebiet: blasse Ebene ohne Boden, Wiese ohne Strasse, Bus schwebt im Nichts (S2 x 6, systemisch)
6. T06 Haltestellen-Unterstaende, Ueberbauungen und Mobiliar fehlen oder sind vereinfacht (S2 x 5, systemisch)
7. T05 Fassadenfarbe/-stil weicht ab (Notiz fehlt, falsch oder wird nicht angewendet) (S2 x 7)
8. T07 Bodenpfeile (Richtungspfeile, Einspurpfeile) und Velopiktogramme fehlen (S1 x 5, systemisch)
9. T09 Parkierte Autos/Roller fehlen an Kerbparkierung; blaue Zone nicht ueberall (S1 x 4, systemisch)
10. T08 Gruener Velostreifen fehlt trotz Eintrag/Foto (S2 x 2)
11. T12 Schwebende Teile (S2 x 2)
12. T13 Viadukte: Unterseite flach dunkelbraun, Boegen/Fussweg und Beton-Seitenwand fehlen (S2 x 2)
13. T11 Kamera steht in Gebaeude: Gebaeude liegt auf der Strasse (Hohlstrasse/Altstetten, Foto zei (S3 x 1)
14. T14 Landmarks erscheinen erst >3.5 s nach Teleport (St. Jakob, Foto 57/48): beim Blick zeigt d (S1 x 2)
15. T18 Landmark fehlt: Landesmuseum/Platzspitz-Eingang (Foto: Schloss-Bau, Eisentor) (S2 x 1)

## T19 Fussgaengerstreifen: Recall ~50 % nach Ortho-Scan (research/markings_audit.md)
- Kategorie: Markierung; Schwere: 3; Haeufigkeit: viele Orte; systemisch
- Orte: Seebahnstrasse/Badenerstrasse (150, -985) (6+ Streifen im Foto, keine im Spiel), Limmatplatz (1105, 95) (3 von ~6), Kalkbreite (270, -1175), Langstrasse/Roentgenstrasse (941, -220)
- Ursache: Zebra-Scan `markings_ortho25.py` (SWISSIMAGE 0.25 m, `crossings.scan`) findet ~210 Streifen (Praezision ~90 % laut Stichprobe `preview/markings_zebra25_check.jpg`); verpasst werden verschattete Streifen, Streifen ausserhalb Fahrbahnpolygon+1 m, Richtungsfilter (>37 Grad zur OSM-Achse).
- Fix-Vorschlag: Ortho 0.1 m nur entlang Hauptstrassen holen, Schattenmaske (lokaler Kontrast) fuer Streifen, Filter lockern.
- Status: TEIL-BEHOBEN 2026-10-19 (Agent Z2B): Scan 211 -> 403 Streifen im Build (Testkacheln, ganzes Gebiet), Recall gegen ortho-bestaetigte OSM-Streifen 68 -> 93 %, Precision geschaetzt 80-90 %. Ursache: Richtungsfilter nutzte die Blob-Hauptachse (bis 90 Grad falsch), Abstand nur zur naechsten Achse. Offen: Tiefschatten, Knoten mit verschmolzenen Streifen/Haltelinien (Matched-Filter waere der naechste Schritt). research/zones/zone2_street.md.

## T20 Markierungen weiss (Mittel-, Halte-, Parklinien) nicht pruefbar bei 0.5 m/px
- Kategorie: Markierung; Schwere: 2; Haeufigkeit: Gebiet; systemisch
- Orte: Stichprobe 0.1 m (preview/markings_audit.jpg): Limmatplatz (1130, 74), Langstrasse/Roentgen (945, -257), Lindenplatz (-2265, 419), Wiedikon (599, -1467): Spurtrenner/Pfeile im Foto, nur teilweise im Spiel; Bodenpfeile fehlen (siehe T07).
- Fix-Vorschlag: 0.1 m SWISSIMAGE-Fenster ausweiten, weisse Linien per Dunkel/Hell-Kontrast extrahieren (audit_markings.py hat die Masken), Overrides `markings_*.json`.

## T21 Fahrbahnpolygon schmaler als echte Strasse an breiten Knoten/Tramhaltestellen
- Kategorie: Strassenform; Schwere: 2; Haeufigkeit: 4 Orte
- Orte: Seebahnstrasse/Kalkbreite (290, -1193), Seebahn/Badenerstrasse (144, -980), Limmatplatz (1117, 87), Langstrasse/Zwinglistrasse (840, -474)
- Status: OFFEN (Agent F geprueft): Vergroesserte Knoten-Discs (carriageway.junction_discs, +2 m je Arm ab 3 Armen) aendern die 4 Orte um 0-8 m2 (insgesamt +4430 m2 von 2.05 Mio) -> nicht die Ursache; Polygon ist durch den AV-Carriageway selbst begrenzt (Cap/Kalibrierbreite in carriageway.apply), kein einfacher Fix. Nicht uebernommen.
- Ursache: AV-/Kalibrierbreite; Zebras werden dort jetzt mit eigenem Asphalt-Fuss ergaenzt (crossings.scan), sonst weggeschnitten.

## T22 Unterfuehrungsportale mit 22-40 % Neigung (echte DTM-Graeben)
- Kategorie: Bodenschwelle/Rampe; Schwere: 2; Haeufigkeit: 4 Orte
- Orte: Badenerstrasse (178, -998), Bullingerstrasse (-527, -269), Hohlstrasse (-61, -190), Foerrlibuckstrasse (-405, 837)
- Fix-Vorschlag: terrain_cuts-Rampen auf <= 12 % ueber 30 m verlaengern (`overrides/terrain_cuts.json`), ausserhalb road_height.
- Status: TEIL-BEHOBEN 2026-10-19 (Agent Z2B): Bullingerstrasse war eine ungetaggte Unterfuehrung unter dem Bahndamm (DTM +4.2 m statt Strasse -3.0 m): `pipeline/underpass_infer.py` + `road_height.carve_underpasses` (4 Faelle im Gebiet), Rampenknicke auf Strassen 3 (27/25/19 cm) -> 0, Hoehenraster-Stufen > 22 % 16 -> 10. Badenerstrasse (178,-998) gehoert zu T23 (Delle 0.24 -> 0.03 m). Hohlstrasse/Foerrlibuckstrasse sind T23. Offen: echte Mulden unter Bruecken ohne OSM-Brueckentag (Seebahnstr. (219,-613), Kanzleistr., Sihlbruecke): braucht Brueckendeck. research/bumps.md.

## T23 Restliche Fahrbahn-Buckel 10-20 cm (research/bumps.md)
- Kategorie: Bodenschwelle; Schwere: 1; Haeufigkeit: ~15 in 43 Kacheln
- Orte: Kornhausbruecke (1191, 135), Seebahnstrasse (219, -613) und (231, -595), Hohlstrasse (-74, -177), Foerrlibuckstrasse (-475, 849)
- Fix-Vorschlag: DTM-Spitzen neben dem Korridor glaetten (Versuch snap_roads brachte nichts), ggf. Fahrbahn-Zellen 4 m.
- Status: TEIL-BEHOBEN 2026-10-19 (Agent Z2B): Ursache war nicht das DTM, sondern `MAX_FILL` 1.2 m in road_height (Fahrbahnrand neben Mulde 20-42 cm zu tief, Asphaltecken auf der Polygonkante). Neu `MAX_FILL_IN` 3.0 m innerhalb der Fahrbahn + Korridor = Polygonbreite. Testkacheln: Strassenbuckel > 8 cm 9 -> 7, > 15 cm 3 -> 1 (Hohlstrasse 17 cm und Badenerstrasse weg). Rest: Kornhausbruecke 20 cm, Foerrlibuckstrasse 14-15 cm, Seebahnstr. (231,-595) 14 cm. research/bumps.md.

## knock Test flaky (Agent F, 2026-10-19)
- Status: ERLEDIGT: Pfosten (679.4,-708.6): an (683.5,-708.2) existiert kein Collider/Parkauto (Sonde), Crash stammte von dynamischem Fremdobjekt (NPC-Auto). knock.mjs wertet Crashs > 4 m vom Ziel nicht mehr als Fehler des Ziels (window.__extCrash). 4 Laeufe gruen.
