"""Build all bike GLBs (pure python, no Blender needed):  python3 pipeline/bikes/build_bikes.py [type ...]
Out: web/public/models/bikes/<type>.glb + <type>_lean.glb, rack.glb, manifest.json.
Axes: glTF (Y up, front = -Z, drive side +X), metres, origin = ground, midway between the wheel contacts."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from bikelib import *
from parts import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../web/public/models/bikes")

_REC = {}
_frame, _saddle = frame, saddle
def frame(m, G, *a, **k):
    r = _frame(m, G, *a, **k); _REC["st"] = r; return r
def saddle(m, G, st, sd, post=.12, **k):
    _REC["saddle"] = np.asarray(st, float) + np.asarray(sd, float) * post; return _saddle(m, G, st, sd, post=post, **k)

def geom(**k):
    G = dict(Rr=.34, Rf=.34, tw=.04, th=.035, sa=70, sl=.5, ha=70, hl=.15); G.update(k)
    ht = np.array(G["htop"], float); G["htop"] = ht; G["hbot"] = ht + dirv(-G["ha"]) * G["hl"]
    G["bb"] = np.array(G["bb"], float); return G

def wheels(m, G, nseg=30, nmin=5):
    wheel(m, G["ru"], G["Rr"], G["tw"], G["th"], nseg, nmin); wheel(m, G["fu"], G["Rf"], G.get("twf", G["tw"]), G.get("thf", G["th"]), nseg, nmin)

def fenders(m, G, col=BLACK):
    fender(m, G["fu"], G["Rf"], G["th"], G["tw"], -38, 70, col)
    fender(m, G["ru"], G["Rr"], G["th"], G["tw"], 48, -105, col)

def city(kid=False, rental=False):
    m = Mesh()
    if rental: G = geom(ru=-.47, fu=.47, Rr=.285, Rf=.285, tw=.052, th=.045, bb=(-.03, .255), sa=70, sl=.42, ha=70, htop=(.33, .75), hl=.17)
    else: G = geom(ru=-.55, fu=.55, bb=(-.06, .30), sa=68, sl=.50, htop=(.38, .80), ha=68, hl=.16)
    wheels(m, G); fenders(m, G, (.05, .05, .055) if not rental else (.12, .12, .13)); fork(m, G)
    st, sd = frame(m, G, "step", dt_r=.045 if rental else .021, dt_sq=.42 if rental else 1.0, K=1.0 if rental else 1.15)
    saddle(m, G, st, sd, post=.22 if rental else .13, kind="city", col=LEATHER if not rental else (.04, .04, .045))
    crank(m, G, guard=True); bars(m, G, "swept", .56 if rental else .60, S=(.30, .96) if rental else (.33, .96)); rack(m, G, h=.66, front=-.17, rear=-.46) if rental else rack(m, G)
    if rental: basket(m, G, .36, .62, .66, .86, .15, .17)
    elif not kid: basket(m, G); lamp_front(m, G)
    else: kidseat(m, G, (.10, .13, .18)); lamp_front(m, G)
    kickstand(m, G); return m, G

def trekking():
    m = Mesh(); G = geom(ru=-.56, fu=.56, tw=.04, th=.035, bb=(-.06, .30), sa=72, sl=.56, htop=(.40, .84), ha=71, hl=.17)
    wheels(m, G); fenders(m, G); fork(m, G); st, sd = frame(m, G, "diamond", dt_r=.021)
    saddle(m, G, st, sd, post=.12, kind="city", col=(.04, .04, .045)); crank(m, G, cassette=True)
    bars(m, G, "flat", .62, S=(.37, .945)); rack(m, G, h=.735); panniers(m, G, (.04, .07, .14)); lamp_front(m, G, h=.88)
    kickstand(m, G); return m, G

def road():
    m = Mesh(); G = geom(ru=-.43, fu=.55, Rr=.335, Rf=.335, tw=.025, th=.025, bb=(-.03, .27), sa=73, sl=.55, htop=(.41, .78), ha=73, hl=.13)
    wheels(m, G); fork(m, G); st, sd = frame(m, G, "diamond", tt_r=.0135, dt_r=.0175, dt_sq=1.0, K=1.0)
    saddle(m, G, st, sd, post=.11, kind="road", col=(.03, .03, .035)); crank(m, G, ring_r=.10, cassette=True, ang=-12)
    bars(m, G, "drop", .42, S=(.47, .80)); return m, G

def mtb():
    m = Mesh(); G = geom(ru=-.435, fu=.575, Rr=.335, Rf=.335, tw=.055, th=.05, bb=(-.05, .32), sa=71, sl=.46, htop=(.42, .84), ha=68, hl=.12)
    wheels(m, G, 30, 6); fork(m, G, susp=True); st, sd = frame(m, G, "diamond", tt_from=.97, dt_r=.025, tt_r=.018, dt_sq=.85)
    saddle(m, G, st, sd, post=.09, kind="mtb", col=(.03, .03, .035)); crank(m, G, cassette=True)
    bars(m, G, "flat", .70, S=(.375, .90))
    for u, R, x in ((G["ru"], G["Rr"], -.045), (G["fu"], G["Rf"], -.045)): disc(m, P(u, R, x), .08, 12, (.5, .5, .52))
    return m, G

def ebike():
    m = Mesh(); G = geom(ru=-.56, fu=.57, tw=.045, th=.04, bb=(-.06, .30), sa=70, sl=.52, htop=(.40, .83), ha=69, hl=.17)
    wheels(m, G); fenders(m, G); fork(m, G); st, sd = frame(m, G, "diamond", tt_from=.82, dt_r=.03, dt_sq=.75)
    ht, hb, bb = G["htop"], G["hbot"], G["bb"]
    a = bb + (hb + (ht - hb) * .12 - bb) * .28; b = bb + (hb + (ht - hb) * .12 - bb) * .78
    obox(m, uh(a, 0), uh(b, 0), .075, .085, (.07, .075, .08), up=(0, 1., 0))                          # battery on the down tube
    cuboid(m, P(bb[0] + .01, bb[1] + .005, 0), .075, .06, .062, (.12, .12, .13))                      # mid motor
    saddle(m, G, st, sd, post=.12, kind="city", col=(.04, .04, .045)); crank(m, G, cassette=True)
    bars(m, G, "flat", .62, S=(.36, .955)); rack(m, G); lamp_front(m, G, h=.90); cuboid(m, P(-.40, .76, 0), .06, .02, .045, (.1, .1, .11))
    kickstand(m, G); return m, G

def cargo():
    m = Mesh(); G = geom(ru=-.95, fu=1.20, Rr=.335, Rf=.255, tw=.045, th=.04, twf=.05, thf=.045, bb=(-.50, .28), sa=70, sl=.52, htop=(1.05, .63), ha=78, hl=.24)
    wheels(m, G); fender(m, G["ru"], G["Rr"], G["th"], G["tw"], 48, -105, BLACK); fork(m, G)
    pk = dict(col=(1, 1, 1), paint=1.0); bb = G["bb"]; ht, hb = G["htop"], G["hbot"]
    tube(m, uh(ht), uh(hb), .022, .022, 6, **pk)
    tube(m, uh(bb), P(1.05, .42, 0), .026, .024, 6, sq=.8, **pk); tube(m, uh(bb + np.array([0, .01])), P(1.05, .55, 0), .016, .016, 5, **pk)
    sd = np.array([-np.cos(np.deg2rad(70)), np.sin(np.deg2rad(70))]); st = bb + sd * .52
    tube(m, uh(bb), uh(st), .0165, .0165, 5, **pk)
    for s in (-1, 1):
        axl = P(G["ru"], G["Rr"], s * .062)
        tube(m, uh(bb + sd * .47, s * .028), axl, .0095, .0095, 5, **pk); tube(m, uh(bb, s * .03), axl, .012, .01, 5, **pk)
    tube(m, uh(bb, -.05), uh(bb, .05), .019, .019, 6, col=STEEL)
    saddle(m, G, st, sd, post=.15, kind="city", col=(.04, .04, .045)); crank(m, G, cassette=True)
    tube(m, P(-.22, .31, 0), P(-.22, .97, 0), .014, .014, 5, CHROME)                                    # steering column
    su, sh = -.19, .99
    for s in (-1, 1):
        ptube(m, [P(su, sh, 0), P(su - .005, sh + .01, s * .12), P(su - .07, sh + .018, s * .28), P(su - .15, sh - .005, s * .32)], .0105, 5, CHROME, cap=False)
        tube(m, P(su - .085, sh + .012, s * .29), P(su - .15, sh - .005, s * .32), .0165, .0165, 6, GRIP, cap=True)
    tube(m, P(su, sh, 0), P(-.22, .97, 0), .0115, .0115, 5, CHROME)
    tube(m, P(-.22, .33, 0), P(1.05, .45, 0), .007, .007, 4, STEEL)                                      # steering rod
    ply = lin(0xb08a55); cuboid(m, P(.50, .365, 0), .40, .008, .245, ply)
    for s in (-1, 1): cuboid(m, P(.50, .515, s * .252), .40, .15, .008, ply)
    for s in (-1, 1): cuboid(m, P(.50 + s * .395, .515, 0), .008, .15, .252, ply)
    fender(m, G["fu"], G["Rf"], G["thf"], G["twf"], -30, 80, BLACK)
    kickstand(m, G); return m, G

def rack_only():
    m = Mesh(); zn = lin(0xb9bcbf); h = .80; hw = .30      # Zuercher Anlehnbuegel: inverted U, 0.60 wide, 0.80 high, 2 posts in ground plate
    pts = [P(0, 0, -hw), P(0, h - .15, -hw), P(0, h - .06, -hw + .03), P(0, h, -hw + .12), P(0, h, hw - .12), P(0, h - .06, hw - .03), P(0, h - .15, hw), P(0, 0, hw)]
    ptube(m, pts, .0165, 6, zn, cap=True)
    for s in (-1, 1): cuboid(m, P(0, .006, s * hw), .06, .006, .06, zn)
    return m, dict()

TYPES = dict(city=lambda: city(), trekking=trekking, road=road, mtb=mtb, ebike=ebike, cargo=cargo, kidseat=lambda: city(kid=True), rental=lambda: city(rental=True))

def finalize(m, G, lean=0.0):
    """Centre between the wheel contacts; optional lean about the ground contact line (rolls to the left)."""
    if "ru" in G:
        sh = (G["ru"] + G["fu"]) / 2; m.transform(lambda p: p + np.array([0, 0, sh]), lambda n: n)
    if lean:
        a = np.deg2rad(lean); c, s = np.cos(a), np.sin(a)   # rotate about z axis (the forward axis): x,y -> tilt
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]); m.transform(lambda p: p @ R.T, lambda n: n @ R.T)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); png = make_atlas(); man = []
    for name in (sys.argv[1:] or list(TYPES) + ["rack"]):
        for lean in ((0, 10) if name != "rack" else (0,)):
            m, G = (rack_only() if name == "rack" else TYPES[name]())
            if lean and "ru" in G: lean_stand(m, G, lean)
            finalize(m, G, lean)
            fn = f"{name}{'_lean' if lean else ''}.glb"; tris, size, Pv = write_glb(m, os.path.join(OUT, fn), png)
            ln = float(Pv[:, 2].max() - Pv[:, 2].min())
            ent = dict(type=name + ("_lean" if lean else ""), file=fn, length=round(ln, 2), tris=int(tris))
            if "ru" in G:   # axle / bottom-bracket positions in glTF space (y, z) so the web can spin wheels and cranks (split by position)
                sh = (G["ru"] + G["fu"]) / 2
                sd_ = _REC["saddle"]
                ent["rig"] = dict(saddle=[float(sd_[1]), float(-(sd_[0] - sh))], rear=[G["Rr"], float(-(G["ru"] - sh))], front=[G["Rf"], float(-(G["fu"] - sh))], bb=[float(G["bb"][1]), float(-(G["bb"][0] - sh))])
            man.append(ent)
            print(fn, tris, "tris", size // 1024, "KB", "len", round(ln, 2))
    if len(sys.argv) == 1: json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
