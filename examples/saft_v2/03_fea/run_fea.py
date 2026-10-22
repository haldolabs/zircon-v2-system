"""Static FEA of SAFT-V2-TAB: Gmsh (C3D10) + CalculiX 2.23.
Load model (the honest one, see fea_report.md): the card stack is a rigid spacer between the two tooth pads and the rib.
It transmits a pure force F (no moment: the stack is a lever balanced on the rib, so each pad carries F/2) — so the
load is F/2 UP on each pad's contact line and F DOWN on the rib top, a self-equilibrated loop that puts the arm, the
tooth, the root AND the floor rail in series, exactly as in the real part. The back face is fixed only to kill rigid
body motion (it carries zero reaction). A unit run gives the loop compliance c = (pad lift − rib drop)/F; a stack of
n cards then needs F = (n·0.127 + d0)/c, and each case is re-run at that force so the .frd can be animated.
Usage: ~/miniconda3/envs/cae/bin/python run_fea.py v1 v2   → <ver>/tab_<case>.inp/.frd/.dat, <ver>/results.json"""
import sys, os, json, math, subprocess, time
import numpy as np, gmsh
HERE = os.path.dirname(os.path.abspath(__file__)); DESIGN = os.path.join(HERE, "..", "02_design")
CCX = os.path.expanduser("~/miniconda3/envs/cae/bin/ccx")
MAT = {"6061-T6": dict(E=69000.0, nu=0.33, yield_MPa=276.0, fatigue_MPa=96.0, rho=2.70e-9),
       "7075-T6": dict(E=71700.0, nu=0.33, yield_MPa=503.0, fatigue_MPa=159.0, rho=2.81e-9)}
T_CARD = 0.127
CASES = {"1_card": 1, "12_cards": 12, "24_cards": 24, "30_cards": 30}
TET10_MAP = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]

def mesh(ver, P, out):
    p, d = P["params"], P["derived"]; W = p["W"]; e = 1e-3
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.model.add(ver)
    gmsh.model.occ.importShapes(os.path.join(DESIGN, ver, f"SAFT-V2-TAB_{ver}.step")); gmsh.model.occ.synchronize()
    vols = gmsh.model.getEntities(3); assert len(vols) == 1
    fix = gmsh.model.getEntitiesInBoundingBox(-e, -e, -e, e, d["H"] + e, W + e, 2)
    pad_in = gmsh.model.getEntitiesInBoundingBox(d["x_t"] - e, d["P"] - e, -e, d["x_t"] + e, d["P"] + e, W + e, 1)
    pad_out = gmsh.model.getEntitiesInBoundingBox(d["notch_x1"] - e, d["P"] - e, -e, d["notch_x1"] + e, d["P"] + e, W + e, 1)
    rib = gmsh.model.getEntitiesInBoundingBox(d["x_r"] - 1, d["rib_top"] - e, -e, d["x_r"] + 1, d["rib_top"] + e, W + e, 2)
    assert fix and pad_in and pad_out and rib, (fix, pad_in, pad_out, rib)
    for dim, ents, tag, name in ((3, vols, 1, "PART"), (2, fix, 2, "FIX"), (1, pad_in, 3, "PAD_IN"), (1, pad_out, 4, "PAD_OUT"), (2, rib, 5, "RIB")):
        gmsh.model.addPhysicalGroup(dim, [t for _, t in ents], tag, name)
    # size fields: fine on the arm (3+ elements through the thickness) and at the root blend, moderate on tooth/rib/floor
    rw = p["root_w"]; H = d["H"]; tmin = min(p["arm_t"], p["arm_t_tip"])
    fields = []
    def boxf(vin, x0, x1, y0, y1):
        f = gmsh.model.mesh.field.add("Box")
        for k, v in dict(VIn=vin, VOut=1.3, XMin=x0, XMax=x1, YMin=y0, YMax=y1, ZMin=-1, ZMax=W + 1, Thickness=1.5).items(): gmsh.model.mesh.field.setNumber(f, k, v)
        fields.append(f)
    boxf(0.22, rw - 1, rw + p["r_root"] + 3, H - p["arm_t"] - p["r_root"] - 1, H + 1)          # root blend
    boxf(tmin / 3.2, rw, d["x_t"] + 1, H - max(p["arm_t"], p["arm_t_tip"]) - 0.5, H + 1)            # arm
    boxf(0.45, d["x_t"] - 1, d["L"] + 1, d["P"] - 1, d["arm_under"] + 1)                               # tooth
    boxf(0.4, d["x_r"] - 3, d["x_r"] + 3, p["floor_t"] - 1, d["rib_top"] + 1)                          # rib
    fmin = gmsh.model.mesh.field.add("Min"); gmsh.model.mesh.field.setNumbers(fmin, "FieldsList", fields); gmsh.model.mesh.field.setAsBackgroundMesh(fmin)
    for k, v in (("Mesh.MeshSizeExtendFromBoundary", 0), ("Mesh.MeshSizeFromPoints", 0), ("Mesh.MeshSizeFromCurvature", 0),
                 ("Mesh.ElementOrder", 2), ("Mesh.SecondOrderIncomplete", 0), ("Mesh.Algorithm3D", 10), ("Mesh.Optimize", 1)):
        gmsh.option.setNumber(k, v)
    gmsh.model.mesh.generate(3); gmsh.write(os.path.join(out, "tab.msh"))
    ntags, coords, _ = gmsh.model.mesh.getNodes(); coords = coords.reshape(-1, 3)
    etypes, etags, enodes = gmsh.model.mesh.getElements(3); assert list(etypes) == [11]
    conn = np.array(enodes[0]).reshape(-1, 10)[:, TET10_MAP]
    sets = {name: gmsh.model.mesh.getNodesForPhysicalGroup(dim, tag)[0] for dim, tag, name in ((2, 2, "FIX"), (1, 3, "PAD_IN"), (1, 4, "PAD_OUT"), (2, 5, "RIB"))}
    gmsh.finalize()
    return ntags, coords, etags[0], conn, sets

