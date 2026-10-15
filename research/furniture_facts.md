# Stadtmobiliar Zürich: Faktenrecherche (Stand 2026-10-15)

Status-Legende: **belegt** = aus Quelle gelesen. **teilweise** = Quelle nennt nur Teilaspekte. **nicht gefunden** = keine verlässliche Quelle, Modell muss als Platzhalter bleiben.

Die Suche war insgesamt ergiebig nur bei Open-Data-Katalogen und Medienberichten. Offizielle Produktblätter der Stadt Zürich (ERZ, Tiefbauamt, VBZ, ewz) liessen sich nicht abrufen (mehrere Pfade lieferten 404). Masse und Farben sind deshalb fast überall nicht belegt.

## 1) Öffentliche Abfallkübel (Züri-Kübel)
- Status: **teilweise**
- Modell: «Züri-Kübel 110 Liter». Ersetzte den bisherigen Betonkübel «Abfallhai» (in Chur «Khurer Kübel»). Grund: zu kleine Öffnung, zu teuer.
- Form: Oberseite flach (Kritik: Pizzaschachteln und Flaschen werden darauf abgestellt). Grössere Einwurföffnung als Vorgänger.
- Farbe: nicht gefunden.
- Material: nicht gefunden (Vorgänger war Beton).
- Masse: nur Volumen 110 l bekannt.
- Aschenbecher: nicht gefunden.
- Hersteller: nicht gefunden. Ein Artikel vermutet Eigenentwicklung der Stadt, das ist unbelegt.
- Quelle: https://www.suedostschweiz.ch/leben-freizeit/was-chur-kauft-wird-in-zuerich-bereits-ersetzt-130411 (Artikel von ca. 2019, Datum nicht geprüft)
- Quelle Datenlage: https://opendata.swiss/en/dataset/abfallgefasse1 (ERZ-Standorte der Abfallgefässe, nur Metadaten gelesen)
- Hinweis: Unterflur-Container «Modell Zürich» (ERZ-Ausschreibung 2026) ist ein anderes Produkt, nicht der Strassenkübel.

## 2) Seilleuchten über Zürcher Strassen
- Status: **nicht gefunden**
- Keine Zürcher Quelle zu Seilleuchten, Form, Farbe oder Aufhängung gefunden.
- Nur Nachbarfall: Küssnacht SZ (nicht Zürich) ersetzt Seilleuchten an Bahnhofstrasse und Oberdorf (2026). Nicht übertragbar.
- Quelle Datenlage: https://opendata.swiss/en/dataset/offentliche-beleuchtung-der-stadt-zurich (ewz-Leuchtenkataster, enthält Leuchtentypen, Attribute nicht geprüft; prüft man vor Modellierung im Datensatz).
- Empfehlung: Leuchtenkataster-Attribute auf Seil-/Querspannung prüfen oder ewz fragen.

## 3) Kandelaber / Strassenlampen-Masten
- Status: **teilweise**
- Bekannt: Stadt Zürich hat Kandelaber und Abspannmasten (ewz-Beleuchtung). Ausschreibung Korrosionsschutz 2026 bis 2027, verlängerbar bis 2029. Das belegt die Existenz, nicht die Form.
- «Zürcher Leuchte»: nicht gefunden (Name in den Quellen nicht vorhanden).
- Farbe, Höhe, Mastform: nicht gefunden.
- Quelle: https://tenderlift.ch/tenders/zurich/korrosionsschutz-beleuchtungskandelaber-und-abspannmasten-20-afb6978e/
- Quelle Datenlage: https://opendata.swiss/en/dataset/offentliche-beleuchtung-der-stadt-zurich

## 4) Robidog (Hundekotsack-Spender)
- Status: **belegt (Medienbericht, Stand 2026-09-07)**
- Farbe: grün («the green Robidog bins were a familiar sight on Swiss streets»).
- Hersteller: Robi AG, Wallbach AG (Geschäftsführer Heinz Zumsteg).
- Wichtig für 3D-Modell: Zürich, Bern, Basel und Lausanne ersetzen die Robidogs **schrittweise durch normale Abfalleimer**, teils mit Beutelspendern. Die Städte sehen einen separaten Hundekotbehälter als unnötig. Robidogs bleiben auf dem Land verbreitet.
- Masse, Form-Details: nicht gefunden.
- Quelle: https://www.bluewin.ch/en/news/switzerland/cult-trash-can-disappears-from-swiss-cities-li.3591100
- Empfehlung: Robidog in Zürich als Auslaufmodell modellieren, nicht als Standard.

