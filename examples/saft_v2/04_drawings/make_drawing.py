"""Release drawing for SAFT-V2-TAB v2: A3 landscape SVG, 2:1, three views (profile with the exact FreeCAD section, plate
face, mouth end) + section detail of the weave at 5:1, GD&T, notes, title block. PDF via inkscape, DXF via freecadcmd.
Usage: ~/miniconda3/envs/cae/bin/python make_drawing.py (needs shapely for the hatched detail)  →  SAFT-V2-TAB.svg (+ .pdf) ; preview.png"""
import json, os, math, subprocess, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "02_design", "v2")
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
P = json.load(open(os.path.join(D, "SAFT-V2-TAB_v2_params.json"))); prm, d = P["params"], P["derived"]
loops = json.load(open(os.path.join(D, "profile.json")))
L, H, W = d["L"], d["H"], prm["W"]; a = prm["floor_t"]; rw = prm["root_w"]; t = prm["arm_t"]; Pp = d["P"]
SC = 2.0; SHEET_W, SHEET_H = 420.0, 297.0
FX, FY = 40.0, 118.0          # front view origin (part 0,0 on sheet; sheet y grows down)
TX, TY = 40.0, 196.0          # top view (plate face): part x → sheet x, part z → sheet up
SX, SY = 205.0, 182.0         # right side view (from the mouth, +X): part z → sheet x, part y → sheet y
DX, DY, DS = 255.0, 236.0, 5.0   # detail of the weave at 5:1, origin at part (x_s, 0)
out = []
def o(s): out.append(s)
def fx(x): return FX + x * SC
def fy(y): return FY - y * SC
def line(x1, y1, x2, y2, cls="v"): o(f'<line class="{cls}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>')
def text(x, y, s, size=3.2, anchor="middle", rot=0, cls="t"):
    tr = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot else ""
    o(f'<text class="{cls}" x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}"{tr}>{s}</text>')
def arrow(x, y, ang):
    a1 = math.radians(ang); L_ = 2.6; w = 0.8; bx, by = x - L_ * math.cos(a1), y - L_ * math.sin(a1); nx, ny = -math.sin(a1) * w, math.cos(a1) * w
    o(f'<polygon class="arr" points="{x:.3f},{y:.3f} {bx + nx:.3f},{by + ny:.3f} {bx - nx:.3f},{by - ny:.3f}"/>')
def hdim(x1, x2, y, yline, txt, ext=True, size=3.0):
    if ext:
        for x in (x1, x2): line(x, y + (1.2 if yline > y else -1.2), x, yline + (1.5 if yline > y else -1.5), "d")
    line(x1, yline, x2, yline, "d"); arrow(x1, yline, 180); arrow(x2, yline, 0); text((x1 + x2) / 2, yline - 1.0, txt, size)
def vdim(y1, y2, x, xline, txt, ext=True, size=3.0):
    if ext:
        for y in (y1, y2): line(x + (1.2 if xline > x else -1.2), y, xline + (1.5 if xline > x else -1.5), y, "d")
    line(xline, y1, xline, y2, "d"); arrow(xline, y1, -90); arrow(xline, y2, 90); text(xline - 1.0, (y1 + y2) / 2, txt, size, "middle", -90)
def leader(x, y, xt, yt, txt, anchor="start", size=2.9):
    line(x, y, xt, yt, "d"); arrow(x, y, math.degrees(math.atan2(y - yt, x - xt))); line(xt, yt, xt + (7 if anchor == "start" else -7), yt, "d")
    text(xt + (0.8 if anchor == "start" else -0.8), yt - 0.9, txt, size, anchor)
def fcf(x, y, sym, tol, datums):
    cells = [sym, tol] + list(datums); w = [6.5, 9] + [5.5] * len(datums); X = x
    for s_, w_ in zip(cells, w):
        o(f'<rect class="v" x="{X:.2f}" y="{y:.2f}" width="{w_}" height="5.5" fill="none"/>'); text(X + w_ / 2, y + 4.0, s_, 3.0); X += w_
    return X
