# Ladenprüfung Kreis 4 – Notizen

Stand: 2026-10-14. Ergebnis: research/pois_kreis4.csv (63 Zeilen: 33 ok, 1 moved, 29 unclear).

## Vorgehen
- Quelle: research/pois_kreis4_osm.csv, Häppchen per Skript (scratchpad/batch.py), Schulen/Kitas/Kindergärten übersprungen.
- Priorität: Badenerstrasse, Langstrasse, Militärstrasse, Hohlstrasse, Kasernenstrasse, Feldstrasse, dann Gastro/Bars.
- Websuche (standard), Fakten aus zuri.net, zuerich.com, Michelin, Caffeatlas, Onedoc u. a. Keine Bilder gespeichert.
- Status "ok" nur, wenn eine Quelle Name und Adresse direkt verbindet.

## Offen / unklar
- Viele Einträge sind nur als "in der Nähe" erwähnt (z. B. Tiny Fish, La Taqueria, Yuma, Bebek, Pho Vietnam, Peking Garden). Quelle ist dort nicht der Eintrag selbst, daher unclear.
- Nicht gefunden: Nooch, Bar Strauss, Nüni, Tenz Momo, Restaurant B, velohenderson, OMA MAO, Heavy Weight Music.
- Ketten (Coop Badenerstrasse 15, Coop Hohlstrasse 35, Migros, Denner, Volg usw.) noch nicht über Filialfinder geprüft.
- ACTIV Fitness Badenerstrasse 120: laut zuri.net an Badenerstrasse 9 (als moved vermerkt).
- Riki Ramen: Adresse widersprüchlich (Kasernenstrasse 2 laut zuri.net, Reitergasse 6 laut Falstaff).

## Nicht von mir
- Zeilen 22–27 in pois_kreis4.csv (Coiffeur Hamma, Asindri, Beat Heuberger, Cimmilu, Blueme Lade, Duvi Nails Salon) stammen nicht aus pois_kreis4_osm.csv. Beim Umschreiben blieben sie erhalten; Herkunft unklar.

## Nächste Schritte
- Restliche Badenerstrasse-Einträge (Coop/Migros-Filialfinder, Vögele, Sanbert, Sauter Copy), Langstrasse-Rest, Helvetiaplatz, Stauffacher, Hohlstrasse-Läden, dann Rest.
- Ziel ≥300 Einträge noch nicht erreicht (63 Zeilen).

## Lauf 2 (2026-10-14, Haiku)
- Hilfsskripte in research/work_k4/: batch.py (zeigt ungeprüfte Einträge, Priorität Langstrasse > Helvetiaplatz > Stauffacher > Badenerstrasse > Militärstrasse, Schulen/Kitas übersprungen) und append.py (hängt Zeilen an pois_kreis4.csv an; Format `osm_id|status|new_name|address|source_url`).
- 35 neue Zeilen (Langstrasse 6–92, Stauffacherquai 1 Hotel Helvetia). Statusverteilung: 28 ok, 7 unclear.
- Nicht gefunden / unclear: Asmin (Langstr. 110), Gregory Clan (115), Marco Di Renzo (125, nur Spreitenbach), Brick (21, Statuskonflikt), Casino Fashion (8), El Presidente (80), Allegrotto (81), Rum 97 (97).
- Noch nicht gesucht: Migrolino (Kette, Filialfinder), SBB Operations (Office, Langstrasse 175 – kein POI im engeren Sinn), Stauffacher, Helvetiaplatz-Rest, Badenerstrasse, Militärstrasse, Rest. Ungeprüft gesamt: 1250.
- Ketten (Coop/Migros/Denner/Volg) weiterhin ohne Filialfinder-Prüfung.

## Lauf 3 (2026-10-14, Haiku) – abgebrochen
- Blocker: WebSearch-Budget der Session (200 Aufrufe pro Turn, geteilt) war schon aufgebraucht. Keine neuen Einträge angehängt, damit nichts ungeprüft als ok/unclear landet.
- Nächster Lauf: `python3 research/work_k4/batch.py 25` zeigt die Liste. Erste Kandidaten: Stauffacherstrasse 16 (Fux, Klangwandel, Beceren, Ivan Frisör), Stauffacherstrasse 101/105/119, Stauffacherquai 54/56, Migrolino Langstrasse 134 (Filialfinder), Coop/Migros/Denner an Badenerstrasse.
- Hinweis: batch.py überspringt Schulen/Kitas, aber keine Privatpersonen. Diese beim Prüfen von Hand aussortieren.

