"""
BINI Cat Handheld — all design parameters (mm).

Edit this file, then run:  python build.py
Every value tagged  # CONFIRM  is a typical datasheet / marketplace value and
must be measured on the real part when it arrives.

Coordinate frame (assembly):
  x  = left/right   (0 = device centreline)
  y  = bottom/top   (+y = top edge, where the ears are; 0 = body centre)
  z  = back/front   (0 = outer back surface, +z = towards the screen)
Mapping from the original GrabCAD STLs:  x_new = x_old - 10,  y_new = y_old + 8.4
"""

# ───────────────────────── Body / styling ─────────────────────────
BODY_W = 56.2              # original footprint, kept
BODY_H = 76.2              # original footprint, kept (ears are added on top)
WALL_THICKNESS = 2.2       # external walls (target 2.0–2.5)
PLAN_CORNER_R = 9.0        # outline corner radius (original ≈ 3) → softer
FRONT_EDGE_R = 6.0         # pillow radius of the front edge
BACK_EDGE_R = 3.5          # pillow radius of the back edge
PRINTABLE_FILLET = True    # first 29 % of every bed-side fillet becomes a 45° chamfer

# Cat ears (part of the outline, full thickness → prints flat, very strong)
EARS = True
EAR_BASE_W = 19.0          # width of each ear where it meets the head
EAR_HEIGHT = 10.0          # how far the ear sticks up above the top edge
EAR_X = 16.6               # x of the ear base centre (±)
EAR_TIP_SHIFT = 2.2        # tip leans outward by this much
EAR_TIP_R = 3.0            # roundness of the ear tip
EAR_BLEND = 3.0            # smooth fillet radius between ear and head

VOXEL = 0.2                # shell surface resolution (smaller = smoother, slower)

# ───────────────────────── Shell joint ─────────────────────────
LIP_T = 1.0                # tongue thickness (back shell, goes inside front shell)
LIP_H = 2.0                # tongue height above the split line
LIP_CLEARANCE = 0.15
SNAP_BUMP = 0.35           # snap bump height (front wall → groove in tongue)
SNAP_LEN = 8.0
SNAP_YS = [-19.0, 11.0]    # snaps on left+right side at these y (4 total)
PRY_NOTCH_W = 7.0          # fingernail notch on the bottom seam (x = 0)

# ───────────────────────── Main (front) PCB ─────────────────────────
# Same idea as original: perfboard screwed to 4 bosses in the front shell,
# display + 6 tact switches on top. Board outline is exported as an SVG template.
MAIN_PCB_T = 1.6
PCB_CLEARANCE = 0.5        # gap PCB edge ↔ inner wall
PCB_UNDERSIDE_KEEPOUT = 2.0  # solder joints / trimmed leads under the main PCB
FRONT_STACK_H = 5.55       # PCB top → inner face of front wall (measured on original)
BOSS_OD = 5.6
BOSS_HOLE_D = 1.7          # M2 self-tapping (original used 2.0 hole)
BOSS_HOLE_DEPTH = 4.6
BOSS_DIAG_OFFSET = 3.0     # boss distance from corner-arc centre (along diagonal)
SCREW = "M2 x 6 pan head self-tapping (x2, OPTIONAL)"
SCREW_HEAD_D = 3.8
SCREW_HEAD_H = 1.4
PCB_WIRE_NOTCH = (8.0, 2.5)  # (length, depth) notch at left/right edge for wires
PCB_WIRE_NOTCH_Y = -12.0

# ───────────────────────── Buttons (original layout kept) ─────────────────────────
TACT_SIZE = 6.0            # 6x6 tact switch                     # CONFIRM
TACT_H = 4.3               # total height incl. plunger (orig. design value)
BUTTON_CLEARANCE = 0.25    # cap ↔ hole, per side
BUTTON_PROTRUDE = 1.6      # cap top above front face
BUTTON_FLANGE_T = 1.0
BUTTON_TOP_R = 0.9         # roundness of the cap top edge

DPAD_CENTER = (-11.2, -16.5)
BUTTON_SPACING = 7.6       # D-pad pitch (original 7.5–7.65)
BUTTON_SIZE = 6.0          # D-pad cap (square, rounded)
BUTTON_CORNER_R = 1.3
DPAD_FLANGE = 7.2          # must stay < BUTTON_SPACING

