# Korrekturen von Spielern («Stimmt etwas nicht?»)

Menü → «Stimmt etwas nicht?» öffnet das Mailprogramm mit einer Mail an daniel.gnaegi@protonmail.com (kein Server, `web/src/ui/report.ts`).
Vorausgefüllt: Betreff «Sandbox Zürich – Korrektur», Koordinate lokal (x/y in m) und WGS84, Blickrichtung, Spielzeit, Kachel, Gerät, Link `?at=…`.
Der Spieler schreibt oben, was nicht stimmt, und hängt gern ein Foto an. Der Block unter «--- automatisch eingefügt ---» bleibt stehen.

## Ablauf
1. Mail als Textdatei speichern (z. B. `research/corrections_in/mail_001.txt`), Foto daneben legen (Foto nur als Referenz, nie als Textur).
2. Einlesen: `.venv/bin/python pipeline/apply_corrections.py --mail research/corrections_in/mail_001.txt --list`
   → neuer Eintrag mit Status `open` in `pipeline/overrides/corrections.json` (id = Hash aus Ort + Text, doppelt eingelesen = kein Duplikat).
3. Mehrere auf einmal: `--csv fixes.csv` (Spalten `x,y,kind,value,note` oder `lat,lon,…`) oder `--json fixes.json` (Liste von Objekten).
4. Prüfen (Ort im Spiel mit dem Link aus der Mail, echte Quelle suchen), dann in `corrections.json` `kind` und `status` setzen:
   - `kind: drop_detail`, `status: ok` → `--apply` trägt `{x,y}` in `pipeline/overrides/details.json` unter `drop` ein (Status wird `applied`).
   - `kind: note` → nur Protokoll. Weitere Kinds (Name, Höhe, Fassade …) werden in `apply_corrections.py` als Handler ergänzt, wenn sie gebraucht werden.
5. Danach Kacheln neu bauen (Overrides werden wie alle `pipeline/overrides/*.json` beim Build gelesen) und in `docs/HANDOFF.md` vermerken.

Regeln: keine personenbezogenen Angaben aus den Mails ins Repo übernehmen (nur Ort + Sachverhalt); Korrekturen brauchen eine Quelle (siehe `docs/DATA_SOURCES.md`).
