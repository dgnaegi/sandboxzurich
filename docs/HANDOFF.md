# Handoff

Wird am Ende jedes Arbeitsschritts überschrieben. Eine neue Session liest das zuerst.

## Stand (2026-10-14)
- M0 erledigt: Projekt in `/Users/danielgnagi/gtazurich`, Git-Repo, Doku, WTFPL-Lizenz, OSM-Bestand (`research/osm_stats.md`).
- Overpass-Helfer mit Mirror-Fallback: `pipeline/overpass.py`. Kreisgrenzen: `research/kreise_poly_simplified.json` (Kreis 5 heisst in OSM «Industriequartier»).
- Python-Umgebung: `.venv` (`requirements.txt`).
- Noch kein Spiel-Code.

## Nächster Schritt: M1 – Karte und Herumlaufen
1. Testgebiet Langstrasse/Helvetiaplatz (ca. 600×600 m) komplett durch die Pipeline in den Browser bringen, begehbar auf Handy und PC. **Erst danach skalieren.**
2. Rohdaten nach `data/raw/` laden: OSM für die BBox aller vier Kreise (einmal, gecacht), swissBUILDINGS3D, swissALTI3D, Velonetzplanung der Stadt Zürich (opendata.swiss, Datensatz «velonetzplanung»).
3. Die Reel-Skripte in `../gta6/src/` als Vorlage nutzen, nicht verändern.

## Offene Punkte
- Push auf GitHub (`dgnaegi/gtazurich`, öffentlich): wartet auf `gh auth login` des Users.
- Hosting/Scalingo: separater Schritt, später.
- Quests, Wahlprogramm, Einwilligungen der Kandidierenden: werden später mit dem User geklärt.

## Letzte Session
- 2026-10-14: Struktur, OSM-Bestand, Umzug nach `gtazurich`, Lizenz.
