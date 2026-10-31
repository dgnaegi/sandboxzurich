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
| Transfer to more ramps unchanged (phase 4) | one of three done: Hohlstrasse / Brauerstrasse PASS without a builder change; Pfingstweid and Hardbrücke Nord have their LiDAR tiles, sites not yet defined | `pipeline/scopes/ramp_sites.py`, `lidar_for_sites.py` |
| Scope C: imagery + vision helper for the lane / footway split and semantics | documented proposal (`scopes_plan.md` §2); not needed for the two sites | — |
| Site discovery (every elevated road chain instead of a hand list) | vision | — |
| Maintainer integration as a pipeline stage after `bridges.py` | vision | — |

## Results on three sites (2026-11-01)

Numbers from `score.py` (full reports `gerold.md`, `duttweiler.md`, `brauer.md`; the pilot column from the snapshot in
`pilot/`). All row sets are measured with the same code; the outline IoU is station-wise against the slice available to the chain.

| Measure | Geroldrampe live → pilot → v2 | Duttweiler south ramp live → pilot → v2 | Hohlstrasse / Brauerstrasse live → v2 |
|---|---|---|---|
| Verdict (v2) | REVIEW (fork gore uncovered) | PASS | PASS |
| Outline IoU at ramp stations | 0.35 → 0.64 → 0.91 | 0.43 → 0.77 → 0.99 | 0.53 → 0.99 |
| Cadastre width, median (available slice) | 9.0 m → 13.9 m → 9.1 m | 14.1 m → 14.2 m → 14.1 m | 9.1 m → 9.1 m |
| Modelled width, median | 3.2 m → 7.5 m → 8.2 m | 6.4 m → 14.5 m → 14.2 m | 6.4 m → 9.1 m |
| Edge overshoot p50 / p95 | -1.6 m / +1.0 m → -1.1 m / +0.5 m → +0.0 m / +0.4 m | -3.3 m / -3.2 m → +0.3 m / +1.3 m → +0.0 m / +0.0 m | -1.1 m / +0.4 m → +0.0 m / +0.4 m |
| Uncovered cadastre width p50 / p95 (any deck row) | 6.8 m / 10.8 m → +3.5 m / +13.7 m → 0.0 m / 4.2 m | 3.8 m / 9.7 m → +0.3 m / +4.4 m → 0.0 m / 0.0 m | 7.1 m / 7.2 m → 0.0 m / 0.1 m |
| Cadastre piers near the axes: under deck / solid / grade / outside | 18: 10 / 0 / 0 / 8 → 18: 10 / 0 / 0 / 8 → 18: 13 / 0 / 0 / 5 | 30: 14 / 0 / 0 / 16 → 30: 26 / 0 / 0 / 4 → 30: 28 / 0 / 0 / 2 | 0: 0 / 0 / 0 / 0 → 0: 0 / 0 / 0 / 0 |
| Tile piers / standing at a real pier | 10 / 2 → 10 / 2 → 13 / 13 | 68 / 8 → 68 / 8 → 34 / 30 | 16 / 0 → 5 / 0 |
| Height residual vs LiDAR deck top p50 / p95 | -0.0 m / 0.1 m → +0.0 m / 0.2 m → -0.0 m / 0.2 m | -0.0 m / 1.0 m → -0.0 m / 0.1 m → -0.0 m / 0.0 m | -0.0 m / 0.1 m → +0.0 m / 0.1 m |
| Ride gate (97 + Geroldrampe routes) | PASS: stuck 14 → 12, fell 2 → 1 city-wide; Geroldrampe routes 0 crashes | car 632 of 638 m (live 183 m) | car and bike no longer stuck |
| Geroldrampe car rides (2 uphill routes) | 0 crashes, reach the Hardbrücke (was: crash at the fork nose) | | |

Remaining blemishes, by eye and by the scorer: the fork gore of the Geroldrampe (the deck area between the two diverging
branches is covered by neither; uncovered p95 4.2 m, the one REVIEW), 0.4 m raw-height steps where a car changes between
overlapping rows at the fork and the Hardbrücke junction (no car jumps), the Duttweiler landing wedge, a 1 m pedestrian step at
(−595, 131), and the walled approaches of the Hohlstrasse bridge modelled as solid blocks down to a game terrain that is up to
6.6 m too low (terrain pass, as at the Geroldrampe fill and the Duttweiler landing).

## Where this stands on the spectrum «handles every ramp» … «promising on the sample»

Position after three sites: between the two, closer to «promising», and the direction is right.

- Rules added while looking at results: eight on the two pilot sites (per-polygon slices at a deck crossing, running-height
  tracking, tail width from wing walls, replaced footway piers, hard caps at splits, coplanar branches, mouth opening on the
  main deck and between sibling chains, static colliders under decks), none for the first transfer site. Two scorer rules
  changed on the transfer site (available slice, station-wise IoU). The builder stopped growing on the third ramp; one site is
  not a trend.
- Two of three sites PASS the thresholds unseen; the Geroldrampe is a REVIEW for one named reason (fork gore), which is what
  the verdict is for. The ride gate improved city-wide (stuck 14 → 12, fell 2 → 1; the Hohlstrasse rides that were stuck cross).
- Two transfer sites remain (Pfingstweid ramp, Hardbrücke Nord), both junction-heavy; their LiDAR tiles are on disk. Site
  definition is still a hand list (`ramp_sites.py` with a name match and two boxes; `overlay.py <site> --rows` draws the map to
  pick from). Data coverage: all three sites have complete cadastre objects; a ramp with none falls back to the live width.

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
python3 pipeline/scopes/ramp_build.py gerold,duttweiler,brauer --write   # rows into web/public/tiles (originals kept in tiles_orig; always all sites)
python3 pipeline/scopes/score.py gerold,duttweiler,brauer --label v2     # reports with verdicts, station tables, overlays
cd web && VITE_WORLD_PROXY=https://sandboxzurich.sandboxzurich-web.workers.dev npx vite --port 5190   # dev server
cd web && node tests/ramp_shots.mjs v2 "" http://localhost:5190  # before/after viewpoints
cd web && node tests/bridges_ride.mjs v2 "" car,bike,foot http://localhost:5190 --gate
```
Python is the anaconda `python3` (3.8); images stay out of git.

## How to continue, in order

1. Fork gore: cover the deck area between diverging branches (a filler row or the main chain keeping the full width until the
   branch has left its slice), then the Geroldrampe passes.
2. Transfer sites 2 and 3: Pfingstweid ramp (182, 352) and Hardbrücke Nord / Wipkingerbrücke (480, 800), tiles are on disk;
   define the sites from the rows map, run everything unchanged, count the rules.
3. Site discovery: every road / tram deck chain with an elevated end or a cadastre bridge object under it, instead of the list.
4. Scope C only if the transfer shows that the lane / footway split or structure semantics decide a ramp's look.
5. Pitch to the maintainer (see below), then integration as a pipeline stage after `bridges.py` (both scopes are in his build).

## Pitch to the maintainer

Fit: the maintainer works with audits, baselines, gates and research protocols; this adds one of each for ramps. What goes
into a PR: `pipeline/scopes/`, the research write-ups here, the ride gate with its baseline fixture and the dev proxy (already
separable), the proposed decisions text in the PR body. What stays out: everything under `docs/`, artifact links, local paths,
the rewritten tiles (the maintainer rebuilds). Order: first the gate + proxy PR (small, independent), then the scopes PR once
the transfer phase has run. The vision helper is pitched as a documented extension, not as a dependency.
