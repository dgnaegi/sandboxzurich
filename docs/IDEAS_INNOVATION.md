# Ideen: Innovation (unkonventionelle Wege zu mehr Realismus und Leben)

Stand 2026-10-16. Recherche aus Projektdocs, Websuche (nur wenige Lizenzchecks) und Fachwissen; Live-Seite nicht im Detail geprüft, kein Code geändert. Aufwand: S < 1 Tag, M 1-3 Tage, L 1-2 Wochen, XL > 2 Wochen. Lizenzampel: grün = laut `DATA_SOURCES.md`/OGD erlaubt, gelb = vor Nutzung auf der Datensatzseite prüfen, rot = nicht ohne Klärung.
**Ehrlicher Hinweis:** Links stammen teils aus dem Gedächtnis und sind nicht alle einzeln aufgerufen worden. Jede Lizenzzeile mit «gelb» vor dem Einbau verifizieren und dann in `DATA_SOURCES.md` eintragen. Wo ich etwas nicht bestätigen konnte, steht «unbestätigt».
Rahmen: statische Auslieferung (Cloudflare), kein Server-Zustand (siehe `ARCHITECTURE.md`). Ein zustandsloser Cloudflare-Worker als Proxy/Cache für Echtzeitdaten ist ein vertretbarer Sonderfall; vorher als Eintrag in `DECISIONS.md` festhalten.

## Top 5 «mutig aber machbar»
1. **#1 Fassaden-Grammatik aus eigenen Fotos lernen** (Fensterraster, Gesims, Sockel, Farbe als Parameter pro Haus statt Textur-Kopie). Grösster Hebel auf S6/S7 in `fidelity.md`, rechtlich sauber.
2. **#6 Klassifikation von Orthofoto/nDSM: automatische Hofbäume, Hecken, Parkfelder, Dachfarbe** per kleinem Segmentierungs-Modell oder reinen Rastermethoden (NDVI + nDSM).
3. **#12 Echtzeit-Tram (VBZ) als «Geister-Trams» im Spiel** mit Fahrplan-Treue (statisches GTFS genügt für 90 % des Effekts, GTFS-RT als Zusatz).
4. **#15 Zeitabhängiges Fussgänger-/Velo-Leben aus Zählstellen-OGD und ÖV-Frequenzen** (Langstrasse um 23 Uhr vs. Sonntag 8 Uhr).
5. **#18 Klanglandschaft aus Strassenlärm-Karte** (Lärmpegel steuert Mix aus Verkehr/Vögel/Stille pro Ort).

## Top 5 «schnelle Gewinne»
1. **#21 «Stimmt etwas nicht?»-Knopf + Korrektur-Import** (S, `apply_corrections.py` existiert schon).
2. **#10 Echter Sonnenstand/Datum/Uhrzeit des Spielers** (SunCalc, 50 Zeilen) plus Jahreszeit aus Datum.
3. **#14 Wetter-Anbindung MeteoSchweiz/Open-Meteo** als Option («echtes Wetter jetzt») auf bestehenden Wetter-Presets.
4. **#4 Dachfarbe aus SWISSIMAGE-Median pro Gebäude** (S-M, Skript).
5. **#20 Wiedererkennungs-Test «Wo bin ich?»** mit Einheimischen (Screenshot-Kontaktbogen, 10 Personen, 1 Abend) als Mess-Schleife für alles andere.

---

## Katalog

### A. Aussehen aus Daten und eigenen Aufnahmen

**#1 Fassaden-Grammatik lernen (Stil statt Kopie)**
- Beschreibung: Aus eigenen Fotos pro Haus nur Parameter extrahieren (Anzahl Fensterachsen, Stockwerkhöhe, Sockelhöhe, Fensterformat, Laden/Balkon, Putzfarbe, Läden-Farbe) und in die vorhandene Notiz-Pipeline (`visual_notes_v3.json`) schreiben. Zusätzlich ein Klassifikator Baujahr/Typ → Default-Grammatik (Gründerzeit, 50er, Genossenschaft, 70er-Beton). Fensterraster-Erkennung: CNN/Segmentierer auf Fassadenbild, Regelmässigkeit per FFT/Autokorrelation.
- Realismus: sehr hoch (Fassade ist das, was Einheimische zuerst als «falsch» lesen).
- Machbarkeit: Lernen läuft offline in der Pipeline, im Browser nur Parameter; null Laufzeitkosten.
- Aufwand: L (Foto-Spaziergänge P3 sind der Engpass, nicht die Technik).
- Lizenz: grün, wenn eigene Fotos (Gesichter/Kennzeichen verwischen). Panoramax/Mapillary-Bilder nur als Referenz, nie als Trainingsdaten für ausgelieferte Assets (CC BY-SA, Share-Alike-Wirkung unklar: gelb/rot). Trainings-/Parameterextraktion aus Fremdfotos rechtlich nicht geklärt, daher nicht empfohlen.
- Erste Schritte: 1) Schema `facade_params` (Achsen, Höhen, Farben) definieren; 2) 30 Häuser Langstrasse per Hand aus eigenen Fotos erfassen; 3) Windowdetektor (z. B. vortrainiertes CMP-Facade-Modell) auf eigene Fotos testen, Trefferquote messen.
- Refs: CMP Facade Database https://cmp.felk.cvut.cz/~tylecr1/facade/ ; Müller et al. «Procedural Modeling of Buildings» (SIGGRAPH 2006); Kelly et al. «FrankenGAN» (SIGGRAPH Asia 2018) https://dl.acm.org/doi/10.1145/3272127.3275065 ; Open-Source `CityEngine`-Alternativen: Houdini/Blender «Building Generator» (nur Ideenquelle).

