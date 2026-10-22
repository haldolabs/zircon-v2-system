# TOOL_CHANGES — record of every tool you modified or added in this run

No source checkout under `~/zircon/src/` was modified: every gap met in this run was closed in the Python layer, in
the project's own `tools/` directory. Nothing here adds network access.

| Tool / repo | Branch · commit | What was missing | What was added | How tested | Deliverable depends on it? |
|---|---|---|---|---|---|
| `tools/render_povray.py` (V1 helper) | n/a (project file) | **Bug:** after `chdir` into the scene's directory it still passed the *relative* `+I`/`+O` paths, so any call with a relative output path died with `Fatal error in parser: Cannot parse input` (V1 only ever called it with same-directory paths). | `+I` is now the scene's basename and `+O` an absolute path. | all four V2 renders + the 36-frame turntable rendered after the fix; before it, 0 of 3 | yes — every POV-Ray image in 02_design and 06_cam |
| `tools/render_povray.py` | n/a | no way to show a second object (a card stack) registered to the part | `--extra STL:COLOR` (repeatable): extra meshes get the part's exact placement transform; `paper` colour added | `media/raytrace/tab_v2_loaded_24cards.png` shows the FEA-deformed keeper holding 24 cards | yes — the "final design under load" render |
| `tools/build_site.py` | n/a | title hard-coded to V1 | title → V2 | site built, index links verified | cosmetic |
| `03_fea/export_deformed.py` (new) | n/a | no path from a CalculiX `.frd` to a renderable deformed surface | extracts the outer boundary faces of the C3D10 mesh (faces owned by one tet), displaces them by U, writes a watertight STL + the matching card-stack STL | 52 010 faces, watertight; rendered | yes — loaded render |
| `03_fea/run_fea.py` (new, from `tools/fea_runner_example.py`) | n/a | V1's runner prescribed a displacement line; this part's physics is a self-equilibrated force loop | force-based loop (F/2 on each pad line, −F on the rib face), unit-run compliance, per-case re-solve, arm-only stress mask | hand calc agrees within 12 % on force, 1 % on stress (v2) | yes |
| `06_cam/gen_gcode.py` (new, from V1's generator) | n/a | V1's toolpaths were hand-written rectangles; a free-form profile with fillets needs offset paths and rest machining | shapely-derived centreline paths (profile ⊕ r), 2-tool rest machining by (void − T1 sweep) ⊕ r clipping, tab lifts on the straight top edge, Fanuc-safe comments kept | `tests/run_tests.py` (8 checks) + CAMotics 3D | yes |
| `02_design/check_profile.py` (new) | n/a | nothing checked machinability at the CAD stage (V1 found its saw problem only when writing G-code) | morphological opening of the void by the tool disk; red = unreachable | 0.02 mm² on both versions; caught the first weave topology's throat (see 02_design) | yes (design gate) |
| `tools/camotics_check.py`, `tools/gdt_symbols.py`, `tools/vf2.ini` | — | used unchanged (tool table rewritten in `06_cam/tests/tool.tbl` for the three V2 tools) | — | — | — |

Known gaps **not** closed (recorded per §7 of the environment contract):
- FreeCAD 1.0 still cannot write semantic GD&T into STEP AP242; the drawing carries graphical GD&T (PDF/SVG) and the
  STEP is AP214. Same status as V1.
- No machine-specific Haas post: the program is hand-formatted Fanuc-style and verified with LinuxCNC's `rs274`, which
  does not enforce Haas-specific syntax (G53 moves, G98/G81 are standard; `M6` tool-change behaviour was not simulated).

## Added after the V2 run (2026-10-22, owner request): `V2 Tool Library/`
Downloaded by explicit owner instruction, *outside* the V2 benchmark's no-network contract, as input for a **V3** run:
RobbJack's ISO 13399 master catalog (JSON/CSV/manifest) and Fusion `.tools`, all 45 downloadable vendor libraries from
Autodesk's CAM tool index (`cam.autodesk.com/tools/download.php?name=<path>`; 7 entries fail server-side and are
listed), Autodesk's tooling JSON schema, and the Pocket NC starter libraries. `collection.py` merges them into one
normalized ISO 13399-named table (148,412 tools, 33 vendors); `catalog.py` exports FreeCAD CAM tool bits, and `collection.py` also writes a FreeCAD 1.0 tool library (`freecad/V3_starter_quarter_eighth`, 1,669 bits, all verified to load headlessly). SHA-256
manifest of every raw file in `V2 Tool Library/MANIFEST.sha256`. No V2 deliverable depends on it.
