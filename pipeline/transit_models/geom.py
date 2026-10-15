"""Pure-python geometry for VBZ vehicle modules. Coordinates: three.js (x right, y up, front = -z), metres."""
import math

def lin(c):
    f = lambda v: (v/12.92) if v <= 0.04045 else ((v+0.055)/1.055)**2.4
    return tuple(f(v/255) for v in c)

BLUE = lin((31, 109, 182)); WHITE = lin((242, 240, 234)); CBLUE = lin((58, 143, 214)); GREY = lin((178, 183, 188))
GLASS = lin((58, 76, 98)); DGLASS = lin((96, 124, 150)); DARK = lin((38, 38, 42))
LIGHT = lin((255, 250, 215)); DOORW = lin((205, 212, 220)); RED = lin((200, 30, 30))

class Mesh:
    def __init__(s): s.f = []   # (pts, color)
    def quad(s, pts, col, ref=None):
        if ref is not None:
            c = [sum(p[i] for p in pts)/len(pts) for i in range(3)]
            a = [pts[1][i]-pts[0][i] for i in range(3)]; b = [pts[2][i]-pts[0][i] for i in range(3)]
            n = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
            if sum(n[i]*(c[i]-ref[i]) for i in range(3)) < 0: pts = pts[::-1]
        s.f.append((list(pts), col))
    def box(s, x0, x1, y0, y1, z0, z1, col):
        r = ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2)
        P = lambda x, y, z: (x, y, z)
        for q in ([P(x0,y0,z0),P(x1,y0,z0),P(x1,y1,z0),P(x0,y1,z0)], [P(x0,y0,z1),P(x1,y0,z1),P(x1,y1,z1),P(x0,y1,z1)],
                  [P(x0,y0,z0),P(x0,y0,z1),P(x0,y1,z1),P(x0,y1,z0)], [P(x1,y0,z0),P(x1,y0,z1),P(x1,y1,z1),P(x1,y1,z0)],
                  [P(x0,y1,z0),P(x1,y1,z0),P(x1,y1,z1),P(x0,y1,z1)], [P(x0,y0,z0),P(x1,y0,z0),P(x1,y0,z1),P(x0,y0,z1)]):
            s.quad(q, col, r)
    def beam(s, p0, p1, t, col):
        d = [p1[i]-p0[i] for i in range(3)]; l = math.sqrt(sum(v*v for v in d)); d = [v/l for v in d]
        ax = (1, 0, 0) if abs(d[0]) < .9 else (0, 0, 1)
        u = [d[1]*ax[2]-d[2]*ax[1], d[2]*ax[0]-d[0]*ax[2], d[0]*ax[1]-d[1]*ax[0]]
        ul = math.sqrt(sum(v*v for v in u)); u = [v/ul*t for v in u]
        v = [(d[1]*u[2]-d[2]*u[1]), (d[2]*u[0]-d[0]*u[2]), (d[0]*u[1]-d[1]*u[0])]; vl = math.sqrt(sum(a*a for a in v)); v = [a/vl*t for a in v]
        C = lambda p, a, b: tuple(p[i]+a*u[i]+b*v[i] for i in range(3))
        r = tuple((p0[i]+p1[i])/2 for i in range(3))
        for p in (p0, p1): s.quad([C(p,-1,-1), C(p,1,-1), C(p,1,1), C(p,-1,1)], col, r)
        for a, b in (((-1,-1),(1,-1)), ((1,-1),(1,1)), ((1,1),(-1,1)), ((-1,1),(-1,-1))):
            s.quad([C(p0,*a), C(p0,*b), C(p1,*b), C(p1,*a)], col, r)
    def wheel(s, x0, x1, y, z, r, col, n=8):
        for i in range(n):
            a0, a1 = 2*math.pi*i/n, 2*math.pi*(i+1)/n
            P = lambda x, a: (x, y+r*math.sin(a), z+r*math.cos(a))
            s.quad([P(x0,a0), P(x1,a0), P(x1,a1), P(x0,a1)], col, (0.0, y, z) if False else ((x0+x1)/2, y, z))
        for x in (x0, x1):
            pts = [(x, y+r*math.sin(2*math.pi*i/n), z+r*math.cos(2*math.pi*i/n)) for i in range(n)]
            s.quad(pts, DARK if col != DARK else GREY, ((x0+x1)/2, y, z))
    def poly(s, pts, col, ref): s.quad(pts, col, ref)
    def tris(s): return sum(len(p)-2 for p, _ in s.f)

