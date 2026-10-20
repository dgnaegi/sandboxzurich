# Nachtplan: Realismus-Woche (7 Nächte à 8 h)

Start 2026-10-18. Ziel: mehr Details, mehr Realismus, alles so nah an der echten Umgebung wie möglich. Keine neuen Spielfunktionen, nur Karte und Stadtbild. Ersetzt für diese Woche `docs/PLAN_8H.md` (Stand 2026-10-15).

**Start jeder Nacht:** neue Session im Auto-Modus, Prompt: «Lies `docs/NIGHT_PLAN.md` und führe die nächste offene Nacht aus.» Dazu `docs/HANDOFF.md` lesen. Nach jeder Phase eine Zeile in HANDOFF («Nacht N, Phase X fertig»). Am Ende die Nacht unten abhaken und eine Zeile ins Protokoll.

## Wochenübersicht
- [x] **Sondernacht (So 18.10. 22:00 – Mo 19.10. 16:00, 18 h)** – User-Auftrag: Schlachthof, Letzipark, Frau Gerolds Garten nach Fotos; Bäume Hardbrücke; Markierungen/Bodenschwellen gegen SWISSIMAGE; Fahrverhalten + umfahrbare Schilder; Ni-Una-Menos-Platz; Übergabe-Punkte; Komplett-Build ~03:30 + Release 1; danach Objekt-Katalog (Nacht 0) im Tagesblock, Komplett-Build ~13:00 + Release 2. Cache-/Speicherfix wurde schon am 18.10. erledigt (Build 11).
- [x] **Nacht 0 (So 18.10.)** – Grundlagen + Objekt-Katalog (Brunnen, Haltestellen, Möbel)
- [x] **Nacht 1 (Mo 19.10.)** (in der Sondernacht vorgezogen, Teilziel: Notizen 248/495, Läden schwach) – Zone 4 Wiedikon
- [x] **Nacht 2 (Di 20.10.)** – Zone 2 Kreis 5 Industrie (am 19.10. tagsüber vorgezogen, ~70 %: Häuser/Plätze ja; Escher-Wyss/Hardbrücke-Häuser, Läden, Haltestellen offen)
- [x] **Nacht 3 (Mi 21.10.)** – Zone 1 HB und Langstrasse (am 19.10. abends vorgezogen; Daten ja, Note nur 2.8 → 2.9)
- [x] **Nacht 4 (Do 22.10.)** – Zone 5 Kreis 9 West (am 20.10. vorgezogen; 17 Landmarks, PJZ verschoben, Ø ~2.7 → 3.2)
- [x] **Nacht 5 (Fr 23.10.)** – Zone 3 Kreis 4 Mitte (am 20.10. vorgezogen; 42 Landmarks, Ø ~2.9 → 3.4)
- [ ] **Nacht 6 (Sa 24.10.)** – Komplett-Build, stadtweite Kontrolle, Deploy, Rückblick

Reihenfolge nach Bestandsaufnahme 2026-10-19 (`research/zones/baseline.md`, Ø gesamt 2.5): Zone 4 (2.7, eigenes Quartier) → 2 (2.2) → 1 (2.3) → 5 (2.7) → 3 (2.8). Die Abschnitte «Nacht 1–5» unten sind nach Zone benannt; massgeblich ist diese Reihenfolge.

## Was «Detail» hier heisst (User 2026-10-18)
Nicht jeder Pixel und nicht alles ganz genau. Es heisst: **die relevanten, grösseren Sachen stimmen mit einem Foto überein.** Massstab ist der Blick aus Fussgänger-/Velo-Distanz (10–50 m), nicht die Nahaufnahme.

Priorität (in dieser Reihenfolge):
1. **Häuser:** Volumen, Höhe, Geschosse, Dachform, Fassadenfarbe, Fensterraster, Erdgeschoss (Laden/Eingang/Tor).
2. **Strassen:** Verlauf, Breite, Trottoirs, Tramgleise, wichtige Markierungen (Fussgängerstreifen, Velostreifen, Parkfelder), Bäume an der richtigen Stelle.
3. **Grosse Objekte:** Brunnen, Tram-/Bushaltestellen, Plätze, Kioske, Unterführungen, Brücken.
4. **Ladenfronten:** echter Name, Hauptfarbe, Markise.