AB_POS = [(11.74, -16.47), (16.76, -8.89)]   # original A / B centres
BUTTON_DIAMETER = 7.4      # A/B cap (orig hole 8.3 left a 0.8 mm web)
AB_FLANGE_D = 8.9          # must stay < A-B distance (9.09)

RECESS_DEPTH = 0.6         # D-pad cross / A-B pill recess (original visual language)

# ───────────────────────── Display (original window kept) ─────────────────────────
DISPLAY_WINDOW = (41.36, 26.56)   # original opening
DISPLAY_WINDOW_C = (0.0, 14.75)
DISPLAY_WINDOW_R = 3.5
BEZEL_CLEARANCE = 0.18
BEZEL_FLANGE = (44.0, 29.6)
BEZEL_FLANGE_T = 1.0
OLED_PCB = (27.3, 27.8, 1.1)      # 0.96" I2C OLED module               # CONFIRM
OLED_GLASS = (26.7, 19.3, 1.4)                                         # CONFIRM
OLED_GLASS_OFFSET_Y = 1.0         # glass centre above PCB centre        # CONFIRM
OLED_VIEW = (23.0, 12.0)          # opening in the black bezel (active area 21.7x10.9)
OLED_HEADER_H = 2.5               # plastic of the header between boards # CONFIRM

# ───────────────────────── ESP32-C3 Super Mini ─────────────────────────
ESP_WIDTH = 18.0                                                        # CONFIRM
ESP_LENGTH = 22.52                                                      # CONFIRM
ESP_PCB_T = 1.0                                                         # CONFIRM
ESP_HEIGHT = 1.0 + 3.26    # PCB + USB-C (tallest part)                 # CONFIRM
ESP_USB_OVERHANG = 0.5     # USB-C shell past the board edge             # CONFIRM
ESP_X = 10.5               # board centre x (USB on bottom edge)

# ───────────────────────── TP4056 (USB-C version) ─────────────────────────
TP4056_WIDTH = 17.5                                                     # CONFIRM
TP4056_LENGTH = 28.0                                                    # CONFIRM
TP4056_PCB_T = 1.6                                                      # CONFIRM
TP4056_HEIGHT = 1.6 + 3.26                                              # CONFIRM
TP4056_USB_OVERHANG = 0.5                                               # CONFIRM
TP4056_X = -10.5

# ───────────────────────── USB-C openings ─────────────────────────
USB_C_W = 8.94             # receptacle shell
USB_C_H = 3.26
USB_CLEARANCE = 0.8        # per side around the receptacle (tolerates board height/position spread)
USB_PLUG_BODY = (12.4, 6.6)  # cable overmold envelope (fits most cables)
USB_PLUG_BODY_CLEARANCE = 0.2
USB_PLUG_SEAT_GAP = 0.4    # max gap overmold ↔ receptacle face when plugged
USB_BOARD_EDGE_GAP = 0.1   # board edge ↔ inner wall
BOARD_LEDGE = 0.8          # standoff rails under ESP / TP4056 (+ foam tape)
MIN_BRIDGE_ABOVE_PORT = 1.0

# ───────────────────────── Battery ─────────────────────────
# Default 502535 pouch (5 x 25 x 35 mm, ~400 mAh). 402535 (~300 mAh) or
# 503035 (~500 mAh) also fit – the build reports collisions if not.
BATTERY_LENGTH = 35.0      # along x  (tracer/airsoft cell 6x20x35)
BATTERY_WIDTH = 20.0       # along y
BATTERY_HEIGHT = 6.0       # thickness
BATTERY_WIRE_SPACE = 3.0   # PCM + wire exit on the -x end
BATTERY_CLEARANCE = 1.5
BATTERY_CENTER_X = -0.5
BATTERY_RIB_H = 3.0        # corner ribs lower than the cell → lift out easily
BATTERY_RIB_T = 1.2

