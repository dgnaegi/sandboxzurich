# LiDAR-Pilot: Ergebnis (2026-10-21)

Stand: nur Area (a) Langstrassen-Unterführung ist gemessen. Die Kacheln für (b) Hardbrücke/Sihlpost/Gessnerbrücke und (c) Velotunnel-Portal fehlen, weil die Bestellung vom Permission-System blockiert wurde (siehe README). Benötigt: `2681000_1248500`, `2681500_1248500` (Hardbrücke Süd), `2682500_1247500`, `2682500_1248000` (Gessnerbrücke/Sihlpost/Velotunnel). Danach laufen die gleichen Skripte.

Sheet: `preview/lidar_pilot.jpg`.

## Messung Area (a), 157 x 206 m, 1.05 Mio. Punkte
- Boden (Klasse 2, 1-m-Raster) minus Spiel-Boden (`audit_float.ground`): Median 0.000 m; 83.8 % der Zellen innerhalb ±0.25 m, 86 % ±0.5 m. Rest: 11.6 % LiDAR höher als 1 m = Bahnbrücke/Dämme über der Unterführung, wo das Spiel den Boden bewusst auf Strassenniveau abgesenkt hat; nur 0.1 % niedriger als -1 m.
- Unterführungs-Rampen: LiDAR-Boden gegen `terrain_cuts`-Profil an 20 Stationen: Abweichung 0.0 bis 0.3 m (Rampen unten bei s = -3 / +99: -7.9 / -8.5 gegen -8.2 / -8.4). Das Profil ist also bereits gut; LiDAR bestätigt es.
- Im Tunnelteil (s = 0..94) sieht LiDAR nur die Oberseite der Bahnbrücke (-2.2 .. -2.9 m Spielhöhe, Klasse 2), nicht den Boden darunter. Boden dort ist nicht messbar, nur Rampenden und Portal (Lichte Höhe = Deckenoberkante minus Fahrbahn minus Plattendicke, Plattendicke unbekannt).
- Querprofile: Fahrbahn 12–14 m breit, seitlicher Streifen 1.1 bis 1.9 m höher (Stützmauer/Trottoir) – sichtbar und messbar.
- Bäume/Masten: Klasse 5 (hohe Vegetation) 21.6 k Punkte, Klasse 15 (Leitungen/Masten) 14.2 k Punkte in Area a: Baumkronenhöhe und -position und Mastpositionen sind direkt ableitbar (nicht verglichen, siehe Plan).
- Intensität: weisse Fahrbahnmarkierungen (Spurtrennlinien, Haltelinien, Zebra) sind bei 20 cm Raster deutlich sichtbar, gelbe Linien kaum (schwach, nahe Asphalt-Rauschen), Autos erscheinen als Lücken. Bei 10 cm sind nur ~16 % der Zellen gefüllt (Streifenmuster), daher 20–25 cm das Minimum. Brauchbar als Plausibilitätsprüfung/Registrierung der weissen Markierungen (Lage auf ~0.1–0.2 m), nicht als Ersatz der Vektorlinien; Farbe fehlt.
- Bridges/Rampen/Velotunnel (b, c): nicht gemessen (siehe oben).

## Was LiDAR ersetzen kann
| Thema | Urteil |
|---|---|
| Brückendecks, Rampenprofile (bridges.py) | Ja, als Messwert: Oberflächenhöhe entlang der Achse (Profil-Sampler `lidar.profile`, Median Klasse 17 und «höchste Nicht-Vegetation»). Aber Bahnbrücken sind teils Klasse 2: Höhe per Achse + Radius ausschneiden statt auf Klasse vertrauen. Unterseiten (Lichte Höhe) nicht sichtbar. |
| Unterführungsböden (terrain_cuts, underpass_infer) | Rampen/Portale ja; unter dem Deckel nein (Interpolation zwischen Portalen bleibt). |
| Gelände unter Gebäuden/Brücken (DTM-Interpolation) | Teilweise: Klasse 2 fehlt dort ebenfalls. Gewinn nur an Brückenrändern/Kanten. |
| Strassenglättung (road_height) | Ja, als Referenz/Validierung (Stufen von Trottoir zu Fahrbahn erkennbar); echte Randsteinhöhe aus 18-cm-Punktabstand nur grob (±5 cm Rauschen). |
| Randstein einheitlich | Fahrbahn-gegen-Trottoir-Stufe pro Strasse als Median messbar; pro Kante zu verrauscht. |
| Bäume, Masten | Ja: Baum-Positionen/Höhen/Kronenradius aus Klasse 3–5 (Lokale Maxima), Masten aus Klasse 15. |
| Markierungen | Nur weiss, nur Prüfung. |
| Gebäudehöhen/Dach | Ja (Klasse 6), ausserhalb dieser Anfrage. |

## Aufwand Gesamtgebiet
Spielgebiet grob 3 x 3 km (ca. 8 km2, Kreise 3/4/5/9; Zahl aus playarea.json prüfen) = ca. 16 Kacheln à 36 MB = ~0.6 GB LAZ (143 MB/km2). Die Bestellung ist auf 4 km2 begrenzt, also 2–4 Bestellungen. Laufzeit Dekodierung laspy/lazrs: ~1.3 s pro 1 Mio. Punkte gefiltert, ca. 10 s pro Kachel; Raster-Aufbau wenige Sekunden. Cache als npz oder 0.5-m-Rasterdateien (DSM/DTM/Klasse) ~ 20 MB gesamt.

## Integrationsplan
1. `pipeline/lidar_cache.py`: Kacheln -> pro 200-m-Spielkachel Raster 0.5 m (ground, top, bridge, class mask) in `data/build/lidar/` (reproduzierbar, nicht im Repo).
2. bridges.py: Deck-z je Stützpunkt = LiDAR-Profil (Median entlang Achse, ±halbe Breite), Rampenneigung dann gemessen statt Regel; Regel bleibt Fallback wo LiDAR fehlt oder Fahrzeuge/Bäume stören.
3. terrain_cuts/underpass_infer: Rampenenden und Portalhöhen aus LiDAR automatisch, Tunnel mittendrin interpolieren.
4. road_height: LiDAR-Boden als Zielhöhe/Validierung (Abweichungsbericht in audit_float).
5. props/cityprops: Bäume und Masten aus Klassen 3–5/15 zur Ergänzung/Prüfung der OSM-Bäume.
6. markings: Intensitätsraster nur als Audit neben `markings_plaus`.

## Risiken
- Stand 2021/22 (Baustellen, neue Brücken, später gebaut ändern sich), Autos auf der Strasse (Klasse 1/6 oder Loch), Rauschen ±5 cm, Brücken teils als Boden klassiert, Unterseiten nicht messbar, Höhenbezug 3.06 m Shift nicht vergessen, Wasser/Glas liefert Lücken, Streifenmuster bei Intensität.
- Download ist nur über Bestellung möglich; Potree-Kopie unvollständig.
