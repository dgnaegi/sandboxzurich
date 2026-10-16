# Verbesserung Details Map (2026-10-16)

Neue Schicht `meta.details` pro Kachel: `pipeline/details_osm.py` (+ `details_leaves.py`, `details_facade.py`) -> `web/src/world/details.ts`
(ein gemergtes Vertex-Color-Mesh pro Kachel, 1 Draw-Call, wird mit der Kachel entladen/disposed). Korrekturen: `pipeline/overrides/details.json`
(`drop` = Punkte, an denen nichts stehen soll; `add` = von Hand gesetzte Objekte). Hook: `build_testarea.py` (`details_osm.prepare`, `tile_meta`).

| Kategorie | Quelle | Anzahl im Spielgebiet | Hinweis |
|---|---|---|---|
| Litfasssäule | OSM `advertising=column` | 37 | 4 Plakatsektoren in gedeckten Farben (keine echten Sujets) |
| Telefonkabine | OSM `amenity=telephone` | 6 | |
| Briefkasten (Post gelb) | OSM `amenity=post_box` | 59 | OSM unvollständig, nichts erfunden |
| Recycling (Glas/Dosen/Textil) | OSM `amenity=recycling` (ohne Unterflur/Zentrum) | 82 | Farben nach `recycling:*`-Tags |
| Trinkbrunnen | OSM `drinking_water`, nur wo kein OGD-Brunnen (WVZ) im Umkreis 6 m | 134 minus OGD | OGD-Brunnen waren schon da |
| Wegweiser | OSM `information=guidepost` | 73 | Velo = weiss/rot, Wandern = gelb |
| Kiosk freistehend | OSM `shop=kiosk` ausserhalb Gebäude | 29 | K-Kiosk rot |
| Strassenuhr, Infotafel, Ladesäule | OSM | 8 / 8 / 13 | |
| Tore | OSM `barrier=gate` auf Zaun/Hecken-Linie | 179 | Breite aus Tag, sonst 3 m (Hofeinfahrt) / 1.2 m |
| Hecken, Zäune (Vorgärten) | OSM `barrier=hedge/fence` | 6.8 km / 9.3 km | in Strassen/Gebäuden ausgeschnitten; Fotos 204, 217, 222, 227, 238, 242 belegen Hecken |
| Laub (Herbst) | Baumkataster-Positionen, Laubbäume | pro Baum ~9-15 Gruppen | Saison Oktober gewollt |
| Kellerschächte, Satellitenschüsseln | keine Daten: Hash-Dichte 9 % / 2 % der Strassenwände ohne Laden | – | grob kalibriert, sparsam |

Nicht umgesetzt: Balkonpflanzen/Wäsche (Balkone sind nur Textur, keine Geometrie), Garagentore (keine Öffnungsdaten), Pfützen,
Imbisswagen (keine Daten). Bereits vorhanden: Baugerüste/Bauzäune (OGD, `sites.py`), Strassenschilder, Hausnummern, Terrassen mit Schirmen und Pflanztrögen
(`storefront_terrace.ts`), Velo-/Motorradparkplätze, Poller, Graffiti, Wildplakate.

## Foto-Kontrolle
43 neue Fotos (Panoramax CC-BY-SA, `research/details_cand.json`, Ids 200-242, Kreis 3/4/9 + Industriequartier) -> `research/details_shots.json`.
Sichtung: Hecken entlang Trottoirs häufig (Kreis 9, 3), Absperrgitter (224), Bauwand mit Graffiti (208, 237), Glas-Wartehalle mit Vitrine (235), Recycling-Container (241).
