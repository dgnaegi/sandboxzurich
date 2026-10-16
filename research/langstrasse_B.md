# Langstrasse Sued (langB): Unterfuehrung bis Helvetiaplatz/Stauffacher

Methode: Panoramax/Mapillary-360-Panoramen (CC BY-SA 4.0) per Skript frontal auf Laden und Haus gecroppt, von Hand gelesen (nur Fakten: Farben, Schilder, Markisen). Keine Bilder im Spiel, keine Logos, Namen als freie Schrift.
- `pipeline/photos/langB_fetch.py` (137 Venues, 307 Ausschnitte), `langB_entrances.py` + `langB_fetch_entr.py` (GWR-Eingaenge, 141 Adressen, 265 Ausschnitte), Bilder in `data/raw/photos/langstrasse_b/` (via shops_r2-Cache).
- Kontaktbogen: `preview/ref_langB_*.jpg`; Quellen je Venue in `research/shops_v3/photos_langB*.json`.
- Annotationen: `research/shops_v3/annotations_langB.jsonl` (24 Bars/Clubs/Imbisse neu, per `langB_apply.py` in shops_v3.json), Haus-Notizen `research/buildings/notes_raw_langB_001.tsv` (32 Adressen).
- Landmarks: `pipeline/landmarks/langB_all.py` (16 Haeuser: Rothaus, Rossi, Lambada, Diamond, Fat Tony, Klaus, Hungry Duck/Eventhaus, Blackout, Milano, Sudaka, Gotthard, Langstrasse 104/20, Dienerstrasse 40, Negresco, Gambrinus, Zwinglistrasse 37) -> `pipeline/overrides/landmarks_langB.json`.
- Unsicher: Klaus-Schildfarbe (geschaetzt), Sudaka-/Milano-Fassaden grob. Nachts: Leuchtschriften (Glow) in Lambada gold, Diamond blau, Negresco magenta, Fat Tony orange.
- Nicht abgedeckt: Stauffacher-Ende (Badenerstrasse) nur Venue-Annotationen; Fotos dort schlecht.
