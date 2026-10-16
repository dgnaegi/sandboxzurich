# Zürich Hauptbahnhof (HB) – Recherche und Modellgrundlagen

Stand 2026-10-16. Alles hier ist **Referenz**: Fotos werden nie als Textur verwendet, kein SBB-Logo, nicht die geschützte SBB-Bahnhofsuhr (siehe `docs/DATA_SOURCES.md`).
Fotos: **632 Bilddateien / 660 Einträge** in `data/raw/photos/hb/` (max. 1280 px; Lizenzen je Bild in `CREDITS.md`, Metadaten `photos.json`; Quellen: Wikimedia Commons Kategorie «Zürich Hauptbahnhof» + Unterkategorien, Geo- und Textsuche = 565, Mapillary 95, Panoramax 5; Lizenzen CC BY-SA 4.0/3.0/2.0, CC BY, CC0, PD). Kontaktbögen `preview/ref_hb_<gruppe>_<n>.jpg` (Gruppen: haupthalle 53, querhalle 23, perron 125, interior 184, exterior 113, tafeln 41, markt 17, loewenstrasse 4, mapillary 95, panoramax 5; Nummern = Index in `photos.json`). Der Abruf wurde bei Wikimedia-Ratenlimit abgebrochen (restliche Unterkategorien Löwenstrasse/Museumstrasse/Nachtbilder nicht geladen; `pipeline/photos/fetch_hb.py` ist wiederaufnehmbar). Foto ↔ Spiel: `preview/hb_cmp_{halle,fassade,perron,querhalle}.jpg` (`pipeline/landmarks/hb_cmp.py`, mit `GAME=1` aus dem Spiel mit den HB-Kacheln).

## Lage (Spielgebiet)
- Modell-Koordinaten: Ursprung `ORG` = lokal (1760, -650), Achse `d` = Gleisrichtung (WSW→ONO, Winkel -21°), `c` quer dazu (nach NNO). Heading der Modelle -21°.
- Vor der Änderung endete das Spielgebiet bei x ≈ 1693 (Bbox) bzw. am Perronkopf: der HB-Kopf (Haupthalle, Querhalle, Bahnhofplatz-Rand) lag **183 m ausserhalb**, nur die westlichen Perrons waren im Gebiet.
- Erweiterung: `pipeline/overrides/playarea_extra.json` (orientiertes Rechteck, d -125..138, c -100..72) und kleiner Edit in `pipeline/playarea.py`. Fläche 6.88 → 6.93 km², Bbox x max 1693 → 1915.
  Neue **Spielkacheln** (200 m): `t_9_-4` (x 1800–2000, y -800…-600) und `t_9_-3` (y -600…-400). Neue **Kulissenkacheln**: `t_9_-6`, `t_9_-5`, `t_10_-5`, `t_10_-4`, `t_10_-3`. (`t_8_-4`, `t_8_-3` waren schon Spielkacheln, ihr Inhalt ändert sich durch Hide/Collider.) Der Bauzaun rückt an die neue Kante (Bahnhofquai/Museumstrasse, d = 138).

## Masse (Quellen: OSM `building:part`, swissBUILDINGS3D-Dachhöhen, SBB Open Data `perron`)
| Teil | Mass | Quelle |
|---|---|---|
| **Wannerhalle = Haupthalle** (`building:part`, alt_name Haupthalle, `height=24 m`) | d -20…113 (**133 m**), c -25…17 (**42 m**), Traufe 21 m, Tonnenfirst 25 m, 7 Oberlicht-Firste 28 m (Abstand 18.2 m) | OSM-Way, 3D-Dächer |
| Südtrakt (Fassade Bahnhofplatz, 4 Geschosse) | d -8…105, c -67…-24 (Fassadenblock 22 m tief, Traufe ~17.5 m, Mansarde bis ~20 m; innen 11 m) | OSM `Südtrakt` (134 × 44), 3D |
| Nordtrakt (Landesmuseum-/Platzspitz-Seite) | d -20…96, c 17…57, Traufe 15 m, First 20 m | OSM `Nordtrakt` (134 × 40) |
| Querhalle | d -45…-21 (24 m breit), c -64…57 (~120 m lang), Traufe 11 m, First 17.8 m, Glas-/Stahlfachwerk | 3D, Fotos |
| Perronhalle (Längshallen 1–8) | je eine Halle pro Inselperron, Spannweite ~17.3 m, Traufe 8.4 m, First 12 m, Stahlstützen in der Perronachse alle ~17.5 m | 3D (Dach z 8–10 + 2.9), SBB `sektortafel` (`BA-Dach_BE Langshalle 3…8`) |
| Perrons 4–17 (Mittelperrons), 3 und 18 (Aussenperrons) | Länge 418–433 m, Breite 9.5 m (Aussenperrons 6–7 m), Gleisabstand 3.9 m | OSM-Relationen, SBB `perron` |
| Kopf der Perrons | d = -45.0 (alle auf einer Linie, 17.3 m Perronabstand) | OSM |
Der Auftrag nannte 170 × 43 m für die Haupthalle: OSM und 3D-Daten ergeben **133 × 42 m**, passend zur Breite 43 m. Die 170 m dürften die Gesamtlänge Hauptgebäude inkl. Querhalle meinen (~165 m: d -45…113 + Wanner-Anbauten).
Höhenbezug: Modell-z = Höhe über Terrain (-2.9 m im lokalen Höhensystem = 408 m ü. M., Terrain im HB-Bereich ±0.2 m eben; Hallenboden wird per `terrain_cuts.json` (neuer Modus `poly` = flach) auf -2.9 gelegt).

