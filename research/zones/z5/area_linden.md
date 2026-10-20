# Zone 5, Gebiet Lindenplatz / Altstetterstrasse / Hohlstrasse / Baslerstrasse (Agent z5b, 2026-10-20)

Vergleichsbilder: `preview/z5b_before_<punkt>.jpg` (Foto | Spiel vorher), `preview/z5b_after_all.jpg` (Foto | Spiel vorher | Modell nachher, isoliert),
`preview/z5b_ref_{linden,flur,basler}.jpg` (Referenzfotos), `preview/z5b_map_*.jpg` (Footprint-Karte mit swissBUILDINGS3D-Id/Höhe, Mapillary-Posen), `preview/z5b_ortho_linden.jpg`, `preview/z5b_models.jpg`.
**Wichtig:** Landmarks ersetzen die Häuser erst nach dem nächsten Kachel-Build (hide-Punkte sind Build-Zeit, `build_testarea.py`); bis dahin liegen die Modelle über den alten Häusern. «Nachher» ist deshalb nur isoliert (lmview) belegt, nicht im Spiel.
Fotos: Mapillary (CC BY-SA 4.0), Panoramax, Commons (CC BY-SA); GPS 10-30 m ungenau (Lehre 11), Häuser nur über Fussabdruck-Karte + zwei übereinstimmende Fotos zugeordnet.

## Befund zur Aufgabenstellung
- **Lindenplatz ist kein Riegelhaus-Dorfkern.** Der Platz (Märkte, Granitpflaster) wird vom Block Badenerstrasse 681 (Hotel Spirgarten, Coop, Apotheke, Zahnarzt) und der Zeile Altstetterstrasse 150/152 gerahmt; Kirche und «Krone» (Dorfkern-Rest) stehen ~100 m weiter westlich (Landmarks `k93_kirche_altstetten`, `k39w3_krone` existieren).
- **«Hohlstrasse Egli-Siedlung» liegt falsch benannt:** die Egli-Siedlung ist in Aussersihl (x≈-400, Landmark `hz_egli_*`). Der Kamerapunkt (-1367, 411) ist die Hohlstrasse in Altstetten beim Letzipark (Fotos zeigen Backsteinbau «Komplex 45x» und Büroschlange Hohlstrasse 459/465). Vorschlag: Punkt umbenennen in «Hohlstrasse Letzipark».

## Pro Kamerapunkt
| Punkt | Foto | Befund (Spiel vorher) | Fix / Ticket | Note vorher → nachher (geschätzt) |
|---|---|---|---|---|
| Lindenplatz (-2345, 352) | px_b9a14c40 (Badenerstr. Ost), cm_Welti_Spirgarten, ml_498123644871495 | Block 681 als orangefarbener Backstein mit Balkonen und Lochfenstern; Platz dunkler Asphalt-Look statt hellem Granitpflaster; schwebende rote Marktstand-Platte (aus `places_detail_lindenplatz.json`) | Landmark `z5b_spirgarten` (lachsfarben, Bandfenster, verglastes EG, flaches Dach); Pflaster `places_detail_z5b.json` (rect -2347..-2309 × 330..378, mat pave, über dem alten Beton-Patch); Storefront Coop (Mapillary 498123644871495) | 2.5 → 3.5 (nach Build) |
| Altstetterstrasse (-2277, 342) | ml_1157056783007138, ml_687999557132870, px_c21af5bc | Bauzaun/Bagger stimmen (Baustelle 2023-25); Häuser W-Seite gelb/blass statt beige mit Läden; Eckhaus Badenerstr. 672 als rosa Rundturm; O-Seite blaugraue Wand | Landmarks `z5b_altst150`, `z5b_altst152` (beige, Mansarddach dunkel), `z5b_baden672` (ocker, rotes Walmdach), `z5b_altst149`, `z5b_altst147` (hellgraue Wohnhäuser) | 3.0 → 3.8 |
| Hohlstrasse Egli-Siedlung (-1367, 411) | ml_795050989783909 (N), ml_1971266673697893 (SO), ml_514605241324304 | N: Backsteinfabrik als fenster- und strukturlose Wand; SO: Büroschlange 459 als rot-graues Karomuster-Hochhaus (falsches Material) | Landmarks `z5b_hohl_brick` (Backstein, hohe Rundbogenfenster, Flachdach), `z5b_hohl_letzi` (cremefarbene Bandfensterscheibe 31 m, Ladenzeile EG) | 2.0 → 3.5 |
| Hohlstrasse/Flurstrasse (-1450, 440) | ml_974017061161906, ml_436475452826573 (übereinstimmend) | Weisses Balkonhaus Flurstrasse 2 fehlt als Detail; Baum im Fussweg bei Pose 436 (Kamera in Baumkrone); Bus im Bild (Verkehr, kein Fehler) | Landmark `z5b_flur_block` (cremeweiss, Balkonplatten als Bänder, 28 m); Ticket T-F1: gläserner Bürobau gegenüber (SW-Seite, Fotos 974/436 links) nicht zugeordnet; Letziturm-Hochhäuser (rot/weiss) in Fotos 703/1692 fehlen | 3.0 → 3.5 |
| Baslerstrasse (-1447, 209) | ml_702254062691884, ml_1346498469748326, ml_3907069202852843, cm_Einkaufszentrum_Letzipark | Spielbild ist eine leere Pflasterfläche; **rote Velostreifen mit grünem Streifen und gelben Pollern fehlen** (Mapillary 2025, neuer als SWISSIMAGE); Letzipark/Hochhaus-Skyline vorhanden | Kein Fix im Rahmen der erlaubten Dateien: `places_detail.MAT` und `markings_override` kennen keine rote Farbfläche → Ticket T-B1 | 2.5 → 2.5 |

