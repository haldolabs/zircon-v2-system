"""Ray-traced product render with Blender Cycles (CPU by default; 48 threads here), headless.
Usage:
  blender -b -P render_raytrace.py -- --stl part.stl --out render.png [--color anodize-blue|clear|black|red|gold|green|raw]
          [--samples 256] [--res 1600x1000] [--view iso|front|top|hero] [--turntable 36] [--paper 8] [--ground]
--turntable N renders N frames around Z into <out>_tt/ and stitches <out>_turntable.mp4 if ffmpeg exists.
--paper N adds a stack of N sheets (0.1 mm each) in the clip's mouth; only N<=8 fits the 0.8 mm rest gap without deforming.
Units: the STL is read as millimetres; the scene is scaled 0.001 so Blender's metres match.
"""
import bpy, sys, os, math, argparse, subprocess, shutil
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser(); ap.add_argument("--stl", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--color", default="anodize-blue"); ap.add_argument("--samples", type=int, default=256); ap.add_argument("--res", default="1600x1000")
ap.add_argument("--view", default="hero"); ap.add_argument("--turntable", type=int, default=0); ap.add_argument("--paper", type=int, default=0); ap.add_argument("--ground", action="store_true", default=True)
ap.add_argument("--gpu", action="store_true"); A = ap.parse_args(argv)
COLORS = {"anodize-blue": (0.08, 0.22, 0.60), "clear": (0.80, 0.81, 0.83), "black": (0.03, 0.03, 0.035), "red": (0.55, 0.05, 0.05),
          "gold": (0.72, 0.52, 0.12), "green": (0.05, 0.35, 0.15), "raw": (0.85, 0.86, 0.88)}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = A.samples; sc.cycles.use_denoising = False   # Debian build has no OpenImageDenoise; use more samples instead
sc.cycles.device = "GPU" if A.gpu else "CPU"; sc.render.film_transparent = False
w, h = [int(v) for v in A.res.lower().split("x")]; sc.render.resolution_x, sc.render.resolution_y = w, h; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"; sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = 0.0   # Standard keeps the anodize colour saturated; AgX washes it out
# part
bpy.ops.wm.stl_import(filepath=A.stl) if hasattr(bpy.ops.wm, "stl_import") else bpy.ops.import_mesh.stl(filepath=A.stl)
part = bpy.context.selected_objects[0]; part.name = "part"; part.scale = (0.001, 0.001, 0.001)
bpy.context.view_layer.objects.active = part; bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30)) if hasattr(bpy.ops.object, "shade_smooth_by_angle") else bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("anodized"); mat.use_nodes = True; bsdf = mat.node_tree.nodes["Principled BSDF"]
c = COLORS.get(A.color, COLORS["raw"]); bsdf.inputs["Base Color"].default_value = (*c, 1)
bsdf.inputs["Metallic"].default_value = 0.0 if A.color.startswith("anodize") or A.color in ("black","red","gold","green","clear") else 1.0
bsdf.inputs["Roughness"].default_value = 0.42; bsdf.inputs["Specular IOR Level"].default_value = 0.4
if "Coat Weight" in bsdf.inputs: bsdf.inputs["Coat Weight"].default_value = 0.15; bsdf.inputs["Coat Roughness"].default_value = 0.2
if A.color in ("raw", "clear"): bsdf.inputs["Metallic"].default_value = 0.9; bsdf.inputs["Roughness"].default_value = 0.32
part.data.materials.append(mat)
bb = [part.matrix_world @ Vector(v) for v in part.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
ctr = (mn + mx) / 2; size = (mx - mn).length
# the clip stands on its anvil bottom (part y=0) → rotate so part Y is world Z (lying on the desk = plate face down is the natural pose; we show it standing on the anvil)
part.rotation_euler = (math.radians(90), 0, 0); bpy.ops.object.transform_apply(rotation=True)
bb = [part.matrix_world @ Vector(v) for v in part.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
part.location.z -= mn.z; ctr = Vector(((mn.x+mx.x)/2, (mn.y+mx.y)/2, (mx.z-mn.z)/2)); part.location.x -= ctr.x; part.location.y -= ctr.y
# paper stack (optional): N sheets × 0.1 mm, lying on the anvil top (part y = 6 → world z = 0.006), entering the mouth from +x
if A.paper:
    t_mm = 0.1 * A.paper
    bpy.ops.mesh.primitive_cube_add(size=1); pap = bpy.context.active_object; pap.name = "paper"
    pap.scale = (0.070, 0.050, t_mm / 1000.0)            # size=1 cube: scale = full edge length (m)
    pap.location = ((0.052 - ctr.x) + 0.035, 0.004, 0.006 + t_mm / 2000.0)   # stack starts at the jaw's back face (part x=52) and runs 70 mm out of the mouth
    pm = bpy.data.materials.new("paper"); pm.use_nodes = True; pb = pm.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.92, 0.92, 0.90, 1); pb.inputs["Roughness"].default_value = 0.9; pap.data.materials.append(pm)
# ground
if A.ground:
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, -0.00002)); g = bpy.context.active_object
    gm = bpy.data.materials.new("desk"); gm.use_nodes = True; gb = gm.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.62, 0.56, 0.48, 1); gb.inputs["Roughness"].default_value = 0.7; g.data.materials.append(gm)
# lights: large soft key, fill, rim
def area(name, loc, energy, size, look_at=(0, 0, 0.006)):
    bpy.ops.object.light_add(type="AREA", location=loc); L = bpy.context.active_object; L.name = name
    L.data.energy = energy; L.data.size = size; d = Vector(look_at) - Vector(loc); L.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return L
area("key", (0.18, -0.22, 0.30), 1.6, 0.35); area("fill", (-0.30, -0.10, 0.18), 0.5, 0.5); area("rim", (0.05, 0.30, 0.25), 1.0, 0.3)   # watts; the scene is 6 cm across
wd = bpy.data.worlds.new("w"); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.85, 0.87, 0.9, 1); wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
# camera
bpy.ops.object.camera_add(); cam = bpy.context.active_object; sc.camera = cam; cam.data.lens = 60
views = {"iso": (0.6, -0.8, 0.55), "hero": (0.75, -0.65, 0.42), "front": (0, -1, 0.15), "top": (0.01, -0.3, 1.0)}
def place(dirv, dist):
    d = Vector(dirv).normalized(); tgt = Vector((0, 0, 0.008)); cam.location = tgt + d * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
dist = size * 3.6
place(views.get(A.view, views["hero"]), dist)
out = os.path.abspath(A.out); os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print("rendered", out)
if A.turntable:
    d = os.path.splitext(out)[0] + "_tt"; os.makedirs(d, exist_ok=True); v0 = Vector(views.get(A.view, views["hero"]))
    for i in range(A.turntable):
        ang = 2 * math.pi * i / A.turntable; x, y = v0.x * math.cos(ang) - v0.y * math.sin(ang), v0.x * math.sin(ang) + v0.y * math.cos(ang)
        place((x, y, v0.z), dist); sc.render.filepath = os.path.join(d, f"f{i:03d}.png"); bpy.ops.render.render(write_still=True)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(d, "f%03d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", os.path.splitext(out)[0] + "_turntable.mp4"])
        print("turntable", os.path.splitext(out)[0] + "_turntable.mp4")
