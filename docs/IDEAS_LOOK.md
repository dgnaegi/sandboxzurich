# Ideen: Look und Stimmung (Art-Direction-Review, 2026-10-16)

Basis: Live-Screenshots Tag 12:00 / Abend 18:30 / Nacht 22:30 an Helvetiaplatz, Hohlstrasse (Langstrasse), Röntgenplatz in PC (1000x600) und Handy (390x700): `preview/ideas_look_pc.jpg` (**[PC]**), `preview/ideas_look_phone.jpg` (**[PH]**). Dazu `qa_final_*.jpg` (**[QA]**), `nachtlauf_vorher_nachher.jpg` (**[NL]**), `fidelity*.jpg` (**[FID]**), `lm*_all.jpg` (**[LM]**). Nichts davon wurde umgesetzt; reine Ideensammlung. Aufwand S < 0.5 Tag, M 1–2 Tage, L > 2 Tage. Handy-Kosten: 0 = keine, + gering, ++ spürbar, +++ nur wenn Budget frei.

## Befund in fünf Sätzen
1. Die Technik ist weiter als der Eindruck: Himmel mit Wolken/Sternen, Grading (S-Kurve, Vignette), Fog, Bloom/AO am PC sind da, aber die Bildwirkung am Tag ist **kühl-grau und flach** (Boden blau-grau, kaum Sonnenlicht-Kontrast, [PC] helv_day/lang_day). Zürich wirkt dadurch wie bedeckter Novembermorgen, auch um 12:00.
2. Der Abend ([PC] lang_eve) kippt in **violett-braunen Matsch**: Boden dunkel, Fassaden orange, kein Licht-/Schatten-Gegensatz. Der Himmel ist schön, der Boden gehört nicht zum Himmel.
3. Die Nacht ist nach #37 gut lesbar ([NL]); die stärkste Wirkung kommt von Lichtkegeln und beleuchteten Fenstern. Es fehlt Nässe/Spiegelung und farbiges Leuchtreklame-Licht.
4. Es gibt viele realistische Details (Strassenmarkierungen, Schilder, Fassaden), aber **keine einheitliche Farbregie**: Wiese (sattes Grün [QA] viadukt) kollidiert mit gedämpftem Beton; Bäume gelb-grün-Herbst sind das einzige Warm.
5. Fernsicht ist der billigste Hebel: Uetliberg/Hochhäuser/Dunst-Schichten sind am Horizont kaum präsent (nur Fog-Verlauf), obwohl Silhouetten Zürich am schnellsten erkennbar machen.

## Entscheid zur Grundrichtung (stilisiert-realistisch)
Echte Geometrie behalten, **Farbe und Licht stilisieren**: leicht übersättigte, warme Hauptfarben mit klar blauen Schatten (Lieblingsrezept von Sable, Townscaper, Mini Motorways: wenige Farbtöne, weiche Verläufe, Fog als Gestaltungsmittel). Auf dem Handy trägt das besser als Details: kleine Pixel, direkte Sonne, kurze Sichtweite → Farbkontrast und Silhouetten schlagen Texturdetail. Kein Fotorealismus-Wettlauf mit GTA V (Vision: Nicht-Ziel). Referenzen und was wir daraus ziehen:
- **Townscaper / Mini Motorways:** begrenzte Palette, weicher Schatten, Wasser/Himmel als Farbfläche, Tilt-Shift-Gefühl.
- **Sable:** Konturen, Gradient-Himmel, sehr warmes Mittagslicht, klare Silhouetten am Horizont, Dunst in 3 Schichten.
- **GTA V:** Tageszeit-Farbkurven (Golden Hour!), Nässe nach Regen, Neon-Bloom, Staub-Lichtstrahlen; Lehre: Atmosphäre schlägt Polygonzahl.
- **three.js-Showcases (z. B. Bruno Simons Folio, Codrops-Demos, "Lusion"-Stil):** Post-Stack aus Bloom, Vignette, Filmkorn, sanfte Tiefenunschärfe; alles in einem Pass.

