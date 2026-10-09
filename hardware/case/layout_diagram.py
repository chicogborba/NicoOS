"""python layout_diagram.py  → out/layout_fit.png  (true-scale fit diagram from the real geometry)"""
import os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import build as B, params as P

asm = os.path.join(B.OUT, "assembly")
back = trimesh.load(os.path.join(asm, "back_shell.stl")); front = trimesh.load(os.path.join(asm, "front_shell.stl"))

def sec(ax, mesh, origin, normal, ix, iy, **kw):
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    if s is None: return
    for e in s.discrete:
        ax.fill(e[:, ix], e[:, iy], **kw)

def rect(ax, x0, x1, y0, y1, fc, label=None, ec="k", fs=7.5, **kw):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=0.8, **kw))
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=fs, color="k")

fig, axs = plt.subplots(1, 3, figsize=(19, 9.5), gridspec_kw=dict(width_ratios=[1, 1, 0.62]))
SH = dict(fc="#f3b6c6", ec="#b0647c", lw=0.6)

# ── 1: back shell layer ──
ax = axs[0]
sec(ax, back, [0, 0, B.PORT_Z], [0, 0, 1], 0, 1, fc="#f3b6c6", ec="none")
s = back.section(plane_origin=[0, 0, B.FLOOR + 0.6], plane_normal=[0, 0, 1])
for e in s.discrete: ax.plot(e[:, 0], e[:, 1], color="#b0647c", lw=0.5)
ax.add_patch(FancyBboxPatch((-B.CI_W2, -B.CI_H2), 2 * B.CI_W2, 2 * B.CI_H2, boxstyle=f"round,pad=0,rounding_size={B.CI_R}", fc="white", ec="none", zorder=0.5))
sec(ax, back, [0, 0, B.FLOOR + 0.6], [0, 0, 1], 0, 1, fc="#f7d3dc", ec="#b0647c", lw=0.4)
for nm, D, col in (("TP4056\n(carga)", B.TP, "#8fb8f0"), ("ESP32-C3\nSuper Mini", B.ESP, "#7f8fd0")):
    rect(ax, D["xc"] - D["w"] / 2, D["xc"] + D["w"] / 2, D["y0"], D["y1"], col, f"{nm}\n{D['w']:.1f}×{D['l']:.1f}")
    rect(ax, D["xc"] - P.USB_C_W / 2, D["xc"] + P.USB_C_W / 2, D["y_conn"], D["y_conn"] + 7.3, "#d0d0d0", "USB-C", fs=6)
bt = B.BAT
rect(ax, bt["x0"], bt["x1"], bt["y0"], bt["y1"], "#d9d9de", f"BATERIA\n{P.BATTERY_LENGTH:.0f}×{P.BATTERY_WIDTH:.0f}×{P.BATTERY_HEIGHT:.0f} mm", fs=8.5)
e = B.BAT_ENV
ax.add_patch(Rectangle((e["x0"], e["y0"]), e["x1"] - e["x0"], e["y1"] - e["y0"], fc="none", ec="#2a9d3a", ls="--", lw=1))
ax.text(e["x1"] - 0.5, e["y1"] + 0.4, f"baia da bateria (cabe até {B.BAY_L:.0f}×{B.BAY_W:.0f})", color="#2a9d3a", fontsize=6.5, ha="right")
rect(ax, bt["x0"] - P.BATTERY_WIRE_SPACE, bt["x0"], (bt["y0"] + bt["y1"]) / 2 - 4, (bt["y0"] + bt["y1"]) / 2 + 4, "#888", "fios", fs=5.5)
r = P.IR_LED_DIAMETER / 2
rect(ax, P.IR_LED_X - r, P.IR_LED_X + r, B.LED_FLANGE_Y, B.LED_TIP_Y, "#b9a5ff")
ax.annotate("LED IR 5 mm\n(emissor)", (P.IR_LED_X, B.LED_FLANGE_Y), (-19, 29.5), fontsize=7.5, ha="center", arrowprops=dict(arrowstyle="-", lw=0.6))
rx = B.RX
rect(ax, rx["x0"], rx["x1"], rx["y0"], rx["y1"], "#444")
ax.add_patch(Circle((P.IR_RX_X, rx["y1"]), P.IR_RX_DOME_D / 2, fc="#444", ec="k", lw=0.6))
ax.annotate("Receptor IR\n(VS1838B)", (rx["x1"], (rx["y0"] + rx["y1"]) / 2), (15.5, 33.5), fontsize=7.5, ha="center", arrowprops=dict(arrowstyle="-", lw=0.6))
if P.POWER_SWITCH:
    sw = B.SW
    rect(ax, sw["x0"], sw["x1"], sw["y0"], sw["y1"], "#666")
    ax.annotate("chave\nliga/desl.", (sw["x0"], P.SW_Y), (12.5, 26), fontsize=7, ha="center", arrowprops=dict(arrowstyle="-", lw=0.6))