## Architektur (aus den Fotos, `ref_hb_haupthalle_*`, `ref_hb_querhalle_*`, `ref_hb_perron_*`)
- **Haupthalle innen**: unten Bogenarkade (3–3.5 m breite Rundbögen zu Läden/Eingängen, grünlich gerahmte Glastüren am Ostende), darüber Gesims und rötlicher Fries, darüber pro 18-m-Joch **ein grosses Rundbogenfenster (7–9 m, Sprossen) und zwei kleine**, Pilaster in Sandstein (ocker bis rosa-beige), Hauptgesims bei 21 m. Ostwand (Bahnhofquai): 7 Türbögen, 2 grosse Rundbogenfenster, kleine Bogenfenster dazwischen. Westseite öffnet sich zur Querhalle (grosse Glasfront mit Raster).
- **Dach** der Haupthalle: dunkle Stahlbinder (braun/rostfarben), Oberlichter in 7 Querfirsten, Lampenreihen, Zugstangen; Decke dunkelgrün/grau.
- **Boden**: dunkelgrauer Naturstein mit breiten hellgrauen Bändern (Längsachse + Querbänder), Querhalle heller.
- **Querhalle**: Glasdach auf schwarzen Stahlbögen, Stahlfachwerk-Stützen, riesige blaue Abfahrtstafeln (rot/weiss/blau, hier neutral nachgebaut), Uhren, Kioske, Treppen/Rolltreppen ins Shopville (Zwischengeschoss -1, Shopville -2), Zugang zu den Perrons durch die offene Westseite.
- **Perronhalle**: schwarze/dunkelgraue Stahlstützen (verjüngt, gabelförmig) in der Perronachse, Sheddach mit Glasstreifen, helle Betonperrons mit Taktilstreifen und weisser Sicherheitslinie, Sektortafeln (A–F) und Gleisnummern an den Stützen, Anzeigetafeln, Uhren, Wartehäuschen aus Glas, Treppen/Lifte.
- **Fassade Bahnhofplatz** (Wanner 1871, Neorenaissance): heller Sandstein, Rustika-Sockel mit Rundbögen, Beletage mit Rundbogenfenstern in Gewänden, Obergeschoss mit Rechteckfenstern, Gesimse, Mansarddach; Mittelportal als **Triumphbogen** (~15 m breit, ~14.5 m hoch).
- **Typische Objekte**: «L'ange protecteur» (Niki de Saint Phalle, 1997) hängt in der Haupthalle (blau/bunt, ~11 m); Märkte/Events in der Halle (Weihnachtsmarkt, Hüttchen), Kioske, Bänke, Kristall-Lüster (Weihnachten), grosse Werbetafeln.
- **Beleuchtung**: Hängeleuchten in Reihen unter dem Dach (Nacht: emissive Platten), Oberlichter Tageslicht, Perrons mit Leuchtbändern.
- **Untergrund**: Gleise 31–34 (Löwenstrasse, -4), 41–44 (Museumstrasse, -3), Shopville -2: nicht modelliert (nur Treppenabgänge als dunkle Öffnungen mit Geländer und Schild).

