# Ideen: «zürcherischer» und echter (Stadtkennerinnen-Blick Kreis 4/5)

Stand: 2026-10-16. Rolle: Stadtkennerin aus dem Kreis 4/5. Nur Ideensammlung, kein Code geändert.
Basis: gelesen wurden `CLAUDE.md`, `VISION.md`, `CONTENT_GUIDELINES.md`, `research/easter_eggs*.md`, `research/fidelity.md`, `research/furniture_facts.md`, Szenen- und Event-Daten (`pipeline/overrides/scenes_src.json`, `events.json`, `anecdotes.json`) und der Spielcode (Missionen, Sprechblasen, Audio). Gespielt wurde gegen die Live-URL (Screenshots `preview/ideas_zurich_1.jpg`: Langstrasse Fr 18:30, Kanzlei Sa 11:00, HB-Gleise Fr 17:30, Limmatplatz Mi 15:00, Hardbrücke Sa 20:00, Kanzlei).
Koordinaten = lokale Meter (x Ost, y Nord, Ursprung LV95 2681400/1248700). Aufwand: S = unter 1 h, M = ein Arbeitsschritt, L = mehrere Schritte. Risiko: Content-Risiko nach `CONTENT_GUIDELINES.md` (niedrig/mittel/hoch).
Quellenlage: «belegt» = Webquelle gefunden, «Erfahrungswissen» = vor Umsetzung gegenprüfen (Regel im Projekt: Fakten nur mit Quelle). Bereits vorhandene Szenen (Jass, Fondue, Stelzen, Boccia, Flohmarkt, Critical Mass, Besichtigungsschlange, Luxemburgerli, Böögg-Mini u. a.) werden hier nicht noch einmal vorgeschlagen.

## Top 10

| # | Idee | Aufwand | Risiko |
|---|---|---|---|
| 1 | Z01 Strassenschild-HUD statt «nächster spielbarer Ort» | S | niedrig |
| 2 | Z02 Sprechblasen mit Zürcher Alltagssätzen (Hochdeutsch-nah, Mundart-Option) | S | niedrig |
| 3 | Z05 Tram- und Tramhaltestellen-Durchsagen (eigene, neutrale Stimme/Text) | M | niedrig |
| 4 | Z10 Recycling-Sammelstellen und Züri-Kübel aus Open Data (ERZ) | M | niedrig |
| 5 | Z12 Letten im Sommer: Badegäste, Sprungturm, Flussschwimmen-Minispiel | M | niedrig |
| 6 | Z20 Christkindlimarkt im HB (Nov–Dez) | M | niedrig |
| 7 | Z18 Knabenschiessen-Chilbi (Sept., Albisgütli, Fahrgeschäfte als Kulisse) | M | mittel |
| 8 | Z03 «Fahndungsstufe» als Formular-Stapel statt GTA-Sterne und «Busse» | S | niedrig |
| 9 | Z27 Waschküche-Zettel-Quest (Waschplan, Hausordnung) | M | niedrig |
| 10 | Z14 Velovorzugsroute Altstetten–Kreis 4 als echte Velo-first-Strecke mit Tempo-Bonus | M | niedrig |

---

## A. Alltag und Szenen

**Z01 Strassenschild-HUD (Strassenname statt Platzname).** Das HUD oben links zeigt heute nur den nächsten «spielbaren Ort» (`map.nearestPlace`): am Limmatplatz, Stauffacher, Hardplatz und HB ist das Feld leer (Test per Teleport an Haltestellenkoordinaten). Ein Zürcher orientiert sich an Strassenschildern. Vorschlag: zweite Zeile mit dem Strassennamen der nächsten Strasse aus `vec.json`-Labels, im Stil des echten Strassenschilds (weiss/blau, Name plus Quartier und Postleitzahl, z. B. «Langstrasse · 8004 Zürich»). Ort: überall. Quelle: Stadt-Zürich-Schilder siehe `research/furniture_facts.md` Abschnitt 9. Aufwand S. Risiko niedrig.