def datum(x, y, label, ang=0):
    a1 = math.radians(ang); tx, ty = x + 5 * math.cos(a1), y + 5 * math.sin(a1); nx, ny = -math.sin(a1) * 1.8, math.cos(a1) * 1.8
    o(f'<polygon class="arr" points="{x:.2f},{y:.2f} {tx + nx:.2f},{ty + ny:.2f} {tx - nx:.2f},{ty - ny:.2f}"/>')
    bx, by = x + 8 * math.cos(a1) - 2.75, y + 8 * math.sin(a1) - 2.75
    o(f'<rect class="v" x="{bx:.2f}" y="{by:.2f}" width="5.5" height="5.5" fill="none"/>'); text(bx + 2.75, by + 4.1, label, 3.2)
o(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}mm" height="{SHEET_H}mm" viewBox="0 0 {SHEET_W} {SHEET_H}" font-family="osifont, DejaVu Sans, Arial, sans-serif">')
o('<style>.v{stroke:#000;stroke-width:0.5;fill:none}.h{stroke:#000;stroke-width:0.25;stroke-dasharray:2,1;fill:none}.c{stroke:#000;stroke-width:0.18;stroke-dasharray:6,1,1,1;fill:none}.d{stroke:#000;stroke-width:0.18;fill:none}.arr{fill:#000;stroke:none}.t{fill:#000}.b{stroke:#000;stroke-width:0.7;fill:none}.thin{stroke:#000;stroke-width:0.25;fill:none}.hatch{stroke:#000;stroke-width:0.15}</style>')
o(f'<rect x="0" y="0" width="{SHEET_W}" height="{SHEET_H}" fill="#fff"/>'); o(f'<rect class="b" x="10" y="10" width="{SHEET_W - 20}" height="{SHEET_H - 20}"/>')
# ---- FRONT VIEW: exact profile ----
text(fx(L / 2), fy(H) - 36, "FRONT VIEW (PROFILE, THROUGH THE PLATE)   2:1", 3.4)
for loop in loops: o('<polygon class="v" points="' + " ".join(f"{fx(x):.3f},{fy(y):.3f}" for x, y in loop) + '"/>')
hdim(fx(0), fx(L), fy(H), fy(H) - 9, f"{L:.1f}")
hdim(fx(0), fx(rw), fy(H), fy(H) - 4.5, f"{rw:.1f}")
hdim(fx(rw), fx(d["x_t"]), fy(H), fy(H) - 4.5, f"{prm['Lf']:.1f}  (FLEX ARM)")
hdim(fx(d["x_s"]), fx(L), fy(0), fy(0) + 8, f"{L - d['x_s']:.1f}")
hdim(fx(0), fx(d["floor_tip"]), fy(0), fy(0) + 13, f"{d['floor_tip']:.1f}")
vdim(fy(0), fy(H), fx(L), fx(L) + 18, f"{H:.1f}")
vdim(fy(0), fy(a), fx(0), fx(0) - 7, f"{a:.1f}")
vdim(fy(H - t), fy(H), fx(d["x_t"] - 14), fx(d["x_t"] - 14) + 0, f"{t:.2f} ±0.03", ext=False)
line(fx(d["x_t"] - 14), fy(H), fx(d["x_t"] - 14) + 6, fy(H) + 0, "d"); line(fx(d["x_t"] - 14), fy(H - t), fx(d["x_t"] - 14) + 6, fy(H - t), "d")
vdim(fy(0), fy(Pp), fx(L), fx(L) + 7, f"{Pp:.2f}")
vdim(fy(Pp), fy(Pp + prm["lead_rise"]), fx(L), fx(L) + 12, f"{prm['lead_rise']:.1f}")
leader(fx(d["land_out_x1"] + 2.5), fy(Pp + 1.45), fx(L) + 14, fy(Pp + 9), f"{prm['lead_deg']:.0f}° LEAD-IN")
leader(fx(rw + prm["r_root"] * 0.3), fy(H - t - prm["r_root"] * 0.3), fx(rw) + 14, fy(H) - 23, f"R{prm['r_root']:.1f} ROOT BLEND", "start")
leader(fx(d["x_t"] + 0.5), fy(d["arm_under"] - 0.5), fx(d["x_t"]) + 2, fy(H) - 14, f"R{prm['r_tool']:.1f} ALL OTHER INTERNAL CORNERS")
leader(fx(d["x_s"] - 1.0), fy(d["stop_top"] - 1.0), fx(d["x_s"]) - 14, fy(d["stop_top"] - 5.5), "STOP", "end")
datum(fx(0), fy(H * 0.6), "C", 180); datum(fx(30), fy(0), "B", 90)
o(f'<rect class="d" x="{fx(d["x_s"] - 1):.2f}" y="{fy(d["roof"] + 1):.2f}" width="{(L - d["x_s"] + 2) * SC:.2f}" height="{(d["roof"] + 1) * SC:.2f}" stroke-dasharray="3,1.5"/>')
text(fx(d["x_s"] + 2), fy(d["roof"] + 1) - 1.5, "SEE DETAIL A (5:1)", 3.0, "start")
# ---- TOP VIEW: plate face, dimples ----
text(TX + L, TY - W * SC - 6, "TOP VIEW (PLATE FACE, ID DIMPLES)", 3.4)
def tx_(x): return TX + x * SC
def ty_(z): return TY - z * SC
o(f'<rect class="v" x="{tx_(0):.3f}" y="{ty_(W):.3f}" width="{L * SC:.3f}" height="{W * SC:.3f}"/>')
for xh in (rw, d["x_s"], d["x_t"], d["notch_x0"], d["notch_x1"], d["floor_tip"]): line(tx_(xh), ty_(W), tx_(xh), ty_(0), "h")
# dimples are in the FRONT-view coordinates (x, y on the plate face); draw them here at (x, z=W/2 ± ...) — the plate face IS the front view's
# face, so in the top view (looking at z) they are not visible; call them out in the front view instead.
vdim(ty_(0), ty_(W), tx_(L), tx_(L) + 7, f"{W:.1f} ±0.2 (STOCK)")
datum(tx_(55), ty_(W), "A", -90)
text(tx_(L / 2), ty_(W) - 2, "DIMPLES ARE ON THIS FACE (SEE FRONT VIEW)", 2.6)
# dimples in the front view (they sit on the +Z plate face, which is the face the front view looks at)
for (x, y) in P["dimple_xy"]:
    o(f'<circle class="v" cx="{fx(x):.3f}" cy="{fy(y):.3f}" r="{1.0 * SC:.3f}"/>'); line(fx(x) - 3, fy(y), fx(x) + 3, fy(y), "c"); line(fx(x), fy(y) - 3, fx(x), fy(y) + 3, "c")
