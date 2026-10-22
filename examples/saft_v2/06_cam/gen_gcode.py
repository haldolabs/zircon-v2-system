"""G-code generator for SAFT-V2-TAB (v2), Haas VF-2 (Fanuc-style), metric, programmed to tool centreline (no cutter comp).
ONE setup (G54, plate flat on a sacrificial subplate, 2x M6 low-head screws through the waste strip above the part):
   T1 1/4" 3FL carbide EM : outer contour at every Z level, climb (CW), 2 tabs on the top edge. The 1/4" automatically skips
                            every feature narrower than itself because the path is the exact profile offset by its radius.
   T2 1/8" 2FL carbide EM : REST machining — the same profile offset by 1.5875, clipped to where material is left (channel,
                            tooth notch, rib, stop gap, flex pocket, mouth). Every segment starts in air T1 cleared.
   T3 1/8" ball EM        : ID dimples (G81), dice pattern.
Paths come from the exact FreeCAD mid-plane section (02_design/v2/profile.json) via shapely offsets, so fillets are followed
exactly. Usage: ~/miniconda3/envs/cae/bin/python gen_gcode.py  → SAFT-V2-TAB_OP10.nc, cam.json, setup_sheet.md, media/toolpaths.png"""
import json, math, os
import numpy as np
from shapely.geometry import Polygon, LineString, MultiLineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, linemerge
HERE = os.path.dirname(os.path.abspath(__file__)); DESIGN = os.path.join(HERE, "..", "02_design", "v2")
P = json.load(open(os.path.join(DESIGN, "SAFT-V2-TAB_v2_params.json"))); prm, d = P["params"], P["derived"]
loops = json.load(open(os.path.join(DESIGN, "profile.json"))); PART = Polygon(loops[0]).buffer(0)
L, H, W = d["L"], d["H"], prm["W"]
# ---------------- machine / tooling / cutting data ----------------
T1 = dict(n=1, d=6.35, r=3.175, desc='1/4" 3FL carbide square EM, 19 LOC', rpm=12000, f=1100, f_plunge=400, stepdown=3.25, h=1, flutes=3)
T2 = dict(n=2, d=3.175, r=1.5875, desc='1/8" 2FL carbide square EM, 16 LOC', rpm=12000, f=480, f_plunge=200, stepdown=1.6, h=2, flutes=2)
T3 = dict(n=3, d=3.175, r=1.5875, desc='1/8" 2FL carbide ball EM', rpm=10000, f=300, h=3, flutes=2)
Z_THRU = -(W + 0.3); Z_CLEAR = 15.0; Z_RAPID = 3.0
TABS = dict(x=[5.0, d["x_t"] + 4.0], width=5.0, height=1.2)          # top edge y=H: root block and the tooth (never the thin arm)
BLANK = dict(x=(-4.5, L + 4.5), y=(0.0, 31.75), z=(-W, 0.0), desc='6061-T6 flat bar 1/2" x 1-1/4" x 3-1/4" (12.7 x 31.75 x 82.55)')
SCREWS = [(15.0, 28.0), (d["x_t"] + 8.0, 28.0)]   # M6 low-head SHCS (head Ø10): head edge y>=23 clears the T1 swath top at H+2R=22.05
RAMP_DEG = 3.0
def levels(step):
    out = []; z = 0.0
    while z > Z_THRU + 1e-6: z = max(Z_THRU, z - step); out.append(round(z, 3))
    return out
# ---------------- toolpath geometry ----------------
STOCK = box(BLANK["x"][0], BLANK["y"][0], BLANK["x"][1], BLANK["y"][1])
VOID = box(-40, -40, L + 40, H + 40).difference(PART)   # everything outside the part is void: beyond the blank it is already air
def ring_coords(ring):   # list of (x,y) without the closing duplicate
    c = list(ring.coords); return c[:-1] if c[0] == c[-1] else c
def rotate_start(coords, pick):
    i = min(range(len(coords)), key=lambda k: pick(coords[k])); return coords[i:] + coords[:i]
