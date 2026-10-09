"""
BINI Cat Handheld — parametric generator.

    python build.py            # build parts, run clearance check, write STL/SVG/report

Outputs (./out):
    print/*.stl       parts in print orientation
    assembly/*.stl    every part + component dummy in assembly coordinates
    mainboard_template.svg   1:1 cut/drill template for the front perfboard
    validation.md / validation.json
"""
import json, math, os, sys, time
import numpy as np
import trimesh
import manifold3d as mf
from manifold3d import Manifold as M, CrossSection as CS, JoinType
from skimage.measure import marching_cubes

import params as P

SEG = 72
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(os.path.join(OUT, "print"), exist_ok=True)
os.makedirs(os.path.join(OUT, "assembly"), exist_ok=True)
EPS = 0.01

# ════════════════════════════ derived stack ════════════════════════════
W2, H2 = P.BODY_W / 2, P.BODY_H / 2
CI_W2, CI_H2 = W2 - P.WALL_THICKNESS, H2 - P.WALL_THICKNESS
CI_R = P.PLAN_CORNER_R - P.WALL_THICKNESS
FLOOR = P.WALL_THICKNESS

BOARD_T_MAX = max(P.TP4056_PCB_T, P.ESP_PCB_T)
PORT_Z = FLOOR + P.BOARD_LEDGE + BOARD_T_MAX + P.USB_C_H / 2          # feature line
PLUG_CB = (P.USB_PLUG_BODY[0] + 2 * P.USB_PLUG_BODY_CLEARANCE,
           P.USB_PLUG_BODY[1] + 2 * P.USB_PLUG_BODY_CLEARANCE)
SPLIT_Z = math.ceil((PORT_Z + PLUG_CB[1] / 2 + P.MIN_BRIDGE_ABOVE_PORT) * 20) / 20

comp_top = max(FLOOR + P.BATTERY_HEIGHT + P.BATTERY_CLEARANCE,
               PORT_Z + P.USB_C_H / 2 + 0.8)
PCB_BOT = math.ceil((comp_top + P.PCB_UNDERSIDE_KEEPOUT) * 20) / 20
PCB_TOP = PCB_BOT + P.MAIN_PCB_T
BUTTON_PLAY_MIN = 0.1
OLED_STACK = P.OLED_HEADER_H + P.OLED_PCB[2] + P.OLED_GLASS[2]
CEIL = PCB_TOP + max(P.FRONT_STACK_H, P.TACT_H + P.BUTTON_FLANGE_T + BUTTON_PLAY_MIN, OLED_STACK)
T = CEIL + P.WALL_THICKNESS
KEEPOUT_Z = PCB_BOT - P.PCB_UNDERSIDE_KEEPOUT
IR_Z = min(PORT_Z, KEEPOUT_Z - P.IR_RX_WIDTH / 2 - 0.2)

# board placement (USB on bottom edge, -y)
def board_geo(xc, w, l, t, overhang):
    y_e = -CI_H2 + P.USB_BOARD_EDGE_GAP
    zb = PORT_Z - P.USB_C_H / 2 - t
    y_conn = y_e - overhang
    cb = (y_conn - (-H2)) - P.USB_PLUG_SEAT_GAP
    return dict(xc=xc, w=w, l=l, t=t, y0=y_e, y1=y_e + l, zb=zb, y_conn=y_conn, cb=cb)

ESP = board_geo(P.ESP_X, P.ESP_WIDTH, P.ESP_LENGTH, P.ESP_PCB_T, P.ESP_USB_OVERHANG)
TP = board_geo(P.TP4056_X, P.TP4056_WIDTH, P.TP4056_LENGTH, P.TP4056_PCB_T, P.TP4056_USB_OVERHANG)
STOP_T = 1.2
for B in (ESP, TP):
    B["stop0"], B["stop1"] = B["y1"] + P.BOARD_REAR_SLACK, B["y1"] + P.BOARD_REAR_SLACK + STOP_T

BAY_L, BAY_W = max(P.BATTERY_BAY[0], P.BATTERY_LENGTH), max(P.BATTERY_BAY[1], P.BATTERY_WIDTH)
BAY_Y0 = max(ESP["stop1"], TP["stop1"]) + P.BATTERY_CLEARANCE
BAT_Y0 = BAY_Y0 + (BAY_W - P.BATTERY_WIDTH) / 2          # dummy cell centred in the bay
BAT = dict(x0=P.BATTERY_CENTER_X - P.BATTERY_LENGTH / 2, x1=P.BATTERY_CENTER_X + P.BATTERY_LENGTH / 2,
           y0=BAT_Y0, y1=BAT_Y0 + P.BATTERY_WIDTH, z0=FLOOR, z1=FLOOR + P.BATTERY_HEIGHT)
BAT_ENV = dict(x0=P.BATTERY_CENTER_X - BAY_L / 2 - P.BATTERY_WIRE_SPACE - P.BATTERY_CLEARANCE,
               x1=P.BATTERY_CENTER_X + BAY_L / 2 + P.BATTERY_CLEARANCE,
               y0=BAY_Y0 - P.BATTERY_CLEARANCE, y1=BAY_Y0 + BAY_W + P.BATTERY_CLEARANCE)

BOSS_D = P.BOSS_DIAG_OFFSET / math.sqrt(2)
BOSSES = [(sx * (CI_W2 - CI_R + BOSS_D), sy * (CI_H2 - CI_R + BOSS_D)) for sx in (-1, 1) for sy in (-1, 1)]

S = P.BUTTON_SPACING
DPAD = [(P.DPAD_CENTER[0] + dx, P.DPAD_CENTER[1] + dy) for dx, dy in ((0, S), (0, -S), (-S, 0), (S, 0))]

# IR LED
LED_R = P.IR_LED_DIAMETER / 2 + P.IR_LED_HOLE_CLEARANCE
LED_TIP_Y = H2 - P.IR_LED_RECESS
LED_FLANGE_Y = LED_TIP_Y - P.IR_LED_LENGTH
# IR RX (lying on its side, leads to +x)
RX_CX = P.IR_RX_X + P.IR_RX_DOME_OFFSET
RX = dict(x0=RX_CX - P.IR_RX_HEIGHT / 2, x1=RX_CX + P.IR_RX_HEIGHT / 2,
          y1=CI_H2 - 0.1, z0=IR_Z - P.IR_RX_WIDTH / 2, z1=IR_Z + P.IR_RX_WIDTH / 2)
RX["y0"] = RX["y1"] - P.IR_RX_DEPTH
# switch
SW_XF = W2 + P.SW_PROTRUDE - P.SW_ACT[2]
SW = dict(x0=SW_XF - P.SW_BODY[1], x1=SW_XF, y0=P.SW_Y - P.SW_BODY[0] / 2, y1=P.SW_Y + P.SW_BODY[0] / 2,
          z0=PORT_Z - P.SW_BODY[2] / 2, z1=PORT_Z + P.SW_BODY[2] / 2)

# ════════════════════════════ helpers ════════════════════════════
def box(x0, x1, y0, y1, z0, z1):
    return M.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))