for x in (P.IR_LED_X, P.IR_RX_X):
    ax.annotate("", (x, B.H2 + 6), (x, B.H2 + 0.5), arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2))
ax.text(0, B.H2 + 7, "IR sai/entra pela borda de cima", color="#c0392b", ha="center", fontsize=8)
ax.set_title("CAMADA DE TRÁS — casca traseira (vista de cima, escala real)", fontsize=10)

# ── 2: front PCB layer ──
ax = axs[1]
sec(ax, front, [0, 0, B.PCB_TOP + 1.5], [0, 0, 1], 0, 1, fc="#f3b6c6", ec="none")
ax.add_patch(FancyBboxPatch((-B.CI_W2, -B.CI_H2), 2 * B.CI_W2, 2 * B.CI_H2, boxstyle=f"round,pad=0,rounding_size={B.CI_R}", fc="white", ec="none", zorder=0.5))
for poly in B.pcb_outline().to_polygons():
    p = np.array(poly); ax.fill(p[:, 0], p[:, 1], fc="#bfe3c4", ec="#2e7d32", lw=1, zorder=1)
ax.text(0, -33.5, "PCB principal = perfurada 5×7 cm\n(cantos arredondados, 4 furos M2)", ha="center", fontsize=8, color="#1b5e20")
cx, cy = P.DISPLAY_WINDOW_C; pcy = cy - P.OLED_GLASS_OFFSET_Y
rect(ax, cx - P.OLED_PCB[0] / 2, cx + P.OLED_PCB[0] / 2, pcy - P.OLED_PCB[1] / 2, pcy + P.OLED_PCB[1] / 2, "#3b3b55", None)
rect(ax, cx - 10.85, cx + 10.85, cy - 5.45, cy + 5.45, "#111", None)
ax.text(cx, cy, "OLED 0.96\"", color="w", ha="center", va="center", fontsize=8)
for (x, y) in B.DPAD + list(P.AB_POS):
    rect(ax, x - 3, x + 3, y - 3, y + 3, "#555"); ax.add_patch(Circle((x, y), 1.75, fc="#ddd", ec="k", lw=0.5))
for (bx, by) in B.BOSSES:
    ax.add_patch(Circle((bx, by), P.BOSS_OD / 2, fc="#f3b6c6", ec="#b0647c", lw=0.8)); ax.add_patch(Circle((bx, by), 1.0, fc="w", ec="k", lw=0.5))
ax.add_patch(Rectangle((-15, -35), 30, 70, fc="none", ec="#d00000", ls="--", lw=2, zorder=5))
ax.text(0, -39.6, "tracejado vermelho = placa 3×7 cm (30×70)", color="#d00000", ha="center", fontsize=8.5)
out = [(x, y) for (x, y) in B.DPAD + list(P.AB_POS) if abs(x) + 3.25 > 15]
for (x, y) in out:
    ax.add_patch(Circle((x, y), 5.2, fc="none", ec="#d00000", lw=1.8, zorder=6))
for (bx, by) in B.BOSSES:
    ax.plot([bx - 2.5, bx + 2.5], [by - 2.5, by + 2.5], color="#d00000", lw=1.5, zorder=6); ax.plot([bx - 2.5, bx + 2.5], [by + 2.5, by - 2.5], color="#d00000", lw=1.5, zorder=6)
ax.set_title("CAMADA DA FRENTE — PCB principal (tela + 6 botões)", fontsize=10)

