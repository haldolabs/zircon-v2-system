"""Query the local RobbJack ISO 13399 master catalog (robbjack/robbjack-master-catalog.json) and the Fusion .tools library.
Usage:
  python catalog.py summary                       # families, tool types, what fields exist
  python catalog.py find [--dia 0.125] [--type "End Mill"] [--flutes 2] [--loc-min 0.6] [--ball] [--unit in|mm] [--limit 20]
  python catalog.py presets TOOLNBR               # cutting presets for one tool from the Fusion library (speeds/feeds by material)
  python catalog.py export-freecad TOOLNBR ...    # FreeCAD 1.0 CAM tool-bit .fctb JSON (endmill / ballend shapes) into freecad_bits/
  python catalog.py saft-v2                       # the three tools the SAFT-V2-TAB program needs, picked from the catalog
Works with /usr/bin/python3 or the cae env (stdlib only)."""
import json, sys, os, zipfile, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw") if os.path.isdir(os.path.join(HERE, "raw")) else HERE   # repo layout keeps vendor files under raw/
RJ = os.path.join(RAW, "robbjack")
CAT = json.load(open(os.path.join(RJ, "robbjack-master-catalog.json")))
TOOLS = CAT["tools"] if isinstance(CAT.get("tools"), list) else list(CAT["tools"].values())
def val(t, key, unit="in"):
    v = t.get("specs", {}).get(key, t.get(key))
    if isinstance(v, dict): return v.get(unit)
    return v
def fusion_tools():
    with zipfile.ZipFile(os.path.join(RJ, "robbjack-fusion360.tools")) as z: return json.load(z.open("tools.json"))
def summary():
    from collections import Counter
    print(f"{CAT['toolCount']} tools, schema {CAT['schemaVersion']}, generated {CAT['generated']}"); print("license:", CAT["license"])
    print("parameters:", ", ".join(f"{k} ({v['label']})" for k, v in CAT["parameters"].items()))
    print("tool types:", Counter(tt for t in TOOLS for tt in (t.get("toolTypes") or t.get("tool_types") or [])).most_common())
    print("lines:", Counter(t.get("line") for t in TOOLS).most_common(12))
    f = fusion_tools(); print("fusion .tools:", len(f.get("data", f)), "tools; first keys:", list((f.get("data", f))[0].keys())[:12])
def find(a):
    out = []
    for t in TOOLS:
        types = t.get("toolTypes") or t.get("tool_types") or []
        if a.type and not any(a.type.lower() in x.lower() for x in types): continue
        dc = val(t, "DC", a.unit)
        if a.dia is not None and (dc is None or abs(dc - a.dia) > a.tol): continue
        if a.flutes is not None and val(t,"NOF") != a.flutes: continue
        loc = val(t, "APMX", a.unit)
        if a.loc_min is not None and (loc is None or loc < a.loc_min): continue
        re_ = val(t, "RE", a.unit)
        if a.ball and not (re_ and dc and abs(re_ - dc / 2) < 1e-4): continue
        if a.square and re_: continue
        out.append(t)
    out.sort(key=lambda t: (-(val(t, "APMX", a.unit) or 0)))
    for t in out[:a.limit]:
        print(f"{t['toolNbr']:14s} DC {val(t,'DC',a.unit)} LOC {val(t,'APMX',a.unit)} DMM {val(t,'DMM',a.unit)} OAL {val(t,'OAL',a.unit)} NOF {val(t,'NOF')} RE {val(t,'RE',a.unit)} "
              f"ND {val(t,'ND',a.unit)} LN {val(t,'LN',a.unit)} FHA {val(t,'FHA')}  {t.get('series')} | {t.get('name','')[:70]}")
    print(len(out), "matches"); return out
def presets(nbr):
    f = fusion_tools(); data = f.get("data", f)
    for t in data:
        if (t.get("product-id") or t.get("description", "")).startswith(nbr) or t.get("product-id") == nbr:
            print(json.dumps({k: t[k] for k in t if k != "start-values"}, indent=1)[:1500])
            for p in t.get("start-values", {}).get("presets", []): print(" preset:", json.dumps(p))
            return t
    print("not in the Fusion library:", nbr)
