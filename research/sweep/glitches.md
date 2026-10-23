# Glitch-Sweep (Build 20, 88 Blickpunkte x 4 Richtungen, 13:00, ohne Post)

Kontaktbogen: `preview/sweep_00..81.jpg` (Zeilenlabel `#n` = Punktindex). Ursachen sind Vermutungen. Coords = lokale Meter (x Ost, y Nord). «bridge2 läuft» wo zutreffend.

| # | Sev | Klasse | x,y | Beschreibung | Ursache (Vermutung) |
|--|--|--|--|--|--|
| 1 | 3 | slab_on_road | 376,-480 | Brauerstrasse West: wide grey concrete ramp/trough slabs with sloped side walls lying in the open area next to carriageway, look like loose slabs [sweep_36 (#37)] | ramp/Unterfuehrung geometry from bridges.py (guess) check with Langstrassen-Unterfuehrung ramp |
| 2 | 3 | slab_on_road | 186,-666 | Seebahnstrasse: tilted grey slab/wall runs diagonally across bike lane and median, wall top at kerb height [sweep_36 (#38)] | railway cutting wall/embankment mesh (guess)  |
| 3 | 3 | bridge_deck_low | 498,834 | Hardbruecke Nord: deck underside very low over pavement, construction hoarding walls around pillars, large grey slabs hanging [sweep_54 (#56)] | bridge2 laeuft also 515,863 |
| 4 | 2 | facade_texture | -177,705 | Westpark office landmark z5R2_westpark_office: facade pale blue-grey with irregular light patches, no windows over a whole wall [sweep_81 (#86)] | landmark texture/UV in z5R2_houses.py (guess)  |
| 5 | 2 | floating_bar | -1972,925 | Vulkanplatz: thin white plank/ramp slanted at ~1 m height without support, near tree pit [sweep_54 (#54), sweep_81 (#85)] | furniture or kerb/ramp prop (guess) dir 90..270 deg from -1960,934 |
| 6 | 2 | facade_texture | -206,-287 | Hardstrasse: yellow house with red wedge-shaped shutters/panels cut at odd angles (UV or polygon error) [sweep_63..81 (#71)] | facade shutter decals (guess)  |
| 7 | 2 | door_tilt | 1208,-78 | Limmatstrasse N: brown door quad stands tilted/sticks out from facade; other door and window frames skewed [sweep_69 (#70)] | facade door placement on non-axis-aligned wall (guess)  |
| 8 | 2 | hedge_on_pavement | 86,-502 | Seebahnstrasse: huge hedge blobs on the pavement, player can stand inside; hedge arch with hole [sweep_69 (#73)] | hedge props with wrong scale (guess) also -460,-662 Albisriederplatz (#82) |
| 9 | 2 | facade_texture | -828,-178 | Brick wall facade strongly stretched/blurred, giant green shutters, UV scale wrong [sweep_57 (#61)] | facade UV on long wall (guess) also -1097,117 (#62) metal wall |
| 10 | 2 | floating_bar | -1097,117 | Thin white horizontal bar floating in front of grey wall at head height / above [sweep_57 (#62)] | unknown sign or banner mesh (guess)  |
| 11 | 2 | loading_void | -108,-195 | Hardplatz spawn: first frames show white featureless ground and sky (tiles not loaded yet); fine after ~3 s. Also white band at Albisriederplatz (#17) [sweep_12 (#16)] | tile streaming at spawn, no ground placeholder (guess) not reproducible after load |
| 12 | 1 | ground_decal | -288,-766 | Small black flat quads scattered on carriageway (Badenerstr/Zypressenstr, Hardstr/Bullingerstr, Gertrudstr, Baslerstr). Look like loose black tiles [sweep_30 (#34,#35)] | manhole/drain decals oversized or untextured (guess) very common, citywide |
| 13 | 1 | slab_ground | -125,-1117 | Idaplatz (-125,-1117): thick white wedge bands standing on plaza like raised kerb ridges; [sweep_00 (#3)] | kerb/marking mesh with height (guess)  |
| 14 | 1 | ground_texture | -4,633 | Turbinenplatz: pale triangular patch on ground next to bed, looks like floating wedge [sweep_06 (#7)] | ground decal or shadow quad (guess)  |
| 15 | 1 | canopy | 1130,60 | Limmatplatz canopy: huge pale disk roof with oval sky hole, looks like a UFO from below [sweep_12 (#15), sweep_81 (#84)] | canopy mesh simplification (guess)  |
| 16 | 1 | vehicle_detail | -405,-939 | Bus articulation joint rendered as black box [sweep_42 (#45)] | bus model (guess)  |
| 17 | 1 | texture_bright | 203,135 | Freitag-Turm plaza: snow-white terrazzo patches very bright vs surroundings [sweep_18 (#21)] | ground material tint (guess)  |
| 18 | 1 | sign_big | 1735,-700 | HB Bahnhofplatz: shop sign (Sora Sushi) huge and low, player walks through it [sweep_18 (#22)] | sign scale/placement (guess)  |
| 19 | 1 | blocked_by_hoarding | -191,-1516 | Goldbrunnenplatz: white Baustelle hoardings fully block spawn view; intended? also 498,834 [sweep_42 (#44)] | construction hoarding props  |
| 20 | 1 | inside_vehicle | 32,111 | Spawn Hardbruecke station platform: camera glued to S-Bahn body (dir 0 fills screen) [sweep_24 (#26)] | spawn point too close to rail vehicle (guess)  |
| 21 | 1 | code_error | -,- | pageerror: CanvasRenderingContext2D.arc radius negative (-1.2) repeatedly at 400x225 viewport [run log] | hud/map radar draw with tiny viewport (guess) check web/src/ui/map*.ts |

Hinweis: Hardplatz/Albisriederplatz weiss ist nur Lade-Artefakt (Nachaufnahme sauber). Rampen/Decks Hardbruecke Nord und Kalkbreite (355,-1094) waren in Sichtweite ohne eindeutigen Fehler ausser #3. Playwright-Skript: `web/tests/glitch_sweep.mjs`.