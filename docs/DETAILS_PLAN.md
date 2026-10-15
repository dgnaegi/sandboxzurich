# Detail-Plan: lebendige Kreise 3, 4, 5, 9

Ziel: Wer durch das Spiel läuft, erkennt sein Quartier an Hunderten kleiner Details. Alles beruht auf echten Quellen, wird per Skript eingelesen (keine Handarbeit) und erscheint in Schichten.

## 1. Quellen sammeln (Recherche, läuft)
| Paket | Inhalt | Ziel | Wer |
|---|---|---|---|
| R1 Rohdaten | OSM komplett (alle Läden inkl. Denner/Migros/Coop/Volg/Lidl/Aldi, Kioske, Bars, Clubs, Stadtmobiliar), swissALTI3D, swissBUILDINGS3D, Stadt-ZH-OGD (Bäume, Brunnen, Velo, Tempo 30) | `data/raw/`, `research/raw_inventory.md` | Agent (Sonnet) |
| R2 Termine | Wiederkehrende Märkte und Anlässe: Flohmärkte (z.B. Kanzlei), Wochenmärkte (Helvetiaplatz), Quartierfeste, Street Food, Openairs, Sportevents (Letzigrund) mit Ort, Wochentag/Saison, Quelle | `research/events.md` + `pipeline/overrides/events.json` | Agent (Haiku) |
| R3 Soziale Infrastruktur | Kitas, Kindergärten, Schulhäuser, Horte, Spielplätze, GZ, Bibliotheken, ZüriWC, Sportanlagen, Badis, Pingpong, Boccia aus Stadt-ZH-OGD | `data/raw/stadtzh_extra/`, `research/social_infra.md` | Agent (Haiku) |
| R4 Quartier-Stimmung | Pro Quartier typische Szenen und Orte (Langstrasse Nachtleben, Bäckeranlage, Josefwiese, Idaplatz, Röntgenplatz, Lochergut, Albisriederplatz, Letzi …) mit Quellen | `research/street_life.md` | Agent (Haiku), zusammen mit R2 |
| R5 Ladenprüfung | OSM-Läden per Web prüfen (existiert noch, Name stimmt) | `research/pois_kreisN.csv` | später, Haiku in Paketen pro Kreis |

## 2. Darstellung in Schichten
1. **Statisch, aus Daten:** Ladenschilder (echte Namen), Detailhändler-Fassaden in Hausfarbe (nur Name, kein Logo), Schulhäuser/Kitas mit Schild und Spielplatz, Brunnen, Bänke, Velo-Abstellplätze mit Velos, Glascontainer, Züri-Kübel, Plakatwände (fiktive Inhalte).
2. **Zeitabhängig:** Märkte und Flohmärkte erscheinen am echten Wochentag (Spielzeit), mit Ständen und Menschenmenge. Nachtleben an der Langstrasse nachts, Kinder bei Schulen und Kitas tagsüber.
3. **Menschen (Ambient-NPCs):** Passant:innen, Leute mit Einkaufstaschen vor Detailhändlern, Gruppen vor Bars, Kinder mit Begleitung, Velofahrer:innen, Betrunkene, die nachts torkeln (comichaft), Strassenmusik, Pingpong- und Boccia-Spieler:innen.
4. **Szenen (Vignetten):** kleine Skripte an echten Orten, z.B. Streit zwischen zwei Betrunkenen, den Freund:innen schlichten (ohne Schläge und Verletzte, siehe Leitplanken), Polizeipatrouille, Lieferverkehr, Velokurier.