Nicht im Fokus: Kleinkram (Schachtdeckel, Hydranten, Schilder-Feinheiten, Texturauflösung, einzelne Velos/Leute). Lieber 50 Häuser mit richtiger Farbe und Höhe als 5 Häuser mit jedem Fenstersims. Tickets nur für Abweichungen, die man auf dem Vergleichsbild sofort sieht.

**Anspruch: sehr hoch.** Wer in Zürich wohnt, soll seine Strasse auf den ersten Blick wiedererkennen. «Ganz okay» ist keine Abnahme. Die Hauptsession beurteilt streng und ehrlich; im Zweifel ist ein Punkt nicht erledigt.

**Ausgangslage (Build 10):** ~11 700 Häuser im Spielgebiet, davon ~230 (≈ 2 %) als Modell nach Fotos, Fassadennotizen für gut 1 000 (≈ 10 %), der Rest generisch. Langstrasse/HB sind stark bearbeitet (dort nur noch Korrekturen); der grösste Gewinn liegt in der Breite: die vielen normalen Häuser und Strassen aller Quartiere.

## Grundidee
1. **Objekt-Katalog statt Einheitsmodell.** Heute sind alle Brunnen dasselbe Modell (`web/src/world/details.ts`, `pipeline/cityprops.py` verwirft alle Attribute ausser Lage/Richtung) und es gibt einen Wartehallen-Typ. Die Stadtdaten können mehr: 334 Brunnen in Kreis 3/4/5/9 mit `material_trog` (Granit, Bronzeguss, Beton, Kunststein, Kalkstein …), `material_saeule`, `material_figur`, `architekt_bildhauer`, `wasserart`, `art` (öffentlich/privat/Notwasser), `ortsbezeichnung`. Nacht 0 baut die echten Varianten nach Fotos; jede reale Stelle bekommt ihre Variante.
2. **Zonen.** Pro Nacht eine Zone nach Fotos nachbauen und prüfen. Nur deren Kacheln bauen (`SBZ_TILES=…`, ~12 statt ~55 min).
3. **Foto | Spiel an festen Kamerapunkten** ist das Mass. Jede Abweichung wird ein Ticket (`research/qa_round/z<N>_<nr>.md`: Ort, Foto, Befund, Ursache, Fix), jeder Fix geht über Pipeline/Overrides.

## Material, das schon da ist
Fotos lokal in `data/raw/photos/` (~37 000 Dateien): `shops_r2` 10 489, `facades` 12 454, `shops_r3` 4 038, `v3` 2 979, `shops` 2 300, `ida` 932, `langstrasse(_b)` 1 353, `hb` 632, `buildings` 630, `squares2` 300, `parks` 290, `transit` 150, `streetscape` 149, `furniture` 113, `bikes` 69, `lochergut` 48. Zuerst diese nutzen, Web nur für Lücken (über `pipeline/photos/fetch_v3.py`-Wrapper wie `fetch_ida.py`). Metadaten-JSONs in `research/` haben Lage + Lizenz.

## Zonen
Grenzen folgen Strassen. Nacht 0 legt sie per Skript fest (`pipeline/zones.py` → `pipeline/overrides/zones.json`: Polygon, Kachelliste, Kamerapunkte pro Zone; Bogen `preview/zones.jpg`).