def rrect(w, h, r, cx=0.0, cy=0.0):
    r = max(0.01, min(r, w / 2 - 0.01, h / 2 - 0.01))
    return CS.square((w - 2 * r, h - 2 * r), center=True).offset(r, JoinType.Round, circular_segments=SEG).translate((cx, cy))

def circ(r, cx=0.0, cy=0.0):
    return CS.circle(r, circular_segments=SEG).translate((cx, cy))

def ext(cs, z0, z1):
    return cs.extrude(z1 - z0).translate((0, 0, z0))

def cyl_z(cx, cy, r, z0, z1):
    return M.cylinder(z1 - z0, r, circular_segments=SEG).translate((cx, cy, z0))

def cyl_y(cx, cz, r, y0, y1):          # axis along +y
    return M.cylinder(y1 - y0, r, circular_segments=SEG).rotate((-90, 0, 0)).translate((cx, y0, cz))

def prism_y_neg(cs, L, scale=(1, 1)):  # 2D (x, z) section, extruded towards -y from y=0
    return cs.extrude(L, scale_top=scale).rotate((90, 0, 0))

def prism_y_pos(cs, L, scale=(1, 1)):  # symmetric-in-z sections only, towards +y
    return cs.extrude(L, scale_top=scale).rotate((-90, 0, 0))

def prism_x_pos(cs, L, scale=(1, 1)):  # 2D (y, z) section, towards +x
    return cs.extrude(L, scale_top=scale).rotate((90, 0, 90))

def stadium(w, h):
    return rrect(w, h, h / 2)

def chamfered_hole_y(cs, w, h, c, y_outer, outward, cx, cz, through_from):
    """Through-hole in a wall normal to y with a 45° chamfer of size c on the outside."""
    L_in = abs(y_outer - through_from) + 1
    if outward < 0:
        hole = prism_y_neg(cs, L_in + 1).translate((cx, through_from + 0.5, cz))
        L = c + 1.0
        ch = prism_y_neg(cs, L, ((w + 2 * L) / w, (h + 2 * L) / h)).translate((cx, y_outer + c, cz))
    else:
        hole = prism_y_pos(cs, L_in + 1).translate((cx, through_from - 0.5, cz))
        L = c + 1.0
        ch = prism_y_pos(cs, L, ((w + 2 * L) / w, (h + 2 * L) / h)).translate((cx, y_outer - c, cz))
    return hole + ch

def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)

def save(m, name, folder="assembly"):
    to_trimesh(m).export(os.path.join(OUT, folder, name + ".stl"))

# ════════════════════════════ smooth outer shell (SDF) ════════════════════════════
def sd_rrect(X, Y, hw, hh, r):
    qx, qy = np.abs(X) - (hw - r), np.abs(Y) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

def sd_triangle(X, Y, p0, p1, p2):
    P_ = np.stack([X, Y], -1)
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    e0, e1, e2 = p1 - p0, p2 - p1, p0 - p2
    v0, v1, v2 = P_ - p0, P_ - p1, P_ - p2
    def pq(v, e):
        t = np.clip((v @ e) / (e @ e), 0, 1)
        return v - e * t[..., None]
    pq0, pq1, pq2 = pq(v0, e0), pq(v1, e1), pq(v2, e2)
    s = np.sign(e0[0] * e2[1] - e0[1] * e2[0])
    dd = np.minimum(np.minimum((pq0 ** 2).sum(-1), (pq1 ** 2).sum(-1)), (pq2 ** 2).sum(-1))
    sg = np.minimum(np.minimum(s * (v0[..., 0] * e0[1] - v0[..., 1] * e0[0]),
                               s * (v1[..., 0] * e1[1] - v1[..., 1] * e1[0])),
                    s * (v2[..., 0] * e2[1] - v2[..., 1] * e2[0]))
    return -np.sqrt(dd) * np.sign(sg)

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

def inset(t, r, printable):
    t = np.clip(t, 0, None)
    out = np.where(t < r, r - np.sqrt(np.maximum(r * r - (r - t) ** 2, 0)), 0.0)
    if printable:
        t45 = r * (1 - math.sqrt(0.5))
        out = np.where(t < t45, t45 + (t45 - t), out)
    return out

def outline_sdf(X, Y):
    d = sd_rrect(X, Y, W2, H2, P.PLAN_CORNER_R)
    if P.EARS:
        r = P.EAR_TIP_R
        for s in (-1, 1):
            bx = s * P.EAR_X
            hb = P.EAR_BASE_W / 2 - r
            p0 = (bx - hb, H2 - 4.0)
            p1 = (bx + hb, H2 - 4.0)
            p2 = (bx + s * P.EAR_TIP_SHIFT, H2 + P.EAR_HEIGHT - r)
            d = smin(d, sd_triangle(X, Y, p0, p1, p2) - r, P.EAR_BLEND)
    return d

