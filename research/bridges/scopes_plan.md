# Ramps from three reference scopes: plan (2026-10-31)

Branch `worktree-ramps` (fork jaenib). Follows the LiDAR pilot (`ramp_lidar_pilot.md`, DECISIONS #81) and the user's verdict:
the pilot satisfies LiDAR-derived guardrails but produces ramps that are only slightly better, because ramps are complex,
unique objects and LiDAR alone cannot tell deck from wall from footway. We add two more reference scopes and score every
modelled ramp against all three. The more scopes a ramp satisfies, the better the method.

## 1. What the pilot got wrong, and what the new data says about it

| Pilot shortfall | Root cause | Which scope fixes it |
|---|---|---|
| Axis jitter (±1 m per 2 m station), kinks, railing collider gaps | Band edges from 0.5 m LiDAR cells: railings, parked cars, footways, neighbouring structures all count as "bridge" | AV deck polygons (`Brücke, Passerelle`) give the exact outline; the axis is the polygon's medial line |
| Width 14 to 16 m for a 2-lane bridge | The class-17 footprint is the whole structure incl. both footways and parapets | AV Bodenbedeckung splits `Strasse, Weg`, `Trottoir`, `Verkehrsinsel` on the deck |
| Solid-vs-pier guess from "no class 17" | LiDAR cannot see under a deck | AV `Pfeiler` polygons (22 at the Geroldrampe, 55 at the Duttweilerbrücke) and `Mauer` polygons (walls of the embankments) say where supports and retaining walls are |
| Landings: continuation along the road graph, jogs at junction nodes, entered from the side | Road graph is an axis model, not a surface | AV carriageway polygon of the landing; walls end where the ramp meets grade |
| Duttweiler landing terrain 3 m too low | Game terrain, not the deck | LiDAR `dtm` already shows it; the scope report must flag terrain errors separately so they go to the terrain pass, not the deck |
| Crest 1.5 m too low in the old model | Old pipeline faded the LiDAR offset near rule ends | LiDAR central-strip heights (keep from the pilot) |
| Nothing says "this is an embankment with grass slopes and a wall on the east side only" | No scope had semantics | Vision helper on orthophoto (+ street-level photo when unsure) |

Keep from the pilot: central-strip height sampling, continuation-to-grade idea, solid skirts, per-vertex left/right widths
(`wl`/`wr`) in the client, prop clearing, the ride gate and the before/after shot tooling. Drop: band tracking as the
primary geometry source, width from the band, road-graph continuation as the only landing rule.

## 2. The three scopes

Every scope produces the same structure, a `RampSpec` (JSON, local metres):
`axis` (polyline), `sections[]` with `s0, s1, kind (deck | embankment | at_grade | stairs), carriageway_wl/wr, structure_wl/wr,
walls (left/right/none), supports (piers | solid | none)`, `ends[] (position, kind: grade | junction | air)`, `heights` (z along s,
source), `confidence` per field, `provenance`.

### Scope A, LiDAR (exists, `pipeline/lidar.py`, `lidar_deck.py`, pilot `ramp_lidar.py`)
Heights along any given axis or inside any polygon (class-17 central strip, class-2 ground for embankments), bridge-class
footprint as a coarse mask, ground under the structure where visible. Strength: z. Weakness: edges, semantics.

### Scope B, official cadastre (new, `pipeline/scopes/scope_av.py`)
Kanton Zürich OGD-WFS `https://maps.zh.ch/wfs/OGDZHWFS` (already used by `groundcover.py` / `fetch_geo_more.py`), layers
`ms:ogd-0402_arv_basis_avzh_einzelobjekte_f` / `_l` (Brücke, Passerelle; Pfeiler; Mauer; wichtige Treppe; Tunnel, Unterführung,
Galerie; Unterstand) and `ms:ogd-0401_arv_basis_avzh_bodenbedeckung_f` (Strasse, Weg; Trottoir; Verkehrsinsel; befestigte Fläche).
Checked today for both pilot sites: Geroldrampe bbox has 11 bridge polygons, 22 piers, 5 walls, 8 road polygons, 3 footway
polygons; Duttweiler bbox has 10 bridge polygons, 55 piers, 16 walls, 5 stair polygons, 2 underpasses. This is the "DWG" the
baurecht-browser pipeline turns into DXF context packs; here we consume the GeoJSON directly, cached under `data/raw/av/<site>.json`.
2D only: heights still come from Scope A. The DXF writer in `brb_code/modules/m_cadfiles` is worth reusing only for a human
check in a CAD viewer; `ezdxf` or the project's `dxf_min_writer.py` can emit the overlay (AV polygons, LiDAR mask, modelled rows).

### Scope C, imagery plus vision helper (new, `pipeline/scopes/scope_vision.py`)
Inputs: SWISSIMAGE crops from the swisstopo WMS (`pipeline/ortho.py` pattern, 0.1 to 0.25 m/px; the WMS also serves older
flights via `ch.swisstopo.swissimage-product` with a TIME parameter, so "simple old imagery" is one parameter away), plus, when
the helper reports low confidence, one or two street-level photos from Mapillary / Panoramax (both already used as references
in `research/`, CC BY-SA). The helper calls a vision model with a fixed schema and returns a `RampSpec`-shaped JSON plus a
plain-language description: structure type per section (deck on piers, embankment with walls, cutting), lane count, which side
has a footway, parapet type, where the ramp meets grade, anything odd (noise walls, stairs, kiosks under the ramp).
Policy: Google Street View stays "inspiration only" per CLAUDE.md, nothing is downloaded or traced from it; the helper reads
open imagery and outputs text. Credentials: `OPENAI_API_KEY` is set on this machine, no Anthropic key yet; the helper takes
the provider from env (`RAMP_VISION_PROVIDER=anthropic|openai`), default Anthropic when a key exists.

## 3. Scoring: how much of each scope a ramp satisfies (`pipeline/scopes/score.py`)
For a modelled chain (tile rows) the scorer computes, per scope, numbers in metres and ratios, never a single magic score:
- B: IoU of the modelled footprint (axis with `wl`/`wr`) against the AV deck polygons; axis distance to the polygon medial
  line (p50/p95); carriageway width error against `Strasse, Weg`; wall coverage (modelled solid sections vs `Mauer` extent);
  pier coverage (piers under modelled deck sections); landing error (distance from the modelled grade end to the end of the
  AV structure).
- A: height residual along the axis (p50/p95) against the central-strip LiDAR; terrain residual game-vs-LiDAR under the ramp
  (reported, not scored against the deck).
- C: agreement per section kind (deck / embankment / at grade) and per side (footway, wall, parapet) with the helper's report;
  disagreements listed verbatim.
Output: one Markdown report per site with the numbers and a top-down overlay (ortho crop, AV polygons, LiDAR mask, old rows,
new rows) so the user can judge by eye, plus the before/after shot pairs (`web/tests/ramp_shots.mjs`) and the ride gate.

## 4. The builder (`pipeline/scopes/ramp_build.py`, replaces the pilot's tracker as the primary path)
1. Site = name match or bbox. Fetch B (cached), A rasters (cached), C report (cached by image hash).
2. Geometry from B: union of deck polygons touching the OSM chain, medial axis (Voronoi / skeleton of the polygon, snapped to
   the OSM axis where they agree within 1 m, since traffic, routes and the road graph follow OSM), per-station left/right
   structure width from the polygon, carriageway width from `Strasse, Weg`, footways from `Trottoir` as separate foot rows at the
   measured position, walls from `Mauer` (solid skirt where a wall runs along the section), piers from `Pfeiler` (pier rows at
   their real positions instead of the rule spacing), stairs from `wichtige Treppe`.
3. Heights from A along that axis (central strip), slope-limited; embankment sections take `dtm`; landings end where the
   structure polygon / wall ends and the surface meets the game terrain, with the terrain residual flagged.
4. Attributes and validation from C: section kinds, parapet/wall sides, oddities; disagreements go to the report.
5. Write rows (`wl`/`wr`, `b`, piers) into the tile JSON as the pilot does; the client needs nothing new except pier rows at
   AV positions (already supported by the `piers` row format).
6. Fallback where B has no polygon (at-grade approaches): the pilot's band tracker, locked to the OSM axis.

## 5. Phases and what the user tests after each
1. **Diagnosis** (half a day): Scope B fetch + scorer on the pilot output and on the live rows for both sites. Deliverable:
   the two site reports with overlays. User judges whether the numbers match what they saw.
2. **Builder v2 on the two pilot sites** (one day): rows from B + A, scorer rerun, ride gate, before/after page updated.
3. **Vision helper** (half a day): schema, prompt, cache, run on both sites; report section C added. User reads the helper's
   descriptions against reality.
4. **Transfer** (half a day): run unchanged on three more ramps (Pfingstweid ramp 182,352; Hardbrücke Nord / Wipkingerbrücke
   480,800; Brauerstrasse ramp 376,-480). Scores and pictures decide whether the method generalises.
5. **Maintainer proposal**: integrate as a pipeline stage after `bridges.py` (AV + LiDAR available in his build), the scope
   reports as `research/bridges/scopes/<site>.md`, the gate baseline accepted with the new rows.

## 6. Open questions for the user
- Vision provider: Anthropic key available, or run the helper on OpenAI for now?
- Street-level photos: Mapillary needs a free token; Panoramax does not. Start with Panoramax only?
- Footways on decks: separate foot rows at the AV `Trottoir` position (current game convention) or one deck with a kerb line?
