# Fidelity: Foto vs. Spiel (2026-10-16)

Methode: 75 Panoramax-Fotos (CC-BY-SA, Fahrrad-Weitwinkel, `research/photos/by_tile.json`, Kandidaten `research/fidelity_cand.json`) im Spiel
aus gleicher Position/Richtung nachgestellt (`web/tests/fidelity_shots.mjs`, 1.6 m, vfov 80, 13:00). Paarbögen `preview/fidelity_k45_1..15.jpg`
(Foto links, Spiel rechts, je 5 Paare; Nummern = Kandidaten-ID). Adress-Overlay zum Ablesen der Fassaden: `pipeline/photos/fidelity_labels.py`.
Einschränkung: GPS der Fotos ±5 m und Blickrichtung ±10°, deshalb sitzt die Kamera teils auf dem Trottoir/neben der Strasse; Vergleich ist qualitativ.

## Systematische Abweichungen (gelten über viele Fotos)

| # | Thema | Foto | Spiel | Fotos | Status |
|---|---|---|---|---|---|
| S1 | Grüne Velostreifen (Farbbelag) | grün gefärbte Velostreifen/Radwege an Hardstr., Badenerstr., Hohlstr., Pfingstweidstr. | fehlen komplett | 2,10,16,27,40,50,55 | Vorschlag: `roadgraph.py` Streifen mit `cycleway=lane` + Farbe (nicht mein Bereich) |
| S2 | Trottoir-Farbe/Textur | mittelgrau, glatt, Asphalt- bzw. Betonplatten, warm | sehr hell (fast weiss), körnig, stark kontrastierend zur Fahrbahn | fast alle | Vorschlag: `ground_tex.py` Trottoir-Multiplikator ~0.80 und weniger Körnung (Komplett-Build) |
| S3 | Fahrbahn-Farbe | warm-neutralgrau, mit Flickstellen | kühl bläulich-grau, Pflasterband-Muster zu auffällig | fast alle | Vorschlag: Asphalt leicht wärmer tönen |
| S4 | Randstein/Rinne | grauer Granitrandstein, schmale Rinne | breite, helle Rinnenbänder mit Würfelmuster, zu dominant | 42,72,87,96,109 | Vorschlag: Rinnenband schmaler (0.25 m) |
| S5 | Blaue Zone / Parkfelder | blaue Linie, parkierte Autos dicht | Linie vorhanden, aber nur wenige Autos; Autos zu kantig/niedrig | 42,44,89,96,108,109,113 | Parkdichte erhöhen (`traffic.ts`, nicht mein Bereich) |
| S6 | Fassadenfarben | gedeckte Töne: weiss, hellgrau, creme, graublau; Putz glatt | Altbauten sehr gelb/orange/lachs gesättigt, dunkelblaue Fenster | 9,54,57,70,72,86–89,96–104 | teils behoben: 82 Adressen in `visual_notes_v3.json`; Rest: Default-Palette entsättigen (`styles.py`) |
| S7 | Fensterläden/Balkone | Läden grün/grau/braun, Glas-/Stahlbalkone | Läden meist rot/grün in Zufallsfarbe, Balkone fehlen bei 50er-Bauten | 42,57,72,96 | teils via Notizen (`laeden`, `balkon`) |
| S8 | Bäume | Sommerlaub (Foto Mai/Juni) | Herbstfarben (gewollt, Oktober) | alle | gewollt |
| S9 | Poller, Veloständer, Motorrad-/Rollerparkplätze | Betonpoller in Reihen, Roller dicht an Fassade, Veloständer an Ecken | fehlen meist | 34,49,57,64,65,86 | Poller/Veloständer behoben (s. u.); Roller als Parkobjekt: Vorschlag `props` |
| S10 | Schilder/Signale | Tafeln (Zone 30, Velo-Route, Parkplatz), Ampelmasten | nur Verbotssignale/Ampeln, keine Hinweistafeln | 10,35,37,99,112 | Vorschlag: `signs` um Zone-30-/P-Tafeln erweitern |
| S11 | Bodenmarkierung | «30»-, «20»-Boden-Zahlen, Velo-Piktogramm, gelbe Kreuze | «ZONE»-Schriftzug teils falsch/abgeschnitten; Piktogramm vorhanden | 43,62,87,97,116 | Vorschlag: Zonenzahl «30» statt «ZONE» |
| S12 | Tramgleise / Fahrleitung | Gleisrillen eingelassen, Fahrleitungen quer | Gleise vorhanden (gut), Fahrleitungen vorhanden | 16,27,67,88,115 | OK |
| S13 | Brücken/Viadukt (Hardbrücke, Bahn) | massive Betonbrüstung, Gehweg unter Hochstrasse | Brüstung/Auflager grob, Kamera landet im Pfeiler | 22,25,45,58,77 | Landmark-Thema, nur dokumentiert |

