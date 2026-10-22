"""Deterministic tests for SAFT-V2-TAB_OP10.nc.
T1 rs274 parse (LinuxCNC interpreter) → canonical move dump
T2 envelope: canonical coords + G54 work offset inside the VF-2 travel
T3 2D material-removal sim (shapely swaths of every full-depth move, per tool) vs the exact CAD section: gouge area,
   part-boundary Hausdorff, every tool-reachable void inside the part envelope actually cut, tabs present
T4 analytics: dimple positions vs CAD, as-machined arm / floor / rib thicknesses, tab heights, rest-segment coverage
T5 cycle time per tool from the canonical dump; chip load / MRR sanity
Usage: ~/miniconda3/envs/cae/bin/python run_tests.py   → test_results.json"""
import os, re, json, math, subprocess, configparser
import numpy as np
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); CAM = os.path.dirname(HERE); DESIGN = os.path.join(CAM, "..", "02_design", "v2")
P = json.load(open(os.path.join(DESIGN, "SAFT-V2-TAB_v2_params.json"))); prm, d = P["params"], P["derived"]
PART = Polygon(json.load(open(os.path.join(DESIGN, "profile.json")))[0]).buffer(0)
C = json.load(open(os.path.join(CAM, "cam.json"))); L, H, W = d["L"], d["H"], prm["W"]
RAPID = 25400.0; TOOLCHANGE_S = 4.0
cfg = configparser.ConfigParser(strict=False); cfg.read(os.path.join(HERE, "vf2.ini"))
LIM = {ax: (float(cfg[f"AXIS_{ax}"]["MIN_LIMIT"]), float(cfg[f"AXIS_{ax}"]["MAX_LIMIT"])) for ax in "XYZ"}
OFF = {k.upper(): [float(v) for v in cfg["WORK"][k].split(",")] for k in cfg["WORK"]}
results = {"tests": {}}
def rec(name, ok, **kw): results["tests"][name] = dict(ok=bool(ok), **kw); print(("PASS " if ok else "FAIL ") + name, {k: v for k, v in kw.items() if k != "violations"})
def canonical(nc):
    out = subprocess.run(["rs274", "-i", os.path.join(HERE, "vf2.ini"), "-t", os.path.join(HERE, "tool.tbl"), "-g", nc], capture_output=True, text=True, cwd=HERE)
    open(nc + ".canon", "w").write(out.stdout + out.stderr)
    moves = []; pos = [0.0, 0.0, 0.0]; feed = None; tool = None
    for line in out.stdout.splitlines():
        m = re.search(r"N(\S+)\s+(\w+)\((.*)\)", line)
        if not m: continue
        kind, args = m.group(2), [x.strip() for x in m.group(3).split(",")] if m.group(3).strip() else []
        try: nums = [float(x) for x in args]
        except ValueError: nums = []
        if kind == "SET_FEED_RATE": feed = nums[0]
        elif kind in ("CHANGE_TOOL", "SELECT_TOOL"): tool = int(nums[0]) if nums else tool
        elif kind in ("STRAIGHT_FEED", "STRAIGHT_TRAVERSE"):
            end = nums[:3]; moves.append(dict(kind=kind, start=pos[:], end=end, feed=feed, tool=tool)); pos = end
        elif kind == "ARC_FEED":
            ex, ey, cx, cy, rot, ez = nums[0], nums[1], nums[2], nums[3], int(nums[4]), nums[5]; sx, sy, sz = pos
            a0 = math.atan2(sy - cy, sx - cx); a1 = math.atan2(ey - cy, ex - cx); r = math.hypot(sx - cx, sy - cy); dd = a1 - a0
            if rot > 0:
                while dd <= 1e-9: dd += 2 * math.pi
            else:
                while dd >= -1e-9: dd -= 2 * math.pi
            n = max(4, int(abs(dd) / math.radians(2))); prev = pos[:]
            for i in range(1, n + 1):
                p_ = [cx + r * math.cos(a0 + dd * i / n), cy + r * math.sin(a0 + dd * i / n), sz + (ez - sz) * i / n]
                moves.append(dict(kind="ARC_FEED", start=prev, end=p_, feed=feed, tool=tool)); prev = p_
            pos = [ex, ey, ez]
        elif kind == "DWELL": moves.append(dict(kind="DWELL", seconds=nums[0], tool=tool))
    ok = out.returncode == 0 and "error" not in out.stderr.lower() and bool(moves)
    return ok, moves, out.returncode, out.stderr[-300:]
