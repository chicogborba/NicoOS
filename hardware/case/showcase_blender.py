"""blender -b -P showcase_blender.py -- <out_dir> <clear|pink> [shot,...]   → out/showcase/*.png"""
import bpy, bmesh, os, sys, math, glob, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out, variant = argv[0], argv[1]
only = argv[2].split(",") if len(argv) > 2 else None
asm = os.path.join(out, "assembly")
sdir = os.path.join(out, "showcase")
os.makedirs(sdir, exist_ok=True)
info = json.load(open(os.path.join(out, "validation.json")))["info"]
U = 0.01  # mm → scene units

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
try:
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = "METAL"
    cp.get_devices()
    for d in cp.devices:
        d.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU unavailable:", e)
clear = variant == "clear"
sc.cycles.samples = 192 if clear else 96
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 24 if clear else 8
sc.cycles.transmission_bounces = 24 if clear else 4
sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast" if clear else "None"
sc.view_settings.exposure = 0.0

world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
wn = world.node_tree.nodes
wn["Background"].inputs[0].default_value = (1, 1, 1, 1)
wn["Background"].inputs[1].default_value = 0.55

def bsdf_set(b, **kw):
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v

def mat(name, rgb, rough=0.45, metal=0.0, **extra):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    bsdf_set(b, **{"Base Color": (*rgb, 1), "Roughness": rough, "Metallic": metal})
    bsdf_set(b, **extra)
    return m

if clear:
    M_SHELL = mat("clear", (1, 1, 1), 0.04, **{"Transmission Weight": 1.0, "IOR": 1.50, "Specular IOR Level": 0.5})
    M_BTN = mat("clearbtn", (1, 1, 1), 0.22, **{"Transmission Weight": 1.0, "IOR": 1.50})
else:
    M_SHELL = mat("pink", (0.90, 0.40, 0.53), 0.42, **{"Coat Weight": 0.15, "Coat Roughness": 0.3, "Subsurface Weight": 0.05})
    M_BTN = mat("cream", (0.98, 0.93, 0.85), 0.35, **{"Coat Weight": 0.2})
M_BEZ = mat("bez", (0.015, 0.015, 0.018), 0.12, **{"Coat Weight": 0.6})
M_PCB = mat("pcb", (0.05, 0.32, 0.14), 0.45)
M_ESP = mat("esp", (0.04, 0.05, 0.12), 0.35)
M_TP = mat("tp", (0.06, 0.18, 0.45), 0.4)
M_BAT = mat("bat", (0.80, 0.80, 0.82), 0.25, 0.85)
M_IR = mat("ir", (0.55, 0.62, 1.0), 0.05, **{"Transmission Weight": 0.85})
M_RX = mat("rx", (0.03, 0.03, 0.03), 0.25)
M_SW = mat("sw", (0.12, 0.12, 0.12), 0.35)
M_MET = mat("metal", (0.85, 0.85, 0.87), 0.2, 1.0)
M_OLED = mat("oled", (0.01, 0.01, 0.012), 0.05)
M_FLOOR = mat("floor", (0.95, 0.95, 0.96), 0.55)

def load(name, material, smooth=False):
    p = os.path.join(asm, name + ".stl")
    bpy.ops.wm.stl_import(filepath=p)
    o = bpy.context.selected_objects[0]
    o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(o.data); bm.free()
    if smooth:
        o.data.shade_smooth()
        o.data.set_sharp_from_angle(angle=math.radians(38))
    else:
        o.data.shade_flat()
    o.data.materials.clear(); o.data.materials.append(material)
    o.scale = (U, U, U)
    return o

def mat_for(n):
    if "main_pcb" in n: return M_PCB
    if "esp32c3" in n: return M_ESP
    if "tp4056" in n: return M_TP
    if "battery_pcm" in n: return M_SW
    if "battery" in n: return M_BAT
    if "ir_led" in n: return M_IR
    if "ir_rx" in n: return M_RX
    if "screw" in n: return M_MET
    if "oled_header" in n: return M_SW
    if "oled" in n: return M_OLED
    if "tact" in n: return M_SW
    if "switch" in n: return M_SW
    return M_PCB