## Einzelne Orte (Auswahl, Foto → Spiel)

| ID | Ort (ca.) | Abweichung | Aktion |
|---|---|---|---|
| 0 | Pfingstweidstr. (Industriequartier, W) | Glas-Unterstand mit Werbevitrine fehlt; Strasse im Spiel breiter, Platz leer | Unterstand in `fidelity.json` (Kachel -6_4 nicht gebaut) |
| 2 | Hardstrasse | grüner Velostreifen + Hecke/Zaun rechts fehlen | S1 |
| 5 | Förrlibuckstr./Hardbrücke | Hochstrassen-Rampe, Kran; Spiel: zu helle Inseln | S2 |
| 9 | Hardstr. | Betongraue Zeile mit Balkonreihen vs. Spiel beige/Ziegel | S6, Adressen nicht lesbar |
| 12 | Hardplatz Richtung Norden | Ampeln, Walmdach-Wärterhaus links fehlt | dokumentiert |
| 16 | Hardstrasse/Tram | grüner Streifen, Trottoir-Pflanztröge links | S1; Tröge als Vorschlag |
| 22 | Hardbrücke | Brüstung, Panorama | S13 |
| 27 | Hardstrasse/Gleise | Lage sehr gut; Plakatwand + Hochhaus links fehlen/anders | – |
| 29 | Kreuzung Zürich 5 | Fassadenfarben falsch, Ampeln fehlen | S6/S10 |
| 32 | Hohlstr./Strassenecke | Eckhaus weiss mit grünen Läden vs. Spiel hellgrün | S6 (Adressen nicht sicher) |
| 34 | Pfingstw./Baumallee | Poller, Baumscheibe gross vs. kleine Gitter | S9 |
| 35 | Escher-Wyss-Quartier | Ampelmast links gross; Büro Kupferfassade | – |
| 37 | Pfingstweidstr. | Gute Übereinstimmung | – |
| 40 | Hardstr. Tram-Insel | Edelstahl-Abfalleimer, Geländer, grüner Streifen | Abfalleimer (fidelity.json), S1 |
| 42 | Agnesstrasse | Genossenschaftsbau weiss/grüne Läden vs. Spiel rot-lachs | Notizen Agnesstr. 11–22 |
| 43 | Quartierstrasse | «20» am Boden fehlt, Velos/Autos vorhanden | S11 |
| 44 | Kreuzung Quartierstrasse | gut | – |
| 47 | Röntgen-/Hardstr. | Litfasssäule rechts, Büro vs. Plattenbau | dokumentiert |
| 48 | Hardstr. | Fussgängerstreifen gelb ok, Ampel ok | – |
| 49 | Zollstrasse Park | Poller + Veloparkplatz rechts | Poller (fidelity.json) |
| 50 | Hardstrasse Sicht Nord | grüner Streifen, Backsteinhaus | S1 |
| 53 | Hardstr. | Glas-Unterstand (Tram), Baum, Grünstreifen | Unterstand nicht umgesetzt (Position unsicher) |
| 54 | Erismannstr./Kanzleistr. | terrakottabraune Eckhäuser, Rote Storen | Notizen Erismannstr. 44/46, Kanzleistr. 203 |
| 55 | Baumallee | Strasse unter Platanen, grüner Streifen | S1 |
| 57 | Zypressen-/Ernastr. | Roller-Parkplatz, Veloständer, Fassaden blau/creme/weiss | Veloständer + Notizen |
| 58 | Hardbrücke Rampe | Betonrampe | S13 |
| 64 | Europaallee/Lagerstr. | Betonpoller in 2 Reihen, Café-Möblierung | Poller (fidelity.json) |
| 65 | Europaallee | Roller, Poller | S9 |
| 67 | Hardstr./Gleise | Bürobau Glas | – |
| 70 | Pflanzschulstr. | hellblaues Eckhaus mit Balkonen | Notizen Pflanzschulstr. 36/47/49 |
| 71 | Kanzlei | grauer Bürobau links | dokumentiert |
| 72 | Anwandstr. | weisses Haus, Glasbalkone | Notizen |
| 76 | Hardstr. Ampel | gut | – |
| 81 | Hardstr. Baustelle | Baustellen-Wand ok | – |
| 86 | Kern-/Bauhallenstr. | Eckhaus rosa; Veloständer | Notizen + Veloständer |
| 87 | Schreinerstr. | ocker Altbau mit Sockel; «30»-Fläche | Notizen |
| 89 | Feldstrasse | blau/gelb/rosa Altbauten | Notizen (Feldstr. 111/115 vorhanden) |
| 96 | Schimmelstr. | hellgelbe Neubauten | Notizen |
| 98 | Gartenhofstr. | gelbes Eckhaus, Café-Terrasse | Notizen |
| 99 | Ankerstr. | rosabeiges Bürohaus mit Fensterbändern | Notizen |
| 101 | Langstr./Kernstr. | mintgrün + rosa Eckhaus (Weinstube) | Notizen |
| 102 | Nietengasse | türkis/grün/weiss | Notizen |
| 104 | Schöneggstr. | ocker/graublau | Notizen |
| 108/109 | Ottostr. | rosa/cremegelb | Notizen |
| 114 | Werdstr. | graue 60er-Bauten | Notizen |
| 115 | Stauffacherstr. Ecke Badenerstr. | sandsteinfarbenes Eckhaus | Notizen |
| 116 | Stauffacherstr./Rotwandstr. | Rustika-Sandstein, Stübli | Notizen |

