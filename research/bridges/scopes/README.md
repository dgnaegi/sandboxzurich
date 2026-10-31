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
| Builder v2: rows from cadastre edges + LiDAR heights + cadastre piers, on the built tiles | implemented on the two pilot sites | `pipeline/scopes/ramp_build.py` |
| Acceptance thresholds (PASS / REVIEW per ramp) | proposed below, not yet in the scorer | this file |
| Transfer to three more ramps unchanged (phase 4) | planned; needs three more LiDAR tiles locally | `pipeline/scopes/ramp_sites.py` (boxes stubbed) |
| Scope C: imagery + vision helper for the lane / footway split and semantics | documented proposal (`scopes_plan.md` §2); not needed for the two sites | — |
| Site discovery (every elevated road chain instead of a hand list) | vision | — |
| Maintainer integration as a pipeline stage after `bridges.py` | vision | — |

## Results on the two pilot sites (2026-10-31)

Numbers from `score.py` (full reports `gerold.md`, `duttweiler.md`; the pilot column from the snapshot in `pilot/`).
All three row sets are measured with the same code.

| Measure | Geroldrampe live → pilot → v2 | Duttweiler south ramp live → pilot → v2 |
|---|---|---|
| Footprint IoU vs the cadastre outline | 0.31 → 0.64 → 0.75 | 0.43 → 0.77 → 0.88 |
| Modelled width at ramp stations (cadastre 13.9 / 14.1 m) | 3.2 → 7.5 → 9.0 m | 6.4 → 14.5 → 14.2 m |
| Edge overshoot p95 | −1.1 → +0.5 → +0.0 m | −3.2 → +1.3 → +0.0 m |
| Uncovered cadastre width p50 | 8.7 → 3.5 → 0.0 m | 4.4 → 0.3 → 0.0 m |
| Cadastre piers under the modelled deck | 10 → 10 → 13 of 18 | 14 → 26 → 28 of 30 |
| Tile piers standing at a real pier | 2/10 → 2/10 → 13/13 | 8/68 → 8/68 → 30/34 |
| Height residual vs LiDAR deck top, p95 | 0.1 → 0.2 → 0.0 m | 1.0 → 0.1 → 0.0 m |
| Structure past the cadastre deck end | n/a (fill, 74 m of edge polygons) | 0 (air) → 26 → 26 m, walled abutment |
| Ride gate (`--gate`, 97 rides) | pass: stuck 14 → 12, fell 2 → 1 city-wide; two crashes elsewhere are run noise | car 632 of 638 m (live: 183 m), foot 638 of 643 m |

Remaining blemishes, by eye: a one-station step in the Geroldrampe's north edge near x ≈ 130 (the slice toggles between the
ramp and the Hardbrücke polygon), the junction strips of the branches lying flush on the Hardbrücke deck, the Duttweiler
landing wedge where the deck polygon ends and the wall-based width begins, and a 1 m step for pedestrians at (−595, 131) where the
OSM footway passes 17 m east of the axis beyond the east wing wall, outside the tail (a footway row or a wider wedge is needed). The game terrain under the Geroldrampe fill (−4.2 m)
and at the Duttweiler landing (−3.0 m) is a terrain-pass item, hidden by the solid skirts.

## Where this stands on the spectrum «handles every ramp» … «promising on the sample»

Honest position: close to the «promising on the sample» end, with the infrastructure that makes the other end testable.

