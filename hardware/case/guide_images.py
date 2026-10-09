"""python guide_images.py → out/guide/pcb_front.png, pcb_back.png, back_shell.png (true scale, from real geometry)"""
import os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
import build as B, params as P

G = os.path.join(B.OUT, "guide"); os.makedirs(G, exist_ok=True)
COL = {"GPIO 0": "#2a9d8f", "GPIO 1": "#457b9d", "GPIO 3": "#6a4c93", "GPIO 4": "#b5179e", "GPIO 5": "#e63946",
       "GPIO 10": "#7b8794", "SDA→GPIO 8": "#00a6fb", "SCL→GPIO 9": "#e09f00", "VCC→3V3": "#f77f00", "GND": "#111"}
BTN = [("CIMA", "GPIO 0", B.DPAD[0]), ("BAIXO", "GPIO 1", B.DPAD[1]), ("ESQ", "GPIO 3", B.DPAD[2]), ("DIR", "GPIO 4", B.DPAD[3]),
       ("A", "GPIO 5", P.AB_POS[1]), ("B", "GPIO 10", P.AB_POS[0])]
cx, cy = P.DISPLAY_WINDOW_C; pcy = cy - P.OLED_GLASS_OFFSET_Y
HY = pcy + P.OLED_PCB[1] / 2 - 1.3
HDR = [cx - 3.81, cx - 1.27, cx + 1.27, cx + 3.81]
NOTCH = B.CI_W2 - P.PCB_CLEARANCE - 1.3

def pcb(ax, m):
    for poly in B.pcb_outline().to_polygons():
        p = np.array(poly); ax.fill(m * p[:, 0], p[:, 1], fc="#cfe8d2", ec="#2e7d32", lw=1.5, zorder=1)
    xs = np.arange(-22.86, 23, 2.54); ys = np.arange(-33.02, 34, 2.54)
    X, Y = np.meshgrid(xs, ys); ax.plot(X.ravel(), Y.ravel(), ".", color="#9cc5a1", ms=2.2, zorder=1.1)
    for (bx, by) in B.BOSSES:
        ax.add_patch(Circle((m * bx, by), 1.1, fc="w", ec="#c62828", lw=1.4, zorder=2))
def fin(ax, title, path):
    ax.set_aspect("equal"); ax.set_xlim(-37, 37); ax.set_ylim(-44, 40); ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.savefig(path, dpi=120, facecolor="white"); plt.close()

# ── front (component side) ──
fig, ax = plt.subplots(figsize=(9, 10.5)); pcb(ax, 1)
ax.add_patch(Rectangle((cx - P.OLED_PCB[0] / 2, pcy - P.OLED_PCB[1] / 2), P.OLED_PCB[0], P.OLED_PCB[1], fc="#3b3b55", ec="k", zorder=3))
ax.add_patch(Rectangle((cx - 10.85, cy - 5.45), 21.7, 10.9, fc="#111", ec="k", zorder=4))
ax.text(cx, cy, "OLED 0.96\"", color="w", ha="center", va="center", fontsize=10, zorder=5)
for x in HDR: ax.add_patch(Circle((x, HY), 0.7, fc="#f2c200", ec="k", lw=0.6, zorder=5))
ax.annotate("4 pinos da OLED\nsoldados na placa", (cx, HY + 0.8), (cx, HY + 6.5), ha="center", fontsize=9, arrowprops=dict(arrowstyle="->"))
for (n, g, (x, y)) in BTN:
    ax.add_patch(Rectangle((x - 3, y - 3), 6, 6, fc="#555", ec="k", zorder=3)); ax.add_patch(Circle((x, y), 1.75, fc="#ddd", ec="k", lw=0.6, zorder=4))
    for sx in (-1, 1):
        for sy in (-1, 1): ax.add_patch(Circle((x + sx * 3.25, y + sy * 2.25), 0.55, fc="#f2c200", ec="k", lw=0.5, zorder=5))
    ax.text(x, y - 4.6, n, ha="center", va="top", fontsize=8.5, fontweight="bold", color=COL[g])
ax.annotate("furo Ø2.2 (pino-guia\nou parafuso)", (B.BOSSES[1][0] + 1, B.BOSSES[1][1] - 1), (-30, 22), fontsize=8.5, color="#c62828", arrowprops=dict(arrowstyle="->", color="#c62828"))
ax.annotate("entalhe pros fios", (-NOTCH - 0.8, P.PCB_WIRE_NOTCH_Y), (-33.5, -4), fontsize=8.5, arrowprops=dict(arrowstyle="->"))
ax.text(0, -37.5, "Botões e tela ficam DESTE lado. As pernas atravessam a placa e são soldadas no verso.", ha="center", fontsize=9)
fin(ax, "Placa — lado da FRENTE (componentes)", os.path.join(G, "pcb_front.png"))

