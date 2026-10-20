# Zone 5 Gebiet Letzigrund / Herdernstrasse / PJZ / Westpark (Agent z5c, 2026-10-20)

Werkzeug: Foto|Spiel-Bogen eigenes Skript (wie `pipeline/zones/zone_cmp.py`, nur 5 Punkte), Vorher `preview/z5c_before_{1,2}.jpg`, nachher `z5c_after_{1,2}.jpg`; freie Ansichten `z5c_pjz_*.jpg`, `z5c_h2.jpg`, `z5c_tw.jpg`.
**Lehre 14:** Die Mapillary-Dashcam-Richtung stimmt bei Strassenbildern oft nicht mit der Blickrichtung ueberein (Foto Letzigrund-Stadion zeigt die Hausreihe SUEDLICH der Tramspur, Heading sagt NW). Der Foto|Spiel-Bogen vom Fotoort zeigt dann in die falsche Richtung. Besser: Fotos ansehen, Gebaeude per `common.near()` + Fussabdruckkarte identifizieren, dann freie Kamera.
**Lehre 15:** Nur Landmarks (GLB) sind sofort im Dev-Spiel sichtbar. Notizen, Bodenflaechen (`places_detail`), Markierungen, Ladenfronten wirken erst nach Kachel-Build (hier verboten).

## PJZ (Schwerpunkt)
Vorher: alles Hauptbau, einheitliche beige Fassade, helle Fenster, Kegelkronen-"Baeume". Nachher: Gefaengnisblock NW (dunkel, Hof), Hauptring 23 m, Mittelblock 31 m, Glasdach-Atrium, Eingang SW-Strassenseite, kuehle graugruene Fassade, dunkle Fenster. Details `research/pjz.md`. Schaetzung Note 3.5 (Strassenansicht), ~3 aus Luft (Fenster-Raster generisch). Kamerapunkt «PJZ Ost» (330,-200) steht hinter den Gleisen, Foto zeigt Schienen + Prime Tower: Spiel dort nicht vergleichbar, Note ~3.

## Kamerapunkte
| Punkt | Befund | Fix | Note vorher -> nachher |
|---|---|---|---|
| Letzigrund Stadion | Suedseite Badenerstrasse (rosa 5-Geschosser, ockerfarbenes Haus mit Walmdach) fuenf Tile-Haeuser in beige/gelb | Landmarks `z5c_letzi_pink` (D0A7406F + 5604C6FA, rosa #d8aba0, Backsteinsockel, flaches Dach) und `z5c_letzi_ocker` (FD985A3E) | 2.5 -> 3.0 |
| Haltestelle Letzigrund | Y-Hochhaeuser (BEDFC1B3, 43BA45EE, 38 m) als braune Streifen-Tuerme, Foto: hellgrau-beige | Landmark `z5c_letzi_tower` (#c4baa8) | 3.0 -> 3.5 |
| Herdernstrasse | Ostseite graue Steinblocks; Foto: weissgrau verputzt, blaue Fensterrahmen (96DB387A, 9F036ED8, 0C87A1B2) | Landmark `z5c_herdern_block` | 3.0 -> 3.2 |
| Westpark | Weg grau mit weissen Linien, Foto: rotbrauner Asphalt + Kies + Hecke; Haeuser ok (Backstein links, graues Buerohaus rechts) | nur Ticket (Boden = Kachel-Build) | 3.0 -> 3.0 |

## Tickets
- Z5c-1 Pilzdach-Haltestelle Letzigrund (Foto 2014, c. (-975,-315)): grosses Flachdach + Glaskabine, Spiel hat 3 normale Glashaeuschen (`stops_equip.sh`).
- Z5c-2 Stadionwand zu orange (Foto: dunkles Rotbraun), nicht in meiner Dateiliste (Letzigrund-Generator, DECISIONS #50).
- Z5c-3 Westpark: roter Velo-/Fussweg (Gleisbogen) fehlt; braucht Bodenfarbe (Code, `markings_override` kennt nur Linien).
- Z5c-4 Rote Veloflaeche am Knoten Haltestelle Letzigrund (Spielbild) zackig/gerissen.
- Z5c-5 Notizen/`fields` fuer Zone-5-Haeuser nicht ergaenzt (wirken erst nach Build; Landmarks decken die auffaelligen Haeuser ab). EGGER ELEKTRO AG (EG links im Foto) nicht gesetzt, Hausnummer unsicher.
- Z5c-6 Vor dem PJZ-Eingang: Rampe/Hochstrasse (weisse Platte) + Holzhuette in der Flucht, Absperrung rot-weiss (andere Ebenen).