- Two sites, both chosen as pilots, both used to tune the builder: four rules were added after looking at results
  (per-polygon slices at a deck crossing, running-height tracking against a crossing deck, tail width from wing walls, dropping
  the replaced footway's piers). Each rule is deterministic and site-independent, but the rule set was still growing on the
  last site, so the transfer phase has to show that it stops growing.
- Zero transfer sites so far. The three stubbed in `ramp_sites.py` need LiDAR tiles that are not on this machine
  (`pipeline/lidar_fetch.py`, then `lidar_grid.py`), about one tile each.
- What makes «every ramp» testable is the scorer: a ramp that passes the thresholds below ships unseen, one that fails is
  routed by the failing measure. Today the thresholds are a proposal; the Geroldrampe would fail one of them (uncovered width
  p95 13.7 m) only because the branch stations inside the Hardbrücke polygon are counted, so the scorer needs a junction
  exclusion before the thresholds mean anything.
- Data coverage is the other open question: both sites happen to have complete cadastre objects (deck polygons, edge-polygon
  pairs, walls, piers). A ramp with none (plain earth embankment) falls back to the live width and gains only heights and
  piers.

## Deterministic vs interpreted

Deterministic, re-runnable, no model in the loop: fetch (B), rows, measure, build, score, overlay, shots, gate. One command per
step, seconds per site (the gate about ten minutes for the whole city). Nothing per site is hand-edited; the site registry holds
a name match and two boxes.

Interpreted (agent time, the costly part): reading overlays and numbers to decide the next rule; the thresholds
(`SIDE_MAX` 12 m, `THIN` 1.5 m, `TOL` 1.0 m, `MAIN_DECK` 24 m, `WALL_NEAR` 2.5 m); the site boxes; the readings in `*_notes.md`.
Tonight that was roughly half of the agent time over two phases. Marginal cost per further site with no new failure mode:
none beyond the run; per new failure mode: one rule, typically half an hour of agent time plus a rerun.

## Proposed acceptance thresholds (to put into the scorer as PASS / REVIEW)

- outline IoU ≥ 0.80; edge overshoot p95 ≤ 0.5 m; uncovered cadastre width p95 ≤ 2.0 m (junction and fork stations excluded)
- height residual vs LiDAR deck top p95 ≤ 0.3 m; modelled structure ends within 5 m of the cadastre / wall end
- every cadastre pier under the modelled deck has a modelled pier within 2 m; ride gate passes
- terrain residual under the ramp reported separately (never blocks the ramp, feeds the terrain pass)

## How to run

```
python3 pipeline/scopes/scope_av.py gerold,duttweiler            # fetch and cache the cadastre (once)
python3 pipeline/scopes/ramp_build.py gerold,duttweiler --write  # rows into web/public/tiles (originals kept in tiles_orig)
python3 pipeline/scopes/score.py gerold,duttweiler --label v2    # reports, station tables, overlays
cd web && VITE_WORLD_PROXY=https://sandboxzurich.sandboxzurich-web.workers.dev npx vite --port 5190   # dev server
cd web && node tests/ramp_shots.mjs v2 "" http://localhost:5190  # before/after viewpoints
cd web && node tests/bridges_ride.mjs v2 "" car,bike,foot http://localhost:5190 --gate
```
Python is the anaconda `python3` (3.8); images stay out of git.

## How to continue, in order

1. Junction exclusion in the scorer, thresholds as PASS / REVIEW in the report.
2. Transfer: fetch the LiDAR tiles for Pfingstweid ramp (182, 352), Hardbrücke Nord / Wipkingerbrücke (480, 800), Brauerstrasse
   ramp (376, −480); run fetch, build, score, shots, gate unchanged; count the rules that had to be added.
3. Site discovery: every road / tram deck chain with an elevated end or a cadastre bridge object under it, instead of the list.
4. Scope C only if the transfer shows that the lane / footway split or structure semantics decide a ramp's look.
5. Pitch to the maintainer (see below), then integration as a pipeline stage after `bridges.py` (both scopes are in his build).

## Pitch to the maintainer

Fit: the maintainer works with audits, baselines, gates and research protocols; this adds one of each for ramps. What goes
into a PR: `pipeline/scopes/`, the research write-ups here, the ride gate with its baseline fixture and the dev proxy (already
separable), the proposed decisions text in the PR body. What stays out: everything under `docs/`, artifact links, local paths,
the rewritten tiles (the maintainer rebuilds). Order: first the gate + proxy PR (small, independent), then the scopes PR once
the transfer phase has run. The vision helper is pitched as a documented extension, not as a dependency.
