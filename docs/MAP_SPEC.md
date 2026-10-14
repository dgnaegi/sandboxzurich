# Karten-Spezifikation

Ziel: Die Kreise 3, 4, 5 und 9 so originalgetreu wie möglich nachbauen, sodass Einheimische ihre Strassen wiedererkennen. Jede Ebene hat eine Quelle (siehe `DATA_SOURCES.md`) und eine Prüfmethode.

## Gebiet
- Die Grenzen der Kreise 3, 4, 5 und 9 kommen aus dem OGD-Datensatz «Stadtkreise» der Stadt Zürich.
- Bounding Box grob: 47.355–47.400 N, 8.465–8.545 E (wird mit dem Datensatz präzisiert).
- Rand: 300 m Kulisse (nur Gebäudesilhouetten), dahinter Panorama (Uetliberg, Hochhäuser).
- Die Reel-Daten (`../gta6/data/`) decken nur etwa 47.370–47.3935 N / 8.506–8.534 E ab und müssen erweitert werden.

## Ebenen (Checkliste)

### Gelände und Wasser
- [ ] Gelände (swissALTI3D, höher aufgelöst als das Terrarium-DEM des Reels)
- [ ] Sihl, Limmat (Kreis 5), Schanzengraben falls im Gebiet; Ufer und Böschungen
- [ ] Brunnen (Züri-Brunnen sind ikonisch, Standorte aus Stadt-ZH-OGD «Brunnen»)

### Gebäude
- [ ] swissBUILDINGS3D LOD2 (Dachformen)
- [ ] Fassaden nach Gebäudetyp und Baujahr (Altbau, Genossenschaft, Gewerbe, Neubau, Hochhaus)
- [ ] Erdgeschoss mit Ladenfront, wo ein POI liegt
- [ ] Landmarks individuell (Prime Tower, Lochergut, Zentralwäscherei, KVA Josefstrasse, Viadukt, Hardturm-/Letzigrund-Stadion, Toni-Areal, Bahnhof Altstetten, Kirche St. Jakob …). Wiederverwenden, was im Reel schon existiert.

### Strassen und Verkehrsflächen
- [ ] Fahrbahnen mit echter Breite und Spurenanzahl (OSM `lanes`, `width`, Fallback nach Strassentyp)
- [ ] Trottoirs mit Randsteinen, Begegnungszonen, Fussgängerzonen
- [ ] Fussgängerstreifen (gelb, Schweizer Standard) an echten Positionen
- [ ] Lichtsignale an echten Kreuzungen
- [ ] Markierungen: Mittellinien, BUS-Spuren (gelb, Schweizer Schrift), Tempo-30-Zonen mit «30»-Markierung und Eingangstoren
- [ ] Unterführungen und Brücken (Langstrasse-Unterführung, Hardbrücke, Duttweilerbrücke, Europabrücke)
- [ ] Parkplätze (blaue und weisse Zone)

### Velo (hohe Priorität)
- [ ] **Velovorzugsrouten** der Stadt Zürich (aktuell und geplant), farblich erkennbar wie in echt
- [ ] Velostreifen (gelb gestrichelt), Velowege, Velo-Ampeln, Velo-Abstellplätze
- [ ] Gegenverkehr für Velos in Einbahnstrassen
- [ ] Velo-Bodenlichter an der Hardbrücke (im Reel schon gebaut)
- [ ] Spielmechanik später: gute Velo-Infrastruktur macht Lieferquests schneller

### ÖV
- [ ] Tramgleise mit Fahrleitungen (Linien 2, 3, 4, 8, 9, 13, 14, 17 …, aus OSM-Routenrelationen)
- [ ] Tramhaltestellen mit Namen, Wartehäuschen und Anzeige
- [ ] Trolleybus- und Buslinien (31, 32, 33, 72, 80 …) mit Fahrleitungen
- [ ] Bahnhöfe Hardbrücke, Wiedikon, Altstetten; Gleisfeld als Kulisse
- [ ] Fahrende Trams und Busse (später, entlang der Routengraphen, mit Fahrplantakt)

### Grün und Freiräume
- [ ] Parks und Plätze: Josefwiese, Bäckeranlage, Helvetiaplatz, Idaplatz, Lochergut-Park, Fritschiwiese, Lindenplatz …
- [ ] Bäume an echten Standorten (Baumkataster der Stadt Zürich), Arten grob nach Kategorie
- [ ] Spielplätze, Pingpong-Tische, Boccia-Bahnen, Gartenbeizen

### Läden, Cafés, POIs
- [ ] Alle Läden, Cafés, Bars, Restaurants, Kioske, Clubs aus OSM (Name, Adresse, Typ)
- [ ] Abgleich mit Web-Recherche: existiert der Laden noch? Stimmt der Name? Ergebnis in `research/pois_kreisN.csv`
- [ ] Darstellung: echter Name als Schild an der Fassade. Eigene Fassadengestaltung nur, wo das Original eindeutig dokumentiert ist; sonst eine neutrale Ladenfront.
- [ ] Wichtige Orte für Quests markieren (Schulhäuser, Labore/Spitäler für die Velokurier-Quest, Werbebildschirme)

### Stadtmobiliar
- [ ] Strassenlaternen (Typ nach Strassenart), Sitzbänke, Abfallkübel (Züri-Kübel), Hydranten
- [ ] Werbeflächen und digitale Werbebildschirme (Positionen recherchieren; Inhalte fiktiv)
- [ ] Velos, Trottinette, Züri-Säcke, Glascontainer, Litfasssäulen

### Beschriftung und Orientierung
- [ ] Strassenschilder (blaues Zürcher Schild) an Kreuzungen
- [ ] Hausnummern (aus amtlichen Adressen)
- [ ] Radar/Minimap mit Strassennamen und Kreis-Anzeige (Stil wie im Reel)

### Leben (nach dem ersten Milestone)
- [ ] Fussgänger:innen auf Trottoirs, Autos auf Strassen, Velos auf Velowegen
- [ ] Tageszeit und Licht, Nachtbeleuchtung der Läden

## Prüfmethoden
- Pro Landmark ein fester Kamerapunkt mit Screenshot, verglichen mit einem Referenzfoto (Mapillary, Wikimedia, eigene Fotos).
- Overlay-Check: Strassen- und Gebäudekanten aus der Vogelperspektive gegen SWISSIMAGE (Abweichung < 1 m).
- POI-Stichproben: 20 zufällige Läden pro Kreis gegen Webquellen prüfen.
