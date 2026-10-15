import bpy, sys, glob, json, os, math
R = "/Users/danielgnagi/sandboxzurich"
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["0", "16", "humans_sheet"]
lo, hi, outname = int(a[0]), int(a[1]), a[2]
man = json.load(open(f"{R}/web/public/models/humans/manifest.json"))
man = [e for e in man if (e["id"] == "player" and lo == 0) or (e["id"].startswith("npc_") and lo <= int(e["id"][4:]) < hi)]
cols = 9 if hi <= 16 else 12; i = 0
for e in man:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f"{R}/web/public/models/humans/{e['file']}")
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None:
            o.location.x = (i % cols) * 1.0; o.location.z = -(i // cols) * 2.0   # glTF-import is Z-up
    i += 1
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"; sc.display.shading.show_cavity = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.75, 0.78, 0.82)
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.ortho_scale = 9.2 if hi <= 16 else 12.4
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (4.0 if hi <= 16 else 5.5, 10, -0.1); co.rotation_euler = (math.radians(90), 0, math.radians(180))
sc.render.resolution_x = 1600; sc.render.resolution_y = 760
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
sc.render.filepath = f"{R}/preview/{outname}.jpg"
bpy.ops.render.render(write_still=True); print("SHEET")
