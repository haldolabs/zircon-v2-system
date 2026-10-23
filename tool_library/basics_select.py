#!/usr/bin/python3
"""Build the pared-down FreeCAD 1.0 CAM tool library for the V3 run: ~70 standard tools picked from the offline
148k-tool vendor collection (../tool_library).  Owner spec (2026-10-23): "just the standards" — square end mills,
ball end mills, chamfer mills, single-profile thread mills that can do ~32 tpi, varied reach, imperial taps 1/2-20
or less down to 1-72, same for metric.  Added 2026-10-23 (owner): drills — the tap drill for every tap and the normal-fit
clearance drill for every screw size (ASME B18.2.8 / ISO 273 medium), max 120 tools.

Writes  freecad/<name>/{Bit,Library,Shape}  next to this script (open in FreeCAD's Tool Bit Library manager, or point CAM's
tool-library path at it) plus  README.md / tools.csv  inside it listing every tool.  Stdlib only; reads the collection as
collection.json or collection.csv[.xz].
Run:    python3 basics_select.py [--name basics] [--lib <tool_library dir>]
Verify: QT_QPA_PLATFORM=offscreen LIBDIR=freecad/<name> freecadcmd basics_verify.py
"""
import json, os, glob, csv, shutil, re, sys, lzma, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--lib", help="the tool_library dir (collection.json|csv[.xz] + freecad/V3_chamfer_tap_threadmill); default: ../tool_library next to this script, else the script's own dir (zircon-v2-system layout)")
ap.add_argument("--name", default="V3_standard", help="library name → <lib or script dir>/freecad/<name>/ (default V3_standard)")
ap.add_argument("--out", help="override the output library dir")
args = ap.parse_args()
cands = [args.lib] if args.lib else [os.path.join(HERE, "..", "tool_library"), HERE]
LIB = next((os.path.realpath(c) for c in cands if c and glob.glob(os.path.join(c, "collection.*"))), None)
if not LIB: raise SystemExit("tool library not found (collection.json / collection.csv[.xz]); pass --lib")
OUT = args.out or os.path.join(HERE if HERE != LIB else LIB, "freecad", args.name)
IN = 25.4
NUM = ("DC", "DMM", "APMX", "OAL", "LB", "NOF", "RE", "ND", "LN", "TA", "n_presets", "DC_mm", "DMM_mm", "APMX_mm", "OAL_mm", "RE_mm")
def load_collection():
    j = os.path.join(LIB, "collection.json")
    if os.path.exists(j): return json.load(open(j))
    src = os.path.join(LIB, "collection.csv"); f = open(src, newline="", encoding="utf-8") if os.path.exists(src) else lzma.open(src + ".xz", "rt", newline="", encoding="utf-8")
    out = []
    for r in csv.DictReader(f):
        for k in NUM:
            v = r.get(k); r[k] = (float(v) if v not in (None, "") else None)
        r["has_3d"] = r.get("has_3d") in ("True", "true", "1"); out.append(r)
    return out
rows = load_collection()
bits_dir = os.path.join(LIB, "freecad", "V3_chamfer_tap_threadmill", "Bit")
near = lambda a, b, t: a is not None and b is not None and abs(a - b) <= t
q = lambda v: f"{v:.4f} mm"

# ---------------------------------------------------------------- end mills (from the collection) ----
VENDOR_PREF = ["HARVEY TOOL", "HELICAL SOLUTIONS", "RobbJack", "KYOCERA SGS Precision Tools", "Garr Tool", "SwiftCARB", "IMCO Carbide Tool", "Mitsubishi Materials", "ISCAR", "Sandvik Coromant"]
TIER = {"std": (2.0, 1.0, 3.1), "long": (4.0, 3.1, 5.2), "xlong": (7.0, 5.2, 9.5)}      # target, lo, hi of reach/D
exotic = lambda r: any(w in ((r["tool_id"] or "") + " " + (r["description"] or "")).upper() for w in ("PCD", "DIAMOND END", "CBN", "DIE MOLD", "TAPERED", "LOLLIPOP"))   # plain carbide only
def pick_endmill(typ, unit, D, tier, flutes):
    tgt, lo, hi = TIER[tier]; tolD = 0.001 if unit == "in" else 0.01
    maxshank = 0.5 if unit == "in" else 12.0      # small tools carry a bigger shank (1/16 in on a 1/8 in shank); anything up to a 1/2 in / 12 mm collet is fine
    c = [r for r in rows if r["type"] == typ and r["unit"] == unit and near(r["DC"], D, tolD) and r["DMM"] and D - tolD <= r["DMM"] <= maxshank
         and r["APMX"] and r["OAL"] and r["NOF"] in flutes and lo <= ((r["LB"] or r["APMX"]) / D) <= hi
         and not exotic(r) and (tier != "std" or r["OAL_mm"] <= (82 if D * (IN if unit == "in" else 1) < 12 else 105))]   # std = a normal-length tool, not a 4 in OAL special
    if not c: raise SystemExit(f"no candidate: {typ} {D}{unit} {tier}")
    vrank = lambda r: VENDOR_PREF.index(r["vendor"]) if r["vendor"] in VENDOR_PREF else 99
    c.sort(key=lambda r: (abs((r["LB"] or r["APMX"]) / D - tgt), not near(r["DMM"], D, tolD), vrank(r), flutes.index(r["NOF"]), -(r["n_presets"] or 0)))
    return c[0]
