"""CMU mocap BVH -> cycle-cut, in-place, yaw-aligned loop clips (npz) for pipeline/blender/mocap_retarget.py.

    .venv/bin/python -I pipeline/mocap/prep.py            # all clips in CLIPS
Source: CMU Graphics Lab Motion Capture Database (free for any use), BVH conversion by B. Hahne (cgspeed),
mirrored on github.com/una-dinosauria/cmu-mocap. Raw files: data/raw/mocap/<subject>/<subject>_<trial>.bvh.
Output: data/cache/mocap/<name>.npz  (world rotations in Blender axes: x = left, y = back, z = up).
"""
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bvh

ROOT = "/Users/danielgnagi/sandboxzurich"
RAW = f"{ROOT}/data/raw/mocap"; OUT = f"{ROOT}/data/cache/mocap"
# name: (file, kind, period range seconds, output fps). set A = subject 35/8 (taller), set B = subject 7/16 (smaller build)
CLIPS = {
    "A_walk": ("035/35_01.bvh", "gait", (0.8, 1.5), 30), "A_run": ("035/35_21.bvh", "gait", (0.55, 1.0), 30), "A_slow": ("035/35_29.bvh", "gait", (0.9, 1.7), 30),
    "B_walk": ("007/07_09.bvh", "gait", (0.8, 1.5), 30), "B_run": ("016/16_46.bvh", "gait", (0.5, 0.9), 30), "B_slow": ("007/07_04.bvh", "gait", (0.9, 1.8), 30),
    "idle_1": ("049/49_16.bvh", "idle", (3.0, 6.0), 15), "idle_3": ("049/49_15.bvh", "idle", (3.0, 5.5), 15),
}
M = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # BVH (x left, y up, z fwd) -> Blender (x left, y back, z up)

