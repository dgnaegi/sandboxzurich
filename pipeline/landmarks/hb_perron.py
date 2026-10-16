"""Zuerich HB Perronhalle (Gleise 3-18): raised platforms (like pipeline/railways.py: rail head 0.29 + 0.55 m above terrain) with edge, tactile strip and
safety line, steps down to the Querhalle floor, one glazed steel Laengshalle per island platform (vault over platform + the two tracks, steel arches every
17.5 m, forked steel columns in the platform axis, clocks and boards), stair/lift housings, waiting rooms, platform signs. Tracks (rails, ballast, catenary)
belong to pipeline/railways.py and are NOT modelled here. Walkability of the raised decks: web/public/data/hb_decks.json (DeckRows, loaded into the
BridgeIndex like station_decks.json). Data: research/hb/tracks.json (OSM platform relations, SBB perron)."""
from hb_kit import *
import hb_geom as G
import hb_props as P

D_HEAD = G.PLAT_HEAD_D          # -45.0
D_END = -470.0                  # platforms are 425 m long (head at d = -45)
D_VAULT = -300.0                # glazed vaults (Laengshallen) up to here, simple cantilever canopies beyond (swissBUILDINGS3D roof heights)
TOP = 0.98                      # platform surface above model z0 (terrain plateau ~ -2.8 m: +0.29 rail head +0.55 platform + 3 cm over railways.py decks)
STEPS = 8
STEP_D = 0.34
PITCH = 17.5