def bit_endmill(r, role):
    shape = "endmill.fcstd" if r["type"] == "flat end mill" else "ballend.fcstd"
    prm = {"Diameter": q(r["DC_mm"]), "Length": q(r["OAL_mm"]), "CuttingEdgeHeight": q(r["APMX_mm"]), "ShankDiameter": q(r["DMM_mm"] or r["DC_mm"])}
    reach = round(float(r["LB"] or r["APMX"]) * (IN if r["unit"] == "in" else 1), 3)
    att = {"Flutes": int(r["NOF"]), "Material": "Carbide" if (r["BMC"] or "carbide") == "carbide" else "HSS", "v3_role": role, "reach_mm": reach,
           "fusion_type": r["type"], "iso13399": {k: r[k] for k in ("DC", "DMM", "APMX", "OAL", "LB", "NOF", "RE", "unit")},
           "vendor": r["vendor"], "tool_id": r["tool_id"], "description": r["description"], "library": r["library"], "product_link": r["product_link"], "source_file": r["source_file"]}
    return {"version": 2, "name": f"{r['vendor']} {r['tool_id']}", "shape": shape, "parameter": prm, "attribute": att}

F, B = "flat end mill", "ball end mill"
ENDMILLS = [  # (type, unit, D, tier, flute preference, role)
    (F, "in", 1/16, "std", (2, 3), "1/16 in square, stub"), (F, "in", 1/16, "long", (2, 3), "1/16 in square, 4D reach"),
    (F, "in", 3/32, "std", (2, 3), "3/32 in square"),
    (F, "in", 1/8, "std", (3, 2), "1/8 in square"), (F, "in", 1/8, "long", (3, 2), "1/8 in square, 4D reach"), (F, "in", 1/8, "xlong", (2, 3), "1/8 in square, 7D reach"),
    (F, "in", 3/16, "std", (3, 2), "3/16 in square"), (F, "in", 3/16, "long", (3, 2), "3/16 in square, 4D reach"),
    (F, "in", 1/4, "std", (3, 2), "1/4 in square"), (F, "in", 1/4, "long", (3, 2), "1/4 in square, 4D reach"), (F, "in", 1/4, "xlong", (3, 2), "1/4 in square, 7D reach"),
    (F, "in", 5/16, "std", (3, 2), "5/16 in square"),
    (F, "in", 3/8, "std", (3, 2), "3/8 in square"), (F, "in", 3/8, "long", (3, 2), "3/8 in square, 4D reach"),
    (F, "in", 1/2, "std", (3, 2), "1/2 in square"), (F, "in", 1/2, "long", (3, 2), "1/2 in square, 4D reach"),
    (B, "in", 1/16, "std", (2,), "1/16 in ball"), (B, "in", 1/8, "std", (2,), "1/8 in ball"), (B, "in", 1/8, "long", (2,), "1/8 in ball, 4D reach"),
    (B, "in", 3/16, "std", (2,), "3/16 in ball"), (B, "in", 1/4, "std", (2,), "1/4 in ball"), (B, "in", 1/4, "long", (2,), "1/4 in ball, 4D reach"),
    (B, "in", 3/8, "std", (2,), "3/8 in ball"), (B, "in", 1/2, "std", (2,), "1/2 in ball"),
    (F, "mm", 2, "std", (2, 3), "2 mm square"), (F, "mm", 3, "std", (3, 2), "3 mm square"), (F, "mm", 3, "long", (3, 2), "3 mm square, 4D reach"),
    (F, "mm", 4, "std", (3, 2), "4 mm square"), (F, "mm", 6, "std", (3, 2), "6 mm square"), (F, "mm", 6, "long", (3, 2), "6 mm square, 4D reach"),
    (F, "mm", 8, "std", (3, 2), "8 mm square"), (F, "mm", 10, "std", (3, 2), "10 mm square"), (F, "mm", 12, "std", (3, 2), "12 mm square"),
    (B, "mm", 2, "std", (2,), "2 mm ball"), (B, "mm", 3, "std", (2,), "3 mm ball"), (B, "mm", 6, "std", (2,), "6 mm ball"),
]