**#2 Gaussian Splatting / NeRF von EIGENEN Aufnahmen für einzelne Wahrzeichen**
- Beschreibung: 3-5 Orte (Helvetiaplatz, Bahnhofbrücke, Hardbrücke-Unterführung) mit Handy filmen, Reconstruction per Nerfstudio/Postshot, Ergebnis nur als «Referenz» oder in vereinfachtes Mesh/Textur-Atlas überführen. Direkt als Splat im Spiel: möglich (three.js Splat-Viewer), aber stilfremd zu stilisierter Welt.
- Realismus: hoch an einem Ort, aber Stilbruch und Aufwand.
- Machbarkeit: Splats 5-30 MB pro Ort, auf dem Handy langsam (Sortierung); besser nur zur Messung/Referenz oder als Mesh-Bake.
- Aufwand: L pro Ort inklusive Aufräumen; Daten selbst S.
- Lizenz: eigene Aufnahmen = grün (Panoramafreiheit CH Art. 27 URG gilt für Aussenansicht vom öffentlichen Grund; Personen/Kennzeichen entfernen; Kunstwerke/Reklamen nicht 1:1 als Asset). Splat-Software separat prüfen: Original-3DGS (INRIA) nur nicht-kommerziell (gelb), Nerfstudio/gsplat Apache-2.0 (grün).
- Erste Schritte: einen Ort mit 150 Fotos aufnehmen, Nerfstudio-Splatfacto laufen lassen, Lesbarkeit der Fassadenmasse prüfen (Geometrie-Referenz statt Asset).
- Refs: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/ ; https://docs.nerf.studio ; https://github.com/nerfstudio-project/gsplat ; https://github.com/mkkellogg/GaussianSplats3D (Three.js-Viewer).

**#3 Texturen aus Satellit/Orthofoto für Böden**
- Beschreibung: SWISSIMAGE-Pixel (10 cm) als Detailquelle für Plätze/Höfe: nicht 1:1 als Textur (Schatten, Autos eingebrannt), sondern Materialklassen pro Fläche (Asphalt, Kies, Rasen, Pflaster) und Medianfarbe als Tint auf die Prozedural-Textur.
- Realismus: mittel-hoch (Plätze wirken richtig farbig).
- Machbarkeit: Pipeline-Schritt, keine Laufzeitkosten.
- Aufwand: M. Lizenz: swisstopo OGD, Quellenangabe (grün).
- Erste Schritte: pro Bodenpolygon Median-RGB + Streuung berechnen, in `ground_paint.py` als Tint; Vorher/Nachher auf Kontaktbogen.
- Refs: https://www.swisstopo.admin.ch/de/orthobilder-swissimage-10-cm

**#4 Dachfarbe/Dachtyp aus Orthofoto + LoD2**
- Beschreibung: pro Gebäude Median unter Polygon aus SWISSIMAGE → Dachtint (Ziegelrot, Eternit, Kies, Gründach per NDVI); Dachaufbauten (Gauben, Kamine) aus Stadt-ZH-Dachmodell LoD2 (siehe `IDEAS_MAP.md` D1/P4).
- Realismus: hoch aus Erhöhung (Hügel, Tram, Hardbrücke).
- Machbarkeit: sehr gut. Aufwand: S-M. Lizenz: grün (OGD); LoD2-Jahrgang vorher prüfen (gelb).
- Erste Schritte: `roof_tint.py` für Kreis 4 als Probe, 20 Dächer visuell gegen Luftbild prüfen.
- Refs: siehe `IDEAS_MAP.md` P4.

**#5 Stil-Transfer / «Look-Dev» mit ML nur im Werkzeugkasten**
- Beschreibung: Stil-Transfer (Neural Style Transfer, ControlNet) NICHT zur Laufzeit, sondern um Referenzbilder in den Spielstil zu übersetzen und Atlas-Texturen zu malen. Generierte Texturen als Material-Basis (Putz, Beton, Asphalt-Varianten).
- Realismus: mittel; Gewinn vor allem Tempo bei Material-Vielfalt.
- Machbarkeit: offline. Aufwand: M.
- Lizenz: gelb. Generierte Bilder aus Fotos Dritter (Street View) = rot. Aus eigenen Fotos oder reinem Text-Prompt: Modell-Lizenz prüfen (Stable Diffusion: CreativeML Open RAIL++-M erlaubt kommerziell mit Auflagen).
- Erste Schritte: 8 kachelbare Putztexturen aus eigenen Fotos mit Seamless-Tiling-Workflow, A/B im Spiel.
- Refs: https://huggingface.co/stabilityai ; https://github.com/lllyasviel/ControlNet

