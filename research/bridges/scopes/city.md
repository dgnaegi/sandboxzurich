# City-wide run of the ramp builder

Generated 2026-10-31 by `pipeline/scopes/city.py`: every site built and scored on its own against the live world (scratch copy of the tiles); automatic sites from `pipeline/scopes/discover.py`. Full reports in `data/build/scopes/city/reports/` (not in git; rerun to regenerate).

Count: PASS 28, REVIEW 2 of 30 sites; REVIEW at helices (parking-garage spirals, out of scope for a bridge-ramp builder): 2.

| Site | kind | verdict | outline IoU live → v2 | width live → v2 (cadastre) | piers modelled / under deck | height p95 | failing checks |
|---|---|---|---|---|---|---|---|
| Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower) (`gerold`) | hand | PASS | 0.37 → 0.98 | 3.2 → 8.1 (8.1) m | 11 / 11 | 0.17 m |  |
| Duttweilerbrücke south ramp (`duttweiler`) | hand | PASS | 0.43 → 0.99 | 6.4 → 14.0 (14.1) m | 30 / 28 | 0.01 m |  |
| Hardbrücke access ramp from Pfingstweidstrasse (`pfingstweid`) | hand | PASS | 0.33 → 1.00 | 3.5 → 10.0 (10.0) m | 1 / 1 | 0.02 m |  |
| Hardbrücke Nord: Hardturmrampe and Sihlquai ramps at the Wipkingerbrücke (`wipkingen`) | hand | PASS | 0.45 → 0.99 | 3.2 → 6.5 (6.5) m | 15 / 14 | 0.01 m |  |
| Hohlstrasse bridge and Brauerstrasse ramp (over the Sihl line tracks) (`brauer`) | hand | PASS | 0.54 → 1.00 | 6.4 → 8.8 (8.7) m | 0 / 0 | 0.10 m |  |
| Hardbrücke (15 chains, 3308 m) (`auto_hardbrucke`) | auto | PASS | 0.64 → 0.98 | 9.6 → 9.0 (9.0) m | 123 / 119 | 0.08 m |  |
| Europabrücke (11 chains, 1338 m) (`auto_europabrucke`) | auto | PASS | 0.62 → 0.99 | 6.4 → 9.9 (9.9) m | 36 / 36 | 0.08 m |  |
| Sihlbrücke (3 chains, 233 m) (`auto_sihlbrucke`) | auto | PASS | 0.53 → 1.00 | 6.4 → 7.4 (7.4) m | 0 / 0 | 0.09 m |  |
| Kornhausbrücke (1 chain, 208 m) (`auto_kornhausbrucke`) | auto | PASS | 0.69 → 1.00 | 12.8 → 18.4 (18.4) m | 2 / 2 | 0.01 m |  |
| unnamed elevated road (1 chain, 197 m) (`auto_unnamed_m58_m123`) | auto | PASS | 0.42 → 0.99 | 3.2 → 5.6 (5.6) m | 7 / 6 | 0.01 m |  |
| Walchebrücke (3 chains, 185 m) (`auto_walchebrucke`) | auto | PASS | 0.61 → 0.98 | 6.4 → 11.3 (11.3) m | 2 / 2 | – m |  |
| unnamed elevated road (1 chain, 183 m) (`auto_unnamed_m2000_18`) | auto, helix | REVIEW | 0.46 → 0.84 | 3.2 → 4.5 (4.5) m | 0 / 0 | – m | edge overshoot p95 (m); uncovered width p95 (m, any deck row counts) |
| unnamed elevated road (1 chain, 155 m) (`auto_unnamed_m845_712`) | auto | PASS | 0.57 → 0.99 | 3.5 → 5.7 (5.7) m | 7 / 7 | – m |  |
| Gessnerbrücke (2 chains, 133 m) (`auto_gessnerbrucke`) | auto | PASS | 0.31 → 0.99 | 3.4 → 10.9 (11.0) m | 1 / 1 | 0.11 m |  |
| Bahnhofbrücke (3 chains, 121 m) (`auto_bahnhofbrucke`) | auto | PASS | 0.47 → 0.99 | 6.4 → 11.1 (11.1) m | 3 / 3 | 0.09 m |  |
| Bändlistrasse (1 chain, 100 m) (`auto_bandlistrasse`) | auto | PASS | 0.41 → 1.00 | 6.4 → 15.4 (15.4) m | 8 / 8 | 0.00 m |  |
| unnamed elevated road (2 chains, 91 m) (`auto_unnamed_1069_173`) | auto, helix | REVIEW | 0.30 → 0.61 | 3.2 → 4.2 (3.5) m | 0 / 0 | – m | outline IoU; uncovered width p95 (m, any deck row counts) |
| unnamed elevated road (1 chain, 85 m) (`auto_unnamed_m960_694`) | auto | PASS | 0.37 → 0.99 | 3.5 → 8.1 (8.1) m | 0 / 0 | – m |  |
| Militärbrücke (1 chain, 74 m) (`auto_militarbrucke`) | auto | PASS | 0.66 → 1.00 | 3.2 → 4.8 (4.8) m | 2 / 2 | 0.01 m |  |
| Remisenstrasse (1 chain, 64 m) (`auto_remisenstrasse`) | auto | PASS | 0.46 → 0.94 | 3.5 → 7.0 (7.0) m | 0 / 0 | 0.07 m |  |
| Pfingstweidbrücke (1 chain, 58 m) (`auto_pfingstweidbrucke`) | auto | PASS | 0.00 → 1.00 | – → 8.0 (8.0) m | 1 / 1 | 0.02 m |  |
| Sihlhölzlibrücke (1 chain, 56 m) (`auto_sihlholzlibrucke`) | auto | PASS | 0.72 → 1.00 | 9.6 → 13.2 (13.1) m | 0 / 0 | 0.09 m |  |
| Kanzleistrasse (1 chain, 56 m) (`auto_kanzleistrasse`) | auto | PASS | 0.47 → 1.00 | 7.0 → 15.0 (15.0) m | 0 / 0 | 0.03 m |  |
| Stauffacherstrasse (1 chain, 54 m) (`auto_stauffacherstrasse`) | auto | PASS | 0.31 → 1.00 | 6.4 → 21.0 (21.0) m | 0 / 0 | 0.05 m |  |
| Badenerstrasse (1 chain, 49 m) (`auto_badenerstrasse`) | auto | PASS | 0.48 → 0.98 | 9.6 → 17.2 (17.2) m | 0 / 0 | 0.10 m |  |
| Sihlhochstrasse (1 chain, 48 m) (`auto_sihlhochstrasse`) | auto | PASS | 0.00 → 0.00 | – → – (–) m | 0 / 0 | – m |  |
| Sihlhölzlibrücke (1 chain, 48 m) (`auto_sihlholzlibrucke_2`) | auto | PASS | 0.57 → 0.99 | 6.4 → 10.7 (10.7) m | 0 / 0 | 0.04 m |  |
| Zweierstrasse (1 chain, 47 m) (`auto_zweierstrasse`) | auto | PASS | 0.53 → 0.99 | 9.6 → 18.0 (18.0) m | 18 / 15 | 0.06 m |  |
| Stauffacherbrücke (1 chain, 46 m) (`auto_stauffacherbrucke`) | auto | PASS | 0.59 → 1.00 | 12.8 → 21.8 (21.8) m | 0 / 0 | 0.11 m |  |
| Kalkbreitestrasse (1 chain, 46 m) (`auto_kalkbreitestrasse`) | auto | PASS | 0.54 → 1.00 | 9.6 → 18.0 (18.0) m | 0 / 0 | 0.06 m |  |