## Gleise / Perrons → `tracks.json`
`research/hb/tracks.json`: je Perron Kopf-d, Kantenlage, Kopfecken und Perronmitte in lokalen Metern, je Gleis die Gleisachse am Prellbock-Ende (Kopfpunkt). Tabelle (Kopf = Querhalle, Linie d_abs = 1831 → lokal x/y siehe Datei):
| Perron | Gleise | c (rel. ORG) SW-Kante…NO-Kante | Kopfmitte lokal (x, y) |
|---|---|---|---|
| 3 | 3 | -74.9 … -69.1 | (1692.3, -701.2) |
| 4/5 | 4, 5 | -61.4 … -51.9 | (1697.8, -686.8) |
| 6/7 | 6, 7 | -44.2 … -35.2 | (1703.8, -670.9) |
| 8/9 | 8, 9 | -26.8 … -17.8 | (1710.0, -654.7) |
| 10/11 | 10, 11 | -9.8 … -0.2 | (1716.2, -638.6) |
| 12/13 | 12, 13 | 7.4 … 17.0 | (1722.3, -622.5) |
| 14/15 | 14, 15 | 24.6 … 34.2 | (1728.5, -606.4) |
| 16/17 | 16, 17 | 41.6 … 51.1 | (1734.5, -590.6) |
| 18 | 18 | 59.2 … 66.1 | (1740.3, -575.4) |
| 31/32, 33/34 (Löwenstrasse, -4) | unterirdisch, Kopf d_abs 1901 → unter der Haupthalle | | (1764.5, -707.7), (1771.4, -690.0) |
| 41/42, 43/44 (Museumstrasse, -3) | unterirdisch, Kopf d_abs 1967/1952 | | (1865.1, -630.0), (1857.5, -608.8) |
Gleisnummern: Perron X/Y hat Gleis X auf der Südwest-, Gleis Y auf der Nordost-Seite (Zwischen zwei Mittelperrons liegen Gleis Y und Gleis X+2 im Abstand 3.9 m, z. B. 5 und 6) (Aussenperron 3 liegt südwestlich von Gleis 3, Aussenperron 18 nordöstlich von Gleis 18; Gleisachse = Perronkante ± 1.9 m). In `tracks.json` steht zusätzlich `osm_rail_ends`: die OSM-Gleisenden (Prellböcke) liegen bei **d ≈ -49** (4 m vor dem Perronkopf d = -45) auf den Gleisachsen c = -67.4/-63.3 (Gl. 3/4), -50.2, -45.6, -33.1, -28.6, -16.1 … 57.7 (Gl. 5…18). Das Modell liefert Perrons (d -470…-45) mit Kanten und Dächern, **keine Schienen** (gehören `pipeline/railways.py`).

## Open Data
- **SBB Open Data** (data.sbb.ch, Lizenz: «Open use»-Lizenzseite https://data.sbb.ch/page/licence; Nutzung mit Quellenangabe «SBB» erlaubt): Datensätze `perron` (13 Treffer im 450-m-Umkreis: Typ, Länge, Fläche), `perronoberflache` (Bitumen), `sektortafel` (179 Tafeln, `montage_an` = Längshalle 3–8), `haltestelle-uhr` (106), `billetautomat` (35), `mobiliar-im-bahnhof` (78). Rohdaten `data/raw/sbb/hb_records.json`. Keine Geometrie der Perronkanten als Linien vorhanden (nur Punkte) → Kanten aus OSM-Relationen.
- **OSM**: `railway=platform`-Relationen (4–17 mit `level=0`, 31–34 `level -4`, 41–44 `level -3`), `building:part` Wannerhalle/Nordtrakt/Südtrakt, `indoor=*` (Shopville, Zwischengeschoss, Passagen; Rohdaten `research/hb/osm.json`).
- **swissBUILDINGS3D 2019**: Dachhöhen (Haupthalle-Rhythmus, Längshallen); die Hauptgebäude-Footprints (`ID_2B72335B…`) und 40 Dachflächen-Gebäude der Perronhalle werden ersetzt (`research/hb/hide.json`).

## Modelle (Pipeline)
`pipeline/landmarks/hb_kit.py` (Rahmen, Primitive, Schilder-Atlas, `register`), `hb_geom.py` (Masse), `hb_shell.py` (Aussenhülle), `hb_inner.py` (Innenraum, begehbar), `hb_perron.py` (Perrons/Dächer), `hb_props.py` (Tafeln, Uhren, Kioske, Marktstände, Engel), `hb_hide.py`, `hb_tracks.py`, `hb_view.py` (Modell allein im Viewer). Einträge in `pipeline/overrides/landmarks_hb.json`: `Zürich Hauptbahnhof` (Hülle, immer ≤ 600 m), `… + Innenraum` (`walkable`, `load_r` 190, eigene Collider-Ringe), `… + Perrons` (`walkable`, `load_r` 480).
