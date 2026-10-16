# Ideen: Karte wiedererkennbar machen («das ist mein Quartier»)

Stand 2026-10-16. Recherche (Web + lokale Docs/Daten), kein Code geändert. Aufwand: S = unter 1 Tag, M = 1-3 Tage, L = mehr. Lizenzampel: grün = CC0/OGD/ODbL erlaubt laut `DATA_SOURCES.md`, gelb = vor Nutzung klären, rot = nicht verwenden.
Hinweis: Lizenzangaben stammen aus Suchtreffern der Katalogseiten. Jede Zeile, die «gelb» ist, vor dem Einbau auf der Datensatzseite prüfen und dann in `DATA_SOURCES.md` eintragen.

## Befund in vier Sätzen
1. Die Geometrie (Strassen, Grundrisse, Höhen) ist schon gut. Was Einheimische als «falsch» empfinden, sind Farben, Dachformen, Erdgeschoss-Mix, Möblierung und Bodenmarkierungen (siehe `research/fidelity.md` S1-S13).
2. Viele Stadt-ZH-Layer liegen schon in `data/raw/stadtzh_all/`, aber **im Pipeline-Code nicht verwendet** (Prüfung per grep in `pipeline/*.py`): `haltestellen_wartehalle/_plakatstelle/_dfi_anzeiger/_sitzgelegenheit/_ticketautomat/_papierkorb/_haltebalken`, `alle_hochhaeuser`, `gebaeudebrueter_inventar`, `vas_e_kunstbauten`, `blaue_tafeln_p`, `velopumpstationen_p`, `gruenflaechen`, `stadtnatur_ogd`, `zwn_meldungen_p`. Das ist die billigste Quelle für Wiedererkennung.
3. Nicht heruntergeladen, aber hochwertig: Dachmodell LoD2 (Stadt ZH), Baumhöhen 2018 (Kronenhöhenmodell), Kanton-ZH-LiDAR 2022 (DOM, nDSM).
4. Fassaden-Realismus ist rechtlich der Engpass (Google tabu, Mapillary/Panoramax CC BY-SA). Der saubere Weg sind eigene Fotos des Teams und fakten-basierte Attribute (Farbe, Läden, Stockwerke) statt Bildtexturen.

---

## A. Datensätze