## Top 10 (Wirkung/Aufwand)
| Rang | # | Idee | Wirkung | Aufwand | Handy |
|---|---|---|---|---|---|
| 1 | 1 | Farbregie Tag: wärmere Sonne, blauere Schatten, Boden-Tint weg von Blaugrau | sehr hoch | S | 0 |
| 2 | 2 | Abend/Golden Hour retten: Boden-Gradient, Rimlight, Fassaden-Glow | sehr hoch | S | 0 |
| 3 | 7 | Horizont-Silhouetten: Uetliberg, Üetliberg-Turm, Prime Tower, Dunst-Schichten | hoch | S–M | + |
| 4 | 5 | Nass-Look nach Regen: dunklerer Asphalt, Spec-Boost, Pfützen-Decals | sehr hoch | M | + |
| 5 | 9 | Himmel/Nebel pro Wetter (Morgennebel, Hochnebel, Föhn) als Daytime-Presets | sehr hoch | M | + |
| 6 | 12 | Neon-/Leuchtreklame-Pass Nacht (farbiger Glow, Flackern) | hoch | S–M | + |
| 7 | 4 | Weiche Blobschatten-Fake am Handy (Bäume, Personen, Fahrzeuge) + Baum-AO an Fassadenfuss | hoch | S | + |
| 8 | 15 | Atmosphäre-Partikel (Laub, Staub im Licht, Dampf Gullideckel) | mittel-hoch | S | + |
| 9 | 21 | HUD/Ladebildschirm im AL-Look (Plakat-Typografie, Magenta) | mittel-hoch | S | 0 |
| 10 | 17 | Sanfte Tilt-Shift-/DoF-Andeutung nur am PC; Filmkorn leicht | mittel | S | 0 |

## Ideenkatalog

### A. Gesamtlook und Farbe
**1. Farbregie Tag (Warm-Kalt-Kontrast).** [PC] helv_day, lang_day: Boden und Schatten blau-grau, Sonne wirkt nicht. Sonnenfarbe und `hg`/`hs` im Mittag in `daytime.ts` wärmen (Sonne +Gelb, Himmelslicht kräftiger blau), Strassen-/Gehwegfarbe 5–8 % wärmer (Sandstein-Grau statt Stahl-Blau), Highlight-Tint im Grading leicht gold. Wirkung sehr hoch, S, Handy 0. Dateien: `engine/daytime.ts`, `engine/grading.ts`, ggf. Tile-Material-Tint.

**2. Abend/Golden Hour.** [PC] lang_eve: Boden violett-braun, Himmel strahlt. Bodenfarbe im Abend heller/wärmer (Streiflicht-Bounce `hg` orange), Fassaden mit Himmels-Rim an Oberkante, Schatten lang und blau statt braun. Eine zusätzliche "Golden Hour" Stützstelle (17:30–18:30) in `daytime.ts`. Wirkung sehr hoch, S, Handy 0.

**3. Zürich-Palette festlegen.** Dokumentierte 12 Farben: Putz-Ocker, Backstein-Rot (Hohlstrasse), Beton-Warmgrau, Sihl-Grün, Tram-Blau, Tram-Weiss, VBZ-Blau, Magenta (AL), Zürisee-Blau, Herbstlaub-Gelb, Dach-Rotbraun, Asphalt-Anthrazit. Als `palette.ts`/JSON für Fassaden-Tint, Props, UI. Verhindert Drift (Wiese zu sattgrün, Beton zu blau). Wirkung mittel-hoch (langfristig), M, Handy 0. Dateien: `world/tint.ts`, `engine/materials.ts`, neues `engine/palette.ts`.

