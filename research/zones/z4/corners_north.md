# Zone 4 Nord: Eckenabgleich Foto | Spiel (Idaplatz-Quartier, 2026-10-19)
Methode: `pipeline/zones/corners_north.py pick|shots|labels` (24 Ecken, 18 mit Foto: 8 Kamerapunkte + 16 Knoten/Zusatzpunkte; Foto = Mapillary, Spielbild 4 m vor Fotoposition). Bögen `preview/z4n_corner_{1,2,3}.jpg` (Foto|Spiel), `preview/z4n_labels_{1,2}.jpg` (Foto mit Adressen/Geschossen), `preview/z4n_zoom_1.jpg`.
Fotos: Mapillary CC BY-SA 4.0, IDs unten (Kurz-ID = letzte 8 Stellen im Bogen). Ohne Foto (kein Tageslicht-Foto 6-45 m, Blick zur Ecke): Badener/Martastr, Badener/Berta/Sihlfeld, Hasler/Zentralstr, Bertastr Nord, Zentralstr Nord, Martastr West.

| # | Ecke | Foto | Befund | Fix / Ticket |
|---|---|---|---|---|
| 0 | Idaplatz Mitte | ml_24332492813086116 | Idaplatz 1 ockerorange (Note passt), EG Kiosk mit roter Markise + Sitzplatz, Graffiti; gemaltes STOP auf Fahrbahn fehlt | storefronts_z4n: Smoking Kiosk Markise rot + Sitzplatz. Ticket T-N1 (STOP-Decal) |
| 1 | Idaplatz Nord / Bertastr | ml_1281520203360307 | Pollerreihe, Erker-/Rosa-Haeuser Idaplatz 8/9, Velobuegel; Spiel gleiche Struktur, Poller OSM-seitig | kein Fix (Poller kommen aus OSM) |
| 2, 8 | Idastr Sued / Idaplatz-Idastr | ml_24431230469820839 | Hintergrund: eingerüstetes weisses Haus + blaugraue Bauten (Baugerüst temporär), Graffiti-Eckhaus links | nichts (Gerüst temporär) |
| 3 | Bertastr/Zurlindenstr | ml_1166110868690167 | Ecke gerundet mit Kerb wie Spiel; Haeuser Zurlindenstr 213/215, Bertastr 20 grau-beige = Notizen passen | kein Fix |
| 4, 11 | Zentralstr/Gertrudstr | ml_831476732776965 | grosser runder Betontopf auf Kerbvorbau, Hecke rechts, Zebra weiter hinten; Aussensitz Lalin unter Baeumen | storefronts_z4n: Lalin t=1. Ticket T-N2 (Betontopf, Lage ±5 m, nicht belegt) |
| 5 | Zurlindenstr West | ml_1280080496763777 | Gertrudstr 26 = cremefarbenes Gruenderzeithaus mit **Mansarddach**, rotbraune Laeden, Restaurant Gertrudhof mit dunkler Markise (Note sagt «niedrig, flach, gewerbe», #d8cf9a: falsch); links daneben dunkler Anthrazit-Neubau (Adresse unklar, ~Gertrudstr 28/30, Note #dcdcd6 hell) | fields: Gertrudstr 26 M; storefronts_z4n Gertrudhof; Hex-Liste unten |
| 6, 14 | Zurlindenstr Ost / Sihlfeld-Zentralstr | ml_1393700231146136, ml_722479823204863 | **Foto-GPS falsch**: Fotopositionen liegen im Pausenplatz Schulhaus Zurlinden (Ortho: Sandplatz, Schopf, Spielgeraete); Foto zeigt in Wahrheit Zentralstrasse mit Parkfeldern/Zebra. Spiel (Mergelplatz + Buesche) ist korrekt | kein Fix; Zurlindenstr 160 (hellgrau, graugruene Balkone) passt |
| 7 | Thomasweg/Martastr | px_0bbaccf7-5e7 | Baukran + Gerüst (temporär), Velos | nichts |
| 12 | Eschwies/Zurlindenstr | ml_1495132664849734 | Zeilenbauten orange-ocker mit Balkonen (Notizen #c9863f passen), Parkfelder | kein Fix |
| 13 | Gertrud/Sihlfeld/Weststr | ml_930072181860399 | Ecke weissgrau mit graugruenen Laeden, dunklen Balkonen, gelbem Ladenschild (Gertrudstr 6 oder Zentralstr 118, Notizen beige #cdbfa5 / #d8cdb0; Licht kuehl, daher nur Hinweis) | kein Fix |
| 16 | Idaplatz West | ml_3668311446803623 | Idaplatz 4 pfirsich/rosa (Note #dccacc passt), rote Blutbuchen, Gelb-Felder | kein Fix |
| 17 | Idaplatz Ost | ml_776462388354240 | Baustellenwand mit Wildplakaten entlang Zurlindenstr (temporär), Idaplatz 1 ockerorange | nichts (temporär) |
| 19 | Zurlindenstr Mitte | ml_1278624740246659 | Zurlindenstr 191 lachsrosa mit Balkonen (passt); Nr. 193 hellgelb, graues Steinsockel-EG mit Laeden; Idastr 50 orange (passt) | fields 193 R; Hex-Liste |
| 21 | Idastr Nord / Berta | ml_712784297736015 | Eckhaus mit rundem Erkerturm: Obergeschosse aprikose/ocker, EG lachsrosa mit Rundbogen + blauer Tuer; auf Fahrbahn gemalte «30», weisse Strichlinien | fields 214 E; markings_z4n: gemalte 30 (Decal); Hex-Liste. Ticket T-N3 (Strichlinien) |
| 22 | Thomasweg Sued | ml_2280260072397352 | linker Block (Zentralstr 138/140) = graubeiger 60er-Bau mit Fensterband, Blumenkaesten, dunkle Arkade, rosa Kopfwand; Note 140 «cremeweiss, Rundbogen, Gesims» passt nicht | neue Note 138; Hex-Liste |
| 9,10,15,18,20,23 | – | – | kein Foto (s.o.) | – |

## Hex-/Stil-Korrekturen für die Hauptsession (bestehende Notizen, fields kann Hex nicht setzen)
- Gertrudstrasse 26: hex #e8dcc0, dach mansard, stil gruenderzeit, laeden rot, EG Restaurant (Gertrudhof). Konfidenz hoch.
- Zurlindenstrasse 214: hex #e6b87c (aprikose), EG-Sockel #d9a090, Erkerturm, stil gruenderzeit (Note «weissgrau» falsch, Ecke Bertastr). Konfidenz mittel (Zuordnung 214 vs 216 aus Bearing).
- Zurlindenstrasse 193: hex #e4dc90 (statt #c4c48c), EG Natursteinsockel grau. Konfidenz mittel.
- Zentralstrasse 140 (+138 neu): hex #cdc4ba, stil 60er, dach flach, fenster band, kein Gesims. Konfidenz mittel.

## Zusammenfassung
Ecken geprüft: 18 mit Foto (6 ohne). Fixes: 1 neue Fassadennote, 3 Felder (E/R/M), 3 Laden-Overrides, 1 Decal (gemalte 30), 0 Plätze/Objekte (keine Lage belegt), 4 Hex/Stil-Korrekturen als Liste.
Tickets (Code/Kachel-Build): T-N1 Decal «STOP» (Fahrbahntext; kein Decal-Typ, Foto #0), T-N2 Betontopf Zentralstr/Gertrudstr, T-N3 gestrichelte weisse Linien/Velostreifen Bertastr und Knoten Zurlindenstr (Ortho im Schatten, Messung bei Licht nötig), T-N4 alle Overrides wirken erst nach Kachel-Build (Spielbilder Nachher fehlen daher), T-N5 Foto-GPS-Fehler beachten (Mapillary-Punkte im Schulhof Zurlinden).
