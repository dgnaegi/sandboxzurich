# Innenhöfe, Vorgärten, Vegetation (pipeline/yards.py, web/src/world/yards.ts)

Quellen (alle offen): swissSURFACE3D minus swissALTI3D (nDSM, 1 m, `data/build/ndsm`), SWISSIMAGE (ExG-Grünwert, `data/raw/ortho_wms`),
Stadt Zürich Grünflächen (Pflegeeinheiten «Strauchbepflanzung», «Formhecke», `stadtzh_all/geo_gruenflaechen`), AV Bodenbedeckung (Rasen vs. befestigt),
OSM (Hecken/Zäune zur Dublettenvermeidung, Spielplätze).

## Was passiert
- **Hofbäume:** nDSM-Kronenmaxima (>3.5 m, grün, ausserhalb Gebäude+1.2 m), nicht innerhalb 0.45 Kronenradius eines Baums aus Baumkataster/OSM -> `C["trees"]` (Quelle `ndsm`), normale Baumpipeline.
- **Sträucher/Hecken:** Zellen 0.8–3.2 m, grün, nicht Baumkrone/Gebäude/Strasse/Park, plus Grünflächen-Pflegeeinheiten (Strauch 0.9 m, Hecke 1.2 m). Langgestreckte Blobs (Länge/Breite >= 2.5) werden Heckenboxen, der Rest Strauchkugeln (instanziert). OSM-Hecken (1.3 m Puffer) ausgespart.
- **Vorgarten:** Grenze Trottoir/Hof näher als 12 m an einem Gebäude: ~60 % der 8-m-Stücke als Mäuerchen (0.45 m), Metallzaun (1 m) oder niedrige Hecke, Lücken für Eingänge, ohne Kollision (niedrig/durchlässig).
- **Hofinventar** (deterministisch gehasht, Höfe >= 120 m², >7 m von Strassen): Velounterstand (1.8–3.8 m vor der Wand, Befestigt, nicht bei bestehenden Velos), Wäschespinne (Rasen), Sandkasten (Rasenhof > 380 m², >35 m von OSM-Spielplätzen), Gartentisch+Hocker(+Sonnenschirm), Kiesstreifen an Hauswänden.
- **Handy-LOD:** halbe Sträucher/Hecken, kein Kies, keine Tische, einfachere Velounterstände; 7 Draw Calls pro Kachel maximal.

## Nicht umgesetzt (Daten fehlen / Zeit)
- Fassadenbegrünung und Balkonpflanzen: im Gebiet keine Datenquelle (Stadt-ZH-OGD enthält keinen Fassadenbegrünungs-Layer; `details_facade.py` liefert keine Balkone).
- Familiengärten: nur 2 OSM-landuse=allotments im Spielgebiet (bei (-731,-99) und (-339,-1017)): Gartenhaus + Beetreihen dort; der OGD-Layer ist ein Punktlayer ohne Geometrie.
- Herbstlaub am Boden: macht `details_leaves.py` (Details-Agent).
