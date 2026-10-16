# Ideen: Spielgefühl und Spieldesign (ohne Quests)

Stand 2026-10-16. Grundlage: CLAUDE.md, VISION, QUESTS, QA_REVIEW, HANDOFF und ein Testlauf gegen die Live-URL (PC 1280x720, Handy 844x390; Screenshots `preview/ideas_gameplay_*.jpg`).

**Beobachtungen vom Testlauf.** Spielstart auf dem Helvetiaplatz neben einem Tram, nur eine graue Zeile unten («WASD laufen ...») als Hinweis, Geld (CHF 312.40) ohne erkennbaren Zweck, Radar oben links. Es gibt schon 595 Anekdoten (`anecdotes.json`, werden beim Vorbeigehen eingeblendet), Tageszeit/Uhr, Velos, Mopeds, Fahrzeuge, Spielplätze, Ambience und Musik. Was fehlt, ist ein Grund, die Welt anzufassen: Es gibt kaum Rückmeldung auf Handlungen (Geräusch, Zahl, Belohnung) und kein sichtbares «Ich habe schon X von Y entdeckt».

Aufwand: S = unter 1 Tag, M = 1–3 Tage, L = Woche+. Risiko: Performance (Perf), Inhalt (Ton/Faktenlage), Technik.

## Top 10 (Wirkung / Aufwand)
| Rang | # | Idee | Aufwand |
|---|---|---|---|
| 1 | 1 | Erste-60-Sekunden-Führung: Spawn aufs Trottoir, ein Ziel-Pfeil, drei Mikro-Hinweise | S |
| 2 | 11 | Kiez-Karte aufdecken (Nebel des Nichtwissens, Quartiere in %) | M |
| 3 | 12 | Sammelalbum «Züri-Inventar» (Anekdoten, Brunnen, Läden) mit Zähler | S |
| 4 | 16 | Fotomodus mit Filtern, Rahmen, Teilen | M |
| 5 | 7 | Velo-Tricks: Bunny-Hop, Wheelie, Combo-Zähler | M |
| 6 | 19 | Tram mitfahren (Passagier-Kamera, Haltestellenansage) | M |
| 7 | 4 | Hupen/Klingeln/Rufen mit Reaktion der Leute | S |
| 8 | 22 | Wetter: Regen, Pfützen, Regenschirme, Sonnenuntergangs-Moment | M |
| 9 | 14 | Postkarten-Teilen mit Ortsstempel (Bild + Link) | M |
| 10 | 24 | Handy-Komfort: Kontext-Knopf, Einhand-Modus, Auto-Rennen | S |

---

## A. Erste 60 Sekunden (Onboarding)

### 1. Erste-60-Sekunden-Führung
Spawn immer auf dem Trottoir, Kamera schaut kurz auf die Figur, dann Schwenk. Ein dezenter goldener Pfeil zeigt zum nächsten «Aha»-Ort (Brunnen, Tram-Haltestelle, Velo), drei Mikro-Hinweise erscheinen nur, wenn die Aktion noch nicht gemacht wurde («Tippe/Drücke E beim Velo», «Rennen», «Karte»). Danach nie wieder.
*Warum Spass:* Die erste Aktion klappt in 10 s, es gibt sofort ein Erfolgsgefühl. *Aufwand:* S. *Risiko:* gering (Hinweise nicht nerven). *Systeme:* `ui/help.ts`, `player/spawn.ts`, neues `ui/hints.ts`, localStorage-Flag.

### 2. «Erster Tag in Züri»-Willkommens-Anekdote
Ein NPC (erfunden) spricht dich beim Start an und gibt einen Satz Humor statt Tutorial («Du bisch neu? Tram hät Vortritt, immer.»). Kann weggetippt werden.
*Warum:* Ton und Stadtgefühl in 5 Sekunden, passt zum Reel-Humor. *Aufwand:* S. *Risiko:* Inhalt (Texte nach CONTENT_GUIDELINES, Platzhalter markieren). *Systeme:* `anecdotes.ts`, `ui/`.