**#6 ML-Segmentierung von Orthofotos (Bäume, Wege, Parkfelder, Hecken)**
- Beschreibung: Mit nDSM (Höhe) + NDVI + einem kleinen Segmentierer (Segment Anything, OpenEarthMap-Modelle) Bäume/Hecken/Parkfelder/Wege finden, die in Kataster fehlen: Hofbäume, parkierte Autos als Dichtekarte, Velostreifen-Farbe.
- Realismus: hoch (Quartiercharakter: Hinterhöfe, Hecken).
- Machbarkeit: offline, Ergebnis als GeoJSON. Aufwand: L.
- Lizenz: Daten grün; Modelle: SAM Apache-2.0 (grün); Trainingsdatensätze (OpenEarthMap CC BY-NC-SA → nur Eval, nicht Training für Auslieferung: gelb).
- Erste Schritte: 500×500 m Kreis 4, nDSM-Spitzen > 3 m abzüglich Gebäude = Baumkandidaten; mit Baumkataster vergleichen (Recall/Precision), Lücken als `trees_extra.json`.
- Refs: https://github.com/facebookresearch/segment-anything ; https://open-earth-map.org ; swisstopo swissSURFACE3D https://www.swisstopo.admin.ch/de/hoehenmodell-swisssurface3d ; Kanton ZH Höhendaten (siehe `IDEAS_MAP.md` D3).

**#7 LiDAR-Detailmodelle (Mauern, Treppen, Böschungen, Vordächer)**
- Beschreibung: Aus Kanton-ZH-LiDAR (≥16 Pkt/m²) Punktwolke in Klassen (Boden/Gebäude/Vegetation/Brücke) auswerten: Stützmauern, Rampen, Vordächer, Kranbahnen; Höhenfehler am Gelände korrigieren (Strassen-Height-Raster existiert schon).
- Realismus: hoch an Hanglagen und Brücken (S13).
- Machbarkeit: offline (LAZ → PDAL → Raster). Aufwand: L.
- Lizenz: OGD, Quelle Kanton ZH (grün; auf Datensatzseite bestätigen).
- Erste Schritte: LAZ-Kachel Hardbrücke laden, PDAL-Klassen 6/17 (Gebäude/Brücke) extrahieren, Brückenträger-Querschnitt messen und gegen das Spielmodell legen.
- Refs: https://www.zh.ch/de/planen-bauen/geoinformation/geodaten/hoehendaten.html (unbestätigt, genaue URL in `IDEAS_MAP.md` D3) ; https://pdal.io ; https://github.com/potree/potree (nur Sichtkontrolle).

**#8 Photogrammetrie-Ableitung aus swisstopo 3D-Tiles / swissBUILDINGS3D als Prüfstein**
- Beschreibung: swisstopo liefert swissBUILDINGS3D als Cesium-3D-Tiles-Dienst. Als Qualitätsvergleich (Dachformen, Höhen) nutzen, nicht als Asset ausliefern. Texturierte Photogrammetrie-Layer von swisstopo (swissTLM3D-/Luftbild-Mesh) nicht herunterladen.
- Realismus: mittel (Prüfmittel). Machbarkeit: offline. Aufwand: S.
- Lizenz: swissBUILDINGS3D OGD (grün). Den Cesium-/Dienst-Datenstrom bei Massenabruf gegen Nutzungsbedingungen prüfen; Bezug per Bulk-Download statt Tiles-API (gelb).
- Erste Schritte: 10 Gebäude pro Kreis, Dachfirst Spiel vs. Dienst vergleichen (ergänzt `P5` in `IDEAS_MAP.md`).
- Refs: https://docs.geo.admin.ch/visualize-data/3d-tiles.html ; https://github.com/CesiumGS/3d-tiles ; Open-Source-Loader 3DTilesRendererJS https://github.com/NASA-AMMOS/3DTilesRendererJS

**#9 Gebäudeeingänge, Hausnummern und Klingelschilder als Lesbarkeits-Detail**
- Beschreibung: Eingänge (GWR/AV) als Tür + Nummernschild; im Spiel lesbar (Hausnummer-Emaille-Schild Zürich: weiss-blau-rot). Wer sein Haus sucht, findet es.
- Realismus: hoch für Wiedererkennung. Machbarkeit: sehr gut (Instanced Quads). Aufwand: M.
- Lizenz: grün (OGD). Namen auf Klingeln nie (Datenschutz).
- Erste Schritte: Eingangspunkte laden, an Fassade projizieren (Snap an Polygonkante), 1 Strasse testen.
- Refs: siehe `IDEAS_MAP.md` D10.

### B. Echtzeit und Zeit

