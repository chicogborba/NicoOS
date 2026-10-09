"""python wiring_diagram.py → out/wiring.png  (ligação elétrica, sem chave, com deep sleep)"""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

fig, ax = plt.subplots(figsize=(17, 10.5))
def box(x0, y0, x1, y1, label, fc, fs=10, tc="k"):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.12", fc=fc, ec="k", lw=1.3, zorder=3))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=fs, color=tc, zorder=4)
def wire(pts, c, lw=2.6):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=c, lw=lw, solid_capstyle="round", solid_joinstyle="round", zorder=2)
def dot(x, y, c="k"):
    ax.plot([x], [y], "o", color=c, ms=7, zorder=5)
def pin(x, y, name, side):
    ax.text(x + (0.12 if side == "L" else -0.12), y, name, ha="left" if side == "L" else "right", va="center", fontsize=9.5, color="w", zorder=5, fontweight="bold")
    ax.plot([x], [y], "s", color="#f2c200", ms=7, zorder=5)
def lab(x, y, t, c="k", ha="center", fs=8.5):
    ax.text(x, y, t, ha=ha, va="bottom", fontsize=fs, color=c, zorder=6)

RED, ORG, BLK = "#d62828", "#f77f00", "#111111"
# ESP32
box(6.5, 2.4, 9.5, 8.6, "", "#1d3557")
ax.text(8, 8.3, "ESP32-C3\nSuper Mini", ha="center", va="top", color="w", fontsize=12, fontweight="bold", zorder=5)
ax.text(8, 2.9, "livres: GPIO 2, 21", ha="center", color="#cfd8e8", fontsize=8.5, zorder=5)
L = {"5V": 8.0, "GND": 7.3, "GPIO 0": 6.6, "GPIO 1": 5.9, "GPIO 3": 5.2, "GPIO 4": 4.5}
R = {"3V3": 8.0, "GPIO 8": 7.3, "GPIO 9": 6.6, "GPIO 6": 5.9, "GPIO 7": 5.2, "GPIO 20": 4.5, "GPIO 5": 3.8, "GPIO 10": 3.1}
for n, y in L.items(): pin(6.5, y, n, "L")
for n, y in R.items(): pin(9.5, y, n, "R")

# GND bus
wire([(6.5, 7.3), (1.5, 7.3), (1.5, 1.0), (15.2, 1.0), (15.2, 7.6)], BLK, 3.4)
ax.text(8, 0.62, "GND comum (um fio só passando por tudo)", ha="center", fontsize=9.5)

# power
box(0.2, 8.5, 1.9, 9.7, "Bateria\n3.7 V", "#d9d9de")
box(2.7, 8.4, 4.6, 9.8, "TP4056\nUSB-C", "#8fb8f0")
for t, x, y in (("B+", 2.78, 9.4), ("B−", 2.78, 8.8), ("OUT+", 4.52, 9.4), ("OUT−", 4.52, 8.8)):
    ax.text(x, y, t, fontsize=7.5, ha="left" if x < 3 else "right", va="center", zorder=5)
wire([(1.9, 9.4), (2.7, 9.4)], RED); wire([(1.9, 8.8), (2.7, 8.8)], BLK)
wire([(4.6, 9.4), (6.0, 9.4), (6.0, 8.0), (6.5, 8.0)], RED)
ax.add_patch(Polygon([(5.05, 9.62), (5.05, 9.18), (5.5, 9.4)], fc="#333", ec="k", zorder=4)); wire([(5.5, 9.62), (5.5, 9.18)], "#333", 3)
lab(5.28, 9.68, "diodo 1N5817\n(faixa pro lado do ESP)", fs=8)
wire([(4.6, 8.8), (5.2, 8.8), (5.2, 7.3)], BLK); dot(5.2, 7.3)

