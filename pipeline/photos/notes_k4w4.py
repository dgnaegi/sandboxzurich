"""Writes research/v3/<id>.md for the wave-4 landmarks (k4w4_*.py) and research/v3/CREDITS_k4w4.md from the photo metadata. Run: python notes_k4w4.py"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
R = ROOT / "research" / "v3"
M = json.load(open(R / "photos_k4w4.json"))
M["zentralwaescherei"] = json.load(open(R / "photos_k4w4_zw.json"))["zentralwaescherei"]

N = {
 "zentralwaescherei": dict(site="zentralwaescherei", name="Zentralwäscherei (Kulturhaus, Neue Hard 12, Kreis 5)", model="pipeline/landmarks/k4w4_zentralwaescherei.py", refs="Panoramax #108, Commons #34 #35 #36 #7, Mapillary #78 #90 #79 #123 #132 #145 #148; Luftbild SWISSIMAGE (Dachformen, Hof, Wasserturm)",
  masse="Hauptbau 101 x 42 m (swissBUILDINGS3D ID_6DCCD334, OSM «Zentralwäscherei Zurich», 6 Geschosse laut OSM). Halle (NE) Traufe 9.3 m mit Sheddach (5 Streifen à 8.4 m, Anstieg 2.4 m, Glasbrüstung nach NW); Aufbauten 12.6 / 18.4 / 22.3 / 25.3 m, Treppenturm 27.8 m (Stufen aus den Dachflächen). Kiosk 66 m², 3.4 m. Wasserturm im Hof bei (334, 277): Tank r 3.4 m, 5.2 m hoch, auf 10 m Stahlgerüst, Gesamthöhe ca. 18 m.",
  farben="Putz #cfcabd (Halle), #cdc8ba / #dcd8cc / #c7c2b4 (Aufbauten), Sockel #96928a, Fensterrahmen dunkel #2f3335, Kiosk rosa #e8a2b0 mit Plakaten/Graffiti, Schriftschild #efede6 / schwarz #141414, Band grau #787876, Wasserturm Rost #7a4a36, gelber Tank #e8be28, Turmbeschriftung «HC BR» #96dc3c, «ZW» #287a3c",
  fenster="Halle: Achse 3.0 m, Fenster 2.3 x 2.0 m mit Sprossen, Brüstung 1.0 m; EG alle 5. Achse Rolltor-Öffnung 3 x 3.4 m; Aufbauten: Bandfenster 2.6 x 1.6 m, Achse 2.9 m.",
  eg="Kiosk/Eingangsbau an der Strasse (Neue Hard): rosa, überklebt mit Plakaten und Graffiti, Dach mit Pergola und Pflanzen; Mauern mit Graffiti beidseits; Hofeinfahrt; Eingang «ZW» (Glastür, im Nachtbild leuchtend)",
  schrift="«Zentral wäscherei» (Barlow Bold, schwarz auf weiss), Band «BAR | KULTUR» und «CAFE | RESTAURANT» (weiss auf grau); am Turm «HC BR» und «ZW» im Graffiti-Stil (freie Schrift Permanent Marker)",
  details="Plakat-/Graffitiflächen als Atlas (prozedural, keine echten Werke); gelber Tank auf dem SW-Block; roter-weisser Kamin im Hintergrund = KVA-Kamin (bestehendes Landmark); Wasserturm mit Leiter und Ringverstrebung; Dachterrasse mit Pflanzkisten",
  nacht="Fensterleuchten (30–40 % warm), Schild weiss, Eingang ZW"),
 "johanneskirche": dict(site="johanneskirche", name="Johanneskirche Limmatplatz", model="pipeline/landmarks/k4w4_johannes.py", refs="Commons #10 #11 #12, Mapillary #2, Panoramax #18 #19",
  masse="Fussabdruck 43 x 22.5 m (ID_117A35C6), Langachse 42°; Turm 7.2 m im Quadrat am SW-Ende, Spitze 48.4 m; Schiff Traufe 14 m, First ca. 20 m; Brunnenpavillon (ID_0D8FAAC7) Oktogon r ≈ 1.95 m, Höhe 8.2 m inkl. Kupferkuppel",
  farben="Sandstein-Quader #a89880 (rustiziert), Gesimse #bcae92 / #cdbf9f, Schiefer #424449, Turmhelm Kupfer #689c84, Zifferblatt dunkelblau #27415f mit Gold #e0b83c; Pavillon Kalkstein #d9c8a6, Gesims dunkelrot #7b2f26, Kuppel Patina #76a88e",
  fenster="Schiff: hohe Rundbogenfenster 2.1 m breit, Brüstung 3.4 m, Kämpfer 9 m, Achse 5.4 m; Turm: Portal 2.6 x 4.4 m, Zwillingsfenster, Schallöffnungen 2.2 m mit Rundbogen",
  eg="Portal im Turm zur Strasse; Brunnen mit Muschelnische und Steintrog am Pavillon", schrift="Zifferblätter (Ziffernstriche) auf 4 Seiten, keine Schrift",
  details="Eckfialen am Turmabschluss, Kugel/Kreuz auf der Spitze, Rundfenster (Oculi) im Pavillon", nacht="Fenster mit warmem Licht, Zifferblatt hinterleuchtet"),
 "limmathaus": dict(site="limmathaus", name="Limmathaus (Limmatstrasse 118)", model="pipeline/landmarks/k4w4_limmathaus.py", refs="Panoramax #23, Mapillary #9 #8 #4, Commons #14–#16 (Nachbar-Wandbild)",
  masse="Fussabdruck 60 x 47.5 m (ID_6AC66823, 16 Eckpunkte = geschwungene Front), Stufen 9.4 / 11.1 / 22.2 / 25.2 / 26.3 m", farben="Putz #d9d2bd, Rahmen blau #2d5a96, Sockel #8f8a7c, Gesimse #bdb49c",
  fenster="Bandfenster 1.75 x 1.55 m, Achse 2.3 m, Geschosshöhe 3.3 m, Geschossbänder 0.3 m", eg="Ladenfront 4.6 m hoch, durchgehend verglast mit Eingängen", schrift="keine am Modell", details="Gewerbehaus 1931, geschwungene Ecke zum Limmatplatz", nacht="Büro- und Ladenlicht 45 %"),
 "houdini": dict(site="idaplatz_block", name="Block Kino Houdini (Hohlstrasse, Idaplatz)", model="pipeline/landmarks/k4w4_houdini.py", refs="Mapillary #10 #7 #13 #4 #11, Panoramax #24",
  masse="Fussabdruck 105 x 76 m (ID_B7D39928), Stufen 12 / 17 / 23 / 25 / 28 / 30.5 m (7 Geschosse)", farben="Backstein sandgelb #cfa971 / #c9a46c, Fugen #d3c19c, Rahmen und EG dunkel #2b2b2c, Schrift Gold #b8955a",
  fenster="quadratische Lochfenster 1.4 x 1.5 m, Achse 2.8 m, Geschoss 3.1 m; EG 5.4 m dunkel verglast", eg="Kino, Läden, Velohalter vor der Fassade", schrift="«KINO HOUDINI» (Barlow Bold, Gold auf Backstein), «KIND» weiss auf schwarz (nur Text, freie Schrift)",
  details="Zeilenartiger Block mit Innenhof, Dachterrassen", nacht="Schaufenster hell, Fenster 40 %"),
 "langstrasse_blau": dict(site="langstrasse_nord", name="Langstrasse Eckhaus blau", model="pipeline/landmarks/k4w4_langstrasse_blau.py", refs="Mapillary #9 #10 #8 #5 #6, Panoramax #16 #17",
  masse="50 x 15 m (ID_D038A8FB), Stufen 23.4 / 26.4 / 27.4 m", farben="Putz blaugrau #8396b4, Rahmen #e9e6de, Markisen dunkelrot #8a1f2a, Sockel #6d6a62", fenster="1.05 x 1.6 m, Achse 2.5 m, Geschoss 3.0 m, Rollläden (hell)",
  eg="Beizen mit Markisen und Terrassentischen, Eingänge", schrift="«BAR» weiss auf dunkelrot", details="zurückversetztes Dachgeschoss, Satellitenschüsseln", nacht="Beizen warm, Fenster 45 %"),
 "wiedikon_block": dict(site="wiedikon_platz", name="Wiedikon-Platz Wohn- und Geschäftshaus", model="pipeline/landmarks/k4w4_wiedikon_block.py", refs="Mapillary #11 #2 #5 #15",
  masse="52 x 22 m (ID_EBF6EB64), Stufen 5.7 / 6.8 / 23 / 25.2 / 26.7 / 29.7 m", farben="Putz hellrosa #e6d2c3, Rahmen #f1ede4, Laden rot #b03a3a / blau #3a5a90, Dachrand #cdbfae", fenster="1.35 x 1.45 m, Achse 2.7 m, Geschoss 3.05 m; rote und blaue Läden/Brüstungsfelder",
  eg="Läden im Sockel (niedriger Anbau 5.7–6.8 m)", schrift="keine", details="weit auskragender Flachdachrand", nacht="Fenster 40 %"),
 "roentgen_zeile": dict(site="roentgen_zeile", name="Röntgenstrasse Zeile Ocker", model="pipeline/landmarks/k4w4_roentgen_zeile.py", refs="Panoramax #14, Mapillary #1 #0 #4 #3",
  masse="107 x 35 m (ID_DBFB2624, zwei Flügel), Traufe 17.3 m, Walmdach 4.8 m", farben="Putz ocker #dcb676, Fensterläden braun #5a3a2a, Gesims #e6d8b5, Ziegel #8a4a38", fenster="1.15 x 1.5 m, Achse 2.55 m, Geschoss 3.0 m, braune Läden",
  eg="Wohnnutzung, Hauseingänge", schrift="keine", details="Wandbild-Rückseite am Nachbarbau (Echse, Krake) nicht modelliert", nacht="Fenster 40 %"),
 "docks": dict(site="docks_langstrasse", name="The Docks (Langstrassen-Unterführung)", model="pipeline/landmarks/k4w4_docks.py", refs="Commons #16 #17 #18 (Moritz Twente)",
  masse="49 x 46 m (ID_FB9C1D94), Stufen 15.6 / 18.4 / 21.6 m, Mast 7 m", farben="Metallpaneele grau #9aa0a6, Bänder #7f858a, Rahmen #cfd3d6, Dachrand #6d7378", fenster="Bandfenster 2.0 x 1.35 m, Achse 2.4 m, Geschoss 3.4 m, vorspringende Geschossbänder",
  eg="verglaster Sockel mit dunkler Verkleidung", schrift="keine", details="Antennenmast und Technikaufbau auf dem Dach", nacht="Büros 40 %"),
 "swissmill_turm": dict(site="swissmill", name="Swissmill Tower (Getreidesilo)", model="pipeline/landmarks/k4w4_swissmill.py", refs="Mapillary #7 #1 #10 #14 #6 #12, Commons #16–#18",
  masse="52 x 33 m (ID_CCF8F166), Höhe 120.9 m über Sockel", farben="Sichtbeton #a9aaa5, Rahmen #7c7e80, Dachaufbau #7a7b78", fenster="schmale Schlitze 0.7 x 1.3 m, Achse 5.5 m, Geschoss 4.2 m (nur flach gezeichnet über 2 m)",
  eg="Sockel 6 m, Anlieferung", schrift="keine", details="Betonplatten-Raster, Maschinenhaus oben; teils mit Gerüst (nicht modelliert)", nacht="wenige Fenster hell (25 %)"),
 "stadtmuehle": dict(site="swissmill", name="Stadtmühle Swissmill (Altbau)", model="pipeline/landmarks/k4w4_swissmill.py", refs="Mapillary #7 #1 #14 #6 #10",
  masse="73 x 24.5 m (ID_32C9B073), Traufe 33.9 m, Walmdach 4.5 m", farben="Putz grauweiss #e2dfd4, Rahmen #f3f1ea, Dach #5b524a, Sockel #85796c, rote Backsteinteile (Staffelgiebel) nicht einzeln modelliert", fenster="1.1 x 1.8 m, Achse 2.5 m, Geschoss 3.4 m",
  eg="Sockelgeschoss 4.4 m mit Toren", schrift="«STADT MÜHLE» am Original senkrecht; nicht modelliert (Schrift zu fein)", details="Steg über die Limmat im Vordergrund nicht modelliert", nacht="Fenster 30 %"),
 "stjoseph": dict(site="st_joseph", name="Pfarrkirche St. Joseph", model="pipeline/landmarks/k4w4_stjoseph.py", refs="Mapillary #2 #11 #7 #6 #3, Panoramax #20",
  masse="44.7 x 28.4 m (ID_D9A9CD22), Traufe 11.5 m, First ca. 20 m, Turm 9 m im Quadrat, Spitze 47 m", farben="Putz cremeweiss #ece4d1, Fenstereinfassung #b9b4a6, Dach braun #584236, Kuppel #3a4642", fenster="Rundbogen 1.7 m breit, Brüstung 2.6 m, Kämpfer 7.6 m, Achse 5 m",
  eg="Haupteingang SW-Front, Vorplatz", schrift="Zifferblätter weiss mit schwarzen Zeigern", details="Zwiebelhelm, Chor mit Apsis, Fassadengiebel", nacht="Fenster warm 30 %"),
 "kw_letten": dict(site="kw_letten", name="Wasserkraftwerk Letten", model="pipeline/landmarks/k4w4_kwletten.py", refs="Commons #10 #9 #11, Mapillary #8 #5 #6",
  masse="50 x 38 m (ID_E365141C) Traufe 16.6 m und 58 x 23 m (ID_5701E4DB) Traufe 13.6 m, Walmdach 3.5 m", farben="Putz hellgrau #d6d8d3, Rahmen #e9e6dc, Backsteineinfassung #9a4a3a, Dach #6a6862", fenster="hohe Rundbogenfenster 1.6 x 5 m, Achse 4.4 m, Geschoss 7.6 m",
  eg="Maschinenhalle, Wehr/Rechen am Wasser nicht modelliert", schrift="keine", details="Baujahr 1892", nacht="wenige Fenster hell"),
 "james": dict(site="james_hochhaus", name="James Hochhaus", model="pipeline/landmarks/k4w4_james.py", refs="Mapillary #1 #3 #4 #0 #2, Commons #6 #7",
  masse="72 x 20 m (ID_C4B58043), Höhe 43 m, Sockel 6.6 m", farben="Paneele flieder #b4bcdc, Bänder #7e8ec4, Rahmen #f4f4f6, Sockel dunkel #2b2d33, Balkone gelb #e2be46 / grün #78aa78", fenster="Bandfenster 2.0 x 1.5 m, Achse 2.4 m, Geschoss 3.1 m",
  eg="dunkler Glassockel mit Läden", schrift="Hausnummer «40d» rosa am Sockel (nicht modelliert)", details="vorspringende Balkone in Farbe, Bambus-Hochbeete im Hof", nacht="Wohnfenster 45 %"),
}

for i, d in N.items():
    ph = M[d["site"]]["photos"]
    t = f"# {d['name']} ({i})\nTyp: landmark | Modell: {d['model']} | Fotos: {len(ph)} (Kontaktbogen preview/ref_v3_{d['site']}.jpg, Nummern = Index in photos_k4w4{'_zw' if i == 'zentralwaescherei' else ''}.json) | Quelle Geometrie: swissBUILDINGS3D + SWISSIMAGE\n\n"
    t += f"**Masse:** {d['masse']}\n**Farben (Hex):** {d['farben']}\n**Fensterraster:** {d['fenster']}\n**Erdgeschoss/Läden:** {d['eg']}\n**Schriften:** {d['schrift']}\n**Details:** {d['details']}\n**Nacht:** {d['nacht']}\n**Referenzfotos:** {d['refs']}\n"
    (R / f"{i}.md").write_text(t)

out = ["# Credits Foto-Recherche Welle 4 (k4w4)\n\nReferenzbilder nur zur Recherche (data/raw/photos/v3/), nicht für Spieltexturen. Mapillary: CC BY-SA 4.0, Namensnennung des Autors. Commons: Lizenz pro Datei. Panoramax: Lizenz pro Bild.\n"]
for sid, v in M.items():
    out.append(f"\n## {sid}")
    for k, p in enumerate(v["photos"]):
        out.append(f"- #{k} {p['source']} | {p['license']} | {p['author']} | {p['url']}")
(R / "CREDITS_k4w4.md").write_text("\n".join(out) + "\n")
print("notes", len(N))