# ---------------------------------------------------------------- chamfer / thread mills / taps (from the exported bits) ----
def load_bits():
    out = []
    for p in glob.glob(os.path.join(bits_dir, "*.fctb")):
        b = json.load(open(p)); b["_file"] = os.path.basename(p); out.append(b)
    return out
BITS = load_bits()
def pick_chamfer(D_in, angle, role):
    c = [b for b in BITS if b["attribute"]["fusion_type"] == "chamfer mill" and b["attribute"]["iso13399"]["unit"] == "in"
         and near(b["attribute"]["iso13399"]["DC"], D_in, 0.001) and b["parameter"]["CuttingEdgeAngle"].startswith(f"{angle:.4f}")]
    c.sort(key=lambda b: (b["attribute"]["vendor"] != "HARVEY TOOL", -(b["attribute"]["iso13399"]["APMX"] or 0), b["name"]))
    if not c: raise SystemExit(f"no chamfer {D_in} {angle}")
    b = json.loads(json.dumps(c[0])); prm = b["parameter"]
    # FIX (found at seed time): the V2 exporter put the vendor flute length (APMX) into CuttingEdgeHeight. In FreeCAD's
    # chamfer.fcstd that is the height of the CONE, so a 1/4 in 90° tool came out 44 mm wide. Cone height follows from
    # the angle: (D - tip) / (2 tan(angle/2)). The vendor flute length is kept in attribute.iso13399.APMX.
    import math
    dc = float(prm["Diameter"].split()[0]); tip = float(prm["TipDiameter"].split()[0]); ang = float(prm["CuttingEdgeAngle"].split()[0])
    prm["CuttingEdgeHeight"] = q((dc - tip) / (2 * math.tan(math.radians(ang / 2))))
    b["attribute"]["v3_fix"] = "CuttingEdgeHeight = cone height from D, tip and angle; V2 export used the flute length, which flares the cone to several times D"
    return b, role
CHAMFERS = [(0.25, 90.0, "1/4 in 90° chamfer"), (0.375, 90.0, "3/8 in 90° chamfer"), (0.5, 90.0, "1/2 in 90° chamfer")]
# Sandvik CoroMill Plura single-profile thread mills ("…P" suffix = one profile per flute): code = ØØØ + pitch (metric, ×100 mm) or ØØØ + tpi (inch, ×10)
THREADMILLS = [("R217.33-016560AC06P", "single-profile thread mill, inch, 56 tpi max, Ø1.6 (#2-56)"),
               ("R217.33-021400AC08P", "single-profile thread mill, inch, 40 tpi max, Ø2.1 (#4-40)"),
               ("R217.33-032320AC12P", "single-profile thread mill, inch, 32 tpi max, Ø3.25 (#6/#8/#10-32)"),
               ("R217.33-035240AC14P", "single-profile thread mill, inch, 24 tpi max, Ø3.55 (#10-24, 5/16-24)"),
               ("R217.33-048200AC19P", "single-profile thread mill, inch, 20 tpi max, Ø4.85 (1/4-20 … 1/2-20)"),
               ("R217.13-012035AC05P", "single-profile thread mill, metric, 0.35 pitch max, Ø1.2 (M1.6)"),
               ("R217.13-023050AC06P", "single-profile thread mill, metric, 0.50 pitch max, Ø2.3 (M2.5/M3)"),
               ("R217.13-040080AC15P", "single-profile thread mill, metric, 0.80 pitch max, Ø4.0 (M4/M5)"),
               ("R217.13-048100AC12P", "single-profile thread mill, metric, 1.00 pitch max, Ø4.8 (M6)")]