def layout(z0, z1, doors, dw=1.3, pw=0.34, maxw=1.6):
    """segments (za, zb, type) between z0<z1; doors = door centres."""
    segs, z = [], z0
    for c in sorted(doors):
        a, b = c-dw/2, c+dw/2
        segs += _win(z, a-pw, maxw, pw) + [(a-pw, a, 'p'), (a, b, 'd'), (b, b+pw, 'p')]; z = b+pw
    return segs + _win(z, z1, maxw, pw)

def _win(a, b, maxw, pw):
    L = b-a
    if L < 0.2: return [(a, b, 'p')] if L > 0.001 else []
    n = max(1, math.ceil((L+pw)/(maxw+pw))); w = (L-(n-1)*pw)/n; out = []; z = a
    for i in range(n):
        out.append((z, z+w, 'w')); z += w
        if i < n-1: out.append((z, z+pw, 'p')); z += pw
    return out

def profile(P):
    hx, y0, belt, wtop, ytop = P['hx'], P['y0'], P['belt'], P['wtop'], P['ytop']
    return [(hx-.05, y0), (hx, y0+.16), (hx, belt), (hx, wtop), (hx-.06, wtop+P['r1']), (hx-P['rx'], ytop-.1), (0, ytop)]

def strip_cols(P, t):
    roof = P['roof']
    return {'p': [P['blue'], P['blue'], P['pillar'], P['white'], roof, roof],
            'w': [P['blue'], P['blue'], GLASS, P['white'], roof, roof],
            'd': [P['blue'], P['blue'], DGLASS, P['white'], roof, roof],
            'n': [P['blue'], P['blue'], GLASS, P.get('nose_top', P['white']), P.get('nose_roof', roof), P.get('nose_roof', roof)]}[t]

def ring(P, zc, sx=1.0, back=0.0, drop=0.0):
    pr = profile(P); ymin, ymax = P['belt'], P['ytop']; out = []
    for x, y in pr:
        fr = max(0.0, min(1.0, (y-ymin)/(ymax-ymin)))
        out.append((x*sx, y - drop*fr, zc + back*fr))
    return out

def mirror(pr): return [(-x, y, z) for x, y, z in pr]

def loft(m, ra, rb, cols, ref):
    """side/roof quads between two half-rings (right) and mirrored (left)."""
    for A, B in ((ra, rb), (mirror(ra), mirror(rb))):
        for i in range(len(A)-1):
            m.quad([A[i], B[i], B[i+1], A[i+1]], cols[i], ref)

def cap(m, r, cols, ref, glass=None, frame=WHITE):
    L = mirror(r)
    for i in range(len(r)-1):
        if glass and i == 2:
            pt = lambda p, u: (p[0]*u, p[1], p[2])
            for a, b, c in ((1, glass, frame), (glass, -glass, cols[i]), (-glass, -1, frame)):
                m.quad([pt(r[i], a), pt(r[i], b), pt(r[i+1], b), pt(r[i+1], a)], c, ref)
        else:
            m.quad([r[i], L[i], L[i+1], r[i+1]], cols[i], ref)