| # | Datensatz | Link | Lizenz | Format / Auflösung | Abdeckung K3/4/5/9 | Nutzen für Wiedererkennung | Aufwand | Risiko |
|---|---|---|---|---|---|---|---|---|
| D1 | 3D-Dachmodell LoD2 Stadt ZH (Jahresstände 2011/13/15/18; auch «Bauten – Dachmodell 3D» und «Dachstrukturen 2D inkl. 3D») | https://ckan.opendata.swiss/dataset/3d-dachmodell-lod2-jahresstand-2018-3d , https://ckan.opendata.swiss/dataset/3d-dachmodell-lod2-jahresstand-2015-3d | Stadt ZH meist CC0; Metadaten einzelner Jahrgänge uneinheitlich («Keine Lizenz angegeben» bei 2011/2013) → 2018 bzw. 2015 nehmen und Lizenzfeld prüfen (gelb) | DXF/GDB/GPKG + WFS/WMS, Dachflächen als 3D-Polygone, Photogrammetrie | ganze Stadt | Dachform (Walm, Mansard, Gauben, Kamine, Dachterrassen) ist das, was man von oben und aus der Ferne am Quartier erkennt. Lokal schon als «zu gross» verworfen (>1 Mio. Features), deshalb nur Bbox-Abfrage pro Kreis | M (Abfrage per WFS-Bbox + Skript `pipeline/roofs_lod2.py`, Abgleich mit sb3d-Dächern; nur Gauben/Kamine/Dachtyp als Attribut statt volle Geometrie) | niedrig |
| D2 | swissBUILDINGS3D 3.0 Beta (schon in `data/raw/sb3d/`) | https://ckan.opendata.swiss/dataset/swissbuildings3d-3-0-beta , https://www.swisstopo.admin.ch/en/geodata/landscape/buildings3d3.html | OGD, «Opendata BY», Quelle nennen (grün) | CityGML/FileGDB, Dächer manuell stereo-extrahiert, Dachüberstände, Fassaden abgeleitet, EGID-Zuordnung; Zürich ist abgedeckt | alle | Dachüberstände und EGID: Verknüpfung zu GWR (Nutzung, Stockwerke, Baujahr) → Fassadenstil nach Baujahr statt Zufall | S-M (EGID-Join prüfen, ob schon gemacht: `pipeline/buildings_info.py`) | niedrig. «LOD2/Dachaufbauten» in Suchtreffern nicht bestätigt, Doku prüfen |
| D3 | Kanton ZH Höhendaten 2022 (LiDAR ≥16 Pkt/m², DTM, DOM, nDSM Gebäude/Vegetation) | https://www.zh.ch/de/news-uebersicht/mitteilungen/2023/planen-bauen/geoinformation/aktuelle-hoehendaten-fuer-den-kanton-zuerich.html , Download `maps.zh.ch/download/hoehen/2022` | OGD, kostenlos (grün, Quellenangabe Kanton ZH) | Raster/LAZ, 0.5 m typ. | ganzer Kanton | Prüfung (siehe Abschnitt C): Gebäudehöhen/Dachfirst, Baumkronen, Mauern und Hecken (nDSM) automatisch gegen unser Modell testen; fehlende Vegetationshöhen | M | niedrig |
| D4 | Baumhöhen 2018 (LiDAR-Kronenmodell Stadt ZH) | https://opendata.swiss/en/organization/stadt-zurich (Suche «Baumhöhen») | Stadt ZH, vermutlich CC0 (gelb: prüfen) | Raster TIFF/WMS | Stadt | echte Kronengrössen auch von privaten Bäumen/Hinterhöfen, die nicht im Baumkataster stehen (Hofbäume = Quartiercharakter) | M | niedrig |
| D5 | Kanton ZH Orthofoto 2021/22 «blattfrei» (Frühling) | https://www.zh.ch/de/news-uebersicht/mitteilungen/2022/planen-bauen/geoinformation/neue-aufnahmen-aus-der-vogelperspektive.html | OGD, frei downloadbar (grün) | RGB, blattfrei = Dächer/Höfe sichtbar | Kanton | Dachfarben, Hofbegrünung, Vorgärten und Parkplatzflächen messen (Skript statt Auge); SWISSIMAGE 10 cm liegt schon vor | S-M | niedrig |
| D6 | Stadt ZH Schrägluftbilder | nicht als OGD-Datensatz gefunden (Suche ohne Treffer) | unbekannt (rot, bis geklärt) | – | – | Fassaden von oben-schräg wären ideal für Farbe/Geschosszahl. Nur ansehen (wie Google), nichts speichern. Bei Stadt ZH Geomatik nachfragen, ob frei | S (Mail) | hoch, wenn man unklar speichert |
| D7 | Stadt ZH 3D-Stadtmodell texturiert | in Suche **nicht** gefunden; vorhandene OGD-Pakete sind untexturiert (`geo_3d_stadtmodell_*`) | – | – | – | Kein Weg über OGD. Nicht weiterverfolgen, ausser Stadt bietet es auf Anfrage an | – | – |
| D8 | Stadt-ZH-Layer lokal vorhanden, aber ungenutzt | `data/raw/stadtzh_all/*` (siehe Befund 2) | CC0 | GeoJSON, Punkte/Linien | im Bereich | siehe Tabelle B | S je Layer | niedrig |
| D9 | Layer ohne eigenen Datensatz | Gründächer, Fassadenbegrünung, Vorgärten, Hofbegrünung: kein OGD-Layer gefunden (Suche + `ogd_catalog.md`) | – | – | – | Ableitung aus Orthofoto (NDVI/Grünanteil) + Kronenmodell + `bodenbedeckung_a` (Rasen/Garten). Fassadenbegrünung nur manuell (Overrides) | M | niedrig |
| D10 | Gebäudeeingänge / Hauseingänge | GWR/Amtliche Vermessung «Gebäudeeingang» (EGAID, Eingangspunkte) | OGD swisstopo/AV (gelb: Layer in Stadt-ZH-Katalog als «ausser Ziel» aussortiert, nochmals prüfen) | Punkte mit Adresse | alle | Haustür + Hausnummer an der Strasse, Klingelbrett: ein Haus wird «meins» durch seine Tür | M | niedrig |
| D11 | Mapillary / Panoramax als Quelle für 3D/Texturen | https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data , https://docs.panoramax.fr/federated-catalog/ | CC BY-SA 4.0. Panoramax erlaubt «nicht-fotografische abgeleitete Daten» unter ODbL/CC-BY/LO 2.0 (explizit OSM-France-Instanz, bei anderen nur empfohlen). Mapillary-AGB: kein Aufbau einer «Datenbank von Orten» ohne Erlaubnis | **Fotos/Texturen/3D-Rekonstruktion = rot** (Share-Alike würde auf das ganze Spiel-Asset zielen und ist mit Scalingo-Auslieferung unklar). **Fakten daraus lesen = gelb-grün**: Farbe, Anzahl Fenster, Ladentyp als Attribut per Hand notiert, mit Namensnennung im Credits-Screen | – | Genau so, wie wir es heute für `fidelity.md` tun: Foto nur als Referenz, Attribute selbst schreiben | schon Praxis | mittel bei Textur, niedrig bei Fakten. Rechtsfrage zur 3D-Rekonstruktion: kein Treffer, daher nicht empfehlen; im Zweifel Panoramax-Betreiber / Mapillary fragen |
| D12 | Fassadenfoto-Datensätze mit offener Lizenz | keine geeignete CC0-Sammlung für Zürcher Fassaden gefunden. Wikimedia Commons hat viele Zürcher Fassaden (CC BY/BY-SA), pro Bild | CC BY-SA = Textur rot; CC0/PD-Bilder gelb | – | punktuell | nicht als Textur. Nur als Referenz für Handnotizen | – | mittel |
| D13 | Eigene Aufnahmen (siehe Abschnitt C) | – | eigene Lizenz, frei | – | beliebig | einzige Quelle, aus der Fassaden-Texturen und Schilder legal entstehen können | M-L | niedrig |

