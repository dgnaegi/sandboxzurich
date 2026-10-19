# Langstrassen-Unterführung (Langstrasse unter dem Gleisfeld, Kreis 4 ↔ 5)
Typ: Tunnel/Bauwerk | OSM: Strassentunnel Way 4592588 (Langstrasse, layer -1, `lanes=3`, `sidewalk=no`, trolley_wire), Fussgänger-/Velotunnel Way 4803419 («West») und 4803422 («Ost»), beide `layer=-1`, `cycleway:width=2…2.2` | Fotos: 73 (Bogen `preview/ref_v3_langstr_unterf.jpg`, `_2.jpg`, `_3.jpg`; Nummern «nterf:N» = `photos.json[langstr_unterf]`, «_sued:N», «_nord:N» = `langstr_unterf_sued/_nord`; die 4 letzten von nterf sind Commons-Fotos der Wandgestaltung). Lizenzen in `CREDITS.md`.
Relevant für den Innenraum: nterf 0,3–11,15,24–26, sued 0–6,13,19,20, nord 4–6,19, Commons (Bild 1–4 Wandgestaltung). Commons-Geosuche liefert sonst v.a. SBB-Dienstgebäude/Panorama (nicht relevant).

## Lage und Länge (aus OSM, LV95-lokal)
- Achse Strassentunnel: S-Portal (894.04, -363.94) → N-Portal (931.68, -278.28), **Länge 93.6 m**, Richtung 24° von Nord (Süd-West → Nord-Ost).
- Fussgänger-/Velotunnel parallel, **Achsabstand ±9.5 m (Ost) / ±9.95 m (West)** von der Strassenachse, gleiche Länge (Ost: (921.8,-275.1)→(885.0,-359.8); West: (902.8,-367.6)→(940.4,-281.6)). Sie münden an den Portalen in die Pfade zur Langstrasse/Zollstrasse (OSM-Wege 741326538, 4803421, 1136458317/18).
- Tunnel liegt unter dem **Gleisfeld** des HB-Vorfelds. swissALTI3D (Spiel-Höhen): Gleisniveau/Deck −2.2 m (S) bis −2.9 m (N), Strassenniveau im Tunnel ca. −8.2 m (S) bis −8.8 m (N).

## Querschnitt (aus Fotos geschätzt, gegen OSM geprüft)
- **Fahrbahn 11.6 m** (drei Streifen + Velostreifen), Mittellinie weiss durchgezogen, gestrichelte Spurlinien, Richtungspfeile (nterf 0, 5–7, 10, 11, 15). Kein Trottoir im Strassentunnel (`sidewalk=no`).
- **Lichte Höhe Strassentunnel ≈ 4.6 m**; Decke Beton mit Querrippen/Fugen alle ~6 m.
- **Wände:** unten eine geneigte graue Betonschräge (Anlauf) bis ~1.6 m, darüber senkrechte Betonwand mit dunklen senkrechten Kabel-/Revisionsblenden im ~6-m-Raster (nterf 0, 5–7, 10–11).
- **Trennwand** Strasse/Durchgang ≈ 1.15 m dick (Strassenwand bei ±6.7 m, Durchgangs-Innenwand bei ±7.85 m).
- **Seitendurchgänge** (links und rechts): Breite am Boden ~3.6 m (7.85–11.5 m ab Achse), **lichte Höhe ≈ 3.4 m**, Boden Asphalt mit gelber gestrichelter Mittellinie (Fuss/Velo, nterf 24–26, sued 13). Innenwand senkrecht, hell gestrichen (Cremeweiss, Revisionsnischen ca. alle 12 m, nterf 25); **Aussenwand stark nach aussen geneigt** (bis ~1.1 m Anlauf über 3.4 m Höhe, nterf 26, Commons Wandgestaltung 2); oben an der Schräge farbige Dreieckskeile (Wandgestaltung 1986, Commons «Wandgestaltung Langstrassenunterführung» Bild 1–4; im Spiel eigene Farbfolge).
- **Beleuchtung:** Strassentunnel: Reihen aus länglichen Leuchten mittig in der Decke + Tagesbeleuchtung (nterf 0, 4–6, sued 3). Durchgänge: Leuchtbänder (LED-Paneele ca. 1.2 × 0.3 m) alle ~3 m an der Decke (nterf 4, 8, 24, 25).
- **Pfeiler:** keine Stützen im Tunnelraum (Rahmenbauwerk), nur Querrippen.
- **Portale:** Betonblende über Fahrbahn und Durchgängen (Stirnwand bis Gleisniveau, nord 5/6, sued 5/6); Öffnungen Strasse 13.4 m breit, Durchgänge je ~4.7 m.
- **Rampen:** beidseits Trog mit senkrechten Betonstützwänden (bis ~5 m hoch, Schalungsspuren und Graffiti, sued 1, 2, 5, 6, 11, 19; nord 0, 1, 4, 20); Gefälle ≈ **7 %** über ~70 m (swissALTI3D: −5.5 m bei 40 m vor dem Portal, −8.0 m am Portal). Geländer oben, daneben Velo-/Fusswege (sued 14).
- **Graffiti:** Tags/Throw-ups v.a. an den Stützwänden der Rampen und in den Durchgängen (nterf 24, sued 11, nord 0); im Strassentunnel kaum.

