"""blender -b -P guide_exploded.py -- <out_dir>  → out/guide/exploded.png, closed.png"""
import bpy, os, sys, glob
out = sys.argv[sys.argv.index("--") + 1]; asm = os.path.join(out, "assembly")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.show_shadows = True
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.55, 0.55, 0.58); sh.background_type = "WORLD"
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = 0.9
sc.render.resolution_x, sc.render.resolution_y = 1100, 1500
def load(n, rgb, dz=0.0, dy=0.0):
    p = os.path.join(asm, n + ".stl")
    if not os.path.exists(p): return None
    bpy.ops.wm.stl_import(filepath=p)
    o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new(n); m.diffuse_color = (*rgb, 1); o.data.materials.append(m)
    o.scale = (0.01,) * 3; o["dz"] = dz; o["dy"] = dy
    return o
PINK, CREAM = (0.95, 0.55, 0.65), (0.98, 0.95, 0.88)
objs = [load("back_shell", PINK, 0.0), load("usb_cap_esp32", PINK, 0.0, -0.16),
        load("cmp_esp32c3", (0.15, 0.2, 0.5), 0.22), load("cmp_tp4056", (0.2, 0.4, 0.8), 0.22),
        load("cmp_battery", (0.8, 0.8, 0.83), 0.22), load("cmp_battery_pcm_wires", (0.3, 0.3, 0.3), 0.22),
        load("cmp_ir_led", (0.6, 0.55, 1.0), 0.22), load("cmp_ir_rx", (0.1, 0.1, 0.1), 0.22),
        load("cmp_main_pcb", (0.15, 0.5, 0.25), 0.62), load("cmp_oled_pcb", (0.15, 0.15, 0.3), 0.62),
        load("cmp_oled_glass", (0.03, 0.03, 0.04), 0.62), load("cmp_oled_header", (0.1, 0.1, 0.1), 0.62),
        load("screen_bezel", (0.05, 0.05, 0.06), 0.95), load("front_shell", PINK, 1.25)]
for i in range(6): objs.append(load(f"cmp_tact_{i}", (0.2, 0.2, 0.2), 0.62))
for p in glob.glob(os.path.join(asm, "button_*.stl")): objs.append(load(os.path.basename(p)[:-4], CREAM, 0.95))
objs = [o for o in objs if o]
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
t = bpy.data.objects.new("T", None); sc.collection.objects.link(t)
c = cam.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.data.lens = 82
for o in objs: o.location = (0, o["dy"], o["dz"])
t.location = (0, 0.05, 0.7); cam.location = (2.3, -3.3, 2.6)
sc.render.filepath = os.path.join(out, "guide", "exploded.png"); bpy.ops.render.render(write_still=True)