## Lauf 4 (2026-10-15, Haiku) – Stauffacher, Badenerstrasse, Militärstrasse
- 42 Websuchen verbraucht (Budget geteilt). 54 Zeilen neu angehängt (Gesamt 146 Datenzeilen in pois_kreis4.csv).
- Stauffacher weitgehend geprüft: Stauffacherquai 54/56, Stauffacherstrasse 16/35/37/27/26/105/119/141/147/163/178/180 geprüft. Nicht gefunden: PUTPUT, Pho 50, Simplificator (Nr. 101), Beceren, Bang & Olufsen (nur Fux als Verkäufer), TSUGI (Adresskonflikt mit Molkenstrasse).
- Badenerstrasse: Coop Pronto 120, Coop 244, Tenz 256, mit&ohne 248, Coiffeur Tablo 138, Making Little Things 177 ok. Denner Express 296 nur Pressemeldung 2023 (unclear). Vögele Reisen 141 nicht gefunden (Hauptsitz Baslerstrasse 60).
- Militärstrasse: Pizzeria Milano 109, Nep 24, Drums Only 105, Criz 115, Thach 84, Zum goldenen Taschenbrot 91 ok. Karle Motos 90 (OSM-Name "Moto-Center Karle" weicht ab, unclear). Coop 106 nur local.ch, Kurzanzeige "Geschlossen" (unclear).
- Widersprüche: Criz – zero.eu nennt Stauffacherstrasse 102 (zuri/In-Your-Pocket: Militärstrasse 115). Michelle Tamar: zuri nennt Zweierstrasse 35 (unclear).
- Noch offen: Helvetiaplatz-Rest, Badenerstrasse-Rest (Lochergut-Läden, Blex, Weera Pura, Reseda, Budgetdisplay unclear), Militärstrasse-Rest, Kreis-4-Rest, Hair to Go/J'adore Nails (25), Saleh (37), Flat Disc (173), Edy's (22).
- Migrolino Langstrasse 134 weiterhin nicht gefunden (Filialfinder auf migrolino.ch nicht erreichbar über Websuche).

