# GRAND THEFT ZÜRI – Browser-Game

Open-World-Browsergame im GTA-3-Stil in den Zürcher Kreisen 3, 4, 5 und 9, mit Quests zu linken Wahlthemen (Wohnen, Freiraum, Verkehr, Schule). Gehostet auf Scalingo. Wird fast vollständig von AI gebaut; der Mensch testet, entscheidet und gibt Feedback.

Dieses Projekt ist **getrennt vom Reel** im Elternordner (`../CLAUDE.md`). Daten und Skripte von dort dürfen gelesen und wiederverwendet werden, aber nichts im Elternordner wird verändert.

## Start jeder Session (Pflicht)
1. `docs/HANDOFF.md` lesen: aktueller Stand, nächster Schritt, offene Fragen.
2. `docs/ROADMAP.md` lesen: aktuelles Milestone und Checkliste.
3. Vor Arbeit an der Karte: `docs/MAP_SPEC.md` und `docs/DATA_SOURCES.md`.
4. Vor Arbeit an Inhalten (Quests, Figuren, Texte): `docs/CONTENT_GUIDELINES.md`.

## Ende jedes Arbeitsschritts (Pflicht)
- `docs/HANDOFF.md` aktualisieren: was erledigt ist, was als Nächstes kommt, was blockiert. So kurz, dass eine neue Session ohne Vorwissen weitermachen kann.
- Erledigtes in `docs/ROADMAP.md` abhaken.
- Architekturentscheide als neuen Eintrag in `docs/DECISIONS.md` festhalten (nie alte Einträge umschreiben, sondern neue mit «ersetzt #N»).
- Arbeit in kleinen, lauffähigen Schritten. Nach jedem Schritt muss das Spiel noch starten.

## Dokumente
| Datei | Inhalt |
|---|---|
| `README.md` | Projektbeschreibung für Menschen |
| `docs/VISION.md` | Ziel, Zielgruppe, Ton, Scope und Nicht-Ziele |
| `docs/ARCHITECTURE.md` | Tech-Stack, Ordnerstruktur, Datenfluss, Performance-Budgets |
| `docs/MAP_SPEC.md` | Was die Karte enthalten muss (Checkliste pro Ebene) |
| `docs/DATA_SOURCES.md` | Quellen, Lizenzen, was erlaubt ist und was nicht |
| `docs/CONTENT_GUIDELINES.md` | Politische und rechtliche Leitplanken |
| `docs/QUESTS.md` | Quest-Ideen (werden später ausgearbeitet) |
| `docs/ROADMAP.md` | Milestones mit Checklisten |
| `docs/DECISIONS.md` | Entscheidungslog (ADR-light) |
| `docs/HANDOFF.md` | Übergabe zwischen Sessions |

## Regeln
- **Sprache:** Mit dem User Deutsch. UI- und Spieltexte Schweizerdeutsch (Züritüütsch). Code, Bezeichner und Commit-Messages Englisch.
- **Realismus:** Echte Strassen, echte Läden an echten Adressen, echte Velo-Infrastruktur. Im Zweifel den echten Ladennamen auf eine neutrale Fassade setzen statt etwas zu erfinden. Jeder POI braucht eine Quelle (siehe `DATA_SOURCES.md`).
- **Google Street View / Google Images:** nur zur Inspiration anschauen. Nie Bilder herunterladen, abpausen, als Textur oder für 3D-Rekonstruktion verwenden.
- **Handy und PC gleichwertig:** Jedes Feature muss mit Touch und mit Tastatur/Maus bedienbar sein. Screenshots und Tests laufen immer in beiden Viewports.
- **Performance zuerst:** Die Budgets in `ARCHITECTURE.md` (Handy und PC) sind verbindlich. Jede neue Ebene wird gegen das Budget gemessen.
- **Scalingo:** Statische App, Build lokal, Deploy per Archiv (`deploy/release.sh`). Nichts einbauen, was einen Server-Zustand braucht (siehe `ARCHITECTURE.md`, Abschnitt «Scalingo»).
- **Pipeline statt Handarbeit:** Kartendaten werden per Skript aus Rohdaten erzeugt (reproduzierbar). Keine von Hand editierten Binärdateien. Manuelle Korrekturen gehören in eine versionierte Override-Datei (`pipeline/overrides/*.json`).
- **Kleine Module:** Dateien möglichst unter ~400 Zeilen. Eine Verantwortung pro Modul.
- **Testen:** Visuelle Kontrolle per Headless-Browser-Screenshots (Playwright) an festen Kamerapunkten. Screenshots nach `preview/`, damit der User den Fortschritt sieht.
- **Sub-Agents:** nur mit klarer Dateizuständigkeit (welche Dateien ein Agent ändern darf), damit sich keine Änderungen überschreiben.
- **Lange Läufe** (Downloads, Tile-Builds) im Hintergrund starten und das Log nach `logs/` schreiben, damit ein Abbruch nachvollziehbar bleibt.
- **Geheimnisse** (API-Keys, Scalingo-Token) nie ins Repo. Sie gehören in `.env`, und `.env` steht in `.gitignore`.

## Koordinaten
Wie beim Reel: lokale Meter mit Ursprung LV95 (2681400, 1248700), z0 = 408 m ü. M., x = Ost, y = Nord. Damit lassen sich die Reel-Daten direkt wiederverwenden. Im Spiel (Three.js, y = oben) gilt: `three.x = x`, `three.y = z`, `three.z = -y`.
