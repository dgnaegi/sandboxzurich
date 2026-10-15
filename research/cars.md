# Auto-Modelle (Low-Poly GLB)

Eigene Erzeugung per Blender-Skript (`pipeline/cars/`, Build: `pipeline/cars/build_cars.sh`, Log `logs/cars.log`). Lizenz: WTFPL. Keine Fremdmodelle, keine Logos/Markennamen. Angelehnt an Fahrzeugklassen (Golf-, Octavia-Kombi-, Fiat-500-, Model-3-, Tiguan-, Transporter-, 911-Art), Masse (Karosserie ohne Spiegel) aus Herstellerdaten gerundet.

Format: 1 Mesh / 1 Primitive / 1 Material (MeshStandard), `COLOR_0` (Vertex Colors, Lack = weiss), `_PAINT` (1 = Lack, pro Instanz einfaerben; 0 = Glas, Reifen, Felgen, Lichter, Kunststoff, Kennzeichen). Meter, Ursprung Mitte am Boden, Front -Z, Y oben. Schweizer Kennzeichen ohne Text.

| Datei | Tris | KB | L x B x H (m) |
|---|---|---|---|
| hatch.glb | 2236 | 91 | 4.28 x 1.79 x 1.46 |
| wagon.glb | 2364 | 96 | 4.69 x 1.82 x 1.47 |
| small.glb | 2166 | 87 | 3.57 x 1.63 x 1.49 |
| sedan.glb | 2402 | 96 | 4.69 x 1.85 x 1.44 |
| suv.glb | 2246 | 94 | 4.51 x 1.84 x 1.67 |
| van.glb | 2382 | 97 | 4.90 x 1.90 x 1.97 |
| sport.glb | 2258 | 89 | 4.52 x 1.85 x 1.30 |

manifest.json (length = Bounding-Box inkl. Kennzeichen/Lichter, ca. +0.1 m).
Vorschau: `preview/cars_sheet.jpg` (7 Typen + Heckansicht Hatch; Lackfarben nur im Render simuliert).