## B. Stadt-ZH-OGD-Layer: was noch fehlt oder ungenutzt ist (alle CC0, `data/raw/...` falls vorhanden)

| Layer (Datei) | Wiedererkennung | Aufwand |
|---|---|---|
| `haltestellen_wartehalle`, `_sitzgelegenheit`, `_papierkorb`, `_plakatstelle`, `_dfi_anzeiger`, `_ticketautomat`, `_haltebalken`, `_infosystem` | Jede Tramhaltestelle wird mit Wartehäuschen, Bank, Anzeige, Billettautomat an der echten Stelle gebaut statt als Standardperron. Hohe Wirkung, da man täglich dort steht | S-M |
| `alle_hochhaeuser` | Skyline: Prime Tower, Hochhäuser Escher-Wyss, Hardau: Höhen/Position prüfen und Landmark-Modelle | S |
| `vas_e_kunstbauten` | Brücken, Stützmauern, Unterführungen an echten Stellen (Langstrasse-Unterführung, Hardbrücke) | M |
| `blaue_tafeln_p`, `denkmalpflege_inventar_p`, `gdp_objekte` | Blaue Tafeln/Inventarobjekte als Infotafel (Heritage ist teils schon in `buildings_info.py`) | S |
| `gebaeudebrueter_inventar` | Mauersegler/Schwalben-Nester als Easter-Egg (Geräusche, kleine Vögel) | S |
| `velopumpstationen_p` | Velopumpen an echten Stellen (kleines Detail, Velofahrende erkennen sie) | S |
| `tbl_knoten_p`, `uebergaenge` | Ampelknoten-Position vs. unsere Ampeln abgleichen; Schulweg-Fussgängerstreifen | S |
| `kunst_im_stadtraum`, `brunnen`, `spielplaetze`, `sitzbaenke`, `zueri_wc`, `abfallgefaesse` (in `stadtzh_extra`) | Schon geladen; nur sicherstellen, dass alle als Modelle erscheinen (Brunnen mit Wasser und richtigem Typ, Kunstwerke als Platzhalter-Skulptur mit Tafel) | S |
| `stadtnatur_ogd`, `gruenflaechen`, `alleenkonzept_baumreihen` | Hecken, Wiesen, Alleen: Strassenbild Bäume in Reihe | S-M |
| `zwn_meldungen_p` («Züri wie neu», 48 980 Punkte) | Wo Graffiti/Kaugummi/Abfall gemeldet wird: Dichte steuern (Graffitis an Unterführungen, Abfall an Parks). Datenschutz: nur aggregiert, kein Text | M |
| `parkierzonen`, `parkplatzverordnung_a`, `behindertenparkplaetze_dav_p` | Blaue/weisse Zonen und IV-Parkplätze (Piktogramm) | S |
| `lbk_laermschutzwand` | Lärmschutzwände an Gleisen/Autobahn | S |
| `vas_e_steigung`, `vas_e_verkehrstraeger` | Steilheit (z. B. Hohlstr./Röntgenstr. Rampen), Spuraufteilung, Busspur-Farbe | M |
| nicht im Katalog | Fussgängerstreifen (OSM `highway=crossing` + Kanton ZH WFS), Treppen, Mauern, Märkte, Plakatstellen privat | OSM-Ergänzung |