# ── underside (solder side, mirrored) ──
fig, ax = plt.subplots(figsize=(9, 10.5)); pcb(ax, -1)
gnd_pts = [(-HDR[0], HY)]
for i, (n, g, (x, y)) in enumerate(BTN):
    X = -x
    ax.add_patch(Rectangle((X - 3, y - 3), 6, 6, fc="none", ec="#888", ls="--", lw=0.8, zorder=2))
    for sx in (-1, 1):
        for sy in (-1, 1): ax.add_patch(Circle((X + sx * 3.25, y + sy * 2.25), 0.6, fc="#c9c9c9", ec="k", lw=0.5, zorder=4))
    sig = (X - 3.25, y + 2.25) if X > 0 else (X + 3.25, y + 2.25)
    gnd = (X + 3.25, y - 2.25) if X > 0 else (X - 3.25, y - 2.25)
    ax.add_patch(Circle(sig, 0.75, fc=COL[g], ec="k", lw=0.6, zorder=6)); ax.add_patch(Circle(gnd, 0.75, fc="#111", ec="k", lw=0.6, zorder=6))
    ax.text(X, y, n, ha="center", va="center", fontsize=8, color="#666", zorder=3)
    side = 1 if X > 0 else -1
    j = [k for k, b in enumerate([b for b in BTN if (-b[2][0] > 0) == (X > 0)]) if b[0] == n][0]
    end = (side * (NOTCH + 0.2), P.PCB_WIRE_NOTCH_Y + (4.2 - 2.1 * j if side < 0 else 2.6 - 1.7 * j))
    ax.plot([sig[0], sig[0] + side * (1.5 + 1.2 * j), end[0]], [sig[1], sig[1] + 0.0, end[1]], color=COL[g], lw=2.4, zorder=5, solid_joinstyle="round")
    ax.text(end[0] + side * 1.0, end[1], g, ha="left" if side > 0 else "right", va="center", fontsize=8.5, color=COL[g], fontweight="bold")
    gnd_pts.append(gnd)
order = [0] + sorted(range(1, len(gnd_pts)), key=lambda k: (-gnd_pts[k][1], gnd_pts[k][0]))
chain = [gnd_pts[0], gnd_pts[order[1]]]
rem = [gnd_pts[k] for k in order[2:]]
while rem:
    last = chain[-1]; k = min(range(len(rem)), key=lambda q: (rem[q][0] - last[0]) ** 2 + (rem[q][1] - last[1]) ** 2); chain.append(rem.pop(k))
ax.plot([p[0] for p in chain], [p[1] for p in chain], color="#111", lw=3, zorder=4.5, solid_joinstyle="round")
names = ["GND", "VCC→3V3", "SCL→GPIO 9", "SDA→GPIO 8"]
for k, x in enumerate(HDR):
    X = -x; c = COL[names[k]]
    ax.add_patch(Circle((X, HY), 0.75, fc=c, ec="k", lw=0.6, zorder=6))
    if k > 0:
        end = (-(NOTCH + 0.2), P.PCB_WIRE_NOTCH_Y + 4.2 - 2.1 * (k + 1))
        vx = -18.5 - 1.3 * k
        ax.plot([X, X, vx, vx, end[0]], [HY, HY - 15.5 - 1.2 * k, HY - 15.5 - 1.2 * k, end[1], end[1]], color=c, lw=2.4, zorder=5, solid_joinstyle="round")
        ax.text(end[0] - 1.0, end[1], names[k], ha="right", va="center", fontsize=8.5, color=c, fontweight="bold")
ge = (-(NOTCH + 0.2), P.PCB_WIRE_NOTCH_Y - 3.5)
ax.plot([chain[-1][0], chain[-1][0], ge[0]], [chain[-1][1], ge[1] - 6.5, ge[1] - 6.5], color="#111", lw=3, zorder=4.5)
ax.text(ge[0] - 1.0, ge[1] - 6.5, "GND", ha="right", va="center", fontsize=8.5, fontweight="bold")
ax.text(0, 36.5, "ordem dos pinos da OLED varia: leia o que está escrito na sua", ha="center", fontsize=8.5, color="#555")
ax.text(0, -39.5, "Preto grosso = fio GND pulando de botão em botão.  Bolinha colorida = perna de sinal, 1 fio pra cada.\n"
        "Os fios são encapados, podem cruzar. 11 fios de ~8 cm saem pelos entalhes e vão até o ESP32.", ha="center", fontsize=9, va="top")