**4. Billige weiche Schatten am Handy.** Am Handy gibt es laut `quality.ts` evtl. keine Echtzeitschatten; Figuren/Bäume/Autos "schweben" ([PH] helv_day). Blob-Shadow-Decal (dunkle weiche Ellipse) für Spieler, NPCs, Autos, Baumstämme, instanziert, Alpha nach Sonnenstand verschoben. Wirkung hoch (Erdung), S, Handy + (1 Instanz-Mesh). Dateien: neues `world/blobshadows.ts`, `player/player.ts`.

**5. Nass-Look/Regen.** Schalter `weather=rain`: Asphalt/Trottoir 25 % dunkler, Roughness runter (PC: Reflexion via vorhandener PMREM, Handy: Fake-Reflexion mit Himmelsfarben wie bei Autos), Pfützen als halbtransparente Decals mit Fresnel-Spiegelung auf Tramschienen/Platz-Senken, Regenstreifen als 1 Instanz-Layer um die Kamera. Nachts ergibt das die Blade-Runner/GTA-Wirkung (Lampenkegel am Boden). Wirkung sehr hoch, M, Handy +. Dateien: `engine/daytime.ts` (Wetter-Achse), `engine/materials.ts`, `world/decals.ts`, neues `engine/weather.ts`.

**6. Erster Schnee / Raureif.** Boden- und Dach-Tint zu Weiss-Blau per Shader-Mix (`worldUp.y`-Schwelle, Normal nach oben), Bäume mit weniger Blattalpha. Kein neues Asset. Wirkung hoch (Saison-Überraschung), M, Handy +. Dateien: `engine/materials.ts`, `world/tree_*`.

### B. Himmel, Wetter, Silhouetten
**7. Horizont-Silhouetten.** [QA] altstetten, [PC] zeigt kaum Ferne. Uetliberg-Kamm (aus DEM, schon Höhendaten) als dunkelblauer Billboard-/Low-Poly-Streifen in 3 Dunstschichten (Atmosphärische Perspektive: ferner = heller und blauer), plus Prime Tower/Hochhäuser/Üetliberg-Turm als Silhouetten-Impostors jenseits des Spielgebiets. Wirkung hoch, S–M, Handy +. Dateien: neues `world/skyline.ts`, `engine/sky.ts`, `engine/renderer.ts` (Fog).

**8. Höhennebel und Gradient-Fog.** Fog nur linear ([renderer.ts](web/src/engine/renderer.ts)). Höhenabhängiger Nebel (dichter in Bodennähe, Sihl/Limmat Morgennebel) als Shader-Chunk im Welt-Material. Wirkung hoch, M, Handy + (ein paar ALU). Dateien: `engine/materials.ts`, `engine/daytime.ts`.

**9. Wetter-Presets.** Daytime-Keys um Wetter-Achse erweitern: *Morgennebel* (Fog 20–150 m, Sonne schwach, warm), *Hochnebel* (typisch Zürich im Nov, geschlossene Decke, kein Schatten, weiche Kontraste, Himmel grauweiss), *Föhn-Klarsicht* (Fog 900 m, Alpenkette als Silhouette ganz hinten, kräftige Farbe, leicht überhöhter Kontrast), *Gewitter-Himmel* (dunkle Wolkenbasis). Wetterwahl im Menü neben der Uhr (`ui/clock.ts`, `ui/settings.ts`). Wirkung sehr hoch, M, Handy +. Dateien: `engine/daytime.ts`, `engine/sky.ts`, `ui/settings.ts`.

**10. Wolkenschatten.** Grosse langsame Schattenflecken auf Boden/Fassaden (Noise-Textur im Welt-Material, World-XZ + Zeit): macht Tag lebendig, ohne Schatten-Rendering. Wirkung mittel-hoch, S, Handy + . Dateien: `engine/materials.ts`.

**11. Sonnenstrahlen/Godrays billig.** Additive Billboard-Strahlen oder radiales Blur nur am PC bei tiefer Sonne, Handy nur Sonnen-Glow im Himmel. Wirkung mittel, M, Handy 0 (aus). Dateien: `engine/post.ts`.