hdim(fx(0), fx(3.0), fy(H), fy(H) - 14, "3.0"); hdim(fx(0), fx(7.0), fy(H), fy(H) - 18, "7.0")
vdim(fy(0), fy(4.0), fx(0), fx(0) - 16, "4.0"); vdim(fy(4.0), fy(H / 2), fx(0), fx(0) - 16, f"{H / 2 - 4:.2f}", ext=False); vdim(fy(H / 2), fy(H - 4), fx(0), fx(0) - 16, f"{H / 2 - 4:.2f}", ext=False)
leader(fx(7.0) + 1.5, fy(H - 4.0) - 1.5, fx(7.0) + 36, fy(H) - 29, "6X Ø2.0 X 0.4 DP DIMPLE, DICE PATTERN, COUNT PER GROUP ID (NOTE 7)")
# ---- RIGHT SIDE VIEW (from the mouth) ----
def sx_(z): return SX + z * SC
def sy_(y): return SY - y * SC
text(sx_(W / 2) + 8, sy_(H) - 6, "VIEW FROM THE MOUTH (+X)", 3.4)
o(f'<rect class="v" x="{sx_(0):.3f}" y="{sy_(H):.3f}" width="{W * SC:.3f}" height="{H * SC:.3f}"/>')
for yh, cls in ((a - prm["floor_ch"], "v"), (a, "h"), (Pp, "v"), (d["rib_top"], "h"), (Pp + prm["lead_rise"], "v"), (H - t, "h")): line(sx_(0), sy_(yh), sx_(W), sy_(yh), cls)
X = fcf(sx_(W) + 5, sy_(Pp) - 2.5, "⊥", "0.05", ["A"]); line(sx_(W) + 5, sy_(Pp), sx_(W) + 0.3, sy_(Pp), "d"); arrow(sx_(W) + 0.3, sy_(Pp), 180)
X = fcf(sx_(W) + 5, sy_(d["rib_top"]) + 4, "∥", "0.03", ["B"]); line(sx_(W) + 5, sy_(d["rib_top"]) + 6.5, sx_(W) + 0.3, sy_(d["rib_top"]), "d"); arrow(sx_(W) + 0.3, sy_(d["rib_top"]), 180)
text(sx_(W / 2), sy_(0) + 5, "PAD PLANE AND RIB TOP RUN THE FULL WIDTH", 2.4)
# ---- DETAIL A: the weave, 5:1 ----
def dx_(x): return DX + (x - d["x_s"] + 1) * DS
def dy_(y): return DY - y * DS
text(dx_(d["x_s"] + 9), dy_(d["roof"] + 2) - 14, "DETAIL A — WEAVE (5:1)", 3.4)
clipx0, clipx1 = d["x_s"] - 1, L + 0.5
import shapely.geometry as sg
part = sg.Polygon(loops[0]); clip = sg.box(clipx0, -0.2, clipx1, d["roof"] + 2.0); piece = part.intersection(clip)
for g in getattr(piece, "geoms", [piece]):
    o('<polygon class="v" points="' + " ".join(f"{dx_(x):.3f},{dy_(y):.3f}" for x, y in g.exterior.coords) + '"/>')