def build_shell():
    v = P.VOXEL
    j = 0.0373   # grid jitter: keeps feature planes off the marching-cubes lattice
    xs = np.arange(-W2 - 2 + j, W2 + 2 + v, v, dtype=np.float32)
    ys = np.arange(-H2 - 2 + j * 1.3, H2 + P.EAR_HEIGHT + 2 + v, v, dtype=np.float32)
    zs = np.arange(-1.0 + j * 0.7, T + 1 + v, v, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    d2 = outline_sdf(X, Y).astype(np.float32)
    g_out = np.maximum(inset(zs, P.BACK_EDGE_R, P.PRINTABLE_FILLET),
                       inset(T - zs, P.FRONT_EDGE_R, P.PRINTABLE_FILLET)).astype(np.float32)
    f = d2[:, :, None] + g_out[None, None, :]
    np.maximum(f, np.maximum(-zs, zs - T)[None, None, :], out=f)
    W = P.WALL_THICKNESS
    d2i = (sd_rrect(X, Y, W2, H2, P.PLAN_CORNER_R) + W).astype(np.float32)
    g_in = np.maximum(inset(zs - W, max(P.BACK_EDGE_R - W, 0.6), False),
                      inset(T - W - zs, max(P.FRONT_EDGE_R - W, 0.6), False)).astype(np.float32)
    fi = d2i[:, :, None] + g_in[None, None, :]
    np.maximum(fi, np.maximum(W - zs, zs - (T - W))[None, None, :], out=fi)
    def mc(field, level):
        verts, faces, _, _ = marching_cubes(field, level=level, spacing=(v, v, v))
        verts += np.array([xs[0], ys[0], zs[0]])
        tm = trimesh.Trimesh(verts, faces, process=True)
        if tm.volume < 0:
            tm.invert()
        m = M(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
        assert not m.is_empty(), m.status()
        return m
    # cavity grown ~1 mm into the wall: every internal rib/boss is clipped to this,
    # so nothing can ever poke through the rounded outer skin
    cav_grow = mc(fi, P.WALL_THICKNESS * 0.45)
    outer = mc(f, 0.0)
    np.maximum(f, -fi, out=f)
    del fi
    return mc(f, 0.0), cav_grow, outer

# ════════════════════════════ 2D outlines ════════════════════════════
CI = rrect(2 * CI_W2, 2 * CI_H2, CI_R)          # cavity outline at the split line

def big_box(z0, z1):
    return box(-W2 - 20, W2 + 20, -H2 - 20, H2 + 40, z0, z1)

# ════════════════════════════ front shell ════════════════════════════
def build_front(shell, cav):
    f = shell ^ big_box(SPLIT_Z, T + 5)
    c = P.BUTTON_CLEARANCE
    inner_clip = cav

    # bosses + gussets
    add = M()
    for bx, by in BOSSES:
        add += cyl_z(bx, by, P.BOSS_OD / 2, PCB_TOP, CEIL + 1.0)
        sx, sy = np.sign(bx), np.sign(by)
        add += box(min(bx, sx * (CI_W2 + 0.8)), max(bx, sx * (CI_W2 + 0.8)), by - 0.6, by + 0.6, PCB_TOP + 1.0, CEIL + 0.5)
        add += box(bx - 0.6, bx + 0.6, min(by, sy * (CI_H2 + 0.8)), max(by, sy * (CI_H2 + 0.8)), PCB_TOP + 1.0, CEIL + 0.5)
    f += add ^ inner_clip

    cut = M()
    for i, (bx, by) in enumerate(BOSSES):
        if i not in P.PCB_PIN_BOSSES:
            cut += cyl_z(bx, by, P.BOSS_HOLE_D / 2, PCB_TOP - 1, PCB_TOP + P.BOSS_HOLE_DEPTH)
    # tongue rebate
    cut += ext(CI.offset(P.LIP_T + P.LIP_CLEARANCE) - CI.offset(-0.3), SPLIT_Z - 1, SPLIT_Z + P.LIP_H + P.LIP_CLEARANCE)
    # pry notch (bottom seam)
    cut += box(-P.PRY_NOTCH_W / 2, P.PRY_NOTCH_W / 2, -H2 - 1, -CI_H2 - P.LIP_T - P.LIP_CLEARANCE + 0.01, SPLIT_Z - 0.1, SPLIT_Z + 0.8)
    # D-pad
    hs = P.BUTTON_SIZE + 2 * c
    for x, y in DPAD:
        cut += ext(rrect(hs, hs, P.BUTTON_CORNER_R + c, x, y), CEIL - 1, T + 2)
    arm = hs + 2.8
    span = 2 * S + arm
    cross = (rrect(arm, span, 2.0) + rrect(span, arm, 2.0)).offset(1.2, JoinType.Round).offset(-1.2, JoinType.Round)
    cut += ext(cross.translate(P.DPAD_CENTER), T - P.RECESS_DEPTH, T + 2)
    # A/B
    rr = P.BUTTON_DIAMETER / 2 + c
    for x, y in P.AB_POS:
        cut += ext(circ(rr, x, y), CEIL - 1, T + 2)
    pill = (circ(rr + 1.4, *P.AB_POS[0]) + circ(rr + 1.4, *P.AB_POS[1])).hull()
    cut += ext(pill, T - P.RECESS_DEPTH, T + 2)
    # display window (+ soft 0.4 chamfer) and bezel-flange rebate
    ww, wh = P.DISPLAY_WINDOW
    cx, cy = P.DISPLAY_WINDOW_C
    win = rrect(ww, wh, P.DISPLAY_WINDOW_R)
    cut += ext(win.translate((cx, cy)), CEIL - 1, T + 2)
    L = 1.4
    cut += win.extrude(L, scale_top=((ww + 2 * L) / ww, (wh + 2 * L) / wh)).translate((cx, cy, T - 0.4))
    fw, fh = P.BEZEL_FLANGE
    cut += ext(rrect(fw + 2 * P.BEZEL_CLEARANCE, fh + 2 * P.BEZEL_CLEARANCE, 4.0 + P.BEZEL_CLEARANCE, cx, cy),
               CEIL - 0.05, CEIL + P.BEZEL_FLANGE_T)
    if P.CHARGE_ICON:
        cut += charge_icon_cut()
    f -= cut

    # snap bumps on the rebate face (left/right)
    xr = CI_W2 + P.LIP_T + P.LIP_CLEARANCE
    zs = SPLIT_Z + P.LIP_H * 0.55
    for s in (-1, 1):
        for sy in P.SNAP_YS:
            f += cyl_y(s * (xr + 0.6 - P.SNAP_BUMP), zs, 0.6, sy - P.SNAP_LEN / 2, sy + P.SNAP_LEN / 2)
    # locating pins (screwless PCB mount)
    for i in P.PCB_PIN_BOSSES:
        bx, by = BOSSES[i]
        zt = PCB_TOP - (P.MAIN_PCB_T - 0.2)
        f += cyl_z(bx, by, P.PCB_PIN_D / 2, zt + 0.4, PCB_TOP + 0.5) + M.cylinder(0.4, P.PCB_PIN_D / 2 - 0.4, P.PCB_PIN_D / 2, circular_segments=SEG).translate((bx, by, zt))
    return f

# ════════════════════════════ back shell ════════════════════════════
def build_back(shell, cav):
    b = shell ^ big_box(-5, SPLIT_Z)
    b += ext(CI.offset(P.LIP_T) - CI.offset(-0.2), SPLIT_Z - 0.5, SPLIT_Z + P.LIP_H)
    floor_clip = cav ^ big_box(-5, max(SPLIT_Z, PCB_BOT))
    add, cut = M(), M()

    # snap grooves
    xr = CI_W2 + P.LIP_T + P.LIP_CLEARANCE
    zs = SPLIT_Z + P.LIP_H * 0.55
    for s in (-1, 1):
        for sy in P.SNAP_YS:
            cut += cyl_y(s * (xr + 0.6 - P.SNAP_BUMP), zs, 0.6 + P.LIP_CLEARANCE, sy - P.SNAP_LEN / 2 - 0.5, sy + P.SNAP_LEN / 2 + 0.5)

    # PCB support ledges (45° corbels): clamp the main PCB against the front bosses when closed
    zt, rch, hw = PCB_BOT - P.PCB_CLAMP_GAP, P.PCB_LEDGE_REACH, P.PCB_LEDGE_W / 2
    def corbel(a0, a1, b_wall, b_dir, along_x):
        # slab on top, tapering to the wall below
        def bx(b0, b1, z0, z1):
            b0, b1 = sorted((b0, b1))
            return box(a0, a1, b0, b1, z0, z1) if along_x else box(b0, b1, a0, a1, z0, z1)
        top = bx(b_wall - b_dir * 0.6, b_wall + b_dir * rch, zt - 0.8, zt)
        root = bx(b_wall - b_dir * 0.6, b_wall + b_dir * 0.05, zt - 0.8 - rch, zt)
        return M.batch_hull([top, root])
    for sx in (-1, 1):
        for y in P.PCB_LEDGE_SIDE_Y:
            add += corbel(y - hw, y + hw, sx * CI_W2, -sx, False)
    for x in P.PCB_LEDGE_TOP_X:
        add += corbel(x - hw, x + hw, CI_H2, -1, True)
    for x in P.PCB_LEDGE_BOTTOM_X:
        add += corbel(x - hw, x + hw, -CI_H2, 1, True)

    # USB-C: ESP32-C3 and TP4056, both on the bottom edge
    ow, oh = P.USB_C_W + 2 * P.USB_CLEARANCE, P.USB_C_H + 2 * P.USB_CLEARANCE
    for B in (ESP, TP):
        xc = B["xc"]
        cut += chamfered_hole_y(stadium(ow, oh), ow, oh, 0.3, -H2 + B["cb"], -1, xc, PORT_Z, -CI_H2 + 0.5)
        cbw, cbh = PLUG_CB
        cut += prism_y_neg(rrect(cbw, cbh, cbh / 2 * 0.95), 3).translate((xc, -H2 + B["cb"], PORT_Z))
        cut += prism_y_neg(rrect(cbw, cbh, cbh / 2 * 0.95), 1.4, ((cbw + 2.8) / cbw, (cbh + 2.8) / cbh)).translate((xc, -H2 + 0.4, PORT_Z))
        # cradle: ledge rails, side guides, rear stop
        x0, x1 = xc - B["w"] / 2, xc + B["w"] / 2
        top = B["zb"] + B["t"]
        for xe, s in ((x0, -1), (x1, 1)):
            SL = P.BOARD_SIDE_SLACK
            r0, r1 = sorted((xe + s * SL, xe - s * 2.2))
            add += box(r0, r1, B["y0"] + 1.0, B["y1"] - 0.5, FLOOR - 0.5, B["zb"])
            g0, g1 = sorted((xe + s * SL, xe + s * (SL + 1.2)))
            add += box(g0, g1, B["y0"] + 3.0, B["y1"] - 3.0, FLOOR - 0.5, top + 0.8)
        add += box(x0 + 1.5, x1 - 1.5, B["stop0"], B["stop1"], FLOOR - 0.5, top + 1.0)

    # battery: four low L-ribs (cell lifts out, never clamped)
    e, t, h, leg = BAT_ENV, P.BATTERY_RIB_T, FLOOR + P.BATTERY_RIB_H, 6.0
    for (cx, sx) in ((e["x0"], 1), (e["x1"], -1)):
        for (cy, sy) in ((e["y0"], 1), (e["y1"], -1)):
            xa, xb = sorted((cx - sx * t, cx + sx * leg))
            ya, yb = sorted((cy - sy * t, cy))
            add += box(xa, xb, ya, yb, FLOOR - 0.5, h)
            xa, xb = sorted((cx - sx * t, cx))
            ya, yb = sorted((cy - sy * t, cy + sy * leg))
            add += box(xa, xb, ya, yb, FLOOR - 0.5, h)

    # IR LED: window + snap-in U cradle + rear stop
    D = 2 * LED_R
    cut += chamfered_hole_y(circ(LED_R), D, D, P.IR_WINDOW_CHAMFER, H2, +1, P.IR_LED_X, IR_Z, CI_H2 - 0.5)
    ow_ = LED_R + 1.2
    u = box(P.IR_LED_X - ow_, P.IR_LED_X + ow_, LED_FLANGE_Y, CI_H2 + 0.3, FLOOR - 0.5, IR_Z + 1.0)
    u -= cyl_y(P.IR_LED_X, IR_Z, LED_R, LED_FLANGE_Y - 1, CI_H2 + 1)
    u -= box(P.IR_LED_X - D * 0.42, P.IR_LED_X + D * 0.42, LED_FLANGE_Y - 1, CI_H2 + 1, IR_Z, IR_Z + 5)
    add += u
    st1 = LED_FLANGE_Y - 1.0 - 0.3
    stop = box(P.IR_LED_X - ow_, P.IR_LED_X + ow_, st1 - 1.4, st1, FLOOR - 0.5, IR_Z + 1.5)
    stop -= box(P.IR_LED_X - 1.8, P.IR_LED_X + 1.8, st1 - 2, st1 + 1, IR_Z - 1.2, IR_Z + 5)
    add += stop

    # IR receiver: window (same Ø as LED, symmetric) + pocket (open to +x for leads)
    cut += chamfered_hole_y(circ(LED_R), D, D, P.IR_WINDOW_CHAMFER, H2, +1, P.IR_RX_X, IR_Z, CI_H2 - 0.5)
    add += box(RX["x0"], RX["x1"], RX["y0"], CI_H2 + 0.3, FLOOR - 0.5, RX["z0"])
    cut += box(RX["x0"] - 0.2, RX["x1"] + 0.2, CI_H2 - 1.0, CI_H2 + 0.02, RX["z0"], RX["z1"] + 0.2)   # relief in inner fillet
    q = P.SMALL_PART_SLACK
    add += box(RX["x0"] - q - 1.2, RX["x0"] - q, RX["y0"] - q - 1.2, CI_H2 + 0.3, FLOOR - 0.5, RX["z0"] + 4.0)
    add += box(RX["x0"] - q - 1.2, RX["x1"] - 2.0, RX["y0"] - q - 1.2, RX["y0"] - q, FLOOR - 0.5, RX["z0"] + 4.0)

    # power switch (right side, on the feature line)
    if P.POWER_SWITCH:
        sw_w, sw_h = P.SW_ACT[0] + P.SW_TRAVEL + 0.6, P.SW_ACT[1] + 0.6
        slot = stadium(sw_w, sw_h)
        cut += prism_x_pos(slot, 6).translate((CI_W2 - 1, P.SW_Y, PORT_Z))
        L = 1.4
        cut += prism_x_pos(slot, L, ((sw_w + 2 * L) / sw_w, (sw_h + 2 * L) / sw_h)).translate((W2 - 0.4, P.SW_Y, PORT_Z))
        ped = box(SW["x0"], SW["x1"], SW["y0"], SW["y1"], FLOOR - 0.5, SW["z0"])
        ped -= box(SW["x0"] + 1.0, SW["x1"] - 1.0, P.SW_Y - 3.2, P.SW_Y + 3.2, FLOOR, SW["z0"] + 1)   # pin clearance
        add += ped
        for s in (-1, 1):
            q = P.SMALL_PART_SLACK
            ya, yb = sorted((P.SW_Y + s * (P.SW_BODY[0] / 2 + q), P.SW_Y + s * (P.SW_BODY[0] / 2 + q + 1.2)))
            add += box(SW["x0"], CI_W2 + 0.4, ya, yb, FLOOR - 0.5, SW["z1"] - 1.0)
        add += box(SW["x0"] - q - 1.2, SW["x0"] - q, P.SW_Y - 3.0, P.SW_Y + 3.0, FLOOR - 0.5, SW["z0"] + 1.5)

    b += add ^ floor_clip
    b -= cut
    return b

# ════════════════════════════ charge icon + ESP port cap ════════════════════════════
ICON_Z0 = SPLIT_Z + 0.45                      # flat band of the bottom edge, front shell
ICON_Z1 = T - P.FRONT_EDGE_R - 0.15
ICON_H = min(P.CHARGE_ICON_H, ICON_Z1 - ICON_Z0)
ICON_ZC = (ICON_Z0 + ICON_Z1) / 2

def bolt_cs(h):
    pts = [(0.10, 0.50), (-0.25, -0.05), (-0.02, -0.05), (-0.10, -0.50), (0.25, 0.07), (0.02, 0.07)]
    pts = [(x * h, z * h) for x, z in pts]
    a = sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(pts, pts[1:] + pts[:1]))
    if a < 0:
        pts = pts[::-1]
    return CS([pts]).offset(-0.08, JoinType.Round).offset(0.08, JoinType.Round)

def charge_icon_cut():
    L = P.CHARGE_ICON_DEPTH + 1.5
    return prism_y_neg(bolt_cs(ICON_H), L).translate((TP["xc"], -H2 + P.CHARGE_ICON_DEPTH, ICON_ZC))

def build_usb_cap(outer):
    B = ESP
    c = P.USB_CAP_CLEARANCE
    cbw, cbh = PLUG_CB
    y_face, y_cb = -H2 - 2.0, -H2 + B["cb"]
    plate = prism_y_neg(rrect(cbw - 2 * c, cbh - 2 * c, (cbh - 2 * c) / 2 * 0.95), y_cb - y_face).translate((B["xc"], y_cb, PORT_Z))
    plate = plate ^ outer                                   # follows the outer skin → flush
    ow, oh = P.USB_C_W + 2 * P.USB_CLEARANCE - 0.1, P.USB_C_H + 2 * P.USB_CLEARANCE - 0.1
    neck_len = B["y_conn"] - y_cb - 0.05
    neck = prism_y_neg(stadium(ow, oh), neck_len + 0.2).translate((B["xc"], y_cb + neck_len, PORT_Z))
    iw, ih = P.USB_C_INNER[0] - 2 * P.USB_CAP_SLEEVE_FIT, P.USB_C_INNER[1] - 2 * P.USB_CAP_SLEEVE_FIT
    y_s0 = y_cb + neck_len
    sleeve = prism_y_neg(stadium(iw, ih), P.USB_CAP_SLEEVE_LEN + 0.1).translate((B["xc"], y_s0 + P.USB_CAP_SLEEVE_LEN, PORT_Z))
    tw, th = P.USB_CAP_TONGUE_SLOT
    sleeve -= prism_y_neg(rrect(tw, th, 0.2), P.USB_CAP_SLEEVE_LEN + 1).translate((B["xc"], y_s0 + P.USB_CAP_SLEEVE_LEN + 0.5, PORT_Z))
    cap = plate + neck + sleeve
    # fingernail notch on the outer end of the plate
    nx = B["xc"] + (cbw / 2 - c) - 0.3
    cap -= cyl_y(nx, PORT_Z, 1.1, -H2 - 1, -H2 + 0.7)
    return cap

# ════════════════════════════ bezel + caps ════════════════════════════
def build_bezel():
    ww, wh = P.DISPLAY_WINDOW
    cx, cy = P.DISPLAY_WINDOW_C
    c = P.BEZEL_CLEARANCE
    plate = ext(rrect(ww - 2 * c, wh - 2 * c, P.DISPLAY_WINDOW_R - c, cx, cy), CEIL, T)
    fl = ext(rrect(*P.BEZEL_FLANGE, 4.0, cx, cy), CEIL, CEIL + P.BEZEL_FLANGE_T)
    vw, vh = P.OLED_VIEW
    view = rrect(vw, vh, 1.0)
    hole = ext(view.translate((cx, cy)), CEIL - 1, T + 1)
    L = 1.6
    hole += view.extrude(L, scale_top=((vw + 2 * L) / vw, (vh + 2 * L) / vh)).translate((cx, cy, T - 0.6))
    return (plate + fl) - hole

def rounded_cap(cs_fn, top_z, r, z0):
    """Convex hull of slices → stem whose top edge is rounded with radius r."""
    sl = [ext(cs_fn(0), z0, top_z - r)]
    for a in np.linspace(0, math.pi / 2, 8):
        off = r * (1 - math.cos(a))
        z = top_z - r + r * math.sin(a)
        sl.append(ext(cs_fn(-off), z - 0.001, z))
    return M.batch_hull(sl)

def build_caps():
    z0 = PCB_TOP + P.TACT_H
    zf = z0 + P.BUTTON_FLANGE_T
    top = T + P.BUTTON_PROTRUDE
    caps = []
    for (x, y) in DPAD:
        s = P.BUTTON_SIZE
        stem = rounded_cap(lambda o: rrect(s + 2 * o, s + 2 * o, max(P.BUTTON_CORNER_R + o, 0.2)), top, P.BUTTON_TOP_R, z0)
        fl = ext(rrect(P.DPAD_FLANGE, P.DPAD_FLANGE, 1.0), z0, zf)
        caps.append(((stem + fl).translate((x, y, 0)), "dpad"))
    for (x, y) in P.AB_POS:
        d = P.BUTTON_DIAMETER
        stem = rounded_cap(lambda o: circ(d / 2 + o), top, min(P.BUTTON_TOP_R * 1.6, d / 2 - 0.5), z0)
        fl = ext(circ(P.AB_FLANGE_D / 2), z0, zf)
        caps.append(((stem + fl).translate((x, y, 0)), "ab"))
    return caps

# ════════════════════════════ main PCB + dummies ════════════════════════════
def pcb_outline():
    o = CI.offset(-P.PCB_CLEARANCE)
    nl, nd = P.PCB_WIRE_NOTCH
    for s in (-1, 1):
        xe = s * (CI_W2 - P.PCB_CLEARANCE)
        o -= rrect(2 * nd, nl, 1.0, xe, P.PCB_WIRE_NOTCH_Y)
    for bx, by in BOSSES:
        o -= circ(1.1, bx, by)
    return o

def components():
    C = {}
    C["main_pcb"] = ext(pcb_outline(), PCB_BOT, PCB_TOP)
    for i, (x, y) in enumerate(DPAD + list(P.AB_POS)):
        ts = P.TACT_SIZE
        C[f"tact_{i}"] = box(x - ts / 2, x + ts / 2, y - ts / 2, y + ts / 2, PCB_TOP, PCB_TOP + 3.4) + \
            cyl_z(x, y, 1.75, PCB_TOP + 3.4, PCB_TOP + P.TACT_H)
    cx, cy = P.DISPLAY_WINDOW_C
    gz1 = CEIL
    gz0 = gz1 - P.OLED_GLASS[2]
    pz1 = gz0
    pz0 = pz1 - P.OLED_PCB[2]
    C["oled_glass"] = box(cx - P.OLED_GLASS[0] / 2, cx + P.OLED_GLASS[0] / 2, cy - P.OLED_GLASS[1] / 2, cy + P.OLED_GLASS[1] / 2, gz0, gz1)
    pcy = cy - P.OLED_GLASS_OFFSET_Y
    C["oled_pcb"] = box(cx - P.OLED_PCB[0] / 2, cx + P.OLED_PCB[0] / 2, pcy - P.OLED_PCB[1] / 2, pcy + P.OLED_PCB[1] / 2, pz0, pz1)
    hy = pcy + P.OLED_PCB[1] / 2 - 1.3
    C["oled_header"] = box(cx - 5.1, cx + 5.1, hy - 1.27, hy + 1.27, PCB_TOP, pz0)
    for nm, B, comp_h in (("esp32c3", ESP, 1.6), ("tp4056", TP, 1.5)):
        x0, x1 = B["xc"] - B["w"] / 2, B["xc"] + B["w"] / 2
        z1 = B["zb"] + B["t"]
        C[nm] = box(x0, x1, B["y0"], B["y1"], B["zb"], z1) + \
            box(B["xc"] - P.USB_C_W / 2, B["xc"] + P.USB_C_W / 2, B["y_conn"], B["y_conn"] + 7.35, z1, z1 + P.USB_C_H) + \
            box(x0 + 1.5, x1 - 1.5, B["y0"] + 8.0, B["y1"] - 1.0, z1, z1 + comp_h)
        # USB plug fully inserted (overmold envelope)
        cw, ch = P.USB_PLUG_BODY
        oy = B["y_conn"] - P.USB_PLUG_SEAT_GAP - 0.02
        C[nm + "_usb_plug"] = prism_y_neg(rrect(cw, ch, ch / 2 * 0.9), 18).translate((B["xc"], oy, PORT_Z))
    C["battery"] = box(BAT["x0"], BAT["x1"], BAT["y0"], BAT["y1"], BAT["z0"], BAT["z1"])
    C["battery_pcm_wires"] = box(BAT["x0"] - P.BATTERY_WIRE_SPACE, BAT["x0"], (BAT["y0"] + BAT["y1"]) / 2 - 4, (BAT["y0"] + BAT["y1"]) / 2 + 4, FLOOR + 0.5, FLOOR + 3.0)
    r = P.IR_LED_DIAMETER / 2
    C["ir_led"] = cyl_y(P.IR_LED_X, IR_Z, r, LED_FLANGE_Y, LED_TIP_Y - r) + \
        M.sphere(r, SEG).translate((P.IR_LED_X, LED_TIP_Y - r, IR_Z)) + \
        cyl_y(P.IR_LED_X, IR_Z, P.IR_LED_FLANGE_D / 2, LED_FLANGE_Y - 1.0, LED_FLANGE_Y) + \
        box(P.IR_LED_X - 1.6, P.IR_LED_X + 1.6, LED_FLANGE_Y - 4.5, LED_FLANGE_Y - 1.0, IR_Z - 0.3, IR_Z + 0.3)
    C["ir_rx"] = box(RX["x0"], RX["x1"], RX["y0"], RX["y1"], RX["z0"], RX["z1"]) + \
        (M.sphere(P.IR_RX_DOME_D / 2, SEG).scale((1, 2 * P.IR_RX_DOME_H / P.IR_RX_DOME_D, 1)) ^ box(-5, 5, 0, 5, -5, 5)).translate((P.IR_RX_X, RX["y1"], IR_Z)) + \
        box(RX["x1"], RX["x1"] + 3.0, RX["y0"] + 1.0, RX["y1"] - 1.0, IR_Z - 0.3, IR_Z + 0.3)
    if P.POWER_SWITCH:
        ay, az, al = P.SW_ACT
        C["power_switch"] = box(SW["x0"], SW["x1"], SW["y0"], SW["y1"], SW["z0"], SW["z1"]) + \
            box(SW["x1"], SW["x1"] + al, P.SW_Y - ay / 2 - P.SW_TRAVEL / 2, P.SW_Y + ay / 2 + P.SW_TRAVEL / 2, PORT_Z - az / 2, PORT_Z + az / 2)
    for i, (bx, by) in enumerate(BOSSES):
        if i in P.PCB_PIN_BOSSES:
            continue
        C[f"screw_head_{i}"] = cyl_z(bx, by, P.SCREW_HEAD_D / 2, PCB_BOT - P.SCREW_HEAD_H, PCB_BOT)
    return C

def envelopes(C):
    """Required free space around parts (checked against everything else)."""
    Ev = {}
    e = BAT_ENV
    Ev["battery_clearance"] = (box(e["x0"], e["x1"], e["y0"], e["y1"], FLOOR + 0.05, BAT["z1"] + P.BATTERY_CLEARANCE), {"battery", "battery_pcm_wires"})
    Ev["pcb_underside_keepout"] = (ext(CI.offset(-P.PCB_CLEARANCE - P.PCB_LEDGE_REACH) - rrect(60, 12, 0.1, 0, CI_H2 - 3.0), KEEPOUT_Z, PCB_BOT) - M().translate((0, 0, 0)),
                                   {f"screw_head_{i}" for i in range(4)})
    Ev["wire_channel_left"] = (box(-CI_W2 + 0.3, -CI_W2 + 1.8, -28, 26, FLOOR + 1.4, FLOOR + 5.5), set())
    Ev["wire_channel_top"] = (box(-20, 18, BAT_ENV["y1"] + P.BATTERY_RIB_T + 0.3, LED_FLANGE_Y - 4.6, FLOOR + 0.3, FLOOR + 4.0), set())
    for s, nm in ((-1, "L"), (1, "R")):
        xe = s * (CI_W2 - P.PCB_CLEARANCE - 1.2)
        Ev[f"wire_riser_{nm}"] = (box(xe - 1.0, xe + 1.0, P.PCB_WIRE_NOTCH_Y - 2.5, P.PCB_WIRE_NOTCH_Y + 2.5, FLOOR + 3.0, PCB_TOP + 1.0), set())
    for nm in ("esp32c3", "tp4056"):
        B = ESP if nm == "esp32c3" else TP
        Ev[nm + "_clearance"] = (box(B["xc"] - B["w"] / 2 - 0.25, B["xc"] + B["w"] / 2 + 0.25, B["y0"] + 0.5, B["y1"] + 0.25,
                                     B["zb"] + 0.01, B["zb"] + B["t"] + 3.3), {nm})
    return Ev

# ════════════════════════════ validation ════════════════════════════
def vol(m):
    return 0.0 if m.is_empty() else m.volume()

def validate(parts, C, caps, bezel, usb_cap=None):
    res = []
    def rec(name, ok, detail):
        res.append(dict(check=name, ok=bool(ok), detail=detail))
    TOL = 0.02  # mm³ (tessellation noise)
    shells = {"front_shell": parts["front_shell"], "back_shell": parts["back_shell"]}
    # 1. components vs shells
    allowed_shell = {("screw_head_0", "front_shell"), ("screw_head_1", "front_shell"), ("screw_head_2", "front_shell"), ("screw_head_3", "front_shell")}
    for cn, cm in C.items():
        for sn, sm in shells.items():
            if (cn, sn) in allowed_shell:
                continue
            v = vol(cm ^ sm)
            if v > TOL:
                rec(f"{cn} vs {sn}", False, f"intersects {v:.3f} mm³")
    # 2. component pairs
    names = list(C)
    allowed = {("main_pcb", "oled_header")}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if (a, b) in allowed or (b, a) in allowed:
                continue
            v = vol(C[a] ^ C[b])
            if v > TOL:
                rec(f"{a} vs {b}", False, f"intersects {v:.3f} mm³")
    # 3. clearance envelopes
    for en, (em, ignore) in envelopes(C).items():
        bad = []
        for sn, sm in shells.items():
            v = vol(em ^ sm)
            if v > TOL:
                bad.append(f"{sn} {v:.2f}")
        for cn, cm in C.items():
            if cn in ignore or cn.endswith("_usb_plug"):
                continue
            v = vol(em ^ cm)
            if v > TOL:
                bad.append(f"{cn} {v:.2f}")
        rec(f"free space: {en}", not bad, "clear" if not bad else "blocked by " + ", ".join(bad))
    # 4. caps + bezel vs shells and each other
    for i, (cm, kind) in enumerate(caps):
        for sn, sm in shells.items():
            v = vol(cm ^ sm)
            if v > TOL:
                rec(f"button_cap_{i} vs {sn}", False, f"{v:.3f} mm³")
        for cn in ("oled_glass", "oled_pcb", "main_pcb"):
            v = vol(cm ^ C[cn])
            if v > TOL:
                rec(f"button_cap_{i} vs {cn}", False, f"{v:.3f} mm³")
    for i in range(len(caps)):
        for j in range(i + 1, len(caps)):
            if vol(caps[i][0] ^ caps[j][0]) > TOL:
                rec(f"button_cap_{i} vs button_cap_{j}", False, "flanges overlap")
    for sn, sm in shells.items():
        v = vol(bezel ^ sm)
        if v > TOL:
            rec(f"bezel vs {sn}", False, f"{v:.3f} mm³")
    if usb_cap is not None:
        for sn, sm in shells.items():
            v = vol(usb_cap ^ sm)
            rec(f"ESP32 port cap vs {sn}", v <= TOL, f"overlap {v:.3f} mm³")
        # receptacle dummy is a solid box; only the part *outside* the receptacle mouth must be free
        rx = box(ESP["xc"] - 6, ESP["xc"] + 6, ESP["y_conn"], ESP["y1"] + 1, 0, SPLIT_Z)
        v = vol((usb_cap - rx) ^ C["esp32c3"])
        rec("ESP32 port cap stops at receptacle face", v <= TOL, f"overlap {v:.3f} mm³")
        ins = vol(usb_cap ^ rx)
        rec("ESP32 port cap sleeve enters receptacle", ins > 1.0, f"{ins:.1f} mm³ inside the USB-C shell")
        bb = usb_cap.bounding_box()
        rec("ESP32 port cap flush (no part beyond outer skin)", bb[1] >= -H2 - 0.05, f"outermost y {bb[1]:.2f} vs skin {-H2:.2f}")
    if P.CHARGE_ICON:
        rest = P.WALL_THICKNESS - P.LIP_T - P.LIP_CLEARANCE - P.CHARGE_ICON_DEPTH
        rec("wall behind charge icon ≥ 0.6", rest >= 0.6, f"{rest:.2f} mm (icon {ICON_H:.1f} mm tall, {P.CHARGE_ICON_DEPTH} deep)")
        rec("charge icon clear of seam", ICON_ZC - ICON_H / 2 >= SPLIT_Z + 0.4, f"icon z {ICON_ZC - ICON_H/2:.2f}–{ICON_ZC + ICON_H/2:.2f}, seam {SPLIT_Z:.2f}")
    v = vol(parts["front_shell"] ^ parts["back_shell"])
    rec("front shell vs back shell (assembled)", v <= TOL, f"overlap {v:.3f} mm³")
    # 5. numeric checks
    play = CEIL - (PCB_TOP + P.TACT_H + P.BUTTON_FLANGE_T)
    rec("button play under ceiling (≥0.1, ≤0.4)", 0.1 <= play + 1e-6 <= 0.4, f"{play:.2f} mm (tact travel 0.25 free)")
    rec("D-pad flange < pitch", P.DPAD_FLANGE < S, f"{P.DPAD_FLANGE} < {S}")
    dab = math.dist(*P.AB_POS)
    rec("A/B flange < spacing", P.AB_FLANGE_D < dab, f"{P.AB_FLANGE_D} < {dab:.2f}")
    web = dab - P.BUTTON_DIAMETER - 2 * P.BUTTON_CLEARANCE
    rec("A/B hole web ≥ 1.0", web >= 1.0, f"{web:.2f} mm")
    for nm, B in (("ESP32", ESP), ("TP4056", TP)):
        rest = P.WALL_THICKNESS - B["cb"]
        rec(f"{nm} USB wall around opening ≥ 0.8", rest >= 0.8 - 1e-6, f"{rest:.2f} mm (plug counterbore {B['cb']:.2f} deep)")
    rec("bridge above USB counterbore ≥ 1.0", SPLIT_Z - (PORT_Z + PLUG_CB[1] / 2) >= 0.99, f"{SPLIT_Z - (PORT_Z + PLUG_CB[1] / 2):.2f} mm")
    rec("front wall at tongue rebate ≥ 1.0", P.WALL_THICKNESS - P.LIP_T - P.LIP_CLEARANCE >= 1.0, f"{P.WALL_THICKNESS - P.LIP_T - P.LIP_CLEARANCE:.2f} mm")
    rec("boss wall around hole ≥ 1.5", (P.BOSS_OD - P.BOSS_HOLE_D) / 2 >= 1.5, f"{(P.BOSS_OD - P.BOSS_HOLE_D) / 2:.2f} mm")
    rec("boss hole blind (does not pierce face)", PCB_TOP + P.BOSS_HOLE_DEPTH < T - 1.0, f"hole top {PCB_TOP + P.BOSS_HOLE_DEPTH:.2f} < {T - 1:.2f}")
    rec("OLED stack fits under bezel", OLED_STACK <= CEIL - PCB_TOP + 1e-6, f"{OLED_STACK:.2f} ≤ {CEIL - PCB_TOP:.2f} mm (shim the header if lower)")
    rec("battery top gap to PCB keepout", KEEPOUT_Z - BAT["z1"] >= P.BATTERY_CLEARANCE - 1e-6, f"{KEEPOUT_Z - BAT['z1']:.2f} mm")
    slab = ext(CI.offset(-P.PCB_CLEARANCE), PCB_BOT - P.PCB_CLAMP_GAP - 0.2, PCB_BOT - P.PCB_CLAMP_GAP - 0.02)
    sup = vol(slab ^ parts["back_shell"]) / 0.18
    rec("PCB ledges really reach the PCB underside", sup > 30, f"{sup:.0f} mm² of support area under the board")
    rec("PCB clamped by back-shell ledges (gap ≤ 0.2)", 0 <= P.PCB_CLAMP_GAP <= 0.2, f"{P.PCB_CLAMP_GAP} mm, edge overlap {P.PCB_LEDGE_REACH - P.PCB_CLEARANCE:.1f} mm, {2*len(P.PCB_LEDGE_SIDE_Y)+len(P.PCB_LEDGE_TOP_X)+len(P.PCB_LEDGE_BOTTOM_X)} ledges")
    rec("PCB locating pins fit holes", P.PCB_PIN_D < 2.2, f"pin Ø{P.PCB_PIN_D} in Ø2.2, {len(P.PCB_PIN_BOSSES)} pins + {4-len(P.PCB_PIN_BOSSES)} optional screws")
    return res

# ════════════════════════════ SVG template ════════════════════════════
def write_svg():
    o = pcb_outline()
    pad = 5
    x0, y0, x1, y1 = -CI_W2 - pad, -CI_H2 - pad, CI_W2 + pad, CI_H2 + pad
    w, h = x1 - x0, y1 - y0
    def tr(x, y):
        return x - x0, y1 - y
    paths = []
    for poly in o.to_polygons():
        d = "M " + " L ".join(f"{tr(px, py)[0]:.3f},{tr(px, py)[1]:.3f}" for px, py in poly) + " Z"
        paths.append(d)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
         '<rect width="100%" height="100%" fill="white"/>',
         f'<path d="{" ".join(paths)}" fill="#e8f5e9" stroke="black" stroke-width="0.2" fill-rule="evenodd"/>']
    for i, (bx, by) in enumerate(BOSSES):
        X, Y = tr(bx, by)
        s.append(f'<circle cx="{X}" cy="{Y}" r="1.1" fill="none" stroke="red" stroke-width="0.15"/>')
        s.append(f'<text x="{X+2.4}" y="{Y+0.8}" font-size="1.8" font-family="sans-serif" fill="red">{"pino" if i in P.PCB_PIN_BOSSES else "M2 opc."}</text>')
        s.append(f'<path d="M{X-2},{Y} L{X+2},{Y} M{X},{Y-2} L{X},{Y+2}" stroke="red" stroke-width="0.1"/>')
    for (x, y) in DPAD + list(P.AB_POS):
        X, Y = tr(x, y)
        s.append(f'<rect x="{X-3}" y="{Y-3}" width="6" height="6" fill="none" stroke="#1565c0" stroke-width="0.15"/>')
        s.append(f'<circle cx="{X}" cy="{Y}" r="1.75" fill="none" stroke="#1565c0" stroke-width="0.1"/>')
    cx, cy = P.DISPLAY_WINDOW_C
    pcy = cy - P.OLED_GLASS_OFFSET_Y
    X, Y = tr(cx - P.OLED_PCB[0] / 2, pcy + P.OLED_PCB[1] / 2)
    s.append(f'<rect x="{X}" y="{Y}" width="{P.OLED_PCB[0]}" height="{P.OLED_PCB[1]}" fill="none" stroke="#6a1b9a" stroke-width="0.15" stroke-dasharray="1,0.6"/>')
    X, Y = tr(-CI_W2, CI_H2 - 3.0 + 6)
    s.append(f'<rect x="{tr(-30,0)[0]}" y="{tr(0, CI_H2)[1]}" width="60" height="6" fill="#fff3e0" opacity="0.6"/>')
    s.append(f'<text x="2" y="{h-1.5}" font-size="2.2" font-family="sans-serif">BINI Cat mainboard — FRONT view (component side), 1:1 — red: Ø2.2 M2 holes, blue: 6x6 tact, purple: OLED, orange: no through-hole parts (IR below)</text>')
    s.append('</svg>')
    with open(os.path.join(OUT, "mainboard_template.svg"), "w") as fh:
        fh.write("\n".join(s))