## Umsetzung im Spiel
- `pipeline/landmarks/lu_geom.py` (Achse, Profil, Masse), `lu_tex.py` (Texturen, eigene Gestaltung), `lu_tunnel.py` (Modell → `web/public/models/landmarks/lu_unterfuehrung.glb`, Eintrag `pipeline/overrides/landmarks_lu.json` mit `colliders`).
- Geländeeinschnitt: `pipeline/overrides/terrain_cuts.json` (Eintrag «Langstrassen-Unterfuehrung …», Typ `profile`, `lock: true`); Deck für Gleise: `research/v3/langstr_unterf_deck.json`.

## Abnahme Runde 2 (Agent U, 2026-10-19; `preview/lu_before.jpg`, `preview/lu_cmp.jpg`, Foto links | Spiel rechts; Referenz `preview/lu_ref.jpg`)
- Fehler gefunden und behoben: Boden-UVs waren transponiert (Spurlinien/Mittellinie verliefen quer zur Fahrtrichtung). Jetzt laufen Fahrbahnmarkierungen und gelbe Durchgangslinie längs; Fussgänger-Piktogramm im Durchgang neu.
- Neu: Portal-Stürze 0.55 m vorspringend, Stahlgeländer an der Deckkante, dunklere Decke, schmalere Querrippen (0.28 m), wärmere Wandtöne. Tris 7236 (im Rahmen).
- Offen, nicht im LU-Zuständigkeitsbereich: Ein grosses Terrain-Dreieck der Kachel (Schnittkante, z -8.5 bis -3) ragt ca. bei s = 48 in den Durchgang und in den Strassentunnel (graue «Keile»). Ursache vermutlich Gitterauflösung/gltfpack-Vereinfachung am Terrain-Cut; Abhilfe: Cut-Raster feiner oder Boden im Bauwerk als Loch.
- Noten 1-5 (Spiel vs. Foto): Strasseninneres 3 (Form/Markierung ok, zu dunkel/bläulich, Wände fehlen cremige Tönung); Durchgang 3 (Proportion, Linie, Leuchten, Wandkeile ok; Graffiti/Nischen grob); Portal S aussen 3; Portal N aussen 2 (Stirn mit Geländer da, aber Fotoportal wirkt viel mächtiger, Aussicht aus 48 m nicht vergleichbar); Beleuchtung 3; Terrain-Keil-Artefakt 1.

## Runde 3 (Agent U; `preview/lu_cmp2.jpg`, Foto links | Spiel rechts)
- Terrain-Keil im Durchgang weg (Bodenloch im Bauwerk-Footprint, `terrain_cuts.json` "hole" + `terrain_cuts.holes()`, Kachel 4_-2 neu gebaut). Im Strassentunnel bleibt links unten eine helle Platte (Randsteinschräge/Bodenstück) sichtbar, nicht weiter untersucht.
- Markierung: Spur-/Mittellinien weiss, rechte Randlinie gelb. Asphalt neutraler, Wände/Decke heller, Szenenlicht färbt noch bläulich.
- Portale: Betonplatte + Brüstung + Geländer + Schildfeld; von aussen aus 48 m nur klein sichtbar, Foto-Wirkung (mächtig) nicht erreicht.
- Noten: Strasseninneres 3, Durchgang 3.5, Portal S 3, Portal N 3, Beleuchtung 3, Keil-Artefakt 4.
