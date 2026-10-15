# Testgebiet Details (Langstrasse / Helvetiaplatz) - Notizen

Stand: 2026-10-15. Quelle der Liste: `web/public/tiles/t_*.json` (Feld `signs`, 330 eindeutige Lokale per OSM-ID).
Output: `research/pois_testarea_details.csv`. Hilfsskripte und Zwischenstände: `research/work_details/`.

## Vorgehen
- OSM-Tags aus `data/raw/osm/kreise.json` (opening_hours, cuisine, outdoor_seating, website, addr) je OSM-ID gejoint.
- Websites per WebFetch abgefragt (Fakten zu Art, Sortiment, Aussenbereich, Schild/Fassade nur wenn im Text belegt).
- WebSearch: 4 Suchen verbraucht (El Presidente, Longstreet, Lugano Bar, Rum 97).
- Keine Bilder heruntergeladen, Google nicht verwendet.

## Stand der Abdeckung
- 330 Einträge gesamt, 108 mit Website- oder Suchfakten (Status `ok` oder Sonderstatus).
- Priorität 1 (Langstrasse-Bars/Restaurants/Clubs) weitgehend abgedeckt; offen: Rum 97 und El Presidente (nicht gefunden).
- Priorität 2/3 (Helvetiaplatz und Hospitality-Rest) zum Teil abgedeckt; Einträge mit Status `offen` haben nur OSM-Daten.
- Retail/Services ohne Website bleiben `offen` (nur OSM).

## Befunde für die Fassaden
- Schild- und Fassadenbeschreibungen (Farbe, Neon, Markise) stehen praktisch nie auf Websites. Im Feld `schild_schaufenster` steht deshalb meist «nicht belegt». Keine Farben erfunden.
- Belegt sind nur: Shokudo (Rotwandstrasse 62): Fotobeschreibung «stone facade and illuminated entrance»; Swiss Fried Chicken: Schild «Wir haben geöffnet» (Alt-Text); The Bite: Website erwähnt «Bite logo in red».
- Für echte Schilder bräuchte es Sichtung vor Ort oder Strassenfotos, die wir nur ansehen dürfen (Inspiration, kein Download).

## Auffälligkeiten (vor dem Übernehmen prüfen)
- Brick (Langstrasse 21): laut Website per 30.4.2026 geschlossen.
- Lele (Restaurant): Website meldet derzeit geschlossen.
- Ynos (Europaallee 47) und Morgenstern (Zwinglistrasse 27): Website meldet "derzeit geschlossen" bzw. "Opening soon".
- Falsche Websites (liefern Inhalt eines anderen Betriebs): so.pizza (Basel), Musik-Hall Strauss (Künstler-Atelier), Bagatelle §93 (Spritzguss), danielh.ch (Charlatan-Inhalt). Diese Fakten wurden nicht übernommen.
- Sport Bar: Website nennt Kanzleistrasse 76, OSM-Adresse abweichend; prüfen.
- Club Privé: Website nennt Stauffacherstrasse 106.
- Longstreet: Öffnungszeiten widersprechen sich (zuerich.com vs MySwitzerland).
- Spaccio: Website leitet auf einen Ketten-Auftritt um, nicht weiter verfolgt.
- Nicht erreichbar (DNS/404/403/502/TLS): u.a. Amazonia, Glamour Bar, Golden Gate Bar, Hongxi, Wunderbox, Monroe, Norden, Milano, Tach, Wunderbar.
- El Presidente und Rum 97: Websuche ohne Treffer. Existenz prüfen.

## Sicherheitshinweis
- Auf der Website von Miró Coffee stand eine versteckte Anweisung im Seitentext. Sie wurde ignoriert, der Fakt daraus nicht übernommen.

## Quellen
- Websites der Lokale wie in Spalte `quelle_url` der CSV.
- Suchtreffer: zuerich.com (Longstreet), myswitzerland.com (Longstreet), zuri.net (Lugano Bar).