**Z02 Sprechblasen mit Zürcher Alltagssätzen.** Heute (`main.ts`, `GREET_DAY/NIGHT`): «Grüezi!», «Hallo zusammen!», «Salü!», «Ciao!», «Gehen wir noch etwas trinken?», nachts «Guten Abend!/Gute Nacht!». Das klingt generisch (Hochdeutsch «Guten Abend» sagt in Zürich niemand). Vorschlag: Pools nach Ort und Zeit, kurze Fetzen: Feierabend Langstrasse «Chömed Sie no uf es Bier?» (nur wenn die Mundart-Entscheidung kippt), Hochdeutsch-nah: «Schönen Feierabend!», «Hast du Feuer?», «Das Tram ist wieder zu spät», «Ich muss noch zur Waschküche», «Hier ist die Wohnung schon vergeben», «Kommst du nach dem Flohmarkt zum Kafi?». Wichtig: Entscheid 2026-10-14 (UI Hochdeutsch) gilt. Mundart-Fetzen («Grüezi», «Merci vilmal», «Ä schööne», «hoi zäme», «Uf Wiederlose», «Es isch kalt») nur als Ausnahme für Sprechblasen, nach Rückfrage beim User. Aufwand S. Risiko niedrig (keine Stereotypen über Herkunft).

**Z03 «Fahndungsstufe» als Formular-Stapel.** Sterne (★) und CHF-Anzeige wirken wie GTA. Das Spiel hat mit «Formular-Büro: 47 Formulare in dreifacher Ausführung» schon die richtige Pointe. Vorschlag: Fahndungsstufe als wachsender Aktenstapel/Stempel-Symbol statt Sterne; Geld als «CHF» belassen, «Busse» in «Ordnungsbusse» ändern (Schweizer Begriff). Ort: HUD. Quelle: Projektinternes Konzept (`CONTENT_GUIDELINES.md`: Polizei comichaft). Aufwand S. Risiko niedrig.

**Z04 Feierabend an der Langstrasse (Zeitfenster Fr 17–20 Uhr).** In der Screenshot-Szene (Fr 18:30) ist die Strasse ruhig. Vorschlag: gestaffelter Feierabend-Strom (mehr Fussgängerinnen mit Rucksack/Laptoptasche aus Richtung Kreis 5/HB, Velopendler:innen dichter, Kioskschlange, Kebab-Take-away-Gruppe), Beizen-Terrassen füllen sich (Stühle besetzt) ab 17:30, Ladenschluss-Rollläden gegen 19 Uhr. Ort: Langstrasse (721, -790), Zeit Mo–Fr 17–20. Quelle: Erfahrungswissen. Aufwand M. Risiko niedrig.

**Z05 Tram- und Haltestellendurchsagen.** Es gibt Tramgeräusche, aber keine Ansagen. Vorschlag: im Tram-Radius kurze Textzeile («Nächste Haltestelle: Helvetiaplatz. Ausstieg links.») als Untertitel, plus optional synthetische Stimme (eigene, Web-Speech/TTS lokal erzeugt, nicht die VBZ-Stimme nachbauen). Im HB: Perron-Durchsage («Zürich HB, Gleis 7: Einfahrt IC … Bitte Vorsicht bei der Zugseinfahrt», als erfundene Zugnummern). Quelle: Echte Text-Formate müssen noch verifiziert werden (Suche lieferte keinen belegten Wortlaut) → Erfahrungswissen. Ort: Tramlinien 2/3/4/8/13/14, HB (1760, -650). Aufwand M. Risiko niedrig; keine echten Sprecher:innen verwenden.

**Z06 Tramklingel und Velokonflikte.** Fussgänger:innen reagieren auf das Tram-Klingeln (Schritt zurück, Blick); Spieler:in kann mit Velo klingeln (Taste), NPCs weichen aus. Ort: Tramgleise Langstrasse/Badenerstrasse. Quelle: Erfahrungswissen. Aufwand S–M. Risiko niedrig.

**Z07 Velopendler:innen im Berufsverkehr.** Morgens 7–9 und abends 17–19: Pulks an Ampeln (Hardbrücke-Rampe, Sihlquai, Langstrasse/Hohlstrasse), Anfahren bei Grün. Quelle: Kanton ZH: Veloverkehr seit 2015 rund +30 % (siehe `easter_eggs.md` 1.05). Aufwand M. Risiko niedrig.

