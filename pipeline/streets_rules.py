"""Official street rules (Stadt Zürich OGD, CC0) used to place markings and signs where they really are.

Sources (data/raw/stadtzh*/, see docs/DATA_SOURCES.md, research/streets_audit.md):
  geo_verkehrszonen__view_geoserver_zonen_ist      T30-Zone / Begegnungszone / Fussgängerzone polygons
  geo_signalisierte_geschwindigkeiten__..._tempo_ist  signalised speed regime per street segment (T20/T30/T50 ...)
  geo_fuss__und_velowegnetz__tbl_routennetz        Velostreifen (BOTH/FT/TF = direction of the line) and Velowege
  geo_schulweguebergaenge__poi_schulweg_view       school crossings (Fussgängerstreifen allowed inside zones)

API: rules() -> Rules (cached).  annotate(S) adds to every S["ways"] item:
  zone  'z30' | 'beg' | 'fuss' | None   (majority of the way lies inside the official zone)
  tempo 20 | 30 | 50 | None             (signalised regime of the street, e.g. T30 on Langstrasse without a zone)
  lanes {'left': [(s0, s1)], 'right': [(s0, s1)]}  painted bike-lane intervals along the way (official + OSM)
  events(coords) -> [(s, kind, direction)] zone / speed regime changes along a polyline (for signs and decals).
"""
import json
import math
from functools import lru_cache

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union

from config import ROOT

RAW = ROOT / "data" / "raw"
ZONE_KIND = {"T30-Zone": "z30", "Begegnungszone": "beg", "Fussgängerzone": "fuss"}
SAMPLE = 3.0


def _load(path):
    return json.load(open(RAW / path))["features"]


def _local(geom):
    import sources
    from shapely.ops import transform
    return transform(lambda x, y, z=None: tuple(np.asarray(sources.geo.to_local(np.asarray(x), np.asarray(y)))), geom)


def _lines(feat):
    g = shape(feat["geometry"])
    return list(g.geoms) if g.geom_type.startswith("Multi") else [g]


class Rules:
    def __init__(self):
        self.zones = {}
        polys = {}
        for f in _load("stadtzh/geo_verkehrszonen__view_geoserver_zonen_ist.geojson"):
            k = ZONE_KIND.get(f["properties"].get("zonentyp"))
            if k and f.get("geometry"):
                polys.setdefault(k, []).append(_local(shape(f["geometry"])).buffer(0))
        for k, v in polys.items():
            u = unary_union(v)
            shapely.prepare(u)
            self.zones[k] = u
        # signalised regimes
        tl, tv = [], []
        for f in _load("stadtzh_all/geo_signalisierte_geschwindigkeiten__view_geoserver_tempo_ist.geojson"):
            r = f["properties"].get("temporegime")
            v = {"T20": 20, "T30": 30, "T50": 50}.get(r)
            if v and f.get("geometry"):
                for ln in _lines(f):
                    tl.append(_local(ln)); tv.append(v)
        self.tempo_lines, self.tempo_val = tl, np.array(tv)
        self.tempo_tree = STRtree(tl) if tl else None
        # official bike lanes / paths
        vl, vk = [], []
        for f in _load("stadtzh/geo_fuss__und_velowegnetz__tbl_routennetz.geojson"):
            p = f["properties"]
            st = (p.get("velostreifen") or "0").strip()
            if (st in ("BOTH", "FT", "TF") or p.get("veloweg") == 1) and f.get("geometry"):
                for ln in _lines(f):
                    vl.append(_local(ln)); vk.append(st if st in ("BOTH", "FT", "TF") else "WEG")
        self.velo_lines, self.velo_kind = vl, vk
        self.velo_tree = STRtree(vl) if vl else None
        sch = []
        for f in _load("stadtzh_all/geo_schulweguebergaenge__poi_schulweg_view.geojson"):
            if f.get("geometry"):
                sch.append(_local(shape(f["geometry"])))
        self.school = STRtree(sch) if sch else None
        self.school_pts = sch

    # ---- point queries -------------------------------------------------
    def zone_at(self, xs, ys):
        xs, ys = np.asarray(xs, float), np.asarray(ys, float)
        out = np.full(len(xs), "", dtype=object)
        for k in ("fuss", "beg", "z30"):
            if k in self.zones:
                out[shapely.contains_xy(self.zones[k], xs, ys)] = k
        return out

    def zone_point(self, x, y):
        return self.zone_at([x], [y])[0] or None

    def near_school(self, x, y, d=30):
        return bool(self.school is not None and len(self.school.query(Point(x, y).buffer(d))))

    def tempo_at(self, pts, hdg):
        """Signalised speed (20/30/50/0) per point: nearest roughly parallel regime line within 7 m."""
        out = np.zeros(len(pts), int)
        if self.tempo_tree is None or not len(pts):
            return out
        P = shapely.points(pts)
        ii, jj = self.tempo_tree.query(P, predicate="dwithin", distance=7.0)
        best = {}
        for i, j in zip(ii, jj):
            ln = self.tempo_lines[j]
            s = ln.project(P[i])
            a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
            d = np.array([b.x - a.x, b.y - a.y])
            n = np.hypot(*d)
            if n < 1e-6 or abs(np.dot(d / n, hdg[i])) < 0.8:
                continue
            dist = ln.distance(P[i])
            if i not in best or dist < best[i][0]:
                best[i] = (dist, self.tempo_val[j])
        for i, (_, v) in best.items():
            out[i] = v
        return out

    def velo_at(self, pts, hdg):
        """Per point: None | 'WEG' | (side flags) via direction. Returns list of sets {'left','right'} or 'WEG'."""
        out = [None] * len(pts)
        if self.velo_tree is None or not len(pts):
            return out
        P = shapely.points(pts)
        ii, jj = self.velo_tree.query(P, predicate="dwithin", distance=6.0)
        best = {}
        for i, j in zip(ii, jj):
            ln = self.velo_lines[j]
            s = ln.project(P[i])
            a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
            d = np.array([b.x - a.x, b.y - a.y])
            n = np.hypot(*d)
            if n < 1e-6:
                continue
            d /= n
            c = float(np.dot(d, hdg[i]))
            if abs(c) < 0.8:
                continue
            kind = self.velo_kind[j]
            dist = ln.distance(P[i])
            if kind == "WEG":
                sides = "WEG"
            elif kind == "BOTH":
                sides = {"left", "right"}
            else:
                travel = d if kind == "FT" else -d
                sides = {"right"} if float(np.dot(travel, hdg[i])) > 0 else {"left"}
            if i not in best or dist < best[i][0]:
                best[i] = (dist, sides)
        for i, (_, sd) in best.items():
            out[i] = sd
        return out