## C. Prozesse

| # | Idee | Nutzen | Aufwand | Lizenz / Risiko |
|---|---|---|---|---|
| P1 | **«Stimmt etwas nicht?»-Knopf** in der Pause/Fotomodus: baut `mailto:` bzw. vorausgefüllten Link zu einem Formular (z. B. Tally/Google-Formular-frei, besser Nextcloud/Framaforms oder GitHub-Issue-Vorlage) mit Parametern `x,y` (LV95), Kachel-ID, Spielversion, Blickrichtung, Uhrzeit. Kein Server-Zustand. Optional «Foto beilegen» (eigenes Foto, Zustimmung zur Lizenz CC0 im Formulartext) | Quartierwissen nutzbar, ohne Backend; passt zur Wahlkampf-Community (Parteimitglieder pro Kreis) | S | DSGVO: keine Personendaten automatisch senden; Mail-Adresse nur der Absender. Kein Tracking |
| P2 | **Korrektur-Import**: Eingegangene Meldungen als Zeilen in `pipeline/overrides/corrections.csv` (id, x, y, Kategorie, Text) und Skript `pipeline/apply_corrections.py` → Overrides-JSON (Farbe, Ladenname, Hausnummer, Dach). Alles reproduzierbar im Pipeline-Lauf | schliesst die Schleife P1 | S-M | niedrig |
| P3 | **Fotospaziergänge** mit 360°-Kamera/Handy durch das Team: Strassenzug als Videos, daraus pro Haus: Fassadenfoto-Referenz (nur intern), Notizen, und **eigene Texturen**: Fassadenkacheln/Schilder aus eigenen Fotos sind frei nutzbar (Zustimmung der Teammitglieder; Personen/Kennzeichen verwischen). Ablage `research/walks/<kreis>/`. Plan: ein Kreis pro Wochenende, 6-8 Strassenzüge (Langstrasse, Hardstrasse, Birmensdorferstrasse, Hohlstrasse, Seebahnstrasse, Josefstrasse, Limmatstr., Hardturmstr.) | höchste Wirkung auf Fassaden; löst das Lizenzproblem sauber | M-L (Menschen, nicht Technik) | eigene Rechte: Einwilligung, Gesichter/Nummernschilder verwischen. Gebäude-Aussenansicht vom öffentlichen Grund in der Schweiz grundsätzlich erlaubt (Panoramafreiheit, Art. 27 URG), aber Schilder/Logos nicht 1:1 als Textur |
| P4 | **Abgleich Luft-/Orthofoto automatisch**: Dachfarbe aus SWISSIMAGE-Pixel unter Gebäude-Polygon (Median) als Dachtextur-Tönung; Hof-/Vorgartengrün aus NDVI; Bäume aus nDSM-Spitzen vs. Baumkataster-Lücken | Dächer und Höfe sind die Ansicht von Hügeln, Tram und Hardbrücke; Daten frei | M (`pipeline/roof_tint.py`) | niedrig |
| P5 | **nDSM-Audit**: für jedes Gebäude Höhe sb3d vs. LiDAR-nDSM-Median, Differenz >2 m → Liste in `research/height_audit.csv`; gleiches für Strassenbäume (Höhe, Kronendurchmesser). Danach Overrides nur dort | schnelle Qualitätsprüfung; Skript 30 Zeilen Ausgabe nach CLAUDE.md-Regel | M | niedrig |
| P6 | **Farb-Audit**: Fassadenfarbe aus Schrägbildern wäre ideal (D6), sonst aus eigenen Spaziergängen. Bis dahin Palette nach Baujahr/Typ (Gründerzeit Beige/Grau, Genossenschaft weiss/Ocker, 60er Beton) | Fassaden-Töne waren die grösste Abweichung (S6) | S | niedrig |
| P7 | **Test mit Einheimischen**: Spiel-Screenshot-Kontaktbogen (4 Bilder pro Kreuzung) an 10 Leute aus dem Quartier: «Welche Kreuzung?» (Wiedererkennungstest). Misst Fortschritt objektiv. Auch als «Quiz» im Spiel nutzbar | liefert Priorität statt Bauchgefühl | S | – |
| P8 | **Panoramax/Mapillary-Abgleich als Dauer-Check**: bestehender Workflow (`fidelity.md`) pro Kreis wiederholen, 15 Paare/Kreis, danach nur Abweichungen mit Foto-Beleg beheben | – | laufend | wie heute |
| P9 | **Eigene Panoramax-Uploads** des Teams (CC BY-SA oder CC0 gewählt) | Community-Karte wächst; unsere Fotos zusätzlich frei verfügbar | S pro Spaziergang | niedrig |

