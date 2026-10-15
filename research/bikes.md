# Velo-Modelle (Auftrag V)
Eigenbau (WTFPL), Referenzfotos aus `data/raw/photos/bikes/` nur als Proportionsvorlage (nichts als Textur uebernommen).
Referenzen im Vergleich (`preview/bikes_compare.jpg`): 131570544 Cilo Rennrad (road), 73205588 Damenvelo Zuerich (city), 75188048 Carvelo2go Bullitt (cargo), 81907949 PubliBike (rental).

Build: `pipeline/bikes/build_bikes.sh` (reines Python/numpy schreibt die GLBs, Blender nur fuer Renders). Ausgabe `web/public/models/bikes/`.

## Format
- Pro Datei 1 Mesh / 1 Primitive / 1 Material. Attribute: POSITION, NORMAL (int8), TEXCOORD_0 (uint16), COLOR_0 (ubyte, Lack = weiss), `_PAINT` (float, 1 = Rahmenlack/Gabel/Kettenschutz-frei).
- Material: doubleSided, alphaMode MASK, alphaCutoff 0.3, baseColorTexture = gemeinsamer Atlas 512x256 (29 KB, embedded PNG): Speichenrad (Felge+Speichen als Alpha), Kettenblatt, Korbgitter, opaker Block fuer alle uebrige Geometrie (UV konstant).
- Im Spiel: `material.alphaTest=0.3`, Texture sRGB, `side=DoubleSide`; Lack = COLOR_0 * Instanzfarbe wo `_PAINT>0.5` (wie bei den Autos). Optional `alphaToCoverage=true` gegen Flimmern der Speichen in der Ferne.
- Achsen: Meter, Y oben, Front -Z, Antriebsseite +X, Ursprung Boden zwischen den Radaufstandspunkten. `*_lean`: 10 Grad nach links (-X) auf Seitenstaender gekippt, Reifenkontakt bleibt auf y=0.
- Typen: city (Tiefeinsteiger, Korb, Gepaecktraeger, Schutzbleche, Kettenschutz), trekking (+Taschen), road (Rennlenker), mtb (Federgabel, Scheibenbremsen), ebike (Akku Unterrohr, Mittelmotor), cargo (Long John, Holzkiste, 20"/26"), kidseat, rental (kleine Raeder, grosser Korb, ohne Logo). `rack.glb` = Zuercher Anlehnbuegel (verzinkt, 0.6 x 0.8 m, 120 Tris).
- Budget: 1184-1414 Tris, 63-73 KB je Velo (Ziel 1500 / 80 KB). manifest.json: `length` = Ausdehnung in Z.
