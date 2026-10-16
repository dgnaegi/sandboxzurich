# PJZ (Polizei- und Justizzentrum Zuerich) – Recherche

Standort Guterbahnhof-Areal, Hohlstrasse / Duttweilerstrasse; Architektur Theo Hotz Partner; eroeffnet 2022. OSM: relation 11839338 («Polizei- und Justizzentrum», building=government).

## Quellen / Lizenzen
- Footprint: swissBUILDINGS3D im Spiel (ID_FEBC2FA3, 14'585 m2). Die Dachhoehen dort (9-13 m, Sheddaecher) stammen aus der Bauphase und sind zu niedrig; Hoehen aus Fotos geschaetzt (6 Geschosse Ost, Gefaengnistrakt West gleich hoch).
- Referenzfotos: `data/raw/photos/pjz/` (meta.json mit Lizenz/Autor/URL). 10 Wikimedia Commons (CC BY-SA 3.0/4.0; Beat Jost, Albinfo, Tschubby), 32 Panoramax (Strassenbilder der Umgebung, kaum PJZ-Fassade; CC BY-SA). Kontaktbogen `preview/ref_pjz.jpg`. Nur zur Ansicht, keine Texturen daraus.
- Fassade nach Fotos (Commons c04, c05, c07, c08): hellgruen-graue Steinraster-Fassade, hohe schmale Fenster mit dunklen Metallladen in tiefen Laibungen, Geschossbaender, hoeheres Erdgeschoss, zurueckgesetztes verglastes Foyer mit Vordach (Haupteingang, Schrift ohne Logo), Gefaengnistrakt im Westen dunkel/geschlossen (c00, c01, c07), Glasdach ueber dem Innenhof.

## Modell
`pipeline/landmarks/pjz_v2.py` -> `web/public/models/landmarks/pjz_v2.glb` (14.8k Tris, 260 kB, prozedurale Texturen), Override `pipeline/overrides/landmarks_pjz.json` (hide = Footprint-Punkte von ID_FEBC2FA3). merge.py noch nicht gelaufen. Vergleich `preview/pjz_cmp.jpg`.

## Offen
- Hoehen/Raster unverifiziert (keine Plaene); Eingangsposition (Sued, Mitte der laengsten Ostfront-Kante) geschaetzt.
- Alte Ersatz-Frage: es gab kein altes PJZ-Landmark (nur die gewoehnliche Gebaeudehuelle), also nichts zu entfernen.