# ───────────────────────── IR (top edge, between the ears) ─────────────────────────
IR_LED_DIAMETER = 5.0      # 5 mm 940 nm LED (3 mm also OK: set 3.0/3.8/5.3) # CONFIRM
IR_LED_FLANGE_D = 5.8                                                   # CONFIRM
IR_LED_LENGTH = 7.6        # dome tip → flange front                    # CONFIRM
IR_LED_HOLE_CLEARANCE = 0.2
IR_LED_RECESS = 0.3        # dome tip behind outer surface
IR_LED_X = -5.0

IR_RX_WIDTH = 6.0          # VS1838B / TSOP382 front face, short side   # CONFIRM
IR_RX_HEIGHT = 7.0         # front face, long side (lies along x)       # CONFIRM
IR_RX_DEPTH = 4.0          # body depth without dome                    # CONFIRM
IR_RX_DOME_D = 4.0                                                      # CONFIRM
IR_RX_DOME_H = 1.5                                                      # CONFIRM
IR_RX_DOME_OFFSET = 1.0    # dome centre offset from body centre (towards -x)
IR_RX_X = 5.0              # window x (symmetric with LED)
IR_WINDOW_CHAMFER = 0.5

# ───────────────────────── Power switch (optional, recommended) ─────────────────────────
POWER_SWITCH = False       # no switch: firmware uses deep sleep, front buttons wake it
SW_BODY = (8.6, 4.4, 4.5)  # (along y, depth x, height z)               # CONFIRM
SW_ACT = (2.0, 1.5, 4.0)   # actuator (y, z, protrusion)                # CONFIRM
SW_TRAVEL = 2.0                                                          # CONFIRM
SW_PROTRUDE = 0.6          # actuator tip beyond the outer surface
SW_Y = 26.0

# Everything on the side faces is aligned to one "feature line" z
# (= USB port centre) so ports, IR windows and switch line up visually.

# ───────────────────────── ESP32 port cap + charge icon ─────────────────────────
USB_CAP = True             # flush plug for the ESP32 (programming) port
USB_CAP_CLEARANCE = 0.15   # plate ↔ counterbore, per side
USB_C_INNER = (8.34, 2.56) # receptacle opening (inside the metal shell) # CONFIRM
USB_CAP_SLEEVE_LEN = 3.0   # how deep the friction sleeve enters the receptacle
USB_CAP_TONGUE_SLOT = (7.0, 1.0)  # clearance for the receptacle's centre tongue
USB_CAP_SLEEVE_FIT = 0.06  # sleeve undersize per side (smaller = tighter)
CHARGE_ICON = True         # lightning bolt engraved above the TP4056 port
CHARGE_ICON_H = 3.0        # max height (auto-limited to the flat band of the edge)
CHARGE_ICON_DEPTH = 0.35

# ───────────────────────── Screwless PCB retention ─────────────────────────
# The main PCB is sandwiched: front bosses above, back-shell ledges below.
# Closing the case clamps it; the 2 screws are optional extra stiffness.
PCB_PIN_BOSSES = (1, 2)    # bosses (top-left, bottom-right) carry a locating pin instead of a screw hole
PCB_PIN_D = 2.0            # pin Ø (PCB hole is Ø2.2)
PCB_CLAMP_GAP = 0.1        # ledge top ↔ PCB underside when closed (0 = tighter)
PCB_LEDGE_REACH = 1.6      # how far the ledges reach in from the wall
PCB_LEDGE_W = 4.0
PCB_LEDGE_SIDE_Y = [-26.0, 1.0, 19.0]   # ledges on left+right walls
PCB_LEDGE_TOP_X = [-14.5, 14.5]         # ledges on the top wall
PCB_LEDGE_BOTTOM_X = [0.0]              # ledge on the bottom wall (between the ports)

# ───────────────────────── Loose-fit interior ─────────────────────────
# Bays are oversized on purpose: parts of slightly different size drop in and are
# fixed with double-sided tape / hot glue. Align the USB boards by plugging a cable in
# before the glue sets.
BATTERY_BAY = (35.0, 25.0) # largest cell footprint the bay accepts (x, y); smaller cells float inside
BOARD_SIDE_SLACK = 0.8     # ESP32 / TP4056: gap board edge ↔ side guide (per side)
BOARD_REAR_SLACK = 1.5     # gap behind the board (TP4056 exists in 26 and 28 mm)
SMALL_PART_SLACK = 0.5     # IR receiver pocket, switch pocket