## D. Die 20 Elemente, die Einheimische sofort erkennen (und wie man sie billig richtig bekommt)

Quelle für Status: `research/fidelity.md`, `IDEAS_ZURICH.md` Abschnitt D, `research/furniture_facts.md`. Bewertung heute: ✓ ok, ~ teils, ✗ fehlt (Einschätzung aus den Docs, nicht frisch geprüft).

| # | Element | Status | Billige korrekte Lösung | Quelle |
|---|---|---|---|---|
| 1 | **Tramhaltestelle** (Wartehalle, Bank, Anzeige, Ticketautomat, Haltebalken, VBZ-Farbe/Schriftzug neutral) | ~ | Layer `haltestellen_*` einbauen (B) | OGD CC0 |
| 2 | **Tram selbst** (blau-weisse Cobra/Tram 2000, Linienfarben als Fahrziel-Anzeige) | ✓/~ | Fahrzeug neutral, Farbbänder und Liniennummer-Pools | Foto-Referenz |
| 3 | **Brunnen** (Trinkbrunnen mit vier Röhren, grosse Dorfbrunnen) | ~ | `brunnen.geojson` Typ → zwei Modelle (Trinkbrunnen vs. Wasserbecken); fliessendes Wasser/Ton | OGD |
| 4 | **Kioske, Backwaren/Lädeli** (Valora-Kiosk, Bäckerei) | ✗ | Läden aus OSM `shop=kiosk` mit neutraler Fassade, Zeitungsständer, Eiskasten | OSM, Fassade neutral |
| 5 | **Läden-Mix im EG** (Coiffeur, Döner, Apotheke, Migros/Coop-Ecke, Beiz) | ~ | OSM-/Gastro-Match + Schild mit Ladennamen; Branche → Farbe/Vitrine; keine Logos | OSM + `gastro_match.csv` |
| 6 | **Strassenschilder** (weisse Strassennamentafel blau umrandet, Hausnummern-Schild, Zonenschilder) | ~ | `strassennamen.geojson` bereits da; Position nach Kreuzung; Hausnummern an Fassade | OGD + GWR |
| 7 | **Blaue-Zone-Linien/Parkscheibe/Parkuhr** | ~ | Parkfeld-Layer + `parkierzonen`; Parkscheiben-Pop auf Autos (S5) | OGD |
| 8 | **Grüne Velostreifen, Velo-Piktogramm, Velovorzugsrouten (violett/Beschilderung)** | ~ | `velo_green.json` erweitern, Vorzugsrouten-Schilder aus OGD-Netz | Overrides + OGD |
| 9 | **Fussgängerstreifen** (Zebra mit Mittelinsel, Aufmerksamkeitsleuchten) | ✓ | OSM `crossing` vorhanden; Kontrolle gegen Orthofoto | OSM |
| 10 | **Pflaster/Belag** (Granitplatten Trottoir, Kopfsteinpflaster Altstadt/Gassen, Tramgleis-Pflaster) | ~ | `vas_e_strassenbelag` ist verwendet (groundcover); Pflasterstrassen aus Foto belegen | OGD + Fotos |
| 11 | **Litfasssäule / Plakatstellen** (APG, Stadt-ZH-Plakatstellen) | ✗ | Standorte aus `haltestellen_plakatstelle`, OSM `advertising=column`; fiktive Plakate | OGD/OSM |
| 12 | **Abfall: Züri-Kübel, Unterflur-Container, Recyclingstellen** | ✓/~ | `abfallgefaesse`, `sammelstellen`, `kehrichtcontainer` vorhanden | OGD |
| 13 | **Hydranten (rot/gelb), Strassenlampen (Seilleuchten über der Strasse)** | ✓/~ | Hydranten da; Beleuchtung ewz da; Seilaufhängungen in den Wohnstrassen typisch Zürich | OGD |
| 14 | **Kirchtürme und Uhren** (St. Jakob, St. Peter, Dreikönigskirche, Kirchenuhr + Läuten) | ~ | Landmark-Liste, Höhe aus LiDAR/DSM, Uhr 12:00 Läuten | OSM/LiDAR |
| 15 | **Bahnviadukt/Bögen, Hardbrücke, Limmat-Brücken, Gleisfeld** | ~ | Kunstbauten-Layer, Brücken-Sonderfälle (S13) | OGD + Handarbeit |
| 16 | **Hochhäuser/Skyline** (Prime Tower, Hardau, Prime-Umfeld, Zürich West Kräne) | ~ | `alle_hochhaeuser` + Dachfarbe/Spitze aus nDSM | OGD |
| 17 | **Genossenschaftsbauten, Blockrand mit Hof** (Kalkbreite, Zurlinden-Blöcke, Baugenossenschaft-Zeilen) | ~ | Hof begrünt (D9), Wäscheleinen/Spielplatz im Hof; Dachterrassen | Orthofoto + Handnotizen |
| 18 | **Vorgärten, Zäune, Hecken, Fahrradbügel vor Hausfront** | ✗/~ | Hecken aus `bodenbedeckung_a` (Gebüsch), `stadtnatur`, Veloständer aus OSM+OGD (schon S9) | OGD |
| 19 | **Märkte & Bäckeranlage/Helvetiaplatz-Szene** (Marktstände, Pétanque, Planschbecken) | ~ | Szenen-Bibliothek `IDEAS_ZURICH` Z-Liste, Marktzeit/Wochentage | Eigene Szenen |
| 20 | **Fassadenfarbe und Rolläden/Fensterläden pro Strassenzug** | ~ | Notizen pro Adresse (82 vorhanden) → mit Spaziergängen (P3) auf je 200 Adressen/Kreis ausbauen | eigene Fotos |

