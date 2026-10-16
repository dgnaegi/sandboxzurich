# Bahnhof Zürich Hardbrücke (BPS ZHB, DIDOK 3000): Perron-Ebene (Recherche und Modell)

Stand 2026-10-16. Gehört zu `pipeline/landmarks/st_data.py` (Daten), `st_station.py` + `st_kit.py` (Modell `web/public/models/landmarks/stp_hardbruecke.glb`), Fotos `preview/ref_station_hardbruecke.jpg`, Vergleich `preview/station_cmp_hardbruecke.jpg`.

## Quellen und Lizenz
- **SBB Open Data «BehiG Haltekantesegment»** (data.sbb.ch, Datensatz `21197_behig-haltekantesegment`): Perron-Nr., Perrontyp, amtliche Kantenlänge, Gleisachsen-Position am Anfang/Ende der Haltekante. Lizenz: Open-Data-Nutzungsbedingungen SBB (https://data.sbb.ch/page/licence; freie Nutzung inkl. kommerziell, Quellenangabe «Quelle: SBB»). Rohdaten `data/raw/stations/behig_seg_zh.json`. Der Datensatz enthält nur Zahlen/Koordinaten, keine Pläne/Logos.
- **OSM** (ODbL): Perron-Polygone (`railway=platform`), Gleise, `highway=steps`, Aufzüge, `building=roof`, Velo-Parkplätze (`research/stations/osm_hardbruecke.json`).
- **Bahnhofpläne/Orientierungspläne (sbb.ch PDF)** nur angeschaut (Fakten-Vorlage), nicht als Textur oder Datenquelle verwendet; Google Street View nur zur Inspiration.
- **Fotos:** 73 Stück (Mapillary CC BY-SA, Wikimedia Commons CC, Panoramax), Lizenz/Autor je Foto in `research/stations/photos_hardbruecke.json`.
- Alle Schilder sind eigene Gestaltung ohne SBB-Logo; die Uhr ist eine neutrale Uhr (weisses Zifferblatt, schwarze Zeiger, kein roter Sekundenzeiger = nicht die geschützte Bahnhofsuhr).

## Perrons (amtlich + OSM, Höhen = Spiel-Koordinaten)
| Perron | Typ | amtl. Kantenlänge | Mass im Spiel (L x B) | Gleise | Höhe Oberkante (lokal z) | in OSM | Bau |
|---|---|---|---|---|---|---|---|
| 1 | Aussenperron | 320.2 m | 319.9 x 6.9 m | 1 | -6.01 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |
| 2/3 | Mittelperron (nicht in amtl. Liste) | - m | 341.1 x 6.8 m | ?, ? | -5.0 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |
| 4 | Aussenperron | 320.1 m | 320.1 x 6.4 m | ?, 4 | -5.64 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |

Kante: 0.40 m helle Randzone, weisse Sicherheitslinie ca. 0.62-1.10 m hinter der Kante, orangebrauner Streifen; Achsabstand Gleis-Kante 1.67 m (SBB P55).

## Perrondächer
- 24 OSM-Dachflächen im Umkreis (`building=roof`); `pipeline/railways.py` baut sie als flache Platten 3.6 m über Perron. Das Station-GLB hängt darunter Leuchtbänder (nachts emissiv).
- Keine eigenen Dachplatten (alle Perrons in OSM, Dächer von `railways.py`).

## Zugänge
- OSM: 40 Treppen-Ways, 9 Aufzüge im Umkreis.
- Im Modell: 14 Treppenläufe (Steigung 17/30 cm, 1.9-2.4 m breit, Betonwangen, Handlauf) vom Perron nach oben, 6 Treppenabgänge (dunkle Öffnung mit Geländer, gelbe Kante) zur Passage, Aufzugtürme (verglast).
- Begehbar: `web/public/data/station_decks.json` (DeckRows wie Brücken) enthält Perronflächen und Treppenläufe; `engine/tiles.ts` lädt sie in `bridges` (Höhenfläche, Reichweite 1.5 m). Läufe: `research/stations/spots_hardbruecke.json` → `walkable_flights`.

## Möblierung (im Modell)
- Sitzbänke (Holz auf Stahl) alle ca. 26 m (OSM: `bench=yes`), Abfallbehälter alle ca. 42 m (`bin=yes`), Glas-Wartehäuschen je Perron (`shelter=yes`), Abfahrtsanzeigen mit neutraler Uhr (3 pro Perron), Perronnummern-Schilder (dunkelblau, weisse Schrift), Sektorschilder A-F, Stationsnamensschilder, Billettautomaten bei Zugängen, Lampenmasten auf unüberdachten Strecken, Velo-Bügel auf unüberdachten OSM-Velo-Parkplätzen.
- Nicht belegt (keine Quelle, deshalb nicht modelliert): Kioske/Läden auf dem Perron, Durchsageboxen, genaue Standorte der Billettautomaten (Annahme: bei Zugängen).
- Wartende Personen: `research/stations/spots_hardbruecke.json` → `waiting` (184 Punkte [x, y, z, blickX, blickY], hinter der weissen Linie, blicken zum Gleis) und `sit` (36 Bank-Plätze im Format der `benches`-Zeilen von pedspots: [x, y, z, heading, 6]). pedspots.ts ist unverändert (die Punkte liegen auf Perrons, die `railzone.ts` vom Bahngebiet ausnimmt; bei der Übernahme prüfen).

## Beobachtungen aus Fotos (Kontaktbogen `preview/ref_station_hardbruecke.jpg`, 73 Fotos)
- **Perronbelag:** graue Betonplatten ca. 60x60 cm im Läuferverband (#2, #20), breite weisse taktile Leitlinie (ca. 0.5 m, Rippen) mit dunklem Streifen kantenseitig, Kante hell.
- **Konstruktion:** Perrons liegen UNTER der Hardbrücke; sehr grosse Sichtbeton-Stützen (ca. 1.2 m, #2, #6) tragen die Brücke, Untersicht Beton. Brückenebene ca. 7 m über Perron (Treppen der OSM-Ways haben 12-20 m Lauflänge = 7-8 m Höhe).
- **Aufgänge:** Treppen ca. 2.4 m breit, Edelstahl-/Glas-Brüstung, roter Handlauf bzw. roter Stahlträger darüber (#6); Gleisschilder «1» schwarz/weiss mit rotem Rahmen an Stahlträger (#6). Verglaste Liftkabinen (OSM: 9 Aufzüge).
- **Rückwand:** rote Perronrückwand mit Vitrinen unter dem Dach (#44, ref_v3 #26), darüber silbernes Lamellengebäude.
- **Bus-/Tramhaltestellen der Brücke** (Perrondächer mit weissen «Y»-Stützen, #21, #25) sind NICHT Teil dieser Perrons (altes Modell `bahnhof_hardbruecke.glb`, unverändert).