for n in ("front_shell", "back_shell"):
    load(n, M_SHELL, True)
load("screen_bezel", M_BEZ)
if os.path.exists(os.path.join(asm, "usb_cap_esp32.stl")):
    load("usb_cap_esp32", M_SHELL, True)
for p in sorted(glob.glob(os.path.join(asm, "button_*.stl"))):
    load(os.path.basename(p)[:-4], M_BTN, True)
for p in sorted(glob.glob(os.path.join(asm, "cmp_*.stl"))):
    n = os.path.basename(p)[:-4]
    if "usb_plug" in n:
        continue
    if not clear and n not in ("cmp_oled_glass",):
        continue
    load(n, mat_for(n))

# OLED content: pixel cat on a 128x64 emissive plane in the bezel opening
CAT = [
    "..X...............X..",
    "..XX.............XX..",
    "..X.X...........X.X..",
    "..X..XXXXXXXXXXX..X..",
    ".X.................X.",
    ".X.................X.",
    ".X...XX.......XX...X.",
    ".X...XX.......XX...X.",
    ".X.................X.",
    ".X........X........X.",
    ".X......X.X.X......X.",
    ".X.......X.X.......X.",
    "..X...............X..",
    "...XXXXXXXXXXXXXXX...",
]
W, H = 128, 64
px = [0.0] * (W * H * 4)
def setp(x, y, v=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = ((H - 1 - y) * W + x) * 4
        px[i:i + 4] = [v, v, v, 1.0]
for i in range(W * H):
    px[i * 4 + 3] = 1.0
s = 3
ox, oy = (W - len(CAT[0]) * s) // 2, (H - len(CAT) * s) // 2 - 2
for r, row in enumerate(CAT):
    for c, ch in enumerate(row):
        if ch == "X":
            for dx in range(s):
                for dy in range(s):
                    setp(ox + c * s + dx, oy + r * s + dy)
for x in range(110, 124):            # tiny battery icon
    setp(x, 3); setp(x, 9)
for y in range(3, 10):
    setp(110, y); setp(123, y)
setp(124, 5); setp(124, 6); setp(124, 7)
for x in range(112, 120):
    for y in range(5, 8):
        setp(x, y)
img = bpy.data.images.new("oled", W, H)
img.pixels = px
m = bpy.data.materials.new("screen"); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 4.0
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0, 0, 0, 1); mix.inputs[2].default_value = (0.75, 0.95, 1.0, 1)
outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], outn.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1)
scr = bpy.context.active_object
scr.scale = (21.7 * U, 10.9 * U, 1)
scr.location = (0, 14.75 * U, info["CEIL"] * U + 0.0004)
scr.data.materials.append(m)

# floor + lights
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.0002))
bpy.context.active_object.data.materials.append(M_FLOOR)

def light(loc, energy, size, color=(1, 1, 1)):
    l = bpy.data.lights.new("L", "AREA"); l.energy = energy; l.size = size; l.color = color
    o = bpy.data.objects.new("L", l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0.05, 0.1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light((1.6, -1.8, 2.6), 380, 2.5)
light((-2.2, -0.4, 1.4), 120, 2.0, (0.95, 0.97, 1.0))
light((0.2, 2.4, 1.0), 160, 1.5)

cam_d = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("T", None); sc.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True
cam_d.dof.focus_object = tgt
cam_d.dof.aperture_fstop = 5.6

SHOTS = {
    "hero":   ((0.95, -1.55, 1.40), (0.0, 0.05, 0.06), 55),
    "front":  ((0.0, -0.55, 2.35), (0.0, 0.05, 0.08), 55),
    "ports":  ((-0.85, -1.75, 0.62), (0.0, -0.12, 0.08), 55),
    "ears":   ((0.85, 1.85, 1.05), (0.0, 0.12, 0.08), 55),
}
for name, (loc, t, lens) in SHOTS.items():
    if only and name not in only:
        continue
    cam.location = loc; tgt.location = t; cam_d.lens = lens
    sc.render.filepath = os.path.join(sdir, f"{variant}_{name}.png")
    bpy.ops.render.render(write_still=True)
print("SHOWCASE DONE")