## E. Bewertung der Strategien (Nutzen / Aufwand / Lizenz / Risiko)

| # | Strategie | Nutzen | Aufwand | Lizenz | Risiko |
|---|---|---|---|---|---|
| 1 | Tramhaltestellen komplett aus `haltestellen_*` | hoch | S-M | grün | niedrig |
| 2 | Dachfarbe/-typ aus Orthofoto (P4) + Dachmodell LoD2 (D1) | hoch | M | grün/gelb (Dachmodell-Jahrgang prüfen) | niedrig |
| 3 | P1+P2 Korrektur-Link + Overrides-Import | hoch (Mobilisierung) | S-M | grün | niedrig |
| 4 | P3 Fotospaziergänge mit eigener Kamera | sehr hoch | M-L | grün | niedrig |
| 5 | P5 nDSM-/Höhenaudit | mittel-hoch | M | grün | niedrig |
| 6 | Läden-Mix-Verfeinerung (Branche→Fassade) | hoch | S-M | grün | niedrig |
| 7 | Hochhaus-/Kirchturm-Skyline aus OGD und nDSM | hoch | S | grün | niedrig |
| 8 | Hecken/Vorgärten/Hofbaum aus Kronenmodell+Bodenbedeckung | mittel | M | grün | niedrig |
| 9 | P7 Wiedererkennungstest mit Einheimischen | hoch (Steuerung) | S | – | – |
| 10 | Gebäudeeingänge/Hausnummern | mittel | M | gelb | niedrig |
| – | Fotorekonstruktion/Textur aus Mapillary/Panoramax | hoch, aber rechtlich unklar | L | rot | hoch → nicht empfohlen |
| – | Google-basierte Ableitungen | – | – | rot (verboten) | – |

