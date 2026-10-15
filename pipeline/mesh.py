"""Geometry helpers: mesh accumulator, 3D polygon triangulation, draping 2D shapes onto the height grid."""
import mapbox_earcut as earcut
import numpy as np
from shapely.geometry import box


class Mesh:
    """Accumulates flat-shaded triangles. Input in local metres (x east, y north, z up)."""

    def __init__(self):
        self.p, self.n, self.c, self.i, self.uv, self.lay = [], [], [], [], [], []
        self.count = 0

    def add(self, pts, tris, normal, color, uv=None, layer=0):
        """uv: Nx2 in texture repeats; default = world-planar xy / 4 m. layer: texture array index."""
        k = len(pts)
        self.p.append(pts)
        self.uv.append(np.asarray(uv, np.float32) if uv is not None else (pts[:, :2] / 4.0).astype(np.float32))
        self.lay.append(np.full(k, layer, np.float32))
        self.n.append(np.tile(normal, (k, 1)))
        lin = np.where((c := np.asarray(color) / 255) <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        self.c.append(np.tile(np.append(np.round(lin * 255), 255), (k, 1)))  # glTF vertex colours are linear
        self.i.append(tris + self.count)
        self.count += k

    def arrays(self):
        """Return arrays in three.js axes (x, z, -y)."""
        if not self.p:
            return None
        p, n = np.concatenate(self.p), np.concatenate(self.n)
        swap = lambda a: np.column_stack([a[:, 0], a[:, 2], -a[:, 1]])
        uv = np.concatenate(self.uv)
        uv -= np.floor(uv.min(0))  # integer shift keeps repeats identical but keeps values small (quantization)
        return {"pos": swap(p), "nrm": swap(n), "col": np.concatenate(self.c), "idx": np.concatenate(self.i).reshape(-1, 3),
                "uv": uv, "layer": np.concatenate(self.lay)}


def poly_normal(a):
    """Newell normal of a 3D polygon."""
    n = np.zeros(3)
    b = np.roll(a, -1, 0)
    n[0] = ((a[:, 1] - b[:, 1]) * (a[:, 2] + b[:, 2])).sum()
    n[1] = ((a[:, 2] - b[:, 2]) * (a[:, 0] + b[:, 0])).sum()
    n[2] = ((a[:, 0] - b[:, 0]) * (a[:, 1] + b[:, 1])).sum()
    ln = np.linalg.norm(n)
    return n / ln if ln > 1e-9 else None


def tri3d(a):
    """Triangulate a planar 3D ring (closing point may repeat). Returns (pts, tris, normal) or None."""
    if np.allclose(a[0], a[-1]):
        a = a[:-1]
    if len(a) < 3:
        return None
    n = poly_normal(a)
    if n is None:
        return None
    drop = int(np.argmax(np.abs(n)))
    uv = np.delete(a, drop, axis=1).astype(np.float64)
    t = earcut.triangulate_float64(uv, np.array([len(uv)], dtype=np.uint32))
    if len(t) == 0:
        return None
    t = t.reshape(-1, 3)
    # earcut winding is arbitrary relative to the 3D normal: fix it per triangle set
    v = a[t]
    tn = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]).sum(0)
    if np.dot(tn, n) < 0:
        t = t[:, ::-1]
    return a.astype(np.float32), t.astype(np.uint32), n


class Heights:
    """Regular height grid in local metres; bilinear sampling."""

    def __init__(self, x0, y0, step, z):
        self.x0, self.y0, self.step, self.z = x0, y0, step, z

    def at(self, x, y):
        fx = np.clip((np.asarray(x) - self.x0) / self.step, 0, self.z.shape[1] - 1.001)
        fy = np.clip((np.asarray(y) - self.y0) / self.step, 0, self.z.shape[0] - 1.001)
        ix, iy = fx.astype(int), fy.astype(int)
        tx, ty = fx - ix, fy - iy
        z = self.z
        return (z[iy, ix] * (1 - tx) * (1 - ty) + z[iy, ix + 1] * tx * (1 - ty)
                + z[iy + 1, ix] * (1 - tx) * ty + z[iy + 1, ix + 1] * tx * ty)


def drape(mesh, geom, heights, lift, color, cell=16.0, layer=0, uv_scale=4.0):
    """Triangulate a 2D (Multi)Polygon, split into cells so it follows the terrain, add to mesh."""
    if geom.is_empty:
        return
    x0, y0, x1, y1 = geom.bounds
    for cx in np.arange(np.floor(x0 / cell) * cell, x1, cell):
        for cy in np.arange(np.floor(y0 / cell) * cell, y1, cell):
            part = geom.intersection(box(cx, cy, cx + cell, cy + cell))
            for poly in getattr(part, "geoms", [part]):
                if poly.geom_type != "Polygon" or poly.area < 0.01:
                    continue
                rings = [np.asarray(poly.exterior.coords)[:-1]] + [np.asarray(r.coords)[:-1] for r in poly.interiors]
                ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
                xy = np.concatenate(rings)
                t = earcut.triangulate_float64(xy, ends).reshape(-1, 3)
                if len(t) == 0:
                    continue
                v = xy[t]
                cr = (v[:, 1, 0] - v[:, 0, 0]) * (v[:, 2, 1] - v[:, 0, 1]) - (v[:, 1, 1] - v[:, 0, 1]) * (v[:, 2, 0] - v[:, 0, 0])
                t[cr < 0] = t[cr < 0][:, ::-1]
                z = heights.at(xy[:, 0], xy[:, 1]) + lift
                mesh.add(np.column_stack([xy, z]).astype(np.float32), t.astype(np.uint32), np.array([0, 0, 1.0]), color,
                         uv=xy / uv_scale, layer=layer)

