# Bahnhof Zürich Wiedikon (DIDOK 3002): Perron-Ebene (Recherche und Modell)

Stand 2026-10-16. Gehört zu `pipeline/landmarks/st_data.py` (Daten), `st_station.py` + `st_kit.py` (Modell `web/public/models/landmarks/stp_wiedikon.glb`), Fotos `preview/ref_station_wiedikon.jpg`, Vergleich `preview/station_cmp_wiedikon.jpg`.

## Quellen und Lizenz
- **SBB Open Data «BehiG Haltekantesegment»** (data.sbb.ch, Datensatz `21197_behig-haltekantesegment`): Perron-Nr., Perrontyp, amtliche Kantenlänge, Gleisachsen-Position am Anfang/Ende der Haltekante. Lizenz: Open-Data-Nutzungsbedingungen SBB (https://data.sbb.ch/page/licence; freie Nutzung inkl. kommerziell, Quellenangabe «Quelle: SBB»). Rohdaten `data/raw/stations/behig_seg_zh.json`. Der Datensatz enthält nur Zahlen/Koordinaten, keine Pläne/Logos.
- **OSM** (ODbL): Perron-Polygone (`railway=platform`), Gleise, `highway=steps`, Aufzüge, `building=roof`, Velo-Parkplätze (`research/stations/osm_wiedikon.json`).
- **Bahnhofpläne/Orientierungspläne (sbb.ch PDF)** nur angeschaut (Fakten-Vorlage), nicht als Textur oder Datenquelle verwendet; Google Street View nur zur Inspiration.
- **Fotos:** 60 Stück (Mapillary CC BY-SA, Wikimedia Commons CC, Panoramax), Lizenz/Autor je Foto in `research/stations/photos_wiedikon.json`.
- Alle Schilder sind eigene Gestaltung ohne SBB-Logo; die Uhr ist eine neutrale Uhr (weisses Zifferblatt, schwarze Zeiger, kein roter Sekundenzeiger = nicht die geschützte Bahnhofsuhr).

## Perrons (amtlich + OSM, Höhen = Spiel-Koordinaten)
| Perron | Typ | amtl. Kantenlänge | Mass im Spiel (L x B) | Gleise | Höhe Oberkante (lokal z) | in OSM | Bau |
|---|---|---|---|---|---|---|---|
| 1 | Aussenperron | 305.7 m | 312.8 x 7.1 m | 1 | -4.92 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |
| 2/3 | Mittelperron | 323.8 m | 328.5 x 8.1 m | 2, 3 | -4.9 m (Kante 0.55 m über Schienenoberkante) | ja | Platte von railways.py, Möblierung/Schilder/Dach-Details im Station-GLB |

Kante: 0.40 m helle Randzone, weisse Sicherheitslinie ca. 0.62-1.10 m hinter der Kante, orangebrauner Streifen; Achsabstand Gleis-Kante 1.67 m (SBB P55).

## Perrondächer
- 27 OSM-Dachflächen im Umkreis (`building=roof`); `pipeline/railways.py` baut sie als flache Platten 3.6 m über Perron. Das Station-GLB hängt darunter Leuchtbänder (nachts emissiv).
- Keine eigenen Dachplatten (alle Perrons in OSM, Dächer von `railways.py`).

## Zugänge
- OSM: 10 Treppen-Ways, 2 Aufzüge im Umkreis.
- Im Modell: 4 Treppenläufe (Steigung 17/30 cm, 1.9-2.4 m breit, Betonwangen, Handlauf) vom Perron nach oben, 0 Treppenabgänge (dunkle Öffnung mit Geländer, gelbe Kante) zur Passage, Aufzugtürme (verglast).
- Begehbar: `web/public/data/station_decks.json` (DeckRows wie Brücken) enthält Perronflächen und Treppenläufe; `engine/tiles.ts` lädt sie in `bridges` (Höhenfläche, Reichweite 1.5 m). Läufe: `research/stations/spots_wiedikon.json` → `walkable_flights`.

## Möblierung (im Modell)
- Sitzbänke (Holz auf Stahl) alle ca. 26 m (OSM: `bench=yes`), Abfallbehälter alle ca. 42 m (`bin=yes`), Glas-Wartehäuschen je Perron (`shelter=yes`), Abfahrtsanzeigen mit neutraler Uhr (3 pro Perron), Perronnummern-Schilder (dunkelblau, weisse Schrift), Sektorschilder A-F, Stationsnamensschilder, Billettautomaten bei Zugängen, Lampenmasten auf unüberdachten Strecken, Velo-Bügel auf unüberdachten OSM-Velo-Parkplätzen.
- Nicht belegt (keine Quelle, deshalb nicht modelliert): Kioske/Läden auf dem Perron, Durchsageboxen, genaue Standorte der Billettautomaten (Annahme: bei Zugängen).
- Wartende Personen: `research/stations/spots_wiedikon.json` → `waiting` (126 Punkte [x, y, z, blickX, blickY], hinter der weissen Linie, blicken zum Gleis) und `sit` (23 Bank-Plätze im Format der `benches`-Zeilen von pedspots: [x, y, z, heading, 6]). pedspots.ts ist unverändert (die Punkte liegen auf Perrons, die `railzone.ts` vom Bahngebiet ausnimmt; bei der Übernahme prüfen).

## Beobachtungen aus Fotos (Kontaktbogen `preview/ref_station_wiedikon.jpg`, 60 Fotos; nur #5 zeigt das Perron, der Rest Vorplatz/Aufnahmegebäude/Tram)
- **Perron/Dach (#5, Commons):** historisches Stahlperrondach: dunkle schlanke Stahlstützen mit geschwungenen Konsolen, gewölbte beige Untersicht, im Hintergrund Backstein-/Sandsteinmauern und Bögen der Stützmauern; kleine weiss/blaue Perronschilder («2 B | B 3»), gelbe taktile Leitlinie. Die OSM-Dächer werden von `railways.py` als flache Platten gebaut (nicht gewölbt); die Stützen im Spiel sind schlanke graue Masten (gleiche Funktion).
- **Aufnahmegebäude** (Reiterbahnhof, nicht Teil dieser Perrons): Zürich-Wiedikon-SBB-Fries, hohe Pfeilerfenster, quadratische Uhr mit römischen Ziffern (#32, #33).
- **Zugänge:** Treppen und Lifte (OSM: 2 Aufzüge, 4 Treppenläufe) führen vom Perron im Einschnitt (ca. 8 m tiefer) ins Aufnahmegebäude bzw. zur Strasse (Seite Sihlhölzli/Stauffacher).