def pick_threadmill(tid, role):
    c = [b for b in BITS if b["attribute"]["fusion_type"] == "thread mill" and b["name"].startswith(f"Sandvik Coromant {tid}")]
    c.sort(key=lambda b: b["name"])
    if not c: raise SystemExit(f"no thread mill {tid}")
    b = json.loads(json.dumps(c[0])); prm = b["parameter"]
    # FIX (found at seed time): the V2 exporter set NeckDiameter = shank for thread mills. FreeCAD's thread-mill.fcstd
    # sketch cannot solve a neck wider than the cutting diameter and SILENTLY keeps the stock shape (Ø5 × 50 mm, 738 mm³)
    # — the bit "loads", but with the wrong geometry. Neck must be < Diameter; shank may stay wider.
    dc = float(prm["Diameter"].split()[0]); shank = float(prm["ShankDiameter"].split()[0])
    prm["NeckDiameter"] = q(min(shank, 0.8 * dc)); b["attribute"]["v3_fix"] = "NeckDiameter set to min(shank, 0.8*D); V2 export had neck = shank, which FreeCAD rejects silently"
    return b, role
TAPS_IN = [("2-56", 0.086, 56), ("4-40", 0.112, 40), ("6-32", 0.138, 32), ("8-32", 0.164, 32), ("10-24", 0.19, 24), ("10-32", 0.19, 32), ("1/4-20", 0.25, 20), ("1/4-28", 0.25, 28),
           ("5/16-18", 0.3125, 18), ("5/16-24", 0.3125, 24), ("3/8-16", 0.375, 16), ("3/8-24", 0.375, 24), ("1/2-13", 0.5, 13), ("1/2-20", 0.5, 20)]
TAPS_MM = [("M1.6x0.35", 1.6, 0.35), ("M2x0.4", 2, 0.4), ("M2.5x0.45", 2.5, 0.45), ("M3x0.5", 3, 0.5), ("M4x0.7", 4, 0.7), ("M5x0.8", 5, 0.8), ("M6x1", 6, 1.0), ("M8x1.25", 8, 1.25), ("M10x1.5", 10, 1.5), ("M12x1.75", 12, 1.75)]
def series_rank(b):   # blind holes dominate the cavity → spiral-flute (Sandvik CoroTap 300) first, then spiral-point (200), then Haas, then the rest
    n = b["name"]
    return 0 if "T300" in n else 1 if "T200" in n else 2 if n.startswith("Haas") else 3
def pick_tap(label, dia_mm, pitch_mm):
    c = [b for b in BITS if b["attribute"]["fusion_type"] == "tap right hand"
         and near(b["attribute"]["iso13399"]["DC"] * (IN if b["attribute"]["iso13399"]["unit"] == "in" else 1), dia_mm, 0.05)
         and near(b["attribute"].get("tap_pitch_mm"), pitch_mm, 0.02)]
    c.sort(key=lambda b: (series_rank(b), b["name"]))
    if not c: raise SystemExit(f"no tap {label}")
    return c[0], f"tap {label}"
def generic_tap_1_72():
    # No 1-72 tap exists in any vendor library on this host. Generic bit from ANSI B94.9 nominal machine-screw tap dimensions
    # (#1: major Ø0.073 in, 72 tpi, OAL 1-11/16 in, thread length 3/8 in, shank Ø0.141 in) — ESTIMATED, flagged in the attribute.
    d, oal, loc, shank, p = 0.073 * IN, 1.6875 * IN, 0.375 * IN, 0.141 * IN, IN / 72
    return {"version": 2, "name": "GENERIC tap 1-72 UNF (ANSI B94.9 nominal)", "shape": "thread-mill.fcstd",
            "parameter": {"Diameter": q(d), "Length": q(oal), "ShankDiameter": q(shank), "NeckDiameter": q(d * 0.8), "NeckLength": q(oal - loc - 1.0), "Crest": q(max(p * 0.3, 0.05)), "cuttingAngle": "60.0000 °"},
            "attribute": {"Flutes": 2, "Material": "HSS", "tap_pitch_mm": round(p, 4), "v3_role": "tap 1-72", "estimated": True,
                          "note": "No 1-72 tap in the vendor collection; dimensions are ANSI B94.9 nominal (estimated). TAP represented with FreeCAD's thread-mill shape; FreeCAD 1.0 has no tap shape.",
                          "fusion_type": "tap right hand", "iso13399": {"DC": 0.073, "DMM": 0.141, "APMX": 0.375, "OAL": 1.6875, "NOF": 2, "unit": "in"}, "vendor": "GENERIC", "tool_id": "1-72"}}, "tap 1-72"

