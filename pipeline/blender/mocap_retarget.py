"""Retarget CMU mocap loops (pipeline/mocap/prep.py -> data/cache/mocap/*.npz) onto the MPFB game_engine rig.

Per mapped bone the world rotation is  W = Dsrc * C * Rest_tgt , with
  Dsrc = world rotation of the source joint relative to the source rest pose (BVH rest = all-identity),
  C    = minimal rotation taking the target rest segment direction onto the source rest segment direction
         (limbs only; spine/neck/head/pelvis keep their own curvature: C = identity).
Local pose = (W_parent * Rest_parent^-1 * Rest)^-1 * W.  Root motion is already removed by prep.py; the vertical
hip bob is scaled by the leg-length ratio and the pelvis is lowered so the lowest foot touches the ground.
Also measures the clip speed (m/s) from the stance feet.  Used by build_human.py (inside Blender).
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Quaternion, Matrix

CACHE = "/Users/danielgnagi/sandboxzurich/data/cache/mocap"
# target bone: (source joint, source child joint | None, target child bone | None, hunch weight)
MAP = {"pelvis": ("Hips", None, None), "spine_01": ("LowerBack", None, None), "spine_02": ("Spine", None, None),
       "spine_03": ("Spine1", None, None), "neck_01": ("Neck", None, None), "head": ("Head", None, None)}
for sd, sn in (("l", "Left"), ("r", "Right")):
    MAP.update({f"clavicle_{sd}": (f"{sn}Shoulder", f"{sn}Arm", f"upperarm_{sd}"), f"upperarm_{sd}": (f"{sn}Arm", f"{sn}ForeArm", f"lowerarm_{sd}"),
                f"lowerarm_{sd}": (f"{sn}ForeArm", f"{sn}Hand", f"hand_{sd}"), f"hand_{sd}": (f"{sn}Hand", f"{sn}FingerBase", f"middle_01_{sd}"),
                f"thigh_{sd}": (f"{sn}UpLeg", f"{sn}Leg", f"calf_{sd}"), f"calf_{sd}": (f"{sn}Leg", f"{sn}Foot", f"foot_{sd}"),
                f"foot_{sd}": (f"{sn}Foot", f"{sn}ToeBase", f"ball_{sd}"), f"ball_{sd}": (f"{sn}ToeBase", None, None)})
# cumulative forward bend (degrees) for stooped posture, per bone
HUNCH_BONES = ["spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "neck_01", "head"]
HUNCH_SHARE = {"spine_01": 0.25, "spine_02": 0.5, "spine_03": 0.75, "clavicle_l": 0.75, "clavicle_r": 0.75, "neck_01": 1.0, "head": 0.9}

def _q(a): return Quaternion((float(a[0]), float(a[1]), float(a[2]), float(a[3])))

def _arc(a, b):
    a = a.normalized(); b = b.normalized(); return a.rotation_difference(b)

def load(name):
    z = np.load(f"{CACHE}/{name}.npz")
    return dict(q=z["q"], hip=z["hip"], names=[str(x) for x in z["names"]], rest=z["rest_pos"], fps=int(z["fps"]), vsrc=float(z["vsrc"]), nm=int(len(z["q"])))

class Retargeter:
    def __init__(self, rig):
        self.rig = rig; self.B = rig.data.bones; self.Pb = rig.pose.bones
        self.rest = {b.name: b.matrix_local.to_quaternion() for b in self.B}
        self.head = {b.name: Vector(b.head_local) for b in self.B}
        for pb in self.Pb: pb.rotation_mode = "QUATERNION"
        self.order = [b.name for b in self.B]            # parents precede children in this armature
        L = lambda a, b: (self.head[a] - self.head[b]).length
        self.leg = L("thigh_l", "calf_l") + L("calf_l", "foot_l")
        self.pelvis_rest = self.rest["pelvis"]
        self.foot_names = ["foot_l", "foot_r", "ball_l", "ball_r"]
        for pb in self.Pb: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        bpy.context.view_layer.update(); self.rest_foot = self._foot_min()

    def _foot_min(self):
        bpy.context.view_layer.update()
        return min(min(self.Pb[b].head.z, self.Pb[b].tail.z) for b in self.foot_names)

    def _corr(self, clip):
        """Per-bone rest correction C (Quaternion) for this source clip."""
        idx = {n: i for i, n in enumerate(clip["names"])}; C = {}
        for bone, (sj, sc, tc) in MAP.items():
            if sc is None: C[bone] = Quaternion(); continue
            sdir = Vector(clip["rest"][idx[sc]] - clip["rest"][idx[sj]]); tdir = self.head[tc] - self.head[bone]
            C[bone] = _arc(tdir, sdir)
        src_leg = float(np.linalg.norm(clip["rest"][idx["LeftLeg"]] - clip["rest"][idx["LeftUpLeg"]]) + np.linalg.norm(clip["rest"][idx["LeftFoot"]] - clip["rest"][idx["LeftLeg"]]))
        return C, idx, self.leg / src_leg

    def frames(self, clip, hunch=0.0, lock_arm=None):
        """-> (list of {bone: Quaternion} local pose, hip offsets [Vector], scale)."""
        C, idx, s = self._corr(clip); out = []; hips = []
        hunch_q = {b: Quaternion((1, 0, 0), math.radians(hunch * HUNCH_SHARE[b])) for b in HUNCH_BONES}
        hip = clip["hip"]; hz = hip[:, 2].mean()
        for f in range(clip["nm"]):
            W = {}; loc = {}
            for name in self.order:
                b = self.B[name]; par = b.parent.name if b.parent else None
                if name in MAP:
                    D = _q(clip["q"][f, idx[MAP[name][0]]])
                    w = D @ C[name] @ self.rest[name]
                    if name in hunch_q: w = hunch_q[name] @ w
                else:
                    w = None
                if par is None: W[name] = self.rest[name] if w is None else w; continue
                lrest = self.rest[par].inverted() @ self.rest[name]
                if w is None: W[name] = W[par] @ lrest; continue
                W[name] = w; loc[name] = (W[par] @ lrest).inverted() @ w
            out.append(loc)
            hips.append(Vector((hip[f, 0] * s, hip[f, 1] * s, (hip[f, 2] - hz) * s)))   # hip is already in Blender axes (x left, y back, z up)
        for f in range(1, len(out)):          # keep quaternion signs continuous so linear key interpolation never takes the long way
            for b, q in out[f].items():
                if q.dot(out[f - 1][b]) < 0: out[f][b] = Quaternion((-q.w, -q.x, -q.y, -q.z))
        return out, hips, s

    def build_action(self, name, clip, hunch=0.0, lock=True, measure=True, override=None):
        """Create a keyed action; returns the measured clip speed (m/s) or 0 for idle."""
        n = clip["nm"]; fps = clip["fps"]; step = 30 // fps; loc, hips, s = self.frames(clip, hunch)
        if override:                                    # fixed local rotations (arms crossed / hands in pockets) over the mocap body
            for f in range(n): loc[f].update({b: q.copy() for b, q in override.items()})
        # pass 1: foot heights/positions without vertical offset
        pel = self.Pb["pelvis"]; zs = []; feet = []; hands = []
        for f in range(n):
            for pb in self.Pb: pb.rotation_quaternion = (1, 0, 0, 0)
            for b, q in loc[f].items(): self.Pb[b].rotation_quaternion = q
            h = hips[f]; pel.location = self.pelvis_rest.inverted() @ Vector((h.x, h.y, h.z))
            zs.append(self._foot_min())
            hands.append(-(self.Pb["hand_l"].head.y - pel.head.y))
            feet.append([(min(self.Pb[f"{a}_{k}"].head.z for a in ("foot", "ball")) , -self.Pb[f"foot_{k}"].head.y) for k in ("l", "r")])
        g = self.rest_foot - min(zs)
        speed = 0.0
        if measure:
            vs = []; floor = min(min(fe[0][0], fe[1][0]) for fe in feet)
            for k in range(2):
                for f in range(n):
                    f2 = (f + 1) % n; z1, y1 = feet[f][k]; z2, y2 = feet[f2][k]
                    if z1 < floor + 0.02 and z2 < floor + 0.02:
                        d = y2 - y1                       # forward = -Y in rig space; the stance foot slides backwards
                        if f2 < f: continue
                        vs.append(-d * fps)
            if vs: speed = float(np.median(vs))
        act = bpy.data.actions.new(name); ad = self.rig.animation_data_create(); ad.action = act
        mapped = list(MAP.keys())
        for f in range(n):
            for pb in self.Pb: pb.rotation_quaternion = (1, 0, 0, 0)
            for b, q in loc[f].items(): self.Pb[b].rotation_quaternion = q
            h = hips[f]; dz = g
            pel.location = self.pelvis_rest.inverted() @ Vector((h.x, h.y, h.z + dz))
            for b in mapped: self.Pb[b].keyframe_insert("rotation_quaternion", frame=f * step)
            pel.keyframe_insert("location", frame=f * step)
        # closing frame = frame 0 (seamless loop)
        for b in mapped: self.Pb[b].keyframe_insert("rotation_quaternion", frame=n * step)
        pel.keyframe_insert("location", frame=n * step)
        # copy frame-0 values onto frame n
        fcs = act.fcurves if hasattr(act, "fcurves") else [fc for ly in act.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            kp = fc.keyframe_points; kp[-1].co[1] = kp[0].co[1]
        act.use_fake_user = True; ad.action = None
        for pb in self.Pb: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        print("ARMSWING", name, "hand fwd range %.2f..%.2f" % (min(hands), max(hands)))
        return round(speed, 3), round(s, 3), round(g, 3)
