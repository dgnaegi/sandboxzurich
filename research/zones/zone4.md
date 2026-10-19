# Zone 4 Wiedikon: Inventar Auftrag Z0 (Stand 2026-10-19)

Quellen: `research/zones/zone4_facades.json` (Fassaden, Auszug aus `research/buildings/visual_notes_v3.json`), `research/zones/zone4_shops.json` (Laeden/Beizen), `research/zones/zone4_photos.json` + `zone4_sites.json` (Lueckenfotos, `pipeline/photos/fetch_z4.py`), `research/zones/zone4_sheet_index.json` (Bogen-Index), OSM (`data/raw/osm/kreise.json`, ODbL), Katalog `web/public/data/catalog.json`, `research/idaplatz.md`, `research/shops_v3/`.
Polygon: `pipeline/overrides/zones.json` (Zone 4, 4 Eckpunkte, 17 Kamerapunkte, 34 Kacheln).

## Haeuser
- 697 OSM-Adressen im Polygon an den Hauptstrassen (Birmensdorfer 117, Zurlinden 74, Aemtler 70, Zentral 70, Goldbrunnen 67, Berta 61, Kalkbreite 52, Gertrud 42, Badener 39, Ida 29, Sihlfeld 21, Schlossgasse 19, Marta 18, Wiesendanger 16, Thomasweg 2).
- 202 davon haben Fassadennotizen (Hex, Material, Stil, Rahmen, teils Geschosse/Dach/Fenster). Alle 202 mit Hex.
- 495 ohne Notiz: Fassaden-Erfassung aus Fotos NOCH OFFEN (Lueckenliste = Adressen in `zone4_facades.json` fehlen, siehe Abschnitt Luecken).
- Dach-/Balkon-/Sockel-Felder nur teilweise (dach 6, achsen 3, geschosse 32 Eintraege).

## Plaetze
### Idaplatz (Platzmitte ca. -125/-1115)
- Boden: Kiesplatz, sandfarben, kein Pflaster, Granit-Randsteine (`research/idaplatz.md`). Strassen-Asphalt aus OSM-Flaechen (asphalt).
- Baeume: OSM 44 Baum-Nodes im 60-m-Radius; Baumkataster ~14 Platz-/Randbaeume (Kirschpflaume, Zierkirsche, Spitzahorn, Blutpflaume entlang Bertastrasse).
- Brunnen: Katalog V2 (Trogbrunnen Stein) bei (-142,-1095). `research/idaplatz.md` beschreibt Trinkbrunnen mit Schwan; V2 passt nur bedingt -> Katalogvariante PRUEFEN (Kandidat V6 Figurenbrunnen). Nicht entschieden.
- Moebel: 12 Baenke (OSM, 17 laut OGD), 4 Velo-Parkierflaechen, Velostaender in Reihen SW-Rand und Bertastrasse.
- Gastro-Aussensitze: Bottega Berta (Metalltische, Kies, rote Neonlinie), Le Calvados, Babette (rote Markise, rote/blaue Tische) an Zentralstrasse.
- Haltestellen: keine am Platz selbst (Aemtlerstrasse Trolleybus, Glasdach, siehe unten).

### Schmiede Wiedikon (139/-1562)
- Boden: Asphalt (6 Flaechen). Baeume: 9 (OSM). Baenke: 3. Tram-Haltestelle: 1 (Linie 2256 laut OSM-Tag). Restaurant Bierstube Scheidegg.
- Brunnen: keiner in 60 m. Katalog-Brunnen V1 bei (108,-1500) ca. 65 m entfernt; nicht am Platz.
- Haltestelle/Wartehalle: Katalog H1/H3/H4 nur im Gesamt-Zonenzaehler, Position am Platz nicht geprueft.

### Goldbrunnenplatz (-191/-1516)
- Boden: Asphalt (34 Flaechen), Beton (4). Baeume: 7. Baenke: 3. Velo-Parkierflaechen: 4. Strassenlampen: 2.
- Haltestellen: Bus 3 (OSM highway=bus_stop), Tram 2 (railway=tram_stop, Linie 1012 laut OSM). Cafe ViCafe, Restaurant Xi Muoi.
- Brunnen: Katalog V2 bei (-212,-1560), ca. 49 m entfernt; nicht eindeutig dem Platz zugeordnet, PRUEFEN.

### Bahnhof Wiedikon Vorplatz (563/-1400)
- Boden: Asphalt (30), Beton (2), Kunstrasen (1, PRUEFEN: vermutlich Begruenung/Verkehrsinsel). Baeume: 18. Baenke: 10. Abfallkoerbe: 8. Velo-Parkierflaechen: 4.
- Haltestellen: Bus 4, Tram 2 (OSM). Katalog-Figurenbrunnen V6 bei (519,-1410), ca. 46 m entfernt, PRUEFEN.
- Gastro: Arcade Pizzeria, Silex (Restaurants).

## Haltestellen (Zone 4, Katalogzaehler)
H1 Wartehalle 19, H3 Ticketautomat 14, H4 Anzeigewand 22, H6 Bank kurz 30, H7 Bank lang 9. Positionen pro Haltestelle nicht einzeln nach Foto geprueft.

## Laeden und Beizen (`zone4_shops.json`)
- 372 Eintraege (OSM-Gastro und Shops im Polygon, ohne Coiffeur/Beauty/Kleider/Bank-Typen). 88 mit Webpruefung aus `research/pois_kreis3.csv`, 3 mit Fotoquelle (Bottega Berta, Idaplatz-Set aus `research/shops_v3`), 113 ohne OSM-Adresse.
- Schild (Farbe/Schrift), Markise und Aussensitze fuer die uebrigen Laeden: NOCH OFFEN.

## Luecken (Stand dieser Session)
1. Fassaden: 495 Adressen ohne Notiz (Hauptstrassen, Polygon). Fotoerfassung fehlt.
2. Laden-Schilder/Markisen: nur 3 von 372 fotografisch geprueft.
3. Brunnen-Varianten Idaplatz, Goldbrunnen, Bahnhof Vorplatz: Katalog-Zuordnung nicht bestaetigt.
4. Haltestellen-Positionen: nicht einzeln geprueft.
5. Kalkbreite/Friedhof Sihlfeld: Lueckenfotos siehe Log, Auswertung nach Download.