## 5) Sitzbänke Stadt Zürich
- Status: **nicht gefunden** (Modellnummer «046» und «gebogene Sitzlatten» in keiner Quelle belegt)
- Datenlage: Sitzbankkataster OGD, Bänke auf städtischem Gebiet von Grün Stadt Zürich und Tiefbauamt. Stand Daten Feb 2024, Metadaten Dez 2025. Ob Modelltyp im Datensatz steht, nicht geprüft.
- Quelle: https://ckan.opendata.swiss/dataset/sitzbankkataster-ogd

## 6) Velobügel / Veloständer Stadt Zürich
- Status: **nicht gefunden**
- Kanton Zürich «Standards Veloverkehr» (2023) sind für kantonale Strassen verbindlich, für kommunale Hoheit nur Empfehlung. Die PDF-Seite selbst enthält keine Bügelmasse.
- Keine Zürcher Standardmodell-Bezeichnung gefunden.
- Velostation HB: RFID-System (Herstellerbeitrag, werblich).
- Quellen: https://www.zh.ch/de/mobilitaet/veloverkehr/veloverkehrsplanung/velostandards.html ; https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/mobilitaet/veloverkehr/downloads/standards-veloverkehr-0723.pdf (PDF nicht abrufbar)
- Datenlage: https://opendata.swiss/en/dataset/veloparkierungsanlagen (kantonal, ohne Stadt Zürich)

## 7) Tramhaltestellen VBZ
- Status: **nicht gefunden** (Wartehalle-Typ, Haltestellenmast, Billettautomat)
- Bekannt: 436 VBZ-Haltestellen (Horizont-Artikel). 257 digitale Werbescreens in Haltestellen geplant. Ein Bundesverwaltungsgerichts-Entscheid nennt eine Wartehalle, die zugunsten Behindertengerechtigkeit verschoben werden sollte, ohne Modellnamen.
- Vergleich nur als Kontext: Basel BVB nutzt Wartehallen-Typen «Mono» und «Duplex» (Tiefe 150 cm, Schmal 120 cm). Nicht Zürich.
- Quellen: https://www.horizont.net/schweiz/nachrichten/werbeflaechen-vbz-die-moeglichkeit-dass-mehrere-vermarkter-lose-ersteigern-koennen-gehoert-zum-grundsatz-der-ausschreibung.-188525 ; https://entscheidsuche.ch/docs/CH_BVGer/CH_BVGE_001_A-2092-2007_2008-01-15.pdf

## 8) Plakatsäulen / Litfasssäulen / Plakatstellen
- Status: **teilweise** (älter, Vergabe 2017)
- Stadt Zürich: 1800 Plakatstellen auf öffentlichem Grund. Konzession 2018 bis 2023 (Vergabe 2017). Formate F200, F12, F24 (426 Grossflächen) und F4 (954 Stück, «Weltformat»). Gesamt 10 bestehende beleuchtete Säulen plus Erweiterung um 25 digitale Einheiten geplant (2017). Vier beleuchtete Drehsäulen in einem Los.
- Form, Farbe, Masse der Säulen: nicht gefunden. Aktueller Vertragsstand nicht verifiziert.
- Kostenlose politische Plakatierung: F4, max. 830 Stellen.
- Quellen: https://www.horizont.net/schweiz/nachrichten/Aussenwerbung-Stadt-Zuerich-schreibt-1800-Plakatstellen-aus-145869 ; https://www.ewz.ch/content/dam/stzh/portal/Deutsch/Abstimmungen%20%26%20Wahlen/3_politische_planung/MB_Kostenlose_politische_Plakatierung_oeG_2023.pdf