def write_inp(path, ntags, coords, etags, conn, sets, mat, F):
    with open(path, "w") as f:
        f.write("*HEADING\nSAFT-V2-TAB card keeper: self-equilibrated clamp loop, F on pads (up) and rib (down)\n*NODE, NSET=NALL\n")
        for n, (x, y, z) in zip(ntags, coords): f.write(f"{n}, {x:.6f}, {y:.6f}, {z:.6f}\n")
        f.write("*ELEMENT, TYPE=C3D10, ELSET=PART\n")
        for t, row in zip(etags, conn): f.write(f"{t}, " + ", ".join(str(int(n)) for n in row) + "\n")
        for name, nodes in sets.items():
            f.write(f"*NSET, NSET={name}\n"); nodes = [int(n) for n in nodes]
            for i in range(0, len(nodes), 12): f.write(", ".join(map(str, nodes[i:i + 12])) + "\n")
        f.write(f"*MATERIAL, NAME=AL\n*ELASTIC\n{mat['E']}, {mat['nu']}\n*DENSITY\n{mat['rho']}\n*SOLID SECTION, ELSET=PART, MATERIAL=AL\n")
        f.write("*STEP\n*STATIC\n*BOUNDARY\nFIX, 1, 3, 0.0\n*CLOAD\n")
        f.write(f"PAD_IN, 2, {F / 2 / len(sets['PAD_IN']):.8e}\nPAD_OUT, 2, {F / 2 / len(sets['PAD_OUT']):.8e}\nRIB, 2, {-F / len(sets['RIB']):.8e}\n")
        f.write("*NODE PRINT, NSET=FIX, TOTALS=ONLY\nRF\n*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n")

def read_frd(path):
    out = {}; cur = None
    for line in open(path):
        if line.startswith(" -4"):
            name = line[5:13].strip(); cur = name if name in ("DISP", "STRESS") else None
            if cur: out[cur] = {}
            continue
        if cur and line.startswith(" -1"):
            nid = int(line[3:13]); out[cur][nid] = [float(line[13 + 12 * i:25 + 12 * i]) for i in range((len(line.rstrip()) - 13) // 12)]
        elif line.startswith(" -3"): cur = None
    return out

def solve(job, ntags, coords, etags, conn, sets, mat, F):
    write_inp(job + ".inp", ntags, coords, etags, conn, sets, mat, F)
    env = dict(os.environ, OMP_NUM_THREADS="24"); t0 = time.time()
    subprocess.run([CCX, "-i", job], cwd=os.path.dirname(job), env=env, check=True, stdout=open(job + ".log", "w"), stderr=subprocess.STDOUT)
    frd = read_frd(job + ".frd"); ids = np.array(sorted(frd["DISP"])); idx = {n: i for i, n in enumerate(ids)}
    U = np.array([frd["DISP"][n][:3] for n in ids]); S = np.array([frd["STRESS"][n][:6] for n in ids])
    sxx, syy, szz, sxy, syz, sxz = S.T
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + sxz ** 2))
    X = coords[np.array([int(n) - 1 for n in ids])]
    return dict(ids=ids, idx=idx, U=U, vm=vm, X=X, t=time.time() - t0)

