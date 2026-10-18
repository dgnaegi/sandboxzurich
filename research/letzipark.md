# Letzipark (Baslerstrasse 50) – Landmark

Einkaufszentrum Letzipark, Kreis 9 Albisrieden/Altstetten-Grenze. Mitte ca. (-1318, 236), Kacheln -7_0 und -7_1 (bzw. -6_x je nach Ausdehnung).

## Quellen
- Fotos (nur angesehen): Commons «Einkaufszentrum Letzipark, Zurich, June 2024» und «Popeyes in Zurich … Letzipark» (Dodo von den Bergen, CC BY-SA 4.0), «Altstetten – Letzipark – Hohlstrasse 2013» (Roland zh, CC BY-SA 3.0), «Baslerstrasse Richtung Letzipark» (gertrudis2010, CC BY-SA 3.0); Mapillary-Strassenfotos `research/v3/photos_schlachthof.json` (Sites lp_*). Kontaktbogen `preview/letzipark_ref.jpg`.
- Volumen: swissBUILDINGS3D ID_9DCBF65B (Hauptdach 7.0 m ü. M. = 16.7 m über Terrain, drei Kuben 13.3 m ü. M. = 23 m, Parkhausflügel Ost), SWISSIMAGE.
- Mieternamen: `research/pois_kreis9_notes.md` (Coop, Manor, Decathlon, H&M, Orell Füssli, Dosenbach, Vögele, bau+hobby, Gidor, C&A, Ochsner Sport, Mobilezone). Schilder sind schlichte Textfelder, keine Logo-Kopien.

## Modell
`pipeline/landmarks/k39w3_letzipark.py` (+ `schlachthof_lp_tex.py`): Wände/Dächer aus den 3D-Daten, graue Paneelfassade mit Fensterbändern, Arkade (Vordach, blaue Säulen mit weissen Kugelleuchten, Ladenfronten mit Namensschildern, verglaste Eingänge), schwarze Dachkuben, blauer Schriftkubus mit «LETZIPARK» + Palme auf dem Dach, «EINKAUFSZENTRUM» und «66 Geschäfte / Montag–Samstag / 9–20 Uhr».

## Runde 2
- Baslerstrasse-Fassade (70 m, Süd): dunkel (wie Foto 2024/2013), keine Fensterbänder, riesige blaue Lettern «L E T Z» + Palme als «I» (`schlachthof_lp_tex.huge`, 50 x 12.5 m). Dach-Schriftzug «LETZIPARK» auf dem blauen Kubus vergrössert (24 x 6 m).
- Rot-weisse Absperrungen/Poller vor der Arkade: NICHT aus dem Landmark. Quelle ist `pipeline/sites.py` (OGD «Aktuelle Tiefbauprojekte», Baustelle t26022 «Baslerstrasse 47-50», 2026-11-02 bis 2027-04-30, ewz-Trafostation) und liegt damit in einer Datei ausserhalb dieses Auftrags. Beleg auf Fotos nicht vorhanden (Fotos stammen von vor Baubeginn). Abschalten nur über eine Ausschlussliste in sites.py (heute nicht vorhanden).

## Offen
- Genaue Fassadenfarbe schwankt je nach Foto (2024 dunkel mit Lichterkette, 2025 blau/Gerüst).
- Treppentürme aussen und Lichthöfe nur als Fläche.
