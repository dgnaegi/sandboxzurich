"""Read-only audits of the game against the LiDAR rasters (pipeline/lidar_grid.py must have run).
Usage: .venv/bin/python pipeline/audit_lidar.py [a b c d e]   (default all)
Writes research/lidar/audit_<x>.tsv (full) and research/lidar/audit_lidar.md (summaries <= 30 lines each).
a ground (tile hmap vs DTM)   b bridge decks (deck chains vs class-17 surface)   c terrain_cuts profiles
d trees (game vs CHM peaks)   e lamps/masts (game vs class-15/1 poles)
Game frame, metres. dz = game - LiDAR (positive: game too high / object floating)."""
import base64
import glob
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lidar  # noqa: E402

OUT = R / "research" / "lidar"
TILES = sorted(glob.glob(str(R / "web/public/tiles/t_*.json")))
LINES = []


def tsv(name, head, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"audit_{name}.tsv", "w") as f:
        f.write("\t".join(head) + "\n")
        for r in rows:
            f.write("\t".join(str(v) for v in r) + "\n")


def say(s=""):
    LINES.append(s)
    print(s)


def hmap(m):
    h = m.get("hmap")
    if not h or "zb64" not in h:
        return None
    z = np.frombuffer(base64.b64decode(h["zb64"]), dtype="<i2").astype(float).reshape(h["h"], h["w"]) / 100
    return h, z


def tile_keys():
    return {Path(f).stem[2:] for f in TILES}


_PA = None


def in_area(x, y):
    """Inside the real play area (data/build/playarea.json); tiles outside are padding with extrapolated terrain."""
    global _PA
    import shapely
    if _PA is None:
        _PA = shapely.Polygon(json.load(open(R / "data/build/playarea.json"))["polygon"])
        shapely.prepare(_PA)
    return shapely.contains_xy(_PA, np.asarray(x, float), np.asarray(y, float))


