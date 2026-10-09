"""blender -b -P render_blender.py -- <out_dir>   (renders preview PNGs)"""
import bpy, os, sys, math, glob
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
asm = os.path.join(out, "assembly")
rdir = os.path.join(out, "renders")
os.makedirs(rdir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 40
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.view_settings.exposure = -0.6

world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.93, 0.92, 0.95, 1); bg.inputs[1].default_value = 0.35

def mat(name, rgb, rough=0.45, metal=0.0, alpha=1.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m

M_SHELL = mat("shell", (0.95, 0.62, 0.70), 0.5)       # soft pink
M_SHELL_X = mat("shellx", (0.95, 0.62, 0.70), 0.5, alpha=0.22)
M_BTN = mat("btn", (0.99, 0.95, 0.88), 0.35)            # cream buttons
M_BEZ = mat("bez", (0.05, 0.05, 0.06), 0.15)
M_PCB = mat("pcb", (0.10, 0.45, 0.22), 0.5)
M_ESP = mat("esp", (0.12, 0.16, 0.35), 0.4)
M_TP = mat("tp", (0.15, 0.30, 0.55), 0.4)
M_BAT = mat("bat", (0.75, 0.76, 0.78), 0.3, 0.6)
M_IR = mat("ir", (0.35, 0.35, 0.95), 0.1)
M_RX = mat("rx", (0.08, 0.08, 0.08), 0.3)
M_SW = mat("sw", (0.2, 0.2, 0.2), 0.4)
M_PLUG = mat("plug", (0.3, 0.3, 0.32), 0.5)
M_OLED = mat("oled", (0.02, 0.02, 0.04), 0.05)
M_SCREW = mat("screw", (0.7, 0.7, 0.72), 0.25, 1.0)

def load(name, material):
    p = os.path.join(asm, name + ".stl")
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=p)
    else:
        bpy.ops.import_mesh.stl(filepath=p)
    o = bpy.context.selected_objects[0]
    o.name = name
    o.data.materials.clear(); o.data.materials.append(material)
    for f in o.data.polygons:
        f.use_smooth = False
    o.scale = (0.01, 0.01, 0.01)   # mm → dm-ish scene units
    return o

def mat_for(n):
    if n.startswith("cmp_main_pcb"): return M_PCB
    if "esp32c3" in n and "plug" not in n: return M_ESP
    if "tp4056" in n and "plug" not in n: return M_TP
    if "plug" in n: return M_PLUG
    if "battery" in n: return M_BAT
    if "ir_led" in n: return M_IR
    if "ir_rx" in n: return M_RX
    if "switch" in n: return M_SW
    if "oled" in n: return M_OLED
    if "screw" in n: return M_SCREW
    if "tact" in n: return M_SW
    return M_PCB

shells = {n: load(n, M_SHELL) for n in ("front_shell", "back_shell")}
bez = load("screen_bezel", M_BEZ)
capf = os.path.join(asm, "usb_cap_esp32.stl")
ucap = load("usb_cap_esp32", M_SHELL) if os.path.exists(capf) else None
ONLY = sys.argv[sys.argv.index("--") + 2].split(",") if len(sys.argv) > sys.argv.index("--") + 2 else None
btns = [load(os.path.basename(p)[:-4], M_BTN) for p in sorted(glob.glob(os.path.join(asm, "button_*.stl")))]
cmps = [load(os.path.basename(p)[:-4], mat_for(os.path.basename(p))) for p in sorted(glob.glob(os.path.join(asm, "cmp_*.stl")))]

# lights
def light(loc, energy, size=3):
    l = bpy.data.lights.new("L", "AREA"); l.energy = energy; l.size = size
    o = bpy.data.objects.new("L", l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light((2, -2, 3), 350); light((-3, 1, 2), 140); light((0, 3, -1.5), 90)

cam_d = bpy.data.cameras.new("C"); cam_d.lens = 85
cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
target = bpy.data.objects.new("T", None); sc.collection.objects.link(target)
tc = cam.constraints.new("TRACK_TO"); tc.target = target; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

def show(objs, on):
    for o in objs:
        o.hide_render = not on

def shot(name, cam_loc, tgt=(0, 0.02, 0.1), lens=85):
    if ONLY and name[:2] not in ONLY:
        return
    cam.location = cam_loc; target.location = tgt; cam_d.lens = lens
    sc.render.filepath = os.path.join(rdir, name + ".png")
    bpy.ops.render.render(write_still=True)

plugs = [o for o in cmps if "plug" in o.name]
inner = [o for o in cmps if "plug" not in o.name]

# 1 hero front
show(inner + plugs, False)
shot("01_front", (0.9, -1.6, 1.9), (0, 0.04, 0.1), 50)
# 2 top edge: ears + IR
shot("02_top_ears_ir", (0.55, 2.1, 0.75), (0, 0.3, 0.1), 50)
# 3 bottom edge: ports
shot("03_bottom_ports", (-0.6, -2.0, 0.45), (0, -0.3, 0.1), 50)
# 3b close-up: capped ESP32 port + charge icon
shot("07_ports_closeup", (-0.12, -1.05, 0.2), (0, -0.38, 0.12), 85)
if ucap: ucap.hide_render = True
shot("08_cap_removed", (-0.12, -1.05, 0.2), (0, -0.38, 0.12), 85)
if ucap: ucap.hide_render = False
# 4 back + switch side
shot("04_back", (1.6, 0.9, -1.4), (0, 0.05, 0.1), 50)
# 5 internals: front shell hidden, back shell + electronics
show([shells["front_shell"], bez] + btns, False); show(inner, True)
for o in cmps:
    if "main_pcb" in o.name or "oled" in o.name or "tact" in o.name or "screw" in o.name:
        o.hide_render = True
shot("05_back_shell_internals", (0.45, -1.2, 2.0), (0, 0.03, 0.03), 50)
# 6 x-ray assembly
show([shells["front_shell"], bez] + btns + inner, True)
for s in shells.values():
    s.data.materials.clear(); s.data.materials.append(M_SHELL_X)
shot("06_xray_assembly", (1.1, -1.5, 1.5), (0, 0.04, 0.1), 50)
print("RENDER DONE")
