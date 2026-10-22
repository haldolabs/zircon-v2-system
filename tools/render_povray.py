"""Ray-traced render with POV-Ray 3.7 (no Blender needed): STL → mesh2 include + scene, then povray.
Usage: ~/miniconda3/envs/cae/bin/python render_povray.py part.stl out.png [--color anodize-blue|clear|black|red|gold|green|raw] [--res 1600x1000] [--view hero|iso|front] [--quality 9] [--radiosity]
"""
import sys, os, argparse, subprocess, numpy as np, trimesh
ap = argparse.ArgumentParser(); ap.add_argument("stl"); ap.add_argument("out"); ap.add_argument("--color", default="anodize-blue"); ap.add_argument("--res", default="1600x1000")
ap.add_argument("--view", default="hero"); ap.add_argument("--quality", type=int, default=9); ap.add_argument("--radiosity", action="store_true"); ap.add_argument("--turntable", type=int, default=0); ap.add_argument("--up", default="y", help="which STL axis is up: y (a part standing on its y=0 face) or z (as modelled, e.g. machined stock)")
ap.add_argument("--extra", action="append", default=[], metavar="STL:COLOR", help="additional STL(s) in the SAME model coordinates as the part (e.g. a card stack), rendered with COLOR (paper|raw|...); V2 addition")
A = ap.parse_args()
COLORS = {"anodize-blue": (0.08, 0.22, 0.60), "clear": (0.80, 0.81, 0.83), "black": (0.03, 0.03, 0.035), "red": (0.55, 0.05, 0.05), "gold": (0.72, 0.52, 0.12), "green": (0.05, 0.35, 0.15), "raw": (0.85, 0.86, 0.88), "paper": (0.93, 0.89, 0.76)}
m = trimesh.load(A.stl)
T = np.eye(4)
if A.up == "y": T = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]); m.apply_transform(T)   # stand on the y=0 face: STL Y → up
shift = -m.bounds[0] * [0, 0, 1] - (m.bounds[0] + m.bounds[1]) / 2 * [1, 1, 0]; m.apply_translation(shift)
T = trimesh.transformations.translation_matrix(shift) @ T                       # the part's placement, reused for --extra meshes so they stay registered
inc = os.path.splitext(A.out)[0] + "_mesh.inc"; pov = os.path.splitext(A.out)[0] + ".pov"
def write_mesh2(f, name, mm):
    f.write("#declare %s = mesh2 {\n vertex_vectors { %d" % (name, len(mm.vertices))); f.write("".join(f",\n  <{x:.4f},{z:.4f},{y:.4f}>" for x, y, z in mm.vertices)); f.write(" }\n")   # POV is left-handed, Y up: swap y/z
    f.write(" face_indices { %d" % len(mm.faces)); f.write("".join(f",\n  <{a},{b},{c}>" for a, b, c in mm.faces)); f.write(" }\n}\n")
extras = []
with open(inc, "w") as f:
    write_mesh2(f, "Part", m)
    for i, spec in enumerate(A.extra):
        path, _, col = spec.rpartition(":"); me = trimesh.load(path); me.apply_transform(T); write_mesh2(f, f"Extra{i}", me); extras.append((f"Extra{i}", COLORS.get(col, COLORS["paper"])))
c = COLORS.get(A.color, COLORS["raw"]); metal = A.color in ("raw", "clear"); size = float(np.linalg.norm(m.extents))
views = {"hero": (0.75, 0.42, -0.65), "iso": (0.6, 0.55, -0.8), "front": (0.0, 0.15, -1.0)}
v = np.array(views.get(A.view, views["hero"])); v = v / np.linalg.norm(v) * size * 2.2
finish = "finish { ambient 0.05 diffuse 0.75 specular 0.25 roughness 0.03 reflection { 0.08, 0.25 } }" if not metal else "finish { ambient 0.03 diffuse 0.3 specular 0.6 roughness 0.015 metallic reflection { 0.35 metallic } }"
with open(pov, "w") as f:
    f.write(f'''#version 3.7; global_settings {{ assumed_gamma 1.0 {"radiosity { pretrace_start 0.08 pretrace_end 0.01 count 60 recursion_limit 2 }" if A.radiosity else ""} }}
#include "{os.path.basename(inc)}"
camera {{ location <{v[0]:.3f},{v[1]:.3f},{v[2]:.3f}> look_at <0,8,0> angle 32 right x*{A.res.split('x')[0]}/{A.res.split('x')[1]} }}
light_source {{ <180,300,-220> rgb 1.1 area_light <60,0,0>,<0,0,60>, 6,6 adaptive 1 jitter }}
light_source {{ <-300,180,-100> rgb 0.5 shadowless }}
light_source {{ <50,250,300> rgb 0.7 area_light <40,0,0>,<0,0,40>, 4,4 adaptive 1 jitter }}
sky_sphere {{ pigment {{ gradient y color_map {{ [0 rgb <0.75,0.78,0.82>] [1 rgb <0.95,0.96,0.98>] }} }} }}
plane {{ y, -0.02 pigment {{ rgb <0.62,0.56,0.48> }} finish {{ diffuse 0.7 ambient 0.1 }} }}
object {{ Part pigment {{ rgb <{c[0]},{c[1]},{c[2]}> }} {finish} }}
''' + "".join(f"object {{ {nm} pigment {{ rgb <{ec[0]},{ec[1]},{ec[2]}> }} finish {{ ambient 0.08 diffuse 0.85 specular 0.02 roughness 0.2 }} }}\n" for nm, ec in extras))
W, H = A.res.split("x")
def run_pov(povfile, outpng):
    # povray runs in the .pov's directory (so the #include resolves); pass the scene by basename and the output as an
    # absolute path, otherwise a relative path given on the command line is re-resolved against that directory and
    # povray dies with "Cannot parse input" (V2 fix, 2026-10-22).
    return subprocess.run(["povray", f"+I{os.path.basename(povfile)}", f"+O{os.path.abspath(outpng)}", f"+W{W}", f"+H{H}", "+A0.3", "+AM2", f"+Q{A.quality}", "-D", "+FN", "-GA"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(povfile)) or ".")
r = run_pov(pov, A.out); print("povray", "ok" if os.path.exists(A.out) else r.stderr[-400:], A.out)
if A.turntable:
    import shutil
    d = os.path.splitext(A.out)[0] + "_tt"; os.makedirs(d, exist_ok=True); scene = open(pov).read()
    for i in range(A.turntable):
        ang = 2 * np.pi * i / A.turntable; c, s_ = np.cos(ang), np.sin(ang)
        vi = np.array([v[0] * c - v[2] * s_, v[1], v[0] * s_ + v[2] * c])      # rotate the camera about the vertical (POV y) axis
        pv = os.path.join(d, f"f{i:03d}.pov"); open(pv, "w").write(scene.replace(f"location <{v[0]:.3f},{v[1]:.3f},{v[2]:.3f}>", f"location <{vi[0]:.3f},{vi[1]:.3f},{vi[2]:.3f}>").replace(os.path.basename(inc), os.path.abspath(inc)))
        run_pov(pv, os.path.join(d, f"f{i:03d}.png"))
    if shutil.which("ffmpeg"):
        mp4 = os.path.splitext(A.out)[0] + "_turntable.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(d, "f%03d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", mp4]); print("turntable", mp4)
