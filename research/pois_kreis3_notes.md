# Ladenprüfung Kreis 3 – Notizen (Stand 2026-10-14)

## Stand
- research/pois_kreis3.csv: 106 Einträge (ok 65, unclear 38, renamed 3).
- Ziel ≥ 300 noch nicht erreicht. Offen: 660 ungeprüfte OSM-Einträge (ohne Schulen/Kitas/Spielplätze/Kunst/Infrastruktur).
- Fortsetzung: Häppchen mit `research/work_k3/next25.py 25` (zeigt nächste 25 ungeprüfte, Priorität Wiedikon/Weststrasse/Idaplatz/Zurlinden/Badener/Gertrud/Birmensdorfer), dann Ergebnisse als `oid|status|neuer_name|adresse|quelle` per `research/work_k3/add.py` anhängen (stdin, Heredoc).

## Methode
- Eingabe: research/pois_kreis3_osm.csv, Häppchen per Skript (Schulen, Kitas, Kinderbetreuung, Spielplätze, Kunst, Ärzte, Polizei, Post, Tankstellen, Kunst am Bau übersprungen).
- Pro Eintrag eine Websuche «<name> <adresse> Zürich». Quellen: zuri.net, treatwell, onedoc, ubs.com, zuerich.com, moneyhouse (nur als Existenznachweis der Adresse), local.ch.
- status: ok = Adresse/Betrieb bestätigt; unclear = in der Suche nicht gefunden oder Quellen widersprechen; renamed = Betrieb unter anderem Namen an der Adresse.

## Offene Punkte (nicht geprüft)
- Priorität 1 nicht fertig: Bars rund um Bahnhof Wiedikon (Nebu ok, La Catedral unclear), Schmiede Wiedikon, Weststrasse, Idastrasse/Idaplatz, Zurlindenstrasse (nur Wiedikon Point, Blumenhaus), Badenerstrasse Süd, Gertrudstrasse.
- Restliche Birmensdorferstrasse-Einträge ab Nummer ~200 (Coiffeure: Afrodita 260, Bekim Barber 188, Coiffeur Andrea 221, Coiffeur Sher 111, Coiffeur Triemli 432, Coiffure Lucia 377, Rolph 253, The Cut 99; Ying Cusine und weitere Gastro offen).
- Ketten noch nicht über Filialfinder geprüft: Migros (Take-Away 140/320, Florissimo 320), Coop, Denner, Volg, Lidl, Aldi, Banken (UBS 123 ok, Raiffeisen 170 ok).
- Migros Take-Away 140: Migros-Supermarkt an dieser Adresse bestätigt, Take-Away-Status offen.

## Auffälligkeiten
- Mehrere OSM-Einträge sind vermutlich veraltet oder falsch verortet: Canaan Asia (200), Li Santi (259), Traum Pizza Kebab (430), Tremonte (129), Müller (320, dort Drogama), MyShop (430), Vastela Books (255), Denim & Iron (199), Rahmenhandlung (201), Beauty by Dilek (432).
- Ein Eintrag mit anderem Namen: Garage von Koerber GmbH an Birmensdorferstrasse 430 (OSM: Peter Zahnd).
- Ein Eintrag umbenannt: Wiedikon Textilpflege -> Texsana Reinigung Wiedikon (Seebahnstrasse 31).
- Widersprüche bei Con Gusto (Hotzestrasse vs. Birmensdorferstrasse 169; zuri.net gewinnt), Apodro (local.ch «closed»), Ying Cusine (Snapshot «closed»).
- Keine Bilder gespeichert. Keine Websuchen wiederholt.

## Hilfsdateien
- Eigenes Skript zum Anhängen: /private/tmp/claude-501/-Users-danielgnagi-sandboxzurich/2c85f10e-b4e1-4c95-8bd3-e132013d6298/scratchpad/k3_add.py (schreibt nur nach research/pois_kreis3.csv).
- Hinweis: Im selben Scratchpad lag zwischenzeitlich ein fremdes add.py, das nach research/pois_kreis5.csv schreibt. Ich habe es nicht ausgeführt. research/pois_kreis5.csv existiert, stammt aber nicht von mir und wurde nicht verändert.

## Sitzung 2026-10-14 (Fortsetzung)
- 44 Websuchen (standard). Erledigt: Velo Schmiede, Schmiede (Zurlindenstrasse 49, umbenannt zu SCHMIDO, evtl. geschlossen), Weststrasse 112-196 (Gastro, Kunst, Läden), Idaplatz, Gertrudstrasse 26-68, Zurlindenstrasse 51-300 (Coiffeur, Garage, Café, Interdiscount), Badenerstrasse 255-435 (Gesundheit, Gastro).
- Nicht geprüft in dieser Sitzung (bewusst übersprungen): Studio Müller (Weststrasse 150), Regionalwache Wiedikon (Zurlindenstrasse 87), Avia Birmensdorferstrasse, Ketten-Filialfinder (Migros, Coop, Denner, Volg, Lidl, Aldi).
- Fehler in dieser Sitzung: Bei «Predrag Krunic» (Privatperson, Arzt) wurde der Name in die Suche aufgenommen. Eintrag steht auf unclear, ohne weitere Suche. Künftig Privatpersonen nur mit Praxis-/Betriebsname suchen.
- Zurlindenstrasse 218a: Garage Zurlinde bestätigt (coparking.ch, Quelle von Drittportal).
- Pompon (Idaplatz): local.ch nennt Idaplatz 10, OSM hat keine Nummer; Öffnungsstatus widersprüchlich → unclear.
- Bekannte Fehlerquellen: zuerich.com zeigt bei Le Calvados «Closed» an allen Tagen (vermutlich Anzeigefehler).

