# Ramps from reference scopes: what this is, where it stands, how to continue

Entry point for the ramp effort in the fork `jaenib/sandboxzurich` (branch `worktree-ramps`). Session log:
`research/bridges/ramps_handoff.md`; proposed decisions: `research/bridges/ramps_decisions_proposed.md`; plan:
`research/bridges/scopes_plan.md`. Nothing here is written into `docs/` on purpose (the maintainer's session contract).

## Goal

One deterministic tool that rebuilds every bridge ramp in the city from official references, plus a per-ramp score that says
whether the result can ship without a person looking at it. The hook in the maintainer's roadmap is the focus item
«Brücken-, Rampen- und Geländefehler stadtweit» (`docs/ROADMAP.md`); the ride gate and the deck audit are the maintainer's own
acceptance style, and this follows it: numbers per ramp, overlays for the eye, a gate for regressions.

## The vectors and their status

| Vector | Status | Where |
|---|---|---|
| Ride gate (`bridges_ride --gate`) against a committed baseline, dev proxy for live world data | implemented, PR-ready (R1) | `web/tests/bridges_ride.mjs`, `web/tests/fixtures/bridges_ride_baseline.json`, `web/vite.config.ts` |
| LiDAR pilot: band tracker, `wl`/`wr` per vertex in the client | implemented, superseded by the builder (R2); the client part (`wl`/`wr`, `ol`/`or`) stays | `pipeline/ramp_lidar.py`, `web/src/world/bridges.ts` |
| Scope B: cadastre fetch (Amtliche Vermessung via OGD-WFS), cached per site | implemented | `pipeline/scopes/scope_av.py`, `data/raw/av/` |
| Scorer: per-station measures against cadastre and LiDAR, per-site report, station tables | implemented | `pipeline/scopes/score.py`, `metrics.py`, `rows.py` |
| Top-down overlays (orthophoto, cadastre, LiDAR bridge class, live and current rows) | implemented | `pipeline/scopes/overlay.py` → `preview/scopes/` |
| Builder v2: rows from cadastre edges + LiDAR heights + cadastre piers, on the built tiles | implemented on three sites | `pipeline/scopes/ramp_build.py` |
| Joins: ramp mouths opened on the main deck and between sibling chains, flush sides, coplanar heights | implemented (the pipeline only joined side-by-side decks) | `pipeline/scopes/join.py` |
| Acceptance thresholds (PASS / REVIEW per ramp) | implemented in the scorer's verdict | `pipeline/scopes/score.py` |
| Transfer to more ramps (phase 4) | three done: Hohlstrasse / Brauerstrasse and the Pfingstweid ramp without a builder change, Hardbrücke Nord with two rules; all PASS | `pipeline/scopes/ramp_sites.py`, `lidar_for_sites.py`, `overlay.py --rows` |
| Improvements log and ride delta against the gate baseline | implemented | `improvements.md`, `pipeline/scopes/ride_delta.py` |
| Pull requests: gate + proxy (#4), scopes as draft (#5) | open on the maintainer's repository | `research/bridges/pr_drafts.md` |
| Site discovery and city-wide run | implemented: 25 automatic sites plus 5 hand sites, all 66 elevated road chains covered; 28 PASS, 2 REVIEW (both parking-garage helices) | `discover.py`, `city.py`, `city.md` |
| Footway decks beside rebuilt decks | implemented: trimmed where the new deck carries them, solid on embankments, air ends continued along the LiDAR ground | `footways.py` |
| Approaches over terrain holes | implemented: from each grade end, road-graph edges the new decks do not cover are followed on the LiDAR ground where the game terrain lies below it; width from the cadastre carriageway; no parapet | `ramp_build.Build.approaches` |
| Ride harness: clipped routes spawn on their deck | implemented (also in PR #4) | `web/tests/bridges_ride.mjs` |
| Scope C: imagery + vision helper for the lane / footway split and semantics | documented proposal (`scopes_plan.md` §2); not needed for the two sites | — |
| Site discovery (every elevated road chain instead of a hand list) | vision | — |
| Maintainer integration as a pipeline stage after `bridges.py` | vision | — |

## Results on five sites (2026-11-01)

Numbers from `score.py` (full reports `<site>.md`, pilot snapshot scores in `pilot/`); every row set is measured with the
same code. Outline IoU is station-wise against the chain's own share of the cadastre slice (other road decks and sibling chains
removed at the Voronoi boundary); "uncovered" is that share covered by no deck row at all. Gate line: PASS: stuck 14 → 12, fell 2 → 1, crashes 1 → 1 city-wide (99 rides, 50 with problems).

| Measure (live → v2) | Geroldrampe | Duttweiler south ramp | Hohlstrasse / Brauerstrasse | Pfingstweid ramp | Hardbrücke Nord (3 ramps) |
|---|---|---|---|---|---|
| Verdict (v2) | PASS | PASS | PASS | PASS | PASS |
| Outline IoU at ramp stations | 0.37 → 0.98 | 0.43 → 0.99 | 0.54 → 0.99 | 0.33 → 1.00 | 0.45 → 0.98 |
| Modelled width, median | 3.2 m → 8.1 m | 6.4 m → 14.2 m | 6.4 m → 8.8 m | 3.5 m → 10.0 m | 3.2 m → 6.5 m |
| Cadastre share width, median | 8.0 m → 8.1 m | 14.1 m → 14.1 m | 8.7 m → 8.7 m | 10.0 m → 10.0 m | 6.5 m → 6.5 m |
| Edge overshoot p50 / p95 | -1.5 m / +1.1 m → +0.0 m / +0.0 m | -3.3 m / -3.2 m → +0.0 m / +0.0 m | -0.8 m / -0.8 m → -0.0 m / +0.0 m | -1.7 m / -1.6 m → +0.0 m / +0.0 m | -1.5 m / -1.2 m → +0.0 m / +0.1 m |
| Uncovered share p50 / p95 | 4.4 m / 10.7 m → 0.0 m / 0.5 m | 3.8 m / 9.7 m → 0.0 m / 0.0 m | 2.5 m / 3.3 m → 0.0 m / 0.0 m | 3.5 m / 5.0 m → 0.0 m / 0.0 m | 3.3 m / 6.6 m → 0.0 m / 0.1 m |
| Tile piers / at a real pier | 10 / 2 → 11 / 11 | 68 / 8 → 34 / 30 | 16 / 0 → 5 / 0 | 11 / 0 → 6 / 1 | 23 / 8 → 17 / 15 |
| Height residual vs LiDAR p50 / p95 | -0.0 m / 0.1 m → -0.0 m / 0.2 m | -0.0 m / 1.0 m → -0.0 m / 0.0 m | -0.0 m / 0.1 m → +0.0 m / 0.1 m | -0.0 m / 0.0 m → -0.0 m / 0.0 m | -0.0 m / 0.0 m → -0.0 m / 0.0 m |
| Ride gate, rides on the site | 2 uphill routes: 0 crashes, raw steps ≤ 0.24 m | car 183 → 632 of 638 m | car and bike stuck → cross | (no route in the gate) | (routes in the gate: bike Sihlquai-Nordrampe: ok, bike Sihlquai-Nordrampe: ok, foot Sihlquai-Nordrampe: with findings, foot Sihlquai-Nordrampe: with findings) |

Remaining blemishes: 0.24 m raw-height steps where a car changes between overlapping rows at the Geroldrampe fork, the
Duttweiler landing wedge and its 1 m pedestrian step at (−595, 131), the walled approaches of three sites modelled as solid
blocks down to a game terrain that is 3 to 6.6 m too low (terrain pass), and the strip between the two Sihlquai ramps that is one
cadastre structure but air in reality (left empty, correctly).

## Where this stands on the spectrum «handles every ramp» … «promising on the sample»

Position after the city-wide run: near the «handles every ramp» end for road ramps and road bridges, with named limits.

- Every elevated road chain in the play area is a site (5 by hand, 25 discovered); PASS 28, REVIEW 2 of 30 sites; REVIEW at helices (parking-garage spirals, out of scope for a bridge-ramp builder): 2. The two REVIEW sites are
  parking-garage helices, which the scorer is right to flag; helices are classified automatically.
- Rules: eight on the two pilot sites, two on Hardbrücke Nord, then nine more on the city run (all generic: cadastre edge as a
  hard cap, landings and walls only over a raised LiDAR surface, junctions on the side of a deck, slope-limited junction blends,
  off-LiDAR junction partners reported instead of followed, short piers modelled, wider half-width limit, faster widening at
  skewed crossings, parallel chains merged into one site). The rule set grew on the first city pass and was stable on the
  second: the last full run changed no verdict on any site that had passed.
- One finding for another deck: the «Hardbrücke West» connector at (−58, −30) lies 4.3 m below the LiDAR deck (an open item in
  the maintainer's handoff); the ramp beside it stays on LiDAR and the report names the connector.
- Ride gate with all 30 sites, footways and approaches in one tile set: PASS; 25 rides better, 2 worse (bike steps of 0.36 and
  0.1 m at terrain-hole edges); stuck 14 → 8, fell 2 → 0, rides not across 17 → 10.
- Approaches patch terrain holes with solid street decks on the LiDAR ground where a road meets a bridge; that is a stopgap: the
  terrain itself is still wrong around them (reported per site, the terrain pass owns it).
- Not covered: tram decks, stairs, the terrain itself, helices.

## Deterministic vs interpreted

Deterministic, re-runnable, no model in the loop: fetch (B), rows, measure, build, score, overlay, shots, gate. One command per
step, seconds per site (the gate about ten minutes for the whole city). Nothing per site is hand-edited; the site registry holds
a name match and two boxes.

Interpreted (agent time, the costly part): reading overlays and numbers to decide the next rule; the thresholds
(`SIDE_MAX` 12 m, `THIN` 1.5 m, `TOL` 1.0 m, `MAIN_DECK` 24 m, `WALL_NEAR` 2.5 m); the site boxes; the readings in `*_notes.md`.
Over three phases that was roughly half of the agent time; the third site cost one run plus two scorer rules, no builder rule.
Marginal cost per further site with no new failure mode: the run (minutes); per new failure mode: one rule, typically half an
hour of agent time plus a rerun; the ride gate adds ten minutes per round.

## Acceptance thresholds (in the scorer's verdict, PASS / REVIEW)

- outline IoU ≥ 0.80 (station-wise, against the slice available to the chain: cadastre slice minus other road rows, halved
  towards sibling chains); edge overshoot p95 ≤ 0.5 m; uncovered cadastre width p95 ≤ 2.0 m (covered by any deck row counts)
- height residual vs LiDAR deck top p95 ≤ 0.3 m; the cadastre / wall structure ends at most 5 m beyond the modelled structure
- every cadastre pier under the modelled deck has a modelled pier within 2 m; ride gate passes
- terrain residual under the ramp reported separately (never blocks the ramp, feeds the terrain pass)

## How to run

```
python3 pipeline/scopes/scope_av.py gerold,duttweiler            # fetch and cache the cadastre (once)
python3 pipeline/scopes/lidar_for_sites.py <site>                # LiDAR tiles + grids a new site needs (ordered from the OGD geoportal)
python3 pipeline/scopes/overlay.py <site> --rows                 # map of all deck rows to define a site in ramp_sites.py
python3 pipeline/scopes/ramp_build.py gerold,duttweiler,brauer,pfingstweid,wipkingen --write   # rows into web/public/tiles (always all sites)
python3 pipeline/scopes/score.py gerold,duttweiler,brauer,pfingstweid,wipkingen --label v2     # reports with verdicts, station tables, overlays
python3 pipeline/scopes/ride_delta.py logs/bridges_ride_<label>.log      # rides that changed status against the gate baseline
python3 pipeline/scopes/lidar_for_sites.py --tiles <E_N,...>             # LiDAR tiles discover.py --lidar lists as missing
python3 pipeline/scopes/discover.py                                      # automatic sites for every elevated road chain group
python3 pipeline/scopes/city.py                                          # every site built and scored on its own -> city.md
cd web && VITE_WORLD_PROXY=https://sandboxzurich.sandboxzurich-web.workers.dev npx vite --port 5190   # dev server
cd web && node tests/ramp_shots.mjs v2 "" http://localhost:5190  # before/after viewpoints
cd web && node tests/bridges_ride.mjs v2 "" car,bike,foot http://localhost:5190 --gate
```
Python is the anaconda `python3` (3.8); images stay out of git.

## How to continue, in order

1. Terrain pass from LiDAR around bridge heads (the approaches only bridge the holes along roads).
2. Integration as a pipeline stage after `bridges.py` in the maintainer's full build (both scopes are there), the reports as
   `research/bridges/scopes/<site>.md`, the gate baseline accepted with the new rows.
3. Terrain pass for fills and landings (the residuals are in every report).
4. Scope C only if the transfer shows that the lane / footway split or structure semantics decide a ramp's look.
5. Pitch to the maintainer (see below), then integration as a pipeline stage after `bridges.py` (both scopes are in his build).

## Pitch to the maintainer

Fit: the maintainer works with audits, baselines, gates and research protocols; this adds one of each for ramps. What goes
into a PR: `pipeline/scopes/`, the research write-ups here, the ride gate with its baseline fixture and the dev proxy (already
separable), the proposed decisions text in the PR body. What stays out: everything under `docs/`, artifact links, local paths,
the rewritten tiles (the maintainer rebuilds). Order: first the gate + proxy PR (small, independent), then the scopes PR once
the transfer phase has run. The vision helper is pitched as a documented extension, not as a dependency.
