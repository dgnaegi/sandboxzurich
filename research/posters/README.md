# Wildplakat-Events: Faktenbasis

`events.json` enthält 254 vergangene Zürcher Kultur-Events (2022–Anfang 2026) als reine Fakten für selbst gestaltete Wildplakate. Es wurden keine Plakatbilder geladen. `raw/` hält die gecachten Rohdaten. `build_events.py` baut die Datei reproduzierbar (Auswahl und Flags stehen dort im Dict `RF`).

Schema: id, title, subtitle, date, time, venue, address, kind, lineup, price, organizer, source_url, political, approval_needed. Zusatz: note, dates (weitere Spieltermine).

## Methode und Quellen
- **Rote Fabrik** (96 Events): öffentliche Kalender-API der Website (`https://kalender.rotefabrik.ch/api/events?from=YYYY-MM-DD&to=YYYY-MM-DD`), Jahre 2022–2025 komplett in `raw/rf_*.json` gecacht. Preise stammen aus dem Feld `price_label`; wo dort kein Betrag steht, ist `price` null. Lineups: aus Titel/Beschreibung, bei Festivals nur teilweise (sonst Festivalname).
- **Helsinki Klub** (22), **Jugendkulturhaus Dynamo** (9), **Gessnerallee** (4): nur aktuelle Programmseiten sind live, deshalb aus Wayback-Machine-Snapshots der Programmseiten (URL in `source_url`). Jahr wurde aus Snapshot-Datum abgeleitet, bei Gessnerallee per Wochentag geprüft. Uhrzeiten bei Dynamo unzuverlässig (null). Preise dort nicht angegeben.
- Datum lokal (Europe/Zurich) aus UTC-Feld umgerechnet.

## Offene Punkte / nicht gefunden
- **Nicht abrufbar** (JS-Seiten, TLS-Fehler oder nur Zukunftsprogramm): Xenix, Riffraff/Houdini, Theater Neumarkt, Helmhaus, Photobastei, Kanzlei, Zukunft, Exil, Bogen F, Plaza, Mascotte, Kauz, Klaus, Gonzo, Kasheme, Moods, Sender, Provitreff, Kasernenareal. Xenix-Events kommen nur indirekt über die Orient Express Filmtage (Rote Fabrik). Das Shedhalle-Programm ist über die Rote-Fabrik-API abgedeckt.
- **«Kino Houdini Openair»** existiert nach Recherche nicht (Houdini ist ein Innenkino in der Kalkbreite). Stattdessen Freiluftkino Rote Fabrik (`rf-3247`).
- **Langstrassenfest**: letzte Ausgabe 2010 (Wikipedia), also kein Event im Zeitraum. **Kreis-4-Fest / Bullingerfest**: keine belegbaren Daten 2022–2026 gefunden. Europaallee-Fest weggelassen (Immobilien-Marketing).
- **Kampfsport-Benefiz**: Websuche ergab nichts für Zürich. Nicht erfunden. `rf-4342` (Boykott Fussball-WM Katar) ist der einzige Sport-Eintrag.
- Zürich Pride: nur Rahmenanlässe in der Roten Fabrik (After-Party 2024, CSD-Soli-Partys). Pride-Demo-Daten nicht separat belegt.
- Preise fehlen bei den meisten Einträgen; für Plakate frei wählbar oder in der Quelle nachprüfen.
- Bewusst **weggelassen**: «Newborn Sky: Women in the Democratic Army of Rojava» (2022-03-17; Nähe zu Gruppen, die teils als terroristisch eingestuft werden), «Rote Kulturtage» (2025, Beteiligung echter Parteien, verletzt CONTENT_GUIDELINES). Keine Markenkonzerte oder Sponsoren-Events.
- Rote Fabrik ist eine reale Institution und kann als Kulisse genannt werden. Namen von Künstler:innen sind öffentliche Auftritte; vor Druck im Spiel trotzdem fiktive Plakate ohne Fotos/Logos gestalten.

## Runde 2 (127 zusätzliche Events, 11 weitere Lokale)
Neu: Gessnerallee 27 (davon 4 aus Runde 1), Moods 17, Hive Club 15, Palais Mascotte 14, Kino Xenix 13 (+3 Xenix Bar), Photobastei 10, Kanzlei Club 9, Plaza Klub 9, Theater Neumarkt 8, Bogen F 1, Provitreff 1. Erzeugt von `build_events2.py` (aufgerufen aus `build_events.py`), alle Einträge werden gegen die gecachten Rohdaten geprüft (Assertions, Wochentag-Abgleich für das Jahr).
- **Gessnerallee**: öffentliche CMS-GraphQL-API (`cms.gessnerallee.ch/graphql`), 461 Events 2024–2026 in `raw/gessnerallee.json`; 23 ausgewählt. Talks zu Politik/Recherche-Kollektiven bewusst ausgelassen.
- **Palais Mascotte**: Nunight-Widget-API (`event_widget_details.jsonp?id=N`), IDs 1–215 in `raw/mascotte/`. Nur Clubabende 2026 (neu eröffnet Jan 2026). Firmenanlässe weggelassen.
- **Kino Xenix**: eigene Monats-JSONs (`static/json/*.json`) in `raw/xenix/`, 2022–2026. Auswahl: Open-Air-Reihe, Gäste-Abende, Bar-Konzerte.
- **Moods, Theater Neumarkt, Photobastei, Kanzlei, Plaza, Hive**: Wayback-Snapshots der Start-/Programmseiten (Text in `raw/wayback/<venue>/<timestamp>.txt`, Snapshot-URL in `source_url`). Jahr per Wochentag-Abgleich.
- **Bogen F, Provitreff**: aktuelle Website (je 1 vergangener Anlass). Provitreff: Adresse nicht auf der Seite, daher null.
- Preise nur wo Quelle sie nennt (Plaza, Bogen F, Mascotte teils).
- Zusätzlich `approval_needed`: `pb-2025-11-06-45JahreJug` (Ausstellung Jugendunruhen, okaj zürich). Insgesamt jetzt 16.