# ---------------------------------------------------------------- drills (from the collection) ----
# Tap drills: standard ~75 % thread chart (number/letter/fraction sizes, decimal inch). Clearance: ASME B18.2.8 normal fit (inch),
# ISO 273 medium (metric). A diameter that serves two roles (e.g. #25 = 10-24 tap drill = #6 clearance) is one tool with both roles.
TAPDRILL_IN = [("1-72", 0.0595, "#53"), ("2-56", 0.070, "#50"), ("4-40", 0.089, "#43"), ("6-32", 0.1065, "#36"), ("8-32", 0.136, "#29"), ("10-24", 0.1495, "#25"),
               ("10-32", 0.159, "#21"), ("1/4-20", 0.201, "#7"), ("1/4-28", 0.213, "#3"), ("5/16-18", 0.257, "F"), ("5/16-24", 0.272, "I"), ("3/8-16", 0.3125, "5/16"),
               ("3/8-24", 0.332, "Q"), ("1/2-13", 0.4219, "27/64"), ("1/2-20", 0.4531, "29/64")]
TAPDRILL_MM = [("M1.6", 1.25), ("M2", 1.6), ("M2.5", 2.05), ("M3", 2.5), ("M4", 3.3), ("M5", 4.2), ("M6", 5.0), ("M8", 6.8), ("M10", 8.5), ("M12", 10.2)]
CLEAR_IN = [("#1", 0.081, "#46"), ("#2", 0.096, "#41"), ("#4", 0.1285, "#30"), ("#6", 0.1495, "#25"), ("#8", 0.177, "#16"), ("#10", 0.201, "#7"),
            ("1/4", 0.2813, "9/32"), ("5/16", 0.3438, "11/32"), ("3/8", 0.4063, "13/32"), ("1/2", 0.5313, "17/32")]
CLEAR_MM = [("M1.6", 1.8), ("M2", 2.4), ("M2.5", 2.9), ("M3", 3.4), ("M4", 4.5), ("M5", 5.5), ("M6", 6.6), ("M8", 9.0), ("M10", 11.0), ("M12", 13.5)]
# The 2011 cavity drawing's own drills (notes K, P, M, L): not screw sizes. The two deep ones need ≥ 2.0 in (51 mm) of flute.
DRAWING_IN = [("drawing Ø0.063 note K, 1.43 in deep", 0.063, 0), ("drawing Ø0.070 note P, through arm", 0.070, 0), ("drawing Ø0.185 note M, 8-32 loose, 2.0 in deep", 0.185, 51.0), ("drawing Ø0.190 note L, 2.0 in deep", 0.190, 51.0)]
DRILL_VENDOR_PREF = ["Guhring", "HARVEY TOOL", "Haas Automation", "Garr Tool", "KYOCERA SGS Precision Tools", "SwiftCARB", "Sandvik Coromant", "ISCAR", "Mitsubishi Materials"]
drill_exotic = lambda r: any(w in ((r["tool_id"] or "") + " " + (r["description"] or "")).upper() for w in ("INDEXABLE", "INSERT", "PCD", "GUN DRILL", "STEP", "MICRO", "LEFT HAND", "LH "))
def pick_drill(d_mm, role, min_flute=0.0, tol=0.02):
    c = [r for r in rows if r["type"] == "drill" and r["DC_mm"] and abs(r["DC_mm"] - d_mm) <= tol and r["OAL_mm"] and r["APMX_mm"]
         and max(4 * d_mm, min_flute) <= r["APMX_mm"] <= max(14 * d_mm, min_flute * 1.6) and not drill_exotic(r) and (r["DMM_mm"] or d_mm) <= max(12.8, d_mm + 0.05)]      # jobber-class flute length; shank fits a 1/2 in collet (or is the drill's own size above that)
    if not c: raise SystemExit(f"no drill {d_mm} mm ({role})")
    vrank = lambda r: DRILL_VENDOR_PREF.index(r["vendor"]) if r["vendor"] in DRILL_VENDOR_PREF else 99
    c.sort(key=lambda r: (round(abs(r["DC_mm"] - d_mm), 3), abs(r["APMX_mm"] / d_mm - 7), vrank(r), -(r["n_presets"] or 0)))   # exact size first, then ~7D flute length = a normal jobber drill
    return c[0]
