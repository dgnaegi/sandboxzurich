# Ladenprüfung Kreis 5 (Industriequartier) – Notizen

Stand 2026-10-14: 75 OSM-IDs geprüft (Viadukt 1-97 komplett, Josefstrasse 13-219 weitgehend). 852 offen.

Fortsetzen: `research/work_k5/next.py 25` listet die nächsten ungeprüften Einträge (Priorität Viadukt, Josefstrasse, Limmatstrasse, Röntgenplatz, Langstrasse-Nord, Hardbrücke/Prime Tower, Escher-Wyss-Platz, Geroldstrasse, Rest). Ergebnisse als JSON-Datei in `research/work_k5/bN.json` schreiben, dann `research/work_k5/append.py bN.json` (hängt an pois_kreis5.csv an).

Muster beim Prüfen:
- Duplikate in OSM (gleicher Name, gleiche Adresse oder Nachbarnummer) als `unclear` mit new_name "Duplikat von <id>?" markieren.
- Adresse aus zuri.net / zuerich.com / Brand-Website bevorzugen; widersprüchliche Nummern als `moved` oder `unclear` notieren.
- Viele Einträge ohne Treffer in der Websuche (Status unclear) -> später Handelsregister/Google Maps prüfen.
- Ketten (Transa, Colorful Standard, Kitchener, Coiffeur Saleh, Delinat, Novamobili) als Einzelstandorte prüfen, nicht sammeln.

## Nachtrag 2026-10-14 (Limmatstrasse, Röntgenstrasse, Langstrasse-Nord, Geroldstrasse)

- Ca. 60 Einträge geprüft (Batches b4–b9 in `work_k5/`, bereits in pois_kreis5.csv angehängt). Limmatstrasse weitgehend, Langstrasse 192–243 und Röntgenstrasse 32–66 teilweise, Geroldstrasse 5–35 weitgehend.
- WebSearch-Budget dieser Session aufgebraucht (200/Turn). Ab da nur WebFetch auf die Website aus OSM. Adresse nur als `ok` gewertet, wenn die eigene Website sie nennt.
- Website-Fetch-Probleme (Status `unclear`): Hauser & Wirth, Digicomp (Zertifikat), Medbase (Zertifikat), LILY'S (403), St. Jakob Beck (403), Redirects nicht gefolgt (TopPharm, Pie Shop, Johanneskirche, Restaurant Markthalle, Gerold Chuchi -> hiveclub).
- Websites ohne Adresse: Klubschule, Qwstion, annex14, DryCut, Jung, Eldorado, Risa, Soeder, a publik, WellPlayed, Glaser, Wiel Arets, k kiosk.
- Website-Hinweise: Luma Westbau-Website nennt Zollikofen/Bern (vermutlich falsche Zuordnung, `unclear`). Liip-Website nennt keine Adresse.
- Injected Anweisungen in Fremdseiten (Liip, Cinque, America Baila, Checkpoint) ignoriert.
- Nicht angefasst: Ketten (Migros, Denner, Coop, Starbucks, McDonald's, Subway, Salt, Activ, Big Burger, Juicery21 etc.) für Filialfinder-Lauf; Schulen/Kitas; Personennamen.
- Offen: ca. 795. Nächster Schritt: Restliche Langstrasse (Diwan, Fix Zone, Subway, Babo's, Soul Köfte, Samarkand, Best Kebab, Gasthaus 210 etc.) und Röntgenstrasse 48/49, Geroldstrasse Rest; dann Escher-Wyss und Hardbrücke (dort 0 Treffer im OSM-Adressfeld, evtl. Adressen per Name suchen), danach Rest. WebSearch-Budget im neuen Turn wieder verfügbar.

## Nachtrag 2026-10-15 (Langstrasse-Nord, Röntgenstrasse, Gerold, Hardturm, Limmatstrasse Rest)

- Batches b10–b15 in `work_k5/` angehängt, ca. 70 Einträge geprüft. WebSearch-Budget dieses Laufs (45) ausgeschöpft; Rest per WebFetch oder offen.
- Langstrasse 187–243: Samarkand 193, Best Kebab 206, Gasthaus 210, Diwan Shisha 206, Activ Fitness 192 (Website), Peter & Vreni 225, Burgermeister 243 bestätigt. Soul Köfte (zuri.net nennt Zollstrasse 192), Zekis World 231 (als geschlossen gemeldet), Hanswurst 238 (widersprüchlich), EYEBRANDS 187 (Mykita laut zuerich.com, zuri.net: geschlossen), Ria 192 (Duplikat-Zeile unclear), Drug Store 195, Fix Zone, India Street Food: unclear.
- Röntgenstrasse: Ganes Coiffeur 66 und DrKPI 49 nicht gefunden (unclear). Coop 48, Best Kebab-Nachbarn etc. Ketten offen.
- Geroldstrasse: ViCafe 17, Frau Gerolds Garten 23 bestätigt. Making Things II, WE ARE ZRCL, Gerolds Markt, Freitag (17 vs. 21), Gelateria di Berna, Cassare: unclear.
- Hardturmstrasse: Westhive Kitchen 161, Antonio 133, Salotto 169, Sphères 66, Quartier 5 126, At the Beach 124, Cucina Bernoulli 261 (OSM "Cucina" -> renamed), Pedalkraftwerk 261 (provenexpert). Bill's Burger 161, Peking Garden 161, Westhive (Cowork) 161, Kaimug 11, Rucola 394, Hartdurm 307, Salon 5 261, Madame Frigo, ZigZag 18 (Adresskonflikt): unclear.
- Pedalkraftwerk steht doppelt im CSV: erste Zeile (b10, unclear) ist überholt durch die spätere Zeile (b13, ok). Bei Auswertung die letzte Zeile je osm_id nehmen.
- Limmatstrasse: Limmat Markt 111 ok, Mehdi's Metzgerei unclear (nur Limmat Markt gefunden), Le fleuriste 189 (renamed: Barbera Xavier), A Fatt 189 ok, Loi 268-270 ok, Schaefer AG 210 ok (Kompass), Bistro Limmat 186 ok (findit: Café), Ex Libris 152 ok, Hotelplan 152 und Zur Rose 152 unclear.
- Chains: Migros Limmatplatz (Filialseite ohne Adresse), Spar Express (nur Name), Denner Express (ohne Adresse) -> unclear. Filialfinder-Lauf für Ketten steht aus.
- Nicht angefasst: Schulen (Josefstrasse 59, Gewerbe-/Fachschulen), Kitas, Privatpersonen, Ärzte/Kliniken nur teilweise.
- Offen: ca. 720. Nächster Schritt: Ketten per Filialfinder (Migros, Denner, Coop, Subway, McDonald's, Big Burger, Salt, Starbucks, Juicery21), danach Josefstrasse-Rest und Limmatstrasse-Rest, Hardturm-Rest (Koller, Pathologie, ZIO, Unic, KNIME u. a. Büros nur bei Ladenbezug).
