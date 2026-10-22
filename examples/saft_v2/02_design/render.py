"""Shaded views of the STL models (matplotlib, no GPU): iso / profile / plate-face PNG per version + a turntable GIF of v2,
with a 24-card stack drawn in the mouth of v2. Usage: ~/miniconda3/envs/cae/bin/python render.py"""
import os, json, numpy as np, trimesh, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); MEDIA = os.path.join(HERE, "media"); os.makedirs(MEDIA, exist_ok=True)
def shade(m, base, light=np.array([0.45, -0.55, 0.7])):
    n = m.face_normals; light = light / np.linalg.norm(light); lam = np.clip(n @ light, 0, 1) * 0.6 + 0.4
    return np.clip(np.array(base)[None, :] * lam[:, None], 0, 1)
def view_dir(elev, azim):
    e, az = np.radians(elev), np.radians(azim); return np.array([np.cos(e) * np.cos(az), np.cos(e) * np.sin(az), np.sin(e)])
def cards(P, n=24):
    """a stack of n cards in the mouth: from the stop wall to 40 mm past the tip, lying on the pad plane P"""
    d = P["derived"]; x0 = d["x_s"] + 0.3; x1 = d["L"] + 40; y0 = d["P"]; y1 = y0 + n * 0.127; z0, z1 = -20, P["params"]["W"] + 20
    return trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0], transform=trimesh.transformations.translation_matrix([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]))
def render(parts, elev, azim, title, fn=None, ax=None, lim=None):
    own = ax is None
    if own: fig = plt.figure(figsize=(8, 4.2), dpi=120); ax = fig.add_subplot(111, projection="3d")
    ax.clear(); L, H, W = lim; ax.set_box_aspect((L + 40, H, W + 40)); ax.view_init(elev=elev, azim=azim)
    for m, base in parts:
        keep = (m.face_normals @ view_dir(elev, azim)) > -0.05
        mm = trimesh.Trimesh(m.vertices, m.faces[keep], process=False)
        v, f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=1.5); mm = trimesh.Trimesh(v, f, process=False)
        ax.add_collection3d(Poly3DCollection(mm.vertices[mm.faces], facecolors=shade(mm, base), edgecolors="none", antialiased=False))
    ax.set_xlim(0, L + 40); ax.set_ylim(0, H); ax.set_zlim(-20, W + 20); ax.set_axis_off(); ax.set_title(title, fontsize=9)
    if own: fig.savefig(fn, bbox_inches="tight"); plt.close(fig)
AL = (0.78, 0.80, 0.84); PAPER = (0.93, 0.88, 0.72)
for v in ("v1", "v2"):
    P = json.load(open(os.path.join(HERE, v, f"SAFT-V2-TAB_{v}_params.json"))); d = P["derived"]; lim = (d["L"], d["H"], P["params"]["W"])
    m = trimesh.load(os.path.join(HERE, v, f"SAFT-V2-TAB_{v}.stl"))
    render([(m, AL)], 28, -60, f"SAFT-V2-TAB {v}  ·  {m.volume:.0f} mm³  ·  {m.volume*2.7e-3:.1f} g", os.path.join(MEDIA, f"tab_{v}_iso.png"), lim=lim)
    render([(m, AL)], 0, -90, f"SAFT-V2-TAB {v}  ·  profile", os.path.join(MEDIA, f"tab_{v}_front.png"), lim=lim)
    render([(m, AL)], 90, -90, f"SAFT-V2-TAB {v}  ·  plate face (dimples)", os.path.join(MEDIA, f"tab_{v}_top.png"), lim=lim)
    render([(m, AL), (cards(P), PAPER)], 22, -55, f"SAFT-V2-TAB {v} holding 24 cards (3.05 mm)", os.path.join(MEDIA, f"tab_{v}_cards.png"), lim=lim)
P = json.load(open(os.path.join(HERE, "v2", "SAFT-V2-TAB_v2_params.json"))); d = P["derived"]; lim = (d["L"], d["H"], 12.7)
m = trimesh.load(os.path.join(HERE, "v2", "SAFT-V2-TAB_v2.stl")); st = cards(P)
fig = plt.figure(figsize=(8, 4.2), dpi=80); ax = fig.add_subplot(111, projection="3d"); frames = []
for i in range(36):
    render([(m, AL), (st, PAPER)], 25, -60 + i * 10, "SAFT-V2-TAB v2 turntable", ax=ax, lim=lim)
    fig.canvas.draw(); frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3]).convert("P", palette=Image.ADAPTIVE, colors=64))
frames[0].save(os.path.join(MEDIA, "tab_v2_turntable.gif"), save_all=True, append_images=frames[1:], duration=120, loop=0)
print("renders ok")
