import math,json,sys
ZEB=open('zeb_cause.txt').read().strip() if __import__('os').path.exists('zeb_cause.txt') else 'noch zu klaeren (Diagnose-Skript lief nicht durch)'
# id, titel, kat, sev, n(shots), orte[(name,x,y,shot)], ursache, fix, systemisch
T=[
('T01','Fussgaengerstreifen fehlen (OSM: crossing=traffic_signals + crossing:markings=zebra, gelb)','Strasse/Markierung',3,10,
 [('Freihofstrasse',-1301,-100,13),('Sportweg/Hardturm',-846,799,20),('Hertersteg',522,-1861,21),('Gueterbahnhof/Hardstr.',235,-387,'05'),('Goldbrunnenplatz',-183,-1546,58),('Werdplatz',798,-1288,61),('Quellenstrasse',876,332,17),('Hubertus',-1312,-782,71),('Letzigrund',-976,-355,59),('Albisrank-West',-1651,-508,66)],
 'pipeline/streets.py markings(): '+ZEB,
 '(1) Die 74 Zebra-Knoten ohne Way: naechsten Car-Way per Abstand <8 m statt Knoten-Identitaet suchen. (2) Die 696 Knoten ohne crossing-Tag: an Kreuzungen von Fussweg-Querung und Car-Way (footway=crossing) bzw. an Lichtsignalen als Zebra zeichnen, ausserhalb Zone 30; Gegenprobe per SWISSIMAGE (markings_ortho.py, gelbe Streifen).',True),
('T02','Hecken/Gruenstreifen als glatte, hellgruene Quader (kein Laub, kein Schatten, zu saettigt)','Vegetation',2,8,
 [('Wiedikon Hardstr.-Seite',502,-1305,'00'),('Feldstrasse',343,-912,31),('Bullingerstrasse',-726,-146,32),('Pfingstweidstrasse W',-932,837,34),('Heinrichstrasse',501,501,55),('Goldbrunnenplatz (grosse gruene Ellipse)',-183,-1546,58),('Kappeli',-1648,25,69),('Letzipark',-1276,371,70)],
 'web/src/world/details.ts HEDGE-Farben (0x3f5f2e..0x8a6a2a) + places_detail.ts/yards.ts: Box mit Flat-Colour, Hoehe/Breite aus OSM; keine Textur.',
 'Hecken: dunklere, entsaettigte Palette, Laubtextur/Noise-Normal, Hoehe-Varianz, Abrundung (Kapsel) oder Instanz mit Laubatlas wie trees.ts; Rasenboeschung (flacher Keil, Foto 34) per Rasen-Textur statt Vollfarbe.',True),
('T03','Fahrbahn-Asphalt: grobe Rechteck-Flicken, Querstreifen, Streckung in der Ferne; Foto: glatter, einheitlicher Belag','Strasse/Markierung',2,7,
 [('Hohlstrasse',-2509,851,25),('Hardturmstrasse',-1096,1073,41),('Kappeli (gestreckte Textur)',-1648,25,69),('Hubertus',-1312,-782,71),('Sportweg',-846,799,20),('Weststrasse',466,-1526,39),('Zurlindenstrasse',100,-1301,37)],
 'pipeline/ground_tex.py asphalt() (Flickstellen-Rechtecke, Teernaht) + Anisotropie im Headless-Test (Qualitaetsstufe, engine/materials.ts Z.59).',
 'Flicken seltener, weicher und kleiner (Konturen mit Rauschen statt Rechteck), Kontrast der Flicken halbieren; Test mit anisotropy=8 gegenpruefen, bevor die Textur angefasst wird.',True),
('T04','Bahnland/Gleisfeld: grosse blasse, fast weisse Flaechen und senkrechte graue Wand (Haze-Farbe) statt Schotter, Boeschung und Haeuser','Gebaeude-Form',3,4,
 [('Pfingstweidstr./Toni W',-501,697,'02'),('Hardturmstrasse',-701,1073,42),('Hardturmstrasse',-324,1047,43),('Schiffbau/Hardbruecke',232,436,60)],
 'pipeline/railways.py / railzone.py (Bahnland-Boden, OSM-Dachplatte) oder Lueckenfuellung hinter den Haeuserzeilen; die Flaeche hat Nebelfarbe -> Material ohne Textur/ausserhalb Kachelradius.',
 'Pro Aufnahme pruefen, ob die Flaeche ein Mesh der Kachel ist (sbxScene Raycast); Bahnland-Boden mit Schotter-Textur statt Flatcolor, Fassadenzeile Hardturmstr. Sued (Foto 42/43: 4-geschossige Haeuser) pruefen: fehlen in OSM/AV-Footprints oder wurden als Bahnzone entfernt.',True),
('T05','Fassadenfarbe/-stil weicht ab (Notiz fehlt, falsch oder wird nicht angewendet)','Fassade-Farbe',2,7,
 [('Weststrasse 177/180',106,-1094,38),('Foerrlibuckstrasse (Notiz Hardturmstr. 76 = Glas, Spiel: Holzpaneele)',69,891,15),('Lettenstrasse',1152,737,16),('Gasometerstrasse (gesaettigt gruen)',1103,223,54),('Eisgasse (mintgruene Fensterbaender)',1155,-656,50),('Selnau',1204,-1301,65),('Bezirksgebaeude/Ankerstr.',663,-1072,11)],
 'research/buildings/visual_notes_v3.json: Notizen 175/177/180/181 Weststrasse haben identischen Text (Copy-Paste, widerspricht Foto 38); Foerrlibuck: Notiz vorhanden, aber Spiel zeigt anderes Fassadenmuster -> Adresse->Gebaeude-Zuordnung (pipeline/build_testarea.py ~Z.346 / styles.py Z.150).',
 'proposed_facades.json (Weststrasse 177/180); fuer Foerrlibuck Zuordnung debuggen (GWR-Punkt in falschem Polygon?); Gasometerstr./Eisgasse: Style-Default fuer Neubau B70 entsaettigen.',False),
('T06','Haltestellen-Unterstaende, Ueberbauungen und Mobiliar fehlen oder sind vereinfacht','Moeblierung',2,5,
 [('Goldbrunnenplatz (Glas-Unterstand + Lift)',-183,-1546,58),('Technopark (Auskragung, Poller)',-76,549,'08'),('Bahnhof Altstetten (Unterstand, parkierte Autos)',-2097,714,'03'),('Aargauerstrasse (Werbevitrine am Unterstand)',-1093,888,10),('Pfingstweidstr. (Glas-Unterstand)',-932,837,34)],
 'pipeline/overrides/fidelity.json / places_detail_*.json (Unterstand-Typ vorhanden, aber nur an einzelnen Orten gesetzt); Haltestellen-Kit nur aus VBZ-Haltekanten.',
 'Haltestellen-Unterstand systematisch aus VBZ-Haltestellen (stops_equip.json) + OSM shelter=yes setzen; Technopark als Landmark-Ticket.',True),
('T07','Bodenpfeile (Richtungspfeile, Einspurpfeile) und Velopiktogramme fehlen','Strasse/Markierung',1,5,
 [('Letzigrund',-976,-355,59),('Wipkingerplatz',521,972,67),('Eisgasse',1155,-656,50),('Foerrlibuckstr. (Velo-Piktogramm)',69,891,15),('Sportweg (Velo-Piktogramm)',-846,799,20)],
 'pipeline/streets.py markings(): nur Linien/Zebra/Haltelinie/«30»; keine Pfeile. markings_ortho.py misst nur Langstrasse.',
 'SWISSIMAGE-Messung (markings_ortho.py) auf weitere Achsen ausdehnen oder Pfeile an Lichtsignal-Zufahrten setzen (signal_arms).',True),
('T08','Gruener Velostreifen fehlt trotz Eintrag/Foto','Strasse/Markierung',2,2,
 [('Bullingerstrasse',-726,-146,32),('Stauffacherstrasse (Eintrag vorhanden!)',83,-530,46)],
 'pipeline/overrides/velo_green.json: Bullingerstrasse nicht erfasst; Stauffacherstrasse (83,-530) erfasst, im Spiel nicht sichtbar -> Kachel evtl. vor fid2-Build gebaut oder Streifenseite falsch.',
 'proposed_velo_green.json (Bullingerstrasse); Kachel 0_-3 pruefen/neu bauen (nur Test, nach Freigabe).',False),
('T09','Parkierte Autos/Roller fehlen an Kerbparkierung; blaue Zone nicht ueberall','Moeblierung',1,4,
 [('Bahnhof Altstetten',-2097,714,'03'),('Feldstrasse (Motorroller)',343,-912,31),('Lettenstrasse (blaue Linie)',1152,737,16),('Friedhof Sihlfeld',-419,-910,63)],
 'pipeline/cityprops.py (Parkautos nur auf OGD-Parkfeldern; Roller-Reihen nicht erzeugt).',
 'Roller/Motorrad-Parkfelder (OGD strassenparkierung Kategorie Motorrad) als Zweiradreihen erzeugen.',True),
('T10','Ausserhalb Spielgebiet: blasse Ebene ohne Boden, Wiese ohne Strasse, Bus schwebt im Nichts','Verkehr',2,6,
 [('Albisrank',-1651,-508,66),('Siemens/Albisriederstr. (Bus schwebt)',-1716,-663,68),('Hohlstrasse W',-2852,742,24),('Badenerstrasse W',-2819,702,27),('Hardturmstrasse W',-1096,1073,41)],
 'Spielgebiet-Polygon (map.json polygon, x_min ~ -2590); Kacheln ausserhalb haben Backdrop ohne Strassen, NPC-/Tram-/Busspuren laufen weiter (transit.json-Linien reichen weiter nach Westen).',
 'Fahrzeuge/Tram ausserhalb des Polygons nicht spawnen und beim Verlassen despawnen; Spieler:in an der Polygongrenze stoppen (weicher Rand), Backdrop-Bodenfarbe statt Nebelweiss.',True),
('T11','Kamera steht in Gebaeude: Gebaeude liegt auf der Strasse (Hohlstrasse/Altstetten, Foto zeigt freie Kreuzung)','Gebaeude-Form',3,1,
 [('Hohlstr. bei Bhf Altstetten Nord',-2053,699,26)],
 'Gebaeude-Footprint ueber Fahrbahn: osm_buildings.update() (Aenderungen nach 2019) oder falscher AV-Gebaeudeeintrag; Strasse aus roadgraph unter dem Haus.',
 'Audit-Skript: Gebaeude-Polygone (Kachel -11_3) mit Fahrbahn-Polygon schneiden (>30 m2) -> Liste; Override: buildings.json hide fuer betroffene IDs.',False),
('T12','Schwebende Teile','Schweben/Versinken',2,2,
 [('Wipkingerplatz: weisse Quader in ~20 m Hoehe',521,972,67),('Sportweg: schwarzer T-Pfosten ohne Boden',-846,799,20)],
 'unbekannt: Kran/Landmark-Teil (Wipkingen) bzw. Signal-Ausleger ohne Mast (traffic_signs.py Ampel-Arme an Knoten ohne Mast-Boden).',
 'Wipkingerplatz: sbxScene-Raycast Mesh-Namen ausgeben; Sportweg: signal_arms()-Mast pruefen (Foto 20 hat Lichtsignal am Zebra).',False),
('T13','Viadukte: Unterseite flach dunkelbraun, Boegen/Fussweg und Beton-Seitenwand fehlen','Gebaeude-Form',2,2,
 [('Im Viadukt Josefstrasse',502,293,51),('Wipkingerviadukt (Betonwand rechts fehlt)',521,972,67)],
 'Landmark viadukt_arches.glb (465,249) deckt nur die Boegen im Westen; OSM-Bruecke ohne Textur.',
 'Viadukt-Bogenreihe laengs der ganzen Josefstrasse (Hardbruecke bis Limmat) modellieren; Wipkingerviadukt als Landmark.',False),
('T14','Landmarks erscheinen erst >3.5 s nach Teleport (St. Jakob, Foto 57/48): beim Blick zeigt der Platz zuerst die Platzhalterfassade','Gebaeude-Form',1,2,
 [('Stauffacher / Kirche St. Jakob',901,-1098,48)],
 'web/src/world/landmarks3d.ts laedt Landmarks lazy nach den Kacheln.',
 'Landmarks mit Prioritaet vor Sichtweite laden (preload bei Teleport/Spawn).',False),
('T15','Kopfsteinpflaster statt Asphalt (Josefstrasse, Foto: Asphalt mit Pflanzbeeten)','Strasse/Markierung',1,1,
 [('Josefstrasse bei Josefwiese-Ost',860,56,52)],
 'pipeline/groundcover.py _cobble(): vas_basis-Achsen mit Namens-/Messbereich-Ueberlappung zu grob.',
 'Fuer Achsen mit OSM surface=asphalt (Josefstrasse) Kopfstein-Maske ausschliessen.',False),
('T16','Hydrant mitten auf der Fahrbahn (zwischen Parkfeldern)','Moeblierung',1,1,
 [('Hardstrasse bei Bhf Hardbruecke',124,269,23)],
 'pipeline/streets.py extras["hydrants"]: Punkt nicht auf Trottoir geklemmt (OSM-Hydrant am Fahrbahnrand).',
 'Hydranten auf naechsten Trottoirpunkt >=0.3 m hinter dem Randstein verschieben.',False),
('T17','Tramgleise in der Naehe (Foerrlibuckstrasse, Linien 8/17) im Spiel kaum sichtbar','Strasse/Markierung',1,1,
 [('Foerrlibuckstrasse',69,891,15)],
 'transit.json fuehrt die Linien in 4-7 m Abstand; Gleise im Spiel nur als schwache Linie (Foto: eingelassene Schienen mit Pflasterband).',
 'Gleis-Kontrast/Pflasterband im Tram-Gleiskoerper (ground_paint.py) erhoehen.',False),
('T18','Landmark fehlt: Landesmuseum/Platzspitz-Eingang (Foto: Schloss-Bau, Eisentor)','Gebaeude-Form',2,1,
 [('Landesmuseum',1866,-510,19)],
 'landmarks.json hat kein Landesmuseum; nur generischer Block/Glasfassade.',
 'Landmark aus Fotos (research/photos) bauen; Prioritaet mittel.',False),
]
def tile(x,y): return f"{math.floor(x/200)}_{math.floor(y/200)}"
out=['# QA-Runde Realitaetscheck (2026-10-18): Tickets\n',
'Methode: 72 Panoramax-Fotos (CC-BY-SA, lokal gecacht `research/fidelity_photos_local.json` bzw. neu `rc_extra.json`) an ca. 60 Orten ausserhalb der von anderen Agents bearbeiteten Plaetze; Spiel-Screenshot an gleicher Position/Richtung (`web/tests/rc_shots.mjs`, 1.7 m, vfov 80, 13:00). Kontaktboegen `preview/rc_1..13.jpg` (je 6 Paare Foto|Spiel; Nummer = Shot-ID in `research/qa_round/rc_shots*.json`). Kachel = floor(x/200)_floor(y/200).',
'Grenzen: Foto-GPS +-5 m, Blick +-10 Grad; Nacht-/360-Fotos (04, 18, 22, 23, 30, 40, 57, 60) nur beschraenkt vergleichbar; Landmarks laden verzoegert (Wiederholung mit 10 s Wartezeit in `game2/`).\n',
'Schwere: 1 = kosmetisch, 2 = faellt auf, 3 = bricht den Realismus/Spielbarkeit.\n']
for t in T:
    i,title,cat,sev,n,orte,ur,fix,sysm=t
    out.append(f"## {i} {title}\n- Kategorie: {cat}; Schwere: {sev}; Haeufigkeit: {n} Orte; {'SYSTEMISCH' if sysm else 'lokal'}")
    out.append('- Orte (Ort, x/y, Kachel, Shot):')
    for o in orte: out.append(f"  - {o[0]}, ({o[1]}, {o[2]}), {tile(o[1],o[2])}, #{o[3]}")
    out.append(f"- Vermutete Ursache: {ur}\n- Fix-Vorschlag: {fix}\n")
def score(t): return (t[3]*t[4]*(1.5 if t[8] else 1))
top=sorted(T,key=score,reverse=True)[:15]
out.append('## Top-15 (Schwere x Haeufigkeit, systemische Ursachen x1.5)\n')
for k,t in enumerate(top,1): out.append(f"{k}. {t[0]} {t[1][:90]} (S{t[3]} x {t[4]}{', systemisch' if t[8] else ''})")
open('tickets.md','w').write('\n'.join(out)+'\n')
print(len(T),'tickets');[print(k,t[0],score(t)) for k,t in enumerate(top,1)]
