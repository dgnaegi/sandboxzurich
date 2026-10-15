# Plan: 8 Stunden «Karte viel besser, Velos & Co. viel realistischer»

Stand: 2026-10-15. Keine Quests/Missionen (macht der User; im Spiel abgeschaltet, nur mit `?missions`).
Grundsatz: **Erst Referenzfotos, dann bauen, dann gegen die Fotos prüfen.** Jede Verbesserung wird per Screenshot neben das Referenzfoto gelegt.

## Fotos: woher und wofür
| Quelle | Zugang | Lizenz | Verwendung |
|---|---|---|---|
| Wikimedia Commons | API (ohne Token) | pro Bild (CC BY, CC BY-SA, PD) | Referenz; Texturen nur bei PD/CC0/CC BY (mit Credit), CC BY-SA nur als Referenz |
| Panoramax | API (ohne Token) | meist CC BY-SA | Strassenansichten als Referenz |
| Mapillary | braucht Gratis-Token des Users | CC BY-SA | Strassenansicht an jeder Adresse (optional, Token fehlt) |
| Google | – | – | nur anschauen, nie speichern |

Ablage: `data/raw/photos/<thema>/` (nicht im Repo) + `research/photos/<thema>.json` (URL, Autor, Lizenz) + Kontaktbogen `preview/ref_<thema>.jpg`.

## Ablauf (parallel, mit klarer Dateizuständigkeit)
| Std. | Paket | Wer |
|---|---|---|
| 0–1 | **F1 Fotos Strassenbild Kreis 4/5:** Langstrasse, Helvetiaplatz, Militär-/Hohl-/Kanonengasse, Bäckeranlage, Kanzlei, Ladenfronten, Hinterhöfe | Agent (Haiku) |
| 0–1 | **F2 Fotos Velo & Stadtmobiliar:** Velos in Zürich (Stadtvelo, Rennvelo, Cargo, E-Bike, Kindersitz, Körbe), Velo-Abstellplätze/-bügel, Seilleuchten, Kandelaber, Züri-Kübel, Brunnen, Bänke, Hydranten, Plakatsäulen, Strassenschilder, Hausnummern, Poller, Glascontainer | Agent (Haiku) |
| 0–1 | **F3 Fotos ÖV & Verkehr:** VBZ-Trams (Cobra, Flexity, Tram 2000), Trolleybus, Haltestellen, Fahrleitungen, Rillenschienen, Markierungen (CH), Velostreifen-Piktogramme, Fussgängerstreifen, Parkfelder | Agent (Haiku) |
| 0–2 | **G Gelände swissALTI3D** statt Schätzung aus Gebäudesockeln (echte Höhen, Rampen) | Agent (Sonnet) |
| 0–2 | **A Adressen & Schilder:** Hausnummern (amtliche Gebäudeadressen), blaue Zürcher Strassenschilder an Kreuzungen | Agent (Sonnet) |
| 1–1.5 | **Review der Kontaktbögen** → Abweichungsliste pro Element (`research/realism_gaps.md`) | ich |
| 1.5–5 | **V Velos v2** (Blender): Stadtvelo, Rennvelo, Mountainbike, E-Bike, Cargo-Velo, Mietvelo ohne Logo; Speichen, Schutzbleche, Körbe, Kindersitze, Schlösser; echte Velobügel-Typen; dichte, realistische Velo-Reihen | Agent (Sonnet) |
| 1.5–5 | **M Stadtmobiliar v2** (Blender) nach Fotos: Seilleuchte, Kandelaber, Züri-Kübel, Zürcher Brunnen, Sitzbank-Modelle aus dem Sitzbankkataster, Hydrant, Plakatsäule, Poller, VBZ-Haltestelle mit Wartehalle | Agent (Sonnet) |
| 1.5–5 | **T Tram v2** (Blender): Cobra und Flexity im VBZ-Look, Stromabnehmer, Türen, Liniennummer | Agent (Sonnet) |
| 1.5–6 | **S Strassenbild v2** (ich): Rillenschienen im Asphalt, Schachtdeckel, Velo-Piktogramme, BUS-Markierung, Abnützung, Randsteindetails, Trottoir-Absenkungen an Fussgängerstreifen | ich |
| 1.5–6 | **H Häuser v2** (ich): Geschosshöhen aus Gebäudehöhe/OSM-levels statt fix 3.2 m, Farben je Strassenzug aus Fotos, Sockelzone, Brandmauern, Dachfarben, Hauseingänge, Balkone als Geometrie im Nahbereich | ich |
| 6–7.5 | **Integration & Abnahme:** alles einbauen, Screenshots neben Referenzfotos (`preview/compare_*.jpg`), Performance-Messung Handy/PC | ich |
| 7.5–8 | **Doku:** HANDOFF, ROADMAP, Credits (Fotos/Lizenzen) | ich |

Falls Zeit bleibt: Skalierung auf ganze Kreise 4 und 5 (zuerst Kreis 4).

## Abnahmekriterien
- Für Velos, Stadtmobiliar, Tram, Ladenfronten, Strasse gibt es je ein Vergleichsbild «Foto vs. Spiel». Das Spiel-Element ist auf den ersten Blick als das echte Zürcher Objekt erkennbar.
- Handy-Budget hält: ≥ 30 fps (gedrosselt ≥ 55), ≤ 250 Draw Calls, ≤ 1.5 Mio Dreiecke, Download bis spielbar ≤ 20 MB.

## Bitte an den User
- **Mapillary-Token** (gratis, mapillary.com → Developers) würde Strassenansichten an jeder Adresse liefern. Ohne Token: Commons + Panoramax.