# ---- a: ground -------------------------------------------------------------------------------------------------------
def audit_a():
    rows, tstat, blocks = [], [], defaultdict(list)
    for f in TILES:
        m = json.load(open(f))
        hz = hmap(m)
        if not hz:
            continue
        h, z = hz
        gy, gx = np.mgrid[0:h["h"]:2, 0:h["w"]:2]
        x, y, g = h["x0"] + gx.ravel() * h["step"], h["y0"] + gy.ravel() * h["step"], z[gy.ravel(), gx.ravel()]
        d = lidar.dtm(x, y)
        ok = in_area(x, y) & ~np.isnan(d) & np.isnan(lidar.bld(x, y)) & np.isnan(lidar.bridge(x, y))
        tp = lidar.top(x, y)
        ok &= np.isnan(tp) | (tp - d < 1.0)
        for ox, oy in ((2.5, 0), (-2.5, 0), (0, 2.5), (0, -2.5)):
            ok &= np.isnan(lidar.bld(x + ox, y + oy))
        dz = (g - d)[ok]
        if not len(dz):
            continue
        tstat.append((Path(f).stem[2:], len(dz), float(np.mean(dz)), float(np.mean(np.abs(dz))), float(np.mean(np.abs(dz) > 0.5))))
        for xx, yy, v in zip(x[ok], y[ok], dz):
            blocks[(int(xx // 20), int(yy // 20))].append(v)
    allv = np.concatenate([np.array(v) for v in blocks.values()])
    brow = [(k[0] * 20 + 10, k[1] * 20 + 10, len(v), round(float(np.mean(v)), 2), round(float(np.max(np.abs(v))), 2)) for k, v in blocks.items() if len(v) >= 6]
    brow.sort(key=lambda r: -abs(r[3]))
    tsv("a_ground_blocks", ["x", "y", "n", "mean_dz", "max_abs_dz"], brow)
    tsv("a_ground_tiles", ["tile", "n", "mean_dz", "mae", "frac>0.5"], [(t, n, round(a, 2), round(b, 2), round(c, 2)) for t, n, a, b, c in tstat])
    say("## a) Gelaende (Kachel-hmap, 4 m Raster) gegen LiDAR-DTM, ohne Gebaeude/Bruecken/Objekte")
    say(f"- {len(allv)} Punkte, Bias {allv.mean():+.3f} m, MAE {np.abs(allv).mean():.3f} m, innerhalb 0.25 m: {np.mean(np.abs(allv) < .25)*100:.1f} %, 0.5 m: {np.mean(np.abs(allv) < .5)*100:.1f} %, >1 m: {np.mean(np.abs(allv) > 1)*100:.2f} %")
    say("- schlechteste Kacheln (MAE): " + ", ".join(f"{t} {b:.2f}" for t, n, a, b, c in sorted(tstat, key=lambda r: -r[3])[:6]))
    say("- schlechteste 20-m-Bloecke (x,y,n,mean dz,max|dz|):")
    for r in brow[:10]:
        say(f"  ({r[0]},{r[1]}) n={r[2]} mean {r[3]:+.2f} max {r[4]:.2f}")


# ---- b: bridge decks ----------------------------------------------------------------------------------------------------
def audit_b():
    import bridges as B
    import lidar_deck
    ch = B.load_chains() or []
    rows, spots, far = [], [], []
    for k, c in enumerate(ch):
        p = np.asarray(c["p"], float)
        prof = lidar_deck.deck_profile(c)
        m = prof["z"]
        dz = p[:, 2] - m
        v = ~np.isnan(dz)
        nb = int((prof["src"] == 1).sum())
        for i in np.where(prof["src"] == 3)[0]:
            far.append((k, c.get("name", ""), c["kind"], round(p[i, 0], 1), round(p[i, 1], 1), round(p[i, 2], 2), round(prof["alt"][i], 2)))
        if not v.any():
            rows.append((k, c.get("name", ""), c["kind"], len(p), 0, nb, "", "", "", "", ""))
            continue
        a = np.abs(dz[v])
        iw = int(np.nanargmax(np.where(v, np.abs(dz), -1)))
        rows.append((k, c.get("name", ""), c["kind"], len(p), int(v.sum()), nb, round(float(dz[v].mean()), 2), round(float(a.mean()), 2), round(float(a.max()), 2), round(p[iw, 0], 1), round(p[iw, 1], 1)))
        for i in np.where(v & (np.abs(dz) > 1.0))[0]:
            spots.append((k, c.get("name", ""), round(p[i, 0], 1), round(p[i, 1], 1), round(p[i, 2], 2), round(m[i], 2), round(dz[i], 2), int(prof["src"][i])))
    tsv("b_decks", ["chain", "name", "kind", "verts", "measured", "n_bridge17", "mean_dz", "mean_abs", "max_abs", "worst_x", "worst_y"], rows)
    tsv("b_spots", ["chain", "name", "x", "y", "game_z", "lidar_z", "dz", "src"], sorted(spots, key=lambda r: -abs(r[6])))
    tsv("b_far", ["chain", "name", "kind", "x", "y", "game_z", "nearest_lidar_layer_z"], far)
    meas = [r for r in rows if r[4]]
    say(f"## b) Brueckendecks: {len(ch)} Chains, {len(meas)} mit LiDAR-Messung, {sum(1 for r in rows if r[5])} mit Klasse-17-Flaeche")
    ma = np.array([r[7] for r in meas]); mx = np.array([r[8] for r in meas])
    say(f"- mittlere |dz| je Chain: Median {np.median(ma):.2f} m, >0.5 m: {int((ma > .5).sum())} Chains, >1 m: {int((ma > 1).sum())}; max|dz| >2 m: {int((mx > 2).sum())} Chains; Punkte >1 m: {len(spots)}")
    say(f"- {len(far)} Deckpunkte in {len({f[0] for f in far})} Chains ohne LiDAR-Ebene innerhalb 4 m der Spielhoehe (audit_b_far.tsv: Ebene ueber/unter, oder Spiel stark falsch)")
    say("- schlechteste Chains (mean|dz|, max, name, worst x,y):")
    for r in sorted(meas, key=lambda r: -r[7])[:12]:
        say(f"  #{r[0]} {r[1][:28] or r[2]}: mean {r[7]:.2f} max {r[8]:.2f} bei ({r[9]},{r[10]}) bias {r[6]:+.2f} ({r[4]}/{r[3]} Punkte)")


# ---- c: terrain cuts ----------------------------------------------------------------------------------------------------
def audit_c():
    cuts = json.load(open(R / "pipeline/overrides/terrain_cuts.json"))["cuts"]
    rows = []
    say("## c) terrain_cuts gegen LiDAR-Boden (Klasse 2; unter Deckeln nicht messbar)")
    for c in cuts:
        if "profile" in c:
            a, b = np.asarray(c["axis"][0], float), np.asarray(c["axis"][1], float)
            L = float(np.linalg.norm(b - a)); d = (b - a) / L; nr = np.array([d[1], -d[0]])
            pr = np.asarray(c["profile"], float)
            s = np.arange(pr[0, 0], pr[-1, 0] + 1e-9, 2.0)
            half = min(float(c["half"]) * 0.5, 5.0)
            zs = np.interp(s, pr[:, 0], pr[:, 1])
            res = []
            for si, zi in zip(s, zs):
                o = np.arange(-half, half + 1e-9, 0.5)
                x, y = a[0] + si * d[0] + o * nr[0], a[1] + si * d[1] + o * nr[1]
                g = lidar.dtm(x, y); g = g[~np.isnan(g)]
                if len(g) >= 4:
                    res.append((si, x.mean(), y.mean(), zi, float(np.median(g))))
                    rows.append((c["name"][:40], round(si, 1), round(x.mean(), 1), round(y.mean(), 1), round(zi, 2), round(float(np.median(g)), 2), round(zi - float(np.median(g)), 2)))
            if res:
                dz = np.array([r[3] - r[4] for r in res])
                say(f"- {c['name'][:42]}: {len(res)}/{len(s)} Stationen messbar, mean dz {dz.mean():+.2f}, max|dz| {np.abs(dz).max():.2f} (Profil z {pr[:,1].min():.1f}..{pr[:,1].max():.1f})")
                lo = [r for r in res if abs(r[3] - r[4]) > 0.4]
                for r in lo[:3]:
                    say(f"    s={r[0]:.0f} ({r[1]:.0f},{r[2]:.0f}) profil {r[3]:.2f} lidar {r[4]:.2f}")
            else:
                say(f"- {c['name'][:42]}: keine messbaren Stationen (ueberdeckt)")
        elif "poly" in c:
            import shapely
            pg = shapely.Polygon(c["poly"]); x0, y0, x1, y1 = pg.bounds
            gx, gy = np.meshgrid(np.arange(x0, x1, 2.0), np.arange(y0, y1, 2.0))
            m = shapely.contains_xy(pg, gx.ravel(), gy.ravel())
            g = lidar.dtm(gx.ravel()[m], gy.ravel()[m]); g = g[~np.isnan(g)]
            say(f"- {c['name'][:42]} (flat z {c['z']}): {len(g)} Bodenzellen, LiDAR median {np.median(g):+.2f}" if len(g) else f"- {c['name'][:42]}: keine Bodenzellen (Halle)")
            if len(g):
                rows.append((c["name"][:40], "poly", "", "", c["z"], round(float(np.median(g)), 2), round(c["z"] - float(np.median(g)), 2)))
    tsv("c_cuts", ["cut", "s", "x", "y", "profile_z", "lidar_z", "dz"], rows)


# ---- d: trees -----------------------------------------------------------------------------------------------------------
def chm_peaks():
    """Local maxima of the smoothed canopy height model (1 m raster) per source tile: x, y, height."""
    from scipy import ndimage as ndi
    out = []
    global SUP
    SUP = {}
    for f in sorted(lidar.GRID.glob("g_*.npz")):
        e, n = (int(v) for v in f.stem[2:].split("_"))
        z = np.load(f)
        veg = z["veg"].astype(np.float32); dtm = z["dtm"].astype(np.float32)
        v = np.where(veg == -32768, np.nan, veg / 100)
        # 1 m cells: max veg, mean dtm (holes filled by nearest)
        v1 = np.nanmax(v.reshape(500, 2, 500, 2), axis=(1, 3)) if np.isfinite(v).any() else np.full((500, 500), np.nan)
        d = np.where(dtm == -32768, np.nan, dtm / 100)
        with np.errstate(all="ignore"):
            d1 = np.nanmean(d.reshape(500, 2, 500, 2), axis=(1, 3))
        bad = np.isnan(d1)
        if bad.all():
            continue
        _, (jy, jx) = ndi.distance_transform_edt(bad, return_indices=True)
        d1 = d1[jy, jx]
        c = np.nan_to_num(v1 - d1, nan=0.0)
        c = np.where(c > 80, 0, c)
        s = ndi.gaussian_filter(c, 1.2)
        SUP[(e, n)] = ndi.maximum_filter(c, size=7) > 2.5   # canopy > 2.5 m within 3 m
        pk = (s == ndi.maximum_filter(s, size=5)) & (s > 3.0) & (c > 3.0)
        pk[:2, :] = pk[-2:, :] = False; pk[:, :2] = pk[:, -2:] = False  # edges are seen from the neighbour tile
        iy, ix = np.where(pk)
        ox, oy = e - lidar.OX, n - lidar.OY
        out += [(ox + i + 0.5, oy + j + 0.5, float(c[j, i])) for j, i in zip(iy, ix)]
    return np.array(out)


def audit_d():
    from scipy.spatial import cKDTree
    tk = tile_keys()
    gt = []
    for f in TILES:
        for r in json.load(open(f)).get("trees", []):
            gt.append((r[0], r[1], r[5], r[4]))
    gt = np.array(gt)
    pk = chm_peaks()
    inside = lambda a: np.array([f"{math.floor(x/200)}_{math.floor(y/200)}" in tk for x, y in a[:, :2]])
    pk = pk[in_area(pk[:, 0], pk[:, 1])]
    gt = gt[in_area(gt[:, 0], gt[:, 1])]
    T = cKDTree(gt[:, :2]); P = cKDTree(pk[:, :2])
    d_pk, i_pk = P.query(gt[:, :2])           # nearest peak for each game tree
    d_gt, i_gt = T.query(pk[:, :2])           # nearest game tree for each peak
    sup = np.zeros(len(gt), bool)   # any canopy > 2.5 m above ground within 3 m of the game tree
    for i, (x, y) in enumerate(gt[:, :2]):
        X, Y = x + lidar.OX, y + lidar.OY
        e, n = int(X // 500) * 500, int(Y // 500) * 500
        S = SUP.get((e, n))
        if S is not None:
            sup[i] = S[min(int(Y - n), 499), min(int(X - e), 499)]
    extra = d_pk > 3.0
    missing = d_gt > 3.0
    tsv("d_trees_extra", ["x", "y", "game_h", "dist_to_peak"], [(round(a, 1), round(b, 1), round(h, 1), round(d, 1)) for (a, b, h, c_), d in zip(gt[extra], d_pk[extra])])
    tsv("d_trees_missing", ["x", "y", "chm_h", "dist_to_tree"], [(round(a, 1), round(b, 1), round(h, 1), round(d, 1)) for (a, b, h), d in zip(pk[missing], d_gt[missing])])
    mt = ~extra
    dh = gt[mt, 2] - pk[i_pk[mt], 2]
    say("## d) Baeume: Spiel (Kacheln) gegen CHM-Spitzen (LiDAR, Klasse 3-5, Hoehe > 3 m, Match 3 m)")
    say(f"- Spiel {len(gt)} Baeume, LiDAR-Spitzen {len(pk)}; Spiel-Baeume ohne Spitze <3 m: {int(extra.sum())} ({extra.mean()*100:.0f} %); Spitzen ohne Spiel-Baum: {int(missing.sum())} ({missing.mean()*100:.0f} %)")
    say(f"- Spiel-Baeume ganz ohne Kronenhoehe >2.5 m im Umkreis 3 m (echt unbelegt): {int((~sup).sum())} ({(~sup).mean()*100:.0f} %)")
    tsv("d_trees_unsupported", ["x", "y", "game_h"], [(round(a_, 1), round(b_, 1), round(h_, 1)) for (a_, b_, h_, c_) in gt[~sup]])
    say(f"- Hoehe gematchter Paare (Spiel - LiDAR): Median {np.median(dh):+.1f} m, P10 {np.percentile(dh,10):+.1f}, P90 {np.percentile(dh,90):+.1f}; Lagefehler Median {np.median(d_pk[mt]):.1f} m")
    big = pk[missing]; big = big[np.argsort(-big[:, 2])][:8]
    say("- hoechste fehlende LiDAR-Baeume (x,y,Hoehe): " + "; ".join(f"({a:.0f},{b:.0f}) {h:.0f} m" for a, b, h in big))
    say("- Hinweis: Wald/Hecken/Gartenbaeume stehen z.T. als 'wild' (nicht in trees); 'fehlend' hier umfasst diese.")


# ---- e: lamps / masts -----------------------------------------------------------------------------------------------------
def audit_e():
    from scipy.spatial import cKDTree
    tk = tile_keys()
    lamps, masts = [], []
    for f in TILES:
        m = json.load(open(f))
        lamps += [(r[0], r[1], r[4]) for r in m.get("lamps", [])]
        masts += [(r[0], r[1], 0) for r in m.get("masts", [])]
    pl = lidar.masts()
    pl = pl[in_area(pl[:, 0], pl[:, 1])]
    P = cKDTree(pl[:, :2])
    gm = np.array(masts); gl = np.array(lamps)
    allg = np.vstack([gm, gl]) if len(gl) else gm
    G = cKDTree(allg[:, :2])
    dm, _ = P.query(gm[:, :2]); dl, _ = P.query(gl[:, :2]) if len(gl) else (np.array([]), None)
    d_p, _ = G.query(pl[:, :2])
    missing = d_p > 2.0
    tsv("e_poles_missing", ["x", "y", "z_top", "h_above", "n"], [(round(a, 1), round(b, 1), round(c, 1), round(c - d, 1), int(n)) for (a, b, c, d, n) in pl[missing]])
    tsv("e_masts_extra", ["kind", "x", "y", "dist_nearest_pole"], [("mast", round(a, 1), round(b, 1), round(d, 1)) for (a, b, _), d in zip(gm, dm) if d > 2.0] + [("lamp", round(a, 1), round(b, 1), round(d, 1)) for (a, b, _), d in zip(gl, dl) if d > g_span(gl, a, b)])
    say("## e) Strassenlampen/Masten: Spiel gegen LiDAR-Masten (Klasse 15/1, vertikal, >3.5 m, 1-m-Cluster)")
    say(f"- Spiel: {len(gm)} Masten (Stehlampen/Kandelaber), {len(gl)} Haengeleuchten; LiDAR: {len(pl)} Masten im Spielgebiet")
    say(f"- Spiel-Masten mit LiDAR-Mast <=2 m: {np.mean(dm <= 2)*100:.0f} %, <=4 m: {np.mean(dm <= 4)*100:.0f} %")
    if len(gl):
        sp = gl[:, 2] / 2 + 2
        say(f"- Haengeleuchten mit LiDAR-Mast <= Halbspanne+2 m: {np.mean(dl <= sp)*100:.0f} %")
    say(f"- LiDAR-Masten ohne Spiel-Objekt <=2 m (fehlend): {int(missing.sum())} von {len(pl)} ({missing.mean()*100:.0f} %); hoechste Dichte siehe audit_e_poles_missing.tsv")
    if missing.any():
        cl = defaultdict(int)
        for x, y in pl[missing][:, :2]:
            cl[(int(x // 100), int(y // 100))] += 1
        say("- Cluster fehlender Masten (100-m-Block, Anzahl): " + ", ".join(f"({k[0]*100},{k[1]*100}) {v}" for k, v in sorted(cl.items(), key=lambda kv: -kv[1])[:8]))
    say("- Hinweis: Masten enthalten auch Tram-/Fahrleitungsmasten und Signalmasten (Spiel: signals/masts getrennt); Ampeln nicht im Vergleich.")


def g_span(gl, a, b):
    return 8.0


if __name__ == "__main__":
    todo = sys.argv[1:] or list("abcde")
    for k in todo:
        {"a": audit_a, "b": audit_b, "c": audit_c, "d": audit_d, "e": audit_e}[k]()
        say()
    (OUT / "audit_lidar.md").write_text("# LiDAR-Audit (pipeline/audit_lidar.py)\n\n" + "\n".join(LINES) + "\n")