def bit_drill(r, role):
    ta = r["TA"] if r["TA"] and r["TA"] > 0 else 118.0
    att = {"Flutes": int(r["NOF"]) if r["NOF"] else 2, "Material": "Carbide" if (r["BMC"] or "carbide") == "carbide" else "HSS", "v3_role": role,
           "fusion_type": r["type"], "iso13399": {k: r[k] for k in ("DC", "DMM", "APMX", "OAL", "LB", "NOF", "TA", "unit")},
           "vendor": r["vendor"], "tool_id": r["tool_id"], "description": r["description"], "library": r["library"], "product_link": r["product_link"], "source_file": r["source_file"]}
    return {"version": 2, "name": f"{r['vendor']} {r['tool_id']}", "shape": "drill.fcstd", "parameter": {"Diameter": q(r["DC_mm"]), "Length": q(r["OAL_mm"]), "TipAngle": f"{ta:.4f} °"}, "attribute": att}
drill_roles = []   # (d_mm, role, min_flute_mm); sizes within 0.03 mm of each other (#46 vs 2.05 mm, #16 vs 4.5 mm, 17/32 vs 13.5 mm) are one tool with both roles
def add_role(d, role, min_flute=0.0):
    for i, (d0, r0, f0) in enumerate(drill_roles):
        if abs(d0 - d) <= 0.03: drill_roles[i] = (d0, r0 + " = " + role, max(f0, min_flute)); return
    drill_roles.append((round(d, 3), role, min_flute))
for label, d, name in TAPDRILL_IN: add_role(d * IN, f"tap drill {label} ({name}, {d} in)")
for label, d in TAPDRILL_MM: add_role(d, f"tap drill {label} ({d} mm)")
for label, d, name in CLEAR_IN: add_role(d * IN, f"clearance {label} screw, normal fit ({name}, {d} in)")
for label, d in CLEAR_MM: add_role(d, f"clearance {label} screw, medium fit ({d} mm)")
for label, d, mf in DRAWING_IN: add_role(d * IN, label, mf)
DRILLS = [(pick_drill(d, role, mf), role) for d, role, mf in sorted(drill_roles)]

# ---------------------------------------------------------------- assemble ----
selected = []   # (bit json, role, source)
for typ, unit, D, tier, fl, role in ENDMILLS:
    r = pick_endmill(typ, unit, D, tier, fl); selected.append((bit_endmill(r, role), role, "collection.json"))
for D, a, role in CHAMFERS:
    b, role = pick_chamfer(D, a, role); selected.append((b, role, b["_file"]))
for tid, role in THREADMILLS:
    b, role = pick_threadmill(tid, role); selected.append((b, role, b["_file"]))
selected.append((*generic_tap_1_72(), "synthesized"))
for label, dia, tpi in TAPS_IN:
    b, role = pick_tap(label + " UN", dia * IN, IN / tpi); selected.append((b, role, b["_file"]))
for label, dia, p in TAPS_MM:
    b, role = pick_tap(label, dia, p); selected.append((b, role, b["_file"]))
for r, role in DRILLS: selected.append((bit_drill(r, role), role, "collection.json"))
assert len(selected) <= 120, len(selected)

for sub in ("Bit", "Library", "Shape"):          # regenerate the library; keep README/tools.csv/sheet.png (the sheet is rendered separately)
    if os.path.isdir(os.path.join(OUT, sub)): shutil.rmtree(os.path.join(OUT, sub))
os.makedirs(os.path.join(OUT, "Bit")); os.makedirs(os.path.join(OUT, "Library"))
# stock FreeCAD shapes, so the library is self-contained: from the sibling library if it ships them, else from FreeCAD's own Tools/Shape
shape_src = next((d for d in (os.path.join(LIB, "freecad", "V3_starter_quarter_eighth", "Shape"), "/usr/share/freecad/Mod/CAM/Tools/Shape", "/usr/lib/freecad/Mod/CAM/Tools/Shape",
                              os.path.expanduser("~/.local/share/FreeCAD/Tools/Shape")) if os.path.isdir(d)), None)