### Nicht erreicht
- Ziel waren ≥12 neue Lokale, erreicht sind 11. Nicht verwertbar: Zukunft (Domain verkauft), Exil (Seite weg), Klaus, Gonzo, Kasheme, Sender, Kauz (keine Programmseiten/Archive auffindbar), Helmhaus und Shedhalle-Website (JS-Seiten ohne Archiv; Shedhalle-Programm steckt in der Rote-Fabrik-API), Kaufleuten (Startseite ohne Events), Volkshaus (keine Programmdaten), Kulturhaus Helferei (JS), Petzi (nur Landesübersicht, kaum Zürich), Zürcher Theater Spektakel (keine Daten im Archiv, Daten nicht erfunden).
- Quartierfeste Kreis 4/5, Kreis-4-Fest, Bullingerfest, Langstrasse Kultur, Flohmarkt Kanzlei: keine belegten Termine gefunden.
- Mascotte, Neumarkt und Gessnerallee liegen im Kreis 1, Photobastei und Hive im Kreis 5. Schwerpunkt Kreis 4/5 daher nur teilweise: Kanzlei, Xenix, Plaza, Hive, Moods, Bogen F, Provitreff.

## approval_needed (Begründung)
Alle Einträge unten sind `political` und/oder Soli-Anlässe mit Trägerschaft, die vor Verwendung geprüft und freigegeben werden müssen. Kein Event nennt Parteien oder Politiker:innen.

- `rf-3611` 2022-02-10 Golden Dawn - A Public Affair (film): Doku zum Golden-Dawn-Prozess, Filmabend mit Podium
- `rf-3485` 2022-05-21 Wir haben noch nicht vergessen: SOLI FÜR AFGHANISTAN (political): Soli für Afghanistan: humanitärer Anlass, Trägerschaft in Quelle nicht benannt
- `rf-4083` 2022-07-30 ROTA (political): Soli von und für ROTA, Selbstorganisation von MigrantInnen v.a. aus Türkei/Kurdistan und Naher Osten; Verbindungen/Positionen vor Verwendung prüfen
- `rf-4342` 2022-11-16 Boykott Fussball-WM 2022 Katar (sport): Boykott Fussball-WM 2022 Katar, Film/Podium, fussballpolitisch
- `rf-4617` 2023-05-19 Soliparty feministischer Streik 23 (political): Soliparty zum feministischen Streik
- `rf-4601` 2023-06-24 CSD ZUREICH (political): Soliparty zur Demo «CSD Zureich» (queere Demo, antikapitalistisch)
- `rf-4772` 2023-07-28 DACHSBAU KONZERTE & SOLI PARTY FÜR BEN48 (benefit): Konzerte & Soli-Party für «BEN48»: Zweck in Quelle unklar, prüfen
- `rf-5389` 2024-04-26 Solidarity Rising (political): Info-Anlass Westsahara (Velo-Weltreise, SUKS)
- `rf-5139` 2024-06-22 CSD soliparty (political): CSD Soliparty, «Antikapitalistischer CSD Zureich»
- `rf-5420` 2024-10-12 Endegelaende (Endstation x Flugelaende) (benefit): Soli für «Nightlife in Solidarity»: Trägerschaft in Quelle prüfen
- `rf-6006` 2025-02-21 Soli for Palestine (political): Solipartei for Palestine, Erlös an Gaza Sunbirds (Para-Sport-Hilfswerk). Organisation prüfen
- `rf-5778` 2025-05-24 Solidaritätsfestival SOS Méditerranée (benefit): Art4Rescue Vol. 2 für SOS Méditerranée: NGO-Anliegen Migration/Seenotrettung
- `rf-6465` 2025-06-28 Picante! Festival (political): CSD Zureich x Picante Afterparty, Spendensammlung für CSD-Kosten
- `rf-6146` 2025-10-25 Jubiläum Solidarité sans Frontières SPAZ (political): Freiplatzaktion Zürich (40 J.), Solidarité sans Frontières (25 J.), SPAZ (20 J.): migrationspolitische Organisationen
- `rf-6281` 2025-11-15 Kern und Schale: Konzert & Afterparty (political): Konzert «in Solidarity with Palestine», Kern und Schale: Veranstalter vor Verwendung prüfen
Hinweis Palästina-Soli (`rf-6006`, `rf-6281`): Veranstalter sind in der Quelle nur als Clubbüro-Programm bzw. «Kern und Schale» benannt; Erlös an Gaza Sunbirds bzw. Ticketlink über Eventfrog. Empfehlung: nicht verwenden, ausser sie werden ausdrücklich freigegeben.
- `pb-2025-11-06-45JahreJug` 2025-11-06 45 Jahre Jugendunruhen (exhibition): Ausstellung zu den Zürcher Jugendunruhen von okaj zürich; Inhalt vor Verwendung prüfen.
