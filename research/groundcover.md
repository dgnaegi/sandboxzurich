# Amtlicher Boden (pipeline/groundcover.py)

Quelle: Kanton ZH OGD-WFS `ogd-0401_arv_basis_avzh_bodenbedeckung_f` (Amtliche Vermessung AV93, LV95, lückenlos).
**Nicht** `bodenbedeckung_a` aus stadtzh_all: das ist das historische 3D-Stadtmodell (Jahr 200-1800), unbrauchbar.
Download in 1-km-Kacheln nach `data/raw/groundcover/bb_*.geojson` (einmalig, ~30 s), Cache `data/build/groundcover_<bbox>.pkl`.

## Klassen (Attribut `artzh`)
| Klasse | artzh |
|---|---|
| carriageway | Strasse, Weg; Parkplatz |
| sidewalk | Trottoir; Verkehrsinsel befestigt |
| plaza | Veloweg, Fussweg; Sportanlage befestigt |
| gravel | Hausumschwung befestigt; übrige befestigte Fläche (Fallback) |
| green | humusiert (Hausumschwung/Verkehrsinsel), Parkanlage, Acker/Wiese, Gartenanlage |
| water | Wasserbecken, Fliessgewässer, Stehendes Gewässer |
| rail | Bahngebiet |
| building | Gebäude* |
Extras: `cobble_road` = Fahrbahn innerhalb 5 m um vas_basis-Achsen, deren Belag (vas_e_strassenbelag, per lokalisationsname + Messwert-Überlappung) Pflästerung/Chaussierung ist (nur ~6000 m2 im Gebiet, Belag nur auf städt. Strassen). `curbs` = Liste {geom, code} aus view_randabschluss_konzept; code 15/25 (Bedeutung ungeklärt, vermutlich Randstein-Typ/Höhe; 1437x 25, 278x 15). Strassenbelag hat keine eigene Geometrie.

## Vergleich Testgebiet (x 600..1200, y -1000..-400), m2
OSM-Fahrbahn 63684 vs amtlich 52941 (OSM 27% zu breit, IoU 0.67); OSM-Trottoir (6 m-Puffer) 96475 vs amtlich Trottoir 46395.
Wichtig: Trottoir ist in der AV in der dichten Innenstadt nur teils erfasst (viele Strassen sind «Strasse, Weg» inkl. Gehweg), 74% des AV-Trottoirs liegt im OSM-Puffer. Plot: preview/groundcover_compare.png.
Gesamtgebiet: ~30 s (Fetch+Union), mit Cache <2 s. Abdeckung 100% (lückenlos).
