# Zone 3 Gebiet Mitte (Agent z3b, 2026-10-20)

Werkzeug: Fotos `data/raw/photos/z3/*` (Mapillary CC BY-SA, Panoramax, Commons), Spielbilder per `pipeline/landmarks/free_shot.mjs` von der Fotopose aus; Grundrisskarten mit swissBUILDINGS3D-Ids (Skript im Scratchpad). Bögen `preview/z3b_*.jpg` (cmp1-4 Foto|Spiel, bp1-3 Brunnen, nob/bh/br freie Ansichten, map_a/b/c Grundrisse).
**Wichtig:** Landmarks z-fighten im Dev-Spiel mit den noch vorhandenen Kachelhaeusern (Lehre 14): die neuen Haeuser sind erst nach dem Build der betroffenen Kacheln sauber (hide-Punkte gesetzt). Vorher wirken sie gemischt (z. B. Backstein + Gelb).

| Punkt | Foto-Befund | Fix | Note vorher -> nachher (geschätzt) |
|---|---|---|---|
| Bullingerplatz (Brunnen) | Flaches rundes Becken, dunkler Granitrand, beiges Becken, Tellerschale; Spiel: Becken war massive graue Scheibe (Wasser im `tellerbrunnen`-Objekt liegt unter dem Deckel), ein zweiter blauer Katalog-Brunnen am Rand | Landmark `z3b_bullinger_brunnen` (Rand R 6.55 / 0.55 m, Wasserflaeche 0.44, Teller Ø 5.3 m, heller Steinring im Pflaster), `z3b_ochre_row` (ockerfarbene Heimatstilreihe SE, Terrakotta-Walmdach, vorher blaugrau) | 3.0 -> 4.0 |
| Bullingerhof | Weisser Rundpavillon (Kratzputz, grosse Fenster), niedriger weisser Flachbau mit Fensterband, Granitplatten + Pflasterfeld | Landmarks `z3b_pavilion` (090BB9FA), `z3b_pavilion_low` (1D4E9A12), `z3b_bhof_main` (CC508A03, Farbe, Id unsicher) | 2.5 -> 3.5 |
| Zypressenstrasse | Rotes Backstein-Eckhaus mit weissem Mittelrisalit und Giebel (praegt den Blick vom Platz nach Sueden), Spiel: gelb-grunes Standardhaus | Landmark `z3b_brick_corner` (06F4F40D) | 3.0 -> 4.0 |
| Sihlfeldstrasse | Rosa 5-Geschosser mit Fensterbaendern und verglastem EG; Spiel beige-kariert | Landmark `z3b_sihlfeld_pink` (07C92BCE; Id nach Fotopose, Zypressenstr.-Seite evtl. orange, siehe Ticket Z3b-4) | 3.2 -> 3.8 |
| Erismannhof | Hofhaeuser creme-ocker mit grauen Laeden, Spiel: Hof als Rasen mit gelb-cremigen Blocks, dunkelgruene Laeden (Farbe nahe genug) | keiner (nur Ticket Z3b-5) | 3.8 -> 3.8 |
| Ernastrasse | Beiges Eckhaus links (DED0B869), blauer Block ok | Landmark `z3b_erna_corner` (beige #e6d2ae, Walmdach) | 3.5 -> 4.0 |
| Brauerstrasse West | Wegen Tramgleisen + Haltelinien + Stahlzaun; Glasbau (hpc?-Schild) vorhanden, Spiel hat ihn; Bruecken-Brüstung riesig, Gleise fehlen | nichts in meinen Dateien moeglich (Bruecke/Gleise) | 3.0 -> 3.0 |

## Tickets
- Z3b-1 `catalog_assign.json`: `exclude: ["BR-41"]` (Bullingerplatz, WVZ Notwasserbrunnen Beton, V4 bei (-44.2,-499.1)): doppelter blauer Brunnen am Rand des Beckens; das Becken zeichnet `places_detail_bullingerplatz.json` (`tellerbrunnen`).
- Z3b-2 `places_detail.ts` `tellerbrunnen`: Wasserflaeche (y 0.3) liegt unter dem Deckel (y 0.4); besser Rand-Ring + Wasser auf 0.34. Mein Landmark deckt das ab, nach Fix ist das Landmark nur noch Deko.
- Z3b-3 Bullingerhof-Platz: Granitplatten-Band + Pflasterfeld vor dem Rundpavillon (ca. (-105..-95,-500..-490), Mapillary 1155629122273388), im Spiel Asphalt.
- Z3b-4 Zypressenstrasse Ostseite: Mapillary 4672603846102916 zeigt orange-braunen Balkonblock mit Laeden (03684AC4/07C92BCE?), Pose ungenau; Id klaeren (Kachel-Build + Blick), sonst Rosa/Orange vertauscht.
- Z3b-5 Erismannhof: Fensterlaeden grau-blau statt dunkelgruen (Notizen `fields`, nicht meine Dateien).
- Z3b-6 Brauerstrasse/Hardstrasse-Bruecke: Tramgleise und gelbe Zebrastreifen fehlen auf der Bruecke, Parapet zu hoch fuers Spieler-Kameraauge (Bruecken-/Schienen-Code).
- Z3b-7 Bullingerplatz Beizen: rote Sonnenschirme/Aussensitze an der NW-Ecke fehlen (kein Parasol-Objekt in `places_detail.ts`; keine Namen belegt).
- Z3b-8 Nach Kachel-Build prüfen: Hide der 8 neuen Landmarks (Kacheln um (-60,-540), (-110,-510), (0,-540), (-15,-585), (75,-400)).