| # | Zone | Kern |
|---|---|---|
| 1 | HB und Langstrasse | Bahnhofplatz, HB-Halle, Europaallee, Sihlpost, Langstrasse bis Helvetiaplatz, Kanzlei, Militär-/Kasernenstrasse, Bäckeranlage |
| 2 | Kreis 5 Industrie | Hardbrücke, Escher-Wyss-Platz, Turbinenplatz/Schiffbau, Josefwiese, Viadukt, Limmatplatz, Röntgenplatz, Limmat/Sihl |
| 3 | Kreis 4 Mitte | Stauffacher, Bullingerplatz, Hardplatz, Albisriederplatz, Lochergut, Badener-/Hohl-/Hardstrasse, Zypressenstrasse |
| 4 | Wiedikon (Kreis 3) | Idaplatz, Zurlinden-/Berta-/Gertrudstrasse, Schmiede Wiedikon, Bahnhof Wiedikon, Goldbrunnenplatz, Friedhof Sihlfeld, Kalkbreite |
| 5 | Kreis 9 West | Letzigrund, Badenerstrasse West, Hohlstrasse West (Egli-Siedlung), PJZ, Bahnhof Altstetten, Lindenplatz |

---

## Nacht 0 – Grundlagen + Objekt-Katalog
**Ziel:** Änderungen werden sichtbar (Cache), Handy hat Speicherreserve, Brunnen/Haltestellen/Möbel gibt es in echten Varianten.

| Zeit | Schritt | Wer |
|---|---|---|
| 0:00–0:30 | Offenen Code-Stand (12 Dateien, `assetver.ts`, `vite.config.ts`, Tests `mem_phone`/`move_quality`, `fetch_ida.py`) prüfen: Typecheck, Tests touch/drive/qa_spawn. Commit. | Hauptsession |
| 0:30–1:15 | **Cache-Fix** fertig: `?v=<commit>` an alle Daten-, Kachel-, Modell-, Textur-URLs (`assetver.ts`); Test: zwei Builds hintereinander, im zweiten muss die neue `landmarks.json` geladen werden. | Hauptsession |
| 1:15–2:00 | **Handy-Speicher:** `signs.ts` auf Handys `SCALE = 0.5`, Hausnummern in eigene geteilte Glyphen-Textur, Canvas nach Upload freigeben, `wildposters.webp` Halbversion für Handys. `mem_phone.mjs` vorher/nachher. Ziel Langstrasse < 250 MB (Endziel < 200 MB in Nacht 2). | Hauptsession |
| 2:00–2:45 | **Bestandsaufnahme:** 15 zufällige Orte über alle Zonen (je 3, an Fotos mit bekannter Lage), Foto \| Spiel → `preview/baseline_sheet.jpg`, Note 1–5 pro Ort und Kriterium (Häuser, Strasse, grosse Objekte) → `research/zones/baseline.md`. Ergebnis kann die Zonen-Reihenfolge ändern (schlechteste zuerst, eigenes Quartier bleibt Nacht 1). |
| 2:45–3:15 | **Zonen:** `pipeline/zones.py` → `zones.json` mit Kachellisten und je 15–20 Kamerapunkten (Liste unten bei jeder Zone, Punkte an Fotos mit bekannter Lage ausrichten); `web/tests/zone_shots.mjs <N> [before|after]` schreibt Kontaktbogen Handy+PC. | Hauptsession |
| 2:00–3:30 | **Inventar-Agent (Haiku)**, siehe Auftrag K1. | Agent |
| 3:30–6:30 | **Modell-Agent (Sonnet)** K2 und **Zuordnungs-Agent (Sonnet)** K3 parallel. | 2 Agents |
| 6:30–7:15 | 6 Testkacheln bauen (Idaplatz, Helvetiaplatz, Bullingerplatz, Escher-Wyss-Platz, Stauffacher, Albisriederplatz), Bogen `preview/catalog_cmp.jpg` (Foto \| Spiel je Variante). Tickets. | Hauptsession |
| 7:15–7:45 | Kleine Korrekturen, `perf` Handy, `qa_leak`. | Hauptsession |
| 7:45–8:00 | HANDOFF, DECISIONS (Katalog, Zonen, Cache), Commit. | Hauptsession |

