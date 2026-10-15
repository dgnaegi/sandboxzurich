# visual_notes_v2: Fassaden-Notizen Spielgebiet (Kreis 3/4/5/9)

Stand 2026-10-15. Ergaenzt `visual_notes.json` (v1, Langstrasse-Testgebiet); `pipeline/visual_overrides.py` liest beide (v1 gewinnt bei Doppelungen).

## Methodik
1. Adressen: `data/build/gwr_kreise.json` (GWR: Strasse, Nr., Baujahr, Geschosse, lokale x/y).
2. Fotos: `research/photos/by_tile.json` (807 geotaggte Panoramax/Commons-Bilder). Pro Foto die 1-4 naechsten Adressen im Blickkegel (+-38 Grad, <= 50 m; ohne Heading die 3 naechsten) bestimmt; zweiter Durchgang fuer 50-95 m Fernsicht (+-30 Grad).
3. Kontaktboegen (8 Fotos, 1600 px, Nummer + Kandidaten-Adressen) angesehen; pro sichtbarem Gebaeude Putzfarbe (Wort aus `COLOURS` in visual_overrides.py), Stil und Besonderheiten notiert und der passendsten Kandidatenadresse zugeordnet. Fotos ohne Gebaeude (Strasse, Zug, Innenraeume, Nacht, Portraits) uebersprungen.
4. Jeder Eintrag haengt GWR-Baujahr/Geschosse an. Google-Bilder wurden nicht verwendet.

## Abdeckung
- 746 neue Adressen (keine Ueberschneidung mit v1).
  - 423 direkt aus Foto (Farbe + Stil + Details); 323 "Nachbar im gleichen Strassenzug": nur Stil/Epoche, aus Foto-Adresse uebernommen, gleiche Strasse, GWR-Baujahr +-6 Jahre, im Blickkegel <= 75 m. Keine Farbe (Wort "Farbe offen").
  - Via visual_overrides.load(): 549 mit Tint, 571 mit Stil.
- Schwerpunkt: Hohlstrasse, Badenerstrasse (Albisrieden-Altstetten), Hardturmstrasse/Escher-Wyss (Kreis 5), Eugen-Huber-/Bachmatt-/Bullinger-/Albisriederstrasse (Kreis 9/4 West), Josef-/Limmat-/Austrasse (Kreis 5), Weststrasse/Aemtlerstrasse (Kreis 3).
- Nur 483 von 807 Fotos hatten Gebaeude-Kandidaten; viele Fotos zeigen nur Strasse/Himmel/Zuege. Rund 125 Fotos (Fernsicht, 50-95 m) wurden nur teilweise gesichtet.

## Unsicherheiten
- Zuordnung Foto -> Adresse ist geometrisch (Standort + Heading); bei Fotos ohne Heading und bei Eckhaeusern kann die Nachbaradresse gemeint sein. Schwache Faelle tragen "(unsicher)".
- Farben aus verkleinerten Bildern, wechselndes Licht: Pastelltoene (rosa/lachs/orange/ocker) sind verwechselbar.
- Geschosszahlen im Text aus dem Foto geschaetzt; massgeblich ist GWR im Anhang.
- Style-only-Nachbarn sind eine Annahme (gleiche Epoche = gleicher Stil), keine Beobachtung.
- Ziel 600 echt fotografierte Adressen nicht erreicht (423); Rest als Stil-Uebernahme.
