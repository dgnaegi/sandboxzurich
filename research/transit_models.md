# VBZ-Fahrzeugmodelle

Erzeugt per `pipeline/transit_models/build_models.py` (`blender -b -P`), Ausgabe `web/public/models/transit/*.glb` + `manifest.json`.
Vorschau: `render_sheet.py` (Blender, aus den GLBs), `sheet.py`, `compare.py` -> `preview/transit_sheet.jpg`, `preview/transit_compare.jpg`.
Referenzen: `data/raw/photos/transit/` (Cobra 3002 Letzistrasse, Flexity Tram 16, Neoplan 560). Nur Proportionen/Farben abgelesen, nichts abgepaust.
Module: Vertex Colors (COLOR_0, linear), Material `body` + (nur Kopfmodule) `display` auf Node `display`, UV 0..1. 168-498 Dreiecke pro Modul.
Ursprung Modulmitte, y=0 Schienenoberkante, Front -Z, Meter. Laengen/Abstaende siehe manifest.json.
Offen: Tram 2000 nicht modelliert (Linie 8: Cobra + Flexity); Fenster dunkler als Vorbild, Front kantiger.
