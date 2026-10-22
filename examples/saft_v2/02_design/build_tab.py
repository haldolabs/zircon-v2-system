"""SAFT-V2-TAB — one-piece offset-tooth ("weave") card keeper, built headless in FreeCAD 1.0.
The profile (XY) is extruded through the plate thickness W (Z). Every void is >= the Ø3.175 end mill, so the
whole part is ONE setup from the plate face. Usage: QT_QPA_PLATFORM=offscreen SAFT_VERS="v1 v2" freecadcmd build_tab.py
Writes <ver>/SAFT-V2-TAB_<ver>.step/.stl, <ver>/profile.json (exact mid-plane section), <ver>/..._params.json,
and prints a machinability check (void area a Ø3.175 tool cannot reach)."""
import sys, json, math, os
import FreeCAD, Part
from FreeCAD import Vector as V
TOOL_D = 3.175; TOOL_R = TOOL_D / 2; CLR = TOOL_D + 0.225   # 3.4: minimum void width
VERSIONS = {
    # v1: hand-sized first pass. Uniform 1.2 arm, every concave corner at the tool radius + 0.1.
    "v1": dict(W=12.7, root_w=10.0, Lf=42.0, arm_t=1.2, arm_t_tip=1.2, floor_t=4.0, chan_h=3.8, d0=0.25,
               rib_w=1.6, rib_ch=0.4, pad_in=1.5, ch_in=0.5, pad_out=1.5, lead_deg=30.0, lead_rise=3.6,
               notch_d=3.8, tooth_cap=3.0, stop_clr=0.35, stop_gap=3.6, floor_beyond_rib=8.3, floor_ch=2.0,
               r_tool=1.7, r_root=1.7, pocket_drop=0.0, post_w=3.0, dimples=6, material="6061-T6"),
    # v2: after FEA (v1: 213 MPa at the R1.7 root at 24 cards, SF 1.3; 262 MPa at 30). Arm 1.1 thick and 46 long
    # (stress ∝ t/L², force ∝ t³/L³), R3 root blend; the pocket floor drops 2 mm behind a 3 mm stop post so R3 fits.
    "v2": dict(W=12.7, root_w=10.0, Lf=46.0, arm_t=1.1, arm_t_tip=1.1, floor_t=4.0, chan_h=3.8, d0=0.25,
               rib_w=1.6, rib_ch=0.4, pad_in=1.5, ch_in=0.5, pad_out=1.5, lead_deg=30.0, lead_rise=3.6,
               notch_d=3.8, tooth_cap=3.0, stop_clr=0.35, stop_gap=3.6, floor_beyond_rib=8.3, floor_ch=2.0,
               r_tool=1.7, r_root=3.0, pocket_drop=2.0, post_w=3.0, dimples=6, material="6061-T6"),
}
def derived(p):
    d = {}
    d["P"] = p["floor_t"] + p["chan_h"]                       # pad plane (tooth pads' underside)
    d["rib_top"] = d["P"] + p["d0"]
    d["x_t"] = p["root_w"] + p["Lf"]                          # tooth root face
    d["x_s"] = d["x_t"] - p["stop_gap"]                       # stop wall
    d["stop_top"] = d["P"] + 24 * 0.127 + p["stop_clr"]       # clears a 24-card stack top
    d["notch_x0"] = d["x_t"] + p["pad_in"]; d["notch_x1"] = d["notch_x0"] + CLR + p["rib_w"] + CLR
    d["x_r"] = d["notch_x0"] + CLR + p["rib_w"] / 2           # rib centre
    d["roof"] = d["P"] + p["notch_d"]
    d["arm_under"] = d["roof"] + p["tooth_cap"]               # = tooth top = arm underside at the tooth
    d["H"] = d["arm_under"] + p["arm_t"]                        # arm underside at the ROOT = arm_under; tapered arms rise toward the tooth
    assert d["arm_under"] - d["stop_top"] >= CLR - 1e-6, "pocket too low for the tool"
    d["land_out_x1"] = d["notch_x1"] + p["pad_out"]
    d["lead_run"] = p["lead_rise"] / math.tan(math.radians(p["lead_deg"]))
    d["x_tip"] = d["land_out_x1"] + d["lead_run"]
    d["L"] = d["x_tip"]
    d["floor_tip"] = d["x_r"] + p["floor_beyond_rib"]            # the lower lip ends 8.3 past the rib centre
    return d