def build():
    m = Model("hb_perron")
    A = P.make_atlas('perron')
    ms = m.mat("sign", *A.images(), rough=0.8)   # 512 x 384 atlas (+ emissive for the lamps / boards at night)
    mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    ASPH, CONC, WHITE, TAC = hx("#8e9093"), hx("#a7a8a5"), hx("#ececea"), hx("#b4b3ad")
    STEELC, GLASS_O, GLASS_I = hx("#2d3033"), hx("#9eb3bd"), hx("#7d8a92")
    colliders = []
    plat = dict(G.PLATFORMS)
    for ref, (cs, cn) in plat.items():
        cm = (cs + cn) / 2
        d0, d1 = D_END, D_HEAD
        bx(m, mf, d0, d1, cs, cn, -0.3, TOP, CONC, top=False, sides=(1, 0, 1, 1))
        slab(m, mf, d0, d1, cs, cn, TOP, ASPH)
        for edge, sg in ((cs, 1), (cn, -1)):   # tactile strip + white safety line, inset from the edge (as railways.py)
            a_, b_ = (edge + 0.0, edge + 0.45) if sg > 0 else (edge - 0.45, edge - 0.0)
            slab(m, mf, d0, d1, a_, b_, TOP + 0.006, TAC)
            a_, b_ = (edge + 0.85, edge + 0.97) if sg > 0 else (edge - 0.97, edge - 0.85)
            slab(m, mf, d0, d1, a_, b_, TOP + 0.009, WHITE)
        # steps down to the Querhalle floor (z 0) at the head end
        for k in range(STEPS):
            zt = G.FLOOR + (TOP - G.FLOOR) * (1 - (k + 1) / STEPS)
            bx(m, mf, D_HEAD + k * STEP_D, D_HEAD + (k + 1) * STEP_D, cs, cn, 0.0, max(zt, G.FLOOR + 0.01), hx("#b0aea6") if k % 2 else hx("#a29f98"), top=True, sides=(0, 0, 0, 0))
        # head-end sign boards with the track numbers on a post per platform
        refs = ref.split("/")
        for k, r in enumerate(refs):
            R = A.rects.get("gl" + r)
            if not R: continue
            cc = cm + ((-1.6 if k == 0 else 1.6) if len(refs) == 2 else 0.0)
            for sg in (-1, 1):
                dd = D_HEAD - 14.0 + 0.05 * sg
                a_, b_ = (cc - 0.5, cc + 0.5) if sg < 0 else (cc + 0.5, cc - 0.5)
                m.quad(ms, [(dd, a_, TOP + 2.2), (dd, b_, TOP + 2.2), (dd, b_, TOP + 3.0), (dd, a_, TOP + 3.0)], uvr(R), W)
        bx(m, mf, D_HEAD - 14.03, D_HEAD - 13.97, cm - 0.03, cm + 0.03, TOP, TOP + 3.0, STEELC, top=False)
        # benches, stair housings, waiting rooms
        for dd in np.arange(D_HEAD - 30, D_END + 20, -38.0):
            P.bench(m, mf, dd, cm + 1.0, z0=TOP); P.bench(m, mf, dd - 6.0, cm - 1.0, z0=TOP)
        for dd in np.arange(D_HEAD - 60, D_END + 20, -75.0):    # stair/lift housing (solid)
            bx(m, mf, dd - 3.0, dd + 3.0, cm - 1.4, cm + 1.4, TOP, TOP + 2.6, hx("#c9c7c0"), top=True, colt=hx("#6b6f73"))
            q(m, mf, [(dd - 2.2, cm - 1.41, TOP), (dd + 2.2, cm - 1.41, TOP), (dd + 2.2, cm - 1.41, TOP + 2.0), (dd - 2.2, cm - 1.41, TOP + 2.0)], hx("#101214"), None, (0, -1, 0))
            colliders.append((dd - 3.0, dd + 3.0, cm - 1.4, cm + 1.4))
        if len(refs) == 2:
            for dd in (D_HEAD - 110, D_HEAD - 215):
                bx(m, mf, dd - 4.0, dd + 4.0, cm - 1.3, cm + 1.3, TOP, TOP + 2.4, hx("#aeb9bf"), top=True, colt=hx("#555b60"))
                for sg in (-1, 1):
                    q(m, mf, [(dd - 3.6 * sg, cm + sg * 1.31, TOP + 0.1), (dd + 3.6 * sg, cm + sg * 1.31, TOP + 0.1), (dd + 3.6 * sg, cm + sg * 1.31, TOP + 2.1), (dd - 3.6 * sg, cm + sg * 1.31, TOP + 2.1)],
                      hx("#364b57"), None, (0, sg, 0))
                colliders.append((dd - 4.0, dd + 4.0, cm - 1.3, cm + 1.3))
    # ---- Laengshallen: one vault per island platform (tracks 4-17), spanning gutter to gutter between the neighbouring tracks
    order = ["4/5", "6/7", "8/9", "10/11", "12/13", "14/15", "16/17"]
    zs, rise = 8.4, 3.6
    for ref in order:
        cs, cn = plat[ref]; cm = (cs + cn) / 2; hw = 8.65
        north = ref == '16/17'   # photos Mapillary #527 #531 #539: the northern hall has a dark red-brown timber-lined roof
        prof = barrel(m, mf, 'd', D_VAULT, D_HEAD - 0.5, cm, hw, zs, rise, hx('#7a4636') if north else GLASS_O, n=6, colin=hx('#9a6a48') if north else GLASS_I)
        for i in range(1, 6):   # longitudinal purlins on the underside (read as structure from below)
            x0 = prof[i][0]; h0 = prof[i][1] - 0.06
            q(m, mf, [(D_VAULT, cm + x0 - 0.1, h0), (D_HEAD - 0.5, cm + x0 - 0.1, h0), (D_HEAD - 0.5, cm + x0 + 0.1, h0), (D_VAULT, cm + x0 + 0.1, h0)], STEELC, None, (0, 0, -1))
        for dd in np.arange(D_HEAD - 3.0, D_VAULT, -PITCH):   # steel arches (black lattice look)
            for i in range(6):
                (x0, h0), (x1, h1) = prof[i], prof[i + 1]
                for dz, nn in ((-0.04, (0, 0, -1)), (0.05, (0, 0, 1))):
                    q(m, mf, [(dd - 0.2, cm + x0, h0 + dz), (dd + 0.2, cm + x0, h0 + dz), (dd + 0.2, cm + x1, h1 + dz), (dd - 0.2, cm + x1, h1 + dz)], STEELC, None, nn)
        for dd in np.arange(D_HEAD - 7.0, D_VAULT, -PITCH / 2):   # lamps under the vault (emissive at night)
            P.box_uv(m, ms, dd - 0.5, dd + 0.5, cm - 0.3, cm + 0.3, zs + rise - 1.3, zs + rise - 1.15, A.rects['lamp'])
        for k, dd in enumerate(np.arange(D_HEAD - 3.0, D_VAULT, -PITCH)):   # forked column in the platform axis (photos Perron #84 #86)
            m.cylinder(mf, dd, cm, 0.42, TOP, TOP + 3.0, n=8, col=STEELC, r1=0.30, mod=(4, 4))
            column(m, mf, dd, cm, 0.28, TOP + 3.0, zs + rise - 0.3, STEELC, 8)
            for sgn in (-1, 1):
                q(m, mf, [(dd - 0.18, cm, 6.0), (dd + 0.18, cm, 6.0), (dd + 0.18, cm + sgn * 3.6, zs + rise - 1.0), (dd - 0.18, cm + sgn * 3.6, zs + rise - 1.0)], STEELC, None, (0, 0, -1))
            colliders.append((dd - 0.35, dd + 0.35, cm - 0.35, cm + 0.35))
            if k % 4 == 1: P.board_pair(m, ms, mf, A, dd, cm, TOP + 4.3, 2.8, 2.0, hang=zs + rise - 0.3)
            if k % 4 == 3: P.clock_pair(m, ms, mf, A, dd, cm, TOP + 4.3, 0.6, hang=zs + rise - 0.3)
    # outer platforms 3 and 18 (whole length) and all island platforms beyond the vaults: cantilever canopy, 4 m above the deck
    for ref in plat:
        cs, cn = plat[ref]; cm = (cs + cn) / 2
        a0 = D_END if ref in ("3", "18") and False else D_END
        x1 = D_HEAD - 0.5 if ref in ("3", "18") else D_VAULT
        bx(m, mf, D_END, x1, cm - 2.6, cm + 2.6, TOP + 4.0, TOP + 4.25, hx("#7a4a38") if ref == "18" else hx("#6c7378"), top=True, bottom=True)
        for dd in np.arange(D_HEAD - 3.0 if ref in ("3", "18") else D_VAULT - 3.0, D_END, -PITCH):
            bx(m, mf, dd - 0.15, dd + 0.15, cm - 0.15, cm + 0.15, TOP, TOP + 4.0, STEELC, top=False)
            colliders.append((dd - 0.15, dd + 0.15, cm - 0.15, cm + 0.15))
    info(m, "hb_perron")
    return m, colliders


