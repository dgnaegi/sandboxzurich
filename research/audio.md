# Audio: Quellen und Lizenzen

Alle Töne sind prozedural in WebAudio synthetisiert (`web/src/engine/audio.ts`, `audio_amb.ts`). Es gibt keine Samples
und keine Fremdquellen, also keine Lizenzfragen. Einzige Datei: `web/public/audio/soundmap.json` (ca. 56 KB), erzeugt von
`pipeline/soundmap.py` aus `vec.json` (OSM, ODbL). Sie wird erst nach der ersten Interaktion geladen.

Schichten: Stadtbrummen (Brownnoise), Verkehr (Distanz zu Hauptstrassen, OSM-Klassen 0-3), Vorbeifahrten, Stimmengewirr
(synthetisierte Silbenfolgen; Plätze, Strassen, Passantendichte), Wind und Blätter (Parks), Vögel (tags, Parks),
Tram-Rollen und Kurvenquietschen, Kirchenglocken zur vollen Stunde (<320 m von einer Kirche, OSM-POI), ferne Velo-Klingel.