def profile_points(p):
    d = derived(p); P = d["P"]; a = p["floor_t"]; rw = p["root_w"]; H = d["H"]
    rib_run = p["rib_ch"] / math.tan(math.radians(30))
    # arm underside: tapered (thickness arm_t at root, arm_t_tip at the tooth) → underside is a sloped line
    under_root = H - p["arm_t"]; under_tip = H - p["arm_t_tip"]
    pts = [(0, 0), (d["floor_tip"], 0), (d["floor_tip"], a - p["floor_ch"]), (d["floor_tip"] - p["floor_ch"], a),
           (d["x_r"] + p["rib_w"] / 2, a), (d["x_r"] + p["rib_w"] / 2, d["rib_top"] - p["rib_ch"]),
           (d["x_r"] + p["rib_w"] / 2 - rib_run, d["rib_top"]), (d["x_r"] - p["rib_w"] / 2, d["rib_top"]),
           (d["x_r"] - p["rib_w"] / 2, a), (d["x_s"], a), (d["x_s"], d["stop_top"])] + (
          [(d["x_s"] - p["post_w"], d["stop_top"]), (d["x_s"] - p["post_w"], d["stop_top"] - p["pocket_drop"]), (rw, d["stop_top"] - p["pocket_drop"])]
          if p["pocket_drop"] > 0 else [(rw, d["stop_top"])]) + [
           (rw, under_root), (d["x_t"], under_tip),
           (d["x_t"], P), (d["x_t"] + p["pad_in"] - p["ch_in"], P), (d["notch_x0"], P + p["ch_in"]),
           (d["notch_x0"], d["roof"]), (d["notch_x1"], d["roof"]), (d["notch_x1"], P), (d["land_out_x1"], P),
           (d["x_tip"], P + p["lead_rise"]), (d["x_tip"], H), (0, H)]
    return pts, d
def build(ver):
    p = VERSIONS[ver]; pts, d = profile_points(p); W = p["W"]; H = d["H"]
    wire = Part.makePolygon([V(x, y, 0) for x, y in pts] + [V(pts[0][0], pts[0][1], 0)])
    solid = Part.Face(wire).extrude(V(0, 0, W))
    def zedges_at(shape, xy_list, tol=1e-3):
        out = []
        for e in shape.Edges:
            a_, b_ = e.Vertexes[0].Point, e.Vertexes[-1].Point
            if abs(a_.x - b_.x) < tol and abs(a_.y - b_.y) < tol and abs(abs(a_.z - b_.z) - W) < tol:
                for (x, y) in xy_list:
                    if abs(a_.x - x) < tol and abs(a_.y - y) < tol: out.append(e)
        return out
    a = p["floor_t"]; rw = p["root_w"]; rt = p["r_tool"]
    under_root = H - p["arm_t"]; under_tip = H - p["arm_t_tip"]
    fillets = [(p["r_root"], [(rw, under_root)]),                                   # arm root (stress riser)
               (rt, ([(rw, d["stop_top"] - p["pocket_drop"]), (d["x_s"] - p["post_w"], d["stop_top"] - p["pocket_drop"])] if p["pocket_drop"] > 0 else [(rw, d["stop_top"])]) + [(d["x_s"], a), (d["x_t"], under_tip), (d["notch_x0"], d["roof"]),
                     (d["notch_x1"], d["roof"]), (d["x_r"] - p["rib_w"] / 2, a), (d["x_r"] + p["rib_w"] / 2, a)])]
    for r, xy in fillets:
        es = zedges_at(solid, xy)
        assert len(es) == len(xy), (r, xy, len(es))
        solid = solid.makeFillet(r, es)
    # ID dimples on the +Z plate face of the root block (dice pattern, up to 6): Ø2.0 × 0.4 deep
    grid = [(3.0, 4.0), (7.0, 4.0), (3.0, H / 2), (7.0, H / 2), (3.0, H - 4.0), (7.0, H - 4.0)]
    order = {1: [2], 2: [0, 5], 3: [0, 2, 5], 4: [0, 1, 4, 5], 5: [0, 1, 2, 4, 5], 6: [0, 1, 2, 3, 4, 5]}[max(1, min(6, p["dimples"]))]
    for i in order:
        x, y = grid[i]; solid = solid.cut(Part.makeSphere(1.5, V(x, y, W + 1.1)))
    solid = solid.removeSplitter()
    assert solid.isValid() and len(solid.Solids) == 1, "bad solid"
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), ver); os.makedirs(out, exist_ok=True)
    base = os.path.join(out, f"SAFT-V2-TAB_{ver}")
    solid.exportStep(base + ".step")
    import Mesh, MeshPart
    m = MeshPart.meshFromShape(Shape=solid, LinearDeflection=0.01, AngularDeflection=0.15, Relative=False); m.write(base + ".stl")
    sec = solid.slice(V(0, 0, 1), W / 2)
    loops = [[[round(v.x, 4), round(v.y, 4)] for v in w.discretize(Deflection=0.003)] for w in sec]
    bb = solid.BoundBox
    info = dict(version=ver, params=p, derived={k: round(v, 4) for k, v in d.items()}, volume_mm3=round(solid.Volume, 2),
                mass_g=round(solid.Volume * 2.70e-3, 2), bbox=[round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
                profile_points=pts, dimple_xy=[grid[i] for i in order], tool_d=TOOL_D)
    json.dump(info, open(base + "_params.json", "w"), indent=1); json.dump(loops, open(os.path.join(out, "profile.json"), "w"))
    print(f"{ver}: L {d['L']:.2f} H {H:.2f} W {W}  volume {info['volume_mm3']} mm3  mass {info['mass_g']} g  faces {len(solid.Faces)}  loops {len(loops)}")
args = [a for a in os.environ.get("SAFT_VERS", "v1 v2").split() if a in VERSIONS]
for v in args: build(v)
