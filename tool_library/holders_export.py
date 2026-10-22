"""Tool holders → STEP solids. FreeCAD 1.0 CAM has no holder tool-bit type, so every holder in holders.json (written by
collection.py: Fusion 'holder' records, segments bottom-up in mm) is revolved into a solid and written as STEP, with a
JSON index. Usage: QT_QPA_PLATFORM=offscreen freecadcmd holders_export.py  [limit via HOLDERS_LIMIT env]
Output: freecad/holders/<vendor>_<id>.step + freecad/holders/index.json"""
import os, json, math
import FreeCAD, Part
from FreeCAD import Vector as V
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "freecad", "holders"); os.makedirs(OUT, exist_ok=True)
H = json.load(open(os.path.join(HERE, "holders.json"))); limit = int(os.environ.get("HOLDERS_LIMIT", "0") or 0)
index = []; fails = []
for i, h in enumerate(H[:limit] if limit else H):
    segs = h.get("segments_mm") or []
    if not segs: fails.append((h.get("product_id"), "no segments")); continue
    try:
        # profile in the XZ plane: z up from the tool tip end (z=0) through the holder, x = radius
        pts = [V(0, 0, 0)]; z = 0.0
        for s in segs:
            pts.append(V(s["lower_diameter"] / 2, 0, z)); z += s["height"]; pts.append(V(s["upper_diameter"] / 2, 0, z))
        pts.append(V(0, 0, z))
        # drop consecutive duplicates
        clean = [pts[0]]
        for p in pts[1:]:
            if (p - clean[-1]).Length > 1e-6: clean.append(p)
        clean.append(clean[0]) if (clean[-1] - clean[0]).Length > 1e-6 else None
        face = Part.Face(Part.makePolygon(clean)); solid = face.revolve(V(0, 0, 0), V(0, 0, 1), 360)
        if not solid.isValid() or solid.Volume <= 0: raise ValueError("invalid solid")
        name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in f"{h['vendor']}_{h.get('product_id') or h.get('guid')}")[:80]
        path = os.path.join(OUT, name + ".step"); solid.exportStep(path)
        index.append(dict(file=name + ".step", vendor=h["vendor"], product_id=h.get("product_id"), description=h.get("description"), gauge_length_mm=h.get("gauge_length_mm"),
                          height_mm=round(z, 3), max_diameter_mm=round(max(max(s["lower_diameter"], s["upper_diameter"]) for s in segs), 3), volume_mm3=round(solid.Volume, 1), product_link=h.get("product_link")))
    except Exception as e: fails.append((h.get("product_id"), repr(e)[:100]))
json.dump(dict(count=len(index), failed=fails, holders=index), open(os.path.join(OUT, "index.json"), "w"), indent=1)
print(f"holders: {len(index)} STEP solids written to freecad/holders, {len(fails)} failed")
for f in fails[:8]: print("  FAIL", f)