### C. Nacht
**12. Leuchtreklame-Pass.** [PC] lang_night: Läden leuchten warmweiss. Echte Langstrasse ist farbig (Magenta, Rot, Grün, Blau): emissive Neon-Texturen/Streifen je Ladentyp, leichtes Flackern/Buzz per Zeit-Uniform, Bloom nimmt sie mit (PC) und eine Pseudo-Halo-Sprite-Variante am Handy. Wirkung hoch, S–M, Handy +. Dateien: `world/storefront_sign.ts`, `world/night_lights.ts`.

**13. Fensterlicht variieren.** [PH] helv_night: Fenster sind schön, aber gleichmässig. Pro Fenster Zufallsfarbe (warmweiss, kalt TV-blau, gelb), 15 % aus, nach 1 Uhr weniger Fenster. Billig im Fassaden-Shader. Wirkung mittel-hoch, S, Handy 0. Dateien: `engine/materials.ts`, Atlas-Shader.

**14. Lichtkegel und Streulicht.** Volumetrisch gefälschter Laternenkegel (additiver Kegelmesh, instanziert) plus Dunst/Halo an Strassenlaternen, bei Regen/Nebel stärker. Wirkung hoch bei Nebel, M, Handy ++ (Overdraw; nur nahe Lampen, max 8). Dateien: `world/night_lights.ts`, `world/streetlife.ts`.

### D. Atmosphäre und Leben
**15. Partikel-Layer.** Herbstlaub fällt von Bäumen (Kamera-nah, 150 Instanzen), Staub im Gegenlicht, Dampf aus Gullideckeln/Kebab-Grill, Tauben-Schwarm am Platz. Ein Instanzmesh + Vertex-Shader-Animation, keine CPU. Wirkung mittel-hoch, S, Handy + . Dateien: neues `world/particles.ts`, `world/tree_field.ts`.

**16. Vögel und Himmelsleben.** Dohlen/Mauersegler-Schwärme (Boid-ähnlich im Shader), Flugzeug-Kondensstreifen, S-Bahn-Pfeif-Ton wirkt da gleich mit. Wirkung mittel, S–M, Handy +. Dateien: `engine/sky.ts`, `world/particles.ts`.

**17. Filmkorn + Tilt-Shift-Andeutung.** Sehr leichtes Korn (animiert 12 fps) und Vignetten-Vertiefung bei Schnellfahrt (Geschwindigkeits-Gefühl); PC optional DoF-light über N8AO-Tiefe. Handy nur Vignette. Wirkung mittel, S, Handy 0. Dateien: `engine/grading.ts`, `engine/post.ts`.

**18. Fahrzeug-Staub/Regen-Gischt.** Räder werfen bei Nässe Wasser auf (kleine Partikelfahne), Trams funken an Oberleitung bei Nacht. Wirkung mittel, S, Handy +. Dateien: `player/crash_fx.ts`, `world/transit.ts`.

### E. Materialien
**19. Glas und Fassadenreflex.** [QA] altstetten: Glasfassaden sind flach-blau. Fake-Reflex per Himmels-Gradient (Fresnel nach Blickwinkel) im Tile-Shader, auch am Handy (kein IBL nötig). Hochhäuser bekommen Spiegelung der Sonne als Streifen. Wirkung hoch, M, Handy +. Dateien: `engine/materials.ts`, `world/tint.ts`.

**20. Boden-Detail: Macro-Variation und Kanten.** [PC] helv_day: Boden hat Textur, aber wirkt an Distanz uniform (Tiling). Grossflächige Farb-Macro-Noise (200 m Wellenlänge), Rinnstein-/Randdunkelung (AO-Linie am Randstein) und Schmutz an Hauswand-Fuss als Vertex-/Textur-Overlay; Pipeline-seitig als Vertexfarbe gebacken. Wirkung hoch, M, Handy 0. Dateien: `pipeline/` (Tile-Bau), `engine/materials.ts`.