Nicht ausgewertet (Nacht/Armaturenbrett/Treppe): 30, 31, 46, 52, 56, 59–61, 74, 77, 79, 80, 90–93, 95, 107, 112.

## Umgesetzt
- `research/buildings/visual_notes_v3.json`: +82 Adressen (Farbe, Material, Stil, Läden, Details) aus `pipeline/photos/fidelity_notes.py`. 8 Adressen hatten schon eine Notiz und blieben unverändert (Feldstr. 115/119, Ankerstr. 61, Hohlstr. 49, Dienerstr. 79/83, Stauffacherstr. 31/35).
- `pipeline/overrides/fidelity.json` → `pipeline/fidelity.py` → `pipeline/overrides/places_detail_fidelity.json` (Poller Europaallee/Zollstr., Unterstand Pfingstweidstr., Abfalleimer Hardstr., 2 Veloständer). Kein Hook in `build_testarea.py` nötig (`places_detail.py` lädt `places_detail*.json` per glob).
- Kacheln neu gebaut: 0_3, -1_3, 0_-2, 2_-5, 3_-4, -2_5 (`logs/fidelity_tiles.log`).

## Vorschläge für einen Komplett-Build / grössere Arbeit
1. Grüne Velostreifen als Strassenbelag (S1): grösster sichtbarer Unterschied, `roadgraph.py`.
2. Trottoir dunkler/glatter, Rinnenband schmaler, Asphalt wärmer (S2–S4): `ground_tex.py`.
3. Default-Fassadenpalette entsättigen (S6) und Balkone für 50er-Bauten.
4. Parkierte Autos in blauer Zone dichter (S5), Roller-/Motorrad-Parkfelder.
5. Hinweistafeln Zone 30/P/Velo (S10) und Bodenzahlen «30»/«20» (S11).
6. Alle 82 neuen Notizen greifen erst nach einem Komplett-Build; bis dahin nur in den 6 neu gebauten Kacheln sichtbar.
