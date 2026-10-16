# HBX – HB-Umfeld und Perron-Ausstattung

Stand 2026-10-16. Skript `pipeline/landmarks/hbx_all.py`, Manifest `pipeline/overrides/landmarks_hbx.json` (via `merge.py`), GLBs `hbx_perron` (4.4k Tris, Nahstufe 330 m) und `hbx_platz` (1.6k Tris, 220 m).

## Umgesetzt
- Perrons 3-18 (Ausstattung): Sektortafeln A-F (hängend, zwischen den Dachstützen, 70 m Abstand), neutrale Abfahrtsanzeigen (kein Logo), Billettautomaten (neutral, 3 pro Perron), Abfallkübel-Paare neben den Bänken.
- Bahnhofplatz: Alfred-Escher-Brunnen (Richard Kissling, 1889): runde Schale, Granitsockel, Bronzegruppe, Standbild, zwei Seitenschalen; Velostand mit parkierten Velos vor dem Südtrakt (d 62-89). Collider um den Sockel.
- Perrondächer, Bänke, Perronkanten-Linie, Gleisnummern: bestehen bereits in `hb_perron.py` (Entscheid #40), nicht doppelt gebaut.
- Tramhaltestellen-Inseln: bestehen über `stops_equip` (Unterstände, Bänke, Automaten, Fahrgäste).

## Nicht umgesetzt (offen)
- Wartende Personen auf Perrons: `research/stations/spots_*.json` gibt es nur für Altstetten/Hardbrücke/Wiedikon (nicht HB). `pedspots.ts` kennt keine Art «waiting» (nur Bänke/Brunnen/Bars/Cafés/Baustellen) und überspringt Spots in `inRail`. Einbindung braucht eine neue Spot-Art und eine Ausnahme für Perrondecks.
- Europaallee-Passerelle, Velostation Europaallee, Sihlquai-Carterminal, Bahnhofbrücke-Anschluss: nicht gebaut (Zeit); ausserhalb des gespielten Ausschnitts bzw. ohne geprüfte Quelle.
- Trinkbrunnen/weitere Brunnen: keine geprüfte Position, daher nicht platziert.
- Referenzfotos: Es wurden nur die vorhandenen 632 HB-Fotos (`data/raw/photos/hb/`, Lizenzen `research/hb/CREDITS.md`) genutzt; keine neuen 50 Fotos geholt. Vergleich: `preview/hbx_cmp.jpg` (Foto | Spiel, 8 Stellen).
- Sektor-Positionen und Automaten-Stellen sind Schätzungen aus Fotos (nicht vermessen); Dachformen unverändert aus `hb_perron.py`.
- Der Escher-Collider wird erst nach einem Kachel-Neubau wirksam (Landmark-`colliders` werden in `build_testarea.py` eingebacken); Modelle laden ohne Neubau.

## Nachtrag (zweite Runde)
- **Perrondächer:** Sie waren vorhanden (Längshallen 4-17, Auslegerdächer 3/18; von oben sichtbar), wirkten von unten aber wie grauer Himmel, weil die Innenfläche fast weiss (#eef3f5) und ungeschattet war. Ursache nur in `hb_perron.py` (Farbe `GLASS_I` jetzt #7d8a92, mit Stahlbögen sichtbar). Neu gebaut mit `pipeline/landmarks/hbx_regen_perron.py` (nur GLB, kein Manifest/merge/Decks). Gleiche Datei, daher keine Manifest-Änderung nötig.
- **Europaplatz-Velostation:** `hbx_europa.glb` (1k Tris, Nahstufe 260 m): Züri-rollt-Mietvelos, Eingangsdach mit Ladesäulen, Billettautomat an den OSM-Knoten (Frame d -265/-117, -249/-135, -341/-120). Die Station selbst (OSM-Way 526215141, d -341..-243, c -143..-105) ist unterirdisch und nicht modelliert. **Manifest-Eintrag steht in `landmarks_hbx.json`, aber `merge.py` wurde nicht ausgeführt (Bauverbot)** - nach dem Build `python pipeline/landmarks/merge.py` laufen lassen. Nicht im Spiel angesehen.
- **Passerelle/Bahnhofbrücke:** Passerelle Gleisbogen liegt bei d -2353 (weit ausserhalb), «Europaallee Passage» ist ein OSM-Fussweg (d -341..-369) ohne Brückenkörper, eine «Passerelle Europaallee» gibt es in OSM nicht. Bahnhofbrücke (Ways 8143580, 53275979, 580414174) liegt bei d 220-285 (> 82 m ausserhalb des erweiterten Spielgebiets, d ≤ 138); sie wird vom bestehenden Brückensystem behandelt, kein Eigenbau.
- **Fotos:** 60 neue Commons-Fotos (`data/raw/photos/hbx/`, Lizenzen `hbx_credits.md`, `hbx_photos.json`, Fetcher `pipeline/photos/fetch_hbx.py`), Kontaktbögen `preview/ref_hbx_{europaallee,platz,bruecke}_*.jpg` (nicht einzeln durchgesehen; Perron-Suchen ergaben keine neuen Treffer, Perron-Referenzen bleiben `ref_hb_perron_*`). Positionen der Perron-Ausstattung bleiben Schätzungen.