## Findings for other decks (not the ramp's error)

- `auto_unnamed_m58_m123`: junction partner at (-58,-30) lies -4.3 m off the LiDAR deck surface; ramp kept on LiDAR, the partner deck needs its own fix

## Ride gate with all 30 sites in one tile set

`ramp_build.py <all sites> --write` (82 s), then `bridges_ride.mjs city "" car,bike,foot --gate`:

GATE FAIL vs baseline 2026-10-31 (base): problems 42 -> 37, not across 17 -> 14 (stuck 14 -> 11, fell 2 -> 2, crash 1 -> 1, error 0 -> 0), 10 rides not in the baseline, 8 baseline rides not run

Rides vs baseline base (2026-10-31): 14 better, 2 worse, 2 new

Better:
- Duttweilerbrücke (car): raw → raw, progress 183 → 632 of 638 m
- Hohlstrasse (bike): stuck → jump, progress 96 → 125 of 130 m
- Hohlstrasse (car): stuck → crash, progress 133 → 293 of 298 m
- Kalkbreitestrasse (bike): jump → ok, progress 288 → 288 of 294 m
- Kalkbreitestrasse (car): crash → ok, progress 225 → 225 of 231 m
- Kalkbreitestrasse (foot): jump → ok, progress 288 → 288 of 294 m
- Kanzleistrasse (foot): raw → ok, progress 262 → 262 of 267 m
- Kornhausbrücke (foot): raw → ok, progress 199 → 199 of 204 m
- Stauffacherstrasse (car): fell → raw, progress 218 → 173 of 249 m
- Wipkingerbrücke (bike): crash → jump, progress 41 → 119 of 124 m
- Wipkingerbrücke (car): crash → raw, progress 114 → 114 of 120 m
- Zweierstrasse (bike): jump → ok, progress 115 → 115 of 121 m
- Zweierstrasse (car): raw → ok, progress 210 → 210 of 215 m
- Zweierstrasse (foot): jump → ok, progress 115 → 115 of 121 m

Worse:
- Kornhausbrücke (bike): raw → jump, progress 199 → 199 of 204 m
- Kornhausbrücke (car): jump → fell, progress 63 → 183 of 189 m

New:
- Geroldrampe up via the north branch (car): raw, progress 257 of 262 m (new route)
- Geroldrampe up via the south branch (car): raw, progress 285 of 290 m (new route)

The one regression is not a builder error: the Kornhausbrücke car used to stop after 63 m; with the rebuilt bridge it drives 183 m
and falls off the far end of a live footway deck (`t_6_0` row 2, unnamed, 87 m) that ends 2.4 m in the air at (1200, 134) above
a game terrain 6.7 m too low. Footway decks are outside the builder (road rows only); see README «How to continue».