def to_freecad(t):
    """FreeCAD 1.0 CAM tool bit (.fctb): shape endmill.fcstd or ballend.fcstd, parameters as quantities in mm."""
    dc = val(t, "DC", "mm"); loc = val(t, "APMX", "mm"); dmm = val(t, "DMM", "mm"); oal = val(t, "OAL", "mm"); re_ = val(t, "RE", "mm"); nof = val(t,"NOF")
    ball = re_ and abs(re_ - dc / 2) < 1e-3
    bit = {"version": 2, "name": f"RobbJack {t['toolNbr']}", "shape": "ballend.fcstd" if ball else "endmill.fcstd",
           "parameter": {"Diameter": f"{dc:.4f} mm", "CuttingEdgeHeight": f"{loc:.4f} mm", "Length": f"{oal:.4f} mm", "ShankDiameter": f"{dmm:.4f} mm", "Flutes": int(nof or 0), "Material": "Carbide"},
           "attribute": {"iso13399": {k: t.get("specs", {}).get(k) for k in ("DC", "DCX", "DMM", "APMX", "OAL", "RE", "ND", "LN", "NOF", "FHA", "KCH", "CCMS")}, "source": "robbjack-master-catalog.json 2026-10-13", "productPage": t.get("url") or f"https://robbjack.com/tools/{t['toolNbr']}"}}
    # ballend.fcstd has CuttingEdgeHeight too (verified by loading in FreeCAD 1.0): keep it for both shapes
    return bit
def export_freecad(nbrs):
    os.makedirs(os.path.join(HERE, "freecad_bits"), exist_ok=True); by = {t["toolNbr"]: t for t in TOOLS}
    for n in nbrs:
        p = os.path.join(HERE, "freecad_bits", f"RobbJack_{n}.fctb"); json.dump(to_freecad(by[n]), open(p, "w"), indent=1); print("wrote", p)
def saft_v2():
    """What SAFT-V2-TAB_OP10.nc needs: T1 1/4 in 3FL square EM >= 19 mm LOC (0.75 in); T2 1/8 in 2FL square EM >= 16 mm LOC (0.63 in, 4xD reach);
    T3 1/8 in 2FL ball EM. Prefer non-ferrous (aluminium) high-helix lines; a reduced-neck tool counts if neck length ND >= 16 mm for T2."""
    picks = {}
    print("== T1 candidates: 0.25 in, 3 flutes, LOC >= 0.75 in, square")
    c = find(argparse.Namespace(type="End Mill", dia=0.25, tol=1e-3, flutes=3, loc_min=0.75, ball=False, square=True, unit="in", limit=8))
    print("== T2 candidates: 0.125 in, 2 flutes, square, LOC >= 0.63 in  (or a reduced-neck tool with ND >= 0.63)")
    c2 = find(argparse.Namespace(type="End Mill", dia=0.125, tol=1e-3, flutes=2, loc_min=0.63, ball=False, square=True, unit="in", limit=8))
    if not c2:
        print("   none with LOC >= 0.63: looking for reduced-neck (ND >= 0.63 in) instead")
        c2 = [t for t in find(argparse.Namespace(type="End Mill", dia=0.125, tol=1e-3, flutes=2, loc_min=None, ball=False, square=True, unit="in", limit=0)) if (val(t, "ND", "in") or 0) >= 0.63 or (val(t, "LN", "in") or 0) >= 0.63]
        c2.sort(key=lambda t: -(val(t, "ND", "in") or val(t, "LN", "in") or 0))
        for t in c2[:8]: print(f"   {t['toolNbr']:14s} LOC {val(t,'APMX','in')} ND {val(t,'ND','in')} LN {val(t,'LN','in')} {t.get('series')} | {t.get('name','')[:60]}")
    print("== T3 candidates: 0.125 in ball, 2 flutes")
    c3 = find(argparse.Namespace(type="End Mill", dia=0.125, tol=1e-3, flutes=2, loc_min=None, ball=True, square=False, unit="in", limit=8))
    for k, lst in (("T1", c), ("T2", c2), ("T3", c3)):
        if lst: picks[k] = lst[0]["toolNbr"]
    print("picks:", picks); json.dump(picks, open(os.path.join(HERE, "saft_v2_picks.json"), "w"), indent=1)
    export_freecad(list(picks.values()))
    for k, n in picks.items(): print(f"--- {k} {n} Fusion presets:"); presets(n)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("summary"); sub.add_parser("saft-v2")
    f = sub.add_parser("find"); f.add_argument("--dia", type=float); f.add_argument("--tol", type=float, default=1e-3); f.add_argument("--type", default="End Mill"); f.add_argument("--flutes", type=int)
    f.add_argument("--loc-min", type=float); f.add_argument("--ball", action="store_true"); f.add_argument("--square", action="store_true"); f.add_argument("--unit", default="in"); f.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("presets"); p.add_argument("nbr"); e = sub.add_parser("export-freecad"); e.add_argument("nbrs", nargs="+")
    a = ap.parse_args()
    {"summary": summary, "find": lambda: find(a), "presets": lambda: presets(a.nbr), "export-freecad": lambda: export_freecad(a.nbrs), "saft-v2": saft_v2}[a.cmd or "summary"]()