fin(ax, "Placa — VERSO (onde você solda), vista espelhada", os.path.join(G, "pcb_back.png"))

# ── back shell with wires ──
back = trimesh.load(os.path.join(B.OUT, "assembly", "back_shell.stl"))
fig, ax = plt.subplots(figsize=(9, 11.5))
def sec(z, **kw):
    s = back.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    for e in s.discrete: ax.fill(e[:, 0], e[:, 1], **kw)
sec(B.PORT_Z, fc="#f3b6c6", ec="none")
ax.add_patch(FancyBboxPatch((-B.CI_W2, -B.CI_H2), 2 * B.CI_W2, 2 * B.CI_H2, boxstyle=f"round,pad=0,rounding_size={B.CI_R}", fc="#fbe9ee", ec="none", zorder=0.5))
s = back.section(plane_origin=[0, 0, B.FLOOR + 0.6], plane_normal=[0, 0, 1])
for e in s.discrete: ax.plot(e[:, 0], e[:, 1], color="#c98aa0", lw=0.6, zorder=1)
def rect(x0, x1, y0, y1, fc, label=None, fs=9, tc="k"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec="k", lw=1, zorder=2))
    if label: ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=fs, color=tc, zorder=3)
T_, E_ = B.TP, B.ESP
rect(T_["xc"] - T_["w"] / 2, T_["xc"] + T_["w"] / 2, T_["y0"], T_["y1"], "#8fb8f0", "TP4056")
rect(E_["xc"] - E_["w"] / 2, E_["xc"] + E_["w"] / 2, E_["y0"], E_["y1"], "#7f8fd0", "ESP32-C3\nSuper Mini")
for D in (T_, E_): rect(D["xc"] - 4.5, D["xc"] + 4.5, D["y_conn"], D["y_conn"] + 7.3, "#d0d0d0", "USB-C", 7)
bt = B.BAT
rect(bt["x0"], bt["x1"], bt["y0"], bt["y1"], "#d9d9de", "BATERIA\n(fita dupla-face embaixo)")
r = P.IR_LED_DIAMETER / 2
rect(P.IR_LED_X - r, P.IR_LED_X + r, B.LED_FLANGE_Y, B.LED_TIP_Y, "#b9a5ff"); ax.text(P.IR_LED_X, B.LED_TIP_Y + 3.2, "LED IR", ha="center", fontsize=8.5)
rx = B.RX
rect(rx["x0"], rx["x1"], rx["y0"], rx["y1"], "#444"); ax.text(B.RX_CX + 1, rx["y1"] + 3.2, "receptor IR", ha="center", fontsize=8.5)
def w(pts, c, lw=2.4): ax.plot(*zip(*pts), color=c, lw=lw, zorder=4, solid_joinstyle="round", solid_capstyle="round")
def pad(x, y, t, c="k", dy=1.6):
    ax.add_patch(Circle((x, y), 0.8, fc="#f2c200", ec="k", lw=0.6, zorder=5)); ax.text(x, y + dy, t, ha="center", fontsize=7, color=c, zorder=6)
