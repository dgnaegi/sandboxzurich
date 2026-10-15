# Stadtmobiliar (Auftrag M)
Build: `/opt/homebrew/bin/blender -b -P pipeline/furniture/build.py` -> `web/public/models/furniture/*.glb` + `manifest.json`. Vorschau: `python3 -I pipeline/furniture/render.py` -> `preview/furniture_sheet.jpg`, `preview/furniture_compare.jpg`.
Format: 1 Mesh/1 Primitive/1 Material, COLOR_0 (uint8, sRGB-Bytes), Flat-Normals, Y oben, Front -Z, Ursprung Boden Mitte. Lampenglas exakt 0xfff3c8.

## Referenz-Befunde (70 Commons-Fotos, ~50 Brunnen; keine Fotos von Kuebeln, Seilleuchten, Masten, Pollern)
- Brunnen: Steintrog mit Stock (Obelisk/Saeule) hinten, Rohr zeigt zum Trog; runde/achteckige Steinschale auf Stiel; kleine Trinkbrunnen (Stein/Beton mit Metallrohr).
- Baenke: Holzlatten auf Betonzylindern (Schanzengraben, Seefeldquai), Gusseisen-Seiten mit Holz, graugruene Metallbaenke (Utoquai).
- Hydranten: grau/dunkelgrau, Gusseisen, Oberflur, Kuppel, 2 Seiten- + 1 Frontstutzen.
- Pingpong: Betonplatte auf X-foermigen Betonbalken, niedriges Netz.
- Laternen: schwarze Sechskant-Laternen (Kandelaber/Wandarm).
## Annahmen ohne Foto (bitte pruefen)
bin (anthrazit Metallzylinder, offene Oeffnung), lamp_cable (Leuchtkoerper haengt unter Aufhaengepunkt, y negativ bis -0.66), lamp_mast, bollard, sign_pole.
Sitzbankkataster «046 gebogene Sitzlatten» nur angenaehert (gerade Latten, gekippte Lehne).
