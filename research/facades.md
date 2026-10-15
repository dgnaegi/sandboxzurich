# Fassaden-Texturebenen (pipeline/gen_facades.py)

Lizenz: eigene prozedurale Erzeugung (numpy/PIL), keine fremden Bilder. Ausgabe `web/public/tex/facades/<name>_{albedo,mask,normal,rough}.png` (1024², Normal OpenGL +Y), `layers.json`, Vorschau `preview/facades_sheet.jpg`. Reproduzierbar (feste Seeds): `.venv/bin/python pipeline/gen_facades.py [name ...]`.

Fassaden: 12 m x 12.8 m (4 Achsen x 4 Geschosse), kachelbar in x und y. Läden: 12 m x 4 m, auf quadratisch gestreckt, nur in x kachelbar. Mask 255 = Putz (Albedo enthält die Putzfarbe, Spiel tönt per Haus).

| Name | Typ / Epoche | Kurzbeschrieb |
|---|---|---|
| gruender_a | facade 1870-1914 | ockerfarbener Putz, Faschen, grüne Klappläden, Gurtgesimse, Balkone mit Gittern, Blumenkästen |
| gruender_b | facade 1870-1914 | graugrün, graue Läden, Segmentbogenfenster, Dreiecks-Verdachungen, durchgehender Balkon |
| gruender_c | facade 1870-1914 | rosa Putz, Storen/Vorhänge, Eckbalkone |
| jugend_a | facade 1900-1914 | Rundbogenfenster, Ornamentband (Wellenranke) zwischen den Geschossen, Balkone grün |
| jugend_b | facade 1900-1914 | mintgrün, Zwillingsfenster, Ornamentband, rotbraune Läden |
| genoss_a/b/c | facade 1920-1939 | schlicht, Sprossenfenster, Klappläden (grün/rot/blau), kleine Balkone |
| block50_a/b | facade 1950-1969 | Putzbau, Betonbalkonbrüstungen bzw. rote Brüstungsbänder |
| block60_a | facade 1960-1975 | Bandfenster, Brüstungsband, Pfeiler |
| waschbeton_a/b | facade 1970-1985 | Kieselstruktur (Waschbeton), Alu-Fenster bronze, Betonbalkone / Bandfenster |
| neubau_a | facade 2005- | weisser Putz, bodentiefe Fenster, Glasbalkone |
| neubau_b | facade 2005- | Faserzement-Platten, versetzte Fenster |
| neubau_c | facade 2005- | Putz + Holzlamellen im Schachbrett |
| gewerbe_a | facade 1900-1960 | Backstein, Stahlsprossenfenster, Rolltore |
| gewerbe_b | facade 1880-1930 | gelber Backstein, Rundbogen-Stahlfenster, Tore |
| gewerbe_c | facade 1950-1990 | Wellblech/Hallenwand, Bandfenster, Rolltore |
| buero_a | facade 1990- | Glas-Rasterfassade, Spiegelung mit Skyline |
| buero_b | facade 1960-1985 | Betonfertigteil mit Bandfenstern, Pfeiler |
| buero_c | facade 2000- | bronzefarbenes Glas, vertikale Lamellen, Sonnenschutz |
| shop_cafe / kiosk / bar / kebab / coiffeur / velo / leer / baeckerei | shop | Schildband ohne Text (Farbe/Beleuchtung je Typ), Schaufenster mit Innenleben, Markise, Rollladen mit Tags, Plakate (leer) |
| dach_ziegel | roof | Biberschwanz-/Ziegeldach mit Moos und Verschmutzung |
| dach_kies | roof | Flachdach Kies mit Bitumenbahnen und Moos |
| brandmauer | wall | fensterlos, verwittert, zugemauerte Fenster, Maueranker, Risse |

Bekannte Grenzen: Sockel fehlt in den Fassaden (vertikal kachelbar, Sockel muss die Geometrie liefern); Gewerbe-Tore schweben 0.3 m über der Kachelkante.

## Einbindung ins Spiel (2026-10-14)
- `gen_textures.py`: Ebenen 0-21 Fassaden, 22-29 Läden, 30 brandmauer (noch ungenutzt), dann roof_tiles (dach_ziegel), dach_kies (Flachdächer in facade.py), roof_flat/asphalt/sidewalk/grass/cobble/tram_bed/white unverändert. 512² (40 Ebenen). Ausgabe `atlas.webp` (1.4 MB), `atlas_mask.png`, neu `atlas_n.webp` (1.5 MB; R,G = Normal xy, B = Roughness, nur Ebenen 0-30), `layers.json` mit `facades`, `shops_end`, `normals`.
- `styles.py`: gewichtete Stilwahl (Gründerzeit 46 %, Genossenschaft 14, 50/60er 11, Jugendstil 10, Neubau 7, Gewerbe 5, 70er 5, Büro 2); >24 m Block/Büro/Neubau, >40 m Büro, <9 m Gewerbe/Genossenschaft.
- `materials.ts`: Normal Map im Lambert-Shader (Tangente = Up x Wandnormale, nur vertikale Flächen mit Normal-Ebene), Nacht-Schwellen aus layers.json. Roughness ungenutzt (bleibt Lambert).
- Speicher GPU: Albedo 40x1 MB + Normal 31x1 MB (RGBA8) + Mips (x1.33) ca. 95 MB. 1024²-Variante für PC nicht gebaut (+380 MB, würde Budget belasten).
- Offen: Brandmauer an fensterlosen Seitenwänden; Nachtfenster wirken dunkler als vorher (v2-Albedo hat weniger reine Dunkelflächen, Schwellen in NIGHT nachjustieren).
