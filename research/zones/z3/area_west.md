# Zone 3 Gebiet West/Nord (Agent z3c, 2026-10-20)

Punkte: Hardplatz, Hohlstrasse/Hardstrasse, Hardstrasse/Bullingerstrasse, Albisriederplatz, Badenerstrasse/Zypressenstrasse.
Material: `research/zones/zone3_cam_photos.json` (`data/raw/photos/z3/`), Mapillary/Panoramax (CC BY-SA 4.0), Commons.
Werkzeug: Fussabdruckkarte mit farbcodierten Debug-Landmarks (Haus je Farbe) + Freikamera auf Augenhoehe an der Fotoposition (`pipeline/landmarks/free_shot.mjs`), Foto | Spiel nebeneinander. Bögen `preview/z3c_before_{A,B}.jpg`, `preview/z3c_after_{A,B}.jpg` (links Foto, rechts Spiel; jeweils 8 Paare).

**Lehre (bestaetigt 15):** Mapillary-Heading/-Position stimmen oft nicht: Zypressenstrasse Foto 0 und Hardplatz Foto 2 schauen real in die Gegenrichtung (+180 Grad), Hardstrasse/Bullingerstrasse Foto 3 liegt ~65 Grad daneben. Zuordnung Foto -> Haus deshalb ueber die Reihenfolge der Haeuser an der Strasse (zwei bis drei Fotos) und farbcodierte Debug-Landmarks, nicht ueber das Heading.
**Lehre 14 gilt:** Die Landmarks verdecken die Original-Haeuser im Dev-Spiel erst nach dem Kachel-Build (`hide`); bis dahin Z-Fighting-Flecken (rosa/orange Flecken auf den Bögen sind die Originalfassaden darunter). Bodenflaechen (`places_detail_z3c.json`) und Ladenfront wirken ebenfalls erst nach Kachel-Build.

## Kamerapunkte
| Punkt | Foto-Befund | Fix | Note vorher -> geschaetzt nachher |
|---|---|---|---|
| Badenerstrasse/Zypressenstrasse | Hellblaues Eckhaus mit blauen Laeden und Rundung (Eckladen), graues Eckhaus mit Walmdach (SO), weisse Haeuser mit grauen Laeden, ockerfarbenes Eckhaus mit Mansarde (NO), rosa-weisses Haus mit Tuere; Rasengleis (Gras zwischen den Schienen) ab der Kreuzung nach Osten | 6 Landmarks `z3c_zy_*` (Farben, Walmdach, Laeden); Gras-Streifen neben/zwischen den Schienen (`places_detail_z3c.json`, Schienen bleiben frei) | 2.8 -> 4.0 (Haeuser stimmen im Spielbild; Gras unbestaetigt bis Kachel-Build) |
| Hardstrasse/Bullingerstrasse | Rotes Eckhaus (NW), weisses/hellgelbes Haus daneben, gelbes Eckhaus mit Balkonen (O), Reihe cremegelb entlang Hardstrasse mit Platanen | 8 Landmarks `z3c_hb_*` | 3.0 -> 4.0 |
| Albisriederplatz | Graues 1950er-Geschaeftshaus mit Apotheke-Arkade (SW), blaugraues + gelbes Haus (NW-Seite), lachsfarbenes/ockergelbes/cremefarbenes Haus (Suedseite) | 6 Landmarks `z3c_al_*`; Ladenfront Nature First Apotheke (`storefronts_z3c.json`) | 2.7 -> 3.6 (Zuordnung NW/Sued nur teilweise gesichert) |
| Hardplatz | Gleisschleife in Kopfsteinpflaster (Mapillary-beat-Serie 2019), dahinter fliederfarbenes grosses Eckhaus mit Laeden, orangefarbenes Backsteinhaus, weisses Haus mit Walmdach, roter Backsteinblock (Reihenfolge nur geschaetzt) | 3 Landmarks `z3c_hp_*` + `z3c_hohl_*` (W-Seite) | 2.5 -> 3.2 |
| Hohlstrasse/Hardstrasse | Hardstrasse faehrt im Betontrog unter die Hardbruecke (Betonwaende, Fahrleitungen), im Spiel offene Flaeche mit Pfeilern; W-Seite grosses weisses Haus mit roten Daechern, Backsteinhaus | 3 Landmarks `z3c_hohl_*` (Trog = Ticket Z3c-1) | 2.3 -> 3.0 |

## Tickets
- Z3c-1 Hardbruecken-Rampe/Trog Hardstrasse (Hohlstrasse/Hardstrasse, Hardplatz Foto 0/1/5/7): Fahrbahn liegt zwischen Betonwaenden im Trog mit Gefaelle, im Spiel offene Ebene; braucht Gelaendeschnitt + Wandgeometrie (nicht in meiner Dateiliste).
- Z3c-2 Baustelle (OGD Tiefbau) am Albisriederplatz: im Spiel riesiger Zaun mit Banner direkt an der Haltestelle (Foto 2023-25 ohne Baustelle) -> Daten pruefen (`pipeline/sites.py`, Stand der Baustellen).
- Z3c-3 Eckladen Zypressenstrasse: Foto «eNDi / Barber with style», OSM nennt am selben Eck «Machida Shoten» (Restaurant) -> Abgleich durch User, nicht umbenannt.
- Z3c-4 Strassenglaettung Seebahn-/Bullingerstrasse (`road_smooth_audit.py`): nur Ticket, nicht angefasst.
- Z3c-5 Zuordnung Foto -> Haus am Albisriederplatz (NW-/W-Seite) und am Hardplatz nur nach Reihenfolge, nicht abgesichert; nach dem Kachel-Build mit Foto-Bögen pruefen.
- Z3c-6 Rasengleis: Ausdehnung nach Osten nur bis x = -205 belegt (Fotos bei x = -250..-270); weitere Abschnitte der Badenerstrasse (Kalkbreite bis Lochergut) in z3a/z3b pruefen.