def run(ver):
    P = json.load(open(os.path.join(DESIGN, ver, f"SAFT-V2-TAB_{ver}_params.json"))); p, d = P["params"], P["derived"]
    out = os.path.join(HERE, ver); os.makedirs(out, exist_ok=True); mat = MAT[p["material"]]
    ntags, coords, etags, conn, sets = mesh(ver, P, out)
    E = mat["E"]; b = p["W"]; rw = p["root_w"]; x_c = (d["x_t"] + d["notch_x1"]) / 2; Lf = p["Lf"]; ex = x_c - d["x_t"]
    # hand calc: cantilever (flexible rw→x_t, rigid tooth to the load centroid x_c); tapered thickness by unit-load integration
    xs = np.linspace(0, Lf, 4000); t_x = p["arm_t"] + (p["arm_t_tip"] - p["arm_t"]) * xs / Lf; I_x = b * t_x ** 3 / 12
    c_arm_hand = float(np.trapezoid((Lf + ex - xs) ** 2 / (E * I_x), xs))                       # mm/N at the load point
    s_hand_perN = float(np.max((Lf + ex - xs) * (t_x / 2) / I_x))                                 # MPa per N, max along the arm
    Lfl = x_c - rw; If = b * p["floor_t"] ** 3 / 12; c_floor_hand = Lfl ** 3 / (3 * E * If)       # floor rail as a cantilever to the rib
    # unit run → loop compliance
    u = solve(os.path.join(out, "tab_unit"), ntags, coords, etags, conn, sets, mat, 1.0)
    def uy(name): return float(np.mean([u["U"][u["idx"][int(n)]][1] for n in sets[name]]))
    pad_in, pad_out, rib = uy("PAD_IN"), uy("PAD_OUT"), uy("RIB")
    c_loop = (pad_in + pad_out) / 2 - rib
    tilt = (pad_out - pad_in) / (d["notch_x1"] - d["x_t"])
    res = dict(version=ver, material=p["material"], nodes=len(ntags), elements=len(etags), sets={k: len(v) for k, v in sets.items()},
               compliance_mm_per_N=dict(loop=c_loop, pads_mean=(pad_in + pad_out) / 2, rib=rib, arm_hand=c_arm_hand, floor_hand=c_floor_hand,
                                        floor_share=-rib / c_loop), k_loop_N_per_mm=1 / c_loop, tooth_tilt_rad_per_N=tilt,
               hand=dict(Lf=Lf, lever_mm=Lf + ex, x_load=x_c, sigma_per_N=s_hand_perN), cases={})
    # mask for the "structural" max: arm + root region, away from the loaded lines (which are point-load singularities)
    X = u["X"]; near_load = np.zeros(len(X), bool)
    for name in ("PAD_IN", "PAD_OUT", "RIB"):
        pts = X[[u["idx"][int(n)] for n in sets[name]]]
        for q in pts[::max(1, len(pts) // 20)]: near_load |= np.linalg.norm(X - q, axis=1) < 1.2
    arm_mask = (X[:, 0] < d["x_t"] + 0.3) & (X[:, 1] > d["stop_top"] - 0.5) & ~near_load
    for case, n in CASES.items():
        inter = n * T_CARD + p["d0"]; F = inter / c_loop
        r = solve(os.path.join(out, f"tab_{case}"), ntags, coords, etags, conn, sets, mat, F)
        vm_arm = r["vm"][arm_mask]; i_arm = int(np.argmax(vm_arm)); vm_max = float(vm_arm[i_arm]); at = X[arm_mask][i_arm]
        vm_glob = float(r["vm"][~near_load].max())
        res["cases"][case] = dict(cards=n, interference_mm=round(inter, 3), clamp_force_N=round(F, 2), pad_lift_mm=round(F * (pad_in + pad_out) / 2, 3),
            rib_drop_mm=round(-F * rib, 3), tooth_tilt_deg=round(math.degrees(F * tilt), 2), vm_max_arm_MPa=round(vm_max, 1), vm_max_at_xyz=[round(float(v), 2) for v in at],
            vm_max_global_excl_loads=round(vm_glob, 1), hand_F_N=round(inter / (c_arm_hand + c_floor_hand), 2), hand_sigma_MPa=round(s_hand_perN * F, 1),
            Kt=round(vm_max / (s_hand_perN * F), 2), SF_yield=round(mat["yield_MPa"] / vm_max, 2), SF_yield_7075=round(503.0 / vm_max, 2), SF_fatigue=round(mat["fatigue_MPa"] / vm_max, 2), solve_s=round(r["t"], 1))
        c = res["cases"][case]
        print(f"{ver} {case}: F {c['clamp_force_N']} N (hand {c['hand_F_N']}), pad lift {c['pad_lift_mm']}, rib drop {c['rib_drop_mm']}, tilt {c['tooth_tilt_deg']}°, vM arm {c['vm_max_arm_MPa']} MPa at {c['vm_max_at_xyz']} (nominal {c['hand_sigma_MPa']}, Kt {c['Kt']}), SF {c['SF_yield']}")
    json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1, default=float)
    print(f"{ver}: {res['nodes']} nodes, {res['elements']} C3D10, loop compliance {c_loop:.5f} mm/N (arm hand {c_arm_hand:.5f} + floor hand {c_floor_hand:.5f}), floor share {res['compliance_mm_per_N']['floor_share']:.2f}")
for v in (sys.argv[1:] or ["v1", "v2"]): run(v)