**Auftrag K1 – Inventar (Haiku).** Darf schreiben: `research/catalog/*`, `preview/ref_cat_*.jpg`, `pipeline/catalog/inventory.py`. Aus lokalen Fotos + Fotometadaten pro Objektart 20–40 Ausschnitte suchen (Lage nahe an Objekt aus Stadtdaten), Varianten bilden und beschreiben (Form, Masse geschätzt mit Bezug wie Person/Türe, Material, Farbe). Objektarten:
- Brunnen: Zürcher Standardbrunnen (Säule + Trog, Generationen), Granittrog rund/eckig, Bronzeguss-Trog, Betontrog, Wandbrunnen, Figurenbrunnen, Notwasserbrunnen, Trinkbrunnen (Säule ohne Trog).
- Haltestellen: Wartehallen-Typen (Glas/Stahl VBZ, alte Typen, Dach ohne Wände), Haltestellenmast mit Fahne (Tram/Bus), Billettautomat, Anzeige, Fahrplankasten, Haltekante/Kaphaltestelle, Bodenmarkierung (gelber Streifen, «BUS»).
- Möbel (nur die grossen, gut sichtbaren): Kandelaber/Seilleuchten, Plakatsäulen/-wände, Kioske, Sammelstellen. Kleinkram (Hydranten, Poller, Kästen) nur wenn Zeit bleibt.
Rückmeldung: Tabelle Variante → Anzahl Fotos → Merkmal zur Zuordnung (≤ 15 Zeilen).

**Auftrag K2 – Modelle (Sonnet).** Darf schreiben: `pipeline/models/catalog_*.py` (Blender), `web/public/models/catalog/*`, `pipeline/pack_models.py`-Liste. Pro Variante ein Modell, Masse nach K1, ein gemeinsamer Atlas für alle Katalogmodelle (≤ 1024², Handy 512²), LOD: Nahmodell + einfache Box ab 60 m. Max. ~1500 Dreiecke pro Brunnen, ~800 pro Möbel. Rückmeldung: Liste Modelle + Dreiecke + Atlasgrösse.

**Auftrag K3 – Zuordnung + Laufzeit (Sonnet).** Darf schreiben: `pipeline/catalog/assign.py`, `pipeline/overrides/catalog_assign.json`, `pipeline/cityprops.py` (nur Brunnen-/Möbel-Export), `web/src/world/catalog.ts` (neu), Einbau in `details.ts`/`stops_equip.ts` nur über einen Aufruf. Regeln: Brunnen nach `material_trog`/`material_saeule`/`material_figur`/`art`; Haltestellen nach VBZ-Attributen in `stops_equip.json`, sonst Standard; bei fehlenden Daten nächstes Foto (K1), sonst häufigste Variante. Eine InstancedMesh pro Variante, Dispose beim Kachel-Entladen. Rückmeldung: Verteilung Varianten (Anzahl), Draw Calls vorher/nachher.

**Abnahme Nacht 0:** Cache-Test grün; Handy-Texturen Langstrasse gesunken; ≥ 6 Brunnen-, ≥ 3 Haltestellen-, ≥ 4 Möbelvarianten im Spiel; Bogen `catalog_cmp.jpg`: jede Variante auf den ersten Blick als das echte Objekt erkennbar; perf Handy ≥ 50 fps.

---

## Ablauf jeder Zonen-Nacht (Nächte 1–5)
| Zeit | Schritt | Wer |
|---|---|---|
| 0:00–0:30 | HANDOFF lesen; Kachelliste + Kamerapunkte aus `zones.json`; offene Tickets der Zone; `zone_shots.mjs <N> before` → `preview/zone<N>_before.jpg`. | Hauptsession |
| 0:30–1:30 | **Inventar (Haiku, Auftrag Z0):** fehlende Fotos holen (Hintergrund, Log `logs/photos_z<N>.log`), dann pro Haus/Laden/Platz einen Eintrag in `research/zones/zone<N>.md` + Bögen `preview/ref_z<N>_*.jpg`. | Agent |
| 1:30–5:00 | **Nachbau (3 Sonnet, Aufträge ZA/ZB/ZC parallel).** Hauptsession prüft Zwischenstände nur per Kontaktbogen. | 3 Agents |
| 5:00–5:30 | Kacheln der Zone bauen (Hintergrund, nichts parallel). | Hauptsession |
| 5:30–6:30 | `zone_shots.mjs <N> after` + Foto \| Spiel → `preview/zone<N>_cmp.jpg`; Note 1–5 pro Kamerapunkt; Tickets. | Hauptsession |
| 6:30–7:30 | Korrekturrunde (Hauptsession oder ein Agent aus dem Nachbau, gleiche Dateien), betroffene Kacheln neu, Bilder neu. | |
| 7:30–8:00 | Tests `mem_phone`, `perf` Handy, `traffic_legal`, `qa_spawn`, `qa_leak`; wenn grün `deploy/publish_world.sh`; HANDOFF, Häkchen, Protokoll, Commit. | Hauptsession |