# hatch the cut material
for k in range(0, 60):
    yy = -0.2 + k * 0.8; seg = sg.LineString([(clipx0, yy), (clipx1, yy + (clipx1 - clipx0))]).intersection(piece)
    for s_ in getattr(seg, "geoms", [seg]):
        if s_.is_empty or s_.length < 0.01: continue
        (x1, y1), (x2, y2) = s_.coords[0], s_.coords[-1]; line(dx_(x1), dy_(y1), dx_(x2), dy_(y2), "hatch")
# a 1-card and a 24-card stack ghost
o(f'<rect class="d" x="{dx_(d["x_s"] + 0.3):.2f}" y="{dy_(Pp + 3.05):.2f}" width="{(L - d["x_s"] + 1) * DS:.2f}" height="{3.05 * DS:.2f}" stroke-dasharray="1.5,1"/>')
text(dx_(L + 1.5), dy_(Pp + 1.2), "24 CARDS (3.05)", 2.4, "start"); text(dx_(L + 1.5), dy_(Pp + 1.2) + 3.2, "LIFT THE ARM", 2.4, "start")
hdim(dx_(d["notch_x0"]), dx_(d["notch_x1"]), dy_(d["roof"]), dy_(d["roof"]) - 6, f"{d['notch_x1'] - d['notch_x0']:.1f}")
hdim(dx_(d["x_r"] - prm["rib_w"] / 2), dx_(d["x_r"] + prm["rib_w"] / 2), dy_(a), dy_(a) + 6, f"{prm['rib_w']:.1f}")
hdim(dx_(d["x_s"]), dx_(d["x_r"]), dy_(a), dy_(a) + 11, f"{d['x_r'] - d['x_s']:.2f}")
vdim(dy_(Pp), dy_(d["rib_top"]), dx_(d["x_r"] + prm["rib_w"] / 2), dx_(d["x_r"] + prm["rib_w"] / 2) + 9, f"{prm['d0']:.2f} ±0.03", size=2.8)
vdim(dy_(Pp), dy_(d["roof"]), dx_(d["notch_x1"]), dx_(d["notch_x1"]) + 9, f"{prm['notch_d']:.1f}", size=2.8)
vdim(dy_(a), dy_(Pp), dx_(d["x_s"]), dx_(d["x_s"]) - 7, f"{Pp - a:.1f}", size=2.8)
vdim(dy_(Pp), dy_(d["stop_top"]), dx_(d["x_s"]), dx_(d["x_s"]) - 13, f"{d['stop_top'] - Pp:.2f} (STOP)", size=2.6)
leader(dx_(d["x_t"] + 0.5), dy_(Pp) + 0.2, dx_(d["x_t"]) - 3, dy_(Pp) + 16, "PAD PLANE, 2 PADS", "end", 2.6)
leader(dx_(d["x_r"]), dy_(d["rib_top"]), dx_(d["x_r"]) + 22, dy_(d["rib_top"]) + 14, "RIB TOP +0.25 ABOVE THE PADS", "start", 2.6)
leader(dx_(d["x_t"] + prm["pad_in"] - 0.25), dy_(Pp + 0.25), dx_(d["x_t"] + 8), dy_(Pp) + 20, "0.5 X 45° INNER PAD, 0.4 X 30° RIB", "start", 2.4)
X = fcf(dx_(d["notch_x1"] + 4), dy_(d["roof"] + 2) - 9, "⏥", "0.03", []); line(dx_(d["notch_x1"] + 4), dy_(d["roof"] + 2) - 6, dx_(d["notch_x1"] + 0.6), dy_(Pp) + 0.3, "d"); arrow(dx_(d["notch_x1"] + 0.6), dy_(Pp) + 0.3, -100)
text(dx_(d["notch_x1"] + 4) + 17, dy_(d["roof"] + 2) - 5, "BOTH PADS, ONE PLANE", 2.4, "start")
# ---- NOTES ----
NX, NY = 232.0, 22.0
notes = ["NOTES (UNLESS OTHERWISE SPECIFIED):",
 "1. MATERIAL: 6061-T6 ALUMINUM, 1/2 IN PLATE OR 1/2 X 1-1/4 FLAT BAR. ALT: 7075-T6 (SEE 03_FEA).",
 "2. UNITS MM. TOLERANCES: X.X ±0.1   X.XX ±0.05   ANGLES ±0.5°. ASME Y14.5-2018.",
 "3. PLATE THICKNESS (12.7) IS STOCK, UNMACHINED, ±0.2. PLATE FACES = DATUM A. FLOOR BOTTOM = DATUM B.",
 "4. THE PROFILE IS ONE 2.5D CUT THROUGH THE PLATE: ALL INTERNAL CORNERS R1.7 MIN (1/8 IN END MILL + 0.1)",
 "   EXCEPT THE ARM ROOT BLEND R3.0. NO SAW, NO SECOND SETUP. WATERJET/LASER ACCEPTABLE ONLY IF",
 "   THE 0.25 RIB HEIGHT, THE 1.10 ARM AND THE 7.80 PAD PLANE HOLD THEIR TOLERANCES THROUGH THE THICKNESS.",
 "5. CARD-CONTACT EDGES (RIB TOP, BOTH PAD LANDS, NOTCH LIPS): BREAK 0.2-0.3, NO BURR. ALL OTHER EDGES 0.2-0.4.",
 "6. ARM THICKNESS 1.10 ±0.03 OVER ITS FULL LENGTH: THIN-WALL, FINISH LAST, LIGHT PASSES. WITNESS LINES OK.",
 "7. ID DIMPLES: DICE PATTERN, 1-6 PER PART PER GROUP ID (POSITIONS SHOWN FOR 6). SEE RFQ TABLE.",
 "8. FINISH: TYPE II ANODIZE PER MIL-A-8625, COLOR PER RFQ TABLE. MASK NOTHING. ANODIZE AFTER DEBURR.",
 "   RIB HEIGHT (0.25) MEASURED AFTER ANODIZE.",
 "9. TAB WITNESS MARKS PERMITTED ON THE TOP EDGE AT X5 AND X60, 0.2 MAX PROUD, BLENDED.",
 "10. FUNCTIONAL TEST (SAMPLE 10%): 1 CARD AND 24 CARDS (0.127 MM INDEX) PUSH ON BY HAND; GROUP STAYS IN",
 "    WHEN LIFTED BY THE HANDLE AND SHAKEN. NO PERMANENT SET AFTER 30 CARDS X 20 CYCLES. NO CARD CREASE.",
 "11. SOURCE MODEL: SAFT-V2-TAB_v2.step (FreeCAD 1.0). THE STEP GOVERNS UNDIMENSIONED GEOMETRY."]