**#10 Sonne, Datum, Jahreszeit wie draussen**
- Beschreibung: Spielzeit = echte Zeit (Option), Sonnenposition via SunCalc, Tageslänge, Jahreszeit-Paletten (Laubfarbe, Kastanienblüte, Schnee in Dez-Feb optional), Sonnenuntergang über dem Üetliberg.
- Realismus: hoch (Schattenwinkel und Tageslicht stimmen mit dem überein, was man draussen sieht).
- Machbarkeit: trivial. Aufwand: S. Lizenz: SunCalc BSD-2 (grün).
- Erste Schritte: `suncalc` einbinden, Lichtrichtung/Himmelsfarbe daran koppeln, Zürich-Koordinaten 47.378 N, 8.52 E.
- Refs: https://github.com/mourner/suncalc

**#11 Saisonale Varianten (Frühling/Sommer/Herbst/Winter)**
- Beschreibung: Baum-Tint-Presets pro Monat (Blüte Apr, Grün Jun, Herbstfarben Okt; kahl Dez), Strassenbeläge, Weihnachtsbeleuchtung Bahnhofstrasse/Niederdorf ab Nov, Sechseläuten (Apr), Street Parade (Aug), Fasnacht. Laubfarbe ist schon «gewollt Herbst» (S8): als Preset statt Festwert.
- Realismus: hoch (Wiedererkennen: «ist wie jetzt gerade»). Machbarkeit: gut (Shader-Uniform + wenig Instanzen). Aufwand: M.
- Lizenz: grün (Eigenbau). Lichter-Installationen (Lichtshow, Marken) nicht 1:1.
- Erste Schritte: Tint-Uniform pro Baumart (Kataster hat Art), Monats-Lookup-Tabelle, Test mit Kontaktbogen 4 Jahreszeiten.
- Refs: `IDEAS_LOOK.md` Abschnitte B/D.

**#12 Echtzeit-ÖV: Trams und Busse nach Fahrplan (GTFS statisch + GTFS-RT)**
- Beschreibung: Aus statischem ZVV-GTFS (Fahrplan als Zeittabelle) laufen Trams linienrichtig, fahrplantreu zur Echtzeit-Uhrzeit. Zusätzlich GTFS-RT (Verspätungen/Positionen) von opentransportdata.swiss: Trams stehen dort, wo sie draussen gerade sind.
- Realismus: hoch + «magisch» (man sieht das 4er-Tram genau dann, wenn es kommt).
- Machbarkeit: statisches GTFS vorab zu kompaktem JSON bauen (kein Server). GTFS-RT braucht API-Key und liefert kein CORS: Proxy-Worker nötig (Key serverseitig, gecacht). Für die Handy-Last unkritisch (wenige Dutzend Fahrzeuge).
- Aufwand: statisch M, RT L.
- Lizenz: Statisches GTFS auf opentransportdata.swiss/opendata.swiss «offene Nutzung, Quellenangabe» (grün, laut Suchtreffern). GTFS-RT: Nutzungsbedingungen und Key-Pflicht auf der Datensatzseite nicht bestätigt (gelb); Registrierung auf https://opentransportdata.swiss, Weitergabe der Rohdaten ggf. eingeschränkt, deshalb nur abgeleitet anzeigen.
- Erste Schritte: 1) ZVV-GTFS (opendata.swiss «zvv-fahrplan-tram-und-bus-static-gtfs») laden, Linie 4/13/2/3 für Kreise extrahieren; 2) `stop_times` → Abfahrtsraster im JSON; 3) Tram-Entities im Spiel auf Gleisgraph mit Fahrplan-Zeit verknüpfen.
- Refs: https://opentransportdata.swiss/de/cookbook/gtfs-rt/ ; https://opentransportdata.swiss ; https://gtfs.org/realtime/ ; https://opendata.swiss/en/dataset/zvv-fahrplan-tram-und-bus-static-gtfs1

