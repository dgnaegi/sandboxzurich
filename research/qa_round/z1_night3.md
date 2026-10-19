# Zone 1 (HB und Langstrasse) – Nacht 3, 2026-10-19 abends

Bögen: `preview/zone1_before.jpg`, `preview/zone1_after.jpg` (Spiel, PC+Handy), `preview/zone1_cmp_{before,after}_{1,2}.jpg` (Foto | Spiel von der Fotoposition, `pipeline/zones/zone_cmp.py`).

## Noten (1–5, streng; vorher → nachher)
| Punkt | vorher | nachher | Bemerkung |
|---|---|---|---|
| Bahnhofplatz (Escher) | 3 | 3 | Portal + Denkmal ok, Platz leer/grau |
| HB-Halle | 2.5 | 3.5 | Buden/Klappen weg, Tore statt erfundener Läden, Boden grau wie Fotos |
| Querhalle | 2.5 | 2.5 | weisse Tafel-Box, Schacht-Platte im Vordergrund |
| Europaallee/Lagerstrasse | 3 | 3 | Fassaden glatt, Masten ok |
| Sihlpost | 3 | 3 | |
| Haltestelle Bahnhofplatz/HB | 2 | 2.5 | Plakatwand/Zaun dominiert, Wartehallen nicht im Blick |
| Langstrasse/Lagerstrasse | 3 | 3 | Ole Ole ok |
| Langstrassen-Unterführung | 3 | 3 | siehe Release 4b |
| Langstrasse/Dienerstrasse | 3 | 3 | |
| Langstrasse/Militärstrasse | 3 | 3 | |
| Langstrasse/Brauerstrasse | 3 | 3 | |
| Helvetiaplatz (Volkshaus) | 3 | 3 | Volkshaus-Farbe passt zum Foto |
| Haltestelle Helvetiaplatz | 3 | 3 | |
| Kanzlei | 2.5 | 2.5 | Platzbelag Kies im Foto, im Spiel Asphalt-grau |
| Bäckeranlage | 3 | 3 | |
| Kasernenstrasse | 3 | 3 | |
| Velotunnel-Portal | 2 | 2 | Portal an der OSM-Lage nicht sichtbar |
| Langstrasse/Hohlstrasse | 2.5 | 3 | |
| **Ø** | **2.8** | **2.9** | Ziel 4 nicht erreicht |

## Ehrliche Einordnung
Die Daten haben stark zugelegt (Notizen 378 → 520, Geschosse 106 → 354, 15 Ladenfronten), aber auf Kamerahöhe ist das kaum zu sehen: Die Häuser haben schon die richtige Höhe und Farbe, und die Geschosszahl ändert vor allem die Fensterzeilen. Was das Bild «generisch» macht, sind Fensterformen, Sockel, Ladenschilder und Strassenmöblierung. Für Note 4 braucht es dort Handarbeit an den Kamerapunkten (Landmark-Häuser, Platzbeläge, Haltestellen).

## Tickets
- Z1-1 Velotunnel-Südportal: an der OSM-Lage (1433,-772) im Spiel nicht erkennbar; Lage prüfen (Rampe Kasernenstrasse/Sihlpost), Portal sichtbar machen.
- Z1-2 Kanzleiareal: Kiesplatz mit Bäumen (Foto 2024), im Spiel grauer Belag → `places_detail` Kies.
- Z1-3 Querhalle: weisse Box (Rückseite Abfahrtstafel?) und Schachtplatte vor der Kamera prüfen.
- Z1-4 Haltestelle Bahnhofplatz/HB: Plakatzaun über die ganze Länge – Bauzaun oder echt? Fotos 2024 zeigen offene Haltestelle.
- Z1-5 Verfolgerkamera steckt in Baumkronen (Foto-Standort unter Baum, Kanzlei): Kamera-Sweep ignoriert Kronen (vgl. T11).
- Z1-6 `zone_cmp.py` Fotoauswahl: Filter (Helligkeit/Struktur) hilft, wählt aber noch Bodenfotos (Kasernenstrasse); besser: Mapillary-`camera_type`/Pitch mitspeichern.
