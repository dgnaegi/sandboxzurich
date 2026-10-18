# Frau Gerolds Garten (Geroldstrasse 23) – Landmark

Gartenlokal in Kreis 5 zwischen den Gleisen der Hardbrücke (Nord) und der Geroldstrasse (Süd, Eingang), Freitag-Turm an der SO-Ecke.

## Quellen
- Fotos (nur angesehen): Wikimedia Commons «Frau Gerolds Garten at night 1/2» und «Zürich Frau Gerolds Garten» (CC BY-SA, siehe `research/v3/photos_fgg_commons.json`), Mapillary-Strassenfotos (CC BY-SA 4.0, `research/v3/photos_fgg.json`). Kontaktbogen `preview/fgg_ref.jpg`. Fetch: `pipeline/photos/fetch_fgg.py`.
- Grundstück: OSM way 1409699323 (`landuse=retail`, «Frau Gerolds Garten»), Hauptweg OSM footway 400682255, Zufahrt Geroldstrasse (service way 1167364818). Gerolds Markt: swissBUILDINGS3D ID_6999753E (OSM 211317369).

## Was die Fotos zeigen
Kiesweg als Hauptachse, beidseitig Holzstände und gestapelte Container (türkis, rost, rot, ocker) mit Pflanzen auf den Dächern, Holzdecks und erhöhte Holzterrasse, Pflanzkisten, Sitzgarnituren mit bunten Sonnenschirmen, Lichterketten und Wimpelketten quer über den Weg, Wegweiser (BAR, KÜCHE, GRILL), Kreidetafeln, Schriftzug am Eingang.

## Modell (`k5w3_fgg.py`, `k5w3_fgg_tex.py`)
Kiesfläche auf dem echten Grundstück (ohne Gebäude-Grundrisse), Gerolds Markt als Gebäude mit Glasfront und Schriftfeld, bis zu 9 Container-Stapel, 8 Holzstände, Holzdecks, Terrasse, Tische, Pflanzkisten, Sträucher, 7 Lichter-/Wimpelketten, 3 Wegweiser, Eingangstor mit Namensschild. Eingang von der Geroldstrasse, Weg ohne Hindernisse (nur der Markt-Grundriss ist Kollider). Die zwei früher versteckten Gebäude ausserhalb des Grundstücks (ID_38727667, ID_B9E3EE20) sind wieder normale Kachelgebäude.

## Offen
- Container sind farbige Flächen (keine Fenster-/Türdetails), Dachbepflanzung nur auf dem Markt als Schirme.
- Kiesfarbe und Holzdecks nicht an der Nacht-Beleuchtung geprüft.
