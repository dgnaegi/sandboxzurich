"""Shared animation library (run inside Blender via build_human.py with env ANIMLIB=<class>).

Clips live in anims_<class>.glb (armature only, ~100 KB), not in every NPC glb: the game loads four libraries once
(A_young, B_young, A_old, B_old = male/female x posture) and adds the clips to every figure of that class
(web/src/world/humans.ts). Sources: CMU mocap windows from pipeline/mocap/prep.py (CLIPS), plus two procedural
arm poses over a mocap idle (arms crossed, hands in pockets). Pelvis translation is scaled to the figure's leg length at load time.
"""
import os, bpy

# lib clip name -> (npz source, arm override | None). hunch applies to old figures only.
PLAN = {
    "shift": ("shift_1", None), "shift2": ("shift_2", None), "look": ("look_1", None), "stand2": ("stand_2", None),
    "wait": ("wait_1", None), "wait2": ("wait_2", None),
    "talk": ("talk_1", None), "listen": ("talk_0", None), "talk2": ("talk_2", None), "argue": ("argue", None),
    "call": ("call_l", None), "text": ("text", None),
    "crossed": ("idle_1", "crossed"), "pockets": ("idle_3", "pockets"), "pockets2": ("shift_1", "pockets"), "crossed2": ("shift_2", "crossed"),
    "sit": ("sit_1", None), "sit_talk": ("sit_talk", None), "sit_chat": ("sit_2", None),
}
ARMS = {   # (out, fwd, up) in character terms, see humans.arm()
    "crossed": dict(r=((0.06, 0.34, -1), (-0.92, 0.38, 0.32)), l=((0.10, 0.30, -1), (-0.92, 0.52, 0.12))),
    "pockets": dict(r=((0.22, -0.02, -1), (-0.22, 0.62, -0.78)), l=((0.22, -0.02, -1), (-0.22, 0.62, -0.78))),
}

def _override(Pb, Hm, kind):
    Hm._st(Pb).clear()
    for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
    for s, (up, lo) in ARMS[kind].items(): Hm.arm(Pb, s, up, lo)
    out = {b: Pb[b].rotation_quaternion.copy() for s in "lr" for b in (f"upperarm_{s}", f"lowerarm_{s}")}
    Hm._st(Pb).clear()
    for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
    return out

def build(rt, Pb, Hm, MR, old, cls, rig, out):
    only = os.environ.get("ANIMLIB_ONLY")
    for name, (src, ov) in PLAN.items():
        if only and name not in only.split(","): continue
        sit = name.startswith("sit")
        hun = (12 if sit else 9) if old else 0
        rt.build_action(name, MR.load(src), hunch=hun, measure=False, override=_override(Pb, Hm, ov) if ov else None)
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
    print("LIBDONE", cls, os.path.getsize(path) // 1024, "KB")
