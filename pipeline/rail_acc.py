"""Batched quad accumulator for the railway meshes (positions in local metres, z up; arrays() in three.js axes)."""
import math

import numpy as np

from styles import LAYER


class Acc:
    """Batched quad accumulator (positions in local metres, z up); arrays() in three.js axes like mesh.Mesh."""

    def __init__(self):
        self.P, self.N, self.C, self.U, self.L = [], [], [], [], []

    def quads(self, P, hint, color, layer=None, uv=None):
        """P: (n,4,3) quads, hint: expected outward direction (3 or (n,3)); flips winding where needed."""
        P = np.asarray(P, np.float64).reshape(-1, 4, 3)
        if len(P) == 0:
            return
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        n += np.cross(P[:, 2] - P[:, 0], P[:, 3] - P[:, 0])
        h = np.broadcast_to(np.asarray(hint, np.float64), n.shape)
        flip = (n * h).sum(1) < 0
        P = np.where(flip[:, None, None], P[:, ::-1], P)
        n = np.where(flip[:, None], -n, n)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        c = np.asarray(color) / 255
        lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        col = np.append(np.round(lin * 255), 255)
        if uv is not None:
            uv = np.asarray(uv, np.float64).reshape(-1, 4, 2)
            uv = np.where(flip[:, None, None], uv[:, ::-1], uv)
        self.P.append(P.astype(np.float32))
        self.N.append(np.repeat(n[:, None], 4, 1).astype(np.float32))
        self.C.append(np.broadcast_to(col, (len(P), 4, 4)))
        self.U.append((P[:, :, :2] / 2.0).astype(np.float32) if uv is None else np.asarray(uv, np.float32).reshape(-1, 4, 2))
        self.L.append(np.full((len(P), 4), LAYER[layer or "white"], np.float32))

    def box(self, x0, x1, y0, y1, z0, z1, color, rot=0.0, cx=0.0, cy=0.0):
        """Axis box (local coords around origin) rotated by rot about z and moved to (cx, cy); no bottom face."""
        c, s = math.cos(rot), math.sin(rot)
        def p(x, y, z): return (cx + x * c - y * s, cy + x * s + y * c, z)
        a, b, d, e = p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0)
        a2, b2, d2, e2 = p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)
        ctr = np.array([(a[0] + d[0]) / 2, (a[1] + d[1]) / 2, (z0 + z1) / 2])
        faces = [[a, b, b2, a2], [b, d, d2, b2], [d, e, e2, d2], [e, a, a2, e2], [a2, b2, d2, e2]]
        for f in faces:
            f = np.array(f)
            self.quads(f, f.mean(0) - ctr, color)

    def arrays(self):
        if not self.P:
            return None
        P, N = np.concatenate(self.P).reshape(-1, 3), np.concatenate(self.N).reshape(-1, 3)
        n = len(P) // 4
        base = (np.arange(n) * 4)[:, None]
        idx = np.concatenate([base + [0, 1, 2], base + [0, 2, 3]], 1).reshape(-1, 3)
        sw = lambda a: np.column_stack([a[:, 0], a[:, 2], -a[:, 1]])
        uv = np.concatenate(self.U).reshape(-1, 2)
        uv = uv - np.floor(uv.min(0))
        return {"pos": sw(P), "nrm": sw(N), "col": np.concatenate(self.C).reshape(-1, 4), "idx": idx.astype(np.uint32),
                "uv": uv, "layer": np.concatenate(self.L).reshape(-1)}


class TrackAcc(Acc):
    """Track-bed mesh: samples the sleeper/ballast texture (u < 0.8) or the plain white column (u = 0.9) for flat colours."""
    FLAT = (0.9, 0.5)

    def quads(self, P, hint, color, layer=None, uv=None):
        if uv is None:
            n = np.asarray(P, np.float64).reshape(-1, 4, 3).shape[0]
            uv = np.broadcast_to(np.asarray(self.FLAT), (n, 4, 2))
        super().quads(P, hint, color, layer, uv)
