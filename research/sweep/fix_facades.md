# Fassaden-Tickets (Agent facades), 2026-10-23

| Ticket | Ursache | Fix | Dateien |
|---|---|---|---|
| #4 Westpark Bürobau | Zwei Landmarks deckten dieselbe Fläche (`Westpark (Galaxus)` k5w3 und `z5R2_westpark_office`, y 601..739): Z-Fighting, kein fehlendes Fenster. | z5R2-Modell deaktiviert (`DISABLED` in z5R2_houses.py, Eintrag aus landmarks_z5R2.json entfernt, merge + apply_names). Kein Tile-Build nötig. | pipeline/landmarks/z5R2_houses.py, pipeline/overrides/landmarks_z5R2.json |
| #8 Hecken | `yards._shrubs`: Strauchbeet-Blobs mit fixem Radius bis 1.7 m, ragten über den Beetrand. | Radius je Blob auf Abstand zum Beetrand begrenzt (EDT). Blobs auf dem Beet bleiben gross (Beet ist breit); Ragen auf Trottoir behoben. | pipeline/yards.py |
| #12 schwarze Quads | Gully-Decal (Kind 2): fast schwarze Platte, 0.55x0.36 m, auch mitten auf der Fahrbahn. | Textur heller (Gusseisenrahmen + Schlitze), 0.46x0.30 m (web/src/world/decals.ts, sofort wirksam). Platzierung: nur im Streifen 1.1 m um den echten Fahrbahnrand (props.decals, braucht Neubau aller Kacheln). | web/src/world/decals.ts, pipeline/props.py |
| #6/#7/#9 Keile in Fassaden | NICHT behoben. Versucht: koplanare swissBUILDINGS3D-Dreiecke mit gemeinsamer Textur-Phase und gemeinsamem Brandmauer-Entscheid (Patch: scratchpad/facades/facade_grouping.patch, wieder entfernt, weil ohne sichtbaren Effekt). Die treppenförmigen Fenster/Läden bleiben, Ursache liegt woanders (Verdacht: Fassadentextur-Variante oder Dreiecks-Überlappung mit anderer Ebene d ±0.1 m). Nächster Schritt: Textur-Layer des Hauses ID_BCCDA8D0 (Hardstrasse) einzeln ansehen. | - |
| #15 Canopy | Dach wirkt plausibel (Loch fuer Rundkiosk), nicht geaendert. | - | - |
| #16 Bus-Gelenk | Faltenbalg bewusst dunkel (echte Gelenkbusse), nicht geaendert. | - | - |
| #18 Sora Sushi | Namensschild (nf=1) hängt auf z0+3.45, z0 liegt am HB bis 0.8-4.6 m unter dem Terrain; Schild/Fassadenfläche der versteckten HB-Halle. Nicht behoben. | - | - |

Kacheln gebaut: 0_-3, -3_-4, -2_-2, 6_-1, -5_-1, -6_0, -2_-4 (yards/props/Decals). -2_-2, 6_-1, -5_-1 enthalten noch die (zurückgenommene) Gruppierung, sichtbar unverändert.
Noch zu bauen: Gully-Platzierung (props.py) und Strauch-Radius (yards.py) wirken stadtweit erst nach Komplett-Build. decals.ts (Textur) ist sofort aktiv.

DECISIONS-Entwurf: Landmark-Duplikate (zwei Modelle auf derselben Fläche) führen zu Z-Fighting; z5R2_westpark_office abgeschaltet, k5w3_westpark bleibt.
