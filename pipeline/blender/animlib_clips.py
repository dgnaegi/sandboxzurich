"""Shared animation library (run inside Blender via build_human.py with env ANIMLIB=<class>).

Clips live in anims_<class>.glb (armature only, ~100 KB), not in every NPC glb: the game loads four libraries once
(A_young, B_young, A_old, B_old = male/female x posture) and adds the clips to every figure of that class
(web/src/world/humans.ts). Sources: CMU mocap windows from pipeline/mocap/prep.py (CLIPS), plus two procedural
arm poses over a mocap idle (arms crossed, hands in pockets). Pelvis translation is scaled to the figure's leg length at load time.
"""
import os, math, bpy

# lib clip name -> (npz source, arm override | None). hunch applies to old figures only.
PLAN = {
    "shift": ("shift_1", None), "look": ("talk_0", "head_look"), "stand2": ("stand_2", None), "wait": ("wait_1", None),
    "talk": ("talk_1", None), "listen": ("talk_0", None), "talk2": ("talk_2", None), "argue": ("argue", None),
    "call": ("talk_0", "call"), "text": ("stand_2", "text"),
    "crossed": ("talk_0", "crossed"), "crossed2": ("stand_2", "crossed"), "pockets": ("talk_0", "pockets"), "pockets2": ("wait_1", "pockets"),
    "sit": ("sit_1", None), "sit_talk": ("sit_talk", None), "sit_chat": ("sit_2", None),
}
HEAD = {"text": (12, 18), "call": (0, 4)}      # extra neck / head pitch (degrees, nodding forward) for the phone poses
ARMS = {
    "text": dict(r=((0.12, 0.35, -1), (-0.42, 0.75, 0.62), (-15, 0, 0)), l=((0.14, 0.3, -1), (-0.5, 0.72, 0.45))),
    "call": dict(r=((0.30, 0.05, -1), (-0.10, 0.20, 1.0), (0, 0, 0)), l=((0.06, 0.50, -0.85), (-0.85, 0.60, 0.40))),   # (out, fwd, up) in character terms, see humans.arm()
    "crossed": dict(r=((0.02, 0.55, -0.85), (-0.85, 0.45, 0.62)), l=((0.06, 0.50, -0.85), (-0.85, 0.70, 0.40))),
    "pockets": dict(r=((0.14, 0.0, -1), (-0.28, 0.50, -0.82), (-45, 0, 0)), l=((0.14, 0.0, -1), (-0.28, 0.50, -0.82), (-45, 0, 0))),
}

def _pitch(rt, kind):
    """Phone poses: nod the head forward (character X axis, like humans.R)."""
    from mathutils import Euler
    nk, hd = HEAD[kind]
    def post(f, n, loc):
        for b, a in (("neck_01", nk), ("head", hd)):
            B = rt.rest[b]; loc[b] = loc[b] @ (B.inverted() @ Euler((math.radians(a), 0, 0), "YXZ").to_quaternion() @ B)
    return post

def _look(f, n, loc):
    """Slow glances left and right: yaw about the long axis of neck (40 %) and head (60 %)."""
    from mathutils import Quaternion
    a = math.radians(38) * (math.sin(2 * math.pi * f / n) + 0.45 * math.sin(4 * math.pi * f / n + 1.0)) / 1.3
    for b, w in (("neck_01", 0.4), ("head", 0.6)): loc[b] = loc[b] @ Quaternion((0, 1, 0), a * w)

def _override(Pb, Hm, kind):
    Hm._st(Pb).clear()
    for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
    for s, v in ARMS[kind].items(): Hm.arm(Pb, s, v[0], v[1], *v[2:])
    out = {b: Pb[b].rotation_quaternion.copy() for s in "lr" for b in (f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}")}
    Hm._st(Pb).clear()
    for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
    return out

def build(rt, Pb, Hm, MR, old, cls, rig, out):
    only = os.environ.get("ANIMLIB_ONLY")
    for name, (src, ov) in PLAN.items():
        if only and name not in only.split(","): continue
        sit = name.startswith("sit")
        hun = (12 if sit else 9) if old else 0
        rt.build_action(name, MR.load(src), hunch=hun, measure=False, override=_override(Pb, Hm, ov) if ov in ARMS else None, post=_look if ov == "head_look" else (_pitch(rt, ov) if ov in HEAD else None))
        print("LIBCLIP", cls, name, src)
    import math
    rig.rotation_euler = (0, 0, math.pi)
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True); bpy.context.view_layer.objects.active = rig
    path = f"{out}/anims_{cls}.glb"
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_animations=True, export_animation_mode="ACTIONS",
        export_force_sampling=True, export_optimize_animation_size=True, export_skins=False, export_def_bones=False,
        export_apply=False, export_yup=True, export_cameras=False, export_lights=False, export_extras=False, export_morph=False)
    import glb_compact, mocap_retarget as _M
    glb_compact.compact(path, keep_rot=set(_M.MAP.keys()))
    print("LIBDONE", cls, os.path.getsize(path) // 1024, "KB")
