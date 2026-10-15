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
    u0, u1, t, nh, d, width, su, zb, hv = frame
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
