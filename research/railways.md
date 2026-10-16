# Railways (Gleisfeld, Bahnhoefe, Zuege) - Stand v2 (2026-10-16)
Quellen: OSM railway=rail inkl. Attribute (service, usage, tracks, electrified, bridge/tunnel/layer/level, railway:track_ref, railway:preferred_direction,
Knoten railway=switch/signal/buffer_stop/railway_crossing; ODbL) via pipeline/sources.py (data/raw/osm/kreise.json); Gelaende swissALTI3D (z_shift -3.06);
Bruecken-Deckhoehen aus pipeline/bridges.py (DeckTrack, gleiche Hoehen wie das Bruecken-Mesh). swissTLM3D und SBB Open Data (data.sbb.ch) wurden NICHT
geladen: OSM ist im Perimeter pro Gleis gemappt (1038 yard-Ways, 1230 Weichen, 157 Signale, 211 Prellboecke), reicht fuer Achsen und Gleisnummern.
HB-Abgleich: research/hb/tracks.json (Prellboecke Gl. 3-18) liegt <= 4.4 m neben den OSM-Wayenden (railway:track_ref), Routen nutzen track_ref.

Pipeline (`.venv/bin/python pipeline/railways.py`, ~50 s):
- rail_net.py: Netz laden, 4-m-Samples, Hoehen = Terrain geglaettet ueber den ganzen Graphen (Weichen teilen eine Hoehe), Bruecken/Rampen = Deckhoehen
  (bridges.py), Tunnel sinken mit 4 % ab Portal (Klasse tunnel auch bei layer/level <= -2). Pro Gleis eine Achse (OSM-Way), keine verschobenen Linien.
- rail_build.py: Schotterbett (dunkel, Boeschung nur auf Hauptgleisen), Schwellen alle 1.6 m, Schienen (Kopf+Fuss), Douglas-Peucker auf Geraden (Tris -65 %);
  Weichen (Zungen, Herzstueck, Antriebskasten, aus OSM-Weichenknoten), Kreuzungen/Doppelte Kreuzungsweichen (Rauten), Signale (Mast+Kopf, Lampe rot/gruen,
  Seite/Richtung aus OSM), Prellboecke, Tunnelportale, Fahrleitungsmasten + Quertragwerke (Joche mit 2 Gurten) ab 3 Gleisen, abgestellte Zuege (rail.json `pk`).
- rail_routes.py: gerichteter Graph, Kurvenlimit 38 Grad (keine Spitzkehren), Rechtsfahrt (Gegengleis links => Aufpreis), platform_centre -> Halt in Perronmitte,
  Kopfbahnhof-Routen enden/starten 6 m vor dem Prellbock (`te`/`ts`, Client: Ankunft und Abfahrt desselben Zuges nahtlos).
- Dienste: S-Bahn Altstetten (Altstetten, Hardbruecke, HB Gl. 15), S-Bahn Wiedikon (Wiedikon, HB Gl. 9), IC Gl. 16/17, IR Gl. 18 (6 Wagen, 33/30 m/s, durchfahren
  Perrongleise nur mit Aufpreis). Beide Richtungen. Gl. 3-14 sind in OSM nur ueber yard-Ways erreichbar, daher nicht benutzt.
- Debug: pipeline/rail_plot.py (Netz+Routen PNG), pipeline/rail_shots.sh + rail_cmp.py (Draufsicht vs. SWISSIMAGE), web/tests/rail_shot.mjs (Freikamera, TRAIN=route:halt).
Offen: Durchmesserlinie (Weinbergtunnel) ist von den Hardbruecke-Perrongleisen im OSM-Graphen nicht erreichbar; S-Bahn endet daher am HB-Kopf.
Zuege: Modelle unveraendert (S-Bahn-Doppelstock, Kopf/Mittel); IC/IR = gleiche Modelle, 6 Wagen, andere Toenung (instanceColor).
