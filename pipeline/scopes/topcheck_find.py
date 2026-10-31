"""Findings of the top-down check (pipeline/scopes/topcheck.py): cell grids of the drawn world in, numbered patches out.

Grids (row 0 = north, res m per cell): deck / rail (drawn deck surface heights), glb (tile mesh: terrain, streets), walk, feet,
ground, push (the client's collision functions sampled at every cell, web/tests/deck_top.mjs). References: the cadastre bridge
polygons and traffic areas (Scope B) and the LiDAR ground / bridge grids (Scope A).
  hole       AV road bridge (eroded by EDGE m) without a drawn deck: interior (ground visible through the deck) or edge
             (deck narrower than the bridge). AV bridges decks hardly touch (< MODELLED) are "not modelled"; bridges carried
             by rail decks are checked the same way but reported apart (not walked, not gating).
  below      on AV traffic areas the drawn surface (deck, else tile mesh) lies >= REAL m below the LiDAR surface
             (max of ground and bridge returns): a missing ramp, approach or deck piece where the AV outline says nothing
             ("no deck"), or a deck drawn too low; rail decks too low are reported, not gating
  above      the drawn surface >= REAL m above the LiDAR surface (reported, not gating)
  step       neighbouring deck cells STEP m apart (overlapping or misjoined slabs; more = a deck above another), not next
             to a parapet top (a level change behind a parapet is wanted)
  blocked    a 0.35 m body is pushed on the deck surface >= 1 m inside its outline: invisible wall
  sink       elevated deck cells where drawn and walkable / stand height differ by > SINK m (or nothing is walkable)
  covered    the tile mesh lies above the drawn deck surface
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lidar  # noqa: E402

EDGE = 1.0              # m, AV outline tolerance
MODELLED = 0.25         # share of an AV bridge polygon the decks must cover for it to count as modelled
STEP = (0.25, 2.5)      # m
SINK = 0.15             # m
PUSH = 0.05             # m
REAL = 1.5              # m, drawn surface vs LiDAR surface
TRAFFIC = ("carriageway", "footway", "path", "paved", "island", "parking")
GATE = {"interior_m2": 1.0, "edge_m2": 4.0, "edge_w": 1.5, "below_m2": 4.0, "below_w": 1.5, "step_m": 2.0, "blocked_m2": 1.0,
        "sink_m2": 2.0}


def raster(geoms, box, res, shape):
    """Polygons (game metres) -> boolean grid."""
    H, W = shape
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    x0, y1 = box[0], box[3]
    tr = lambda cs: [((x - x0) / res, (y1 - y) / res) for x, y in cs]  # noqa: E731
    for g in geoms:
        for p in getattr(g, "geoms", [g]):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            d.polygon(tr(p.exterior.coords), fill=1)
            for r in p.interiors:
                d.polygon(tr(r.coords), fill=0)
    return np.array(img, bool)


def comps(mask, res, box, extra=None, min_m2=0.5):
    """Connected patches: area, centre (game metres), width (2 x deepest inside), the cells, plus extra(rows, cols)."""
    lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        c = lab[sl] == k
        if c.sum() * res * res < min_m2:
            continue
        rr, cc = np.nonzero(c)
        rr = rr + sl[0].start; cc = cc + sl[1].start
        item = {"m2": round(len(rr) * res * res, 1), "x": round(box[0] + (cc.mean() + 0.5) * res, 1),
                "y": round(box[3] - (rr.mean() + 0.5) * res, 1),
                "w": round(float(2 * ndimage.distance_transform_edt(np.pad(c, 1)).max() * res), 1), "rc": (rr, cc)}
        if extra is not None:
            item.update(extra(rr, cc))
        out.append(item)
    return sorted(out, key=lambda c: -c["m2"])


def _holes(polys, drawn, walkable, res, box, shape):
    req = np.zeros(shape, bool)
    for _, m, _ in polys:
        req |= m
    req_in = ndimage.binary_erosion(req, iterations=max(1, round(EDGE / res)))
    hole = req_in & ~drawn
    border = req_in & ~ndimage.binary_erosion(req_in, iterations=2)
    info = lambda rr, cc: {"kind": "edge" if border[rr, cc].any() else "interior", "walkable": round(float(walkable[rr, cc].mean()), 2)}  # noqa: E731
    return req, hole, comps(hole, res, box, info, min_m2=1.0)


def analyse(name, P, box, res, av):
    D, Rl = P["deck"], P["rail"]
    H, W = D.shape
    deck, rail = ~np.isnan(D), ~np.isnan(Rl)
    drawn = deck | rail
    a = res * res
    road_b, rail_b, unmod = [], [], []
    for g in av.geoms("deck"):
        if g.is_empty:
            continue
        m = raster([g], box, res, (H, W))
        if not m.any():
            continue
        cd, cr = (m & deck).sum() / m.sum(), (m & rail).sum() / m.sum()
        (unmod if cd + cr < MODELLED else rail_b if cr > cd else road_b).append((g, m, cd + cr))
    walkable = ~np.isnan(P["walk"])
    req, hole, holes = _holes(road_b, drawn, walkable, res, box, (H, W))
    rreq, rhole, rholes = _holes(rail_b, drawn, walkable, res, box, (H, W))
    unmod_m = raster([u[0] for u in unmod], box, res, (H, W))

    # LiDAR surface on the cadastre traffic areas and modelled bridges
    xs = box[0] + (np.arange(W) + 0.5) * res
    ys = box[3] - (np.arange(H) + 0.5) * res
    X, Y = np.meshgrid(xs, ys)
    real = np.fmax(lidar.dtm(X.ravel(), Y.ravel()), lidar.bridge(X.ravel(), Y.ravel())).reshape(H, W)
    surf = np.fmax(np.fmax(D, Rl), P["glb"])
    src = np.where(surf == D, 0, np.where(surf == Rl, 1, 2))      # what is drawn on top: road deck, rail deck, tile mesh
    SRC = ("road deck too low", "rail deck too low", "no deck")
    region = raster([g for grp in TRAFFIC for g in av.geoms(grp)], box, res, (H, W)) | req | rreq
    region = ndimage.binary_erosion(region & ~unmod_m, iterations=max(1, round(EDGE / res)))
    has = region & ~np.isnan(real) & ~np.isnan(surf)
    diff = np.where(has, real - surf, 0.0)
    below = has & (diff >= REAL)
    above = has & (-diff >= REAL)
    lows = comps(below, res, box, lambda rr, cc: {"depth": round(float(np.median(diff[rr, cc])), 1), "real": round(float(np.median(real[rr, cc])), 1),
                                                   "drawn": SRC[int(np.bincount(src[rr, cc], minlength=3).argmax())]}, min_m2=GATE["below_m2"])
    highs = comps(above, res, box, lambda rr, cc: {"height": round(float(np.median(-diff[rr, cc])), 1)}, min_m2=GATE["below_m2"])

    # steps between neighbouring drawn deck cells
    mag = np.zeros((H, W), np.float32)
    for ax in (0, 1):
        dz = np.abs(np.diff(D, axis=ax))
        dz = np.where((dz >= STEP[0]) & (dz <= STEP[1]), dz, 0)
        sl = (slice(1, None), slice(None)) if ax == 0 else (slice(None), slice(1, None))
        mag[sl] = np.maximum(mag[sl], dz)
    wall = ndimage.binary_dilation(~np.isnan(P["wall"]), iterations=1)   # across a parapet: a level change, not a step
    st = (mag > 0) & ~wall
    steps = comps(st, res, box, lambda rr, cc: {"dz": round(float(mag[rr, cc].max()), 2), "len": round(len(rr) * res, 1)})

    # invisible walls and sinking, inside the deck outline only (railings and ramp feet are wanted)
    inner = ndimage.binary_erosion(deck, iterations=max(1, round(1.0 / res)))
    push = np.nan_to_num(P["push"], nan=0.0)
    blk = inner & (push > PUSH)
    blocked = comps(blk, res, box, lambda rr, cc: {"push": round(float(push[rr, cc].max()), 2)})
    elev = deck & (D - P["ground"] > 0.5)
    off = lambda q: np.abs(np.nan_to_num(q, nan=-99.0) - D) > SINK  # noqa: E731
    snk = elev & inner & (np.isnan(P["walk"]) | off(P["walk"]) | off(P["feet"]))
    sinks = comps(snk, res, box, lambda rr, cc: {"dz": round(float(np.nanmedian((P["feet"] - D)[rr, cc])), 2)})
    covered = deck & (P["glb"] > D + 0.1)

    for pre, lst in (("H", holes), ("R", rholes), ("L", lows), ("S", steps), ("B", blocked), ("K", sinks), ("U", highs)):
        for n, c in enumerate(lst, 1):
            c["id"] = f"{pre}{n}"
    g = GATE
    gating = {
        "interior holes": [h for h in holes if h["kind"] == "interior" and h["m2"] >= g["interior_m2"]],
        "edge holes": [h for h in holes if h["kind"] == "edge" and h["m2"] >= g["edge_m2"] and h["w"] >= g["edge_w"]],
        "below LiDAR": [c for c in lows if c["w"] >= g["below_w"] and c["drawn"] != "rail deck too low"],   # rail: reported only
        "steps": [s for s in steps if s["len"] >= g["step_m"]],
        "blocked": [b for b in blocked if b["m2"] >= g["blocked_m2"]],
        "sink": [s for s in sinks if s["m2"] >= g["sink_m2"]],
    }
    fails = [k for k, v in gating.items() if v]
    return {
        "site": name, "box": [round(v, 1) for v in box], "res": res, "verdict": "FAIL" if fails else "PASS", "fails": fails,
        "gating": {k: [c["id"] for c in v] for k, v in gating.items()},
        "deck_m2": round(deck.sum() * a), "av_modelled_m2": round(req.sum() * a),
        "av_covered": round(float((req & drawn).sum() / max(1, req.sum())), 3),
        "lidar_share": round(float(has.sum() / max(1, region.sum())), 2),
        "holes": holes, "rail_holes": rholes, "below": lows, "above": highs, "steps": steps, "blocked": blocked, "sinks": sinks,
        "covered_m2": round(covered.sum() * a, 1),
        "unmodelled": [{"m2": round(m.sum() * a), "covered": round(float(c), 2), "x": round(gg.centroid.x, 1), "y": round(gg.centroid.y, 1)}
                       for gg, m, c in unmod],
        "_masks": {"req": req, "rreq": rreq, "hole": hole, "rhole": rhole, "below": below, "above": above, "step": st, "blocked": blk,
                   "sink": snk, "covered": covered, "unmodelled": unmod_m, "deck": deck, "rail": rail},
    }


def clean(R):
    """The result without grids and cells (for the json)."""
    out = {k: v for k, v in R.items() if not k.startswith("_")}
    for key in ("holes", "rail_holes", "below", "above", "steps", "blocked", "sinks"):
        out[key] = [{k: v for k, v in c.items() if k != "rc"} for c in R[key]]
    return out
