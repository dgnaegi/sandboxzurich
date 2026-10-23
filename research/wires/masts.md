# Fahrleitungs-Masten pruefen (2026-10-22, Agent masts)

## Befund (v2 vor Aenderung, 1485 neue Randstein-Masten)
- Abstand zum naechsten LiDAR-Mast (<=2 / 2-4 / 4-8 / >8 m): alle Klasse 15: 12/34/146/1293; nur h>=6.3 m: 0/4/86/1395. Zu OSM-Lichtern: 1/54/145/1285. Ein groesserer Fangradius hilft kaum (ca. 46 Masten <4 m): die Masten waren erfunden.
- Fassade >=7.5 m innerhalb 13 m (irgendeine Richtung): 588.
- Verstoesse: 30 auf der Fahrbahn, 140 <1.2 m von der Gleismitte, 17 <0.8 m von einem Gebaeude (Eingang), 0 im Gebaeude.

## Regeln (wires.py)
- Mast-Fenster entlang des Gleises +-9 m (vorher +-5), Fassade bleibt vor Randstein.
- Neuer Randstein-Mast nur, wenn die Gegenseite einen echten Anker hat (Mast/Wand); sonst kein Querdraht (Fahrdraht laeuft ohne Span weiter).
- `kerb_ok`: nicht auf Fahrbahn (0.4 m Puffer), nicht innerhalb 1.6 m der Gleismitte, >=1.7 m von Fassaden (Eingang, Gehweg >=1.5 m bleibt). Gleisenden: 0.7 m, letzte Rueckfallebene ohne Fahrbahnpruefung (Platz/Wendeschleife).

## Ergebnis
- Randstein-Masten 1485 -> 563; Wandanker 570 -> 522; Mastanker 2616 -> 1704; Querdraehte 1559 -> 1079 (Entscheid: Realismus vor Querdraht).
- Verstoesse: Fahrbahn 5 (nur Gleisend-Masten auf Plaetzen), Gleis 0, Gebaeude 0, Gehweg <1.5 m 0.
- audit_wires: unverankert 0, Durchs Gebaeude 0, Kachelnaht 0.
- Rebuild: alle Kacheln mit Drahtmasten (voller Build). Keine Spiel-Screenshots (Kacheln noch Build 20).
