"""Score the modelled ramp rows of a site against the reference scopes; one Markdown report per site.

  python3 pipeline/scopes/score.py <site>[,<site>] [--tiles web/public/tiles] [--out research/bridges/scopes] [--no-overlay]
                                   [--label v2] [--override data/build/tiles_pilot]
Compares two row sets (pipeline/scopes/rows.py): live (deployed) and the current tile JSON (the last builder's output; `--label`
names that column, default "current"; `--override <dir>` scores tiles of an older output instead, e.g. the LiDAR pilot snapshot).
Numbers are metres and ratios per scope (research/bridges/scopes_plan.md §3), never a single score; the overlay
(pipeline/scopes/overlay.py) goes next to the report so the reader can judge by eye. Per-station tables are written as
<out>/<site>_<label>_stations.tsv; a hand-written <out>/<site>_notes.md is appended to the report when present.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import metrics as M  # noqa: E402
import scope_av  # noqa: E402
from ramp_sites import site as site_cfg  # noqa: E402
from rows import Rows  # noqa: E402

STEP = 2.0
TSV_COLS = ("s", "x", "y", "model", "kind", "z", "g", "b", "wl", "wr", "lz", "lflag", "lg", "av_mode", "av_lo", "av_hi", "road_lo", "road_hi", "wall_gl", "wall_gr")


def f1(v, unit="", signed=False):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "–"
    return (f"{v:+.1f}" if signed else f"{v:.1f}") + unit


def run_end(T, mask, j_end, step_dir, gap=1, look=50):
    """Where a feature ends past the chain end: from the end station walk inward until the feature is present (<= look stations),
    then outward while it stays present (<= gap missing stations in a row). Metres past the end, None if absent near the end."""
    n = len(mask)
    i = j_end
    k = 0
    while 0 <= i < n and not mask[i] and k < look:
        i -= step_dir; k += 1
    if not (0 <= i < n) or not mask[i]:
        return None
    last, miss = i, 0
    while 0 <= i + step_dir < n:
        i += step_dir
        if mask[i]:
            last, miss = i, 0
        else:
            miss += 1
            if miss > gap:
                break
    return step_dir * (T["s"][last] - T["s"][j_end]) + STEP / 2


def landing(T, end):
    j = np.flatnonzero(T["is_model"])[end]; d = 1 if end == -1 else -1
    return {"model_end": run_end(T, T["kind"] > 0, j, d, gap=0), "av_deck_end": run_end(T, np.isfinite(T["av_w"]), j, d),
            "wall_end": run_end(T, T["wall_flank"], j, d, gap=3), "end_el_game": float(T["z"][j] - T["g"][j]),
            "end_el_lidar": float(T["z"][j] - T["lg"][j]), "end_terr": float(T["terr"][j])}


def summarize(chains, tables, av, rows, box):
    S = {k: [] for k in ("av_w", "model_w", "w_err", "off", "excess", "uncovered", "road_w", "res_b", "res_g", "terr")}
    L = {k: 0.0 for k in ("model_struct", "av_deck", "both", "model_only", "av_only", "wall_l", "wall_r", "solid", "solid_wall", "deck_wall", "edges")}
    L.update({k: 0 for k in ("stations", "ramp_stations", "road_stations", "bridge_cls", "ground_cls", "terr_n")})
    for T in tables:
        m = T["is_model"] & T["inbox"]
        L["stations"] += int(m.sum())
        struct = m & (T["kind"] > 0); deck = m & np.isfinite(T["av_w"])
        L["model_struct"] += struct.sum() * STEP; L["av_deck"] += deck.sum() * STEP; L["edges"] += (m & (T["av_mode"] == 2)).sum() * STEP
        L["both"] += (struct & deck).sum() * STEP; L["model_only"] += (struct & ~deck).sum() * STEP; L["av_only"] += (deck & ~struct).sum() * STEP
        r = m & T["ramp"]
        L["ramp_stations"] += int(r.sum())
        S["av_w"] += T["av_w"][r].tolist(); mw = (T["wl"] + T["wr"]); S["model_w"] += mw[r].tolist()
        S["w_err"] += (mw - T["av_w"])[r].tolist(); S["off"] += T["av_off"][r].tolist()
        S["excess"] += np.maximum(T["excess_l"], T["excess_r"])[r].tolist()
        S["uncovered"] += np.maximum(-T["excess_l"], -T["excess_r"])[r].tolist()
        rd = m & np.isfinite(T["road_w"]); L["road_stations"] += int(rd.sum()); S["road_w"] += T["road_w"][rd].tolist()
        L["wall_l"] += (m & T["wall_l"]).sum() * STEP; L["wall_r"] += (m & T["wall_r"]).sum() * STEP
        solid = m & (T["kind"] == 1); L["solid"] += solid.sum() * STEP
        L["solid_wall"] += (solid & (T["wall_l"] | T["wall_r"])).sum() * STEP
        L["deck_wall"] += (m & (T["kind"] == 2) & (T["wall_l"] | T["wall_r"])).sum() * STEP
        bcls = m & (T["lflag"] == 1); gcls = m & (T["lflag"] == 2)
        L["bridge_cls"] += int(bcls.sum()); L["ground_cls"] += int(gcls.sum())
        S["res_b"] += T["res"][bcls].tolist(); S["res_g"] += T["res"][gcls].tolist()
        tv = T["terr"][m]; S["terr"] += tv.tolist(); L["terr_n"] += int(np.isfinite(tv).sum())
    out = {"len": L}
    for k, v in S.items():
        v = np.asarray(v, float); v = v[np.isfinite(v)]
        out[k] = {"p50": M.pct(v, 50), "p95": M.pct(v, 95), "abs50": M.pct(np.abs(v), 50), "abs95": M.pct(np.abs(v), 95), "max": float(np.max(np.abs(v))) if len(v) else np.nan, "n": len(v)}
    out["piers"] = M.piers(chains, tables, av, rows)
    out["areas"] = M.areas(chains, tables, av, box)
    return out


def terrain_runs(T, thr=-1.0):
    """s-ranges (model stations in the window) where the game terrain lies more than |thr| below the LiDAR ground."""
    m = T["is_model"] & T["inbox"] & np.isfinite(T["terr"]) & (T["terr"] < thr)
    runs, start = [], None
    for i, v in enumerate(m):
        if v and start is None:
            start = i
        if not v and start is not None:
            runs.append((start, i - 1)); start = None
    if start is not None:
        runs.append((start, len(m) - 1))
    return [(float(T["s"][a]), float(T["s"][b]), float(np.min(T["terr"][a:b + 1]))) for a, b in runs if (b - a + 1) * STEP >= 6]


def score_site(name, tiles_dir, label="current", override=None):
    cfg = site_cfg(name); av = scope_av.load(name)
    res = {"label": label}
    for variant in ("live", "current"):
        R = Rows(tiles_dir, variant, override if variant == "current" else None); chains = R.site_chains(cfg)
        tables, lands = [], []
        for c in chains:
            ext = tuple(e for e in (0, -1) if c.ends[e] in ("grade", "air"))
            T = M.measure(c, av, R, box=cfg["view"], ext=ext)
            tables.append(T)
            for e in ext:
                if cfg["view"][0] <= c.P[e, 0] <= cfg["view"][2] and cfg["view"][1] <= c.P[e, 1] <= cfg["view"][3]:
                    lands.append((repr(c), c.ends[e], landing(T, e)))
        res[variant] = {"chains": chains, "tables": tables, "landings": lands, "sum": summarize(chains, tables, av, R, cfg["view"])}
    return cfg, av, res


def write_tsv(f, chains, tables):
    with open(f, "w") as fh:
        fh.write("chain\t" + "\t".join(TSV_COLS) + "\n")
        for ci, (c, T) in enumerate(zip(chains, tables)):
            for i in range(len(T["s"])):
                vals = {"s": T["s"][i], "x": T["xy"][i, 0], "y": T["xy"][i, 1], "model": int(T["is_model"][i]), "kind": int(T["kind"][i]),
                        "lflag": int(T["lflag"][i]), "av_mode": int(T["av_mode"][i])}
                row = [str(ci)] + [(f"{vals[k]}" if k in vals else ("" if not np.isfinite(T[k][i]) else f"{T[k][i]:.2f}")) for k in TSV_COLS]
                fh.write("\t".join(row) + "\n")


def report(name, cfg, av, res, out_dir):
    L = res["live"]["sum"]; P = res["current"]["sum"]; lab = res["label"]
    lines = [f"# Scope report: {cfg['title']} (`{name}`)", "",
             f"Generated {dt.date.today().isoformat()} by `pipeline/scopes/score.py`; window {cfg['view']} (game metres). "
             f"Columns: live = deployed rows (release 23), {lab} = the rows in the tile JSON now. "
             f"Overlay `preview/scopes/{name}_overlay.png` (left live rows, right {lab} rows; orthophoto, cadastre, LiDAR bridge class). "
             f"Per-station tables `{name}_live_stations.tsv`, `{name}_{lab}_stations.tsv`.", "",
             "## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)", "",
             "Objects in the fetch box: " + ", ".join(f"{g} {n}" for g, n in sorted(av.summary().items()) if g in ("deck", "pier", "wall", "stairs", "underpass", "shelter", "carriageway", "footway", "island", "path")) + ".", "",
             f"| Measure | live rows | {lab} rows | reading |", "|---|---|---|---|"]

    def row(label, lv, pv, how):
        lines.append(f"| {label} | {lv} | {pv} | {how} |")
    la, pa = L["areas"], P["areas"]
    row("Chains / stations in window", f"{len(res['live']['chains'])} / {L['len']['stations']}", f"{len(res['current']['chains'])} / {P['len']['stations']}", "2 m stations of the modelled axes inside the window")
    row("Footprint IoU vs AV ramp outline", f"{la['outline_iou']:.2f}", f"{pa['outline_iou']:.2f}", "AV structure cross-sections along the modelled axes (ramp stations); 1 = identical outline")
    row("Footprint IoU / precision / recall vs all AV bridge polygons", f"{la['iou']:.2f} / {la['precision']:.2f} / {la['recall']:.2f}", f"{pa['iou']:.2f} / {pa['precision']:.2f} / {pa['recall']:.2f}", "polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck")
    row("Footprint area model / AV outline / AV polygons (m²)", f"{la['model_area']:.0f} / {la['outline_area']:.0f} / {la['av_area']:.0f}", f"{pa['model_area']:.0f} / {pa['outline_area']:.0f} / {pa['av_area']:.0f}", "")
    row("Structure length model / AV (m)", f"{L['len']['model_struct']:.0f} / {L['len']['av_deck']:.0f}", f"{P['len']['model_struct']:.0f} / {P['len']['av_deck']:.0f}", "along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons")
    row("of which both / model only / AV only (m)", f"{L['len']['both']:.0f} / {L['len']['model_only']:.0f} / {L['len']['av_only']:.0f}", f"{P['len']['both']:.0f} / {P['len']['model_only']:.0f} / {P['len']['av_only']:.0f}", "model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade")
    row("AV structure as edge polygons only (m)", f"{L['len']['edges']:.0f}", f"{P['len']['edges']:.0f}", "axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures")
    row("AV structure width p50 (m, ramp stations)", f1(L["av_w"]["p50"], " m"), f1(P["av_w"]["p50"], " m"), f"stations where the AV structure is narrower than {M.MAIN_DECK:.0f} m (live {L['len']['ramp_stations']}, {lab} {P['len']['ramp_stations']})")
    row("Modelled width p50 (m, same stations)", f1(L["model_w"]["p50"], " m"), f1(P["model_w"]["p50"], " m"), "wl + wr (live rows: w)")
    row("Width error p50 / p95 |err| (m)", f"{f1(L['w_err']['p50'], ' m', True)} / {f1(L['w_err']['abs95'], ' m')}", f"{f1(P['w_err']['p50'], ' m', True)} / {f1(P['w_err']['abs95'], ' m')}", "model minus AV structure width")
    row("Axis offset to AV centre line p50 / p95 (m)", f"{f1(L['off']['abs50'], ' m')} / {f1(L['off']['abs95'], ' m')}", f"{f1(P['off']['abs50'], ' m')} / {f1(P['off']['abs95'], ' m')}", "distance between the modelled axis and the middle of the AV structure at the station")
    row("Edge overshoot p50 / p95 (m)", f"{f1(L['excess']['p50'], ' m', True)} / {f1(L['excess']['p95'], ' m', True)}", f"{f1(P['excess']['p50'], ' m', True)} / {f1(P['excess']['p95'], ' m', True)}", "how far the wider modelled edge reaches beyond the AV edge (negative = inside)")
    row("Uncovered AV width p50 / p95 (m)", f"{f1(L['uncovered']['p50'], ' m', True)} / {f1(L['uncovered']['p95'], ' m', True)}", f"{f1(P['uncovered']['p50'], ' m', True)} / {f1(P['uncovered']['p95'], ' m', True)}", "AV structure left uncovered on the worse side (negative = model wider)")
    row("AV carriageway width p50 (m)", f"{f1(L['road_w']['p50'], ' m')} ({L['len']['road_stations']} st.)", f"{f1(P['road_w']['p50'], ' m')} ({P['len']['road_stations']} st.)", "Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks)")
    row("Walls at the modelled edge left / right (m)", f"{L['len']['wall_l']:.0f} / {L['len']['wall_r']:.0f}", f"{P['len']['wall_l']:.0f} / {P['len']['wall_r']:.0f}", f"AV «Mauer» within {M.WALL_NEAR} m of the modelled edge")
    row("Modelled solid length / with a wall (m)", f"{L['len']['solid']:.0f} / {L['len']['solid_wall']:.0f}", f"{P['len']['solid']:.0f} / {P['len']['solid_wall']:.0f}", "solid = underside on the ground (embankment / skirt); a flanking wall confirms it")
    row("Modelled free deck with a wall at the edge (m)", f"{L['len']['deck_wall']:.0f}", f"{P['len']['deck_wall']:.0f}", "walls flank embankments, not decks on piers: candidates for a solid section")
    pl, pp = L["piers"], P["piers"]
    row("AV piers near the axes: under deck / solid / grade / outside", f"{pl['av_total']}: {pl['under_deck']} / {pl['under_solid']} / {pl['under_grade']} / {pl['outside']}", f"{pp['av_total']}: {pp['under_deck']} / {pp['under_solid']} / {pp['under_grade']} / {pp['outside']}", "piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint")
    row("Tile pier rows near the axes / at an AV pier", f"{pl['tile_total']} / {pl['tile_matched']}", f"{pp['tile_total']} / {pp['tile_matched']}", "modelled piers within 2 m of a cadastre pier polygon")
    row("AV piers with a modelled pier within 2 m", f"{pl['av_matched']} / {pl['av_total']}", f"{pp['av_matched']} / {pp['av_total']}", "")
    lines += ["", "### Landings (chain ends at grade or in the air, inside the window)", "",
              "| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |", "|---|---|---|---|---|---|---|---|---|"]
    for v in ("live", "current"):
        for crep, kind, ld in res[v]["landings"]:
            lines.append(f"| {v if v == 'live' else lab} | {crep} | {kind} | {f1(ld['model_end'], ' m', True)} | {f1(ld['av_deck_end'], ' m', True)} | {f1(ld['wall_end'], ' m', True)} | {f1(ld['end_el_game'], ' m', True)} | {f1(ld['end_el_lidar'], ' m', True)} | {f1(ld['end_terr'], ' m', True)} |")
    lines += ["", f"Metres past the chain end along the road graph (negative = before the end; continuation {M.EXT:.0f} m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within {M.WALL_SIDE:.0f} m of the axis any more.", "",
              "## Scope A, LiDAR (heights along the modelled axes)", "", f"| Measure | live rows | {lab} rows | reading |", "|---|---|---|---|"]
    row("Stations with bridge class / ground class", f"{L['len']['bridge_cls']} / {L['len']['ground_cls']}", f"{P['len']['bridge_cls']} / {P['len']['ground_cls']}", "central strip of the modelled width: class 17 present, else class 2")
    row("Height residual on bridge class p50 / p95 |res| (m)", f"{f1(L['res_b']['p50'], ' m', True)} / {f1(L['res_b']['abs95'], ' m')}", f"{f1(P['res_b']['p50'], ' m', True)} / {f1(P['res_b']['abs95'], ' m')}", "model minus LiDAR deck top (35th percentile of the strip)")
    row("Height residual on ground class p50 / p95 |res| (m)", f"{f1(L['res_g']['p50'], ' m', True)} / {f1(L['res_g']['abs95'], ' m')}", f"{f1(P['res_g']['p50'], ' m', True)} / {f1(P['res_g']['abs95'], ' m')}", "model minus LiDAR ground where no deck class: embankment or at grade")
    row("Terrain game − LiDAR ground p50 / p95 |d| / max (m)", f"{f1(L['terr']['p50'], ' m', True)} / {f1(L['terr']['abs95'], ' m')} / {f1(L['terr']['max'], ' m')} ({L['len']['terr_n']} st.)", f"{f1(P['terr']['p50'], ' m', True)} / {f1(P['terr']['abs95'], ' m')} / {f1(P['terr']['max'], ' m')} ({P['len']['terr_n']} st.)", "game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error")
    lines += ["", "## Chains", ""]
    for v in ("live", "current"):
        for c, T in zip(res[v]["chains"], res[v]["tables"]):
            m = T["is_model"] & T["inbox"]; r = m & T["ramp"]
            tr = "; ".join(f"terrain {d:.1f} m low at s {a:.0f}–{b:.0f}" for a, b, d in terrain_runs(T))
            lines.append(f"- {v if v == 'live' else lab}: {c}; in window {int(m.sum()) * 2} m; AV ramp width p50 {f1(M.pct(T['av_w'][r], 50), ' m')}, modelled {f1(M.pct((T['wl'] + T['wr'])[r], 50), ' m')}; "
                         f"axis offset p50 {f1(M.pct(np.abs(T['av_off'][r]), 50), ' m')}, max {f1(M.pct(np.abs(T['av_off'][r]), 100), ' m')}; "
                         f"kinds grade/solid/deck {int((m & (T['kind'] == 0)).sum()) * 2}/{int((m & (T['kind'] == 1)).sum()) * 2}/{int((m & (T['kind'] == 2)).sum()) * 2} m" + (f"; {tr}" if tr else ""))
    lines += ["", "## Scope C, imagery + vision helper", "", "Not run yet (phase 3).", ""]
    notes = os.path.join(out_dir, f"{name}_notes.md")
    if os.path.exists(notes):
        lines += ["## Reading", "", open(notes).read().strip(), ""]
    os.makedirs(out_dir, exist_ok=True)
    f = os.path.join(out_dir, f"{name}.md")
    open(f, "w").write("\n".join(lines))
    for v in ("live", "current"):
        write_tsv(os.path.join(out_dir, f"{name}_{v if v == 'live' else lab}_stations.tsv"), res[v]["chains"], res[v]["tables"])
    return f


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tiles = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    out_dir = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "research", "bridges", "scopes")
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "current"
    override = sys.argv[sys.argv.index("--override") + 1] if "--override" in sys.argv else None
    for n in (args[0].split(",") if args else ["gerold", "duttweiler"]):
        cfg, av, res = score_site(n, tiles, label, override)
        f = report(n, cfg, av, res, out_dir)
        print(f)
        if "--no-overlay" not in sys.argv:
            import overlay
            print(overlay.render(n, tiles, label=label, override=override))