# T1: exact profile dilated by R; CW exterior = climb on an outside contour
off1 = orient(PART.buffer(T1["r"], quad_segs=48), -1.0)
path1 = ring_coords(off1.exterior)
path1 = rotate_start(path1, lambda c: abs(c[1] + T1["r"]) + 0.01 * abs(c[0] - L / 2))   # start on the bottom edge (y=-R, in air below the blank)
cleared1 = VOID.buffer(-T1["r"]).buffer(T1["r"])                     # everything a 1/4" can sweep in the void
# T2: dilate by r; exterior CW (climb outside), interior rings CCW (climb inside the pocket)
off2 = orient(PART.buffer(T2["r"], quad_segs=48), -1.0)
rest = VOID.difference(cleared1).buffer(T2["r"] + 0.35)             # tool-centre zone where a 1/8" still meets T1's leftover material
ext2 = LineString(ring_coords(off2.exterior) + [ring_coords(off2.exterior)[0]])
seg2 = ext2.intersection(rest)
segs = [g for g in (seg2.geoms if hasattr(seg2, "geoms") else [seg2]) if g.length > 0.5]
merged = linemerge(MultiLineString(segs)) if len(segs) > 1 else segs[0]
segs = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
segs.sort(key=lambda g: g.coords[0][0])
# NOTE: the flex pocket is NOT a closed void — it connects to the channel through the 3.4 mm passage above the stop post,
# so the whole void is one region reachable from the mouth and T2 needs no ramp entry anywhere (every segment starts in
# air that T1 already cleared). Closed rings would appear here as off2.interiors; there are none.
pocket_rings = [ring_coords(r) for r in off2.interiors]
assert len(pocket_rings) == 0, len(pocket_rings)
# ---------------- G-code writer ----------------
g = []
def cmt(text):
    text = (text.replace("Ø", "DIA").replace("°", "DEG").replace('"', "IN").replace("×", "X").replace("(", "-").replace(")", "-"))
    return "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in text).upper()
def o(s):
    if "(" in s:
        i = s.index("("); j = s.rindex(")"); s = s[:i] + "(" + cmt(s[i + 1:j]) + ")" + s[j + 1:]
    g.append(s)
def fmt(v): return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"
def xy(x, y): return f"X{fmt(x)} Y{fmt(y)}"
def toolchange(T, x, y, zclear=Z_CLEAR):
    o(f"T{T['n']} M6 ({T['desc']})"); o(f"S{T['rpm']} M3"); o(f"G0 {xy(x, y)}"); o(f"G43 H{T['h']} Z{fmt(zclear)}"); o("M8")
def op10():
    o("%"); o("O2010 (SAFT-V2-TAB OP10 ONE SETUP PLATE FLAT)"); o("(SAFT-V2-TAB REV v2  MATERIAL 6061-T6  UNITS MM)")
    o("(WCS G54: X0 Y0 = PART ROOT-BOTTOM CORNER, Z0 = TOP OF PLATE)")
    o(f"(BLANK {BLANK['desc']} ON SACRIFICIAL SUBPLATE, 2X M6 LOW-HEAD AT X{SCREWS[0][0]:.0f}/X{SCREWS[1][0]:.0f} Y28)")
    o("(T1 1/4 EM OUTER CONTOUR W/ 2 TABS   T2 1/8 EM REST + POCKET   T3 1/8 BALL DIMPLES)")
    o("(PROGRAMMED TO TOOL CENTERLINE - NO CUTTER COMP)")
    o("G21 G17 G40 G49 G80 G90 G94"); o("G54"); o("G53 G0 Z0.")
    # ---- T1 contour ----
    R = T1["r"]; x0, y0 = path1[0]
    toolchange(T1, x0, y0)
    o("(--- T1 OUTER CONTOUR, CLIMB CW, EVERY LEVEL, PLUNGE IN AIR BELOW THE BLANK ---)")
    lv1 = levels(T1["stepdown"]); ztab = -(W - TABS["height"])
    o(f"G0 Z{fmt(Z_RAPID)}")
    for z in lv1:
        o(f"G1 Z{fmt(z)} F{T1['f_plunge']}"); o(f"G1 F{T1['f']}")
        pts = path1 + [path1[0]]
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            top_edge = abs(ya - (H + R)) < 1e-6 and abs(yb - (H + R)) < 1e-6 and abs(xb - xa) > 10
            if top_edge and z < ztab - 1e-6:
                direction = 1 if xb > xa else -1
                for tx in sorted(TABS["x"], reverse=(direction < 0)):
                    x_in, x_out = tx + direction * -(TABS["width"] / 2 + R), tx + direction * (TABS["width"] / 2 + R)
                    o(f"G1 {xy(x_in, ya)}"); o(f"G1 Z{fmt(ztab)}"); o(f"G1 {xy(x_out, ya)}"); o(f"G1 Z{fmt(z)}")
                o(f"G1 {xy(xb, yb)}")
            else:
                o(f"G1 {xy(xb, yb)}")
    o(f"G0 Z{fmt(Z_CLEAR)}"); o("M9"); o("M5")
    # ---- T2 rest + pocket ----
    r = T2["r"]; lv2 = levels(T2["stepdown"])
    toolchange(T2, *segs[0].coords[0])
    o(f"(--- T2 REST MACHINING: {len(segs)} SEGMENTS OF THE PROFILE THE 1/4 COULD NOT REACH, EVERY LEVEL ---)")
    for i, sgm in enumerate(segs):
        c = list(sgm.coords); x0, y0 = c[0]
        o(f"(SEGMENT {i + 1}: X{x0:.1f} Y{y0:.1f} TO X{c[-1][0]:.1f} Y{c[-1][1]:.1f}, {sgm.length:.1f} MM)")
        o(f"G0 {xy(x0, y0)}"); o(f"G0 Z{fmt(Z_RAPID)}")
        for z in lv2:
            o(f"G1 Z{fmt(z)} F{T2['f_plunge']}"); o(f"G1 F{T2['f']}")
            for (xb, yb) in c[1:]: o(f"G1 {xy(xb, yb)}")
            if z != lv2[-1]:
                o(f"G0 Z{fmt(Z_RAPID)}"); o(f"G0 {xy(x0, y0)}")
        o(f"G0 Z{fmt(Z_CLEAR)}")
    o("M9"); o("M5")
    # ---- T3 dimples ----
    o("(--- T3 ID DIMPLES: DICE PATTERN, UP TO 6, DELETE LINES FOR SMALLER GROUPS ---)")
    grid = P["dimple_xy"]
    toolchange(T3, *grid[0]); o(f"G0 Z{fmt(Z_RAPID)}")
    o(f"G98 G81 Z-0.4 R{fmt(Z_RAPID)} F{T3['f']}")
    for (x, y) in grid[1:]: o(xy(x, y))
    o("G80"); o(f"G0 Z{fmt(Z_CLEAR)}")
    o("M9"); o("M5"); o("G53 G0 Z0."); o("G53 G0 Y0."); o("M30"); o("%")
    return "\n".join(g) + "\n"