ty = T_["y1"] - 1.5; tx = T_["xc"]
P_ = {"OUT+": tx - 6.5, "B+": tx - 2.3, "B−": tx + 2.3, "OUT−": tx + 6.5}
for k, x in P_.items(): pad(x, ty, k, dy=-3.0)
bw = (bt["x0"] - 1.5, (bt["y0"] + bt["y1"]) / 2)
w([(bt["x0"], bw[1] + 1), (bw[0] - 1.5, bw[1] + 1), (bw[0] - 1.5, ty + 3.2), (P_["B+"], ty + 3.2), (P_["B+"], ty)], "#d62828")
w([(bt["x0"], bw[1] - 1), (bw[0] - 0.2, bw[1] - 1), (bw[0] - 0.2, ty + 2.0), (P_["B−"], ty + 2.0), (P_["B−"], ty)], "#111")
ex0, ex1 = E_["xc"] - E_["w"] / 2 + 1.2, E_["xc"] + E_["w"] / 2 - 1.2
e5 = (ex0, E_["y1"] - 3); eg = (ex0, E_["y1"] - 6.5)
pad(*e5, "5V", dy=-0.6); pad(*eg, "GND", dy=-0.6)
ax.texts[-2].set_x(e5[0] + 2.6); ax.texts[-1].set_x(eg[0] + 2.9)
dx = (T_["xc"] + T_["w"] / 2 + E_["xc"] - E_["w"] / 2) / 2
w([(P_["OUT+"], ty), (P_["OUT+"], ty + 4.6), (dx - 1.0, ty + 4.6), (dx - 1.0, e5[1] + 4)], "#d62828")
ax.add_patch(Polygon([(dx - 2.0, e5[1] + 4), (dx, e5[1] + 4), (dx - 1.0, e5[1] + 2.4)], fc="#333", ec="k", zorder=6)); w([(dx - 2.0, e5[1] + 2.4), (dx, e5[1] + 2.4)], "#333", 2.5)
w([(dx - 1.0, e5[1] + 2.4), (dx - 1.0, e5[1]), e5], "#d62828")
ax.annotate("diodo\n(faixa pro ESP)", (dx - 1.0, e5[1] + 3.2), (dx - 1.0, e5[1] + 9.5), ha="center", fontsize=8, arrowprops=dict(arrowstyle="->"), zorder=7)
w([(P_["OUT−"], ty), (P_["OUT−"], eg[1]), eg], "#111")
# IR
pins = {"GPIO 6": (ex1, E_["y1"] - 3), "GPIO 7": (ex1, E_["y1"] - 6.5), "GPIO 20": (ex1, E_["y1"] - 10), "GND ": (ex1, E_["y1"] - 13.5)}
for k, (x, y) in pins.items():
    ax.add_patch(Circle((x, y), 0.8, fc="#f2c200", ec="k", lw=0.6, zorder=5)); ax.text(x - 1.4, y, k, ha="right", va="center", fontsize=7, zorder=6)
xr = B.CI_W2 - 1.6
ly = B.LED_FLANGE_Y - 3
w([(P.IR_LED_X - 1.2, B.LED_FLANGE_Y), (P.IR_LED_X - 1.2, ly - 1.5), (xr - 3.6, ly - 1.5), (xr - 3.6, pins["GPIO 6"][1] + 9)], "#9d4edd")
rect(xr - 4.6, xr - 2.6, pins["GPIO 6"][1] + 5, pins["GPIO 6"][1] + 9, "#f4e3b1"); ax.text(xr - 6.3, pins["GPIO 6"][1] + 7, "100 Ω", fontsize=7.5, ha="right", va="center", zorder=7)
w([(xr - 3.6, pins["GPIO 6"][1] + 5), (xr - 3.6, pins["GPIO 6"][1]), pins["GPIO 6"]], "#9d4edd")
w([(rx["x1"], B.IR_Z * 0 + rx["y0"] + 3.2), (xr - 2.2, rx["y0"] + 3.2), (xr - 2.2, pins["GPIO 7"][1]), pins["GPIO 7"]], "#e76f51")
w([(rx["x1"], rx["y0"] + 2.0), (xr - 0.9, rx["y0"] + 2.0), (xr - 0.9, pins["GPIO 20"][1]), pins["GPIO 20"]], "#f77f00")
w([(rx["x1"], rx["y0"] + 0.8), (xr + 0.4, rx["y0"] + 0.8), (xr + 0.4, pins["GND "][1]), pins["GND "]], "#111")
w([(P.IR_LED_X + 1.2, B.LED_FLANGE_Y), (P.IR_LED_X + 1.2, ly), (rx["x1"] + 1.5, ly), (rx["x1"] + 1.5, rx["y0"] + 0.8)], "#111")
ax.text(P.IR_LED_X - 2.4, B.LED_FLANGE_Y - 1.2, "+", fontsize=11, fontweight="bold", color="#9d4edd", ha="right", zorder=7)
ax.annotate("11 fios sobem daqui\npra placa da frente", (E_["xc"], E_["y1"] - 8), (E_["xc"] - 3, -44.5), ha="center", fontsize=9, color="#1d3557",
            arrowprops=dict(arrowstyle="->", color="#1d3557"), zorder=8)
ax.text(0, 52.5, "posição dos pinos no ESP é ilustrativa: siga os nomes impressos na placa", ha="center", fontsize=8.5, color="#555")
ax.set_aspect("equal"); ax.set_xlim(-31, 31); ax.set_ylim(-47, 54); ax.axis("off")
ax.set_title("Casca de TRÁS — onde vai cada peça e cada fio", fontsize=13, fontweight="bold")
plt.tight_layout(); plt.savefig(os.path.join(G, "back_shell.png"), dpi=120, facecolor="white"); plt.close()
print("ok")
