# Bruecken: Gleise und Markierungen (Z3b-6)
Ursache: Deck-Geometrie entsteht zur Laufzeit (web/src/world/bridges.ts) aus Zeilen von pipeline/bridges.py. Gleise (tram_track.py), Linien und Zebras
werden nur aufs Terrain gedrapt und von der Bruecken-Exklusion (EX) unter dem Deck entfernt: auf Tram-/Strassendecks blieb nichts.
Loesung: bridges.ts zeichnet auf Decks kind=tram zwei Schienenkoepfe (+-0.5 m, Meterspur) und auf Strassendecks Zebrastreifen (gelb) aus
`zb` (bridges.py `_zebras`: OSM highway=crossing innerhalb 2.5 m der Deck-Kette, Deck >= 1 m ueber Terrain). Gelaender: Oberkante 1.1 m (vorher 1.46 m).
Betroffen: alle 23 Tram-Decks (Schienen); Zebras auf 14 Strassendecks (u.a. Hohlstrasse, Hardbruecke, Zweierstrasse, Sihlhoelzli, Kanzlei, Zollbruecke).
Offen: Randlinien/Mittellinien gelb/weiss aus streets.markings (setzt S voraus) nicht auf Decks; nur die bestehende weisse Mittellinie.