# left buttons
for (n, g, c) in (("CIMA", "GPIO 0", "#2a9d8f"), ("BAIXO", "GPIO 1", "#457b9d"), ("ESQ.", "GPIO 3", "#6a4c93"), ("DIR.", "GPIO 4", "#b5179e")):
    y = L[g]
    box(2.7, y - 0.27, 3.9, y + 0.27, f"botão {n}", "#eeeeee", 8.5)
    wire([(3.9, y), (6.5, y)], c); wire([(2.7, y), (1.5, y)], BLK); dot(1.5, y)
ax.text(4.2, 3.75, "GPIO 0–5 acordam\ndo deep sleep", fontsize=8.5, color="#2a9d8f", ha="center")

# OLED
box(12.0, 6.2, 14.2, 8.5, "OLED 0.96\"\nI2C", "#222", 10, "w")
for t, y in (("VCC", 8.0), ("SDA", 7.3), ("SCL", 6.6)):
    ax.text(12.08, y, t, color="#ffd", fontsize=7.5, va="center", zorder=5)
ax.text(14.12, 7.6, "GND", color="#ffd", fontsize=7.5, va="center", ha="right", zorder=5)
wire([(9.5, 8.0), (12.0, 8.0)], ORG); wire([(9.5, 7.3), (12.0, 7.3)], "#00a6fb"); wire([(9.5, 6.6), (12.0, 6.6)], "#ffb703")
wire([(14.2, 7.6), (15.2, 7.6)], BLK)
# IR LED
box(10.2, 5.67, 11.2, 6.13, "100 Ω", "#f4e3b1", 8.5)
box(12.0, 5.62, 13.3, 6.18, "LED IR ▶|", "#b9a5ff", 9)
wire([(9.5, 5.9), (10.2, 5.9)], "#9d4edd"); wire([(11.2, 5.9), (12.0, 5.9)], "#9d4edd"); wire([(13.3, 5.9), (15.2, 5.9)], BLK); dot(15.2, 5.9)
lab(11.6, 6.2, "perna longa (+) →", fs=7.5)
# IR RX
box(12.0, 4.2, 13.8, 5.5, "Receptor IR\nVS1838B", "#444", 9, "w")
ax.text(12.08, 5.2, "OUT", color="#ffd", fontsize=7.5, va="center", zorder=5); ax.text(12.08, 4.5, "VCC", color="#ffd", fontsize=7.5, va="center", zorder=5)
ax.text(13.72, 4.85, "GND", color="#ffd", fontsize=7.5, va="center", ha="right", zorder=5)
wire([(9.5, 5.2), (12.0, 5.2)], "#e76f51"); wire([(9.5, 4.5), (12.0, 4.5)], ORG); wire([(13.8, 4.85), (15.2, 4.85)], BLK); dot(15.2, 4.85)
lab(10.75, 4.52, "liga/desliga o receptor", ORG, fs=7.5)
# A / B
for (n, g, c) in (("A", "GPIO 5", "#e63946"), ("B", "GPIO 10", "#8d99ae")):
    y = R[g]
    box(12.0, y - 0.27, 13.2, y + 0.27, f"botão {n}", "#eeeeee", 8.5)
    wire([(9.5, y), (12.0, y)], c); wire([(13.2, y), (15.2, y)], BLK); dot(15.2, y)
lab(10.75, 3.12, "não acorda do sleep", "#8d99ae", fs=7.5)

ax.text(8, 10.15, "BINI Cat — ligação elétrica (sem chave, com deep sleep)", ha="center", fontsize=14, fontweight="bold")
ax.text(8, 0.12, "A posição dos pinos no desenho é ilustrativa: siga os NOMES impressos na sua placa.  Botões: sem resistor, usar INPUT_PULLUP (apertado = LOW).  "
        "Confira a ordem dos pinos da OLED e do VS1838B na peça real.", ha="center", fontsize=8.5, color="#444")
ax.set_xlim(0, 15.8); ax.set_ylim(0, 10.5); ax.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "wiring.png"), dpi=130, facecolor="white")
print("ok")
