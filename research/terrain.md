# Terrain (swissALTI3D) – Vergleich mit alter IDW-Methode
- pipeline/terrain.py: heights(area, step) -> mesh.Heights; liest data/raw/alti3d/*.tif (tifffile+imagecodecs), bilinear auf Raster, Cache data/build/terrain_<area>_<step>.npz. z = H - 408.
- Laufzeit 600x600 m, step 1: kalt ~1.0 s, mit Cache ~0.005 s (Budget < 5 s).
- DTM-Bereich im Testgebiet: -9.1 .. +4.4 m (Mittel +1.0 m), also 399-412 m ü. M. (plausibel).
- Vergleich an 547 Gebaeuden (GroundSurface min z, Mittel pro Gebaeude) vs DTM(x,y) am Schwerpunkt:
  - Systematischer Offset DTM - Gebaeudesockel: Mittel +3.06 m, Median +2.90 m (Gebaeudedaten/Reel-z0 liegen ~3 m tiefer).
  - Nach Abzug des Offsets: Streuung sd 0.54 m, robust (MAD) 0.16 m -> Form stimmt, nur Versatz.
  - 20 Zufallsgebaeude: Bias +3.03, sd 0.41, min/max +2.41/+4.39 m.
- Folge: Gelände und Gebäude müssen konsistent sein. Entweder Gebäude-z um +3.06 m heben oder Terrain um -3.06 m senken (Parameter z_shift in heights()).
