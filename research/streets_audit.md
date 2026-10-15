# Strassen-Audit (Markierungen, Velo, Signalisation)

Referenz: swisstopo SWISSIMAGE 10 cm (OGD), per WMS in `data/raw/ortho/` (`pipeline/ortho.py`); Spiel-Draufsicht via `pipeline/ortho_render.mjs`.
Kontaktbögen: `preview/ortho_compare_NN.jpg` (links Spiel, rechts Luftbild), `*_before_*` = Stand vor der Korrektur. 24 Kontrollpunkte (Liste: `data/build/ortho_points.json`).
Offizielle Daten (CC0, Stadt Zürich): Zonen (T30/Begegnung), signalisierte Geschwindigkeit, Velonetz (Velostreifen mit Richtung), Schulwegübergänge, ausgewertet in `pipeline/streets_rules.py`.

## Abweichungen (vorher) und Korrektur
| Befund | Korrektur |
|---|---|
| Velostreifen-Linien/Mittellinien in Quartierstrassen ohne Markierung (Kreis 4, Zone 30) | Keine Mittel-/Randlinien in T30-Zonen und Begegnungszonen; Mittellinie nur auf klassierten Strassen ausserhalb Zone, nicht auf Tramgleis, nicht in Einmündungen |
| Velostreifen nur aus OSM-Tags (48 km) | Offizielles Velonetz (Streifen mit Richtung) ergänzt: Intervalle je Seite; gelbe Linie unterbrochen vor Einmündungen, Lücke an Seitenstrassen; Piktogramme nach jeder Einmündung und alle 40 m |
| Fussgängerstreifen: Signalanlagen-Querungen fehlten (179 `traffic_signals`+zebra in OSM) | Jetzt gelb gezeichnet; in T30-Zonen/Begegnungszonen keine (ausser signalisiertes T30, Schulweg ≤ 40 m) |
| Haltelinien/Streifen an Ampeln fehlten | Haltelinie (0.5 m) an jedem signalisierten Zufahrtsast, Streifen 1 m dahinter falls keiner kartiert; Geradeaus-Pfeile wenn der Ast gerade weiterführt |
| ZONE-30/Tempo-Schilder nach OSM-`maxspeed` | Aus Zonengrenzen/Tempo-Linien: Zone 30 / Ende Zone 30, Begegnungszone (neu, Schild 20), Tempo 30 / Ende (50) auf signalisierten Strecken; Markierung «ZONE 30» bzw. gemaltes «30» |
| Busspuren ohne Markierung | Gelbe Linie + «BUS»-Schrift (aus `bus:lanes*`, 71 Wege) |

## Offen
- Rote/eingefärbte Velofurten und gelb schraffierte Sperrflächen (z. B. Wiedikon) – brauchen eine Farbe/Layer im Ground-Build (build_testarea.py).
- Abbiegepfeile (nur Geradeaus), Randlinien auf Hauptstrassen, Tramhaltestellen-Inseln, Vortrittslinien.
- Fussgängerstreifen an Knoten ohne OSM-Querung nur bei Ampeln; sonst fehlen einige (OSM-Lücke).
- Strassenbreiten im Spiel teils schmaler als im Luftbild (OSM-Breiten); Kontrollpunkt albisriederplatz: Render-Timeout (nicht ausgewertet).
- Kacheln neu gebaut: 2_-6,4_-6,4_-3,3_-4,2_-8,1_-6,5_0,3_-5,-1_-1,-12_1,-3_-4,1_2,0_1,0_0,4_-7,0_-5,4_-2,-1_-6,1_-8.