def envelope(moves, wcs):
    off = OFF[wcs]; bad = []
    for m in moves:
        if "end" not in m: continue
        for i, ax in enumerate("XYZ"):
            v = m["end"][i] + off[i]
            if not LIM[ax][0] - 1e-6 <= v <= LIM[ax][1] + 1e-6: bad.append((ax, round(v, 3), m["kind"]))
    return bad
def cycle_time(moves):
    per_tool = {}; tf = tr = td = 0.0; dist = 0.0
    for m in moves:
        if m["kind"] == "DWELL": td += m["seconds"]; continue
        dd = math.dist(m["start"], m["end"]); t = m.get("tool")
        if m["kind"] == "STRAIGHT_TRAVERSE": tr += dd / RAPID * 60
        elif m["feed"]: tf += dd / m["feed"] * 60; dist += dd; per_tool[t] = per_tool.get(t, 0.0) + dd / m["feed"] * 60
    tools = sorted(k for k in per_tool if k is not None)
    return dict(feed_s=round(tf, 1), rapid_s=round(tr, 1), dwell_s=td, toolchange_s=TOOLCHANGE_S * len(tools), total_s=round(tf + tr + td + TOOLCHANGE_S * len(tools), 1),
                feed_dist_mm=round(dist, 1), feed_s_per_tool={str(k): round(v, 1) for k, v in per_tool.items()}, tools=tools)
def swath(moves, r, tool, zmax):
    segs = [LineString([m["start"][:2], m["end"][:2]]) for m in moves if m.get("tool") == tool and "end" in m and m["kind"] != "STRAIGHT_TRAVERSE"
            and max(m["start"][2], m["end"][2]) <= zmax + 1e-9 and math.dist(m["start"][:2], m["end"][:2]) > 1e-9]
    return unary_union([s.buffer(r, quad_segs=48) for s in segs]) if segs else Point(0, 0).buffer(0)
# ---------------- run ----------------
nc = os.path.join(CAM, "SAFT-V2-TAB_OP10.nc"); ok, moves, rc, err = canonical(nc)
rec("T1_rs274_parse", ok, moves=len(moves), rc=rc, stderr=err.strip()[-120:])
bad = envelope(moves, "G54"); rec("T2_envelope", not bad, wcs="G54", offset=OFF["G54"], violations=bad[:5], n_violations=len(bad))
ct = cycle_time(moves); results["tests"]["T5_cycle_time"] = ct; print("INFO T5_cycle_time", ct)
# T3: full-depth 2D kerf sim
R1, R2 = C["T1"]["r"], C["T2"]["r"]; zfull = -(W - 0.01)
blank = box(C["BLANK"]["x"][0], C["BLANK"]["y"][0], C["BLANK"]["x"][1], C["BLANK"]["y"][1])
rem1 = swath(moves, R1, 1, zfull); rem2 = swath(moves, R2, 2, zfull); removed = unary_union([rem1, rem2])
gouge_poly = removed.intersection(PART); gouge = gouge_poly.area
gouge_depth = max((PART.boundary.distance(Point(v)) for g in getattr(gouge_poly, "geoms", [gouge_poly]) if g.area > 1e-6 for v in g.exterior.coords), default=0.0)   # deepest penetration into the part
remaining = blank.difference(removed)
part_region = remaining.intersection(box(-1, -1, L + 1, H))                 # clip at the top edge: above it is tab + waste strip
haus = part_region.boundary.hausdorff_distance(PART.boundary)
area_err = abs(part_region.area - PART.area)
# every void a 1/8" can reach inside the part envelope (below the top edge) must be cut
reach = box(-40, -40, L + 40, H + 40).difference(PART).buffer(-R2).buffer(R2)
must_cut = reach.intersection(box(-0.5, 0, L + 0.5, H)).intersection(blank)
missed = must_cut.difference(removed).area
tabs = C["TABS"]; tab_fp = remaining.intersection(box(-1, H + 0.02, L + 1, H + 2 * R1 - 0.1))   # inside the T1 kerf band above the top edge
tab_parts = [g for g in getattr(tab_fp, "geoms", [tab_fp]) if g.area > 0.5]
rec("T3_kerf_sim", gouge < 0.05 and gouge_depth < 0.01 and haus < 0.05 and missed < 0.5 and len(tab_parts) == len(tabs["x"]),
    gouge_area_mm2=round(gouge, 4), gouge_max_depth_mm=round(gouge_depth, 4), hausdorff_mm=round(haus, 4), area_error_mm2=round(area_err, 3), part_area_mm2=round(part_region.area, 2), cad_area_mm2=round(PART.area, 2),
    missed_reachable_void_mm2=round(missed, 4), tabs_found=len(tab_parts), tab_areas_mm2=[round(g.area, 2) for g in tab_parts], tab_x=[round(g.centroid.x, 1) for g in tab_parts])