**21. Vegetation.** Wiesen ([QA] viadukt, kalkbreite) sind Teppichgrün. Gras-Tint-Varianz (Gelb-Grün-Braun, Trampelpfade), Blumen/Klee-Sprenkel als Decal, Bäume mit Herbst-Gradient (Krone oben gelb, unten grün) und Alpha-Cutout-Rändern; Hecken/Rabatten als Instanzen. Wirkung hoch, M, Handy +. Dateien: `world/lawns.ts`, `world/trees.ts`, `world/tree_impostor.ts`.

**22. Fassaden-Altern.** Wasserlaufspuren unter Fenstern, Russ über Eingängen, Plakat-/Tag-Reste, Farbunterschiede pro Etage (Sockel dunkler). Als zweite Atlas-Schicht (Detailtextur, 1 Tile pro Hausseite). Wirkung hoch, M–L, Handy +. Dateien: `engine/materials.ts`, `world/tint.ts`, Atlas-Pipeline.

### F. UI-Look
**23. HUD im AL-Look.** [QA]: grüne "CHF 312.40", grüne Sterne neutral. Typografie Anton/Barlow ist gut (Plakat-Anmutung); Farbe auf Magenta/Weiss reduzieren, Radar mit dickem schwarzem Rahmen, Ortsname als Plakat-Streifen (leicht schief, Druckschatten). Wirkung mittel-hoch, S, Handy 0. Dateien: `ui/hud.css`.

