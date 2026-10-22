"""Animates the 2D material-removal simulation of SAFT-V2-TAB_OP10.nc (top view, kerf accumulating move by move,
coloured by tool, Z level in the title) → media/op10_sim.gif / .mp4 / op10_final.png. Also media/op10_setup.png (fixture diagram).
Usage: ~/miniconda3/envs/cae/bin/python animate_cam.py"""
import os, json, math, subprocess, tempfile, sys
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); MEDIA = os.path.join(HERE, "media"); os.makedirs(MEDIA, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, "tests")); os.chdir(os.path.join(HERE, "tests"))
src = open(os.path.join(HERE, "tests", "run_tests.py")).read().split("# ---------------- run ----------------")[0]; __file__ = os.path.join(HERE, "tests", "run_tests.py"); exec(src)   # HERE is now tests/, CAM is 06_cam/
MEDIA = os.path.join(CAM, "media")
ok, moves, rc, err = canonical(os.path.join(CAM, "SAFT-V2-TAB_OP10.nc")); assert ok, err
TOOL_R = {1: C["T1"]["r"], 2: C["T2"]["r"], 3: C["T3"]["r"]}; COL = {1: "#9ecae1", 2: "#fc9272", 3: "#a1d99b"}
blank = box(C["BLANK"]["x"][0], C["BLANK"]["y"][0], C["BLANK"]["x"][1], C["BLANK"]["y"][1])
cut = [m for m in moves if "end" in m and m["kind"] != "STRAIGHT_TRAVERSE" and m.get("tool") in TOOL_R and math.dist(m["start"][:2], m["end"][:2]) > 1e-9]
N = 90; chunks = np.array_split(np.arange(len(cut)), N)
acc = {t: None for t in TOOL_R}; frames = []; tmp = tempfile.mkdtemp()
fig, ax = plt.subplots(figsize=(10, 4.4), dpi=100)
def draw(title, final=False):
    ax.clear(); bx, by = blank.exterior.xy; ax.fill(bx, by, fc="#ece7dc", ec="#998", lw=0.6)
    for t in (1, 2, 3):
        if acc[t] is not None:
            for g in getattr(acc[t], "geoms", [acc[t]]): x, y = g.exterior.xy; ax.fill(x, y, fc=COL[t], ec="none", alpha=0.9)
    px, py = PART.exterior.xy; ax.plot(px, py, "k", lw=0.5)
    ax.set_aspect("equal"); ax.set_xlim(C["BLANK"]["x"][0] - 2, C["BLANK"]["x"][1] + 2); ax.set_ylim(-5, 34); ax.set_title(title, fontsize=9, loc="left")
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
for i, idx in enumerate(chunks):
    if len(idx) == 0: continue
    new = {}
    for k in idx:
        m = cut[k]; t = m["tool"]; new.setdefault(t, []).append(LineString([m["start"][:2], m["end"][:2]]).buffer(TOOL_R[t], quad_segs=16))
    for t, polys in new.items(): acc[t] = unary_union([acc[t]] + polys) if acc[t] is not None else unary_union(polys)
    last = cut[idx[-1]]; draw(f"OP10 2D kerf simulation · move {idx[-1] + 1}/{len(cut)} · T{last['tool']} · Z {last['end'][2]:.2f} mm (projection of all levels so far)")
    fn = os.path.join(tmp, f"f{i:03d}.png"); fig.savefig(fn, bbox_inches="tight"); frames.append(fn)
draw("OP10 complete — blue T1 1/4 in kerf, red T2 1/8 in rest + pocket, green T3 dimples; black = CAD profile"); fig.savefig(os.path.join(MEDIA, "op10_final.png"), bbox_inches="tight", dpi=130)
for _ in range(10): fn = os.path.join(tmp, f"f{len(frames):03d}.png"); fig.savefig(fn, bbox_inches="tight"); frames.append(fn)
imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
imgs[0].save(os.path.join(MEDIA, "op10_sim.gif"), save_all=True, append_images=imgs[1:], duration=90, loop=0, optimize=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "10", "-i", os.path.join(tmp, "f%03d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", os.path.join(MEDIA, "op10_sim.mp4")], check=False)
# setup diagram: side view of the fixture
fig2, ax2 = plt.subplots(figsize=(8, 3.2), dpi=130)
ax2.add_patch(plt.Rectangle((-20, -40), 130, 25, fc="#bbb", ec="k")); ax2.text(45, -30, "sacrificial aluminium subplate on the VF-2 table (T-slot clamped)", ha="center", fontsize=7)
ax2.add_patch(plt.Rectangle((C["BLANK"]["x"][0], -12.7), C["BLANK"]["x"][1] - C["BLANK"]["x"][0], 12.7, fc="#ece7dc", ec="k")); ax2.text(37, -6.5, "blank 12.7 x 31.75 x 82.55, part profile cut through (+0.3 into the subplate)", ha="center", fontsize=7)
for sx_, _ in C["SCREWS"]: ax2.add_patch(plt.Rectangle((sx_ - 3, -30), 6, 31.5, fc="#777", ec="k")); ax2.add_patch(plt.Rectangle((sx_ - 5, 0), 10, 3.5, fc="#555", ec="k")); ax2.text(sx_, 5.5, "M6 low-head\nY28 in waste strip", ha="center", fontsize=6.5)
ax2.annotate("tools enter from +Z: T1 1/4 EM, T2 1/8 EM (4xD reach), T3 1/8 ball", (40, 10), (40, 16), fontsize=7, ha="center", arrowprops=dict(arrowstyle="->"))
ax2.set_xlim(-25, 115); ax2.set_ylim(-42, 22); ax2.set_aspect("equal"); ax2.axis("off"); ax2.set_title("OP10 setup, side view (X-Z): one setup, plate flat, no vise", fontsize=8)
fig2.savefig(os.path.join(MEDIA, "op10_setup.png"), bbox_inches="tight"); print("cam animation ok", len(frames))
