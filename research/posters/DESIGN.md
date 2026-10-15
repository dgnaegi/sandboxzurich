# Wildplakate v2 – Gestaltungsregeln

Generator: `pipeline/gen_wildposters.py` (+ `wildposter_data.py`, `wildposter_styles.py`, `wildposter_wall.py`).

## Inhalt
- Nur Events aus `research/posters/events.json` mit `approval_needed=false`. Fehlt die Datei: 5 Testeinträge (`wildposter_data.SAMPLE`).
- Gezeigt wird nur, was im Schema steht (Titel, Untertitel, Datum, Zeit, Ort, Adresse, Line-up, Preis, Veranstalter). Keine URLs, keine Logos, keine Fotos, keine Gesichter.
- Kein APG|SGA-Logo, keine Parteien. Formate Weltformat F4 (89.5×128 cm), A1, A2, aber ohne Aufdruck der Plakatgesellschaft.

## Stile (eigene Layouts, nur freie Schriften: Anton, Archivo Black, Barlow, Bebas Neue, DM Serif Display, Oswald, Permanent Marker, Space Mono)
| Stil | Kinds | Merkmale |
|---|---|---|
| swiss | Standard | Raster, Linien, grosse Grotesk, eine Formfläche in Akzentfarbe, Infos in Mono-Spalten |
| riso | Zufall bei swiss/lineup | 2 Volltonfarben, Multiply, Versatz 0–5 px, Halbton-Blob, Korn |
| neon | club, party, dj, techno | dunkel, Glow-Titel (Bebas), Röhren-Rahmen für das Datum |
| lineup | konzert, live, festival | Datum-Balken, Line-up-Liste abnehmend gross |
| theater | theater, lesung, tanz, film | Serif, Doppelrahmen, zentriert |
| flohmarkt | flohmarkt, markt | Signalfarbe, Marker-Schrift, Pfeil |

## Wand (Stück 1.5×1.5 m, Atlas 2048², 4×4 Stücke à 512 px, RGBA, ca. 0.5–1 MB WebP)
- 3–6 Bögen überlappend, alte unten (verblasst, entsättigt, Papierton), neuster oben mit Kleisterglanz.
- Knitterschatten, Falzlinien, abgerissene Ecken mit weissem Papierrand, ausgefranste Kanten, Schatten unter dem obersten Bogen.
- Marker-Tags (erfundene Kürzel) und Sticker (Namensschild, Punkte, Streifen) obenauf.
- Alpha-Test im Spiel (`alphaTest 0.5`), Lücken zeigen die Hauswand.
- Auswahl pro Wand: Stücke, deren oberstes Event-Lokal nah liegt (grobe Strassen-Geokodierung `wildposter_data.STREETS`), bevorzugt.

## Platzierung (`pipeline/props.py: wild_posters`)
Brandmauern / leere EG-Wände, 1–2 Stücke pro Wand, Abstand 22 m (13 m an Hauptstrassen). Noch nicht umgesetzt: Unterführungen, Bauzäune, Stromkästen, Kandelaber, Viadukt-Pfeiler (dafür fehlt Geometrie in den Kachel-Daten).
