"""DXF of the SAFT-V2-TAB v2 profile (exact arcs) via FreeCAD's Draft DXF exporter + the dimple circles on a DIMPLES layer.
Usage: QT_QPA_PLATFORM=offscreen freecadcmd export_dxf.py → SAFT-V2-TAB_profile.dxf"""
import os, json, FreeCAD, Part, importDXF
from FreeCAD import Vector as V
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "02_design", "v2")
P = json.load(open(os.path.join(D, "SAFT-V2-TAB_v2_params.json")))
solid = Part.read(os.path.join(D, "SAFT-V2-TAB_v2.step"))
sec = solid.slice(V(0, 0, 1), P["params"]["W"] / 2)
doc = FreeCAD.newDocument("dxf")
objs = []
for i, w in enumerate(sec):
    o = doc.addObject("Part::Feature", f"PROFILE_{i}"); o.Shape = w; objs.append(o)
for j, (x, y) in enumerate(P["dimple_xy"]):
    o = doc.addObject("Part::Feature", f"DIMPLE_{j}"); o.Shape = Part.Wire(Part.makeCircle(1.0, V(x, y, P["params"]["W"] / 2))); objs.append(o)
doc.recompute()
out = os.path.join(HERE, "SAFT-V2-TAB_profile.dxf"); importDXF.export(objs, out)
print("dxf", os.path.getsize(out), "bytes,", len(sec), "profile wire(s),", len(P["dimple_xy"]), "dimples")
