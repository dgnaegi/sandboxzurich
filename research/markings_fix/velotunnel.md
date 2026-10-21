# Velotunnel Stadttunnel: Markierungen (Spec fuer die Umsetzung)

Befund im Code (pipeline/landmarks/velotunnel.py, build()): Die «weissen Rechtecke» sind die Boden-Piktogramm-Quads (Schleife «pictograms every 24 m»).
Sie nutzen die Textur-Zelle mit weissem Hintergrund (Atlas ohne Alpha, Material hb3_lit) und erscheinen als weisse Rechtecke; die Fahrrad-Skizze ist
frei erfunden (blau auf weiss). Ausserdem sind Mittel- und Randlinien (0.12 m, LANE #d8d8d0) nicht belegt.

Quellen (Websuche 2026-10-21, keine Fotos/Markierungsdetails publiziert in den gefundenen Texten):
- Baunetzwissen «Stadttunnel Zuerich»: Sichtbeton bleibt roh, Roehre 6 m breit, ca. 320 m Rohbau.
- Domus 2025-06-16, SRF-Testfahrer-Bericht: Eroeffnung 22.5.2025, Velo/E-Bike/S-Pedelec/E-Moped, Tempo 20, keine Fussgaenger, Zweirichtung.
- Fotos (Wikimedia Commons / Panoramax) NICHT geprueft: kein Beleg fuer Piktogramme oder Pfeile.

Empfehlung (konservativ, «keine Markierung ohne Beleg»):
1. Piktogramm-Quads entfernen (nicht durch neue Erfindungen ersetzen).
2. Mittellinie: eine einzige durchgehende oder lange gestrichelte weisse Linie (CH: Gegenverkehr-Trennung auf Radweg: Leitlinie weiss, 12 cm, 3 m Strich / 6 m Luecke wie auf Strassen), Randlinien weglassen (Beton-Wandsockel genuegt).
3. Falls Fotos eine Veloroute-Beschilderung zeigen: ein einzelnes weisses Velo-Piktogramm (SSV 6.xx) am Portal je Richtung, geometrisch (Linien-Quads auf hb3_pit), nie als Textur mit weissem Hintergrund.
4. Offen: Eine Fotoprüfung (Commons-Kategorie «Velotunnel Zürich», Mapillary) steht aus.
