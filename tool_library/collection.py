"""Merge every raw vendor library in this directory into ONE normalized collection (ISO 13399 field names, mm + source unit).
Sources it understands:
  robbjack/robbjack-master-catalog.json       RobbJack ISO 13399 master catalog (schema 1.1)
  robbjack/*.tools, pocketnc/*.tools          Fusion .tools = zip holding tools.json
  autodesk/fusion/*.json                      Fusion tools.json downloaded from cam.autodesk.com/tools/download.php?name=<path>
Outputs (next to this script): collection.csv, collection.json, summary.md, saft_v2_candidates.md
Usage: /usr/bin/python3 collection.py   (stdlib only)
"""
import json, os, csv, glob, zipfile, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw") if os.path.isdir(os.path.join(HERE, "raw")) else HERE   # repo layout keeps vendor files under raw/
IN2MM = 25.4
FIELDS = ["vendor", "library", "tool_id", "type", "description", "unit", "DC", "DMM", "APMX", "OAL", "LB", "NOF", "RE", "ND", "LN", "TA", "BMC", "coating",
          "n_presets", "has_3d", "product_link", "guid", "source_file", "DC_mm", "DMM_mm", "APMX_mm", "OAL_mm", "RE_mm"]
rows = []
# Fusion tool type → FreeCAD 1.0 CAM shape (verified by loading in freecadcmd). Defined up here because load_fusion() uses it.
SHAPES = {"flat end mill": "endmill.fcstd", "ball end mill": "ballend.fcstd", "bull nose end mill": "bullnose.fcstd", "drill": "drill.fcstd",
          "spot drill": "drill.fcstd", "center drill": "drill.fcstd", "counter sink": "drill.fcstd",
          "chamfer mill": "chamfer.fcstd", "tap right hand": "thread-mill.fcstd", "tap left hand": "thread-mill.fcstd", "thread mill": "thread-mill.fcstd",
          "dovetail mill": "dovetail.fcstd"}
EXTRA = {}      # guid -> extra Fusion geometry (TA, TP, tip-diameter, shoulder-diameter) the FreeCAD shapes need
HOLDERS = []    # raw holder records (segments) — FreeCAD has no holder bit type, see holders.json / holders_export.py
def mm(v, unit):
    if v in (None, ""): return None
    try: v = float(v)
    except (TypeError, ValueError): return None
    return round(v * IN2MM, 4) if unit == "in" else round(v, 4)
def add(r):
    u = r.get("unit")
    for k in ("DC", "DMM", "APMX", "OAL", "RE"): r[k + "_mm"] = mm(r.get(k), u)
    rows.append({k: r.get(k) for k in FIELDS})
# ---- RobbJack ISO 13399 master catalog ----
def load_robbjack():
    cat = json.load(open(os.path.join(RAW, "robbjack", "robbjack-master-catalog.json")))
    for t in cat["tools"]:
        s = t.get("specs", {}); g = lambda k: (s.get(k) or {}).get("in") if isinstance(s.get(k), dict) else s.get(k)
        types = t.get("toolTypes") or []
        re_ = g("RE"); dc = g("DC")
        typ = "slitting saw" if any("Saw" in x for x in types) else ("ball end mill" if re_ and dc and abs(re_ - dc / 2) < 1e-4 else ("bull nose end mill" if re_ else "flat end mill")) if any("End Mill" in x or "Router" in x for x in types) else "/".join(types)
        add(dict(vendor="RobbJack", library="robbjack-master-catalog (ISO 13399)", tool_id=t["toolNbr"], type=typ, description=t.get("name"), unit="in",
                 DC=dc, DMM=g("DMM"), APMX=g("APMX"), OAL=g("OAL"), LB=None, NOF=g("NOF"), RE=re_, ND=g("ND"), LN=g("LN"), TA=None, BMC="carbide",
                 coating="|".join(t.get("coatings") or []), n_presets=None, has_3d=bool(t.get("step")), product_link=t.get("url"), guid=None, source_file="robbjack/robbjack-master-catalog.json"))
    return cat["toolCount"]
