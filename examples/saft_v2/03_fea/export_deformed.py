"""Export the FEA-deformed outer surface of a case as STL (true scale, or exaggerated) plus the card stack as a second STL,
so the ray tracer can show the keeper actually holding a stack. Usage: python export_deformed.py v2 24_cards [scale]"""
import os, sys, json, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from animate_fea import read_inp, read_frd, HERE
ver, case = sys.argv[1], sys.argv[2]; scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
job = os.path.join(HERE, ver, f"tab_{case}"); res = json.load(open(os.path.join(HERE, ver, "results.json")))["cases"][case]
P = json.load(open(os.path.join(HERE, "..", "02_design", ver, f"SAFT-V2-TAB_{ver}_params.json"))); d = P["derived"]; W = P["params"]["W"]
nodes, conn = read_inp(job + ".inp"); frd = read_frd(job + ".frd")
ids = np.array(sorted(nodes)); idx = {n: i for i, n in enumerate(ids)}; X = np.array([nodes[n] for n in ids]); U = np.zeros_like(X)
for n, v in frd["DISP"].items(): U[idx[n]] = v[:3]
c = conn[:, :4]; faces = np.concatenate([c[:, [0, 1, 2]], c[:, [0, 3, 1]], c[:, [0, 2, 3]], c[:, [1, 3, 2]]])
key = np.sort(faces, axis=1); _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
surf = faces[cnt[inv] == 1]                                    # faces owned by exactly one tet = outer surface
tri = np.vectorize(idx.get)(surf); m = trimesh.Trimesh(X + scale * U, tri, process=True); trimesh.repair.fix_normals(m)
out = job + f"_deformed{'' if scale == 1 else f'_x{scale:g}'}.stl"; m.export(out)
n = res["cards"]; y0 = d["rib_top"] - scale * res["rib_drop_mm"]; st = n * 0.127
cards = trimesh.creation.box(extents=[d["L"] + 48 - (d["x_s"] + 0.3), st, 76.2], transform=trimesh.transformations.translation_matrix([(d["L"] + 48 + d["x_s"] + 0.3) / 2, y0 + st / 2, W / 2]))
cout = os.path.join(HERE, ver, f"cards_{case}.stl"); cards.export(cout)
print(out, len(m.faces), "faces, watertight", m.is_watertight, "| cards", cout, "thickness", st)
