"""3D trim for v3 Altbau facades: eave cornice (Dachgesims) and bay windows (Erker). Few triangles, merged into the tile mesh.

Both use the wall frame returned by facade._wall: (u0, u1, t, nh, d, width, su, zb, hv) with
point = u * t + d * nh (t = tangent, nh = outward normal)."""
import numpy as np

from styles import LAYER, h32


def _quad(mesh, p, nrm, col, uv=None, layer=None):
    p = np.asarray(p, np.float32)
    uv = np.zeros((4, 2)) if uv is None else np.asarray(uv)
    tri = np.array([[0, 1, 2], [0, 2, 3]], np.uint32)
    if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), nrm) < 0:
        tri = tri[:, ::-1].copy()
    mesh.add(p, tri, np.asarray(nrm, float), col, uv=uv, layer=LAYER["white"] if layer is None else layer)


def _pt(frame, u, off, z):
    u0, u1, t, nh, d = frame[:5]
    xy = u * t + (d + off) * nh
    return [xy[0], xy[1], z]


def cornice(mesh, frame, z_eave, col, proj=0.32, hgt=0.42):
    """Projecting eave band: front face, soffit and top, a little wider than the wall (closes corners)."""
    u0, u1, t, nh = frame[0] - 0.18, frame[1] + 0.18, frame[2], frame[3]
    zt, zb = z_eave + 0.08, z_eave - hgt
    nrm = np.array([nh[0], nh[1], 0.0])
    f = (u0, u1)
    _quad(mesh, [_pt(frame, f[0], proj, zb), _pt(frame, f[1], proj, zb), _pt(frame, f[1], proj, zt), _pt(frame, f[0], proj, zt)], nrm, col)
    _quad(mesh, [_pt(frame, f[0], 0, zb), _pt(frame, f[1], 0, zb), _pt(frame, f[1], proj, zb), _pt(frame, f[0], proj, zb)], [0, 0, -1], tuple(np.array(col) * .6))
    _quad(mesh, [_pt(frame, f[0], proj, zt), _pt(frame, f[1], proj, zt), _pt(frame, f[1], 0, zt), _pt(frame, f[0], 0, zt)], [0, 0, 1], col)


def erker(mesh, frame, z_lo, z_hi, layer, tint, seed, w=2.7, depth=0.75):
    """One bay window: front (same facade texture, windows line up with the wall behind), two angled sides, flat roof + belly."""
    u0, u1, t, nh, d, width, su, zb, hv = frame[:9]  # seg[9] = shop span (storefronts)
    if width < w + 3.0:
        return False
    uc = u0 + width * (0.5 if width < 10 else 0.32 + 0.36 * ((seed >> 3) % 2)) 
    a, b = uc - w / 2, uc + w / 2
    nrm = np.array([nh[0], nh[1], 0.0])
    uvf = lambda u, z: [(u - u0) * su, -(z - zb) / hv]
    P = [(a, z_lo), (b, z_lo), (b, z_hi), (a, z_hi)]
    _quad(mesh, [_pt(frame, u, depth, z) for u, z in P], nrm, tint, [uvf(u, z) for u, z in P], layer)
    for u, sgn in ((a, -1), (b, 1)):  # sides: solid, same plaster
        sn = np.array([t[0] * sgn, t[1] * sgn, 0.0])
        q = [_pt(frame, u, 0, z_lo), _pt(frame, u, depth, z_lo), _pt(frame, u, depth, z_hi), _pt(frame, u, 0, z_hi)]
        if sgn < 0:
            q = q[::-1]
        _quad(mesh, q, sn, tint, [uvf(u, z) for u, z in P], layer)
    _quad(mesh, [_pt(frame, a, 0, z_hi), _pt(frame, a, depth, z_hi), _pt(frame, b, depth, z_hi), _pt(frame, b, 0, z_hi)][::-1], [0, 0, 1], tuple(np.array(tint) * .8))
    _quad(mesh, [_pt(frame, a, 0, z_lo), _pt(frame, b, 0, z_lo), _pt(frame, b, depth, z_lo), _pt(frame, a, depth, z_lo)], [0, 0, -1], tuple(np.array(tint) * .5))
    return True