# ---- Fusion tools.json (zipped .tools or raw .json) ----
def fusion_records(path):
    if path.endswith(".tools"):
        with zipfile.ZipFile(path) as z: d = json.load(z.open("tools.json"))
    else: d = json.load(open(path, encoding="utf-8-sig"))
    return d.get("data", d) if isinstance(d, dict) else d
def load_fusion(path, library, default_vendor):
    n = 0
    for t in fusion_records(path):
        g = t.get("geometry", {}); unit = "in" if str(t.get("unit", "")).startswith("inch") else "mm"
        sv = t.get("start-values", {}) or {}; presets = sv.get("presets", []) if isinstance(sv, dict) else []
        if t.get("guid") and t.get("type") in SHAPES and t.get("type") not in ("flat end mill", "ball end mill", "bull nose end mill"):
            EXTRA[t["guid"]] = {k: g.get(k) for k in ("TA", "TP", "tip-diameter", "shoulder-diameter", "SIG")}
        if t.get("type") == "holder":
            HOLDERS.append(dict(vendor=(t.get("vendor") or default_vendor).strip(), library=library, product_id=t.get("product-id"), description=t.get("description"), unit=unit,
                                gauge_length=t.get("gaugeLength"), segments=t.get("segments"), product_link=t.get("product-link"), guid=t.get("guid")))
        add(dict(vendor=(t.get("vendor") or default_vendor).strip(), library=library, tool_id=t.get("product-id") or "", type=t.get("type"), description=t.get("description"), unit=unit,
                 DC=g.get("DC"), DMM=g.get("SFDM"), APMX=g.get("LCF"), OAL=g.get("OAL"), LB=g.get("LB"), NOF=g.get("NOF"), RE=g.get("RE"), ND=g.get("shoulder-length"), LN=None, TA=g.get("TA"),
                 BMC=t.get("BMC"), coating=None, n_presets=len(presets), has_3d=bool(t.get("3dmodel") or t.get("3d-model")), product_link=t.get("product-link"), guid=t.get("guid"), source_file=os.path.relpath(path, HERE)))
        n += 1
    return n
log = []
log.append(("RobbJack ISO 13399 master catalog", load_robbjack()))
for p in sorted(glob.glob(os.path.join(RAW, "robbjack", "*.tools"))): log.append((os.path.basename(p), load_fusion(p, "robbjack-fusion360.tools", "RobbJack")))
for p in sorted(glob.glob(os.path.join(RAW, "pocketnc", "*.tools"))): log.append((os.path.basename(p), load_fusion(p, "pocketnc/" + os.path.basename(p), "Pocket NC")))
for p in sorted(glob.glob(os.path.join(RAW, "autodesk", "fusion", "*.json"))):
    lib = os.path.basename(p)[:-5]; log.append((lib, load_fusion(p, "autodesk/" + lib, lib.split("_")[0]))); print("loaded", lib, log[-1][1], file=sys.stderr)
