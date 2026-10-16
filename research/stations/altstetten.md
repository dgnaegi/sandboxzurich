# Bahnhof Zürich Altstetten (BPS ZAS, DIDOK 3001): Perron-Ebene (Recherche und Modell)

Stand 2026-10-16. Gehört zu `pipeline/landmarks/st_data.py` (Daten), `st_station.py` + `st_kit.py` (Modell `web/public/models/landmarks/stp_altstetten.glb`), Fotos `preview/ref_station_altstetten.jpg`, Vergleich `preview/station_cmp_altstetten.jpg`.

## Quellen und Lizenz
- **SBB Open Data «BehiG Haltekantesegment»** (data.sbb.ch, Datensatz `21197_behig-haltekantesegment`): Perron-Nr., Perrontyp, amtliche Kantenlänge, Gleisachsen-Position am Anfang/Ende der Haltekante. Lizenz: Open-Data-Nutzungsbedingungen SBB (https://data.sbb.ch/page/licence; freie Nutzung inkl. kommerziell, Quellenangabe «Quelle: SBB»). Rohdaten `data/raw/stations/behig_seg_zh.json`. Der Datensatz enthält nur Zahlen/Koordinaten, keine Pläne/Logos.
- **OSM** (ODbL): Perron-Polygone (`railway=platform`), Gleise, `highway=steps`, Aufzüge, `building=roof`, Velo-Parkplätze (`research/stations/osm_altstetten.json`).
- **Bahnhofpläne/Orientierungspläne (sbb.ch PDF)** nur angeschaut (Fakten-Vorlage), nicht als Textur oder Datenquelle verwendet; Google Street View nur zur Inspiration.
- **Fotos:** 52 Stück (Mapillary CC BY-SA, Wikimedia Commons CC, Panoramax), Lizenz/Autor je Foto in `research/stations/photos_altstetten.json`.
- Alle Schilder sind eigene Gestaltung ohne SBB-Logo; die Uhr ist eine neutrale Uhr (weisses Zifferblatt, schwarze Zeiger, kein roter Sekundenzeiger = nicht die geschützte Bahnhofsuhr).

## Perrons (amtlich + OSM, Höhen = Spiel-Koordinaten)
| Perron | Typ | amtl. Kantenlänge | Mass im Spiel (L x B) | Gleise | Höhe Oberkante (lokal z) | in OSM | Bau |
|---|---|---|---|---|---|---|---|
| 2 | Hausperron | 320.0 m | 320.2 x 6.0 m | 2 | -11.57 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |
| 3/4 | Mittelperron | 375.3 m | 367.1 x 8.2 m | 3, 4 | -11.58 m (Kante 0.55 m über Schienenoberkante) | NEIN | Platte, Kante, weisse Linie, taktile Linie, Dach im Station-GLB (stp_altstetten.glb) |
| 6/7 | Mittelperron | 320.2 m | 318.3 x 8.3 m | 6, 7 | -11.52 m (Kante 0.55 m über Schienenoberkante) | NEIN | Platte, Kante, weisse Linie, taktile Linie, Dach im Station-GLB (stp_altstetten.glb) |

Kante: 0.40 m helle Randzone, weisse Sicherheitslinie ca. 0.62-1.10 m hinter der Kante, orangebrauner Streifen; Achsabstand Gleis-Kante 1.67 m (SBB P55).

## Perrondächer
- 27 OSM-Dachflächen im Umkreis (`building=roof`); `pipeline/railways.py` baut sie als flache Platten 3.6 m über Perron. Das Station-GLB hängt darunter Leuchtbänder (nachts emissiv).
- Eigene Dächer im Station-GLB nur dort, wo das Perron in OSM fehlt (Altstetten 3/4, 6/7: Sichtbeton, 4.2 m, Brettschalungs-Textur, Stützen alle 12 m).

## Zugänge
- OSM: 21 Treppen-Ways, 8 Aufzüge im Umkreis.
- Im Modell: 0 Treppenläufe (Steigung 17/30 cm, 1.9-2.4 m breit, Betonwangen, Handlauf) vom Perron nach oben, 5 Treppenabgänge (dunkle Öffnung mit Geländer, gelbe Kante) zur Passage, Aufzugtürme (verglast).
- Begehbar: `web/public/data/station_decks.json` (DeckRows wie Brücken) enthält Perronflächen und Treppenläufe; `engine/tiles.ts` lädt sie in `bridges` (Höhenfläche, Reichweite 1.5 m). Läufe: `research/stations/spots_altstetten.json` → `walkable_flights`.

## Möblierung (im Modell)
- Sitzbänke (Holz auf Stahl) alle ca. 26 m (OSM: `bench=yes`), Abfallbehälter alle ca. 42 m (`bin=yes`), Glas-Wartehäuschen je Perron (`shelter=yes`), Abfahrtsanzeigen mit neutraler Uhr (3 pro Perron), Perronnummern-Schilder (dunkelblau, weisse Schrift), Sektorschilder A-F, Stationsnamensschilder, Billettautomaten bei Zugängen, Lampenmasten auf unüberdachten Strecken, Velo-Bügel auf unüberdachten OSM-Velo-Parkplätzen.
- Nicht belegt (keine Quelle, deshalb nicht modelliert): Kioske/Läden auf dem Perron, Durchsageboxen, genaue Standorte der Billettautomaten (Annahme: bei Zugängen).
- Wartende Personen: `research/stations/spots_altstetten.json` → `waiting` (222 Punkte [x, y, z, blickX, blickY], hinter der weissen Linie, blicken zum Gleis) und `sit` (38 Bank-Plätze im Format der `benches`-Zeilen von pedspots: [x, y, z, heading, 6]). pedspots.ts ist unverändert (die Punkte liegen auf Perrons, die `railzone.ts` vom Bahngebiet ausnimmt; bei der Übernahme prüfen).

## Beobachtungen aus Fotos (Kontaktbogen `preview/ref_station_altstetten.jpg`, 52 Fotos; Perronfotos #45-51 Commons CC BY-SA 4.0, Max Vogt)
- **Perrondach:** Sichtbeton mit Brettschalung (braungrau), Untersicht ca. 3.5-4 m über Perron, rechteckige Sichtbeton-Stützen (ca. 0.5 m, Holzschalung) auf der Perronmittelachse; Wannenleuchten (weiss, ca. 1.2 x 0.3 m) an der Untersicht.
- **Beschilderung:** dunkelblaue Schilder mit weisser Schrift: Schrägschild «Altstetten» an Stützen, Täfelchen «Gleis 7 | Sektor E» an der Untersicht; im Treppenabgang schwarzes Hängeschild «Gleis 3 Zürich Altstetten Gleis 4» (#7).
- **Belag:** dunkelgrauer Asphalt/Belag, weisse taktile Leitlinie (3 Rippen) ca. 0.6 m hinter der Kante, daneben oranger Streifen; Lifte verglast mit Stahlrahmen (#48), Zugang über Treppen/Lifte in die Passage (#0-4, 8-9 Passage mit Wandmalerei Blätter/Vögel; #29 Treppenhaus mit Leiter/gelbem Licht).
- **Perron 2 (Hausperron)** liegt an der Seite der Bahnhofsgebäude/IBM-Stengel; die Mittelperrons 3/4 und 6/7 fehlten in OSM und im Spiel (bis jetzt).
