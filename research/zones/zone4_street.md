# Zone 4 Wiedikon: Strassenraum (Auftrag ZB, 2026-10-19)

## Boden
- Audit: `pipeline/audit_ground_z4.py` (AV-Bodenbedeckung vs. OSM-Fahrbahn). Spielgebiet endet bei y = -1810: Baseline #11 (30,-2126) liegt ausserhalb (Kulisse, Foto-GPS/Wiese+Baustellenwand), dort nichts zu beheben.
- Befund im Spielgebiet der Zone: AV-Fahrbahn ohne OSM-Strasse 8 250 m2 (Parkplaetze, Vorplaetze); **25 585 m2 AV-Strasse/Trottoir/Weg fielen im Hof-Zweig von `_ground_base` auf Rasen** (Friedhof Sihlfeld Wege 2 700 + 2 000 m2, Platzflaechen Idaplatz/Kalkbreite u.a.).
- Fix (`build_testarea.py`, `S["av_paved_ext"]` + Block in `_ground_base`): was von den Hoefen uebrig bleibt und in der AV Strasse/Trottoir/Weg ist, wird befestigt (roof_flat), nie Rasen. Gilt global, nur dort, wo vorher Rasen auf AV-Pflaster lag.

## Trottoirkante
- Hoehe war schon 12 cm (CURB), Rinnstein 22 cm; sichtbar zu duenn, weil die Kantenoberseite nur 16 cm breit und dunkel (205) war. Jetzt `CURB_TOP_W = 0.22`, Farbe (226,223,214): helle Granitkante wie auf den Fotos. Tramgleis-Teil unberuehrt.

## Markierungen
- `markings_override.py` liest jetzt zusaetzlich `overrides/markings_z<N>.json` (add_yellow/add_white/cut/decals), additiv. `markings_z4.json` ist leer (Handkorrekturen).
- Automatische Gelb-Messung aus SWISSIMAGE 0.25 m (`pipeline/markings_z4_measure.py`): 436 Treffer, aber Friedhofswege/Schatten (Kalkbreite-Kreuzung im Schatten: 0 Treffer) -> verworfen, nicht angewendet. Fotobeleg (Zurlinden/Kalkbreite): Velostreifen rot mit Pfeil, weisse Parkfeldlinien; bleibt offen (Tickets).
- Zone 4 Ist (Kacheldaten): Velopiktogramme 138, ZONE 30 89, gemaltes 30 nur 6, Schachtdeckel 361.

## Plaetze / Brunnen
- `places_detail_z4.json`: Boden aus SWISSIMAGE (`ortho_ground`) fuer Goldbrunnenplatz (r 45), Schmiede Wiedikon (r 40), Bahnhof Wiedikon Vorplatz (r 45). Objekte nicht ergaenzt: ohne Foto mit Position keine Erfindung (Goldbrunnenplatz: Glasdach-Wartehalle, Uhrenmast, Bancomat-Haeuschen; Schmiede: Veloinsel).
- Idaplatz: Katalog-V2-Trog BR-269 (-142,-1095) war ein zweiter, falscher Brunnen neben dem Trinkbrunnen (`dfount` in places_detail_idaplatz.json) -> in `catalog_assign.json` ausgeschlossen, catalog.json neu erzeugt.
- Brupbacherplatz BR-278: bereits runder Reliefbrunnen (squares2). Fotos zeigen an den anderen Zone-4-Brunnen (Goldbrunnen, Bahnhof, Schmiede, Aemtler 23) keinen Brunnen -> Katalogvarianten unbestaetigt, unveraendert. Keine `fountain_z4_*.py` noetig (kein Einzelmodell mit Foto belegt).