**24. Menü und Karte.** Menü wie Plakat/Stadtplan-Faltblatt: Papiertextur, Rasterpunkte, Stempel. Karte (Vektor, #28) in Zürcher-Stadtplan-Palette (Cremeweiss, Hellblau Wasser, Grün Parks). Wirkung mittel, S–M, Handy 0. Dateien: `ui/menu.ts`, `ui/map_render.ts`, `ui/hud.css`.

**25. Ladebildschirm.** Bisher bewusst neutral (#25). Vorschlag ohne Text: Tram-Linie, die über die Skyline fährt (SVG-Animation, <5 KB), Fortschritt als Tramfahrt. Kein Spielinhalt, bleibt "Loading". Wirkung mittel, S, Handy 0. Dateien: `ui/loading.ts`, `index.html`.

**26. Orts-Einblendung.** Beim Kreiswechsel kurzer Titel (Kreis 5 / Industriequartier) in Plakat-Typo statt dauernder Anzeige. Wirkung mittel, S, Handy 0. Dateien: `ui/hud.css`, `main.ts`.

### G. Kamera und Post
**27. Kamera-Feeling.** Leichtes FOV-Kick beim Rennen, Kopfbewegung minimal, Kamera-Neigung in Kurven (Fahrzeug), weiche Kollisionsvermeidung an Wänden (Fassade verdeckt aktuell Spieler [QA] lochergut). Wirkung hoch (Spielgefühl), M, Handy 0. Dateien: `player/player.ts`, `player/drive.ts`.

**28. Photo-Mode-Grading.** Taste "P": LUT-Auswahl (Fotofilm, Kodak-warm, Schwarzweiss-Zeitung) → Teilen-Funktion für Social (Zielgruppe Instagram). Wirkung mittel (Viralität), M, Handy 0. Dateien: `engine/grading.ts`, `ui/menu.ts`.

### H. Performance-Tricks für mehr Look pro Budget
**29. Baked AO in Vertexfarben.** Pipeline backt AO (Hauskanten, Gassen, unter Bäumen) in Vertex-Farbe; ersetzt N8AO am Handy fast kostenlos. Wirkung sehr hoch, M–L, Handy 0 (nur Pipeline). Dateien: `pipeline/` Tile-Build, `engine/materials.ts`.

**30. Fassaden-Impostors/Atlas für Ferne.** Ab 200 m Hauszeilen als vereinfachte Boxen mit Atlas-Farbe (LOD), spart Dreiecke, die in Skyline/Dunst gesteckt werden können. Wirkung mittel (indirekt), L, Handy – spart. Dateien: `engine/tiles.ts`, Pipeline.

**31. Lichtprobe-Gradient.** Statt IBL am Handy: 2-Farben-Hemisphärenlicht + Richtungs-Tint nach Normale (Himmelsfarbe oben, Boden-Bounce unten, Sonnenseitige Wärme), im Welt-Material per Uniform. Macht Lambert deutlich plastischer. Wirkung hoch, S, Handy 0. Dateien: `engine/materials.ts`.

**32. Zeit-basiertes Material-Toggle.** Nachtatlas (`atlas_n_half`) mit sanftem Crossfade statt hartem Wechsel; Fensterleuchten bereits drin, aber Übergang Dämmerung 17–19 Uhr als Fade-Fenster. Wirkung mittel, S, Handy 0. Dateien: `engine/daytime.ts`, `engine/materials.ts`.

**33. Adaptive Qualität sichtbar machen.** Dynamische Auflösungsskala + Fog-Verkürzung bei fps < 30 (Fog verdeckt Pop-in). Wirkung mittel (Stabilität), S, Handy spart. Dateien: `engine/quality.ts`.

**34. Kontur-/Kanten-Pass (optional stilisiert).** Dünner dunkler Tiefenkanten-Outline am PC (Sobel auf Tiefe) macht Silhouetten klarer und gibt Comic-Hauch ("Arcade"-Ton aus Vision). Wirkung mittel, M, Handy ++ (aus). Dateien: `engine/post.ts`.

**35. Karten-/Himmels-Sync.** Himmelsfarbe in Karte/HUD aufgreifen (Rahmen färbt sich Tag/Abend/Nacht), kleine UI-Stimmung. Wirkung klein, S, Handy 0. Dateien: `ui/hud.css`, `engine/daytime.ts`.

## Mood-Bilder (Beschreibungen, eigene Werke zu zeichnen)
**Mood A "Hochnebel-Novembermorgen Kreis 5".** Geschlossene milchig-warmgraue Decke, die Hardbrücke-Bögen und Prime Tower oben im Dunst verlieren (nur 40 % Kontrast), Tramschienen nass und dunkel, in jeder Pfütze ein orangefarbenes Haltestellen-Licht, ein einzelnes Gelb vom fallenden Platanenlaub, Dampf aus einem Kebab-Lüfter. Palette: Grauweiss, Anthrazit, Tram-Blau, Herbstgelb, ein Magenta-Fleck (AL-Plakat).

**Mood B "Golden Hour Hohlstrasse".** Tiefe Sonne durch die Strasse, Backsteinfassaden glühen Orange-Rot, lange blaue Schatten der Passanten auf warmem Sandsteingrau, Himmel Rosa-Aprikose über Violett am Zenit, Silhouette des Üetlibergs als blaue Welle in drei Dunststufen, erste Fenster gehen warmgelb an. Palette: Terrakotta, Aprikose, Schattenblau, Violett, Backstein.

**Mood C "Regennacht Langstrasse".** Nasser Asphalt als Spiegel, Neon in Magenta/Grün/Blau zerfliesst in Streifen, Lichtkegel der Laternen mit sichtbarem Regenfall, Schirme als bunte Punkte, Tram als beleuchteter Kasten, schwarze Fassaden mit vereinzelt warmgelben Fenstern; Bloom nur an Leuchtreklamen. Palette: Tiefes Blauschwarz, Neon-Magenta, Gelb, Spiegel-Silber.

## Empfohlene Reihenfolge
1) #1, #2, #31 (alles reine Farb-/Licht-Parameter, ein Nachmittag) – danach Screenshot-Kontaktbogen. 2) #7 Skyline und #4 Blobschatten. 3) #9 Wetter-Presets mit #5 Nässe. 4) #12/#13 Nacht. 5) UI (#23, #25). Immer vor/nach in beiden Viewports, Budgets aus `ARCHITECTURE.md` messen (Draw Calls ≤ 250 Handy).