def body(P, L, sides, nose=None, tail=None, bogies=(), wheels_r=0.34, extra=None):
    """Build module of length L centred at origin. nose: front (-z) cab; tail: rear cab. sides: {'r':[doors], 'l':[doors]}."""
    m = Mesh(); h = L/2; ref = (0, P['ytop']/2, 0); disp = []
    zf = -h; zb = h
    # ends
    gap = 0.12
    if nose:
        ringsN = [(0.0, nose['sx'][0], nose['back'][0], nose['drop'][0])] + [(d, s, b, dr) for d, s, b, dr in zip(nose['dz'][1:], nose['sx'][1:], nose['back'][1:], nose['drop'][1:])]
        rs = [ring(P, zf+d, sx, back, drop) for d, sx, back, drop in ringsN]
        cap(m, rs[0], strip_cols(P, 'n'), ref, glass=nose.get('glass'), frame=P.get('frame', P.get('nose_top', P['white'])))
        for a, b in zip(rs, rs[1:]): loft(m, a, b, strip_cols(P, 'n'), ref)
        z_start = zf+nose['dz'][-1]
        # front lights + display on cap
        r0 = rs[0]
        def on_cap(i, x0, x1, v0, v1, off):
            A, B = r0[i], r0[i+1]
            lerp = lambda a, b, t: tuple(a[k]+(b[k]-a[k])*t for k in range(3))
            pts = []
            for x, v in ((x0, v0), (x1, v0), (x1, v1), (x0, v1)):
                p = lerp(A, B, v); pts.append((x, p[1], p[2]-off))
            return pts
        if nose.get('lights'):
            for sx_ in (-1, 1):
                m.quad(on_cap(1, sx_*nose['lights'][1]-.14, sx_*nose['lights'][1]+.14, .3, .7, .012), LIGHT, ref)
        if nose.get('red'):
            for sx_ in (-1, 1):
                m.quad(on_cap(0, sx_*nose['red']-.07, sx_*nose['red']+.07, .3, .7, .012), RED, ref)
        di = nose['display']; dpts = on_cap(di[0], -di[1], di[1], di[2], di[3], .015)
        disp = dpts
    else:
        z_start = zf+gap
        e = ring(P, zf, 0.93); i0 = ring(P, zf+gap)
        loft(m, e, i0, [DARK]*6, ref); cap(m, e, [DARK]*6, ref)
    if tail:
        zt = zb-tail['dz'][-1]
        rs = [ring(P, zb-d, sx, -back, drop) for d, sx, back, drop in zip(tail['dz'], tail['sx'], tail['back'], tail['drop'])]
        cap(m, rs[0], strip_cols(P, 'n'), ref)
        for a, b in zip(rs, rs[1:]): loft(m, a, b, strip_cols(P, 'n'), ref)
        z_end = zt
        z_end = zt
    else:
        z_end = zb-gap
        e = ring(P, zb, 0.93); i0 = ring(P, zb-gap)
        loft(m, i0, e, [DARK]*6, ref); cap(m, e, [DARK]*6, ref)
    # body span
    cuts = {'r': sides.get('r', []), 'l': sides.get('l', [])}
    rr = ring(P, 0)
    segs = {s: layout(z_start, z_end, cuts[s]) for s in 'rl'}
    for s, sg in segs.items():
        for za, zb_, t in sg:
            A = [(x, y, za) for x, y, _ in rr]; B = [(x, y, zb_) for x, y, _ in rr]
            if s == 'l': A, B = mirror(A), mirror(B)
            cols = strip_cols(P, t)
            for i in range(0, 4):  # side strips only
                m.quad([A[i], B[i], B[i+1], A[i+1]], cols[i], ref)
    # roof strips common (4,5) both sides
    A = [(x, y, z_start) for x, y, _ in rr]; B = [(x, y, z_end) for x, y, _ in rr]
    for S in (1, -1):
        a = [(S*x, y, z) for x, y, z in A]; b = [(S*x, y, z) for x, y, z in B]
        for i in (4, 5): m.quad([a[i], b[i], b[i+1], a[i+1]], P['roof'], ref)
    # underside
    hx = P['hx']-.05; y0 = P['y0']
    m.quad([(-hx, y0, zf), (hx, y0, zf), (hx, y0, zb), (-hx, y0, zb)], DARK, ref)
    # bogies
    for bz in bogies:
        m.box(-.78, .78, .06, y0+.12, bz-1.2, bz+1.2, DARK)
        for az in (-.9, .9):
            m.wheel(-.78, -.62, wheels_r, bz+az, wheels_r, GREY); m.wheel(.62, .78, wheels_r, bz+az, wheels_r, GREY)
    if extra: extra(m, P, L)
    return m, disp

def roof_boxes(m, P, L, zs, w=1.0, hgt=.22, ln=1.6):
    for z in zs: m.box(-w/2, w/2, P['ytop']-.02, P['ytop']+hgt, z-ln/2, z+ln/2, P['roofbox'])

def pantograph(m, P, z0, wire=5.45):
    y = P['ytop']
    for sx in (-.35, .35): m.box(sx-.05, sx+.05, y-.02, y+.1, z0-.5, z0+.5, DARK)
    knee = (0, y+1.5, z0-1.2); top = (0, wire-.05, z0+.15)
    m.beam((0, y+.1, z0+.6), knee, .035, DARK); m.beam(knee, top, .03, DARK); m.beam((0, y+.1, z0-.4), (0, y+1.4, z0-1.15), .02, DARK)
    m.box(-.6, .6, wire-.08, wire, z0+.15-.18, z0+.15+.18, GREY)

def trolley_poles(m, z_base, L_half):
    for sx in (-.32, .32):
        m.beam((sx, 3.1, z_base), (sx*.95, 5.55, z_base+4.8), .03, DARK)
        m.box(sx*.95-.06, sx*.95+.06, 5.5, 5.62, z_base+4.8-.1, z_base+4.8+.1, GREY)
        m.box(sx-.08, sx+.08, 3.05, 3.2, z_base-.2, z_base+.2, DARK)
