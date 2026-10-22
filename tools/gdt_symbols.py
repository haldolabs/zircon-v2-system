"""GD&T / drawing symbol library for script-generated SVG drawings (ASME Y14.5-2018, ISO 1101, AWS A2.4, ISO 1302).

Glyph coverage was verified with fontconfig on this host: every GD&T symbol below exists in Noto Sans Symbols /
Noto Sans Symbols2 (installed), most also in DejaVu Sans. FreeCAD also ships symbol SVGs in
/usr/share/freecad/Mod/TechDraw/Symbols/{gd-and-t,surface-roughness-symbols,Welding,misc,other}/ (see SYMBOL_SVG_DIRS).

Use:  from gdt_symbols import FONT_STACK, GDT, fcf, datum_feature, surface_finish, weld_symbol, proof_sheet
Every helper returns an SVG fragment string in mm user units (1 unit = 1 mm) using class names v (visible line),
d (dimension line), arr (arrowhead), t (text); define those classes in the host SVG's <style>.
"""
import math, os, subprocess, shutil
FONT_STACK = "'Noto Sans Symbols','Noto Sans Symbols2','DejaVu Sans','FreeSans',sans-serif"   # for symbols
TEXT_FONT = "'osifont','DejaVu Sans',sans-serif"                                                # ISO 3098 lettering if installed
SYMBOL_SVG_DIRS = {k: f"/usr/share/freecad/Mod/TechDraw/Symbols/{k}" for k in ("gd-and-t", "surface-roughness-symbols", "Welding", "misc", "other")}

# name: (glyph, codepoint, meaning, note)
GDT = {
  "straightness":     ("⏤", 0x23E4, "straightness (form)", ""),
  "flatness":         ("⏥", 0x23E5, "flatness (form)", ""),
  "circularity":      ("○", 0x25CB, "circularity / roundness (form)", ""),
  "cylindricity":     ("⌭", 0x232D, "cylindricity (form)", ""),
  "profile_line":     ("⌒", 0x2312, "profile of a line", ""),
  "profile_surface":  ("⌓", 0x2313, "profile of a surface", ""),
  "angularity":       ("∠", 0x2220, "angularity (orientation)", ""),
  "perpendicularity": ("⟂", 0x27C2, "perpendicularity (orientation)", ""),
  "parallelism":      ("∥", 0x2225, "parallelism (orientation)", ""),
  "position":         ("⌖", 0x2316, "position (location)", "Noto Sans Symbols2"),
  "concentricity":    ("◎", 0x25CE, "concentricity / coaxiality (ISO; removed from ASME 2018)", ""),
  "symmetry":         ("⌯", 0x232F, "symmetry (ISO; removed from ASME 2018)", ""),
  "circular_runout":  ("↗", 0x2197, "circular runout", "single arrow"),
  "total_runout":     ("⌰", 0x2330, "total runout", "double arrow"),
  "MMC":              ("Ⓜ", 0x24C2, "maximum material condition modifier", ""),
  "LMC":              ("Ⓛ", 0x24C1, "least material condition modifier", ""),
  "free_state":       ("Ⓕ", 0x24BB, "free state", ""),
  "projected":        ("Ⓟ", 0x24C5, "projected tolerance zone", ""),
  "tangent_plane":    ("Ⓣ", 0x24C9, "tangent plane", ""),
  "unequal":          ("Ⓤ", 0x24CA, "unequally disposed profile", ""),
  "statistical":      ("Ⓢ", 0x24C8, "statistical tolerance", ""),
  "envelope":         ("Ⓔ", 0x24BA, "envelope requirement (ISO)", ""),
  "continuous":       ("Ⓒ", 0x24B8, "continuous feature", ""),
  "independency":     ("Ⓘ", 0x24BE, "independency (ISO)", ""),
  "diameter":         ("⌀", 0x2300, "diameter", ""),
  "sph_diameter":     ("S⌀", 0x2300, "spherical diameter", "S + diameter"),
  "radius":           ("R", 0x52, "radius", ""),
  "sph_radius":       ("SR", 0x52, "spherical radius", ""),
  "controlled_radius":("CR", 0x52, "controlled radius", ""),
  "square":           ("□", 0x25A1, "square", ""),
  "counterbore":      ("⌴", 0x2334, "counterbore / spotface", ""),
  "countersink":      ("⌵", 0x2335, "countersink", ""),
  "depth":            ("⌶", 0x2336, "depth", ""),
  "conical_taper":    ("⌲", 0x2332, "conical taper", ""),
  "slope":            ("⌳", 0x2333, "slope", ""),
  "arc_length":       ("⌒", 0x2312, "arc length (over the dimension)", ""),
  "between":          ("↔", 0x2194, "between", ""),
  "all_around":       ("○", 0x25CB, "all around (circle on the leader bend)", "drawn, not text"),
  "all_over":         ("◎", 0x25CE, "all over (double circle)", "drawn, not text"),
  "degree":           ("°", 0x00B0, "degrees", ""),
  "plus_minus":       ("±", 0x00B1, "plus/minus", ""),
  "times":            ("X",     0x58,   "places (6X)", ""),
  "datum_target":     ("⨉", 0x2A09, "datum target point (×)", ""),
  "basic":            ("[ ]",   0x5B,   "basic dimension (boxed)", "drawn box"),
  "reference":        ("( )",   0x28,   "reference dimension", ""),
  "cf":               ("Ⓒ", 0x24B8, "continuous feature", ""),
}
WELD_GLYPHS = ("fillet", "square", "vee", "bevel", "u", "j", "plug", "spot", "seam", "flare_v", "flare_bevel", "edge")

