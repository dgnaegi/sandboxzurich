"""Rail network from OSM (railway=rail) with attributes, switches, signals, buffer stops and consistent track heights.

Heights: terrain (swissALTI3D) smoothed over the whole network graph (Laplacian on the dense sample graph, so branches
meeting at a switch share the same height), bridge decks interpolated between their abutments (chains over several
OSM ways), tunnels sink along a 4 % ramp from the portals. Dense samples every STEP metres, shared OSM nodes keep ids.
"""
import math
from collections import defaultdict

import numpy as np
from shapely.geometry import LineString, Polygon

import sources
from config import POLYGON

STEP = 4.0
SERVICES = (None, "yard", "siding", "crossover", "spur")
PORTAL_GRADE = 0.04
TUNNEL_DEPTH = 9.0
SMOOTH_ITERS = 14


class Net:
    pass


def way_class(t):
    tun = t.get("tunnel") in ("yes", "building_passage", "flooded")
    try:
        lay = int(t.get("layer", 0))
    except ValueError:
        lay = 0
    try:
        lev = int(str(t.get("level", 0)).split(";")[0])
    except ValueError:
        lev = 0
    if tun or lay <= -2 or lev <= -2:
        return "tunnel"
    if t.get("bridge") not in (None, "no"):
        return "bridge"
    return "ground"


def load(H):
    nodes, els = sources.osm()
    play = Polygon(POLYGON).buffer(260)
    ways, nodetags = [], {}
    stops, plats, roofs = [], [], []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node":
            if e["id"] in nodes and t.get("railway") in ("switch", "signal", "buffer_stop", "railway_crossing"):
                nodetags[e["id"]] = t
            if t.get("railway") in ("stop", "station") and t.get("train") == "yes" and e["id"] in nodes:
                stops.append({"name": t.get("name", ""), "x": nodes[e["id"]][0], "y": nodes[e["id"]][1],
                              "ref": t.get("local_ref"), "kind": t["railway"]})
            continue
        if e["type"] != "way" or not all(n in nodes for n in e["nodes"]):
            continue
        xy = np.array([nodes[n] for n in e["nodes"]])
        if len(xy) < 2 or not play.intersects(LineString(xy)):
            continue
        if t.get("railway") == "rail" and t.get("service") in SERVICES:
            ways.append({"id": e["id"], "nodes": e["nodes"], "xy": xy, "tags": t, "cls": way_class(t)})
        elif t.get("railway") == "platform" or (t.get("public_transport") == "platform" and t.get("train") == "yes"):
            plats.append({"xy": xy, "tags": t})
        elif t.get("building") in ("roof", "train_station") and len(xy) >= 4 and (xy[0] == xy[-1]).all():
            roofs.append(xy)
    net = Net()
    net.nodes, net.nodetags = nodes, nodetags
    net.stops, net.plats, net.roofs = stops, plats, roofs
    net.ways = ways
    densify(net, H)
    apply_decks(net, els, H)
    return net


