# Schlachthof Zürich (Herdernstrasse) – Landmark

Städtischer Schlachthof, 1909, Kreis 4 Hard, direkt nordöstlich des Letzigrund-Stadions. Im Spielgebiet (Mitte ca. -860, 40; Kacheln -5_-1, -5_0, -4_-1, -4_0).

## Quellen
- Fotos (nur angesehen, nichts übernommen): Wikimedia Commons «Schlachthof Zürich» (Roland zh, CC BY-SA 3.0, 2011-08-16; Rudolf H. Boettcher, CC BY-SA 4.0, «Westportal», «in Zürich-Aussersihl», 2025; ETH-Bildarchiv/BAZ historische Aufnahmen). Kontaktbogen: `preview/schlachthof_ref.jpg`. Mapillary/Panoramax-Strassenfotos: `research/v3/photos_schlachthof.json`.
- Volumen und Dachhöhen: swissBUILDINGS3D (ID_B529B079 Hallen, ID_73904D69 Nordblock, ID_9B116DAC Restaurant, ID_45AE7D98 Kamin) und SWISSIMAGE (`pipeline/landmarks/schlachthof_plan.py`).
- Google nur zur Inspiration, nichts verwendet.

## Was das Foto zeigt (und im Modell steckt)
- Gelber Klinker, rote Backsteinbögen und -bänder, graue Steinsockel/-gesimse.
- Tonnendach-Halle (Zink, flach-segmentbogig, 24 m Spannweite, First 24 m über Terrain) über Hallenschiffen mit Rundbogenfenstern; zwei Portal-Giebel mit grossem Halbkreis-Bogen (Steinring, roter Backsteinring, Glaswand mit Sprossen), drei Torbögen, Eckpfeiler mit Spitzdach. Nordwest-Seite mit Uhr und Schriftfeld «STÄDTISCHER SCHLACHTHOF 1909», Südost-Seite schlichter (ohne Uhr), «jede Seite ein bisschen anders».
- Backstein-Kamin 48 m (rot, helle Bänder) rechts vom Westportal (Position aus swissBUILDINGS3D).
- Restaurant Schlachthof: Walmdach (Ziegel), gelber Verputz, grüne Fensterläden, Rundbogenfenster im EG, Schriftzug.

## Modell
`pipeline/landmarks/schlachthof.py` (+ `schlachthof_tex.py`): Wände und Dächer pro Polygon aus swissBUILDINGS3D, Ziegeltextur und Fenster/Tor-Decals (Alpha), Tonnendach und Portale nach Foto. Registriert in `pipeline/overrides/landmarks_schlachthof.json` (`hide_ids`, damit die Grundrisse Kollider bleiben).

## Offen
- Innenraum der Tore nur dunkel (nicht begehbar).
- Fassadenfarben der Nordblöcke (73904D69) nicht belegt, daher gleiche Backstein-Sprache.
- Photovoltaik- und Gründächer nur als Flächenfarbe.