**Auftrag Z0 – Inventar (Haiku).** Darf schreiben: `research/zones/zone<N>.md`, `research/zones/zone<N>_shops.json`, `preview/ref_z<N>_*.jpg`, `logs/photos_z<N>.log`. Pro Gebäude an den Hauptstrassen: Fassadenfarbe (Hex), Geschosse, Fensterraster, Dachform/-farbe, Balkone/Erker, Sockel, Erdgeschoss-Nutzung. Pro Laden: Name, Adresse, Quelle, Schild (Farbe/Schrift/Lage), Markise, Aussensitze. Pro Platz: Boden, Bäume, Brunnen (Katalogvariante prüfen), Möbel. Läden mit Webquelle gegenprüfen (geschlossen? umbenannt?). Rückmeldung ≤ 15 Zeilen.

**Auftrag ZA – Häuser (Sonnet).** Darf schreiben: `pipeline/landmarks/z<N>_*.py`, `pipeline/overrides/facades_z<N>.json`, Einträge Zone N in `landmarks.json` (nur über `merge.py`). Zuerst flächig: Höhe/Geschosse, Dachform, Fassadenfarbe und Fensterraster für **alle** Häuser an den Hauptstrassen der Zone (Override pro Haus). Danach 5–15 prägende Häuser als Landmarks. Keine Feinornamente. Gemeinsame Kit-Texturen, keine eigene Textur pro Haus. Budget pro Zone: +≤ 15 MB Texturen Handy.

**Auftrag ZB – Strassenraum (Sonnet).** Darf schreiben: `pipeline/overrides/places_detail_z<N>.json`, `pipeline/overrides/catalog_assign.json` (nur Zone N), `pipeline/overrides/markings_z<N>.json`, Platzbrunnen-Modelle `pipeline/models/fountain_z<N>_*.py`. Katalog-Zuordnung an jedem Kamerapunkt prüfen, besondere Brunnen einzeln nachbauen, Haltestellen nach Fotos (Typ, Lage Automat/Anzeige, Haltekante), Markierungen (Parkfelder, Haltelinien, Velostreifen, Fussgängerstreifen), Trottoirkanten und Absenkungen, Baumarten nach Baumkataster, Platzböden.

**Auftrag ZC – Erdgeschoss (Sonnet).** Darf schreiben: `pipeline/overrides/storefronts_z<N>.json`, `pipeline/overrides/pedspots_z<N>.json`, `pipeline/overrides/bikes_z<N>.json`. Ladenfronten mit echten Namen, Hauptfarbe und Markise, Hauseingänge/Tore, Aussensitze von Beizen/Cafés. Velos/Leute nur, wo ein Ort sonst leer wirkt.

**Abnahme Zonen-Nacht:** Auf dem Vergleichsbild stimmen an jedem Kamerapunkt Häuser (Höhe, Farbe, Dach), Strassenraum und grosse Objekte mit dem Foto überein; Ø-Note der Kamerapunkte ≥ 4 (Ziel 4.5), kein Punkt unter 3; keine Ladennamen ohne Quelle; Handy-Texturen in der Zone < 200 MB, perf Handy ≥ 50 fps; `traffic_legal` nicht schlechter als vorher; offene Tickets dokumentiert.

---

## Nacht 1 – Zone 4 Wiedikon
**Warum zuerst:** Idaplatz-Fotos liegen schon bereit (`data/raw/photos/ida`, 932 Dateien, `research/v3/photos_ida.json`, `sites_ida.json`), und im eigenen Quartier fällt jede Abweichung sofort auf.