def _txt(x, y, s, size=3.2, anchor="middle", font=FONT_STACK, cls="t"):
    return f'<text class="{cls}" x="{x:.3f}" y="{y:.3f}" font-size="{size}" font-family="{font}" text-anchor="{anchor}">{s}</text>'

def fcf(x, y, characteristic, tolerance, datums=(), modifiers="", h=6.0, dia=False, between=None):
    """Feature control frame at top-left (x,y). characteristic = key of GDT; tolerance e.g. '0.05'; datums e.g. ('A','B','C')
    or with modifiers ('A','BⓂ'); modifiers = string appended to the tolerance cell (e.g. GDT['MMC'][0]).
    Returns (svg, total_width)."""
    sym = GDT[characteristic][0]
    tol = (GDT["diameter"][0] if dia else "") + tolerance + modifiers
    cells = [(sym, h * 1.15), (tol, max(h * 1.6, 2.1 * len(tol) + 2))] + [(d, h * 1.05) for d in datums]
    out = []; X = x
    for s, w in cells:
        out.append(f'<rect class="v" x="{X:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="none"/>')
        out.append(_txt(X + w / 2, y + h * 0.72, s, size=h * 0.55)); X += w
    if between:
        out.append(_txt(X + 1, y + h * 0.72, f"{between[0]} {GDT['between'][0]} {between[1]}", size=h * 0.5, anchor="start"))
    return "\n".join(out), X - x

def datum_feature(x, y, label, angle_deg=90, h=6.0):
    """Datum feature symbol: filled/open triangle on the feature at (x,y), leader of length h, boxed letter. angle = leader direction."""
    a = math.radians(angle_deg); tx, ty = x + h * math.cos(a), y + h * math.sin(a); nx, ny = -math.sin(a) * h * 0.33, math.cos(a) * h * 0.33
    bx, by = x + (h + h * 0.5) * math.cos(a) - h / 2, y + (h + h * 0.5) * math.sin(a) - h / 2
    return "\n".join([f'<polygon class="v" points="{x:.3f},{y:.3f} {tx+nx:.3f},{ty+ny:.3f} {tx-nx:.3f},{ty-ny:.3f}" fill="none"/>',
                      f'<rect class="v" x="{bx:.3f}" y="{by:.3f}" width="{h:.3f}" height="{h:.3f}" fill="none"/>',
                      _txt(bx + h / 2, by + h * 0.73, label, size=h * 0.58, font=TEXT_FONT)])

def surface_finish(x, y, ra=None, machining="any", lay=None, h=5.0, extra=None):
    """ISO 1302 / ASME Y14.36 surface texture symbol with its tip at (x,y). machining: 'any' (plain check), 'required'
    (bar), 'prohibited' (circle). ra = roughness value text placed left of the long leg; lay = lay symbol letter."""
    s = h; out = [f'<polyline class="v" points="{x-0.5*s:.3f},{y-s:.3f} {x:.3f},{y:.3f} {x+0.9*s:.3f},{y-1.8*s:.3f}" fill="none"/>']
    if machining == "required": out.append(f'<line class="v" x1="{x-0.5*s:.3f}" y1="{y-s:.3f}" x2="{x+0.5*s:.3f}" y2="{y-s:.3f}"/>')
    if machining == "prohibited": out.append(f'<circle class="v" cx="{x+0.05*s:.3f}" cy="{y-0.55*s:.3f}" r="{0.3*s:.3f}" fill="none"/>')
    if ra is not None: out.append(_txt(x - 0.7 * s, y - 1.25 * s, f"Ra {ra}", size=h * 0.55, anchor="end", font=TEXT_FONT))
    if lay: out.append(_txt(x + 0.45 * s, y - 0.2 * s, lay, size=h * 0.5, anchor="start", font=TEXT_FONT))
    if extra: out.append(_txt(x + 1.0 * s, y - 1.25 * s, extra, size=h * 0.5, anchor="start", font=TEXT_FONT))
    return "\n".join(out)

