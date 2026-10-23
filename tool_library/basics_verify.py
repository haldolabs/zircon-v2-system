"""Load every bit of a FreeCAD library in FreeCAD 1.0 and check each builds a valid solid with its parameters actually applied
(not the stock shape, bbox = max(D, shank) × Length). Optionally writes all the solids as one STL grid for a contact-sheet render.
Run: QT_QPA_PLATFORM=offscreen [LIBDIR=freecad/V3_standard] [GRID_STL=sheet.stl] freecadcmd basics_verify.py
(module-level code: freecadcmd imports scripts; paths relative to this script's directory)"""
import os, json, sys, time
import FreeCAD, Path, Part, Mesh
import Path.Tool.Bit as Bit
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
LIB = os.path.join(HERE, os.environ.get("LIBDIR", os.path.join("freecad", "basics")))
GRID = os.environ.get("GRID_STL"); grid = Mesh.Mesh(); cols, px, py = 16, 18.0, 125.0
lst = json.load(open(os.path.join(LIB, "Library", "V3_standard.fctl")))
# default volume of each stock shape: a bit whose solid equals it had its parameters silently rejected by the sketch solver
defaults = {}
for sh in sorted({json.load(open(os.path.join(LIB, "Bit", t["path"])))["shape"] for t in lst["tools"]}):
    d = FreeCAD.openDocument(os.path.join(LIB, "Shape", sh)); d.recompute()
    body = [o for o in d.Objects if o.TypeId.startswith("PartDesign::Body")][0]; defaults[sh] = round(body.Shape.Volume, 1); FreeCAD.closeDocument(d.Name)
doc = FreeCAD.newDocument("verify"); ok = bad = 0; t0 = time.time()
for t in lst["tools"]:
    p = os.path.join(LIB, "Bit", t["path"])
    try:
        b = Bit.Factory.CreateFrom(p, f"T{t['nr']:02d}"); doc.recompute()
        sh = b.Shape
        if sh.isNull() or not sh.isValid() or sh.Volume <= 0: raise RuntimeError(f"invalid shape (null={sh.isNull()} valid={sh.isValid()} vol={sh.Volume})")
        j = json.load(open(p)); prm = j["parameter"]; val = lambda k: float(prm[k].split()[0])
        if abs(round(sh.Volume, 1) - defaults[j["shape"]]) < 0.05: raise RuntimeError(f"parameters NOT applied: solid is the stock {j['shape']} ({defaults[j['shape']]} mm3)")
        bb = sh.BoundBox; wantD = max(val("Diameter"), val("ShankDiameter")) if "ShankDiameter" in prm else val("Diameter")
        if abs(bb.ZLength - val("Length")) > 0.05 or abs(max(bb.XLength, bb.YLength) - wantD) > 0.05: raise RuntimeError(f"bbox {bb.XLength:.3f}x{bb.YLength:.3f}x{bb.ZLength:.3f} vs D={wantD} L={val('Length')}")
        ok += 1
        if GRID:
            i = t["nr"] - 1; g = sh.copy(); bb = g.BoundBox
            g.translate(FreeCAD.Vector((i % cols) * px - bb.Center.x, -(i // cols) * py - bb.Center.y, -bb.ZMin)); grid.addMesh(Mesh.Mesh(g.tessellate(0.02)))
    except Exception as e:
        bad += 1; print(f"FAIL T{t['nr']:02d} {t['path']}: {e}")
if GRID: grid.write(os.path.join(HERE, GRID) if not os.path.isabs(GRID) else GRID)
print(f"{os.path.basename(LIB)}: {ok} bits OK, {bad} failed, {time.time()-t0:.1f}s")