for i, n in enumerate(notes): text(NX, NY + i * 4.9, n, 2.7 if i else 3.1, "start")
# ---- TITLE BLOCK ----
bx, by, bw, bh = SHEET_W - 10 - 150, SHEET_H - 10 - 42, 150, 42
o(f'<rect class="b" x="{bx}" y="{by}" width="{bw}" height="{bh}"/>')
for yy in (11, 22, 31): line(bx, by + yy, bx + bw, by + yy, "v")
line(bx + 112, by, bx + 112, by + 31, "v"); line(bx + 72, by + 11, bx + 72, by + 31, "v")
text(bx + 2, by + 8, "HALDO LABS · AUTOMATIC FACTORY TESTING V2", 2.7, "start"); text(bx + 131, by + 8, "A3  2:1", 3.0)
text(bx + 2, by + 15, "TITLE", 2.0, "start"); text(bx + 2, by + 20.5, "CARD-STACK KEEPER, WEAVE FLEXURE", 3.1, "start")
text(bx + 74, by + 15, "PART NO.", 2.0, "start"); text(bx + 74, by + 20.5, "SAFT-V2-TAB", 3.1, "start")
text(bx + 114, by + 15, "REV", 2.0, "start"); text(bx + 114, by + 20.5, "v2", 3.1, "start")
text(bx + 130, by + 15, "SHEET", 2.0, "start"); text(bx + 130, by + 20.5, "1 OF 1", 3.1, "start")
text(bx + 2, by + 26, "DRAWN: CLAUDE FABLE 5.1 (THE INSTRUMENT)  2026-10-22", 2.3, "start"); text(bx + 2, by + 29.8, "CHECKED: J. GARMAN   APPROVED: ________", 2.3, "start")
text(bx + 74, by + 26, "MATL: 6061-T6", 2.3, "start"); text(bx + 74, by + 29.8, f"MASS: {P['mass_g']:.1f} g", 2.3, "start")
text(bx + 114, by + 26, "FINISH: ANOD II", 2.3, "start"); text(bx + 114, by + 29.8, "UNITS: mm", 2.3, "start")
text(bx + 2, by + 38, "THIRD ANGLE PROJECTION   ASME Y14.5-2018   DO NOT SCALE DRAWING", 2.5, "start")
o('</svg>')
svg = os.path.join(HERE, "SAFT-V2-TAB.svg"); open(svg, "w").write("\n".join(out)); print("svg written", os.path.getsize(svg))
if shutil.which("inkscape"):
    r = subprocess.run(["inkscape", svg, "--export-type=pdf", "--export-filename=" + svg[:-4] + ".pdf"], capture_output=True, text=True, timeout=300); print("pdf", "ok" if os.path.exists(svg[:-4] + ".pdf") else r.stderr[-300:])
    r = subprocess.run(["inkscape", svg, "--export-type=png", "--export-dpi=110", "--export-filename=" + os.path.join(HERE, "preview.png")], capture_output=True, text=True, timeout=300); print("png", "ok" if os.path.exists(os.path.join(HERE, "preview.png")) else r.stderr[-300:])