def _weld_glyph(kind, cx, baseline, s, above):
    """AWS A2.4 weld glyph drawn as paths; 'above' = other side (glyph mirrored above the reference line)."""
    sgn = -1 if above else 1   # SVG y grows down; arrow side = below the line
    p = []
    if kind == "fillet":   p.append(f'<polygon class="v" points="{cx-s/2:.3f},{baseline:.3f} {cx-s/2:.3f},{baseline+sgn*s:.3f} {cx+s/2:.3f},{baseline:.3f}" fill="none"/>')
    elif kind == "square": p += [f'<line class="v" x1="{cx-s*0.25:.3f}" y1="{baseline:.3f}" x2="{cx-s*0.25:.3f}" y2="{baseline+sgn*s:.3f}"/>', f'<line class="v" x1="{cx+s*0.25:.3f}" y1="{baseline:.3f}" x2="{cx+s*0.25:.3f}" y2="{baseline+sgn*s:.3f}"/>']
    elif kind == "vee":    p.append(f'<polyline class="v" points="{cx-s/2:.3f},{baseline+sgn*s:.3f} {cx:.3f},{baseline:.3f} {cx+s/2:.3f},{baseline+sgn*s:.3f}" fill="none"/>')
    elif kind == "bevel":  p.append(f'<polyline class="v" points="{cx-s/2:.3f},{baseline+sgn*s:.3f} {cx-s/2:.3f},{baseline:.3f} {cx+s/2:.3f},{baseline+sgn*s:.3f}" fill="none"/>')
    elif kind == "u":      p.append(f'<path class="v" d="M {cx-s/2:.3f} {baseline+sgn*s:.3f} L {cx-s/2:.3f} {baseline+sgn*s*0.5:.3f} A {s/2:.3f} {s/2:.3f} 0 0 {1 if above else 0} {cx+s/2:.3f} {baseline+sgn*s*0.5:.3f} L {cx+s/2:.3f} {baseline+sgn*s:.3f}" fill="none"/>')
    elif kind == "j":      p.append(f'<path class="v" d="M {cx-s/2:.3f} {baseline+sgn*s:.3f} L {cx-s/2:.3f} {baseline:.3f} M {cx-s/2:.3f} {baseline+sgn*s*0.5:.3f} A {s/2:.3f} {s/2:.3f} 0 0 {1 if above else 0} {cx+s/2:.3f} {baseline+sgn*s*0.5:.3f} L {cx+s/2:.3f} {baseline+sgn*s:.3f}" fill="none"/>')
    elif kind == "plug":   p.append(f'<rect class="v" x="{cx-s/2:.3f}" y="{min(baseline, baseline+sgn*s*0.6):.3f}" width="{s:.3f}" height="{s*0.6:.3f}" fill="none"/>')
    elif kind == "spot":   p.append(f'<circle class="v" cx="{cx:.3f}" cy="{baseline+sgn*s*0.5:.3f}" r="{s*0.45:.3f}" fill="none"/>')
    elif kind == "seam":   p += [f'<circle class="v" cx="{cx:.3f}" cy="{baseline+sgn*s*0.5:.3f}" r="{s*0.45:.3f}" fill="none"/>', f'<line class="v" x1="{cx-s*0.6:.3f}" y1="{baseline+sgn*s*0.35:.3f}" x2="{cx+s*0.6:.3f}" y2="{baseline+sgn*s*0.35:.3f}"/>', f'<line class="v" x1="{cx-s*0.6:.3f}" y1="{baseline+sgn*s*0.65:.3f}" x2="{cx+s*0.6:.3f}" y2="{baseline+sgn*s*0.65:.3f}"/>']
    elif kind == "flare_v":p.append(f'<path class="v" d="M {cx-s*0.6:.3f} {baseline+sgn*s:.3f} Q {cx-s*0.1:.3f} {baseline+sgn*s:.3f} {cx-s*0.1:.3f} {baseline:.3f} M {cx+s*0.6:.3f} {baseline+sgn*s:.3f} Q {cx+s*0.1:.3f} {baseline+sgn*s:.3f} {cx+s*0.1:.3f} {baseline:.3f}" fill="none"/>')
    elif kind == "flare_bevel": p.append(f'<path class="v" d="M {cx-s*0.25:.3f} {baseline+sgn*s:.3f} L {cx-s*0.25:.3f} {baseline:.3f} M {cx+s*0.7:.3f} {baseline+sgn*s:.3f} Q {cx+s*0.2:.3f} {baseline+sgn*s:.3f} {cx+s*0.2:.3f} {baseline:.3f}" fill="none"/>')
    elif kind == "edge":   p += [f'<line class="v" x1="{cx-s*0.3:.3f}" y1="{baseline:.3f}" x2="{cx-s*0.3:.3f}" y2="{baseline+sgn*s:.3f}"/>', f'<line class="v" x1="{cx+s*0.3:.3f}" y1="{baseline:.3f}" x2="{cx+s*0.3:.3f}" y2="{baseline+sgn*s:.3f}"/>', f'<line class="v" x1="{cx-s*0.3:.3f}" y1="{baseline+sgn*s:.3f}" x2="{cx+s*0.3:.3f}" y2="{baseline+sgn*s:.3f}"/>']
    return p

