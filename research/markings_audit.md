# Markierungs-Audit gegen SWISSIMAGE (`pipeline/audit_markings.py`)

Spiel: 1736811 m² Fahrbahn, 42536 m² Gelb, 23325 m² Weiss.

Orte (zusammengelegte 10-m-Zellen) nach Art: extra_white 37, extra_yellow 126, missing_white 157, missing_yellow 1032

Weisse Linien (12 cm) sind bei 0.5 m/px kaum messbar: «missing_white/extra_white» nur grobe Hinweise; Gelb (Zebra, Randlinien) ist belastbar.

| Art | Fläche m² | x | y |
|---|---|---|---|
| missing_yellow | 446.0 | 758.5 | 169.4 |
| missing_yellow | 440.0 | 787.8 | 34.7 |
| missing_yellow | 432.9 | 144.2 | -980.2 |
| missing_yellow | 415.0 | -235.6 | 262.6 |
| missing_yellow | 370.8 | -139.4 | 434.9 |
| missing_yellow | 365.1 | 289.6 | -1193.2 |
| missing_yellow | 333.0 | -530.8 | -278.7 |
| missing_yellow | 302.5 | -2285.3 | 405.1 |
| missing_yellow | 294.0 | -700.9 | -984.2 |
| missing_yellow | 276.4 | 839.6 | -474.4 |
| missing_yellow | 275.8 | -2154.5 | 777.8 |
| missing_yellow | 273.2 | 1105.2 | 107.4 |
| missing_yellow | 270.0 | -1872.7 | -103.8 |
| missing_yellow | 261.0 | 1178.2 | -879.4 |
| missing_yellow | 240.9 | 689.7 | -850.8 |
| missing_yellow | 236.0 | 872.4 | -148.1 |
| missing_yellow | 217.5 | 1479.8 | 550.2 |
| missing_yellow | 193.8 | -513.5 | -1142.1 |
| missing_yellow | 185.5 | 671.0 | -1643.8 |
| missing_yellow | 180.9 | 1103.7 | 53.9 |
| missing_yellow | 174.5 | -1.1 | -1840.2 |
| missing_yellow | 173.5 | -1360.7 | 965.8 |
| missing_yellow | 172.8 | -569.6 | -854.3 |
| missing_yellow | 168.4 | 934.7 | -217.7 |
| missing_yellow | 168.2 | -1063.4 | -1111.3 |
| missing_yellow | 164.8 | -1567.1 | -1091.4 |
| missing_yellow | 159.8 | -198.0 | -112.8 |
| missing_yellow | 158.5 | 1124.4 | -1868.8 |
| missing_yellow | 150.2 | -1075.8 | -899.3 |
| missing_yellow | 142.2 | -820.4 | 970.4 |
| missing_yellow | 141.2 | -1182.0 | 589.3 |
| missing_yellow | 138.8 | 732.1 | 1158.7 |
| missing_yellow | 138.3 | 1159.2 | 54.4 |
| missing_yellow | 137.9 | 587.1 | -1072.1 |
| missing_yellow | 132.5 | 1210.2 | -0.8 |
| missing_yellow | 132.0 | -1944.2 | 440.5 |
| missing_yellow | 130.5 | -373.6 | 601.0 |
| missing_yellow | 130.2 | -457.9 | -636.0 |
| missing_yellow | 129.8 | -1455.2 | 426.7 |
| missing_yellow | 125.0 | 948.9 | -1156.5 |
| missing_yellow | 122.0 | 1388.6 | 338.4 |
| missing_white | 118.9 | 1129.5 | 74.2 |
| missing_yellow | 118.2 | 1892.0 | -192.5 |
| missing_yellow | 118.0 | -1791.8 | 445.9 |
| missing_yellow | 117.8 | -698.2 | 1017.7 |
| missing_yellow | 115.3 | 883.2 | -1213.0 |
| missing_yellow | 114.2 | 304.6 | -1590.4 |
| missing_yellow | 109.5 | 214.0 | -1730.0 |
| missing_yellow | 108.2 | -927.5 | -1235.4 |
| missing_yellow | 107.0 | -307.9 | -44.3 |
| missing_yellow | 107.0 | -1677.7 | 884.9 |
| missing_yellow | 106.0 | -1225.0 | 956.8 |
| missing_yellow | 105.8 | 775.0 | 336.4 |
| missing_yellow | 105.5 | -877.0 | 908.0 |
| missing_yellow | 105.2 | -30.2 | 855.9 |
| missing_yellow | 104.9 | 876.9 | -423.3 |
| missing_yellow | 104.5 | -2154.4 | 335.8 |
| missing_yellow | 102.9 | 629.9 | -1143.3 |
| missing_yellow | 101.0 | -2459.9 | -115.7 |
| missing_yellow | 100.0 | 1384.5 | 227.8 |

## Massnahmen (Stand 2026-10-19)
- Zebra-Scan: `pipeline/markings_ortho25.py` (SWISSIMAGE 0.25 m, `data/raw/ortho_025`, 156 Boxen) + `crossings.scan`: 234 -> ca. 440 Streifen (+211 gemessen, 11 Tag-Streifen ohne Ortho-Beleg versetzt). Stichprobe 30: 25 echt (vor Abstands-/Breitenfilter), danach keine der 5 Fehltreffer mehr.
- Asphalt-Fuss unter gemessenen Streifen (Fahrbahnpolygon war dort zu schmal).
- Audit-Metriken «missing_yellow» sind bei 0.1 m unscharf (warmer Asphalt); massgeblich ist die Sichtkontrolle `preview/markings_zebras.jpg`, `preview/markings_zebra25_check.jpg`.
- Offen: T19-T21 in research/qa_round/tickets.md.

## T19 Zebra-Recall (Agent Z2B, 2026-10-19)
Details und Zahlen: `research/zones/zone2_street.md`. Kurz: Richtung aus der Streifenperiodizität statt Blob-Kovarianz, Abgleich mit allen Achsen im Umkreis, zweites (leichteres) Closing, Mindestflächen/Sättigungsfilter, zweite Meinung per 0.5-m-Streifentest für zerfranste Blobs. Scan-Streifen im Build 211 -> 403 (Testkacheln-Lauf, ganzes Gebiet), Recall gegen 41 durch Ortho bestätigte OSM-Streifen 68 % -> 93 %, Precision der Messung geschätzt ca. 80-90 % (Sichtprobe). Regler: `markings_ortho25.STRIPE_MIN` (-0.1), `AREA_MIN/EXTD_MIN/FILL_MAX/MYB_MAX`, `crossings.SCAN_REACH/SCAN_COS`.
