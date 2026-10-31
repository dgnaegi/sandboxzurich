Transfer site 3 (2026-11-01): Hardbrücke Nord at the Wipkingerbrücke with three ramps meeting the viaduct: the Hardturmrampe
from the west, the Sihlquai-Südrampe and the Sihlquai-Nordrampe from the east. The LiDAR tiles were ordered with
`pipeline/scopes/lidar_for_sites.py` (three tiles).

- **What the cadastre shows.** Three ramp chains of 170 to 190 m, each from grade up to a junction with the viaduct deck 7 to 8 m
  up; long stretches between thin edge polygons (fill between edge structures: 56 to 82 m per ramp), the rest bridge polygons.
  The two Sihlquai ramps run side by side east of the viaduct at different grades (one climbing, one descending) inside what
  the cadastre merges into one structure.
- **What the builder did, unchanged.** Widths 3.2 → 6.3 to 6.8 m (p50) from the cadastre, fill parts solid, all three mouths
  on the viaduct opened. Outline IoU 0.89 to 0.92, uncovered ≤ 0.2 m, verdict PASS.
- **Rules that had to change for this site:** two, both about neighbours that are not one surface. A sibling chain's height
  is only adopted where the LiDAR on the own axis agrees within 0.35 m (the first run dragged the climbing Nordrampe down to the
  descending Südrampe, a 24 % step); and the main deck's carriageway rows cut a ramp's slice at their edge, so a merge lane
  reaches the carriageway and a station on the main deck itself stays a flush lane (this also closed the Geroldrampe's
  fork gore and junction patches, which the first version of the uncovered measure had blamed on the ramp).
- **Open:** the strip between the two Sihlquai ramps is air in reality but one cadastre structure; the scorer no longer counts
  it (each chain is measured on its own share), the builder leaves it empty, correctly.