## 3. Offene Entscheide (Kampagne)
- **Sexarbeit an der Langstrasse:** gehört zur Realität des Quartiers. Vorschlag: als respektvoll gezeichnete Figuren im Strassenbild, ohne Interaktion, ohne Sexualisierung und nie als Ziel oder Witz. Alternative: weglassen. → Entscheid der Kampagne.
- **Schlägereien:** Die Leitplanken verbieten Gewalt gegen Menschen. Vorschlag: nur als lautes Gerangel/Streit zwischen NPCs, das sich auflöst; die Spielerin kann schlichten (positives Gameplay). → Entscheid der Kampagne.
- **Betrunkene:** comichaft torkelnd, nicht als Spott über Suchtkranke. Keine Darstellung von Drogenkonsum.

## 4. Reihenfolge
1. Karte im Testgebiet fertig (Look, Läden, Schilder, Stadtmobiliar), GTA-Karte mit Sprungpunkten.
2. Daten R1–R3 einlesen: Detailhändler, Schulen/Kitas, Brunnen, Velos.
3. Ambient-NPCs mit Rollen (Einkauf, Schule, Nachtleben) und Tageszeit.
4. Märkte/Flohmärkte nach Kalender.
5. Vignetten (nach Entscheid der Kampagne).
6. Verkehr: Trams, Autos, Velos (klauen und fahren).

## 5. Ergänzungen (User, 2026-10-14)
- **Demos:** Critical Mass (Velo-Demo, letzter Freitag im Monat) als Massen-Velo-Event; eine weitere Demo (z.B. Wohnungsdemo) mit Transparenten (fiktive/Kampagnen-Texte). Polizei begleitet comichaft.
- **Polizei:** Patrouillen zu Fuss und im Auto, Kastenwagen; Verhalten gemäss Leitplanken (fangen statt verletzen).
- **Friedhof Sihlfeld mit altem Krematorium:** realistisch, mit Trauernden bei Gräbern (still, respektvoll), Leute liegen in der Wiese, Spaziergänger:innen; Krematorium als Landmark individuell modellieren.
- **Bahnhof Wiedikon:** Landmark, möglichst originalgetreu (Bahnhofgebäude, Gleise im Einschnitt, Brücken), viele Bars rundherum (aus OSM + Ladenprüfung), abends belebt.
- **Offene Quellen-Katalog:** alle OGD-Datensätze (siehe `research/raw_inventory.md`, `research/social_infra.md`) plus Referenzbilder (Mapillary, Panoramax, Wikimedia Commons; nur mit Lizenz, nur als Referenz/Textur, wo erlaubt) → `research/sources_catalog.md`.
- **Langstrasse maximal realistisch (Priorität 1):** alle Bars, Clubs, Kebab, Kioske, Läden mit echtem Namen an der echten Adresse; Ladenprüfung per Web (Haiku-Agent, `research/pois_langstrasse.csv`), Fehler/Neues in `pipeline/overrides/pois.json`. Leuchtreklamen nachts.
- **Baustellen:** einige echte Baustellen (Stadt-ZH-OGD «Baustellen»/Tiefbau, falls verfügbar), sonst plausibel gesetzt: Abschrankungen, Signale, Bagger, Gerüste an Fassaden, Mulden.
- **Kurzzeitvermietung:** immer wieder Hinweise auf AirBnB-Wohnungen und Business Apartments: Schlüsselboxen an Hauseingängen, Rollkoffer-Tourist:innen, Klingelschilder ohne Namen. Business-Apartment-Häuser aus OSM (`tourism=apartment`/`guest_house`) als neutrale Fakten; AirBnB nur fiktiv («AirBnZ»), nie an konkreter echter Wohnung als Vorwurf. Verbindung zur Quest-Idee in `QUESTS.md`.
- **Denkmäler und Kunst im Stadtraum:** echte Standorte aus Stadt-ZH-OGD «Kunst im Stadtraum» (421) und OSM `historic=memorial|monument`; Sockel + Platzhalterform automatisch, wichtige Werke einzeln modelliert (Referenz: Wikimedia Commons mit Lizenz).
- **Tankstellen:** OSM `amenity=fuel` mit Dach, Zapfsäulen, Shop (Name als Schild, keine Markenlogos), Autos beim Tanken.
