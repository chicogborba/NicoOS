"""blender -b -P quick_color.py -- <out_dir> <name> <shell r,g,b> <button r,g,b>   (Workbench, seconds)"""
import bpy, os, sys, glob
a = sys.argv[sys.argv.index("--") + 1:]
out, name = a[0], a[1]
shell = tuple(map(float, a[2].split(","))); btn = tuple(map(float, a[3].split(",")))
asm = os.path.join(out, "assembly")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = 0.9
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.35, 0.35, 0.37); sh.background_type = "WORLD"
def mat(rgb):
    m = bpy.data.materials.new("m"); m.diffuse_color = (*rgb, 1); return m
MS, MB, MK = mat(shell), mat(btn), mat((0.05, 0.05, 0.06))
def load(n, m):
    bpy.ops.wm.stl_import(filepath=os.path.join(asm, n + ".stl"))
    o = bpy.context.selected_objects[0]; o.data.materials.append(m); o.scale = (0.01,) * 3
for n in ("front_shell", "back_shell", "usb_cap_esp32"):
    if os.path.exists(os.path.join(asm, n + ".stl")): load(n, MS)
load("screen_bezel", MK); load("cmp_oled_glass", MK)
for p in glob.glob(os.path.join(asm, "button_*.stl")): load(os.path.basename(p)[:-4], MB)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
t = bpy.data.objects.new("T", None); sc.collection.objects.link(t); t.location = (0, 0.04, 0.08)
c = cam.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.data.lens = 50
for tag, loc in (("front", (0.9, -1.6, 1.9)), ("ports", (-0.7, -1.9, 0.55))):
    cam.location = loc
    sc.render.filepath = os.path.join(out, "quick", f"{name}_{tag}.png")
    bpy.ops.render.render(write_still=True)