# ════════════════════════════ main ════════════════════════════
def main():
    t0 = time.time()
    print(f"stack: back 0 | floor {FLOOR:.2f} | port/feature line {PORT_Z:.2f} | IR {IR_Z:.2f} | split {SPLIT_Z:.2f} | "
          f"PCB {PCB_BOT:.2f}-{PCB_TOP:.2f} | ceiling {CEIL:.2f} | face {T:.2f}")
    shell, cav, outer = build_shell()
    print(f"shell SDF meshed ({shell.num_tri()} tris) {time.time()-t0:.1f}s")
    front = build_front(shell, cav)
    back = build_back(shell, cav)
    bezel = build_bezel()
    caps = build_caps()
    usb_cap = build_usb_cap(outer) if P.USB_CAP else None
    C = components()
    parts = {"front_shell": front, "back_shell": back}
    print(f"parts built {time.time()-t0:.1f}s")

    for n, m in parts.items():
        print(f"{n}: {len(m.decompose())} body, genus {m.genus()}, {m.volume()/1000:.2f} cm³")
        save(m, n)
    save(bezel, "screen_bezel")
    if usb_cap is not None:
        save(usb_cap, "usb_cap_esp32")
        uc = usb_cap.rotate((90, 0, 0))
        save(uc.translate((0, 0, -uc.bounding_box()[2])), "usb_cap_esp32_FACE_DOWN", "print")
    for i, (cm, kind) in enumerate(caps):
        save(cm, f"button_{kind}_{i}")
    for n, m in C.items():
        save(m, "cmp_" + n)

    # print orientation
    save(front.mirror((0, 0, 1)).translate((0, 0, T)), "front_shell_FACE_DOWN", "print")
    save(back, "back_shell", "print")
    save(bezel.mirror((0, 0, 1)).translate((0, 0, T)), "screen_bezel_FACE_DOWN", "print")
    zc = PCB_TOP + P.TACT_H
    dp = caps[0][0].translate((-DPAD[0][0], -DPAD[0][1], -zc))
    ab = caps[4][0].translate((-P.AB_POS[0][0], -P.AB_POS[0][1], -zc))
    save(M.batch_boolean([dp.translate((i * 10, 0, 0)) for i in range(4)] +
                         [ab.translate((i * 11, 12, 0)) for i in range(2)], mf.OpType.Add), "buttons_x6", "print")
    write_svg()

    res = validate(parts, C, caps, bezel, usb_cap)
    fails = [r for r in res if not r["ok"]]
    info = dict(T=T, SPLIT_Z=SPLIT_Z, PORT_Z=PORT_Z, IR_Z=IR_Z, PCB_BOT=PCB_BOT, PCB_TOP=PCB_TOP, CEIL=CEIL,
                bosses=BOSSES, battery=BAT, esp=ESP, tp=TP,
                volumes={n: round(m.volume() / 1000, 2) for n, m in parts.items()},
                overall=[round(v, 2) for v in (np.array(to_trimesh(front + back).bounds[1]) - np.array(to_trimesh(front + back).bounds[0]))])
    with open(os.path.join(OUT, "validation.json"), "w") as fh:
        json.dump(dict(info=info, checks=res), fh, indent=1, default=float)
    lines = ["# Validation", "", f"Overall size (incl. ears): {info['overall'][0]} x {info['overall'][1]} x {info['overall'][2]} mm", ""]
    lines += ["| check | result | detail |", "|---|---|---|"]
    for r in res:
        lines.append(f"| {r['check']} | {'PASS' if r['ok'] else '**FAIL**'} | {r['detail']} |")
    if not any("vs" in r["check"] and not r["ok"] for r in res):
        lines.append("| no component ↔ component / component ↔ shell intersections | PASS | all pairs checked |")
    with open(os.path.join(OUT, "validation.md"), "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\n{len(res)} checks, {len(fails)} failed — {time.time()-t0:.1f}s")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
