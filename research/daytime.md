# Tag-Nacht-Zyklus

1 Spielminute = 1 Echtsekunde (24 min = 1 Tag). Sonnenstand: Zürich 47.37 N, Deklination 9.5 Grad (Mitte April), solare Zeit (Sonnenaufgang ca. 5:15, Untergang ca. 18:45). Keyframes in `web/src/engine/daytime.ts` (Tabelle `K`), linear interpoliert.

| Zeit | Stimmung | Zenit | Horizont/Nebel | Sonne (Intensität) | Hemi | Exposure |
|---|---|---|---|---|---|---|
| 0:00-4:30 | blaue Nacht, Sterne, Mond | 0a1236 | 2a3a70 | Mond 7f93d0 (0.5) | 3d4f8a/151a30, 0.75 | 1.25 |
| 5:25 | pinke Dämmerung | 2a3a78 | e08a9a | ff9a80 (1.0) | 8a8ac0 | 1.15 |
| 6:30 | goldener Morgen | 4f7fc8 | f7c08a | ffc890 (2.6) | d8d8f0 | 1.05 |
| 8:30-16:00 | Tag | 3f74c4 | a9cdee | fff0dc (3.6) | cfe0ff/7c7a68, 1.5 | 1.0 |
| 17:36 | goldener Abend (Startwert) | 3f74c4 | f4b98e | ffd9a8 (3.2) | cfe0ff | 1.05 |
| 18:30 | pinker Sonnenuntergang | 3a4f9a | f08a7a | ff8a5a (2.0) | b8a0c8 | 1.1 |
| 19:18 | Dämmerung violett | 1a2a66 | 8a5a90 | d06a70 (0.5) | 6a70b0 | 1.2 |
| 20:24+ | blaue Nacht | wie 0:00 | | | | 1.25 |

Nachtfaktor `night` (0..1; 0.2 um 18:30, 0.7 um 19:18, 1 ab 20:24): Fenster gehen schrittweise an (Zelle an, wenn Hash < 0.35*night), Ladenfronten (Ebenen shop0-7) leuchten mit Eigenfarbe, Laternen (Vertexfarbe fff3c8) emissiv. Schatten: Sonnenlicht-Gewicht > 0.15, sonst Shadow-Map eingefroren (`autoUpdate=false`) und `shadow.intensity` ausgeblendet. 4 PointLights (warm, nur PC) folgen dem Spieler ab night > 0.35.
