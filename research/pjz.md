# PJZ (Polizei- und Justizzentrum Zuerich) – Recherche

Standort Guterbahnhof-Areal, Hohlstrasse / Duttweilerstrasse; Architektur Theo Hotz Partner; eroeffnet 2022. OSM: relation 11839338 («Polizei- und Justizzentrum», building=government).

## Quellen / Lizenzen
- Footprint: swissBUILDINGS3D ID_3D89E8BB (Guterstrasse 33, 16'700 m2; frueher falsch ID_FEBC2FA3 = Neugasse 145, DECISIONS #63). Dachhoehen aus den 3D-Daten: 24 m Hauptring (passt zu 6 Geschossen nach Fotos), 31 m hoeherer Mittelblock, nur 2 m im NW-Quadrat (Bauzustand, dort steht der dunkle Gefaengnisblock).
- Referenzfotos: `data/raw/photos/pjz/` (meta.json mit Lizenz/Autor/URL). 10 Wikimedia Commons (CC BY-SA 3.0/4.0; Beat Jost, Albinfo, Tschubby), 32 Panoramax (Strassenbilder der Umgebung, kaum PJZ-Fassade; CC BY-SA). Kontaktbogen `preview/ref_pjz.jpg`. Nur zur Ansicht, keine Texturen daraus.
- Fassade nach Fotos (Commons c04, c05, c07, c08): hellgruen-graue Steinraster-Fassade, hohe schmale Fenster mit dunklen Metallladen in tiefen Laibungen, Geschossbaender, hoeheres Erdgeschoss, zurueckgesetztes verglastes Foyer mit Vordach (Haupteingang, Schrift ohne Logo), Gefaengnistrakt im Westen dunkel/geschlossen (c00, c01, c07), Glasdach ueber dem Innenhof.

## Modell (Stand 2026-10-20, nach Neueinpassung)
`pipeline/landmarks/pjz_v2.py` -> `web/public/models/landmarks/pjz_v2.glb` (25k Tris, 355 kB). Aufteilung nach den 3D-Dachhoehen statt nach x: NW-Quadrat (Dach < 6 m, ca. 3270 m2, mit Innenhof) = dunkler, geschlossener Gefaengnisblock (H 21 m, Wellblech-Optik, Schlitzfenster); Mittelblock mit Dach > 28 m = 31 m hoch; Rest = Hauptring 23.1 m (Steinraster, hohe schmale Fenster, Geschossbaender). Laengster Innenhof (1030 m2) mit Glasdach. Eingang/Foyer: Mitte der langen SW-Kante (Strassenseite, Gueterstrasse), Vordach + Schriftzug. Fassadenfarbe kuehler (#a9b4ab) und Fenster dunkler (Metallladen) als vorher. Die frueheren Zierbaeume (Kegelkronen sahen aus wie schwebende Eimer) entfernt, die Strassenbaum-Ebene pflanzt sie.
Ansichten: `preview/z5c_pjz_a.jpg` (Luft), `z5c_pjz_b.jpg`, `z5c_pjz_c.jpg` (Strasse), `z5c_pjz_d.jpg` (nachher, kuehle Farben).

## Offen
- Hoehen/Raster nur aus Fotos + 3D-Daten, keine Plaene. Welcher Teil genau der Gefaengnisblock ist, folgt aus der Lage (NW-Ende, Foto c02/c03/c07: dunkler Block am Ende des hellen Baus).
- Mittelblock 31 m: nicht fotografisch belegt (nur 3D-Daten).
- Im Spiel steht eine Hochstrasse/Rampe (weisse Platte) direkt SW vor dem Eingang und eine kleine Holzverkleidete Huette in der Fassadenflucht (nicht von diesem Generator).