## Top 10

1. **Tramhaltestellen aus den 8 `haltestellen_*`-Layern** (sofort, Daten da).
2. **Korrektur-Link «Stimmt etwas nicht?» mit Koordinate** + `apply_corrections.py` (Quartier mobilisieren, ohne Server).
3. **Fotospaziergänge** Langstrasse/Hardstrasse/Birmensdorferstrasse mit 360°/Handy, eigene Lizenz, Fassadennotizen.
4. **Dachfarbe aus SWISSIMAGE/Orthofoto** unter Gebäudepolygon + Dachtyp aus Dachmodell LoD2 (nur Attribute).
5. **nDSM-Höhen-/Baumaudit** (Kanton ZH LiDAR 2022): Liste der Abweichungen, Overrides nur dort.
6. **Läden-Mix**: Branche → Vitrine/Farbe, Kioske, Bäckereien, Zeitungsständer; Ladenname als Schild.
7. **Skyline**: `alle_hochhaeuser` + Kirchtürme (Höhe aus nDSM), Uhr + Läuten.
8. **Hecken/Vorgärten/Hofbäume** aus Bodenbedeckung + Baumhöhen 2018.
9. **Wiedererkennungstest** (Kontaktbogen an 10 Einheimische) als Messlatte.
10. **Brunnen/Kunst/Velopumpen/Plakatsäulen** aus bereits geladenen OGD-Layern vollständig und an echter Stelle zeigen.

## Konkrete nächste Schritte

