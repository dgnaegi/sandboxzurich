# Zone 1 Landmark-Runde an den Kamerapunkten (Agent z1L, 2026-10-22)

Werkzeug: Fotos `data/raw/photos/z1/*` (Mapillary CC BY-SA, Panoramax, Commons), Spielbilder per `pipeline/landmarks/free_shot.mjs` von der Fotopose aus (auch «nob» = nur Landmarks), Grundrisskarten mit swissBUILDINGS3D-Ids (graue Flaechen = von bestehendem Landmark ausgeblendet). Vorher-Bogen `preview/zone1_before.jpg`, Vergleich `preview/z1L_cmp_bahnhofplatz.jpg` (Foto | Landmark allein).
Code: `pipeline/landmarks/z1L_houses.py` -> `pipeline/overrides/landmarks_z1L.json` (1 Landmark, 128 kB GLB, kein eigenes Texturpaket).
**Befund:** Zone 1 ist durch langA/B/C, k4w3 (Amtshaus, Volkshaus, Kanzlei), hz, k4w5 (Europaallee grau), hb* schon dicht mit Landmarks belegt (235 Eintraege, an fast jedem Punkt 3-12 im Umkreis 90 m). Die Fotovergleiche zeigen dort Farbe/Hoehe/Typ im Rahmen; offen sind nur Ornament und Ladennamen. Mapillary-Heading war bei mehreren Punkten (Kasernenstrasse, Dienerstrasse, Lagerstrasse) um bis 90 Grad falsch, deshalb dort keine Haus-Id ohne sichere Zuordnung (Lehre 15).

| Punkt | Foto-Befund | Fix | Note vorher -> nachher (geschaetzt) |
|---|---|---|---|
| Haltestelle Bahnhofplatz/HB | Westseite Bahnhofplatz: 7-8-geschossiger graugruener Steinplatten-Bau mit paarigen Hochfenstern (dunkelgruene Rahmen), verglastes EG mit rotem Vordach-Band (Mapillary 2024 h160, 2019); Spiel: dunkelgraue Granit-Gruenderzeitfassade mit Kinderladen-Schild | Landmark `z1L_bahnhofplatz_teal` (ID_CBA646B8, 28 m, #82948f, roter Vordach-Streifen) | 3.2 -> 3.7 |
| Langstrasse/Dienerstrasse, Militaer, Brauer, Hohl, Lager | Fotos vs. Spiel: Eck- und Strassenhaeuser bereits als Landmarks (Farbe, Fensterachsen, Laeden) | keiner (nur Farbnuance Hohlstrasse NO-Zeile: Foto blass lachsbeige mit bordeauxroten Laeden, Spiel creme mit braunen Laeden) | unveraendert ~3.5 |
| Helvetiaplatz / Haltestelle / Kanzlei | Volkshaus (rot, Walmdach), Amtshaus-Plattenbau, Kanzlei-Schulhaus vorhanden und passend; Platzboden (Rautenfelder) vorhanden | keiner | unveraendert ~3.8 |
| Kasernenstrasse | Foto: helle Rasterfassade 6-7 Geschosse am Sihlufer, Spiel: dunkelblaue Glasfassade (C418 31 m / DFE4 29 m); Foto-Heading unsicher | keiner (Zuordnung unsicher, Ticket Z1L-2) | 3.0 -> 3.0 |
| Baeckeranlage | Rundes Sandbecken mit Steinrand und Pergola, polygonale Natursteinplatten-Wege, Pferdeskulpturen; Spiel: eckiger Sandkasten mit bunten Boxen, Kiesweg | keiner (Platz-/Objektcode, nicht Landmarks) | 3.0 -> 3.0 |
| Europaallee, Sihlpost, HB-Halle, Querhalle, Velotunnel, Bahnhofplatz (Escher) | bereits eigene Arbeit (#58, #71, k4w5) | keiner | unveraendert |

## Tickets
- Z1L-1 **Kachel neu bauen** (Hide wirkt erst dann): t_8_-4 (Bahnhofplatz, Hide-Punkte (1692.9,-764.9), (1673.9,-772.7)). Zur Sicherheit Nachbar t_8_-3.
- Z1L-2 Kasernenstrasse: hellgraue Rasterfassade (Sihlufer, Mapillary 2023/24 Nr. 4/6) statt dunkelblauem Glas; Ids C418/DFE4 pruefen mit Begehung vor Ort oder besserem Foto (Heading).
- Z1L-3 Baeckeranlage: Platzdetail rundes Sandbecken (Steinring, Pergola Holz) + Natursteinplatten statt Kies (`places_detail_baeckeranlage.json`, nicht in meinen Dateien); Pferdeskulpturen am Brunnen.
- Z1L-4 Hohlstrasse NO-Zeile (8153, 33BD, C6C1) und Langstrasse-Eckhaus mit Laeden: Farbnuance lachsbeige + bordeaux Laeden (Ticket, kein sicheres Id-Mapping).
- Z1L-5 Dienerstrasse: Dashcam-Fotos 2025 zeigen violettgrauen 6-Geschosser und braunglasiges Buerohaus (Dienerstrasse West), Standort der Fotopose liegt im Spiel in einem Gebaeude, Pose ungenau; Haus-Ids offen.
- Z1L-6 Kamera Heading: Mapillary-Heading bei Zone 1 oft falsch (bis 90 Grad); `fetch_zone_cams.py` sollte Kamera-/Fahrtrichtung-Flag speichern.

## Kacheln zum Neubau
t_8_-4 (Bahnhofplatz), optional t_8_-3. Hinzugefuegt: 128 kB GLB (1 Landmark, 8.8k Tris).
