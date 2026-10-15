"""Minimal BVH reader + FK (numpy). CMU Graphics Lab mocap, cgspeed BVH conversion (units: 1 = 0.0564 m)."""
import numpy as np
SCALE = 0.0564

def parse(path):
    toks = open(path).read().split("\n")
    joints = []; stack = []; i = 0
    while i < len(toks):
        s = toks[i].split()
        if s and s[0] in ("ROOT", "JOINT"):
            joints.append(dict(name=s[1], parent=stack[-1] if stack else -1, off=None, ch=[])); stack.append(len(joints) - 1)
        elif s and s[0] == "End":
            stack.append(-2)
        elif s and s[0] == "OFFSET" and stack[-1] >= 0: joints[stack[-1]]["off"] = np.array([float(x) for x in s[1:4]])
        elif s and s[0] == "CHANNELS": joints[stack[-1]]["ch"] = s[2:]
        elif s and s[0] == "}": stack.pop()
        elif s and s[0] == "MOTION": i += 1; break
        i += 1
    nf = int(toks[i].split()[1]); ft = float(toks[i + 1].split()[2])
    data = np.array([[float(x) for x in l.split()] for l in toks[i + 2:i + 2 + nf] if l.strip()])
    return joints, data, ft

def euler_to_mat(axes, angs):
    """angs (n,3) degrees, axes list like ['Z','Y','X'] applied in this order (first = outermost). -> (n,3,3)"""
    out = np.tile(np.eye(3), (len(angs), 1, 1))
    for ax, a in zip(axes, angs.T):
        r = np.radians(a); c, s = np.cos(r), np.sin(r); m = np.zeros((len(a), 3, 3))
        if ax == "X": m[:, 0, 0] = 1; m[:, 1, 1] = c; m[:, 1, 2] = -s; m[:, 2, 1] = s; m[:, 2, 2] = c
        if ax == "Y": m[:, 1, 1] = 1; m[:, 0, 0] = c; m[:, 0, 2] = s; m[:, 2, 0] = -s; m[:, 2, 2] = c
        if ax == "Z": m[:, 2, 2] = 1; m[:, 0, 0] = c; m[:, 0, 1] = -s; m[:, 1, 0] = s; m[:, 1, 1] = c
        out = out @ m
    return out

def fk(joints, data):
    """-> local rot (nf,nj,3,3), world rot (nf,nj,3,3), world pos (nf,nj,3) in metres"""
    nf, nj = len(data), len(joints); col = 0
    L = np.tile(np.eye(3), (nf, nj, 1, 1)); pos = np.zeros((nf, 3))
    for j, J in enumerate(joints):
        ch = J["ch"]; vals = data[:, col:col + len(ch)]; col += len(ch)
        rot = [c for c in ch if c.endswith("rotation")]
        if len(rot) == 3:
            idx = [ch.index(c) for c in rot]
            L[:, j] = euler_to_mat([c[0] for c in rot], vals[:, idx])
        if "Xposition" in ch: pos = vals[:, [ch.index("Xposition"), ch.index("Yposition"), ch.index("Zposition")]]
    W = np.zeros_like(L); P = np.zeros((nf, nj, 3))
    for j, J in enumerate(joints):
        p = J["parent"]
        if p < 0: W[:, j] = L[:, j]; P[:, j] = pos * SCALE
        else: W[:, j] = W[:, p] @ L[:, j]; P[:, j] = P[:, p] + (W[:, p] @ J["off"]) * SCALE
    return L, W, P