def decks():
    """DeckRows (web/src/world/bridges.ts) for the raised platforms: polyline along the platform axis, ends with the steps down to the Querhalle floor."""
    rows = []
    for ref, (cs, cn) in G.PLATFORMS.items():
        cm = (cs + cn) / 2; zt = GZ + TOP; zf = GZ + G.FLOOR
        pts = [(D_END, zt), (D_END / 2, zt), (D_HEAD, zt), (D_HEAD + STEPS * STEP_D, zf)]
        p = [[*[round(v, 2) for v in to_world(d, cm)], round(z, 2)] for d, z in pts]
        rows.append({"p": p, "g": [round(GZ + 0.1, 2)] * len(p), "b": [round(z - 0.4, 2) for _, z in pts], "w": round(cn - cs, 2), "kind": "foot", "name": f"HB Perron {ref}"})
    return {"decks": rows, "piers": []}


if __name__ == "__main__":
    m, cl = build()
    rings = [[[round(v, 2) for v in to_world(d, c)] for d, c in ((a, b), (a2, b), (a2, b2), (a, b2))] for a, a2, b, b2 in cl]
    H = json.load(open(ROOT / "research/hb/hide.json"))
    register(m, "hb_perron", "Zürich Hauptbahnhof + Perrons", H["osm_points"]["perron"], hide_ids=H["swiss"]["perron"], walkable=True, colliders=rings, load_r=480)
    json.dump(decks(), open(ROOT / "web/public/data/hb_decks.json", "w"), separators=(",", ":"))
    print("hb_decks.json:", len(decks()["decks"]), "decks")