def mat2quat(R):
    """(...,3,3) -> (...,4) w,x,y,z (continuous sign fixed by caller)."""
    sh = R.shape[:-2]; R = R.reshape(-1, 3, 3); q = np.zeros((len(R), 4)); t = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]
    for i, r in enumerate(R):
        if t[i] > 0:
            s = np.sqrt(t[i] + 1) * 2; q[i] = [s / 4, (r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s]
        elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
            s = np.sqrt(1 + r[0, 0] - r[1, 1] - r[2, 2]) * 2; q[i] = [(r[2, 1] - r[1, 2]) / s, s / 4, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s]
        elif r[1, 1] > r[2, 2]:
            s = np.sqrt(1 + r[1, 1] - r[0, 0] - r[2, 2]) * 2; q[i] = [(r[0, 2] - r[2, 0]) / s, (r[0, 1] + r[1, 0]) / s, s / 4, (r[1, 2] + r[2, 1]) / s]
        else:
            s = np.sqrt(1 + r[2, 2] - r[0, 0] - r[1, 1]) * 2; q[i] = [(r[1, 0] - r[0, 1]) / s, (r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, s / 4]
    return (q / np.linalg.norm(q, axis=1, keepdims=True)).reshape(sh + (4,))

def qmul(a, b):
    w1, x1, y1, z1 = np.moveaxis(a, -1, 0); w2, x2, y2, z2 = np.moveaxis(b, -1, 0)
    return np.stack([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2], -1)
def qinv(a): return a * np.array([1, -1, -1, -1])
def slerp(a, b, t):
    """a,b (...,4); t (...,1) or scalar."""
    d = (a * b).sum(-1, keepdims=True); b = np.where(d < 0, -b, b); d = np.abs(d).clip(0, 1)
    th = np.arccos(d); s = np.sin(th); small = s < 1e-6
    wa = np.where(small, 1 - t, np.sin((1 - t) * th) / np.where(small, 1, s)); wb = np.where(small, t, np.sin(t * th) / np.where(small, 1, s))
    q = wa * a + wb * b; return q / np.linalg.norm(q, axis=-1, keepdims=True)
def fixsign(q):
    for i in range(1, len(q)):
        flip = (q[i] * q[i - 1]).sum(-1) < 0; q[i][flip] *= -1
    return q

def process(name, spec):
    f, kind, (pmin, pmax), fps = spec
    J, D, ft = bvh.parse(f"{RAW}/{f}"); L, W, P = bvh.fk(J, D); nf = len(D); nm = [j["name"] for j in J]
    # heading: net displacement of the hips over the whole clip -> yaw so that travel is +Z
    d = P[-1, 0] - P[0, 0]; yaw = np.arctan2(d[0], d[2]) if kind == "gait" else 0.0
    c, s = np.cos(-yaw), np.sin(-yaw); Ry = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    W = Ry @ W; P = P @ Ry.T
    q = fixsign(mat2quat(W))                                      # (nf,nj,4) world quats, BVH axes
    key = [nm.index(n) for n in ("Hips", "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg", "LeftFoot", "RightFoot", "Spine1", "LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "Head")]
    feat = np.concatenate([W[:, key].reshape(nf, -1), 0.15 * np.gradient(W[:, key].reshape(nf, -1), axis=0) / ft * 0.1, 4 * np.gradient(P[:, 0, 1:2] * 0 + P[:, 0, 1:2], axis=0) / ft * 0.1], 1)
    best = None
    pmin_f, pmax_f = int(pmin / ft), int(pmax / ft)
    for Pf in range(pmin_f, min(pmax_f, nf - 2) + 1, 1):
        a = np.arange(0, nf - Pf); dist = np.linalg.norm(feat[a] - feat[a + Pf], axis=1)
        k = int(dist.argmin()); sc = dist[k] * (1 + 0.25 * Pf * ft)          # prefer short cycles
        if kind == "gait" and k + Pf > nf - 1: continue
        if best is None or sc < best[0]: best = (sc, k, Pf, dist[k])
    _, a, Pf, dd = best
    # closed loop: spread the end-start mismatch linearly over the cycle
    idx = np.arange(Pf + 1); t = (idx / Pf)[:, None, None]
    qq = q[a:a + Pf + 1].copy(); dq = qmul(qq[0], qinv(qq[-1]))[None]
    ident = np.zeros_like(dq); ident[..., 0] = 1
    qq = qmul(slerp(ident, dq, t), qq)
    hp = P[a:a + Pf + 1, 0].copy(); disp = hp[-1] - hp[0]; vsrc = float(np.hypot(disp[0], disp[2]) / (Pf * ft))
    for ax in (0, 2): hp[:, ax] -= disp[ax] * (idx / Pf) + (hp[:, ax] - disp[ax] * (idx / Pf)).mean() * (kind == "gait")   # in place, keep sway
    hp[:, 1] -= disp[1] * (idx / Pf)                                                                                      # absolute height, drift removed
    # phase: start at left-foot forward-most (heel strike) for gaits
    start = 0
    if kind == "gait":
        lf = nm.index("LeftFoot"); fz = (P[a:a + Pf + 1, lf, 2] - P[a:a + Pf + 1, 0, 2])[:-1]; start = int(fz.argmax())
    # resample cyclically to output fps
    n = max(8, round(Pf * ft * fps)); u = (start + np.arange(n) * Pf / n) % Pf
    i0 = np.floor(u).astype(int); fr = (u - i0)[:, None, None]; i1 = np.minimum(i0 + 1, Pf)
    # wrap: index Pf equals index 0 after the correction (closed loop)
    qo = slerp(qq[i0], qq[i1], fr)
    ho = hp[i0] * (1 - fr[:, 0]) + hp[i1] * fr[:, 0]
    # to Blender axes
    Mq = mat2quat(M[None])[0]
    qb = qmul(qmul(Mq, qo), qinv(Mq)); hb = ho @ M.T
    P0 = bvh.fk(J, np.zeros((1, sum(len(j["ch"]) for j in J))))[2][0] @ M.T
    os.makedirs(OUT, exist_ok=True)
    np.savez(f"{OUT}/{name}.npz", q=qb.astype(np.float32), hip=hb.astype(np.float32), names=np.array(nm), parents=np.array([j["parent"] for j in J]),
             rest_pos=P0.astype(np.float32), fps=fps, duration=n / fps, vsrc=vsrc)
    print(f"{name:7s} {f} cycle {Pf*ft:.2f}s -> {n} frames @{fps} ({n/fps:.2f}s) mismatch={dd:.3f} v_src={vsrc:.2f} m/s start={start}")

if __name__ == "__main__":
    for k in (sys.argv[1:] or CLIPS): process(k, CLIPS[k])
