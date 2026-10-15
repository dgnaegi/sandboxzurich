# swissBUILDINGS3D im Spielgebiet

Skript: `pipeline/parse_sb3d.py` (iterparse, Format wie `../gta6/data/bld/*.pkl`). Ausgabe `data/build/bld/<blatt>.pkl`, Log `logs/parse_sb3d.log`.
Filter: Schwerpunkt in x -2600..1900, y -2900..1300 (lokale Meter). `sources.buildings(margin, area)` bevorzugt diese Pickles.

| Blatt | Gebäude behalten / gesehen | Laufzeit | Zentroid-Bereich (x / y) |
|---|---|---|---|
| 1091-14 | 2884 / 6333 | 16 s | -2600..-150 / -700..1300 |
| 1091-23 | 3923 / 9215 | 36 s | -148..1900 / -701..1300 |
| 1091-32 | 3981 / 4921 | 9 s | -2600..-148 / -2899..-700 |
| 1091-41 | 4448 / 11264 | 51 s | -151..1900 / -2900..-699 |
| 1091-12, -34, -43 | 0 (ausserhalb) | <5 s | leere Pickles |

Total 15236 Gebäude, 153 MB Pickles. Das Gebiet ist vollständig von 14/23/32/41 abgedeckt.

## Lücken
- 1091-13 und 1091-31 liegen nur als FileGDB vor (Layer `Building_solid`, `Roof_solid`, Geometrietyp 1016 = TIN/MultiPatch). pyogrio (GDAL) lehnt diesen Typ ab ("Geometry type is not supported: 1016"), fiona lässt sich nicht bauen. Beide Blätter liegen aber ausserhalb des Spielgebiets (kein Gebäude fehlt). Falls je nötig: CityGML-Variante dieser Blätter laden.