## Weitere Fixes
- `pipeline/overrides/storefronts_z5b.json`: Coop (OSM 2028881218: dunkles Band, orangefarbene Schrift), UBS Badenerstrasse 678 (OSM 1701730818: dunkles Portal, rotes Logo). Beide mit Quelle.
- Modelle ohne Ladennamen (Signs kommen über das POI-System, vgl. z4_houses): Spirgarten/Coop-Schilder wären sonst doppelt.

## Tickets
- **T-B1 Rote Velostreifen Baslerstrasse** (und allgemein rote/grüne Radstreifen jüngeren Datums): `markings_override` um `add_red` bzw. `places_detail.MAT` um «red» (178,64,52) erweitern. Fotos Mapillary 2025 (ml_702254…, ml_5849…, ml_1152…).
- **T-S1 Hip-Dach-Spike:** `hip_roof` erzeugt auf dem Fussabdruck 85DB372F (Spirgarten) eine Spitze auf dem Dach; deshalb Flachdach (SWISSIMAGE zeigt ein flaches Walmdach mit Oberlicht).
- **T-L1 Marktstand «stall»** in `places_detail_lindenplatz.json` (h 70–80) wirkt als schwebende rote Platte; Fotos zeigen keine Stände. Prüfen/entfernen.
- **T-F1** s. oben (Glasbau Flurstrasse, Letzitürme). **T-H1** Pose-Foto 436 zeigt Baum als Blattbrei vor der Kamera (Baum zu nah an Fahrbahn, Koordinate des Baumes im Baumkataster prüfen).
- **T-N1** Kamerapunkt «Hohlstrasse Egli-Siedlung» umbenennen (s. Befund); in `pipeline/zones.py` steht noch `S:Hohlstrasse`.
- Nach dem nächsten Kachel-Build in-game prüfen (Vorher/Nachher-Bogen `python pipeline/zones/zone_cmp.py 5 after2`): Spirgarten/Coop-Ecke, Pflaster, Altstetterstrasse-Häuser, Hohlstrasse N/SO.
- Fassadennotizen/Felder wurden nicht ergänzt (Lehre 6: Handarbeit an prägenden Häusern); daher kein `facades_notes.py`/`merge_notes`-Lauf nötig.

## Dateien
`pipeline/landmarks/z5b_houses.py` (9 Landmarks: spirgarten, altst150, altst152, baden672, altst149, altst147, hohl_brick, hohl_letzi, flur_block), `pipeline/overrides/landmarks_z5b.json`, `web/public/models/landmarks/z5b_*.glb`, `pipeline/overrides/places_detail_z5b.json`, `pipeline/overrides/storefronts_z5b.json`; `merge.py` + `apply_names.py` gelaufen.