### 3. Ladebildschirm mit Tipps und Wusstest-du-Karten
Während des Ladens wechseln Kurztipps und Quartier-Fakten (nur mit Quelle in `research/facts.md`). Zeigt auch, was die Steuerung kann.
*Warum:* Wartezeit wird Inhalt, senkt Absprungrate. *Aufwand:* S. *Risiko:* Fakten-Quelle nötig. *Systeme:* `ui/loading.ts`, `research/facts.md`.

## B. Spontan tun: Spielplatz-Momente

### 4. Hupen, Klingeln, Rufen mit Reaktion
Taste/Button löst je nach Zustand Velo-Klingel, Auto-Hupe oder «Hoi!» aus. Passanten drehen den Kopf, winken, weichen aus, manche rufen zurück («Fahr nöd so schnell!»). Kein Schaden an Menschen.
*Warum:* Direkte Reaktion der Welt, sofort lustig (Goose-Game-Prinzip: ein Knopf, viele Antworten). *Aufwand:* S–M. *Risiko:* Humans-Animationsclips müssen existieren. *Systeme:* `world/humans.ts`, `pedestrians.ts`, `audio.ts`, `input/actions.ts`.

### 5. Winken, Tanzen, Hinsetzen (Emote-Rad)
Radiales Menü: winken, tanzen, hinsetzen auf Bänken, Kaffee trinken, Fotopose. Mocap-Clips sind vorhanden. NPCs in der Nähe machen manchmal mit (kleine Menschenansammlung).
*Warum:* Ausdruck und Screenshot-Material; Social-Media-tauglich. *Aufwand:* M. *Risiko:* Clip-Qualität. *Systeme:* `world/humankit.ts`, `player/player.ts`, UI-Radial.

### 6. Pingpong, Boccia und Schach am Brunnen
An Orten mit echten Tischen/Plätzen (Josefwiese, Helvetiaplatz, Kasernenareal) startet bei Annäherung ein 30-s-Minispiel: Pingpong als Timing-Tap, Boccia-Wurf (Kraft/Winkel, Reel-Anspielung «Boccia-Grosis»), Schach nur als Deko. Highscore lokal.
*Warum:* Kleine Pausen im Wandern, wiedererkennbarer Quartier-Gag. *Aufwand:* M je Spiel. *Risiko:* Orte müssen Quellen haben (OSM `leisure=pitch/table_tennis`). *Systeme:* neues `gameplay/minigames/`, `world/props.ts`, Daten aus Pipeline.