@lru_cache(maxsize=1)
def rules():
    return Rules()


def _samples(line, step=SAMPLE):
    n = max(2, int(line.length / step) + 1)
    ss = np.linspace(0, line.length, n)
    pts = shapely.get_coordinates(shapely.line_interpolate_point(line, ss))
    a = shapely.get_coordinates(shapely.line_interpolate_point(line, np.clip(ss - 1.5, 0, line.length)))
    b = shapely.get_coordinates(shapely.line_interpolate_point(line, np.clip(ss + 1.5, 0, line.length)))
    d = b - a
    d /= (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9)
    return ss, pts, d


def _intervals(ss, mask, step=SAMPLE, min_len=6.0):
    out, s0 = [], None
    for s, m in zip(ss, mask):
        if m and s0 is None:
            s0 = s
        if not m and s0 is not None:
            out.append((s0, s)); s0 = None
    if s0 is not None:
        out.append((s0, ss[-1]))
    return [(max(0.0, a - step / 2), b) for a, b in out if b - a >= min_len]


def annotate(S):
    """Add zone / tempo / lanes to every S["ways"] item (idempotent)."""
    R = rules()
    for w in S["ways"]:
        if "zone" in w:
            continue
        ln = w["line"]
        if ln.length < 1:
            w.update(zone=None, tempo=None, lanes={"left": [], "right": []})
            continue
        ss, pts, d = _samples(ln)
        z = R.zone_at(pts[:, 0], pts[:, 1])
        mid = (ss > 6) & (ss < ln.length - 6) if ln.length > 14 else np.ones(len(ss), bool)
        zs = [k for k in z[mid] if k]
        zone = None
        if len(zs) > 0.5 * mid.sum():
            zone = max(set(zs), key=zs.count)
        w["zone"] = zone
        tp = R.tempo_at(pts, d)
        tv = [v for v in tp[mid] if v]
        w["tempo"] = max(set(tv), key=tv.count) if len(tv) > 0.4 * mid.sum() else None
        # bike lanes: official intervals; the OSM tag counts for the whole way
        vel = R.velo_at(pts, d)
        lanes = {}
        for side in ("left", "right"):
            m = np.array([isinstance(v, set) and side in v for v in vel])
            iv = _intervals(ss, m)
            if "lane" in w["cyc"][side] and not iv:
                iv = [(0.0, ln.length)]
            lanes[side] = iv if w["hw"] not in ("service",) and zone not in ("beg", "fuss") else []
        w["lanes"] = lanes
        w["velo_weg"] = sum(1 for v in vel if v == "WEG") > 0.6 * len(vel)


def events(coords, R=None):
    """Zone / signalised-speed changes along a polyline (N x 2 array, local m).
    Returns [(s, prev, new)]: regime before / after s in polyline direction ('' = none; z30, beg, fuss, t20, t30, t50).
    Travelling +s leaves prev and enters new; travelling -s leaves new and enters prev."""
    R = R or rules()
    ln = LineString(coords)
    if ln.length < 12:
        return []
    ss, pts, d = _samples(ln, 2.0)
    z = R.zone_at(pts[:, 0], pts[:, 1])
    tp = R.tempo_at(pts, d)
    cls = np.array([zz if zz else (f"t{t}" if t else "") for zz, t in zip(z, tp)], dtype=object)
    out = []
    for i in range(1, len(ss)):
        if cls[i] == cls[i - 1]:
            continue
        # require the new regime to persist for ~8 m so tiny gaps (junction mouths) do not create signs
        j = min(len(ss), i + 4)
        k = max(0, i - 4)
        if len(set(cls[i:j])) > 1 or len(set(cls[k:i])) > 1:
            continue
        out.append((float(ss[i]), cls[i - 1], cls[i]))
    return out
