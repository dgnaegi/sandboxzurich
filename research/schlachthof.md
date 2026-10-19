# Schlachthof Zürich (Herdernstrasse) – Landmark

Städtischer Schlachthof, 1909, Kreis 4 Hard, direkt nordöstlich des Letzigrund-Stadions. Im Spielgebiet (Mitte ca. -860, 40; Kacheln -5_-1, -5_0, -4_-1, -4_0).

## Quellen
- Fotos (nur angesehen, nichts übernommen): Wikimedia Commons «Schlachthof Zürich» (Roland zh, CC BY-SA 3.0, 2011-08-16; Rudolf H. Boettcher, CC BY-SA 4.0, «Westportal», «in Zürich-Aussersihl», 2025; ETH-Bildarchiv/BAZ historische Aufnahmen). Kontaktbogen: `preview/schlachthof_ref.jpg`. Mapillary/Panoramax-Strassenfotos: `research/v3/photos_schlachthof.json`.
- Volumen und Dachhöhen: swissBUILDINGS3D (ID_B529B079 Hallen, ID_73904D69 Nordblock, ID_9B116DAC Restaurant, ID_45AE7D98 Kamin) und SWISSIMAGE (`pipeline/landmarks/schlachthof_plan.py`).
- Google nur zur Inspiration, nichts verwendet.

## Was das Foto zeigt (und im Modell steckt)
- Gelber Klinker, rote Backsteinbögen und -bänder, graue Steinsockel/-gesimse.
- Tonnendach-Halle (Zink, flach-segmentbogig, 24 m Spannweite, First 24 m über Terrain) über Hallenschiffen mit Rundbogenfenstern; zwei Portal-Giebel mit grossem Halbkreis-Bogen (Steinring, roter Backsteinring, Glaswand mit Sprossen), drei Torbögen, Eckpfeiler mit Spitzdach. Die Seite mit Uhr und Schriftfeld «STÄDTISCHER SCHLACHTHOF 1909» ist das SÜDOST-Portal (Runde 2 korrigiert: Foto 7/10 zeigt den offenen Platz, der Kamin steht links weit dahinter; Foto 9 zeigt das Nordwest-Portal mit dem Kamin rechts daneben, ohne Uhr). Nordwest-Seite schlichter (Rundfenster statt Uhr), «jede Seite ein bisschen anders».
- Fassade (Runde 2): hellgelblich-cremer Klinker mit hellgrauen Fugen (512-px-Textur, `schlachthof_tex.brick_wall`), rote Backsteinbänder und Pilasterstreifen im 4-m-Raster (wie Foto 3); Restaurant mit gleicher Textur ohne rote Bänder.
- Backstein-Kamin 48 m (rot, helle Bänder) rechts vom Westportal (Position aus swissBUILDINGS3D).
- Restaurant Schlachthof (ID_E1E2306E): Walmdach (Ziegel, Wandflächen jetzt als echte Vierecke aus den 3D-Daten, damit keine Giebelplatten über die Traufe stehen), geschwungener Mittelgiebel (Steinrand, drei Fenster), Schriftfeld «RESTAURANT SCHLACHTHOF» über dem Eingang, Dachgauben auf allen langen Fronten, zwei Backstein-Kamine auf dem First (`schlachthof_rest.py`). Steileres Dach als in den Daten nicht umgesetzt (Dachflächen bleiben swissBUILDINGS3D).
- Haus bei ID_9B116DAC (SE-Portal, ca. 45 m vom Portal entfernt, rund 17 m neben der Portalachse): echt, in swissBUILDINGS3D und SWISSIMAGE (orange Ziegeldach) belegt. Es ist KEIN Pförtnerhaus vor dem Portal, nur aus der Achse sieht es so aus. Wird jetzt schlicht (Fenster ohne Läden, keine Restaurant-Tür) gezeichnet.

## Modell
`pipeline/landmarks/schlachthof.py` (+ `schlachthof_tex.py`): Wände und Dächer pro Polygon aus swissBUILDINGS3D, Ziegeltextur und Fenster/Tor-Decals (Alpha), Tonnendach und Portale nach Foto. Registriert in `pipeline/overrides/landmarks_schlachthof.json` (`hide_ids`, damit die Grundrisse Kollider bleiben).

## Offen
- Innenraum der Tore nur dunkel (nicht begehbar).
- Fassadenfarben der Nordblöcke (73904D69): GESCHÄTZT. Die Mapillary-/Panoramax-Fotos in data/raw/photos/schlachthof (schl_nord, schl_mitte, geprüft Runde 4) zeigen sie nicht, Commons-Fotos nur die Hauptportale. Darum gleiche Klinker-Sprache wie die Hallen.
- Photovoltaik- und Gründächer nur als Flächenfarbe.

## Runde 4
- Backstein: 40 Schichten, dunklere Fugen, stärkere Farbvariation inkl. dunkler Klinker, rote Bänder (6 Schichten pro 4 m) und Pilaster kräftiger; Sockel dunkelgrau 2 m mit Steinleiste (`schlachthof_tex.brick_wall`).
- Tore: echte Öffnungen im Portal mit 0.8 m Laibung (Stein), Haupttor mit zwei Stahlflügeln und offener Mitte mit Blick in eine einfache Innenhalle (Boden, Wände, Säulen, Tonnen-Untersicht, helles Ende); Seitentore geschlossen (Holz am NW, Stahl am SE) (`schlachthof_gates.py`).
- Restaurant: Dachhöhe über der Traufe x1.5 (Wände und Dachflächen konsistent), Gauben und Kamine passend; PV und Gründächer weiterhin nur Flächenfarbe.
- Kamin: schlank, verjüngt (3.1 auf 1.8 m), Backsteintextur, Kopfkranz.


## Bestätigung User 2026-10-19
- Nordblöcke: Backstein (User vor Ort). Die bisher geschätzte Backstein-Sprache ist damit belegt.
