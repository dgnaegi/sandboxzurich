# Musik (Hintergrund, leise, abschaltbar)

Alle Tracks: instrumental, via Wikimedia Commons (Lizenzfeld in der Commons-API geprüft), heruntergeladen am 2026-10-16.
Bearbeitung: Normalisierung auf -16 LUFS, Fade-in/out, ggf. gekürzt, AAC 96 kbps (.m4a) in `web/public/audio/music/` (gesamt ca. 11.7 MB). Nur .m4a (AAC): wird von Safari/iOS, Chrome, Firefox und Edge abgespielt, daher kein zweites Format (Budget).
Pflicht-Nennung bei CC BY: Urheber:in, Titel, Lizenz, Link, Hinweis auf Änderungen. Steht in Credits (index.html) und README.

| Datei | Titel | Künstler:in | Quelle | Lizenz |
|---|---|---|---|---|
| audionautix-hiphop-no-vocal | Hip Hop 1 No Vocal | Jason Shaw (audionautix.com) | https://commons.wikimedia.org/wiki/File:Audionautix-com-ccby-hiphopnovocal.mp3 | CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ (Credit: «music by audionautix.com») |
| audionautix-pool | Pool (Trip-Hop) | Jason Shaw (audionautix.com) | https://commons.wikimedia.org/wiki/File:Audionautix-com-ccby-pool.mp3 | CC BY 3.0 |
| nfaom-boom-bap | Boom bap instrumental | Nfaom loor | https://commons.wikimedia.org/wiki/File:Boom_bap_instrumental.wav | CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ |
| luode-hiphop-b-minor | Hip Hop In B Minor (gekürzt auf 3:30) | Antti Luode | https://commons.wikimedia.org/wiki/File:Hip_Hop_In_B_Minor_(Antti_Luode).mp3 | CC BY 3.0 |
| luode-hop-hip-beat | Hop Hip Beat (gekürzt auf 3:09) | Antti Luode | https://commons.wikimedia.org/wiki/File:Hop_Hip_Beat_(Antti_Luode).mp3 | CC BY 3.0 |

Hinweise
- Gehört nicht angehört (kein Audio-Review möglich); «No Vocal»/«instrumental» laut Titel/Beschreibung. Der User sollte kurz reinhören.
- Nicht verwendet: «Hip Hop 1» (Audionautix, mit Gesang), CC BY-SA-Tracks (Share-Alike vermieden).
- Technik: `web/src/engine/audio_music.ts`; Streaming erst nach erster Geste (+1.5 s), nicht im Startbudget.