for ax in axs[:2]:
    ax.set_aspect("equal"); ax.set_xlim(-31, 31); ax.set_ylim(-42, 50); ax.axis("off")
    ax.plot([-B.W2, B.W2], [-41, -41], "k-", lw=0.6); ax.text(0, -41.6, f"{P.BODY_W} mm", ha="center", va="top", fontsize=7)

# ── 3: side stack (looking from the right, y horizontal → drawn vertical for compactness) ──
ax = axs[2]
for m in (back, front):
    sec(ax, m, [0.5, 0, 0], [1, 0, 0], 2, 1, fc="#f3b6c6", ec="#b0647c", lw=0.4)
rect(ax, bt["z0"], bt["z1"], bt["y0"], bt["y1"], "#d9d9de", "bat.", fs=6.5)
for nm, D, col in (("TP4056 / ESP32", B.TP, "#8fb8f0"),):
    rect(ax, D["zb"], D["zb"] + D["t"], D["y0"], D["y1"], col)
    rect(ax, D["zb"] + D["t"], D["zb"] + D["t"] + P.USB_C_H, D["y_conn"], D["y_conn"] + 7.3, "#d0d0d0")
    ax.text(D["zb"] + D["t"] + 2.6, D["y0"] + 17, nm, fontsize=7, rotation=90, va="center", ha="center")
rect(ax, B.IR_Z - r, B.IR_Z + r, B.LED_FLANGE_Y, B.LED_TIP_Y, "#b9a5ff")
ax.text(B.IR_Z, B.LED_FLANGE_Y - 2.2, "LED IR /\nreceptor", fontsize=6.5, ha="center", va="top")
rect(ax, B.PCB_BOT, B.PCB_TOP, -B.CI_H2 + 0.5, B.CI_H2 - 0.5, "#bfe3c4", ec="#2e7d32")
ax.text(B.PCB_BOT + 0.8, -20, "PCB 5×7", fontsize=7, rotation=90, va="center", ha="center", color="#1b5e20")
gz1 = B.CEIL; gz0 = gz1 - P.OLED_GLASS[2] - P.OLED_PCB[2]
rect(ax, gz0, gz1, pcy - P.OLED_PCB[1] / 2, pcy + P.OLED_PCB[1] / 2, "#3b3b55"); rect(ax, B.PCB_TOP, gz0, pcy + 10, pcy + 13, "#555")
ax.text((gz0 + gz1) / 2, pcy, "OLED", color="w", fontsize=6.5, rotation=90, ha="center", va="center")
for (x, y) in [B.DPAD[1], B.DPAD[0]]:
    rect(ax, B.PCB_TOP, B.PCB_TOP + 3.4, y - 3, y + 3, "#555"); rect(ax, B.PCB_TOP + P.TACT_H, B.T + P.BUTTON_PROTRUDE, y - 3, y + 3, "#fff7e6")
ax.axvline(B.SPLIT_Z, color="#b0647c", ls=":", lw=0.8)
for z, lab in ((0, "0"), (B.FLOOR, f"{B.FLOOR:.1f}"), (bt["z1"], f"{bt['z1']:.1f}"), (B.PCB_BOT, f"{B.PCB_BOT:.1f}"), (B.PCB_TOP, f"{B.PCB_TOP:.1f}"), (B.T, f"{B.T:.1f}")):
    ax.plot([z, z], [-41.5, -39.5], "k-", lw=0.5); ax.text(z, -42, lab, fontsize=6, ha="center", va="top", rotation=90)
ax.text(B.T / 2, -47.5, f"espessura {B.T:.1f} mm\n← costas | frente →", ha="center", fontsize=7.5)
ax.text((bt["z1"] + B.PCB_BOT) / 2, bt["y1"] + 1.5, f"{B.PCB_BOT - bt['z1']:.1f} mm\nlivre", fontsize=6, ha="center", color="#2a9d3a")
ax.set_aspect("equal"); ax.set_xlim(-2, B.T + 4); ax.set_ylim(-50, 50); ax.axis("off")
ax.set_title("CORTE LATERAL — as duas camadas", fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(B.OUT, "layout_fit.png"), dpi=130, facecolor="white")
print("ok")