**#13 Abfahrtsanzeiger (DFI) live auf den Haltestellen**
- Beschreibung: Die DFI-Anzeigen (aus `haltestellen_dfi_anzeiger`) zeigen echte nächste Abfahrten (aus GTFS), im Spiel lesbar. Mini-Detail mit grossem Wiedererkennungswert.
- Realismus: hoch (Detail). Machbarkeit: Canvas-Textur, trivial. Aufwand: S (nach #12).
- Lizenz: wie #12. Erste Schritte: Canvas-Anzeige pro Haltestelle, nur Linie/Ziel/Min.
- Refs: wie #12.

**#14 Echtes Wetter jetzt (MeteoSchweiz / Open-Meteo)**
- Beschreibung: Option «Wetter wie draussen»: Regen, Nebel (Hochnebel im Herbst!), Wind, Temperatur. MeteoSchweiz hat seit 2025 viele OGD-Daten frei (Open Data Strategie). Bequemer: Open-Meteo (kostenlos nicht-kommerziell, CORS offen).
- Realismus: mittel-hoch, vor allem Stimmung. Machbarkeit: ein fetch pro 10 Min, Fallback auf Preset. Aufwand: S.
- Lizenz: MeteoSchweiz OGD (CC BY, Quellenangabe; gelb bis Seite bestätigt); Open-Meteo: CC BY 4.0 Daten, Gratis-API nur nicht-kommerziell (gelb: Nutzungsbedingungen prüfen oder Self-Host der MeteoSwiss-Daten).
- Erste Schritte: Open-Meteo Forecast-Aufruf mit `current=weather_code,cloud_cover,wind_speed_10m`, Mapping auf bestehende Wetter-Presets.
- Refs: https://open-meteo.com/en/docs ; https://opendatadocs.meteoswiss.ch/ ; https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html

**#15 Simulation: Leben nach Uhrzeit und Frequenz**
- Beschreibung: Fussgängerdichte pro Ort/Zeit aus Zählstellen-OGD (Stadt ZH Fussgänger-/Velozählungen, Viertelstunden-/Stundenwerte) und ÖV-Frequenzen (Passagierzahl pro Haltestelle). Beispiel: Langstrasse Fr 23 Uhr dicht, Sonntag Morgen leer, Pendlerspitze am HB. Veloverkehr aus Velozählstellen (Wetter-/Jahreszeit-Skalierung). Verlässliche Wochenprofile als kleine JSON-Tabelle, keine Laufzeit-Rechenlast.
- Realismus: sehr hoch («die Stadt atmet»). Machbarkeit: sehr gut, vorhandenes NPC-System nur über Spawnraten steuern. Aufwand: M.
- Lizenz: Zählungen opendata.swiss/Stadt ZH, offene Nutzung (laut Suchtreffer; Datensatzseite prüfen, gelb→grün).
- Erste Schritte: Zählstellen mit Koordinaten laden, Wochenprofil (7×24) pro Stelle, Interpolation per Inverse-Distanz auf NPC-Spawn.
- Refs: https://data.stadt-zuerich.ch (Suche «Verkehrszählungen Werte Fussgänger Velo») ; Agentenbasiert: Helbing «Social Force Model» (1995) https://arxiv.org/abs/cond-mat/9805244 ; Crowd in Browser: https://github.com/recastnavigation/recastnavigation (WASM-Ports vorhanden).

**#16 Parkplatzbelegung und Autodichte zeitabhängig**
- Beschreibung: Parkhaus-Belegung live (Stadt ZH Parkleitsystem: Parkhäuser in Echtzeit) und typische Belegung der Blauen Zone nach Tageszeit (nachts hoch, tags tiefer). Heute sind 90 % der Blaue-Zone-Felder statisch besetzt (S5).
- Realismus: mittel-hoch. Machbarkeit: gut. Aufwand: S-M (Profil) / M (live).
- Lizenz: Parkleitsystem-Daten Stadt ZH (CC BY?, unbestätigt: gelb), Live-Abruf braucht CORS-Prüfung.
- Erste Schritte: Tageskurve (0.9 nachts → 0.6 mittags) auf `cityprops.py`-Besetzung als Laufzeit-Parameter.
- Refs: https://data.stadt-zuerich.ch (Suche «Parkleitsystem»)

**#17 Tag-Nacht-Aktivität der Läden (Öffnungszeiten aus OSM)**
- Beschreibung: Schaufenster hell/dunkel, Rollläden zu, Gastgarten besetzt, Bars nachts beleuchtet nach OSM `opening_hours`. Wiedererkennen: «um 3 Uhr ist die Langstrasse Bars, tagsüber Gemüseläden».
- Realismus: hoch. Machbarkeit: gut (Emissive-Parameter, Parser `opening_hours.js` ist klein). Aufwand: M.
- Lizenz: ODbL (grün). Erste Schritte: `opening_hours` für Langstrasse-Läden auswerten, nur Anteil mit gültigem Tag sichtbar.
- Refs: https://github.com/opening-hours/opening_hours.js

### C. Klang

**#18 Klanglandschaft aus Lärmkarten (Strassenlärm OGD)**
- Beschreibung: Strassenlärm-Immissionskarten (Stadt ZH/BAFU, Lden/Lnight, dB(A)) steuern Mix und Lautstärke: Verkehrsrauschen hoch an Hardbrücke/Hohlstrasse, Vogelgezwitscher und Brunnen in Hinterhöfen/Parks, Kirchenglocken zu echten Zeiten (Viertelstunden-Schläge, Samstag 11 Uhr Läuten). Lärmkarte als 2D-Raster, abgefragt an Spielerposition, Mixer mit 4-6 Loops.
- Realismus: sehr hoch fürs Gefühl («hier ist es laut, dort ist ein stiller Hof»). Machbarkeit: gut, Audio-Loops kleine Opus-Dateien. Aufwand: M.
- Lizenz: Lärmdaten OGD (BAFU/Stadt ZH, CC BY/CC0 je Datensatz: gelb); Sounds nur CC0/eigene Aufnahmen (freesound CC0 filtern; eigene Feldaufnahmen sind grün).
- Erste Schritte: Raster (25 m) in 8-Bit PNG exportieren; 4 Loops (Verkehr, Hof, Park, Platz) + Zonen-Mix; Feldaufnahmen am Helvetiaplatz (5 Min).
- Refs: https://data.stadt-zuerich.ch (Suche «Strassenlärm») ; https://www.bafu.admin.ch/bafu/de/home/themen/laerm/zustand/laermbelastung.html ; https://freesound.org (CC0 filtern) ; Web Audio Spatial https://developer.mozilla.org/docs/Web/API/Web_Audio_API/Web_audio_spatialization_basics

**#19 Glocken und Stadtklang zur echten Zeit**
- Beschreibung: Kirchturmuhren (Grossmünster, St. Jakob, Kreis 4/5-Kirchen aus OSM) schlagen nach echter Uhrzeit; Tram-Klingeln, Anflug-Lärm Flug (Flughafen, Ost-/Südanflug je Tageszeit) leise im Hintergrund.
- Realismus: mittel-hoch. Machbarkeit: sehr gut. Aufwand: S.
- Lizenz: eigene Aufnahmen/CC0 (grün). Erste Schritte: 1 Glockenschlag-Sample, Position aus OSM `amenity=place_of_worship` mit Turm.
- Refs: freesound.org (CC0).

### D. Community, Messen, Recht

**#20 Wiedererkennungs-Tests mit Einheimischen als Messgrösse**
- Beschreibung: «Wo bin ich?»-Quiz: 12 Spiel-Screenshots (Kontaktbogen), Testpersonen aus Kreis 3/4/5 sagen den Ort in 10 Sekunden. Metrik: Trefferquote pro Kreis, Zeit bis zur Erkennung, «was fehlt?». Ergebnisse als Liste Priorität für Fassaden/Details. Alternativ im Spiel selbst: Foto-Modus «Erkenne den Ort» als Teaser.
- Realismus: Mess-Schleife (steuert alles andere). Machbarkeit: sehr gut. Aufwand: S.
- Lizenz: Einwilligung der Testpersonen, keine personenbezogenen Daten speichern.
- Erste Schritte: 12 feste Kamerapunkte (existieren in Playwright), Google-Formular-frei (z. B. Framaforms/Tally), 10 Personen.
- Refs: Lynch «The Image of the City» (1960) als Methode «Wahrnehmung der Elemente» https://mitpress.mit.edu/9780262620017/the-image-of-the-city/

**#21 «Stimmt etwas nicht?»-Knopf + Korrektur-Import (ohne Server)**
- Beschreibung: Knopf in Pause/Fotomodus baut einen vorausgefüllten Link auf ein GitHub-Issue-Formular (Issue Forms YAML) oder `mailto:` mit `x,y`, Kachel, Version, Blickrichtung. `pipeline/apply_corrections.py` (existiert als Datei) übernimmt als Overrides. Siehe `IDEAS_MAP.md` P1/P2.
- Realismus: Dauerhaft hoch (Quartierwissen). Machbarkeit: sehr gut, kein Backend. Aufwand: S.
- Lizenz: Foto-Beilage nur mit ausdrücklicher CC0-Erklärung; keine Personendaten; GitHub-Konto-Pflicht ist Hürde (Alternative: öffentliches Formular).
- Erste Schritte: Issue-Template `.github/ISSUE_TEMPLATE/korrektur.yml`, Link-Builder in Pause-Menü, Test mit 3 Personen aus dem Quartier.
- Refs: https://docs.github.com/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms

**#22 Community-Foto-Walks mit Auswertung ohne Fremdfotos**
- Beschreibung: Team filmt Strassenzüge, Skript (OpenCV) extrahiert Frames, wählt scharfe aus, verwischt Gesichter/Kennzeichen (z. B. YOLO-basierte Open-Source-Blur), legt `research/walks/<kreis>/` ab. Nutzung: Parameter für #1, #9, #17; Texturausschnitte nur aus eigenen Aufnahmen.
- Realismus: Basis für fast alles. Machbarkeit: offline. Aufwand: M (+ Mensch-Zeit).
- Lizenz: grün bei eigenem Material und Einwilligung. Schweiz: Aufnahmen vom öffentlichen Grund erlaubt, Persönlichkeitsrecht beachten (Gesichter unkenntlich).
- Erste Schritte: Wochenende Langstrasse, Insta360/Handy, Skript `walk_frames.py` (Sharpness-Filter).
- Refs: https://github.com/facebookresearch/EgoBlur (Apache-2.0, unbestätigt) ; https://opencv.org

**#23 «Kreis-Paten»: Experten-Review mit Checkliste**
- Beschreibung: Pro Kreis 2-3 Personen mit Ortskenntnis prüfen den Kontaktbogen anhand fester Checkliste (Ladennamen, Tramhaltestellen, Plätze, Brunnen, Graffiti-Hotspots). Resultat strukturiert → Overrides. Verbindet Quartier-Community mit Datenqualität.
- Realismus: hoch. Machbarkeit: sehr gut. Aufwand: S pro Kreis.
- Lizenz: keine Personendaten ausser Namen für Credits (Einwilligung). Erste Schritte: Checkliste aus `fidelity.md` ableiten, PDF-Kontaktbogen pro Kreis.

### E. Weitere Hebel

**#24 Graffiti, Plakate und Stadtspuren aus «Züri wie neu»-Dichte**
- Beschreibung: Dichte der Meldungen (Graffiti, Abfall, Sperrgut) steuert Menge an Graffiti-Decals, Abfall, Aufkleber an Masten. Aggregiert, nie Einzeltexte (siehe `IDEAS_MAP.md`, `zwn_meldungen_p`). Plakatstellen (Stadt ZH) zeigen wechselnde eigene Plakate.
- Realismus: hoch (Gebrauchsspuren machen Stadt echt). Machbarkeit: Decal-Instanzen, billig. Aufwand: M.
- Lizenz: Meldedaten Stadt ZH (CC0, laut `IDEAS_MAP.md`); Graffiti-Motive selbst gestalten (keine echten Tags kopieren, Urheberrecht der Sprayer*innen).
- Erste Schritte: Raster 50 m Dichte, 6 eigene Graffiti-Atlasmotive, Unterführungen priorisieren.
- Refs: siehe `IDEAS_MAP.md` Tabelle B.

**#25 Lebendige Hintergrund-Ereignisse aus offenen Kalendern**
- Beschreibung: Wochenmarkt (Rosengartenplatz), Flohmarkt (Kanzlei), Street Parade, Fanzonen, Baustellen aus Stadt-ZH-Baustellenkarte (Strassensperrungen!) erscheinen im Spiel mit Datum. Baustellen und Umleitungen sind das, was Einheimische wirklich im Alltag bemerken.
- Realismus: hoch, aber wartungsintensiv. Machbarkeit: gut, JSON-Kalender in Pipeline monatlich neu gebaut (kein Live-Server). Aufwand: M.
- Lizenz: Baustellen/Veranstaltungen Stadt ZH OGD (gelb je Datensatz).
- Erste Schritte: Stadt-ZH-Baustellen-Datensatz prüfen (unbestätigt, ob OGD), Markt-Zeiten manuell als `events.json` (existiert schon in `web/public/data/events.json`).
- Refs: https://data.stadt-zuerich.ch (Suche «Baustellen», «Märkte»)

**#26 Prozedurale Details aus Mustern, die nur 5 Regeln brauchen**
- Beschreibung: Wiederkehrende Elemente, die Einheimische täglich sehen, aus Regeln statt Einzelmodellierung: Poller-Reihen vor Schulen, Veloständer an Ladenfronten, Blumenkästen an Altbauten, Sonnenstoren/Markisen (Tag/Nacht aus Öffnungszeiten, #17), Handläufe, Briefkasten (gelb), Wäscheleinen in Hinterhöfen. Regelbasiert aus OSM-Tags + Gebäudetyp.
- Realismus: hoch pro Aufwand (viele kleine Dinge = «Atmosphäre»). Machbarkeit: Instanced Meshes, billig. Aufwand: M.
- Lizenz: grün (Eigenbau). Erste Schritte: 6 Prop-Typen, Platzierung nach Fassadenlänge, siehe `pipeline/props.py`.
- Refs: Wonka/Wonka-Style Split Grammar https://dl.acm.org/doi/10.1145/1141911.1141931

**#27 Mikro-Kartenwissen: Brunnen, Bänke, Denkmäler mit Tafelinfo als «Entdeckungen»**
- Beschreibung: Zusätzlich zu Quests: Foto-/Entdeckungsmodus, der echtes Quartierwissen belohnt (Blaue Tafeln, Brunnen, Kunst im öffentlichen Raum, Gebäudebrüter, Velopumpen). Unterstützt Wiederkennen und Lernen.
- Realismus: indirekt (Detailpflege wird belohnt). Machbarkeit: gut. Aufwand: M.
- Lizenz: OGD-Layer grün (CC0 laut `IDEAS_MAP.md` B). Texte selbst, keine Fremdtexte.
- Erste Schritte: 50 Entdeckungs-POIs aus Layern, Sammelalbum im Menü.

**#28 Offline-Qualitätsmessung: automatischer Foto-vs-Spiel-Score**
- Beschreibung: Eigene Fotos vs. Spiel-Screenshots am selben Standpunkt automatisch vergleichen (Farbhistogramm, Kantenstruktur, Himmelsanteil, SSIM/LPIPS) als Zahl pro Strassenzug; Fortschritt wird messbar statt «Gefühl». Erweitert `web/tests/fidelity_shots.mjs`.
- Realismus: indirekt (steuert Prioritäten). Machbarkeit: offline Python. Aufwand: M.
- Lizenz: nur eigene Fotos als Vergleichsbasis (Panoramax-Fotos nur lokal, nicht ausliefern: gelb, Auswertung ohne Weitergabe vermutlich ok).
- Erste Schritte: 20 Paare, Farbabstand im Lab-Raum für Fassadenband (Höhe 3-12 m) berechnen, Bericht als 30-Zeilen-Tabelle.
- Refs: https://github.com/richzhang/PerceptualSimilarity ; https://scikit-image.org (SSIM).

**#29 Photogrammetrie mit Drohne oder Handy für ganz kleine Details: nein, aber Referenz-Tour**
- Beschreibung: Nicht umsetzen: Drohnen über Stadtgebiet (Flugverbot Zone, Bewilligung, Persönlichkeitsrecht). Stattdessen 360°-Tour mit Bodenkamera (#22). Dokumentiert, damit die Idee nicht wieder aufkommt.
- Aufwand: – ; Lizenz/Recht: rot (Drohnenflug im Stadtgebiet bewilligungspflichtig, BAZL).
- Refs: https://www.bazl.admin.ch/bazl/de/home/drohnen.html

**#30 Cesium/Google Photorealistic 3D Tiles: bewusst NICHT**
- Beschreibung: Google Photorealistic 3D Tiles (Map Tiles API) wäre die schnellste «Wow»-Lösung, ist aber Fremddaten mit Auflagen (nur online abrufbar, Attribution, kein Caching/Ableiten) und widerspricht der Projektregel «Google nur zur Inspiration». Cesium World Terrain/OSM Buildings sind gelb (Cesium ion Konditionen). Als Variante: swisstopo-Tiles-Layer (#8) ausschliesslich als Vergleich.
- Lizenz: rot für Google; Machbarkeit technisch hoch, rechtlich/politisch ausgeschlossen.
- Refs: https://developers.google.com/maps/documentation/tile/3d-tiles ; https://cesium.com/platform/cesium-ion/content/

---

## Machbarkeit auf einen Blick

| # | Idee | Wirkung | Aufwand | Handy | Lizenz |
|---|---|---|---|---|---|
| 1 | Fassaden-Grammatik aus Fotos | sehr hoch | L | 0 | grün (eigene Fotos) |
| 2 | Gaussian Splatting eigener Orte | mittel | L | – | grün/gelb |
| 3 | Boden-Tint aus Orthofoto | mittel-hoch | M | 0 | grün |
| 4 | Dachfarbe aus Orthofoto | hoch | S-M | 0 | grün |
| 5 | ML-Texturen/Stil-Transfer (offline) | mittel | M | 0 | gelb |
| 6 | ML-Segmentierung Hofbäume etc. | hoch | L | 0 | grün/gelb |
| 7 | LiDAR-Detailmodelle | hoch | L | 0 | grün |
| 8 | swisstopo 3D-Tiles als Prüfstein | mittel | S | 0 | grün/gelb |
| 9 | Hauseingänge + Nummern | hoch | M | + | grün |
| 10 | Sonne/Datum/Saison echt | hoch | S | 0 | grün |
| 11 | Saisonale Varianten und Anlässe | hoch | M | + | grün |
| 12 | Echtzeit-ÖV | hoch | M/L | + | statisch grün, RT gelb |
| 13 | Abfahrtsanzeiger live | hoch | S | 0 | wie 12 |
| 14 | Echtes Wetter | mittel-hoch | S | 0 | gelb |
| 15 | Leben nach Zählstellen | sehr hoch | M | + | gelb→grün |
| 16 | Parkplatz-Belegung | mittel-hoch | S-M | 0 | gelb |
| 17 | Öffnungszeiten-Leben | hoch | M | + | grün |
| 18 | Klang aus Lärmkarte | sehr hoch | M | + | gelb |
| 19 | Glocken, Stadtklang | mittel-hoch | S | 0 | grün |
| 20 | Wiedererkennungs-Tests | Messung | S | 0 | grün |
| 21 | Korrektur-Knopf + Import | hoch dauerhaft | S | 0 | grün |
| 22 | Foto-Walks mit Auswertung | Basis | M | 0 | grün |
| 23 | Kreis-Paten-Review | hoch | S | 0 | grün |
| 24 | Spuren aus «Züri wie neu» | hoch | M | + | grün |
| 25 | Kalender: Märkte, Baustellen | hoch | M | 0 | gelb |
| 26 | Prozedurale Mikro-Details | hoch | M | + | grün |
| 27 | Entdeckungen aus OGD-Layern | indirekt | M | 0 | grün |
| 28 | Foto-vs-Spiel-Score | Messung | M | 0 | gelb |
| 29 | Drohne | – | – | – | rot |
| 30 | Google/Cesium Photoreal Tiles | – | – | – | rot |

## Empfohlene Reihenfolge
1. Woche 1: #10, #14, #21, #4, #20 (alles S, sofort sichtbar/messbar).
2. Woche 2-3: #22 Foto-Walk Langstrasse starten, #15 und #17 (Leben), #9.
3. Danach: #1 mit den Walk-Daten, #12 statisch, #18 Klang.
4. Später/Experiment: #6, #7, #2.

Offen: Rechtsfrage zu Modell-Training auf CC-BY-SA-Fotos (#1/#5) nicht geklärt; Rechtsberatung einholen, bevor so etwas ausgeliefert wird.
