"""3D material-removal verification with CAMotics' headless simulator (camsim, built from source on this host).
Writes a .camotics project (tools + workpiece + nc), runs camsim → simulated stock STL, then compares the stock to the
CAD target: 2D sections at chosen depths (gouge / missed area, Hausdorff) and ray-cast depths at listed probe points.
Usage: ~/miniconda3/envs/cae/bin/python camotics_check.py spec.json
spec.json: {"nc": "...OP10.nc", "out_dir": "...", "resolution": 0.15, "units": "metric",
            "tools": {"1": {"shape": "cylindrical", "diameter": 6.35, "length": 20}, "2": {"shape": "ballnose", "diameter": 3.175, "length": 15}},
            "workpiece": {"min": [-1.75, 0, -12.7], "max": [61.75, 38.1, 0]},
            "target_profile": [[x,y],...] (polygon the stock should match through the thickness, may have holes: "target_holes": [[...]]),
            "section_z": [-6.0, -12.2], "section_clip": [xmin,ymin,xmax,ymax],
            "probes": [{"name":"dimple1","x":2.5,"y":9.0,"expect_z":-0.4,"tol":0.1}, ...]}
"""
import sys, os, json, subprocess, time
import numpy as np, trimesh
from shapely.geometry import Polygon, LineString, MultiPolygon, box
from shapely.ops import unary_union, polygonize
spec = json.load(open(sys.argv[1])); out = spec["out_dir"]; os.makedirs(out, exist_ok=True)
proj = dict(units=spec.get("units", "metric"), **{"resolution-mode": "manual", "resolution": spec.get("resolution", 0.15)},
            tools={k: dict(units="metric", shape=v["shape"], length=v.get("length", 20), diameter=v["diameter"], description=v.get("desc", "")) for k, v in spec["tools"].items()},
            workpiece=dict(automatic=False, margin=0, bounds=dict(min=spec["workpiece"]["min"], max=spec["workpiece"]["max"])),
            files=[os.path.abspath(spec["nc"])])
pfile = os.path.join(out, "sim.camotics"); json.dump(proj, open(pfile, "w"), indent=1)
stl = os.path.join(out, "sim_stock.stl"); t0 = time.time()
r = subprocess.run(["camsim", "--binary", "--resolution", str(spec.get("resolution", 0.15)), pfile, stl], capture_output=True, text=True)
log = os.path.join(out, "camsim.log"); open(log, "w").write(r.stdout + r.stderr)
res = dict(camsim_rc=r.returncode, camsim_s=round(time.time() - t0, 1), resolution=spec.get("resolution", 0.15))
if r.returncode or not os.path.exists(stl):
    res["error"] = (r.stderr or r.stdout)[-500:]; print(json.dumps(res, indent=1)); sys.exit(1)
m = trimesh.load(stl); m.merge_vertices(); trimesh.repair.fill_holes(m); res["stock_volume_mm3"] = round(float(m.volume), 1); res["stock_watertight"] = bool(m.is_watertight); res["faces"] = len(m.faces)
tgt = Polygon(spec["target_profile"], holes=spec.get("target_holes", [])).buffer(0)
clip = box(*spec["section_clip"]) if spec.get("section_clip") else None
res["sections"] = {}
for z in spec.get("section_z", []):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None: res["sections"][str(z)] = "no section"; continue
    # use the section's own XY (to_2D() would recentre it); snap to 0.01 mm so near-miss loop ends close, then polygonize
    from shapely import set_precision
    lines = unary_union([set_precision(LineString(sec.vertices[ent.points][:, :2]), 0.01) for ent in sec.entities if len(ent.points) > 1])
    polys = list(polygonize(lines))
    # polygonize returns every planar face (material regions AND voids such as a through-pocket). Keep the faces whose
    # representative point lies inside the simulated solid (ray-parity test on the mesh at this z).
    pts = np.array([[q.representative_point().x, q.representative_point().y, z] for q in polys]) if polys else np.zeros((0, 3))
    inside = m.contains(pts) if len(pts) else []
    stock2d = unary_union([q for q, ok in zip(polys, inside) if ok]).buffer(0) if polys else Polygon()
    if clip is not None: stock2d = stock2d.intersection(clip); tgt_c = tgt.intersection(clip)
    else: tgt_c = tgt
    gouge = tgt_c.difference(stock2d).area; extra = stock2d.difference(tgt_c).area
    haus = stock2d.boundary.hausdorff_distance(tgt_c.boundary) if not stock2d.is_empty else None
    res["sections"][str(z)] = dict(stock_area=round(stock2d.area, 2), target_area=round(tgt_c.area, 2), gouge_area=round(gouge, 3), extra_material_area=round(extra, 3), hausdorff=round(haus, 3) if haus is not None else None)
res["probes"] = []
if spec.get("probes"):
    origins = np.array([[p["x"], p["y"], 50.0] for p in spec["probes"]]); dirs = np.tile([0, 0, -1.0], (len(origins), 1))
    loc, idx, _ = m.ray.intersects_location(origins, dirs, multiple_hits=False)
    hit = {int(i): float(l[2]) for l, i in zip(loc, idx)}
    for i, p in enumerate(spec["probes"]):
        z = hit.get(i)
        ok = (z is None) if p["expect_z"] is None else (z is not None and abs(z - p["expect_z"]) <= p.get("tol", 0.1))   # expect_z null = "cut through, no surface"
        res["probes"].append(dict(name=p["name"], z=round(z, 3) if z is not None else None, expect=p["expect_z"], ok=bool(ok)))
res["ok"] = all(v.get("gouge_area", 1) < spec.get("gouge_tol", 0.5) and (v.get("hausdorff") or 9) < spec.get("haus_tol", 0.3) for v in res["sections"].values() if isinstance(v, dict)) and all(p["ok"] for p in res["probes"])
json.dump(res, open(os.path.join(out, "camotics_check.json"), "w"), indent=1); print(json.dumps(res, indent=1))