### 7. Velo-Tricks und Combos
Bunny-Hop, Wheelie, Bordstein-Hüpfer, kleine Rampen (Treppen-Rampen, Skatespots). Combo-Zähler mit Punkten («Drift-Stil, 3 Tricks»). Stürze bleiben comichaft ohne Verletzung (existiert, #38).
*Warum:* Das Velo ist Kern-Fortbewegung und braucht Skill-Decke (Jet-Set-Radio-Gefühl). *Aufwand:* M. *Risiko:* Physik-Feintuning, Handy-Bedienung (siehe 24). *Systeme:* `player/vehicle_player.ts`, `world/ridepose.ts`, `gameplay/velo.ts`.

### 8. Graffiti-Sprayen auf Zeit (nur erlaubte Flächen)
An markierten «Legal Walls» (z.B. Wildplakat-Flächen, Bauzäune) sprüht man ein kleines Muster nach (Tippfolge/Strich). Ergebnis bleibt als Decal. Nur freigegebene Wände, nie echte Gebäude oder echte Tags.
*Warum:* Jet-Set-Radio-Feeling, kreativ und wirkungsvoll fürs Teilen. *Aufwand:* M. *Risiko:* Inhalt (Sachbeschädigung-Lesart, vgl. CONTENT_GUIDELINES «Offener Entscheid»), Perf bei vielen Decals. *Systeme:* `world/decals.ts`, UI.

### 9. Leute ansprechen: Mini-Dialoge
Passanten haben je eine Mini-Zeile (Berufsrolle: Bau, Büro, Kurier). Antippen/E gibt einen Satz Quartierwitz oder Tipp. Wiederholt sich nicht in 10 Min.
*Warum:* Macht NPCs zu Persönlichkeiten, Stoff für Zürcher Humor. *Aufwand:* S–M. *Risiko:* nur erfundene Figuren, Textmenge. *Systeme:* `world/humans.ts`, `anecdotes.ts`.

### 10. Tiere und Dinge, mit denen man spielen kann
Tauben, Hunde an der Leine, Spielplatz-Wippe/Rutschbahn (Spielgeräte existieren in `playgrounds.ts`). Tauben fliegen auf, wenn man rennt; man kann auf Schaukeln, Rutsche, Wippe «interagieren».
*Warum:* Kleine Physik-Freude, Bewegung der Stadt. *Aufwand:* M. *Risiko:* Perf (Boids begrenzt). *Systeme:* `playgrounds.ts`, neues `world/pigeons.ts`.

## C. Belohnungen ohne Quests

### 11. Kiez-Karte aufdecken
Karte zeigt unerforschte Stellen als «Nebel»; Gehen, Radeln, Tram-Fahren deckt auf. Pro Kreis Prozentanzeige (Kreis 4: 37 %). Bei 100 % gibt es einen Titel/Sticker.
*Warum:* Alt bewährt (Zelda/Mini Metro-Netz-Gefühl); stärkt Motivation, Strassen abzulaufen. *Aufwand:* M. *Risiko:* Speicher in localStorage (Raster 25 m reicht). *Systeme:* `ui/map*.ts`, `gameplay/state.ts`.

### 12. Sammelalbum «Züri-Inventar»
Die 595 Anekdoten werden zu Karten im Album, geordnet nach Quartier. Zusätzlich: Brunnen (Trinkbrunnen als Trink-Aktion!), Läden, Wildplakate, Graffiti, Tauben-Kackspuren. Fortschrittsbalken, «noch 12 bis Kreis-4-Meister».
*Warum:* Sammeln ohne Quest, Anekdoten werden greifbar. *Aufwand:* S. *Risiko:* gering. *Systeme:* `anecdotes.ts`, `ui/menu.ts`, `state.ts`.

### 13. Orte abhaken: «100 Orte»-Liste
Handverlesene Orte (Brunnen, Aussichten, Brücken, Läden, Kunst) werden beim Besuch geabhakt, mit Mini-Titelbild und Kurzgeschichte. Auf der Karte als Stecknadeln, die gelb werden.
*Warum:* Das Spiel wird Stadtführer, der Zürcher:innen stolz macht («da isch mis Kafi!»). *Aufwand:* M. *Risiko:* Quellen für jeden POI. *Systeme:* `public/data/*.json`, `ui/map.ts`.

### 14. Postkarten teilen
Fotomodus-Bild plus Ortsstempel, Datum/Zeit, Slogan («Grüsse aus Aussersihl»). «Teilen»-Button (Web Share API) oder Download. Link `?at=...` führt Freund:innen an dieselbe Stelle.
*Warum:* Verbreitung ohne Backend. *Aufwand:* M. *Risiko:* Canvas-Export auf iOS, Plakate/Logos im Bild (rechtlich ok, nur eigene). *Systeme:* `engine/renderer.ts` (Capture), `ui/`, URL-Params existieren (`?at=`).

### 15. Titel und Sticker
Spielerprofil mit Titeln («Tramfahrer 3. Klasse», «Kreis-5-Gstudierte», «Velo-Rowdy ohne Sturz»). Sticker zierten Menü und Postkarten.
*Warum:* Identität statt Punktezahl, humorvoll. *Aufwand:* S. *Risiko:* gering. *Systeme:* `state.ts`, `menu.ts`.

## D. Fotomodus und Kamera

### 16. Fotomodus
Taste/Button blendet HUD aus, Freiflug-Kamera um die Figur, Tiefenschärfe, Tageszeit-Regler, Filter (Polaroid, Neon-Nacht, S/W), Rahmen und Wasserzeichen mit Spielname.
*Warum:* Nutzer:innen erzeugen selbst Werbung; stärkt Tageszeit-Erlebnis. *Aufwand:* M. *Risiko:* Perf-Spitze (nur im Modus), Kamerakollision. *Systeme:* `engine/post.ts`, `daytime.ts`, `player` Kamera.

### 17. Selfie-Kamera und Gruppenfoto mit NPCs
Figur dreht Kamera zu sich, NPCs in der Nähe stellen sich dazu (Emote 5).
*Warum:* Soziales Moment, Humor. *Aufwand:* S–M. *Risiko:* NPC-Kollision. *Systeme:* `humans.ts`, Kamera.

### 18. Filmische Kameras beim Fahren
Auto, Velo und Tram haben optionale Cinematic-Ansicht (tief, seitlich), Geschwindigkeits-FOV, leichter Kamerastoss bei Schlaglöchern.
*Warum:* Geschwindigkeitsgefühl, Jet-Set-Radio. *Aufwand:* S. *Risiko:* Übelkeit → Option, Reduzierte-Bewegung-Schalter (siehe 27). *Systeme:* `player/vehicle_player.ts`, Kamera.

## E. Fahrzeuge und Bewegung

### 19. Tram mitfahren
Zur Haltestelle gehen, Tram betreten, Passagier-Ansicht (Fenster, Haltestellenansage «Helvetiaplatz», Türen-Piepton), Schnellvorlauf optional, Aussteigen beliebig. Karte deckt unterwegs auf.
*Warum:* Stärkstes Zürich-Gefühl, entspannt, schnelle Fortbewegung für Handy. *Aufwand:* M. *Risiko:* Tram-Fahrplan/Sync, Kamera im Fahrzeug, Perf (nur sichtbare Kacheln laden). *Systeme:* `world/transit.ts`, `stops.ts`, `player/vehicle_use.ts`.

### 20. Velo-Leihe und Veloständer (Publibike-ähnlich, fiktiv)
Leih-Velostationen (nur fiktiver Name), Velo-Schloss-Ritual, eigenes Velo parkieren und später wiederfinden (Marker).
*Warum:* Realismus, kleine Alltagsroutine. *Aufwand:* M. *Risiko:* echte Anbieter vermeiden. *Systeme:* `world/bikes.ts`, `state.ts`.

### 21. Auto-Ausparkhilfe und Rückwärtsgang-Hinweis
Hinweis «S = rückwärts», sanftes Wegschieben von Parkautos, Rückkamera-Kurzansicht (QA-Punkt 5).
*Warum:* Frust verhindern. *Aufwand:* S. *Risiko:* gering. *Systeme:* `player/vehicle_player.ts`, `world/parkedcars.ts`.

## F. Tageszeit und Wetter

### 22. Wetter als Erlebnis
Regen mit Pfützen-Spiegelungen, Regenschirme bei NPCs, Nebel am Morgen, Gewitter mit Donner, Föhn-Himmel am Abend. Regen verändert Velo-Grip leicht. Tram-Räder quietschen.
*Warum:* Stimmung, Wiederspielwert, Screenshot-Material. *Aufwand:* M–L. *Risiko:* Perf auf Handy (Partikel auf Quality-Stufen abstellen). *Systeme:* `engine/env.ts`, `sky.ts`, `post.ts`, `materials.ts`, `audio_amb.ts`.

### 23. Goldene-Stunde und Zürcher Tagesrhythmus
Uhr läuft schon. Dazu: Morgens Kaffee-Geruch (Ton), Mittags Schlangen, abends Terrassen voll, nachts Clubs (Bass aus Türen), Laternen, Strassenreinigung bei Morgengrauen. Event-Kalender existiert (`events.ts`): sichtbar machen («Heute: Flohmarkt Helvetiaplatz»).
*Warum:* Stadt wirkt lebendig und lädt zum Wiederkommen zu anderen Uhrzeiten ein. *Aufwand:* M. *Risiko:* NPC-Dichte-Budget. *Systeme:* `daytime.ts`, `events.ts`, `streetlife.ts`, `night_lights.ts`.

## G. Handy-Steuerung

### 24. Handy-Komfort
Einhand-Modus (Stick links, Knöpfe auf Daumenzone), Auto-Rennen ab ~90 % Auslenkung (QA-Punkt 7, teilweise erledigt), Kontext-Knopf (ein grosser Button wechselt: Velo nehmen, Tram einsteigen, Foto), Auto-Kamera-Zentrierung hinter der Figur, Vibration bei Crash/Hupen (falls erlaubt).
*Warum:* Handy ist Haupt-Eingang; weniger Knöpfe, mehr Fluss. *Aufwand:* S–M. *Risiko:* Linkshänder-Option. *Systeme:* `input/touch.ts`, `ui/settings.ts`.

### 25. Tipp-zum-Gehen und Ziel-Pfad
Auf der Karte oder auf dem Boden tippen: Figur geht automatisch (Navigationsgraph, `roadgraph`), Auto-Stopp bei Hindernis. Ermöglicht ruhiges Zuschauen und Fotografieren.
*Warum:* Entspannte Bedienung, Barrierefrei, für Touristen. *Aufwand:* M. *Risiko:* Pfadsuche auf Gehwegen (Daten vorhanden `pedspots`/`paths`). *Systeme:* `player/`, `ui/map.ts`, Pfad-Graph.

### 26. Mini-Karte mit Richtungsmarker und «Wo bin ich»
Radar zeigt Kompass, Namen der Strasse, Ziel-Marker in Pfeilform am Rand. Antippen öffnet Karte.
*Warum:* Orientierung, besonders auf kleinem Bildschirm. *Aufwand:* S. *Risiko:* gering. *Systeme:* `ui/map*.ts`.

## H. Barrierefreiheit

### 27. Zugänglichkeits-Paket
Reduzierte Bewegung (kein Kamerawackeln, weniger FOV-Effekte), Farbenblind-Modus für Marker/Plakate, grosse Schrift, Kontrast-Hinweise, alternative Steuerung (Tippen statt Halten), Untertitel für Ton-Hinweise, Tastaturbelegung änderbar.
*Warum:* Mehr Spielende, verlangen öffentliche Kampagne. *Aufwand:* M. *Risiko:* Test-Aufwand. *Systeme:* `ui/settings.ts`, `hud.css`, `input/*`.

### 28. Vorlese- und Ruhe-Modus
Anekdoten optional vorgelesen (Browser-TTS, de-CH), «Ruhig»-Modus mit weniger Verkehr und Lärm.
*Warum:* Entspanntes Erkunden, Reizüberflutung vermeiden. *Aufwand:* S. *Risiko:* TTS-Qualität. *Systeme:* `anecdotes.ts`, `audio*.ts`, `settings.ts`.

## I. Performance-Gefühl

### 29. Weiche Qualitätsanpassung
Dynamische Auflösung und Schattendistanz, die FPS-Einbrüche in Handy-Szenen (35–49 fps) abfedert, bevor man sie bemerkt; Qualitätsanzeige im Menü («Auto»). Kachelladen auf mehrere Frames verteilt (QA-Punkt 6).
*Warum:* Flüssigkeit ist wichtiger als Auflösung. *Aufwand:* M. *Risiko:* Pop-in. *Systeme:* `engine/quality.ts`, `renderer.ts`, `tiles.ts`.

### 30. Lade-Pause statt Ruckler
Beim Ortswechsel kurzer Fade statt Hitch, Vorladen entlang der Bewegungsrichtung.
*Warum:* Gefühl von Qualität. *Aufwand:* S–M. *Risiko:* gering. *Systeme:* `tiles.ts`, `ui/loading.ts`.

## J. Welt, Humor und Easter Eggs

### 31. Züri-Insider-Easter-Eggs
Versteckte Orte: Kuh auf dem Dach (Reel-Anspielung), «Formular-Büro» als Kulisse, eine Tür mit «ja es Formular gern», Boccia-Grosis auf der Wiese, verlorener Schuh am Zaun, Graffiti-Zeile pro Quartier. Auffindbar nur durch Zufall; Hinweis in der Anekdoten-Karte.
*Warum:* Belohnt Neugier, Gesprächsstoff. *Aufwand:* S je Egg. *Risiko:* Humor-Check, echte Personen nein. *Systeme:* `scenes.ts`, `anecdotes.ts`.

### 32. Münzen, Trinkgeld und Kaffee kaufen
Das Geld hat einen Zweck: Kaffee kaufen (Stärke für Tempo), Trinkgeld an Strassenmusiker:innen (erfunden) bringt Musik-Boost, Spenden an einen fiktiven «Quartierverein» schaltet Dekor frei (Blumen, Plakate).
*Warum:* Wirtschaftlicher Kreislauf, klein aber spürbar. *Aufwand:* M. *Risiko:* Echte Läden nicht werben. *Systeme:* `state.ts`, `storefronts.ts`.

### 33. Quartier-Radio
Radio-Sender im Spiel (Hip-Hop existiert): Sendungen wechseln pro Kreis, Verkehrsmeldungen mit Zürcher Humor («Stau auf der Hardbrücke wegen Tram»), Platz für Botschaften des Users später.
*Warum:* Stimmung, Information. *Aufwand:* S–M. *Risiko:* Musik-Lizenz (CC BY ok). *Systeme:* `audio_music.ts`.

### 34. Streetart-Gallery
Kunstwerke/Skulpturen im Quartier als «Gallery-Tour» (nur mit Quelle). Vorbeigehen schaltet Bildkarte frei.
*Warum:* Entdeckerfreude. *Aufwand:* M. *Risiko:* Urheberrecht der Werke. *Systeme:* `landmarks.json`.

### 35. Zufalls-Mini-Ereignisse
Alle paar Minuten passiert etwas im Quartier: Demo zieht durch (Kalender), Velo-Critical-Mass fährt vorbei (man kann mitfahren, Existenz in `events.ts` prüfen), Hund reisst aus, Strassenfest baut auf.
*Warum:* Überraschung, die Wiederspielwert bringt. *Aufwand:* M. *Risiko:* Perf, Fahrt-AI. *Systeme:* `events.ts`, `streetlife.ts`.

## K. Soziales (ohne Backend)

### 36. Geisterspuren und Notizen anderer
Spuren-Lösung nur lokal oder per statischer Datei: «Tipps der Redaktion» als Zettel an Orten. Später evtl. Backend-frei via Teilen-Link.
*Warum:* Gemeinschaft ohne Server. *Aufwand:* S (lokal). *Risiko:* Moderation bei echtem UGC, deshalb zunächst weglassen. *Systeme:* `anecdotes.ts`.

### 37. Wochen-Herausforderung per Link
Ein Link `?challenge=velo-hardbruecke` startet eine feste Route/Zeit; man teilt das Ergebnis als Bild. Kein Server nötig.
*Warum:* Wiederkehrender Anlass für Social Media. *Aufwand:* M. *Risiko:* Betrug egal, da lokal. *Systeme:* URL-Params, `state.ts`.

## L. Quests (spätere Ideen, nur Skizze)

### 38. Quest-Rahmen aus Spielmomenten
Q1 «Züri werbefrei» ohne Zerstörung: Bildschirme «abschalten/übermalen/bepflanzen» als Mini-Aktionen; Q3 Velokurier nutzt Velo-Tricks und Tram-Abkürzungen; Q2 Mobilisieren: Gespräche mit NPCs sammeln Unterschriften (kein Gegner, nur Zählen). Kern: Mechaniken aus Teil B/C wiederverwenden.
*Warum:* Quests wirken stimmiger, wenn die Grundbewegungen schon Spass machen. *Aufwand:* L. *Risiko:* Inhalt, Freigaben. *Systeme:* `missions.ts`.

---

## Empfehlung zur Reihenfolge
1. Onboarding (1, 26), Sammelalbum (12), Hup-/Klingel-Reaktion (4): 2–3 Tage, grosse Wirkung.
2. Kiez-Aufdecken (11), Fotomodus (16), Postkarten (14): macht das Spiel teilbar.
3. Velo-Tricks (7), Tram-Mitfahren (19), Wetter (22): Spielgefühl und Stimmung.
4. Zugänglichkeit (27), Handy-Komfort (24), Qualitätsanpassung (29) parallel mitlaufen lassen.
