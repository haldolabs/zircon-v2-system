"""Stress heat-field animation from the CalculiX results: von Mises on the +Z plate face, deformation exaggerated,
clamp ramped 0 → 100 % (linear static, fields scale with the ramp). Also draws the card stack as a rigid spacer.
Usage: ~/miniconda3/envs/cae/bin/python animate_fea.py v2 24_cards [v1 24_cards ...] → media/fea_<ver>_<case>.gif/.mp4/.png"""
import os, sys, math, json, subprocess, tempfile
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.tri as mtri
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); MEDIA = os.path.join(HERE, "media"); os.makedirs(MEDIA, exist_ok=True)
def read_inp(path):
    nodes = {}; conn = []; mode = None
    for line in open(path):
        if line.startswith("*NODE,"): mode = "n"; continue
        if line.startswith("*ELEMENT,"): mode = "e"; continue
        if line.startswith("*"): mode = None; continue
        if mode == "n": p = line.split(","); nodes[int(p[0])] = [float(p[1]), float(p[2]), float(p[3])]
        elif mode == "e": p = [int(x) for x in line.split(",")]; conn.append(p[1:])
    return nodes, np.array(conn)
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
def run(ver, case):
    dd = os.path.join(HERE, ver); job = os.path.join(dd, f"tab_{case}")
    R = json.load(open(os.path.join(dd, "results.json"))); res = R["cases"][case]
    P = json.load(open(os.path.join(HERE, "..", "02_design", ver, f"SAFT-V2-TAB_{ver}_params.json"))); prm, d = P["params"], P["derived"]; W = prm["W"]
    nodes, conn = read_inp(job + ".inp"); frd = read_frd(job + ".frd")
    ids = np.array(sorted(nodes)); idx = {n: i for i, n in enumerate(ids)}
    X = np.array([nodes[n] for n in ids]); U = np.zeros_like(X); S = np.zeros((len(ids), 6))
    for n, v in frd["DISP"].items(): U[idx[n]] = v[:3]
    for n, v in frd["STRESS"].items(): S[idx[n]] = v[:6]
    sxx, syy, szz, sxy, syz, sxz = S.T
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (sxy ** 2 + syz ** 2 + sxz ** 2))
    c = conn[:, :4]; faces = np.concatenate([c[:, [0, 1, 2]], c[:, [0, 1, 3]], c[:, [0, 2, 3]], c[:, [1, 2, 3]]])
    fz = X[np.vectorize(idx.get)(faces)][:, :, 2]; top = faces[np.all(np.abs(fz - W) < 1e-3, axis=1)]; tri = np.vectorize(idx.get)(top)
    vmax = res["vm_max_arm_MPa"]; scale = 3.0; L = d["L"]; H = d["H"]; n_cards = res["cards"]
    tmp = tempfile.mkdtemp(); files = []
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=100)
    lam_seq = list(np.linspace(0, 1, 24)) + [1.0] * 10 + list(np.linspace(1, 0, 12))
    for i, lam in enumerate(lam_seq):
        ax.clear(); ax.set_aspect("equal"); ax.set_xlim(-3, L + 30); ax.set_ylim(-3, H + 12)
        xd = X[:, 0] + scale * lam * U[:, 0]; yd = X[:, 1] + scale * lam * U[:, 1]
        ax.triplot(mtri.Triangulation(X[:, 0], X[:, 1], tri), color="#bbb", lw=0.12)
        tc = ax.tripcolor(mtri.Triangulation(xd, yd, tri), lam * vm, shading="gouraud", cmap="turbo", vmin=0, vmax=vmax)
        if i == 0: cb = fig.colorbar(tc, ax=ax, fraction=0.03, pad=0.02); cb.set_label("von Mises (MPa)")
        # the card stack: a rigid spacer from the stop wall out of the mouth, thickness n·0.127 (drawn at the same exaggeration), on the rib
        st = n_cards * 0.127 * lam * scale; y_rib = d["rib_top"] - scale * lam * res["rib_drop_mm"]
        ax.add_patch(plt.Rectangle((d["x_s"] + 0.3, y_rib), L + 28 - d["x_s"], max(st, 0.05), fc="#f0d9a0", ec="#b08a40", lw=0.5, alpha=0.9))
        ax.set_title(f"SAFT-V2-TAB {ver} · {case.replace('_', ' ')} · interference {lam * res['interference_mm']:.2f} mm (×{scale:.0f} shown) · "
                     f"clamp {lam * res['clamp_force_N']:.1f} N · max vM {lam * vmax:.0f} MPa at the arm root · SF {res['SF_yield']:.2f} (6061) / {res['SF_yield_7075']:.2f} (7075)", fontsize=9, loc="left")
        ax.text(1, H + 9.5, "colour capped at the arm-root max; the loaded lines on the pads and rib are point-load singularities", fontsize=7, color="#555")
        ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
        fn = os.path.join(tmp, f"f{i:03d}.png"); fig.savefig(fn, bbox_inches="tight"); files.append(fn)
        if i == 23: fig.savefig(os.path.join(MEDIA, f"fea_{ver}_{case}.png"), bbox_inches="tight", dpi=130)
    imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE, colors=128) for f in files]
    imgs[0].save(os.path.join(MEDIA, f"fea_{ver}_{case}.gif"), save_all=True, append_images=imgs[1:], duration=80, loop=0, optimize=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(tmp, "f%03d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", os.path.join(MEDIA, f"fea_{ver}_{case}.mp4")], check=False)
    print(ver, case, "frames", len(files), "top-face tris", len(tri), "vmax", vmax)
if __name__ == "__main__":
    args = sys.argv[1:] or ["v2", "24_cards"]
    for i in range(0, len(args), 2): run(args[i], args[i + 1])