def weld_symbol(ax, ay, rx, ry, arrow_side=None, other_side=None, size=None, length_pitch=None, all_around=False, field=False,
                tail=None, contour=None, s=4.0, ref_len=22.0, left=False):
    """AWS A2.4 welding symbol. Arrow from the reference-line junction (rx,ry) to the joint at (ax,ay). Reference line
    extends from (rx,ry) toward +x (or -x if left). arrow_side/other_side: weld kind from WELD_GLYPHS. size: text left of the
    glyph (e.g. '5'); length_pitch: text right (e.g. '50-100'). contour: 'flush' | 'convex' | 'concave'."""
    out = []; dirn = -1 if left else 1
    out.append(f'<line class="v" x1="{rx:.3f}" y1="{ry:.3f}" x2="{ax:.3f}" y2="{ay:.3f}"/>')
    ang = math.degrees(math.atan2(ay - ry, ax - rx)); L_ = 2.2; w = 0.7
    bx, by = ax - L_ * math.cos(math.radians(ang)), ay - L_ * math.sin(math.radians(ang)); nx, ny = -math.sin(math.radians(ang)) * w, math.cos(math.radians(ang)) * w
    out.append(f'<polygon class="arr" points="{ax:.3f},{ay:.3f} {bx+nx:.3f},{by+ny:.3f} {bx-nx:.3f},{by-ny:.3f}"/>')
    ex = rx + dirn * ref_len
    out.append(f'<line class="v" x1="{rx:.3f}" y1="{ry:.3f}" x2="{ex:.3f}" y2="{ry:.3f}"/>')
    cx = rx + dirn * ref_len * 0.5
    if arrow_side: out += _weld_glyph(arrow_side, cx, ry, s, above=False)
    if other_side: out += _weld_glyph(other_side, cx, ry, s, above=True)
    if size: out.append(_txt(cx - s * 0.9, ry + s * 0.95, str(size), size=s * 0.75, anchor="end", font=TEXT_FONT))
    if length_pitch: out.append(_txt(cx + s * 0.9, ry + s * 0.95, str(length_pitch), size=s * 0.75, anchor="start", font=TEXT_FONT))
    if contour == "flush": out.append(f'<line class="v" x1="{cx-s*0.5:.3f}" y1="{ry+s*1.25:.3f}" x2="{cx+s*0.5:.3f}" y2="{ry+s*1.25:.3f}"/>')
    if contour == "convex": out.append(f'<path class="v" d="M {cx-s*0.5:.3f} {ry+s*1.35:.3f} Q {cx:.3f} {ry+s*0.85:.3f} {cx+s*0.5:.3f} {ry+s*1.35:.3f}" fill="none"/>')
    if contour == "concave": out.append(f'<path class="v" d="M {cx-s*0.5:.3f} {ry+s*1.05:.3f} Q {cx:.3f} {ry+s*1.55:.3f} {cx+s*0.5:.3f} {ry+s*1.05:.3f}" fill="none"/>')
    if all_around: out.append(f'<circle class="v" cx="{rx:.3f}" cy="{ry:.3f}" r="{s*0.4:.3f}" fill="none"/>')
    if field: out.append(f'<polygon class="arr" points="{rx:.3f},{ry:.3f} {rx:.3f},{ry-s*1.3:.3f} {rx+dirn*s*0.9:.3f},{ry-s*1.0:.3f}"/>')
    if tail:
        out.append(f'<polyline class="v" points="{ex+dirn*s*0.8:.3f},{ry-s*0.8:.3f} {ex:.3f},{ry:.3f} {ex+dirn*s*0.8:.3f},{ry+s*0.8:.3f}" fill="none"/>')
        out.append(_txt(ex + dirn * s * 1.1, ry + s * 0.3, tail, size=s * 0.7, anchor="start" if not left else "end", font=TEXT_FONT))
    return "\n".join(out)