def densify(net, H):
    """Dense samples + heights. Fills way['pts'] (n,3), way['nidx'] (index of each OSM node in pts)."""
    pid = {}            # key -> dense index
    P = []              # xy
    def get(key, p):
        if key not in pid:
            pid[key] = len(P)
            P.append(p)
        return pid[key]
    for wi, w in enumerate(net.ways):
        xy, ids = w["xy"], []
        nidx = []
        for i in range(len(xy) - 1):
            k = max(1, int(math.ceil(np.linalg.norm(xy[i + 1] - xy[i]) / STEP)))
            for j in range(k):
                if j == 0:
                    ids.append(get(("n", w["nodes"][i]), xy[i]))
                    nidx.append(len(ids) - 1)
                else:
                    ids.append(get(("w", wi, len(ids)), xy[i] + (xy[i + 1] - xy[i]) * j / k))
        ids.append(get(("n", w["nodes"][-1]), xy[-1]))
        nidx.append(len(ids) - 1)
        w["ids"], w["nidx"] = np.array(ids), nidx
    P = np.array(P)
    z = np.asarray(H.at(P[:, 0], P[:, 1]), np.float64)
    # --- smoothing graph (ground only; bridge/tunnel samples are overwritten below)
    ea, eb = [], []
    for w in net.ways:
        ea.extend(w["ids"][:-1]); eb.extend(w["ids"][1:])
    ea, eb = np.array(ea), np.array(eb)
    deg = np.bincount(np.concatenate([ea, eb]), minlength=len(P)).astype(float)
    zs = z.copy()
    for _ in range(SMOOTH_ITERS):
        acc = np.bincount(ea, zs[eb], len(P)) + np.bincount(eb, zs[ea], len(P))
        zs = (acc + zs) / (deg + 1)
    # --- bridge / tunnel chains over consecutive ways
    nodeways = defaultdict(list)
    for wi, w in enumerate(net.ways):
        for n in (w["nodes"][0], w["nodes"][-1]):
            nodeways[n].append(wi)
    seen = set()
    for wi0, w0 in enumerate(net.ways):
        if w0["cls"] == "ground" or wi0 in seen:
            continue
        cls = w0["cls"]
        chain = chain_of(net, wi0, cls, nodeways, seen)   # [(wi, reversed)]
        idx = []
        for wi, rev in chain:
            ii = list(net.ways[wi]["ids"])
            ii = ii[::-1] if rev else ii
            idx.extend(ii if not idx else ii[1:])
        idx = np.array(idx)
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P[idx], axis=0), axis=1))])
        L = d[-1]
        if cls == "bridge":
            z[idx] = zs[idx[0]] + (zs[idx[-1]] - zs[idx[0]]) * (d / max(L, 1e-6))
        else:
            dep = np.minimum(TUNNEL_DEPTH, PORTAL_GRADE * np.minimum(d, L - d))
            # a tunnel continuing from a tunnel at the play-area border: keep ends at their terrain
            z[idx] = np.where(True, zs[idx] - dep, zs[idx])
    for w in net.ways:
        g = w["cls"] == "ground"
        zz = zs[w["ids"]] if g else z[w["ids"]]
        w["pts"] = np.column_stack([P[w["ids"]], zz])
        w["svc"] = w["tags"].get("service")
        w["elec"] = w["tags"].get("electrified") != "no"
    net.P, net.zs, net.z = P, zs, z


def chain_of(net, wi0, cls, nodeways, seen):
    """Walk both ways from wi0 over end-to-end connected ways of the same class (degree-2 joints)."""
    chain = [(wi0, False)]
    seen.add(wi0)
    for direction in (0, 1):
        cur, rev = wi0, False
        while True:
            w = net.ways[cur]
            end = w["nodes"][-1] if (direction == 0) != rev else w["nodes"][0]
            cand = [x for x in nodeways[end] if x != cur and x not in seen and net.ways[x]["cls"] == cls]
            if len(nodeways[end]) != 2 or len(cand) != 1:
                break
            nx = cand[0]
            nw = net.ways[nx]
            nrev = nw["nodes"][-1] == end if direction == 0 else nw["nodes"][0] == end
            # orientation relative to the chain direction
            if direction == 0:
                nrev = nw["nodes"][-1] == end
                chain.append((nx, nrev))
            else:
                nrev = nw["nodes"][0] == end
                chain.insert(0, (nx, nrev))
            seen.add(nx)
            cur, rev = nx, nrev
    return chain


def apply_decks(net, els, H):
    """Rails on viaducts/ramps follow the deck heights of pipeline/bridges.py (same ids -> same heights as the bridge mesh)."""
    import bridges
    from config import AREA
    from decktrack import DeckTrack
    dt = DeckTrack([b for b in bridges.bridge_ways(net.nodes, els, AREA, H) if b["kind"] == "rail"])
    n = 0
    for w in net.ways:
        if w["cls"] == "tunnel":
            continue
        dz = dt.z(w["pts"][:, :2], [w["id"]])
        if all(v is None for v in dz):
            continue
        z = w["pts"][:, 2].copy()
        for i, v in enumerate(dz):
            if v is not None:
                z[i] = v
        w["pts"][:, 2] = z
        n += 1
    print("rail ways on bridge decks:", n)
