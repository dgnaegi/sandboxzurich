# Zone 1 HB und Langstrasse: Namensprüfung Läden und Beizen (2026-10-19)

Methode: 430 Einträge (OSM + `pois_kreis*.csv`). Feld `name_geprueft` in `zone1_shops.json`: ok = Web-Status ok (2026-10-14) oder Eintrag auf der offiziellen Europaallee-Seite; unclear = Verzeichnis unklar; offen = nie geprüft. Regel: Umbenennen/Schliessen nur mit offizieller Quelle, Presse oder Handelsregister. Ergebnis: 174 ok, 129 unclear, 127 offen. 0 umbenannt, 0 geschlossen (keine belastbare Quelle).

## Gesuchte Fälle (jede Suche einmal)
- Europaallee (offizielle Seite https://europaallee.ch/en/offer/): Nooba, Loft Five, vomFASS, Hiltl Sihlpost, doodah, Revendo, Wood Factory, Vito, Changemaker, Ynos, Coop, Happy Bike, Starbucks, Jack Wolfskin, Più, MANA, Ochsner Sport Pro, radix, Beetnut, La Cucina, Bean Bank, Café Europa, Via del Gusto 28 aktuell gelistet -> ok. Hiltl Sihlpost auch zuerich.com.
- Peking Garden (Langstrasse 13): zuri.net/inyourpocket, Betrieb, Sommerterrasse -> ok.
- Burger King Lagerstrasse 1: Verzeichnis (intravel.net) "Clipper", Candrian -> Name bleibt.
- Brick (Langstrasse 21): zuri.net «als geschlossen gemeldet», Rezensionen 2024/25 positiv, brickbar.ch -> unklar, offen.
- Oh My Greek! (OSM n9277633394, Brauerstrasse 37 laut Verzeichnis): zuri.net Januar 2025 «als geschlossen gemeldet», kein Datum, nur Verzeichnis -> offen, nicht geändert.
- Zur Goldigen Guttere (bluewin 2025): wegen Renovation geschlossen, nicht im Inventar.
- Ohne Treffer: Infocafé (Militärstrasse 8), Cheesecake Love (Militärstrasse 16), La Capricciosa (Militärstrasse 117, in Verzeichnissen nur Restaurant Milano Nr. 109 gefunden).

## Offen (nicht geändert)
Militärstrasse (Ka3an, viajes.ch, Moto-Center Karle, COOP 106), Langstrasse 13 Pho Vietnam, Lagerstrasse (VeloKliniK, Sula, Atelier Grünenwald «moved»), Kasernenstrasse (Jack Wolfskin, Più), Zürich Fried Chicken («moved»), Haus von Klaus / Schneiderei Club (Verzeichnisname abweichend), Helvetiaplatz-Umfeld. Namen mit «Helvetiaplatz» unverändert (`apply_names.py`).
HB-Haupthalle: keine Läden erfunden (SDA 07/2026: Südtrakt Reisezentrum, Nordtrakt-Läden Q2 2027).