**Z08 Kehrichtabfuhr mit Züri-Säcken.** Am Abend vor dem Abfuhrtag stehen blaue Säcke am Trottoir (grüne/blaue Säcke Stadt Zürich), morgens fährt ein ERZ-ähnliches Fahrzeug (fiktives Design, kein Original-Logo) und leert; Spieler:in darf Sack aufheben (Mini-Bonus). Der blaue Züri-Sack gilt seit 2023 (belegt: https://www.stadt-zuerich.ch/de/umwelt-und-energie/entsorgung/zueri-sack.html). Konkrete Gebühren nicht angeben (Suche lieferte keinen aktuellen Preis). Ort: Wohnstrassen Kreis 4/5. Aufwand M. Risiko niedrig.

**Z09 Brockenstube/Brocki als Quartiertreffpunkt.** Scenes kennen `brocki` schon. Ergänzung: Tisch mit «Zu verschenken»-Kiste am Trottoir (Zürcher Tradition, Erfahrungswissen) mit anklickbarem Fundstück («altes Radio, ein Gratis-Lampenschirm»). Ort: Kanzleiareal (706, -944), Hardstrasse. Aufwand S. Risiko niedrig.

**Z10 Recycling-Sammelstellen und Züri-Kübel aus Open Data.** Die Stadt führt ein Netz von 168 Sammelstellen für Altglas und Kleinmetall (63 unterirdisch; belegt: EU-Ausschreibung, https://op.europa.eu/en/web/public-procurement/procurement-details/-/procurement/c5ab7685-1565-4251-b719-ff07730ef346); ERZ-Datensatz «Kehrichtcontainer im öffentlichen Raum» (https://ckan.opendata.swiss/en/dataset/caa6e6e8-81e3-4099-b2b5-588bf0dda5cb). `furniture_facts.md` Abschnitt 13 sagt «nicht gefunden»: der Datensatz ist die Lösung. Im Spiel: Glascontainer an echten Standorten (Farbtrennung grün/braun/weiss ist Erfahrungswissen), Mini-Quest «Altglas wegbringen, aber erst nach 7 Uhr». Aufwand M (Pipeline-Schritt, Kachelbau). Risiko niedrig.

**Z11 Märkte: Wochenmarkt-Kulisse als echte Zeitfenster.** Der Wochenmarkt Helvetiaplatz steht schon in den Anekdoten; Ergänzung: Marktstände mit Zürcher Waren (Gemüse, Käse, Blumen), Zeitfenster per Kalender wie `events.json`. Vor Umsetzung Marktzeiten aus `stadt-zuerich.ch` verifizieren (nicht eigens geprüft). Aufwand M. Risiko niedrig.

**Z12 Letten im Sommer.** Flussbad Unterer Letten (1909, älteste Flussbadi Zürichs, Holzbau, 1986 als schützenswert eingestuft, ca. 100 m Schwimmkanal in der Limmat, 3-m-Sprungturm/-brett, Eintritt frei; belegt: https://www.zuerich.com/de/besuchen/natur/flussbad-unterer-letten und https://www.badi-info.ch/Unterer_letten.html). Saison 2026: 9. Mai bis 20. September. Vorschlag: Badegäste auf Wiese und Steg Mai–September, Handtücher auf dem Rasen, Flussschwimmen als Minispiel (Strömung, Ausstieg am Rechen), nach Saisonende (Oktober) Absperrung/leeres Becken als Jahreszeiten-Detail. Ort: Wasserkraftwerk Letten (1215, 352). Aufwand M. Risiko niedrig (keine Drogenszene-Anspielung, siehe `easter_eggs.md` 4.07/4.08: nur sachlich).

**Z13 Street-Parade-Nachwehen (Sonntag nach der Parade, August).** Am Morgen danach: Konfetti-Reste, Absperrgitter, leere Becher, Stadtreinigung, müde Gruppen mit Neon-Armbändern. Ort: Limmatquai-Umfeld ausserhalb Spielgebiet, aber in Kreis 4/5 Zugang/Heimweg (Langstrasse, Hardbrücke). Quelle: Chronik https://www.swissinfo.ch/eng/culture/how-the-street-parade-shook-up-zurich/30868098 (siehe `easter_eggs.md` 3.12). Aufwand M. Risiko niedrig (kein Drogenbezug).

**Z14 Velovorzugsroute Altstetten–Kreis 4.** Die Stadt eröffnete 2023 diese Velovorzugsroute als Alternative zu Badener- und Hohlstrasse mit breiten Velostreifen, Tempo 30, Vortritt, Einbahnabschnitten und klarer Markierung (belegt: https://www.stadt-zuerich.ch/de/aktuell/medienmitteilungen/2023/03/230309a1.html). Im Spiel: Route als eigene, erkennbare Strecke (Boden-Piktogramm «Velo» in Grün/Blau), Velo-Geschwindigkeitsbonus, Quest «Velokurier» darauf routen. Geplante Franca-Magnani-Brücke (zwischen Kreis 4 und 5, laut VCS-Jahresbericht) nur als Bauschild, nicht als Fakt hinstellen. Ort: siehe `veloinfra.json`. Aufwand M. Risiko niedrig (Wahlthema Verkehr, aber sachlich).

**Z15 Brunnen mit Trinkwasser aktiv nutzbar.** Zürich hat über 1200 Brunnen (https://www.zuerich.com/de/besuchen/brunnenstadt-zuerich). Spiel: Brunnenstellen aus Open Data; Wasser trinken heilt Ausdauer/«Hitze» im Sommer, Hunde trinken, Kinder planschen. Dazu Schild «Trinkwasser» vs. «Kein Trinkwasser» (nur wo belegt). Aufwand S–M. Risiko niedrig.

**Z16 Hundespaziergang mit Robidog-Spender.** Robidog-Stationen sind in `furniture_facts.md` Abschnitt 4 bereits belegt. Szene: Hundehalter:in zieht Sack, wirft ihn in Station. Quelle: ebd. Aufwand S. Risiko niedrig.

**Z17 Kiosk als Nachbarschaftsinstitution.** Scenes enthalten `kiosk`. Ergänzung: Kiosk mit Zeitungsständer (fiktive Titel), Lottoscheine, Mineralwasser, Öffnung bis spät; Dialog-Fetzen: «Zwei Gipfeli, bitte». Konkrete Kiosk-Ketten nur als neutrale Fassade. Aufwand S. Risiko niedrig.

## B. Kalender und Jahreszeiten

**Z18 Knabenschiessen-Chilbi.** Albisgütli, Mitte September (2026: 12.–14. Sept.; nächster Termin 11.–13. Sept. 2027), Tradition seit 1656 erwähnt, heutige Form seit 1899, Mädchen seit 1991 (belegt: https://www.zuerich.com/de/besuchen/knabenschiessen und https://www.guidle.com/de/veranstaltungen/zuerich/knabenschiessen-eine-zuercher-tradition_AQh7NMY). Spiel: Jahrmarktkulisse (Riesenrad, Lebkuchenherzen, Zuckerwatte); **kein Schiessen als Spielmechanik** (Leitplanke Gewalt, Name irreführend: kurzer Hinweis «hier wird nicht auf Jungen geschossen»). Eher Ambient/Anekdote als Quest. Ort: Albisgütli (liegt ausserhalb des Spielgebiets; als Horizont-Kulisse oder Toast-Text). Aufwand M. Risiko mittel (Waffenthema, nur Kulisse und Chilbi).

**Z19 Sechseläuten-Rauch (Kalender April).** Ausserhalb Spielgebiet (Sechseläutenplatz, Kreis 1), aber sichtbar: schwarzer Rauch/Böögg-Silhouette am Horizont, Zünfte-Reiter am Montag nach der Tagundnachtgleiche (Erfahrungswissen: Montag im April; Wetter-Orakel: schneller Knall = guter Sommer). Quelle: https://www.zuerich.com/de/wer-ist-der-boeoegg. Aufwand S (Toast) bis M. Risiko niedrig.

**Z20 Christkindlimarkt im HB.** Hauptbahnhof-Halle, ca. 140 Holzchalets, Tannenbaum mit Swarovski-Kristallen (Angaben schwanken: 10–15 m, ca. 7000 Kristalle); 2025 vom 20. Nov. bis 24. Dez.; Eintritt frei (belegt: https://www.freizeit.ch/kalender/19491/christkindlimarkt-im-hauptbahnhof-zurich). Spiel: Halle mit Chalets, Glühweindampf, Lichterketten vom 20. Nov. bis 24. Dez., HB-Innenraum-Landmark liegt bei (1760, -650). Achtung: Sponsor-Logos weglassen. Aufwand M. Risiko niedrig.

**Z21 Weihnachtsbeleuchtung «Lucy» (Kreis 1, Verweis).** Siehe `easter_eggs.md` 3.17: in Kreis 4/5 nur Fenster-Lichterketten, Sterne in Seilleuchten (Seilleuchten sind belegt, `furniture_facts.md` Abschnitt 2). Aufwand S. Risiko niedrig.

**Z22 Räbeliechtli-Umzug (November).** Kinder tragen ausgehöhlte Zuckerrüben mit Kerzen durch die Strassen und singen; Brauch in vielen Kantonen, Ursprung unklar (belegt: https://famigros.migros.ch/de/ausfluege-und-freizeit/feste-und-saisonales/raebeliechtliumzug). Konkrete Kreis-4-Umzüge nicht belegt: als allgemeiner Quartierbrauch ohne Ortsbehauptung darstellen (z. B. beim Kanzlei-Schulhaus). Szene Anfang/Mitte November, Dämmerung. Aufwand M. Risiko niedrig (Kinder nur Silhouetten, nicht als Quest-Ziel).

**Z23 Silvester.** Silvesterraketen/Feuerwerk über der Stadt 23:30–00:30 am 31. Dezember (Skybox-Effekt), Strassen voller, Sektflaschen; Hinweis auf geltende Regeln nur nach Quelle prüfen (nicht recherchiert). Aufwand S–M. Risiko mittel (Feuerwerk/Alkohol: keine Anreize, keine Knallkörper gegen Menschen).

**Z24 Zürifäscht (alle drei Jahre).** Grosse Stadtfest-Kulisse mit Feuerwerk; Jahrgang (2023, 2026) muss verifiziert werden, nicht recherchiert → «prüfen». Ort: Seebecken, ausserhalb. Nur als Kalender-Toast und Horizont-Feuerwerk. Aufwand S. Risiko niedrig.

**Z25 Laub und Herbst als Spielmotiv.** Der Herbst ist gewollt (fidelity S8). Ergänzung: Laubbläser:innen (gelbe Westen) am Morgen, Laubsäcke am Trottoir, Kastanienverkäufer am HB (Marroni-Stand, Erfahrungswissen; Marroni-Stand ist ein klassischer Zürcher Wintergeruch). Aufwand S–M. Risiko niedrig.

## C. Institutionen, Alltag zu Hause

**Z26 Quartiertreff / Gemeinschaftszentrum als Ort.** Kein Name wurde im Web gefunden (Suche liess offen); Recherche nötig (stadt-zuerich.ch, Stiftung Gemeinschaftszentren). Vorschlag nach Verifikation: Treffpunkt mit Anschlagbrett («Repair-Café Samstag», «Zumba für alle», «Kinderkleiderbörse»). Ort: Kreis 4/5, TBD. Aufwand S nach Recherche. Risiko niedrig.

**Z27 Waschküche-Zettel-Quest.** Waschplan mit Namensschildern, Zettel «Bitte Flusen entfernen» an der Maschine, Tauschgespräch «Du hast meinen Slot». Mini-Quest in einem Mehrfamilienhaus (Innenraum nur als Quest-Raum, erlaubt laut `VISION.md`), Ort: Kalkbreite oder Egli-Siedlung (400, -1209). Echte Regeln und Mietrecht nicht recherchiert (Suche lieferte nichts für Zürich) → nur humorvoll, ohne Rechtsaussagen. Aufwand M. Risiko niedrig.

**Z28 Hausordnung und Ruhezeiten.** Schild im Treppenhaus «Ruhezeiten: 12–13 Uhr, 22–7 Uhr» (Erfahrungswissen, Zeiten variieren je Haus und nicht belegt → «prüfen»). Als Humor-Ambient, kein Fakt. Aufwand S. Risiko niedrig.

**Z29 Altglas nur werktags.** Sprechblase vor Glascontainer: «Nicht nach 20 Uhr!» (Regel nicht belegt → erst verifizieren, ERZ-Seite). Aufwand S. Risiko niedrig.

**Z30 Kulturorte als echte Kulisse.** Xenix (Kanzlei), Volkshaus, Schiffbau, Zentralwäscherei/Neue Hard, Rote Fabrik (Kreis 2, Verweis): kleines «Heute»-Plakat am Eingang mit erfundenem Programmtitel. Echte Programme nicht ohne Freigabe (`research/posters/README.md`). Aufwand S–M. Risiko mittel (nur echte vergangene Events mit Freigabe).

## D. Details, die Einheimische sofort erkennen

**Z31 Blaue Zone mit Parkscheibe.** Autos in blauen Zonen haben Parkscheibe im Fenster (Erfahrungswissen); Politesse-Figur schreibt Busse (nicht Polizei). Ort: blaue Parkfelder (`traffic_signs._blue_zone_signs`). Aufwand S–M. Risiko niedrig.

**Z32 Tramhaltestellen-Details.** Billettautomat (ZVV, orange/blau), Fahrplan-Aushang, Bank mit Werbung, Dynamische Anzeige «2 | Tiefenbrunnen | 3 min». Quelle: `furniture_facts.md` Abschnitt 7. Aufwand M. Risiko niedrig (keine Original-Logos kopieren).

**Z33 Plakatsäulen mit Zürcher Kulturplakaten.** Litfasssäulen mit eigenen, fiktiven Plakaten (Konzert, Filmfestival, Theater), Quelle: `furniture_facts.md` Abschnitt 8. Aufwand S. Risiko niedrig.

**Z34 Spielplatz-Schilder, Sandkasten, Planschbecken.** Planschbecken sind bereits in den Szenen (Bäckeranlage, Josefwiese, Bullingerhof). Ergänzung: saisonal (Mai–September gefüllt, im Oktober leer, wie heute der Herbst) – sichtbare Jahreszeit. Aufwand S. Risiko niedrig.

**Z35 Velo-Abstellplätze an Cafés: Velos mit Kindersitz, Lastenvelo, Anhänger.** Fidelity S9 hat Veloparkplätze; ergänze Variation (Kindersitz, Körbe, Schloss-Kabel, Veloanhänger «Chinderwage»). Aufwand S. Risiko niedrig.

**Z36 Geschäfte mit korrekter Schreibweise und Mischformen.** Beizen-Namen und Schilder: «Metzgerei», «Coiffeur», «Dönerbude», Brocki, Apotheke mit grünem Kreuz, Migros/Coop-Fassade neutral. Passt zu CLAUDE.md-Regel «neutrale Fassade». Aufwand S. Risiko niedrig.

## E. Klänge und Sprache

**Z37 Kirchenglocken und Uhrzeit-Zusätze.** Kirchenglocken zur vollen Stunde sind bereits in `audio_amb.ts`. Ergänzung: Viertelstunden-Schläge (hell/dunkel), um 7 Uhr/Samstag 17 Uhr Einläuten des Sonntags (Erfahrungswissen, Brauch nicht überall → «prüfen»). Aufwand S. Risiko niedrig.

**Z38 Stadtklang-Fetzen: Radio im Kiosk, Strassenmusik, Mundart-Hip-Hop.** `easter_eggs.md` 1.11 und 1.20 beschreiben das; Musik und Radio nur mit eigener Produktion (Lizenz). Aufwand M. Risiko niedrig.

**Z39 «Hoi, hoi» als Fussgängerinnen-Gruss mit Velo-Klingel-Antwort.** Mikro-Interaktion: Taste «Grüssen» löst Antwort aus (siehe Z02). Aufwand S. Risiko niedrig.

**Z40 Zugsdurchsagen am Bahnhof Hardbrücke/Altstetten.** Gleise und Perrons sind schon modelliert (Landmarks «Perrons Zürich Hardbrücke»). Textzeile und Gong beim Zugseinlauf, kein Original-SBB-Jingle (Urheberrecht). Aufwand M. Risiko niedrig.

## F. Mini-Quests und Satire (Politik nur über den User)

**Z41 Quest «Nachbarschaftsfest» statt reinem Flyer verteilen.** Der heutige Flyer-Quest nennt die AL ausdrücklich («Flyer der Alternativen Linken»). Sozial-politisch sinnvoll, aber als Spielinhalt trocken. Stattdessen/zusätzlich: Hof-Fest organisieren (Sitzbänke tragen, Girlande aufhängen, Bewilligung holen = Formular-Gag). Botschaft liefert der User (TODO-PROGRAMM). Aufwand M. Risiko mittel (Parteibezug nur durch den User).

**Z42 Quest «Wohnung ergattern» (Zufallsgenerator).** Echte Idee aus der Presse (Zufallsgenerator für Besichtigungen, blue News Juni 2025; siehe `easter_eggs.md` 3.01). Die Mission «Wohnungsbesichtigung» existiert; Ausbau mit Würfelmechanik und «Nummer 147»-Pointe. Aufwand S–M. Risiko niedrig.

**Z43 Fiktive «Event-Konzern»-Plakatwand ersetzen statt zerstören.** Die Leitplanke «offener Entscheid» nennt Alternativen zur Zerstörung (übermalen, begrünen). Vorschlag: Spielmechanik «Plakat überkleben mit Quartierkunst» (Stempel), wirkt zürcherisch (Wildplakat-Kultur) und umgeht Sachbeschädigung. Aufwand M. Risiko mittel (Leitplanken).

---

## Fehler und Unstimmigkeiten im aktuellen Spiel

Stand: Live-Version vom 2026-10-16. Koordinaten in lokalen Metern.

| # | Befund | Ort | Vorschlag | Status |
|---|---|---|---|---|
| F1 | HUD-Platzname leer an den meisten Knoten (Limmatplatz, Stauffacher, Hardplatz, Escher-Wyss-Platz, HB, Schmiede Wiedikon, Löwenbräu, Schiffbau): `nearestPlace` kennt nur «spielbare Orte». | Limmatplatz (1131, 74), Stauffacher (991, -1182), Hardplatz (-102, -206) | Z01 | erledigt: Locator (square/hub/Strasse) in main.ts, Daten districts.json |
| F2 | Mehrere Anekdoten teilen exakt dieselbe Koordinate (721, -790): a0, a1, a3, a4, a6, a9, a26, a39–a42 (gut 10 Stück). Weil nach jeder Anzeige 25 s Pause gilt, laufen sie hintereinander ab und wirken wie Spam. Zudem sind Ole-Ole-Texte an einem Strassenpunkt statt an der Bar (Landmark «Ole Ole Bar (Langstrasse 138)» steht bei (870, -445)). | (721, -790) vs. (870, -445) | Anekdoten auf echte Adressen verteilen (`anecdotes.json`) | erledigt: Overrides pipeline/overrides/anecdote_places.json, geteilte Punkte werden verworfen |
| F3 | Anker «Olé Olé» liegt rund 400 m von der als Landmark modellierten Bar entfernt (siehe F2); eines von beiden stimmt nicht. | (721, -790) und (870, -445) | Landmark-Position prüfen (Adresse Langstrasse 138) | geprüft: kein Fehler. OSM-Adresse Langstrasse 138 (869,-441) = Landmark (870,-445); der Anker (721,-790) war falsch und ist ersetzt |
| F4 | Begrüssungs-Sprechblasen generisch/unzürcherisch: «Guten Abend!», «Gute Nacht!», «Ciao!», «Gehen wir noch etwas trinken?». | `main.ts` GREET_* | Z02 | erledigt: web/src/ui/chatter.ts, Hochdeutsch nach Ort/Zeit, keine Mundart |
| F5 | HUD wirkt amerikanisch: Sterne für Fahndung, Geldanzeige als Spielgeld wie in GTA; «Busse» statt «Ordnungsbusse». | HUD oben rechts | Z03 | offen (HUD Z03, nicht in meinen Dateien) |
| F6 | Beim Test an HB-Koordinaten (1640, -640) landet die Kamera in den Gleisen; für Neu-Spieler:innen nicht zugänglich (kein Fehler, aber erster Eindruck «Rohbau»). | (1640, -640) | Spawn nicht auf Gleisfeld (`findSpot` greift nur ohne `exact`) | offen (Spawn/findSpot) |
| F7 | Kamera am Hardbrücke-Standpunkt blickt auf eine einfarbige violette Fläche (Pfeiler/Unterseite) ohne Details. | (-106, -101), Sa 20:00 | Landmark-Thema, siehe fidelity S13 | offen (Landmark-Thema) |
| F8 | Kreis-Label am Bahnhof Hardbrücke: HUD meldet «KREIS 4 · AUSSERSIHL» an (56, 118). Der Bahnhof Hardbrücke wird in der Regel dem Kreis 5 (Industriequartier) zugerechnet (nur Erfahrungswissen, per Adresse 8005 prüfen). | (56, 118) | Kreispolygon an dieser Stelle prüfen | geprüft: kein Fehler. Offizielles Stadtkreis-Polygon (OGD) liegt (56,118) in Kreis 4; HUD jetzt «KREIS 4 · LANGSTRASSE» aus Quartier-Polygonen |
| F9 | Flohmarkt Kanzlei (Sa 8–16 Uhr) war im Test (Sa 11:03, 5 s nach dem Laden bei (690, -930)) kaum sichtbar: wenige Personen, keine Stände im Bild. Eventuell Streaming-Verzögerung oder Kamerawinkel. | (676, -958) | Test mit längerer Wartezeit wiederholen | erledigt: Flohmarkt auf freie Fläche (672,-955), Bau erst bei Nähe (<170 m, 1.2 s Wartezeit für exakte Tile-Höhen), 20 Stände/28 Leute |
| F10 | Kanzleiareal-Platz auf Screenshot grosse leere Asphaltfläche, nur zwei Bänke; wenig Alltagsdetails (Velos, Tische, Pflanzen). | (700, -940) | Z09, Z35 | offen (Z09/Z35) |
| F11 | Strassennamen in Kartendaten mit OSM-Schreibweise: «Huebweg», «Schwerzgruebstrasse», «Bernhard-Jaeggi-Weg», «Kalkbreite/Bhf. Wiedikon». Amtliche Schreibweise (Stadt Zürich) wird bei ä/ö/ü teils mit Umlaut geführt: bitte gegen das Strassenverzeichnis prüfen (nicht verifiziert). Haltestellenname «Bhf.» mit Punkt sollte VBZ-konform «Bahnhof Wiedikon» heissen, falls ausgeschrieben. | Karte, `vec.json` | Mit Strassenverzeichnis der Stadt abgleichen | offen (Schreibweise gegen Strassenverzeichnis) |
| F12 | Landmark-Namen im Code mit «ue/ae/oe»-Ersatz («Kirche Buehl», «Roentgenplatz», «Bezirksgebaeude»). Nur Intern-IDs; falls irgendwo sichtbar: Umlaute verwenden. | `landmarks.json` | Anzeige-Namen prüfen | offen |
| F13 | Letzigrund: Stadion liegt laut Quartierspiegel in Altstetten (Kreis 9), das HUD stimmt dort. Das Tram-Halt «Letzigrund» an der Badenerstrasse liegt aber in Kreis 4, deshalb steht dort «KREIS 4 · AUSSERSIHL»: kein Fehler, nur missverständlich bei «Letzigrund». | (-971, -335) vs. (-969, -166) | kein Eingriff, nur beachten | kein Eingriff (Quartier-Polygone zeigen jetzt «Hard»/«Altstetten» korrekt) |
| F14 | Debug-Zeile («60 fps · 464 calls …») war mit `&debug` sichtbar; in der Produktion bitte ohne Parameter nicht anzeigen (nur zur Kontrolle). | HUD unten | prüfen | geprüft: Zeile nur mit &debug (body.debug), kein Fehler |

---

## Quellenverzeichnis (neu gesucht, 2026-10-16)

- Züri-Sack (blau seit 2023, 10-l-Sack): https://www.stadt-zuerich.ch/de/umwelt-und-energie/entsorgung/zueri-sack.html
- Knabenschiessen: https://www.zuerich.com/de/besuchen/knabenschiessen
- Räbeliechtli allgemein: https://famigros.migros.ch/de/ausfluege-und-freizeit/feste-und-saisonales/raebeliechtliumzug
- Christkindlimarkt HB: https://www.freizeit.ch/kalender/19491/christkindlimarkt-im-hauptbahnhof-zurich
- Flussbad Unterer Letten: https://www.zuerich.com/de/besuchen/natur/flussbad-unterer-letten, https://www.badi-info.ch/Unterer_letten.html
- Velovorzugsroute Altstetten–Kreis 4 (2023): https://www.stadt-zuerich.ch/de/aktuell/medienmitteilungen/2023/03/230309a1.html
- Sammelstellen Altglas/Kleinmetall (168, davon 63 unterirdisch): https://op.europa.eu/en/web/public-procurement/procurement-details/-/procurement/c5ab7685-1565-4251-b719-ff07730ef346 ; ERZ-Open-Data: https://ckan.opendata.swiss/en/dataset/caa6e6e8-81e3-4099-b2b5-588bf0dda5cb
- Letzigrund in Altstetten: https://zop.zb.uzh.ch/bitstreams/5f5d18ba-6366-4812-9ba8-1293e7e0cbbe/download
- Nicht gefunden (bleiben «Erfahrungswissen/prüfen»): Tramdurchsage-Wortlaut, Waschküchen-/Hausordnungs-Regeln Stadt Zürich, Glas-Einwurfzeiten ERZ, Zürifäscht-Termine, Gemeinschaftszentrum Kreis 4/5.
