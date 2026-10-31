# NPC-Sprechblasen in Züritüütsch (Vorschlag, 2026-10-31)

Die Sprechblasen der Passant:innen (`web/src/ui/chatter.ts`) waren Hochdeutsch. Vorschlag: gesprochene Mundart mit
Swisscore-/Züricore-Satire (liebevolle Klischees über Zürich und seine Typen), weil auf der Strasse niemand
Hochdeutsch redet. UI-Texte bleiben Hochdeutsch (CLAUDE.md). Der Entscheid liegt beim Maintainer; bis dahin ist die
Kopfzeile in `chatter.ts` entsprechend markiert.

## Stand der Freigabe (2026-10-31)
- **Aktiv** (`chatLine()` benutzt sie): die vom Fork-Owner genannten Zeilen (`OWNER`: «So en Lappe!», «Bisch scho imne
  Verein?», «Angst und Geld hani kei.», «Hey, gömmer Bulle go schlah?», «Multipli hundert.», «Chatsy.», die
  California-Zeile; dazu «Hesch Termin?» auf dem Trottinett und «Voll wüests Auto.» im Auto) und die Originalzeilen des
  Maintainers eins zu eins übersetzt (Begrüssungen, Morgen, Mittag, Feierabend, Nacht, Wochenende, Orte).
- **Reserve** (`RESERVE` in `chatter.ts`, nicht in Gebrauch): alles Recherchierte und Komponierte aus den Abschnitten
  unten. Tester:innen sollen zuerst über die Insider lachen; was gefällt, wird von Hand aus `RESERVE` in den
  passenden Pool verschoben. Schreibweise der Owner-Zeilen wie geliefert (z. B. «Geld», nicht «Gäld»).
- Hinweis zu «Hey, gömmer Bulle go schlah?»: Berührt `CONTENT_GUIDELINES` («keine Gewalt gegen Menschen, Polizei
  comichaft»). Es ist eine Sprechblase ohne Folgen im Spiel; der Maintainer entscheidet, ob sie bleibt.

## Regeln (CONTENT_GUIDELINES)
- Keine echten Politiker:innen, Parteien oder Privatpersonen. Echte Läden/Firmen höchstens neutral erwähnt
  (Migros/Coop als Kulturfrage, Xenix als Kino, Volkshaus als Treffpunkt), nie als Ziel des Spotts.
- Keine Slurs, keine Gewalt; Polizei nur comichaft («Tschugger»). Milde Zürcher Schimpfwörter (Lappe, Tubel, Galööri,
  Halbschue, Stürmi) sind drin, das Derbere nicht.
- Zeilen kurz (≤ ~60 Zeichen), damit die Blase auf dem Handy passt (`#bubble` darf neu umbrechen).

## Schreibweise (Internet-Züritüütsch, keine Dieth-Orthografie)
- `ch` statt k (Chind, chasch, Chreis), `sch` vor Konsonant und in -st- (isch, bisch, hesch, Tourischt).
- Zürcher Verneinung `nöd` (nicht Berner `nid`), `nanig` = noch nicht, `hät` als Zürich-Marker, `dete` = dort.
- Lange Vokale doppelt (Ziit, Züri, tüür, Stüüre), `ä` für offenes e (gäll, Läbe), nur ss.
- Z-Mahlzeiten (Zmorge, Znüni, Zmittag, Znacht), -li überall (Gipfeli, Weggli, Trotti).

## Kontexte und Gewichtung
- Immer: Begrüssungen/Allgemeines + Klischees (Bünzli, Seefeld, Kreis-5-Startup, Expat; Englisch = Expats).
- Fortbewegung ×3 (`ChatCtx.mode`): rennen, Velo, Trottinett («Hesch Termin?» doppelt), Auto («Voll wüests Auto.»),
  Tram/Bus als Fahrer:in. Zu Fuss keine Extra-Zeilen.
- Ort ×2 (Langstrasse, Helvetiaplatz/Kanzlei, Limmatplatz/Hardbrücke, Stauffacher, HB, Parks), Tageszeit ×2
  (Morgen, Mittag, Feierabend, Nacht), Wochenende, Sonntag/Ruhezeit ×2.

## Quellen (Zeilen belegt «A» oder im Stil komponiert «C», Liste im Agent-Protokoll der Recherche)
- Wortschatz/Redewendungen: zuerich.com «Zürichdeutsch», SRF Virus «15 besten Kraftausdrücke», SRF 1 Mundart
  «Zürischnure», zuri.net Slängikon, iamexpat.ch (typische Zürcher Wörter; Bünzli-Erklärung mit Reddit-Zitat
  «Punkt Zähni»), lingoda.com (Sprichwörter, Schimpfwörter), lingvist.com (Slang).
- Jugendwörter 2026 (ZHAW-Medienmitteilung): «würd mi», «nöd so deep», «peak».
- Zürich-Klischees: Tumblr «when you really live in Zurich» (via newlyswissed.com und SRF Kultur), 20min über
  KI-«Durchschnittsschweizer» (Polo, On-Schuhe, Garmin; Gemeinde-Job), NZZ-Titel «Seefeld, wo der neurotische
  Bürger wohnt», Wikipedia Goldküste/Pfnüselküste, Blick zu E-Trottis (Statistik Stürze) und zu US-Expat-Wünschen
  (entpersonalisiert), Vice «Langstrasse» (Soja-Chai-Latte/Gentrifizierung), SRF News «Bei Anruf Ruhe» und
  Expat-Einsamkeit, nau.ch Velos auf dem Trottoir, Martin Suter über das Tram (Tagesspiegel).
- Nicht gefunden: eine Presse- oder Meme-Dokumentation unter dem Namen «Swisscore»/«Züricore»; Reddit war für
  die Recherche gesperrt (nur indirekt zitiert). Wer dort Material findet: einfach Zeilen in `chatter.ts` ergänzen.

## Bewusst weggelassen
- Derbe Flüche (Schofseckel u. ä.), Zitate gegen Nationalitäten («Scheiss Dütsche»), Zeilen mit echten Parteien
  (Hundesteuer-Debatte), Zeilen, die eine echte Firma verspotten (Sternen-Grill-Senf, Osterhase-Coop, Porsche-Dichte
  als Marken-Witz; die Porsche-Zeile zielt auf das Seefeld, nicht auf die Marke), zu lange Basel-Witze.