STYLE = ".v{stroke:#000;stroke-width:0.35;fill:none}.d{stroke:#000;stroke-width:0.18;fill:none}.arr{fill:#000;stroke:none}.t{fill:#000}"

def proof_sheet(path_svg, render_png=True):
    """Render every glyph and helper once so a human can verify the fonts on this host actually draw them."""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210" font-family="{FONT_STACK}">', f"<style>{STYLE}</style>",
         '<rect width="297" height="210" fill="#fff"/>', _txt(148, 10, "GD&T symbol proof sheet — fonts on this host", 5, font=TEXT_FONT)]
    x, y = 8, 20
    for i, (k, (g, cp, meaning, note)) in enumerate(GDT.items()):
        o.append(f'<rect class="v" x="{x}" y="{y-5}" width="8" height="7"/>'); o.append(_txt(x + 4, y + 0.4, g, 4.2))
        o.append(_txt(x + 10, y, f"{k}  U+{cp:04X}  {meaning}", 2.4, anchor="start", font=TEXT_FONT))
        y += 7.2
        if y > 196: y = 20; x += 100
    # helpers
    X, Y = 212, 20
    s1, w1 = fcf(X, Y, "position", "0.1", ("A", "B" + GDT["MMC"][0], "C"), modifiers=GDT["MMC"][0], dia=True); o.append(s1)
    s2, w2 = fcf(X, Y + 9, "profile_surface", "0.2", ("A",), between=("D", "E")); o.append(s2)
    s3, w3 = fcf(X, Y + 18, "perpendicularity", "0.05", ("A",)); o.append(s3)
    s4, w4 = fcf(X, Y + 27, "flatness", "0.02", ()); o.append(s4)
    o.append(datum_feature(X + 4, Y + 48, "A", 90)); o.append(datum_feature(X + 20, Y + 48, "B", 0)); o.append(datum_feature(X + 40, Y + 48, "C", -90))
    o.append(surface_finish(X + 5, Y + 75, ra="1.6", machining="required", lay="=")); o.append(surface_finish(X + 25, Y + 75, ra="3.2", machining="any")); o.append(surface_finish(X + 45, Y + 75, machining="prohibited"))
    o.append(weld_symbol(X - 6, Y + 95, X + 4, Y + 87, arrow_side="fillet", other_side="fillet", size="5", length_pitch="50-100", all_around=True, field=True, tail="GMAW"))
    o.append(weld_symbol(X - 6, Y + 118, X + 4, Y + 110, arrow_side="vee", size="6", contour="flush"))
    o.append(weld_symbol(X - 6, Y + 141, X + 4, Y + 133, arrow_side="bevel", other_side="square", size="4"))
    yy = Y + 160
    for i, k in enumerate(WELD_GLYPHS):
        cx = X + 2 + i * 7.6; o.append(f'<line class="d" x1="{cx-3}" y1="{yy}" x2="{cx+3}" y2="{yy}"/>'); o += _weld_glyph(k, cx, yy, 4, above=False)
        o.append(_txt(cx, yy + 9, k, 1.6, font=TEXT_FONT))
    o.append("</svg>"); open(path_svg, "w").write("\n".join(o))
    if render_png and shutil.which("inkscape"):
        subprocess.run(["inkscape", path_svg, "--export-type=png", "--export-dpi=130", "--export-filename=" + path_svg[:-4] + ".png"], capture_output=True, timeout=300)
    return path_svg

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "gdt_proof_sheet.svg")
    print(proof_sheet(out))
