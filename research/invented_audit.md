# Audit: zufällig/per Hash platzierte Objekte (2026-10-20)

Frage: Was sieht aus wie ein echtes, fest stehendes Objekt, hat aber keine Datengrundlage?

| Quelle | Was | Urteil |
|---|---|---|
| `props.construction` | Gerüste + Bauzaun an Hauptstrassen (Hash), «Im Bau» 2019 | **erfunden → entfernt (#62)** |
| `sites.py` | Bagger/Kegel/Container innerhalb echter OGD/OSM-Baustellen | ok (Variation in echten Flächen) |
| `cityprops.py` | Velos/Mopeds in echten Velo-Ständern/Parkfeldern | ok |
| `yards.py` | Strauchgrösse/-farbe aus nDSM, Hofinventar (Wäscheständer, Sandkasten, Velohaus) | ok/unsichtbar von der Strasse |
| `props.wild_posters`, `props.graffiti`, `props.scooters`, `lawn_spots` | Stimmung (wie Leute/Autos) | bewusst so, kein echtes Objekt vorgetäuscht |
| `places_detail.py` (seed/spacing) | Streuung innerhalb belegter Platzflächen | ok |
| Fassaden-/Ladenfarben ohne Notiz | Hash-Defaults | bekannt (Lehre 1/6), kein neues Ticket |

Ergebnis: nur die Gerüste waren ein echtes Problem.
