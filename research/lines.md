# Längslinien (Mittel-, Spur-, Velostreifenlinien)

Auftrag L, 2026-10-19. User: «Strassenlinien sind oft nicht durchgezogen und bisschen weird.» Prüfskript `pipeline/audit_lines.py`
(`--tag before|after`, `--sheet`, `--glb <Ordner mit t_*.glb>`), Zahlen in `data/build/lines_audit_{before,after}.json`, Ortho-Vergleich `preview/lines_audit.jpg`.

## Ursachen (gemessen)
1. **Strichphase je Abschnitt neu gestartet.** `streets.markings` stricht jede OSM-Way einzeln und jedes freie Intervall zwischen Lücken ab 0.5 m neu; der letzte Strich wird abgeschnitten (Stummel < 1.5 m: 47 im ganzen Netz, Strichlänge-Streuung 0.30 m).
2. **6 m Lücke an jedem Way-Ende**, auch wo die Strasse weiterläuft (OSM-Wechsel). Dazu Lücken an Hauszufahrten (service) und an Knicken zwischen zwei Ways derselben Strasse (Winkel > 31°). 13 von 45 Way-Übergängen ohne Kreuzung hatten kein Strich ±4 m.
3. **Achse = rohe OSM-Polylinie** (Knicke an Knoten) mit je Way einem konstanten Fahrbahn-Versatz; an Übergängen springt der Versatz.
4. **Strich unter dem Asphalt (z-Fighting):** Markierung wurde mit Raster 10 m und +0.8 cm gezeichnet, der Asphalt mit 6 m. In den Testkacheln lagen **7.1 % der Farbdreiecke unter der Asphaltfläche, 11.9 % < 3 mm darüber** (`audit_lines.py --glb`). Das sieht aus wie «nicht durchgezogen».
5. Fussgängerstreifen schnitten Mittel-/Velolinien nicht (Strich lief über den Zebra).

## Fix
- `pipeline/markings_lines.py` (neu): Ways einer Strasse (gleicher Name/Klasse, Enden < 0.6 m, geradeaus, genau zwei Enden) werden zu **Ketten** verbunden; die Kette wird auf 1 m neu abgetastet, geglättet (7 m gleitender Mittelwert, Enden fest) und mit dem **zwischen den Ways überblendeten Fahrbahn-Versatz** versetzt. Mittellinie: freie Intervalle zwischen Kreuzungen, Zebras, Tram und Kettenenden; darin werden Striche **eingepasst** (Strich 3 m, Lücke 4.5–8 m, an beiden Enden ein Strich, keine Stummel). Spurlinien (>= 4 Spuren) und Velo-/Busstreifen werden aus derselben glatten Linie geschnitten.
- `streets.py` (`junction_gaps`, `markings`): Hauszufahrten unterbrechen die Mittellinie nicht (`gaps_main`), Knoten zwischen zwei Ways derselben Strasse sind keine Kreuzung, Zebras/Haltelinien liefern Lücken für Mittel-, Spur- und Velolinien; Velostreifen unterbrochen 1 m / 1 m.
- `build_testarea.py` (Linien-Teil in `_ground_base`): Markierungen mit Raster `ROAD_CELL` (wie Asphalt) und `LINE_LIFT` 3 cm (`SBZ_LINE_LIFT`).
- Kachel-Clip: Linien sind globale Polygone, erst `intersection(roads)` je Kachel; Phase hängt nicht an Kacheln (war schon so, bleibt).

## Schweizer Masse
Leitlinie (Mittellinie) innerorts 3 m Strich / 6 m Lücke (Stadt Bern, Normalien 2.10, SSV Nr. 6.03; Quellen: bern.ch «Mittellinien, Längsmarkierungen», SN 640 850). Breite im Spiel 0.12 m (Bern nennt für allgemeine Linien 15 cm; 12 cm ist eine Annahme aus dem Auftrag, nicht belegt). Velostreifen gelb, unterbrochen 1 m / 1 m vor Einmündungen, sonst durchgezogen (Annahme laut Auftrag, nicht im Detail gegen SSV geprüft).

## Zahlen vorher -> nachher (ganzes Netz, Audit mit 0.3 m Toleranz)
| | vorher | nachher |
|---|---|---|
| Stummel-Striche (< 1.5 m) | 47 | 19 |
| Strichlänge-Streuung (sd) | 0.28–0.39 m | 0.13–0.15 m |
| Way-Übergänge ohne Strich ±4 m | 13 von 45 | 8 von 45 (Rest: Zebra/Tram/Zufahrten) |
| Velolinie: Lücken > 3 m | 0 | 3 (Zebras, gewollt); Abdeckung 1.00 -> 0.97 |
| Farbdreiecke unter Asphalt (4 Testkacheln) | 7.1 % (< 3 mm: 11.9 %) | 2.0 % (< 3 mm: 4.1 %), Ø Abstand 7.8 -> 16.9 mm |

Kachelvergleich Badener-/Hard-/Lang-/Birmensdorferstrasse (Topdown + Bodenperspektive, nur Bodenebenen aus den Kachel-GLBs): `preview/lines_cmp.jpg` (`pipeline/lines_cmp.py`). Ortho-Vergleich: `preview/lines_audit.jpg`. Hinweis: Kachelraster 6 m teilt Striche, der Rest-Anteil unter dem Asphalt kommt vom grossen Asphaltdreieck (nur Randpunkte).
