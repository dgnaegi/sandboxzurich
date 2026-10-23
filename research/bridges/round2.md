# Brücken Runde 2 (Agent bridge2, 2026-10-22/23)

## Erledigt
1. **Treppen** (`bridges._stairs`, `_limit_foot_drop`, TS `stairs()` in `web/src/world/bridges.ts`): `highway=steps` werden nur noch gesammelt (nicht als Kettenglied). Ein Fussweg-Deck, das > 0.8 m über Grund endet und kein anderes Deck-Ende in 4 m hat, bekommt ein Treppen-Deck (`st:1`, 2.2 m breit, massiv bis Grund, Treppenstufen 0.17 m im Client; Begehen über die glatte Rampe): entlang der OSM-Treppe, die <= 4 m vom Ende beginnt (3 Fälle), sonst geradeaus mit 0.45 Gefälle (16 Fälle); Abbruch bei Gebäude im Korridor. Zusätzlich darf ein Fussweg-Profil von keinem höheren Punkt schneller als 0.45/m fallen (LiDAR-Plateau nach Regelrampe, Hardbrücke (49,122): Klippe 3.8 m -> Rampe 0.29). Betrifft 19 Treppen, 16 Fussketten.
   Treppen-Orte: (65,140), (-142,-172), (-162,-166), (1115,-1428), (240,-603), (1405,-828), (1920,-460), (1963,-594), (1191,-1218), (1196,-1206), (1384,-1529), (-1662,1550), (599,1215), (405,1241), (-949,1256).
   Die meisten T3/T5/T7-Enden hatten KEINE OSM-Treppe in der Nähe (> 9 m): sie bekommen die geradeaus-Treppe.
2. **Hardbrücke Nord** (2_4): Ursache war `_follow_parallel`: das Tram (514,865) folgte dem "nächsten" Strassendeck = Hardbrücke-Hauptdeck (+2.5) statt der Wipkingerbrücke (-5.5), Rampe 8.5 m in 18 m. Fix: `z_rule` (Regelhöhe vor LiDAR) merken; nur Strassendecks innerhalb `FOLLOW_RULE_DZ` = 4.5 m der Regelhöhe zählen. Tram bleibt flach auf -5.5. Verbleibender Audit-Befund "stack tram dz 8" bei (515,863) ist real (Hardbrücke überspannt die Wipkingerbrücke, Sicht-Check `preview/bridge2_nord.jpg`).
3. **Kalkbreite K-1** (355,-1094): Naht Deck/Boden war die Deckfarbe (0x3c3d40 -> gerendert (59,66,81)) gegen Boden-Asphalt (89,87,86). Strassen-/Tramdeck jetzt 0x544e47 (gerendert (87,86,88)), wirkt auf alle Brücken. Vorher/nachher `preview/bridge2_k1_top_{before,after}.jpg`. Rest (Randstein-Waisen an den Rundungen, schräge Kante, Einschnitt breiter als Deck) bleibt Ticket K-1.
4. **T-G3 Bodenstufen** (1322,-632), (1622,66), (-548,1236), (1550,124), (1504,175): keine Brückendecks in 25 m; es sind Gelände-/road_height-Hänge (Freischützgasse = steiler Pflasterhang, Wasserwerkstrasse = Böschung vor Tunnelportal, Am Wasser = Treppen/Hang). Kein Deckproblem, Ursache in `road_height`/Terrain: Ticket für den Terrain-Agenten.
5. Audit: `audit_decks.py` ignoriert Steigung/Knick bei `st`-Decks.

## Offene Tickets
- Hardbrücke West (-1_-1): Deck 4 "Hardbrücke" 3.2 m (-67,-48) schwebt 5.9 m über Grund (Openend 9.7), Tram (-77,-63)->(-45,-17) hat Buckel von -5.9 auf +0.1 (unter dem Hauptdeck angehoben, gleiche Klasse wie #75, `_follow_parallel` greift nicht, vermutlich LiDAR-Kreuzung). Nicht behoben.
- (583,999)/(574,999) Hardbrücke Nord: Ende 1.1 m über Grund = Gebietsrand (AREA), ignorieren.
- K-1 Randstein-Waisen, Z2b-2/Z2c-2 (Fachwerk/Bogen), T6 Bahndecks.
- Neu zu bauen (Komplett-Build ohnehin): alle Treppen-Kacheln ausser den gebauten (0_0, 0_1, -1_-1, 1_-4, 5_-8, 2_4, 2_3, 1_-6).
- Eingang Koordinator (glitches.md): (376,-480) Brauerstrasse, (186,-666) Seebahnstrasse Trog, (-1972,925), (-828,-178), (-1097,117): nicht bearbeitet, keine Deck-Ursache geprüft.

## Entwurf DECISIONS
**#78 – Treppen für schwebende Fussweg-Decks, Deckfarbe = Bodenasphalt.** `bridges._stairs` hängt an Fussweg-Deck-Enden > 0.8 m über Grund ein Treppen-Deck (`st`) an (OSM-Treppe oder geradeaus 0.45); `_limit_foot_drop` begrenzt das Fussweg-Gefälle auf 0.45; `_follow_parallel` folgt nur Strassendecks nahe der Regelhöhe (`z_rule`, 4.5 m). Strassen-/Tramdeck-Farbe 0x544e47 (passt zum Boden-Asphalt).

## Messwerte
Audit vor: 326 (stack 15, kink 86, openend 48, steep 159, buried 18) - nach (8 neu gebaute Kacheln, Rest alt): 327 (stack 18, openend 44, kink 91, steep 171, buried 3); Log `logs/bridge2_audit1.log`. bridges_ride bridge2a: 97 Fahrten, 49 Probleme, stuck 14, fell 2, crashes 6 (= Baseline).
