# Langstrasse Nord (Limmatplatz bis Unterführung) und Markierung der ganzen Langstrasse

## Fotos
- `pipeline/photos/langA_fetch.py`: 112 Zielpunkte (alle 7 m, links/rechts der Achse, 9.5 m Versatz), 212 Ausschnitte aus Panoramax (CC-BY-SA) und Mapillary-Panoramen, `data/raw/photos/langstrasse/`, Metadaten `research/langstrasse_A_photos.json`. Kontaktbögen `preview/ref_langA_01..09.jpg` (`pipeline/photos/langA_sheets.py`).
- Grenze: Die meisten Bilder sind Velo-/Auto-Kameras mit Blick entlang der Strasse (Schrägansichten, selten frontal). Farben sind Schätzungen.
- s = Meter ab Nordportal der Unterführung Richtung Limmatplatz. Ungerade Hausnummern links (187 bei s 49 bis 243 bei s 340), gerade rechts.

## Fassaden und Läden
- `research/buildings/notes_raw_langA_001.tsv` (35 Häuser, Format `pipeline/photos/facades_notes.py`), Läden: 12 Einträge in `research/shops_v3/shops_v3.json` (`annotated_from` = `langA:panoramax`).
- Landmarks `pipeline/landmarks/langA_houses.py` (Kit `langA_kit.py`, Registry `overrides/landmarks_langA.json`): Chicago-Bar-Eck, grünes Eckhaus (Coop to go), Langstrasse 206/210 (terrakotta/korall), Cinque-Eck 215, MeiXin-Eck Josefstrasse, gelbes Haus (Werner's), Langstrasse 243. Gebäude-IDs über `langA_find.py`. Namen nur als freie Schrift.
- Kontrolle Foto | Spiel: `preview/langA_cmp.jpg` (`langA_cmp.py`).

## Markierung (ganze Langstrasse)
- Ist laut Foto/Orthofoto: Nord Limmatplatz-Unterführung durchgehende gelbe Linien ~0.3 m breit, 2.95 m links/rechts der OSM-Achse (Velostreifen/Parkverbot), vor Querstrassen unterbrochen; gelbe Zebrastreifen an jeder Querstrasse; Bodenzahl «30»; Velopiktogramme.
- `pipeline/langA_ortho.py` (Messstellen 120 m), `pipeline/markings_ortho.py` (SWISSIMAGE 0.1 m/px per WMS, 19 Kacheln `data/raw/ortho_langstrasse/ls_*.jpg`, Gelbmaske -> Polygone), `pipeline/markings_synth.py` (Linien Nord an OSM-Kreuzungen unterbrochen), Ergebnis `pipeline/overrides/markings_langstrasse.json`.
- Hook: `pipeline/markings_override.py` (`apply`, in `build_testarea.py` nach `streets.markings`): gemessene Gelbmarkierung auf Fahrbahn zugeschnitten, ergänzt die gebauten Markierungen; `add_white`, `add_yellow`, `cut` für Handkorrekturen.
- Schwäche: Schattenzonen (Südteil) liefern weniger Gelbtreffer; Weiss wird nicht gemessen.
- Vorher|Nachher: `preview/langA_markings.jpg`.