prog = op10(); open(os.path.join(HERE, "SAFT-V2-TAB_OP10.nc"), "w").write(prog)
json.dump(dict(T1=T1, T2=T2, T3=T3, Z_THRU=Z_THRU, TABS=TABS, BLANK=BLANK, SCREWS=SCREWS, RAMP_DEG=RAMP_DEG, levels_T1=levels(T1["stepdown"]), levels_T2=levels(T2["stepdown"]),
               rest_segments=[dict(start=list(s.coords[0]), end=list(s.coords[-1]), length=round(s.length, 2)) for s in segs],
               path1_len=round(LineString(path1 + [path1[0]]).length, 1)),
          open(os.path.join(HERE, "cam.json"), "w"), indent=1)
# ---------------- toolpath figure ----------------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=140)
sx, sy = STOCK.exterior.xy; ax.fill(sx, sy, fc="#ece7dc", ec="#998", lw=0.6)
x, y = PART.exterior.xy; ax.fill(x, y, fc="#c9ced6", ec="k", lw=0.7)
for hole in PART.interiors: hx, hy = hole.xy; ax.fill(hx, hy, fc="#ece7dc", ec="k", lw=0.7)
for gpoly in getattr(cleared1, "geoms", [cleared1]):
    cx_, cy_ = gpoly.exterior.xy; ax.fill(cx_, cy_, fc="none", ec="none")
kerf1 = LineString(path1 + [path1[0]]).buffer(T1["r"]); kx, ky = kerf1.exterior.xy; ax.fill(kx, ky, fc="#9ecae1", alpha=0.45, ec="none", label='T1 1/4" kerf')
for hole in kerf1.interiors: hx, hy = hole.xy; ax.fill(hx, hy, fc="#ece7dc", ec="none")
ax.fill(x, y, fc="#c9ced6", ec="k", lw=0.7)
for hole in PART.interiors: hx, hy = hole.xy; ax.fill(hx, hy, fc="#ece7dc", ec="k", lw=0.7)
px_, py_ = zip(*(path1 + [path1[0]])); ax.plot(px_, py_, color="#1f77b4", lw=0.8)
for i, s in enumerate(segs):
    cx_, cy_ = s.xy; ax.plot(cx_, cy_, color="#d62728", lw=1.4, label='T2 1/8" rest segments' if i == 0 else None)
for tx in TABS["x"]: ax.add_patch(plt.Rectangle((tx - TABS["width"] / 2, H), TABS["width"], 2 * T1["r"], fc="#ffbf00", ec="none", alpha=0.8, label="tab" if tx == TABS["x"][0] else None))
for (sx_, sy_) in SCREWS: ax.add_patch(plt.Circle((sx_, sy_), 5, fc="none", ec="#555", ls="--")); ax.add_patch(plt.Circle((sx_, sy_), 3.3, fc="#777", ec="none"))
for (dx, dy) in P["dimple_xy"]: ax.add_patch(plt.Circle((dx, dy), 1.0, fc="#444", ec="none"))
ax.set_aspect("equal"); ax.set_xlim(BLANK["x"][0] - 2, BLANK["x"][1] + 2); ax.set_ylim(-5, 34); ax.legend(loc="upper right", fontsize=7, ncol=4)
ax.set_title("SAFT-V2-TAB OP10 — one setup: T1 contour (blue kerf), T2 rest segments (red), tabs (amber), M6 screws, dimples", fontsize=8)
fig.savefig(os.path.join(HERE, "media", "toolpaths.png"), bbox_inches="tight"); plt.close(fig)
print("OP10 lines", prog.count("\n"), "rest segments", len(segs), [round(s.length, 1) for s in segs], "path1", round(LineString(path1 + [path1[0]]).length, 1))
