# Zone 4 Erdgeschoss (Auftrag ZC)

Mechanismus: Kachel-`signs[].v` aus `pipeline/shopfronts_v3.py` (Fotonotizen `research/shops_v3`). Neu: Overrides `pipeline/overrides/storefronts_z*.json` (Schluessel OSM-Id ohne n/w/r, `name` = Schildname, `v` = Notizen b/f/s/a/as/t/p) ueberschreiben die Fotonotizen; `display_name()` setzt umbenannte Namen. Hook in `shopfronts_v3.py` und `props.signs` (eine Zeile).

Erledigt (6 Laeden geprueft, Ergebnis in `zone4_shops.json`): Beke -> Babette (Bertastrasse 16, rote Markise, Tische), Bottega Berta, Et Cetera (neu 2026), Le Calvados (Terrasse), Berta Bar (Aussensitze), WheelHouse (Schildfarbe grob).

Grenzen: Die Kontaktboegen (Handy-/Dashcam-Fotos) zeigen fast keine lesbaren Ladenfronten; Schild- und Markisenfarben der uebrigen ~300 Laeden ohne Foto NICHT erfunden, bleiben Hash-Defaults. Idaplatz hat Aussentische (gtable) und Velostaender mit Velos schon in `places_detail_idaplatz.json`; Wandvelos und Cafe-Personen kommen prozedural (props.wall_bikes, pedspots). Kein Override-Mechanismus fuer bikes/pedspots: nicht gebaut (build_testarea.py tabu).
Offen: Fotos an Ladenfronten Birmensdorfer-/Zurlindenstrasse (Streetlevel-Naheinstellungen), Webpruefung der uebrigen Prio-Laeden.