## Auffälligkeiten (neu)
- Zu den früheren Auffälligkeiten kommen hinzu: Interdiscount-Filiale und Coiffeur Saval Hair bestätigt; Galerie West 41, DASH- DOT. KNOT*, lavie home, Ecke West, S-Family, mf-system, Chornlade, Aurum Fitness: nicht gefunden → unclear, teils wahrscheinlich veraltete OSM-Einträge.

## Sitzung 2026-10-14 (Abbruch Websuche-Limit)
- WebSearch-Budget der Session erschöpft (Limit 200 Aufrufe pro Turn). Keine neuen Einträge in dieser Sitzung angehängt, weil ohne Suche nichts belegt werden kann.
- Nächster Batch (ungeprüft, Priorität Birmensdorferstrasse): Migros BSS 140, Coop BSS 200, Denner BSS 320, Coop BSS 310, Fressnapf BSS 320, McOptic BSS 320, Vista Augenpraxis BSS 318, Dani Reisen BSS 285, Galerie König BSS 299, Weber+Widmer BSS 127, Zweifel 1898 BSS 155, Coiffeur-Liste BSS 111-260, Artigiano BSS 172, 2nd Skin BSS 187, Bekim Barber BSS 188, Flohstube BSS 188, Schmid Orthopädie BSS 198, Studio Müller/Club Pascha Weststr. 150, Regionalwache Zurlindenstr. 87, Avia BSS.
- Helper-Befehl: `python3 research/work_k3/next25.py 25`, Eingabe per Pipe in `research/work_k3/add.py`.

## Sitzung 2026-10-15 (Subagent, Kreis 3)
- 32 Websuchen (standard). Keine Bilder, keine Privatpersonen, Schulen/Kitas übersprungen.
- Angehängt (je Eintrag eine Zeile in pois_kreis3.csv): Coop BSS 200 ok (Too-Good-To-Go-Listing «Coop Supermarkt Wiedikon»), Coop BSS 310 unclear (nur Stellenanzeige Talwiesenstrasse-Birmensdorferstrasse 310), Migros BSS 140 ok (zuri.net), Artigiano BSS 172 ok, Schmid Orthopädie BSS 198 ok (local.ch), Well & Belle BSS 260 ok (zuri.net nennt Kosmetiksalon statt Massage), Afrodita BSS 260 ok, Vista Augenpraxis Talwiesen BSS 318 ok (chirurgie seit 2022 in Wollishofen), Mikkeller Zweierstrasse 124 ok, Lou's Restaurant & Bar Zweierstrasse 106 ok, Bar Sacchi Bertastrasse 1 ok (OSM ohne Adresse, Koordinaten weichen ab), Enfant terrible Aemtlerstrasse 48 ok (zog 2024 aus Zentralstrasse 156 aus, Adresse via zuri.net), Berta Bar Bertastrasse 26 ok, Dalí's Bar Meinrad-Lienert-Strasse 17 ok, Raygrodski Sihlfeldstrasse 49 ok, Wohnzimmerbar Kalkbreitestrasse 10 ok, The Cut BSS 99 renamed -> The Cut Pete Hairstyling.
- unclear (nicht gefunden oder widersprüchlich): Denner BSS 320, Fressnapf BSS 320, McOptic BSS 320 (OneDoc nennt McOptic Wiedikon M-Mart, Adresse offen), Weber+Widmer BSS 127 (local.ch «closed», Adresse unbestätigt), Zweifel 1898 BSS 155 (Weinbeiz ist Regensdorferstrasse 20), 2nd Skin BSS 187, Flohstube und Bekim Barber BSS 188, Dani Reisen BSS 285, Galerie König BSS 299 (nur Expat-Exchange-Listing), Rolph BSS 253 (local.ch zeigt Rolph AG an der Künzlistrasse 23, BSS 253 = Hofmann Roland), Titan BSS 249, Fantasy Bar, NachBar, Zeig Bar, Bar Stadio, Coiffeur Sher BSS 111, Coiffeur Andrea BSS 221, Studio Müller / Club Pascha Weststr. 150, Regionalwache Zurlindenstr. 87, Avia (laut coparking BSS 256, nicht OSM-Eintrag bestätigt).
- Noch offen: Migros Take-Away BSS 140 (eigener OSM-Eintrag n4827130219, Take-Away-Status offen), Migros/Florissimo/Take-Away BSS 320 (OSM n1702309790, n4827130220, n3055722588), Coop Vitality BSS 200 (Apotheke, übersprungen), Wiedikon Point, Züri CiTea, Die Bücherregale/Lesebänke (nicht geprüft), Bahnhof-Wiedikon-Restaurant Seebahnstrasse 33 (nicht geprüft).
- Ketten: Denner/Fressnapf/Filialfinder-Suche über Websuche unzuverlässig; Filialfinder-Seiten (denner.ch, fressnapf.ch, migros, coop) direkt prüfen, falls möglich.