# tab height check: moves along the top edge at the tab z
ztab = -(W - tabs["height"]); tab_moves = [m for m in moves if m.get("tool") == 1 and "end" in m and abs(m["end"][2] - ztab) < 1e-6 and abs(m["start"][2] - ztab) < 1e-6]
rec("T4_tabs", len(tab_moves) == len(tabs["x"]) and all(abs(m["end"][1] - (H + R1)) < 1e-6 for m in tab_moves), tab_moves=len(tab_moves), z_tab=ztab, tab_height=tabs["height"])
# dimples
dimp = [tuple(m["end"][:2]) for m in moves if m.get("tool") == 3 and m["kind"] == "STRAIGHT_FEED" and m["end"][2] <= -0.39]
cad_d = P["dimple_xy"]; dmatch = len(dimp) == len(cad_d) and all(any(math.dist(q, c) < 0.01 for c in cad_d) for q in dimp)
rec("T4_dimples", dmatch, programmed=len(dimp), cad=len(cad_d), depth=-0.4)
# as-machined thicknesses from the simulated section (vertical cuts through the part region)
def spans(x):
    cut = part_region.intersection(LineString([(x, -1), (x, H + 1)]))
    segs_ = [g for g in getattr(cut, "geoms", [cut]) if g.length > 0]
    return sorted([(round(min(g.xy[1]), 3), round(max(g.xy[1]), 3)) for g in segs_])
arm_x = (prm["root_w"] + d["x_t"]) / 2; sp_arm = spans(arm_x); sp_rib = spans(d["x_r"]); sp_tooth = spans((d["x_t"] + d["notch_x0"]) / 2)
arm_t = sp_arm[-1][1] - sp_arm[-1][0]; floor_t = sp_arm[0][1] - sp_arm[0][0]; rib_top = sp_rib[0][1]; pad_y = sp_tooth[-1][0]
rec("T4_as_machined", abs(arm_t - prm["arm_t"]) < 0.02 and abs(rib_top - d["rib_top"]) < 0.02 and abs(pad_y - d["P"]) < 0.02,
    arm_thickness=round(arm_t, 3), arm_cad=prm["arm_t"], floor_thickness=round(floor_t, 3), rib_top=round(rib_top, 3), rib_top_cad=d["rib_top"], pad_plane=round(pad_y, 3), pad_cad=d["P"],
    interference=round(rib_top - pad_y, 3))
# rest segments: T2 must cut every part of the profile wall T1 could not reach
tab_zone = unary_union([box(tx - tabs["width"] / 2 - R1, H - 0.05, tx + tabs["width"] / 2 + R1, H + 1) for tx in tabs["x"]])   # the top edge under a tab is uncut by design
wall_not_t1 = PART.boundary.difference(tab_zone).difference(rem1.buffer(0.02)); wall_left = wall_not_t1.difference(rem2.buffer(0.02))
rec("T4_rest_coverage", wall_left.length < 0.5, wall_length_T1_missed_mm=round(wall_not_t1.length, 1), wall_uncut_after_T2_mm=round(wall_left.length, 3), rest_segments=len(C["rest_segments"]))
# T5 extras
T1_, T2_ = C["T1"], C["T2"]
fs = dict(T1_chipload_mm=round(T1_["f"] / (T1_["rpm"] * T1_["flutes"]), 4), T1_SFM=round(T1_["rpm"] * math.pi * T1_["d"] / 304.8), T1_MRR_slot_mm3_min=round(T1_["d"] * T1_["stepdown"] * T1_["f"]),
          T1_power_kW_est=round(T1_["d"] * T1_["stepdown"] * T1_["f"] / 60 * 0.0007, 3), T2_chipload_mm=round(T2_["f"] / (T2_["rpm"] * T2_["flutes"]), 4), T2_SFM=round(T2_["rpm"] * math.pi * T2_["d"] / 304.8),
          T2_MRR_slot_mm3_min=round(T2_["d"] * T2_["stepdown"] * T2_["f"]), T2_reach_xD=round(W / T2_["d"], 1))
results["feeds_speeds"] = fs; print("INFO feeds/speeds", fs)
results["all_pass"] = all(v["ok"] for k, v in results["tests"].items() if "ok" in v)
json.dump(results, open(os.path.join(HERE, "test_results.json"), "w"), indent=1, default=str)
print("ALL PASS" if results["all_pass"] else "SOME FAILED")