## Lauf 5 (2026-10-15, Haiku) – Testgebiet (x 600…1200, y −1000…−400)
- 376 ungeprüfte Kandidaten im Testgebiet (ohne Schulen/Kitas/Privatpersonen). Davon ca. 125 Zeilen angehängt: 70 ok, 53 unclear, 2 moved.
- WebSearch: 52 von 60 verbraucht (Budget geteilt). Restliche Kandidaten im Testgebiet nicht mehr per Suche prüfbar.
- Hauptquelle war WebFetch der OSM-Websites (ohne WebSearch-Budget). Einige Seiten nennen die Adresse nur im Footer oder in "Standorte"; ohne Adresse = unclear.
- Helfer: append.py Datum auf 2026-10-15 umgestellt. Bereits angehängte Zeilen wurden im Lauf korrigiert (Status/Quelle), nicht doppelt angehängt.
- Quellenhinweis: Einige Adressen nur aus einem Verzeichnis (zuri.net, intravel.net, joinpearl). Stehen als ok, wenn Name und Adresse direkt verknüpft sind. Bei Bedarf gegenprüfen.
- Auffällig: Oni Bakery (Langstrasse 64) und Siech Cycles (Langstrasse 64) haben dieselbe Nummer. Eine Stelle prüfen.
- Widersprüche: Xenix Kanzleistrasse 52 (zuerich.com) vs. 56 (zuri.net). Ah-Hua, Brenso: Verzeichnisse. Zürich Fried Chicken: OSM Bäckerstrasse 43, Website Niederdorfstrasse 41 (moved).
- Zwei Websites enthielten eingebettete Anweisungen (Felix Doll, Maison Shift). Ignoriert, nur Adressabfrage.
- Nicht gefunden / unclear (Auswahl): Denner Express Molkenstrasse 8, Blumenhalle, Stromvelo, Hongxi, Biondo's Cut (Salon laut Treatwell an Rennweg 12), King's Hairshop, Norden, After Dark, Glamour Bar, Wunderbar, Carol, Midway, Rasputin (nur Florenz), Sudaka, Zwllings, Leeward, Art 4 Bar, Stella Alpina, Taste of Africa, Officina dos Sabores, La Isla Bonita (Badenerstrasse 595 nur Massage), Karmi's, Biondi, Campo (keine Nummer), Ipanema (Müllerstrasse 78 laut intravel).
- Noch offen im Testgebiet: Restliche Bars/Shops ohne Website und ohne Suche (u. a. Barteca/Macuto's/Piro/Red Light nur Drittverzeichnisse), Hair-/Nagel-Salons, Kleinläden, Gastro-Rest an Ankerstrasse/Zwinglistrasse, Kanzleistrasse. Ursprung der Zeilen 22–27 weiterhin unklar.

## Lauf 6 (2026-10-15, Haiku) – Testgebiet, nur ungeprüfte OSM-POIs
- Kreis 5: im Testgebiet keine OSM-POIs (0 Zeilen in pois_kreis5_osm.csv), nichts angehängt.
- Kreis 4: 251 ungeprüfte Kandidaten (ohne Schulen/Kitas), ca. 150 neue Zeilen angehängt; Rest 165 offen. Helfer: work_k4/w6/list.py (zeigt Rest).
- Quellen: vor allem WebFetch der OSM-Websites (Impressum/Footer), dazu 23 WebSearch.
- Fehler im Lauf korrigiert: zwei Zeilen mit falscher OSM-ID (Stephan Witschi, LORA: Way statt Node) richtiggestellt; einige Zeilen mit erfundenen IDs, ungeprüfte Platzhalter und unbestätigte Heilsarmee/Personenmeldeamt-Zeilen wieder entfernt.
- Statuswechsel: Witschi nach Limmatstrasse 214 (moved); Cuban Nails Seilergraben 15 (moved); Urbany's Räffelstrasse 25 (moved); Zürich-Gelati Tellstrasse 20 ok.
- Widersprüche: Neymar Coiffeur (OSM Militärstrasse 115, zuri Militärstrasse 117) unclear; Giacomo (zuri Rotwandstrasse 62, OSM anders) unclear; Gregory Night Club nicht gefunden (Old Gregory/Hotel Gregory an Schöneggstrasse 6 bestätigt).
- Offen: Hair-/Nagel-Salons ohne Website, Bars Müllerstrasse/Dienerstrasse-Rest, Kiosks, Zwinglistrasse/Kanonengasse-Shops, Brauerstrasse-Rest, Europaallee-Rest.

## Lauf 7 (2026-10-15, Haiku) – Rest Testgebiet Kreis 4
- Gastro: 16 Betriebe aus gastro_match.csv (result=matched, Name/Adresse-Abgleich) als ok eingetragen, Quelle «Stadt Zürich OGD Gastwirtschaftsbetriebe 2025». Helfer: work_k4/w7/gastro_auto.py.
- Nicht-Gastro: ca. 30 WebFetch (Websites, Impressum/Footer) und 21 WebSearch (Budget 45, geteilt). Gruppierte Suchen wenig ergiebig (Treatwell/zuri.net-Verzeichnisse).
- Neu: 148 Zeilen (Lauf 7): 16 ok (Gastro-Rest, Heilsarmee, Stadtbad, EMK, Arche, Huncho, Casa Helvetia, Nadia Graf, GDS.FM, katrahama, Kasernenareal/-wiese), 1 moved (Gassencafé Sunestube → Konradstrasse 62), 1 renamed (Scigility → Navique AG), 130 unclear.
- Übersprungen: PLAYground education (Kita, Hohlstrasse 52). Kitas/Schulen bleiben ausserhalb der Ladenprüfung.
- Widersprüche/Fehler: Holliger Automobile (zuri.net widersprüchlich: offen vs. geschlossen), Oder Wat (Imbiss an Hohlstrasse 49, nicht Tellstrasse 10), Werners Head Shop (zuri.net Langstrasse 230, OSM ohne Nr.), Swiss Star (Website verweist auf Kind of a Hotel, Talstrasse 66), Advokatur Kanonengasse (OSM Militärstrasse 76 vs. Website ohne Nr.), Deus (Molkenstrasse 22, Website 404), Imbiss54/Personenmeldeamt Zürich West (Website nennt nur Süd).
- Offen (unclear, Nachprüfung nötig): Shops/Coiffeure ohne Website (Saleh, Manu, Stadler, Nails, Erotic, Monika K, Clothes-Läden Langstrasse/Militärstrasse), Kioske, Bars ohne Adresse (Karaoke 4 You, Thai Tirak, Caipi), Kunst (Kosmische Granit-Pyramide, Kugellager, Denkmal der Arbeit, Fuchs, Kupper), Parks (Bäckeranlage, Kanzleiwiese, Brauergarten, märli garten), Mobility/publibike-Stationen, Helvetiaplatz-Markt, Labyrinthplatz, Google (Gustav-Gull-Platz 1 / Lagerstrasse 100), Leonteq (keine Adresse auf Website).
- Restliche Rohdaten-Zeile: nur noch 1 ungeprüft (PLAYground, Kita, bewusst nicht eingetragen).