| Schritt | Datensatz | Skript / Ort | Ergebnis |
|---|---|---|---|
| 1 | `haltestellen_*` (7 Dateien in `data/raw/stadtzh_all/`) | neues `pipeline/stops_furniture.py`, danach in Kachel-Build einhängen | Wartehalle, Bank, Anzeige, Automat, Plakat an echter Position |
| 2 | – | Web: Button «Stimmt etwas nicht?» (`web/src/ui/`), URL-Schema `mailto:` oder GitHub-Issue `?title=&body=` mit `x,y,tile,version`; Pipeline: `pipeline/apply_corrections.py` | Meldungen → `pipeline/overrides/corrections.json` |
| 3 | SWISSIMAGE 10 cm (`data/raw/ortho*`) | `pipeline/roof_tint.py`: Median-RGB je Gebäudepolygon, Ausreisser (Schnee, Schatten) filtern | `roof_color` je EGID in `buildings_info` |
| 4 | Kanton ZH Höhendaten 2022: nDSM-Kacheln | `pipeline/height_audit.py` (Ausgabe ≤30 Zeilen + CSV nach `research/`) | Gebäude- und Baumhöhen-Abweichungen |
| 5 | Dachmodell LoD2 2018 (WFS-Bbox, Kreis 4/5) | `pipeline/fetch_roofs_lod2.py` (Cache nach `data/raw/roofs_lod2/`) | Gauben/Kamine/Dachtyp als Attribute |
| 6 | – | Plan für Fotospaziergang (Route, Pflicht-Aufnahmen: Strasse beidseitig, Haltestelle, Ladenzeile), `research/walks/README.md` | Fassaden-Notizen für 200 Adressen/Kreis |
| 7 | `alle_hochhaeuser`, OSM `building=church` | `pipeline/skyline_check.py`: Höhe vs. nDSM | Skyline-Liste, Landmark-Modelle priorisieren |
| 8 | `bodenbedeckung_a` + Baumhöhen 2018 | `pipeline/yards_green.py`: Hofbäume/Hecken | Instanzliste Bäume/Hecken in Höfen |
| 9 | – | Kontaktbogen «Welche Kreuzung ist das?» (`web/tests/` existiert), 10 Kreuzungen/Kreis | Rangliste der unkenntlichsten Orte |

## Sofort machbar (S)

- `haltestellen_*` Layer einbauen (S-M, erste Stufe: nur Wartehalle + Bank + Plakat).
- `velopumpstationen_p`, `blaue_tafeln_p`, `gebaeudebrueter_inventar` als Details platzieren.
- `alle_hochhaeuser` mit Landmark-Liste abgleichen, fehlende Höhen setzen.
- `parkierzonen`/`behindertenparkplaetze_dav_p`: Bodenpiktogramme.
- «Stimmt etwas nicht?»-Link mit Koordinate (mailto), Meldungstabelle als CSV.
- Wiedererkennungstest (Kontaktbogen) mit 10 Einheimischen.
- Stadt ZH Geomatik per Mail fragen: Schrägluftbilder/texturiertes Modell frei nutzbar?
- Brunnen-Typen (Trinkbrunnen vs. Becken) aus Attributen unterscheiden.
- Lizenzeinträge in `DATA_SOURCES.md` für Kanton-ZH-Höhendaten 2022, Dachmodell 2018, Baumhöhen 2018 vorbereiten (noch nicht ändern, nur Prüfliste).

## Offene Rechtsfragen (vor Nutzung klären)

- Dachmodell Jahrgangs-Lizenz (Metadaten uneinheitlich); sicherer: 2018.
- Panoramax/Mapillary-Ableitung (3D/Textur): keine verlässliche Aussage gefunden. Empfehlung: nicht tun; Attribute (Farbe, Läden, Stockwerke) selbst notieren.
- Schrägluftbilder/texturiertes Stadtmodell: kein OGD gefunden, Anfrage nötig.
- Foto-Spaziergänge: Einwilligungstext fürs Team (CC0 oder eigene Lizenz) und Verwischen von Gesichtern/Nummernschildern.

## Quellen
- https://ckan.opendata.swiss/dataset/3d-dachmodell-lod2-jahresstand-2018-3d
- https://ckan.opendata.swiss/dataset/3d-dachmodell-lod2-jahresstand-2015-3d
- https://ckan.opendata.swiss/dataset/swissbuildings3d-3-0-beta
- https://www.swisstopo.admin.ch/en/geodata/landscape/buildings3d3.html
- https://www.zh.ch/de/news-uebersicht/mitteilungen/2023/planen-bauen/geoinformation/aktuelle-hoehendaten-fuer-den-kanton-zuerich.html
- https://www.zh.ch/de/news-uebersicht/mitteilungen/2022/planen-bauen/geoinformation/neue-aufnahmen-aus-der-vogelperspektive.html
- https://ckan.opendata.swiss/dataset/baumkataster
- https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data
- https://docs.panoramax.fr/federated-catalog/
- https://wiki.openstreetmap.org/wiki/Panoramax
- lokal: `research/ogd_catalog.md`, `research/fidelity.md`, `docs/IDEAS_ZURICH.md`