# ---- outputs ----
with open(os.path.join(HERE, "collection.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
json.dump(rows, open(os.path.join(HERE, "collection.json"), "w"), separators=(",", ":"))
by_vendor = Counter(r["vendor"] for r in rows); by_type = Counter(r["type"] for r in rows); by_lib = Counter(r["library"] for r in rows)
with_presets = sum(1 for r in rows if r["n_presets"]); with_3d = sum(1 for r in rows if r["has_3d"])
md = [f"# V2 Tool Library — merged collection summary", "", f"**{len(rows):,} tools** from {len(by_lib)} libraries / {len(by_vendor)} vendors; {with_presets:,} carry cutting presets; {with_3d:,} flag a 3D model. Built by `collection.py` on 2026-10-22.", "",
      "| Library (source file) | tools |", "|---|---|"] + [f"| {k} | {v:,} |" for k, v in sorted(by_lib.items(), key=lambda kv: -kv[1])] + ["", "| Vendor | tools |", "|---|---|"] + [f"| {k} | {v:,} |" for k, v in by_vendor.most_common()] + ["", "| Tool type | tools |", "|---|---|"] + [f"| {k} | {v:,} |" for k, v in by_type.most_common()]
open(os.path.join(HERE, "summary.md"), "w").write("\n".join(md) + "\n")
# ---- what SAFT-V2-TAB OP10 needs, across every vendor ----
def cand(pred, title, key, limit=12):
    c = [r for r in rows if r["DC_mm"] and pred(r)]; c.sort(key=key)
    out = [f"## {title}", "", f"{len(c)} candidates across the collection; best {min(limit, len(c))}:", "", "| vendor | tool id | type | DC mm | LOC mm | shank mm | OAL mm | flutes | RE mm | presets | description |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {r['vendor']} | {r['tool_id']} | {r['type']} | {r['DC_mm']} | {r['APMX_mm']} | {r['DMM_mm']} | {r['OAL_mm']} | {r['NOF']} | {r['RE_mm']} | {r['n_presets']} | {(r['description'] or '')[:70]} |" for r in c[:limit]]
    return out + [""]
near = lambda a, b, tol: a is not None and b is not None and abs(a - b) <= tol
flat = lambda r: (r["type"] or "").startswith("flat") or r["type"] in ("flat end mill",)
md2 = ["# Candidates for the SAFT-V2-TAB program (06_cam) from the merged collection", "",
       "T1 = 1/4 in square end mill, 3 flutes, flute length ≥ 19 mm; T2 = 1/8 in square end mill, 2 flutes, flute length ≥ 16 mm (4×D reach through 12.7 mm plate); T3 = 1/8 in ball end mill, 2 flutes. Sorted by flute length descending, then by presets.", ""]
md2 += cand(lambda r: flat(r) and near(r["DC_mm"], 6.35, 0.02) and r["NOF"] == 3 and (r["APMX_mm"] or 0) >= 19, "T1 — Ø6.35 square, 3 flutes, LOC ≥ 19", lambda r: (-(r["APMX_mm"] or 0), -(r["n_presets"] or 0)))
md2 += cand(lambda r: flat(r) and near(r["DC_mm"], 3.175, 0.02) and r["NOF"] == 2 and (r["APMX_mm"] or 0) >= 16, "T2 — Ø3.175 square, 2 flutes, LOC ≥ 16", lambda r: (-(r["APMX_mm"] or 0), -(r["n_presets"] or 0)))
md2 += cand(lambda r: (r["type"] or "").startswith("ball") and near(r["DC_mm"], 3.175, 0.02) and r["NOF"] == 2, "T3 — Ø3.175 ball, 2 flutes", lambda r: (-(r["n_presets"] or 0), -(r["APMX_mm"] or 0)))
open(os.path.join(HERE, "saft_v2_candidates.md"), "w").write("\n".join(md2) + "\n")
# ---- FreeCAD 1.0 CAM tool library: .fctb bits + .fctl list, openable in the Tool Bit Library manager ----
# Shapes verified by loading in freecadcmd: endmill/ballend/bullnose take Diameter, CuttingEdgeHeight, Length,
# ShankDiameter (+ FlatRadius for bullnose), drill takes Diameter, Length, TipAngle; attributes Flutes, Material,
# Chipload, SpindleDirection are accepted on all of them.
# (SHAPES, EXTRA and HOLDERS are defined at the top of the file; EXTRA is filled by load_fusion with the tip diameter,
#  taper angle, pitch and shoulder diameter the chamfer / tap / thread-mill / dovetail shapes need beyond the ISO columns)
def fc_bit(r):
    shape = SHAPES.get(r["type"])
    if not shape or not r["DC_mm"] or not r["OAL_mm"]: return None
    q = lambda v: f"{v:.4f} mm"; k = IN2MM if r["unit"] == "in" else 1.0; x = EXTRA.get(r["guid"], {})
    name = f"{r['vendor']} {r['tool_id']}".strip() if r["tool_id"] else f"{r['vendor']} {(r['description'] or '')[:40]}"
    dc, oal, loc, shank = r["DC_mm"], r["OAL_mm"], r["APMX_mm"] or r["OAL_mm"] * 0.4, r["DMM_mm"] or r["DC_mm"]
    prm = {"Diameter": q(dc), "Length": q(oal)}; note = None
    if shape in ("endmill.fcstd", "ballend.fcstd", "bullnose.fcstd"):
        prm["CuttingEdgeHeight"] = q(loc); prm["ShankDiameter"] = q(shank)
        if shape == "bullnose.fcstd": prm["FlatRadius"] = q(max(dc / 2 - (r["RE_mm"] or 0), 0))
    elif shape == "drill.fcstd":
        ta = x.get("TA") or r["TA"]; prm["TipAngle"] = f"{(ta if ta and ta > 0 else 118.0):.4f} °"      # spot/centre drills carry their included angle in TA; plain drills rarely do → 118°
    elif shape == "chamfer.fcstd":
        ta = x.get("TA") or r["TA"] or 45.0; tip = (x.get("tip-diameter") or 0) * k
        prm["CuttingEdgeAngle"] = f"{2 * ta:.4f} °"; prm["CuttingEdgeHeight"] = q(loc); prm["ShankDiameter"] = q(shank); prm["TipDiameter"] = q(max(tip, 0.01))   # Fusion TA is per side, FreeCAD wants the included angle
    elif shape == "thread-mill.fcstd":
        tp = (x.get("TP") or 0) * k
        prm["ShankDiameter"] = q(shank); prm["NeckDiameter"] = q(min(shank, dc * 0.8) if r["type"].startswith("tap") else shank); prm["NeckLength"] = q(max(oal - loc - 1.0, 0.1))
        prm["Crest"] = q(max(tp * 0.3, 0.05)); prm["cuttingAngle"] = "60.0000 °"
        if r["type"].startswith("tap"): note = "TAP represented with FreeCAD's thread-mill shape (cylindrical envelope with thread crest); FreeCAD 1.0 has no tap shape. Pitch kept in attribute.tap_pitch_mm"
    elif shape == "dovetail.fcstd":
        ta = x.get("TA") or r["TA"] or 30.0; neck = (x.get("shoulder-diameter") or 0) * k or shank
        prm["CuttingEdgeAngle"] = f"{2 * ta:.4f} °"; prm["CuttingEdgeHeight"] = q(loc); prm["ShankDiameter"] = q(shank); prm["NeckDiameter"] = q(neck); prm["NeckHeight"] = q(max(oal - loc - 1.0, 0.1)); prm["TipDiameter"] = q(max(dc - 2 * loc * __import__("math").tan(__import__("math").radians(ta)), 0.1))
    att = {"Flutes": int(r["NOF"]) if r["NOF"] else 2, "Material": "Carbide" if (r["BMC"] or "carbide") == "carbide" else "HSS"}
    extra = {"tap_pitch_mm": round((x.get("TP") or 0) * k, 4)} if r["type"].startswith("tap") else {}
    if note: extra["note"] = note
    return {"version": 2, "name": name, "shape": shape, "parameter": prm,
            "attribute": {**att, **extra, "fusion_type": r["type"], "iso13399": {k_: r[k_] for k_ in ("DC", "DMM", "APMX", "OAL", "NOF", "RE", "ND", "TA", "unit")}, "vendor": r["vendor"], "library": r["library"], "product_link": r["product_link"], "source_file": r["source_file"]}}
def write_freecad_library(name, selected):
    lib = os.path.join(HERE, "freecad", name); bits = os.path.join(lib, "Bit"); os.makedirs(bits, exist_ok=True); tools = []; seen = set()
    for r in selected:
        b = fc_bit(r)
        if not b: continue
        fn = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in f"{r['vendor']}_{r['tool_id'] or r['guid'] or len(tools)}")[:80] + ".fctb"
        if fn in seen: continue
        seen.add(fn); json.dump(b, open(os.path.join(bits, fn), "w"), indent=1); tools.append({"nr": len(tools) + 1, "path": fn})
    os.makedirs(os.path.join(lib, "Library"), exist_ok=True)
    json.dump({"version": 1, "tools": tools}, open(os.path.join(lib, "Library", name + ".fctl"), "w"), indent=1)
    return len(tools)
flatmm = lambda r: (r["type"] or "") in SHAPES and r["DC_mm"] and r["APMX_mm"]
starter = [r for r in rows if flatmm(r) and (near(r["DC_mm"], 6.35, 0.02) or near(r["DC_mm"], 3.175, 0.02)) and (r["NOF"] in (2, 3)) and (r["APMX_mm"] >= 16 if near(r["DC_mm"], 3.175, 0.02) else r["APMX_mm"] >= 19)]
n_fc = write_freecad_library("V3_starter_quarter_eighth", starter)
print(f"FreeCAD library freecad/V3_starter_quarter_eighth: {n_fc} bits (every 1/4 in and 1/8 in end mill/ball/bullnose in the collection with the SAFT-V2 reach)")
# chamfer mills, taps, thread mills, dovetails, spot/centre drills — every one in the collection
ctt = [r for r in rows if r["type"] in ("chamfer mill", "tap right hand", "tap left hand", "thread mill", "dovetail mill", "spot drill", "center drill", "counter sink") and r["DC_mm"] and r["OAL_mm"]]
n_ctt = write_freecad_library("V3_chamfer_tap_threadmill", ctt)
print(f"FreeCAD library freecad/V3_chamfer_tap_threadmill: {n_ctt} bits ({Counter(r['type'] for r in ctt).most_common()})")
# holders: FreeCAD 1.0 has no holder tool-bit type → normalized JSON (segments in mm, bottom-up) + holders_export.py makes STEP solids
for h in HOLDERS:
    k = IN2MM if h["unit"] == "in" else 1.0
    h["gauge_length_mm"] = round(float(h["gauge_length"]) * k, 4) if isinstance(h.get("gauge_length"), (int, float)) else None
    num = lambda v: (num(v[0]) if isinstance(v, (list, tuple)) and v else (float(v) if isinstance(v, (int, float)) else 0.0))   # a few vendors wrap values in lists
    h["segments_mm"] = [dict(height=round(num(s.get("height")) * k, 4), lower_diameter=round(num(s.get("lower-diameter")) * k, 4), upper_diameter=round(num(s.get("upper-diameter")) * k, 4)) for s in (h["segments"] or []) if isinstance(s, dict)]
json.dump(HOLDERS, open(os.path.join(HERE, "holders.json"), "w"), indent=0)
print(f"holders.json: {len(HOLDERS)} holders from {Counter(h['vendor'] for h in HOLDERS).most_common()}")
if "--full" in sys.argv:   # one FreeCAD library per vendor with every exportable tool type (~125k bits, GUI-unfriendly; for scripted use)
    for v in sorted(by_vendor):
        n = write_freecad_library("full/" + "".join(ch if ch.isalnum() else "_" for ch in v), [r for r in rows if r["vendor"] == v and r["type"] in SHAPES]); print(f"  full/{v}: {n} bits")
for name, n in log: print(f"{n:7,}  {name}")
print(f"TOTAL {len(rows):,} tools, {len(by_vendor)} vendors, {len(by_lib)} libraries -> collection.csv/.json, summary.md, saft_v2_candidates.md")