**Kamerapunkte (16):** Idaplatz Mitte · Idaplatz Nord/Zurlindenstrasse · Idastrasse Süd · Bertastrasse · Gertrudstrasse · Aemtler-/Wiesendangerstrasse · Zentralstrasse · Zurlindenstrasse West/Ost · Thomasweg/Martastrasse · Schmiede Wiedikon (Kreuzung + Tramhaltestelle) · Bahnhof Wiedikon Vorplatz · Bahnhof Wiedikon Perron · Goldbrunnenplatz + Haltestelle · Friedhof Sihlfeld Haupteingang · Ortsmuseum Wiedikon · Kalkbreite.

**Schwerpunkte:** Idaplatz komplett (Brunnen, Bäume, Bänke, Beizen-Aussensitze, Spielplatz); Blockrand-Fassaden Zurlinden-/Bertastrasse; Haltestellen Schmiede Wiedikon und Goldbrunnenplatz nach Fotos; Bahnhof Wiedikon (Abgleich mit #39); Friedhofsmauer/-tor.

**Altlasten:** Grenze zu Zone 3 (Kalkbreite, Lochergut) in `zones.json` sauber festlegen.

## Nacht 2 – Zone 1 HB und Langstrasse
**Kamerapunkte (18):** Bahnhofplatz (Escher) · HB-Halle · Querhalle/Shopville-Abgang · Europaallee/Lagerstrasse · Sihlpost · Haltestelle Bahnhofplatz/HB · Langstrasse/Lagerstrasse · Langstrassen-Unterführung · Langstrasse/Dienerstrasse · Langstrasse/Militärstrasse · Langstrasse/Brauerstrasse · Helvetiaplatz (Volkshaus) · Haltestelle Helvetiaplatz · Kanzlei · Bäckeranlage · Kasernenstrasse · Velotunnel-Portal · Shopville unten.

**Schwerpunkte:** Bahnhofplatz-Boden (Pflaster statt Rasen), Escher-Brunnen, Haltestellen-Inseln; HB-Untergeschosse dunkler und nach Fotos (Lichtfarben, Schilder), Rolltreppen; Langstrasse-Häuser tags/nachts prüfen; Helvetiaplatz-Brunnen und Markt-Möblierung.

**Altlasten:** Bahnhofplatz Rasen (Boden-Klassifikation am Rand der Spielgebiets-Erweiterung); Farben Kir Royal, Peeeng, Rasputin, Midway, Monroe (`research/langstrasse_C.md`); Weissmarkierungen Langstrasse Süd; Handy-Endziel < 200 MB Texturen an der Langstrasse (Landmark-Texturen der 42 Häuser auf Kit/Atlas umstellen).

## Nacht 3 – Zone 3 Kreis 4 Mitte
**Kamerapunkte (16):** Stauffacher (Kreuzung + Haltestelle) · Bullingerplatz (Brunnen) · Bullingerhof · Hardplatz · Albisriederplatz (Haltestelle + Platz) · Lochergut (Hochhaus + Haltestelle) · Badenerstrasse/Kalkbreite-Seite · Badenerstrasse/Zypressenstrasse · Hohlstrasse/Hardstrasse · Hardstrasse/Bullingerstrasse · Sihlfeldstrasse · Zypressenstrasse · Erismannhof · Brauerstrasse West · Seebahnstrasse · Ernastrasse.

**Schwerpunkte:** Bullingerplatz komplett (Brunnen, Platanen, Beizen); Albisriederplatz als Verkehrsknoten (Haltestellen, Markierungen, Fahrleitungen); Lochergut-Fassaden; Genossenschafts-Höfe (Erismannhof, Bullingerhof).

**Altlasten:** Strassenglättung Seebahn-/Bullingerstrasse (`road_smooth_audit.py`).

## Nacht 4 – Zone 2 Kreis 5 Industrie
**Kamerapunkte (16):** Escher-Wyss-Platz (Haltestelle + Brücke) · Bahnhof Hardbrücke Perron · Hardbrücke Fahrbahn · Turbinenplatz · Schiffbau · Prime Tower Fuss · Josefwiese · Viadukt (Markthalle) · Limmatplatz · Röntgenplatz · Limmatstrasse/Konradstrasse · Josefstrasse · Heinrichstrasse · Fabrikstrasse · Sihlquai · Limmatufer.

**Schwerpunkte:** Viaduktbögen mit echten Läden; Escher-Wyss-Platz und Hardbrücke-Haltestellen; Josefwiese (Brunnen, Spielplatz, Pavillon); Limmatplatz (Migros, Tramschlaufe); Ufer Limmat/Sihl.

**Altlasten:** Autos im Wasser (Verkehrsgraph/Parkautos/Brücken gegen `water.py`, Prüfskript analog `audit_rail.py`); Escher-Wyss-Platz `traffic_legal` 1.15 %; Gleise/Brücken (`research/audit_rail.md`, `overrides/rail_excl.json`).

## Nacht 5 – Zone 5 Kreis 9 West
**Kamerapunkte (15):** Letzigrund Stadion · Haltestelle Letzigrund · Badenerstrasse West · Hohlstrasse Egli-Siedlung · PJZ Eingang · Bahnhof Altstetten Vorplatz · Bahnhof Altstetten Perron · Lindenplatz · Altstetterstrasse · Hohlstrasse/Flurstrasse · Herdernstrasse · Westpark · Vulkanplatz · Baslerstrasse · Rautistrasse-Rand.

**Schwerpunkte:** Bahnhof Altstetten mit Vorplatz und Bushaltestellen; Lindenplatz (Dorfkern, Brunnen); Letzigrund; Gewerbebauten Hohlstrasse.

**Altlasten:** PJZ Höhen/Eingang (`research/pjz.md`, `preview/pjz_cmp.jpg`); Norastrasse-Glättung.

## Nacht 6 – Komplett-Build und Abnahme
| Zeit | Schritt |
|---|---|
| 0:00–1:00 | Komplett-Build (`build_testarea.py`, Log `logs/build_fullN.log`), keine Agents parallel. |
| 1:00–2:30 | Alle Tests; Fehler-Sweep (`web/tests/sweep.mjs`) gegen den Vorher-Stand; Bogen aller Zonen `preview/week1_cmp.jpg` (je 4 beste und 4 schlechteste Kamerapunkte). |
| 2:30–6:00 | Restliche Tickets nach Wirkung (Note × Sichtbarkeit), max. 3 Agents, nach Zonen getrennt. |
| 6:00–7:30 | Betroffene Kacheln neu, Handy-Speicher/FPS an der dichtesten Stelle jeder Zone, Deploy. |
| 7:30–8:00 | Rückblick hier (was hat am meisten gebracht, was nicht), Vorschlag Woche 2 (zweiter Durchgang: Zonen mit tiefster Ø-Note zuerst; Innenhöfe, Nacht-Look, Wetter). |

---

## Regeln für alle Nächte
- **Max. 3 Agents gleichzeitig**, nie Kacheln parallel zu einem Build bauen (Mac 16 GB). Agents nie `git stash`, nie `pkill -f build_testarea`, keine `pgrep`-Warteschleifen.
- **Jeder Agent hat seine Dateiliste** (oben), sonst nichts ändern; Rückmeldung ≤ 15 Zeilen.
- **Höchstens ein Commit pro Stunde**, Agent-Ergebnisse bündeln.
- **Handy-Budget:** < 200 MB Texturen an der dichtesten Stelle, perf Handy ≥ 50 fps. Speicher geht vor neuen Details.
- **Fotos** (lokal, Commons, Panoramax, Mapillary) als Vorlage für Masse, Farben, Typen; Lizenz in den Metadaten. Google Street View/Images nur zur Inspiration, nie als Textur oder Vorlage.
- **Jeder Laden/POI mit Quelle**, im Zweifel echter Name auf neutraler Fassade.
- Lange Läufe im Hintergrund mit Log in `logs/`, kein Polling. Nach jedem Schritt muss das Spiel starten.

## Token-Budget (Claude Max)
Eine 8-h-Nacht überspannt zwei 5-h-Fenster. Die Nacht muss auch sauber enden, wenn das Limit früher erreicht wird.
- **Pro Nacht höchstens 4 Agents insgesamt** (1 Haiku Inventar, 3 Sonnet Nachbau; Nacht 0: 1 + 2). Kleinkram macht die Hauptsession selbst.
- **Opus-Hauptsession nur für Abnahme, Tickets und kleine Fixes.** Grössere Code-Arbeit schreiben die Sonnet-Agents.
- **Bilder nur als Kontaktbogen** (≤ 1600 px, mehrere Punkte pro Bild), pro Nacht höchstens ~6 Bögen.
- **Nichts Grosses in den Kontext:** Foto-Metadaten, Logs, JSON nur per Skript mit ≤ 30 Zeilen Ausgabe; Logs nur `tail -20`/`grep`.
- **Recherche einmal:** Ergebnisse nach `research/zones/` bzw. `research/catalog/`, nie dieselbe Suche wiederholen.
- **Wenn das Limit knapp wird:** Korrekturrunde streichen, direkt zu Tests + HANDOFF + Commit. Lieber eine Zone halb fertig und dokumentiert als fertig und undokumentiert. Die nächste Nacht beginnt dann mit dem Rest.

## Messgrössen pro Nacht
- Ø-Note der Kamerapunkte (1–5, Abnahme durch Hauptsession), vorher/nachher.
- Offene / erledigte Tickets.
- Textur-MB Handy, fps Handy/PC, Ladezeit.

## Protokoll
<!-- Eine Zeile pro Nacht: Datum – Nacht N – Ergebnis – Note vorher→nachher – offene Tickets – Textur-MB Handy -->
- 2026-10-20 nachmittags – Nacht 5 Zone 3 – Kamerapunkte + Spawn Stauffacher, 3 Agents: 42 Haus-Landmarks, Bullingerplatz-Brunnen, Rasengleis, BR-41 raus; 34 Kacheln, publiziert – Ø ~2.9→3.4 – Z3a/b/c-Tickets – 157/145 MB, 58 fps, tex max 581
- 2026-10-20 – Nacht 4 Zone 5 – Kamerapunkte von Hand, PJZ aufs richtige Gebäude (#63), 3 Agents an Kamerapunkten: 17 Landmarks + Lindenplatz-Pflaster, rote Flächen per Override (#64); 133 Kacheln, publiziert – Ø ~2.7→3.2 – Z5a/b/c-Tickets – 157/145 MB, 58 fps
- 2026-10-19 nachts – Nacht 1 Rest (Zone 4) – Kamerapunkte, Ecken-Abgleich 77 Ecken (wenige sichere Fixes), Autofassade verworfen (#60), Mapillary-Schilder als Schalter (#61), braune Kugel-Sträucher grün, erfundene Gerüste raus (#62); Build 16 – Zone 4 ~3.0 unverändert – T-N1…5, T-S1…7 – 157/145 MB, 58 fps
- 2026-10-19 abends – Nacht 3 Zone 1 – HB-Halle (Buden weg, Tore), Kamerapunkte neu, Foto|Spiel-Werkzeug, +142 Notizen (Geschosse 106→354), 15 Ladenfronten; 24 Kacheln, publiziert – Ø 2.8→2.9 – Z1-1…6 – Langstrasse 157 MB, HB 145 MB, 58 fps
- 2026-10-19 Tag – Zone 2 (~70 %), Fassaden v4, Spawn, HB-Dächer, Schlachthof R4, Linien, Zebras 403, Unterführungen; Builds 14+15, Releases 3+4 – Zone 2 nicht neu benotet – T21, Brücken-Mulden – perf Handy 58 fps
- 2026-10-19 – Sondernacht + Nacht 0 + Nacht 1 (Zone 4) – Schlachthof/Letzipark/FGG/Letzigrund, Katalog (21 Modelle), Fahren, Tram, Zebras, Bodenfehler; Builds 12+13 – Baseline Ø 2.5 (Zone 4 nachher nicht neu benotet) – Tickets T19–T23, knock-Test – perf Handy 58 fps
