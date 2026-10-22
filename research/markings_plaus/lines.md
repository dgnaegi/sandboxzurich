# Strassenmarkierungen plausibilisieren, Zonen 1-3 (21.10.2026)

User: «Viele Strassenmarkierungen sind falsch.» Methode: 60-m-Zellen, Spiel von oben (aus den Kachel-GLBs, `pipeline/markings_plaus.py`) neben SWISSIMAGE 0.25 m
(swisstopo OGD, `data/raw/ortho_025`), 36 Zellen je Zone (Seed 7, `z<N>_before_*.jpg`, Zellenliste `z<N>_before_cells.tsv`), plus Grossansichten 8 px/m (`--big`).
Werkzeuge nehmen `--zone N` (zones.json). Das Ortho zeigt dünne Linien nur schwach (JPEG-Chroma), deshalb wurden Linien auch als Profil über die Linienlänge
gemessen (`pipeline/markings_plaus_lines.py`).

## Befunde (Ursache -> Fix)
| Klasse | Beleg | Ursache | Fix |
|---|---|---|---|
| C1 Velostreifen-Linie durchgezogen statt unterbrochen | Ortho Lagerstrasse, Hohlstrasse, Kasernenstrasse, Zollbrücke: gelb unterbrochen, Periode ~6 m (Autokorrelation 10 von 31 periodischen Stücken bei 6.0-6.5 m), Strichanteil 0.2-0.5 bei 96 % von 105 Stücken, > 0.8 nur bei 4 %. SSV Art. 74a Abs. 5 / Markierung 6.09: «unterbrochene oder ununterbrochene gelbe Linie», unterbrochen = Regelfall | `streets.markings` zeichnete jede Velostreifen-Linie durchgezogen (Annahme aus Auftrag L, «nicht gegen SSV geprüft») | `pipeline/markings_bike.py`: Strich 2.5 m / Lücke 3.5 m (`fit_dashes`), vor Einmündungen weiter 1 m / 1 m |
| C2 Velostreifen auf der Innenseite getrennter Fahrbahnen | Badenerstrasse (Tram in der Mitte, zwei Einrichtungs-Ways): 4 Linien statt 2; OSM `cycleway:left=no` | amtliches Velonetz markiert `BOTH` pro Way, auch für die beiden Fahrbahnen einer getrennten Strasse | `markings_bike.prune_lanes`: auf Einrichtungs-Ways zählt ein explizites OSM `no` (Seite fällt weg, Piktogramme folgen). 1.9 km in Zonen 1-3 |
| C3 Fussgängerstreifen 3-5 m neben den Streifen | je Zone 7-15 Streifen (25 % der Scan-Zebras) mit f0 < 0.12 am Ort, aber f > 0.35 bei -4 m entlang der Strasse; nach Fix 125 von 125 belegt | `crossings._scan25`, Rettungszweig: das 0.5-m-Fenster (`ortho_score`, Verschiebung ±4 m, Gleichstand -> erste) verschob den Blob-Mittelpunkt um ~4 m | Blob-Mittelpunkt (0.25 m) bleibt, die Verschiebung entfällt; wirkt stadtweit (~100 Streifen) |
| C4 OSM-Tag-Zebra ohne Streifen im Ortho | 17 von 63 Tag-Zebras (Z1 4/17, Z2 5/21, Z3 8/25) | meist Schatten (Streifen unsichtbar) oder OSM-Knoten auf Fussweg | unverändert (Schatten lässt sich nicht entscheiden) |

## Gemessen, aber nicht gefixt
- Velostreifen-Linie liegt dort, wo am Kerb geparkt wird, 3-4 m zu nah am Kerb: Lagerstrasse (`cycleway:both=lane` + Parkplätze) hat die gelbe Linie ~4.5 m vom Kerb (Parkstreifen 2 + Radstreifen 1.5 + Markierung), das Spiel 1.5 m. Die OGD-Parkplatzpunkte liegen aber 2-4 m von der OSM-Achse (nicht am Kerb), die Zuordnung Seite -> Parken ist damit nicht belastbar (`markings_parking.py` ist der Ansatz, 1 von 31 Stücken erkannt). Nur 8 % der Linienfläche liegen in Parkfeldern.
- Rot eingefärbte Velostreifen (Bahnhofquai, Lagerstrasse Süd, Hohlstrasse) sind im Ortho deutlich rot, die Rot-Erkennung (`streets_ortho.red_surfaces`) liefert dort pixelige Flecken und lässt Streifen aus.
- Weisse Mittellinien: nur in der Hälfte der besonnten 40-m-Fenster als Profilspitze messbar (Strichanteil 1/3 verdünnt); Zusammenhang Spiel/Realität in den Grossansichten plausibel, keine systematische Abweichung gefunden.
- Parkfeld-Rechtecke liegen auf der Trottoir-Schicht (35), nicht auf Fahrbahn (34); optisch (Spiel von oben) kein Fehler.

## Für die Zonen-4/5-Runde
`.venv/bin/python pipeline/markings_plaus.py --zone N --n 36 --seed 7` (Blatt `research/markings_plaus/z<N>_before_*.jpg`), `--big --cells "x,y;x,y"` für 8-px/m-Paare, `pipeline/markings_plaus_lines.py --zone N` (Profil je Velostreifen-Stück),
`pipeline/markings_plaus_classify.py --zone N --tag before|after`. Code-Fixes C1-C3 gelten stadtweit; die Zonen-4/5-Kacheln müssen nur neu gebaut werden.
