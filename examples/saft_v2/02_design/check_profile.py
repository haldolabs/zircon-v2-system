"""Machinability + geometry checks on the exact FreeCAD mid-plane section.
(1) void reachable by the Ø3.175 end mill: morphological opening of the void region by the tool disk; whatever the
    opening does not cover is material the tool would leave behind (must be ~0).
(2) minimum void width along the card path, interference d0, lead-in angle.
Also draws media/profile_<ver>.png. Usage: ~/miniconda3/envs/cae/bin/python check_profile.py"""
import json, os, math, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon, box
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(HERE, "media"); os.makedirs(M, exist_ok=True)
res = {}
for ver in ("v1", "v2"):
    P = json.load(open(os.path.join(HERE, ver, f"SAFT-V2-TAB_{ver}_params.json"))); d = P["derived"]; p = P["params"]
    loops = json.load(open(os.path.join(HERE, ver, "profile.json")))
    part = Polygon(loops[0]).buffer(0); r = P["tool_d"] / 2
    stock = box(-5, -5, d["L"] + 5, d["H"] + 5).buffer(r + 0.5, quad_segs=32); void = stock.difference(part)   # rounded stock box: no fake corners
    reach = void.buffer(-r, quad_segs=64).buffer(r, quad_segs=64)      # opening = area the tool can sweep clear
    left = void.difference(reach); left = left.buffer(0)
    unreach = [(round(g.centroid.x, 2), round(g.centroid.y, 2), round(g.area, 4)) for g in getattr(left, "geoms", [left]) if g.area > 1e-3]   # >1e-3: ignores arc-discretisation slivers
    res[ver] = dict(area_mm2=round(part.area, 2), L=d["L"], H=d["H"], tool_d=P["tool_d"], unreachable_area_mm2=round(left.area, 4), unreachable_spots=unreach,
                    interference_mm=round(d["rib_top"] - d["P"], 3), notch_span_mm=round(d["notch_x1"] - d["notch_x0"], 2), lead_deg=p["lead_deg"],
                    channel_h=round(d["P"] - p["floor_t"], 2), pocket_h=round(d["arm_under"] - d["stop_top"], 2), stop_gap=p["stop_gap"])
    print(ver, res[ver])
    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=150)
    x, y = part.exterior.xy; ax.fill(x, y, fc="#cfd5de", ec="k", lw=0.8)
    for g in getattr(left, "geoms", [left]):
        if g.area > 1e-4: gx, gy = g.exterior.xy; ax.fill(gx, gy, fc="red", ec="none", alpha=0.8)
    # card plane and a 24-card stack
    ax.add_patch(plt.Rectangle((d["x_s"], d["P"] + 0.0), 40, 24 * 0.127, fc="#f0d9a0", ec="#b08a40", lw=0.5, alpha=0.8))
    ax.axhline(d["P"], color="#c44", lw=0.5, ls="--")
    ax.annotate("pad plane P", (2, d["P"] + 0.3), fontsize=7, color="#c44")
    ax.annotate(f"rib +{d['rib_top']-d['P']:.2f}", (d["x_r"], d["rib_top"] + 0.2), (d["x_r"] - 10, d["rib_top"] - 3.2), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
    ax.annotate("stop", (d["x_s"], d["stop_top"] - 1), (d["x_s"] - 8, d["stop_top"] + 1.5), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
    ax.annotate(f"{p['lead_deg']:.0f}° lead-in", (d["land_out_x1"] + 3, d["P"] + 1.8), (d["land_out_x1"] + 4, d["P"] - 2.5), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
    ax.annotate("flex arm", (30, d["H"] + 0.3), fontsize=7, ha="center")
    ax.set_aspect("equal"); ax.set_xlim(-2, d["L"] + 2); ax.set_ylim(-3, d["H"] + 3); ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"SAFT-V2-TAB {ver} — profile (red = void a Ø{P['tool_d']} tool cannot reach: {left.area:.3f} mm²), 24-card stack shown", fontsize=8)
    fig.savefig(os.path.join(M, f"profile_{ver}.png"), bbox_inches="tight"); plt.close(fig)
json.dump(res, open(os.path.join(HERE, "profile_check.json"), "w"), indent=1)