def band(mesh, frame, z, col, proj=0.1, hgt=0.22):
    """Thin projecting storey band (Stockwerkgesims) across the wall: front + top face (4 tris)."""
    u0, u1, nh = frame[0], frame[1], frame[3]
    nrm = np.array([nh[0], nh[1], 0.0])
    zb, zt = z - hgt / 2, z + hgt / 2
    _quad(mesh, [_pt(frame, u0, proj, zb), _pt(frame, u1, proj, zb), _pt(frame, u1, proj, zt), _pt(frame, u0, proj, zt)], nrm, col)
    _quad(mesh, [_pt(frame, u0, proj, zt), _pt(frame, u1, proj, zt), _pt(frame, u1, 0, zt), _pt(frame, u0, 0, zt)], [0, 0, 1], col)


def dormers(mesh, pts, n, tint, layer, roof_col, pitch, street_ok=lambda x, y: True, max_n=6):
    """Dormer windows (Gauben) on one pitched roof plane (pts = plane polygon, n = unit normal): front wall with a window bay
    of the facade layer, two triangular cheeks, flat top. ~10 tris each; none when the plane is steep/small or faces away from the street."""
    from shapely.geometry import Point, Polygon
    nz = float(n[2])
    if nz < 0.25 or nz > 0.9:
        return 0
    o = np.array([n[0], n[1]]) / max(np.hypot(n[0], n[1]), 1e-6)       # horizontal outward direction
    th = np.array([-o[1], o[0]])
    u = pts[:, :2] @ th
    w = pts[:, :2] @ o
    poly = Polygon(np.column_stack([u, w])).buffer(0)
    if poly.is_empty or poly.area < 12:
        return 0
    inner = poly.buffer(-0.9)
    if inner.is_empty:
        return 0
    cnt = min(max_n, int((u.max() - u.min() - 1.0) // (2.0 * pitch)))
    if cnt < 1:
        return 0
    tanb = np.hypot(n[0], n[1]) / nz
    hf, wd = 1.25, 1.1
    z_of = lambda x, y: float(pts[0, 2] - (n[0] * (x - pts[0, 0]) + n[1] * (y - pts[0, 1])) / nz)
    placed = 0
    um = (u.min() + u.max()) / 2
    span = cnt * 2.0 * pitch
    for i in range(cnt):
        uc = um - span / 2 + (i + 0.5) * 2.0 * pitch
        wlo, whi = w.min(), w.max()
        wc = wlo + (whi - wlo) * 0.38
        if not inner.contains(Point(uc, wc)) or not inner.contains(Point(uc - wd, wc)) or not inner.contains(Point(uc + wd, wc)):
            continue
        bx, by = uc * th + wc * o
        if not street_ok(bx + o[0] * 8, by + o[1] * 8):
            continue
        zb = z_of(bx, by)
        zt = zb + hf
        dep = hf / tanb
        P = lambda du, dw, z: [bx + du * th[0] + dw * o[0], by + du * th[1] + dw * o[1], z]
        nrm = np.array([o[0], o[1], 0.0])
        a, b = -wd / 2, wd / 2
        _quad(mesh, [P(a, 0, zb), P(b, 0, zb), P(b, 0, zt), P(a, 0, zt)], nrm, tint, [[0.0, -0.5], [0.25, -0.5], [0.25, -0.25], [0.0, -0.25]][::-1] if False else [[0.0, -0.25], [0.25, -0.25], [0.25, -0.5], [0.0, -0.5]], layer)
        for du, sg in ((a, -1), (b, 1)):
            q = np.array([P(du, 0, zb), P(du, 0, zt), P(du, -dep, zt)], np.float32)
            sn = np.array([th[0] * sg, th[1] * sg, 0.0])
            tr = np.array([[0, 1, 2]], np.uint32)
            if np.dot(np.cross(q[1] - q[0], q[2] - q[0]), sn) < 0:
                tr = tr[:, ::-1].copy()
            mesh.add(q, tr, sn, roof_col, uv=np.zeros((3, 2)), layer=LAYER["white"])
        _quad(mesh, [P(a, 0, zt + .08), P(b, 0, zt + .08), P(b, -dep, zt + .08), P(a, -dep, zt + .08)], [0, 0, 1], roof_col)
        _quad(mesh, [P(a - .05, .12, zt), P(b + .05, .12, zt), P(b + .05, .12, zt + .1), P(a - .05, .12, zt + .1)], nrm, tuple(min(255, c * 1.05) for c in tint))
        placed += 1
    return placed
