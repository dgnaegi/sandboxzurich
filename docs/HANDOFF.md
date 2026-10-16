# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Stand (2026-10-16 früh, nach Nachtlauf)
Spielgebiet: Kreise 4+5, Teile 9 und 3, Friedhof Sihlfeld (6.88 km², 219 Spiel- + 82 Kulissenkacheln, Rand = Baustellenzaun). Karten-Phase: Quests, Polizei, Einblendungen aus (DECISIONS #25/#26). **Nicht selbst deployen**: User deployt später über ein CDN nach `docs/DEPLOY.md`.

### Was der Nachtlauf gebracht hat (Details in DECISIONS #27–#36)
- **Bewegung**: CMU-Mocap statt Sinus-Clips (#29), Animationsbibliothek für Stehen/Reden/Sitzen/Handy (`anims_*.glb`, #36), Kleidung per Laufzeit-Tönung (`world/tint.ts`). Rennen: Shift / ⇧ (Touch = Umschalter).
- **Fahrzeuge**: Auto klauen und fahren (E), `player/drive.ts`, `vehicle_*.ts` (#30); Automodelle v3 (Loft-Karosserie, Schilder, Lichter, #31); Velo-Rig mit Neigung und IK-Fahrpose.
- **Rendering**: AgX, natürliche Tageszeiten, Oktober-Sonne, Schatten-Snapping; PC: Himmels-IBL + PBR-Kacheln mit Glaserkennung (#33), Handy: Lambert.
- **Karte + Uhr**: Vektor-Stadtplan `pipeline/mapdata.py` → `data/map/vec.json`, Uhr-Panel per Klick (`ui/clock.ts`, #28).
- **Strassen v2** (#27): Velo-Piktogramm aufrecht (90°-Bug), Spurpfeile, Tram-Inseln, Baustellen sperren Spuren (`roadgraph.py`).
- **Boden v2**: prozeduraler Asphalt/Trottoir/Pflaster/Randstein/Rinnstein (`pipeline/ground_tex.py`), Weltkoordinaten-Variation im Shader.
- **Bäume v2**: Höhe/Krone aus swissSURFACE3D-nDSM (`pipeline/trees_dims.py`, `data/build/ndsm/`), 15 Arten, Herbstfarben, LOD + Impostor, Baumscheiben.
- **Fassaden v3** (#32): exakte Wandfarben, Gründerzeit/Klinker/Sandstein, Gesimse, Erker; Notizen für 261 Adressen (`research/buildings/visual_notes_v3.json`) + Wandfarbe aus Ladenfotos (nicht bei «Identität unsicher»).
- **Ladenfronten v3**: 349 Lokale mit Foto-Notizen (`research/shops_v3/shops_v3.json`), Laufzeit-Stil (`world/storefront_style.ts`, `_sign`, `_terrace`), Front nur über Lokalbreite, Terrassen nur auf gemessenem Trottoir (`pd`).
- **Landmarks** (GLB, `pipeline/landmarks/`, Manifeste `overrides/landmarks_*.json` → `merge.py`): Runde 3 + Wellen 2/3, zusammen ~60 Bauten in allen Kreisen (u. a. Volkshaus, Lochergut, St. Jakob, Prime Tower, Viadukt, Hardbrücke, KVA, Röntgenplatz-Randbau, Toni, Schiffbau, Letzigrund, Bhf Altstetten/Wiedikon, Krematorium + 7000 Grabsteine, Amtshaus Helvetiaplatz, Sihlpost, Kaserne, Zeughäuser, Freitag-Turm, Löwenbräu, Westpark/Galaxus, Mobimo, Puls 5, Technopark, Letzipark, Lindenplatz-Häuser). Vergleichsbilder `preview/lm3_*`, `lm4_*`, `lm5_*`. Vertex-Farben linear → `D.hexl()`.
- **Plätze** (#35): `pipeline/places_detail.py` + `overrides/places_detail*.json`, Röntgenplatz und 14 weitere (Boden aus Orthofoto, Brunnen, Kioske, Bänke).
- **Wildplakate v2**: eigene Gestaltung echter vergangener Kultur-Events (`research/posters/events.json`, `pipeline/gen_wildposters.py` + `wildposter_*.py`). Politische Events stehen auf der Freigabeliste in `research/posters/README.md` und werden NICHT verwendet, bis die Kampagne freigibt.
- **Fixes**: OSM-Multipolygon-Gebäude (Westpark/Galaxus, Technopark) wurden als «abgerissen» gelöscht; OSM-Parks nur Rasen wo AV grün (Kanzlei-Schulhof); Röntgenplatz-Koordinaten; Besichtigungsschlange nur um ihre Uhrzeit; Build-Vorlauf 450 → 140 s (STRtree für Adress-Notizen).

### Pipeline-Reihenfolge für einen Komplett-Build
1. Texturen (nur wenn Ebenen geändert): `gen_facades.py neubau_b`, `gen_facades3.py`, `gen_textures.py`, `gen_wildposters.py`.
2. Landmarks: jeweilige `k*_*.py` bzw. `k93_all.py`, dann `pipeline/landmarks/merge.py`.
3. `pipeline/roadgraph.py` nur wenn Baustellen geändert.
4. `.venv/bin/python pipeline/build_testarea.py > logs/build_fullN.log 2>&1` (30–45 min; einzelne Kacheln `SBZ_TILES=ix_iy,…`).

### Tests und Werkzeuge (web/tests)
`gameplay.mjs`, `touch.mjs`, `drive.mjs`, `clock.mjs`, `perf.mjs` (Handy 4× gedrosselt), `perf_pc.mjs`, `shots.mjs` (feste Punkte inkl. Landmarks; Kontaktbogen per PIL zusammensetzen, der eingebaute bricht bei vielen Bildern ab), `look.mjs`, `topdown.mjs`, `gait.mjs`, `humans_v4.mjs`, `ground_shots.mjs`, `trees_shots.mjs`, `wildposters_shots.mjs`. Achtung: keine Warteschleifen mit `pgrep -f build_testarea` (matchen sich selbst), nie `git stash` (parallele Agents).

## Offen / Nächstes
1. Ergebnis des 2. Komplett-Builds im Spiel prüfen (QA-Bogen `preview/qa_night2_*.jpg`), siehe unten «Letzte Kontrolle».
2. Westpark-Fassade wirkt in der Modellansicht dunkel (im Spiel prüfen), Zeughäuser/Kaserne grob, Toni-Rampen, Hardbrücke-Perrons.
3. Wildplakate: mehr Venues (Recherche Runde 2 läuft/gelaufen), Unterführungen/Stromkästen/Bauzäune als Plakatorte.
4. Fassaden-Notizen: Fotoqualität limitiert (≈5 Häuser pro Bogen); besser mit Feedback von Leuten aus dem Quartier oder eigenen Fotos.
5. Vor MVP (User): Tests auf echten Handys, Impressum, Kennzeichnung politische Werbung, Freigabe Plakate durch Kampagne, Deploy nach `docs/DEPLOY.md`.
6. Spawn auf Brücke per Teleport landet unten (groundAt braucht z).

## Letzte Kontrolle (2026-10-16, 03 Uhr, nach 4. Komplett-Build)
- Build `logs/build_full7.log`: 301 Kacheln, 0 Fehler, 55 min.
- Bilder: `preview/qa_final_desktop.jpg`, `preview/qa_final_phone.jpg` (27 Punkte), Nacht vorher/nachher `preview/nachtlauf_vorher_nachher.jpg`.
- Perf (Dev-Server): Handy 4× gedrosselt 58 fps, 167 Calls, 0.53 Mio ✔; PC 58 fps, 425 Calls, 2.6 Mio ✔.
- Tests: gameplay 5/5, touch 4/4, drive 18/18, clock 12/12.
- Download bis spielbar (Prod, unkomprimiert) 26.8 MB, Budget 20 MB → mit Brotli am CDN ≈ 21–23 MB; nächste Hebel: Figuren-Texturen (4 MB), Karte lazy laden (1.9 MB), Fassaden-Atlas.
- Zuletzt behoben: Haltestellenschild von hinten gespiegelt (zwei Flächen), Tram-Frontscheibe leuchtete nachts, Nachtlicht erst ab Nachtanteil 0.12 (PC-Dämmerung 51 → 56 fps).
- Bekannt offen: Bezirksgebäude-Fenster mit Dreiecksartefakten (`k4w3_bezirk.py`), Hardau-Türme ca. 2 m tief (prüfen), offene Parks nachts dunkel, Tram 2000 fehlt, Kandelaber-Typen (keine Daten).