if not shape_src: raise SystemExit("no FreeCAD Tools/Shape directory found to copy the stock shapes from")
shutil.copytree(shape_src, os.path.join(OUT, "Shape"))
tools, table = [], []
for nr, (b, role, src) in enumerate(selected, 1):
    b = {k: v for k, v in b.items() if not k.startswith("_")}
    b["attribute"]["v3_role"] = role; b["attribute"]["v3_tool_nr"] = nr
    fn = f"T{nr:02d}_" + re.sub(r"[^A-Za-z0-9._-]+", "_", b["name"])[:70] + ".fctb"
    json.dump(b, open(os.path.join(OUT, "Bit", fn), "w"), indent=1, ensure_ascii=False)
    tools.append({"nr": nr, "path": fn}); a = b["attribute"]; i = a["iso13399"]; k = IN if i.get("unit") == "in" else 1.0
    table.append({"nr": nr, "role": role, "shape": b["shape"].replace(".fcstd", ""), "vendor": a.get("vendor"), "tool_id": a.get("tool_id") or b["name"].replace(a.get("vendor", ""), "").strip(),
                  "D_mm": round(float(b["parameter"]["Diameter"].split()[0]), 3), "LOC_mm": round((i.get("APMX") or 0) * k, 2), "reach_mm": a.get("reach_mm", ""), "OAL_mm": round(float(b["parameter"]["Length"].split()[0]), 1),
                  "flutes": a.get("Flutes"), "pitch_mm": a.get("tap_pitch_mm", ""), "material": a.get("Material"), "file": fn, "estimated": a.get("estimated", "")})
json.dump({"version": 1, "tools": tools}, open(os.path.join(OUT, "Library", "V3_standard.fctl"), "w"), indent=1)
with open(os.path.join(OUT, "tools.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
md = [f"# {args.name} — the pared-down, FreeCAD-ready CAM tool library", "",
      f"**{len(table)} tools**, chosen from the offline vendor collection (148,412 tools) by `{os.path.basename(sys.argv[0])}` to the owner's",
      "spec: standards only — square and ball end mills in the common imperial and metric sizes with stub / 4D / 7D reach variants, 90° chamfer mills,",
      "Sandvik single-profile thread mills that cover 56–20 tpi and 0.35–1.0 mm pitch (so every tap below has a thread-mill alternative), and",
      "spiral-flute taps 2-56 … 1/2-20 and M1.6 … M12. The 1-72 tap is **generic** (no vendor has one): ANSI nominal dimensions, flagged `estimated`.",
      "Drills (added 2026-10-23): the tap drill for every tap above and the normal-fit clearance drill for every screw size, deduplicated where one",
      "diameter serves both (#25 = 10-24 tap drill = #6 clearance; #7 = 1/4-20 tap drill = #10 clearance), plus the four drills the 2011 cavity",
      "drawing calls for by size (Ø0.063, 0.070, 0.185 and 0.190 in; the last two with ≥ 51 mm of flute for the 2.0 in deep holes). Max 120 tools.", "",
      f"Library folder: `{os.path.relpath(OUT, HERE)}/` (`Bit/*.fctb`, `Library/{args.name}.fctl`, `Shape/*.fcstd` — self-contained; point FreeCAD CAM's",
      "tool-library path at it or open it in the Tool Bit Library manager). Taps and thread mills use FreeCAD's `thread-mill.fcstd` shape (FreeCAD 1.0 has",
      "no tap shape); the tap pitch is in `attribute.tap_pitch_mm`. Reach = vendor length-below-shank (`LB`) where given, else flute length.", "",
      "| T | role | shape | vendor | tool id | Ø mm | LOC mm | reach mm | OAL mm | flutes | pitch mm | est. |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
md += [f"| {t['nr']} | {t['role']} | {t['shape']} | {t['vendor']} | {t['tool_id']} | {t['D_mm']} | {t['LOC_mm']} | {t['reach_mm']} | {t['OAL_mm']} | {t['flutes']} | {t['pitch_mm']} | {'yes' if t['estimated'] else ''} |" for t in table]
open(os.path.join(OUT, "README.md"), "w").write("\n".join(md) + "\n")
print(f"wrote {len(table)} bits to {OUT}")
for t in table: print(f"T{t['nr']:02d} {t['role']:55s} {t['vendor']:28s} {t['tool_id']:28s} D={t['D_mm']:<7} LOC={t['LOC_mm']:<6} reach={t['reach_mm']!s:<7} OAL={t['OAL_mm']:<6} fl={t['flutes']}")
