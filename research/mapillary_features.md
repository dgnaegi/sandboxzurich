# Mapillary Map Features als Schilderquelle (Prototyp)

Quelle: Mapillary Graph API `map_features` (Zellen 125 m, Cache `data/raw/mapillary_features/`, Log `logs/mapillary_features.log`), Lizenz CC BY-SA 4.0 (siehe `docs/DATA_SOURCES.md`). Skript `pipeline/mapillary_features.py` (`fetch`, `build`, `compare`). Das API liefert pro Feature `aligned_direction` (Blickrichtung, Kompasswinkel) und die Bildliste (Bestaetigung).
Filter: >= 2 Bilder, `last_seen_at` ab 2022. Zonen 1 + 4. Ausgabe: `pipeline/overrides/mly_signs.json`.

## Features in den Zonen 1 + 4 (alle, vor Filter)
| Typ | Anzahl |
|---|---|
| regulatory / information / warning / complementary | 838 / 518 / 138 / 12 |
| davon letzte Sichtung vor 2022 (verworfen) | 908 (Bilder 2015-2020 dominieren) |
| nur 1 Bild (verworfen) | 15 |
| object--street-light / traffic-light / bench / fire-hydrant (nur gezaehlt) | 2291 / 1821 / 297 / 193 |

## Uebernommen (SSV-Code mit vorhandener Textur), Zonen 1 + 4 zusammen 255
vortritt 60, einfahrt_verboten 34, zone30end 36, speed30 23, halteverbot 22, einbahn 18, radweg 17, zone30 12, fussgaenger 8, fussweg 8, sackgasse 7, speed50 6, stop 2, fahrverbot 2.
Nur gezaehlt (kein Code): roadworks 59, keep-right 55, no-left-turn 32, bicycles-both-ways 30, warning--children 23, shared-path 16, camera 10 u.a.

## Vergleich Zone 4 (Mapillary 168 vs. OSM-abgeleitet 603; Treffer = gleicher Code, <= 8 m)
| Code | Mly | OSM | Treffer | fehlt bei uns | zu viel bei uns |
|---|---|---|---|---|---|
| einbahn | 10 | 134 | 5 | 5 | 129 |
| einfahrt_verboten | 14 | 138 | 1 | 13 | 137 |
| vortritt | 45 | 5 | 1 | 44 | 4 |
| zone30end | 24 | 80 | 4 | 20 | 76 |
| zone30 | 9 | 100 | 0 | 9 | 100 |
| speed30 / speed50 | 13 / 6 | 5 / 8 | 0 / 0 | 13 / 6 | 5 / 8 |
| halteverbot | 11 | 1 | 0 | 11 | 1 |
| radweg / fussweg | 16 / 8 | 0 / 0 | 0 | 24 | 0 |
| fussgaenger | 5 | 30 | 0 | 5 | 30 |
| sackgasse | 5 | 16 | 0 | 5 | 16 |
| stop / fahrverbot | 1 / 1 | 4 / 1 | 0 | 2 | 5 |
| blauzone, begegnung(end) | 0 | 81 | 0 | 0 | 81 |
| Total | 168 | 603 | 11 (6.5 % der Mly) | 157 | 592 |

Ausrichtung: mittlere Abweichung Mly-Blickrichtung zu OSM-Heading bei Treffern 36 Grad, 9 % ueber 90 Grad (Konvention passt, `h = pi/2 - rad(aligned_direction)`).

## Einschaetzung
- Mapillary 2022+ deckt nur Teile ab (Karte `preview/mly_signs_z4.jpg`: Cluster an Hauptachsen, grosse Luecken); die OSM-Ableitung deckt flaechig ab, ist aber lagemaessig geschaetzt. Die 5 % Treffer sagen: die abgeleitete Lage stimmt selten auf 8 m.
- Echter Gewinn: Vortritt (44 fehlen), Velo-/Fussweg, Halteverbot, Tempo 30/50. Ersetzen bei gleichem Code im Umkreis 15 m, sonst additiv.
- Mly-Schilder sind teils Dubletten (gleiches Schild mehrfach erkannt) und nicht geprueft; ohne Review keine Quelle fuer Pflicht-POIs.