## 9) Strassennamenschilder Stadt Zürich
- Status: **nicht gefunden** (Farbe, Schrift, Format, Kreisnummer)
- Bekannt: Widmungstafel-Datensatz ist Grundlage für Bestellung und Unterhalt der Strassennamenschilder. Ob Kreis/Quartier aufs Schild kommt: unbekannt.
- Quellen: https://opendata.swiss/en/dataset/widmungstafel ; https://ckan.opendata.swiss/dataset/strassennamenverzeichnis1

## 10) Hausnummernschilder Stadt Zürich
- Status: **teilweise**
- Bekannt: Hausnummernschilder sind **blau mit weisser Schrift** (laut Gebäudeadressen-Regelung). Montage meist durch Tiefbauamt. Kombinationsschilder (Strassenname + Hausnummer) empfohlen, wo Zuordnung unklar.
- Format, Material, Masse: nicht gefunden (PDF der Verordnung war 404; Quelle über Suchtreffer, Inhalt nicht selbst gelesen).
- Quelle: https://www.stadt-zuerich.ch/dam/web/de/politik-verwaltung/politik-recht/amtliche-sammlung/702/130/702.130%20Geb%C3%A4udeadressierung%20ab%2006%20V2.pdf (Suchtreffer)

## 11) Hydranten Zürich
- Status: **nicht gefunden** (Farbe, Typ)
- Datenlage: Wasserversorgung Stadt Zürich, Hydranten (städtische und private, gewartet durch WVZ), täglich aktualisiert. Attribute nicht geprüft.
- Kanton: GVZ-Richtlinie Löschwasserversorgung (2018), Abschnitt «Hydrantenanlagen». Inhalt nicht gelesen.
- Deutsche Quelle (Braunschweig, nicht Schweiz): Überflurhydranten grau oder rot mit weissen Ringen (DIN EN 14384). Unterflurdeckel oval. Nur als Orientierung, nicht übertragen.
- Quelle Datenlage: https://ckan.opendata.swiss/dataset/hydranten

## 12) Briefkasten Post (gelb)
- Status: **teilweise**
- Farbe: «Postgelb» seit 1939 festgelegt (PTT-Entscheid für Briefkästen). Nähe zu RAL 1004 (Goldgelb) laut Drittquelle (parcelsapp.com), **kein offizieller RAL-Code belegt**.
- Masse, Form, Typ: nicht gefunden. Post-Verordnung regelt Masse und Material, Brieffach und Ablagefach (Milchkästchen) sind Pflicht. Wohnungsbriefkästen sind Haushaltsware (z. B. Ernst Schweizer), nicht das öffentliche Strassenmodell.
- Quellen: https://www.post.ch/de/ueber-uns/aktuell/2023/alles-ueber-briefeinwuerfe ; https://www.horizont.net/marketing/nachrichten/-Deutsche-Post-laesst-sich-Farbe-Gelb-schuetzen-47129 (Hinweis: Deutsche Post hat RAL 1032 geschützt, nicht Schweiz)

## 13) Recycling-Sammelstellen (Glas / Alu)
- Status: **nicht gefunden**
- Keine Quelle zu Farben oder Containermodellen gefunden. ERZ hat Open-Data-Datensatz der Abfallgefässe mit Typen, Attribute nicht geprüft.
- Quelle Datenlage: https://opendata.swiss/en/dataset/abfallgefasse1

## Offene Punkte für 3D-Modelle
- Stadt Zürich hat kein öffentlich dokumentiertes Produktblatt für Abfallkübel, Velobügel, VBZ-Haltestellen, Hydranten oder Strassenschilder in den erreichbaren Quellen.
- Vorschlag: Open-Data-Attribute prüfen (Abfallgefässe, Beleuchtung, Hydranten, Sitzbankkataster) und Fotos der Ist-Zustände nur zur Inspiration, nicht als Textur (CLAUDE.md).
- Direkte Anfragen: ERZ (Abfallkübel), ewz (Beleuchtung), VBZ (Haltestellen), Tiefbauamt (Velobügel, Strassenschilder), Wasserversorgung Zürich (Hydranten), Post (Briefkasten).
