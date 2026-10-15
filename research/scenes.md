# Szenen und Easter Eggs (generiert)

Quelle: `pipeline/overrides/scenes_src.json` (fixed = handplatziert, groups = Orts-Resolver auf OSM). Generator: `python3 pipeline/scenes_build.py` -> `web/public/data/scenes.json` (138 Eggs, gleichmässig über das Spielgebiet, per Farthest-Point-Sampling; Positionen in OSM-Gebäuden werden verworfen oder auf die Strassenseite verschoben).

| Gruppe | Typ | Ort (OSM) | Anzahl |
|---|---|---|---|
| pingpong | Tisch + 2 Spieler, Ball animiert | sport=table_tennis (ohne Namen) | 5 |
| boccia | Kugeln + 3 Figuren | Bocciodromo Letzi, Josefwiese, Lutherwiese | 3 |
| badi | Tücher, Sonnenschirm, Liegende | Planschbecken Bäckeranlage/Josefwiese/Bullingerhof | 3 |
| strassenmusik | Gitarre/Akkordeon/Sax | vor Cafés | 5 |
| techbros | 3 Figuren | office=it | 4 |
| touristen, selfie | Gruppe mit Fähnchen / Selfie | tourism=information | 3+3 |
| besichtigung | Wohnungsschlangen | Wohnblöcke (building=apartments) | 5 |
| flohmarkt, brocki | Stand mit Vinyl | shop=music, second_hand | 4+2 |
| kunst_a, kunst | Info-Tafel + Toast | tourism=artwork | 6+12 |
| miniboeoegg | kleiner Böögg | Veloständer | 5 |
| graffiti | Wand mit Spruch (fiktiv) | Wohnblöcke | 6 |
| tram, uhr, velopumpe | nur Toast | Tramhalte, Uhren, Reparaturstationen | 8+3+4 |
| slang | Wort-des-Tages-Schild | Kioske | 6 |
| kurier, lastenvelo | Velos, Rucksäcke, Hund im Korb | Veloverleih, Convenience | 2+2 |
| club, atm | Schlangen mit Absperrung | Nachtclubs, Bankomaten | 3+3 |
| ente, tauben, handschuh, pflanze | kleine Objekte | Brunnen, Bänke, Briefkästen, Recycling | 3+4+3+3 |
| jass/fondue, toeggeli, menu, umzug | Tisch-Szenen, Schilder | Picknicktische, Bars, Restaurants, Wohnblöcke | 3+2+4+3 |
| hundespaziergang, jogger, spaziergaenger, stelzen2 | gehende Figuren (Hund mit Leine) | OSM-Fusswege (Parks) | 3+2+2+1 |

Leitplanken: keine echten Personen/Firmen/Parteien, keine Faktenbehauptungen (Kunsttexte generisch), Schilder nennen keine echten Adressen. Nicht umgesetzt: Dach-Eggs (keine Gebäudehöhen im Cache, `data/build/bld` leer).

Performance: `Scenes` baut nur Szenen im Umkreis `visRadius` (max. eine pro Frame), entsorgt ab +30 m (Pfade +60 m); Mixer nur < 60 m. Eggs sind reine Daten (Fund < 9 m).
