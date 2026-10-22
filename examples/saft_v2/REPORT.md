# Automatic Factory Testing V2

**The problem:** loose index cards on a desk (0.127 mm thick, written on both sides) must be grouped in stacks of up to
24 and moved as a group, with a device that is one piece, passive and simple to make. **The ask:** the full engineering
pipeline — brainstorm, CAD with an iteration, FEA, release drawing with GD&T, RFQ and shop quote, CNC strategy with
tested G-code, ray-traced renders and animations — on the open-source Zircon v1 toolchain, nothing leaving this
machine. **The result:** `SAFT-V2-TAB`, a one-piece machined aluminium *weave* keeper that holds one card as surely as
twenty-four, is cut in a single setup with no saw, and whose every stage is reproducible from the scripts in this folder.

![loaded](02_design/media/raytrace/tab_v2_loaded_24cards.png)

## The part in one paragraph
A 73.6 × 15.7 × 12.7 mm bar of 6061-T6 cut as one 2D profile through 1/2 in plate, 26.8 g. A 1.1 × 46 mm flexure arm
carries a tooth with two pads on one plane and an 8.4 mm notch between them; from the floor, inside that notch, a 1.6 mm
rib stands **0.25 mm proud of the pad plane**. Cards weave over the rib and under the pads, so the rest gap is
*negative* without any cut — the thing no slit clip can do, because no kerf on this toolchain is thinner than a card.
One card is held by its own bending at 0.9 N; a 24-card stack lifts the arm 3.3 mm and is clamped at 8 N (13× its
weight). A 30° lead-in makes the push-on ~9 N. The 46 mm arm is the handle and the ID tab (six dice dimples × six
anodize colours = 36 groups).

## Walk the pipeline
| Stage | Folder | What is in it | Verified by |
|---|---|---|---|
| 1 Brainstorm | [01_brainstorm/](01_brainstorm/brainstorm.html) | 10 quantified requirements, the kerf-vs-card-thickness table that rules out every slit clip, 9 concepts, Pugh matrix → offset-tooth weave; series-spring model of the weave (`sizing.py`) | the clamp/holding table is re-derived by the FEA |
| 2 Design | [02_design/](02_design/design_iteration.html) | parametric FreeCAD build (`build_tab.py`), v1 and v2 STEP/STL, exact sections, **machinability proof** (`check_profile.py`), renders, turntables, the loaded render | FreeCAD solid validity; 0.02 mm² of unreachable void |
| 3 FEA | [03_fea/](03_fea/fea_report.html) | Gmsh C3D10 → CalculiX, force-loop load model, 2 versions × 4 stacks, stress heat-field animations, FEA-deformed STL | force within 12 % and stress within 1 % of the hand calc |
| 4 Drawing / RFQ | [04_drawings/](04_drawings/RFQ.html) | A3 release drawing with GD&T + 5:1 weave detail (SVG + PDF), true-arc DXF, RFQ with group-ID table | every callout read back on the preview |
| 5 Quote | [05_quote/](05_quote/quote.html) | shop profile, quote builder, 6 priced scenarios | cycle time from the G-code tests |
| 6 CAM | [06_cam/](06_cam/cam_strategy.html) | one-setup strategy, setup sheet, generated OP10 program (3 tools), 8-check test rig, CAMotics 3D sim, kerf animation | rs274 parse, VF-2 envelope, 2D kerf sim (0.0007 mm max gouge, 0.003 mm Hausdorff), CAMotics (0.10 mm), cycle 269 s |

Open [index.html](index.html) for a thumbnail index of every file; every `.md` has an `.html` twin.

## Headline numbers
| | v1 (first pass) | **v2 (released)** |
|---|---|---|
| Arm | 1.2 × 42, R1.7 root | **1.1 × 46, R3 root, pocket floor dropped 2 mm** |
| Clamp force, 1 / 12 / 24 cards | 1.4 / 6.8 / 12.6 N | **0.9 / 4.3 / 8.0 N** |
| Holding ÷ stack weight (μ 0.3 est.) | 59× / 25× / 21× | **37× / 16× / 13×** (R2 asks 5×) |
| Max von Mises at 24 cards | 213 MPa (SF 1.30) | **160 MPa (SF 1.72; 3.1 in 7075)** |
| Max von Mises at 30 cards (overload) | 262 MPa (SF 1.05) | **198 MPa (SF 1.40; 2.5 in 7075)** |
| Tooth tilt at 24 cards | 6.0° | 5.7° |
| Setups / ops | 1 / 1 | **1 / 1** (V1 clip: 2 / 2 incl. a slitting saw) |
| OP10 cycle | — | **269 s** (T1 46, T2 206, T3 4) |
| Quote, 24 pcs, 1 / 4 colours | — | **$30.18 / $42.93** per part (V1: $35.75 / $48.50) |
| Quote, 100 pcs, 1 / 6 colours | — | **$17.26 / $22.36** per part (V1: $17.22 / $22.32) |

## What the pipeline found (the honest part)
1. **A kerf cannot be thinner than a card, so a slit clip cannot hold a small group.** The 1/32 in saw that made V1's
   gap holds nothing below 7 index cards; wire EDM, 3. That single table decided the concept: the preload has to come
   from geometry (a rib 0.25 mm above the pads, inside a notch), not from a cut. The resulting part has no slit, no
   saw and no second setup — V1's whole manufacturing problem is gone.
2. **The first weave topology was unmachinable and the CAD script now proves machinability before anything else.**
   With the tooth dipping into a floor notch, the 30° lead-in overhung a floor finger and left a throat no Ø3.175 tool
   could enter. Inverting it (rib on the floor, notch in the tooth) fixed it, and `check_profile.py` (morphological
   opening of the void by the tool disk) now sits between CAD and everything downstream. V1 discovered its equivalent
   problem only while writing G-code.
3. **v1's stress problem was the arm section, not the fillet.** The FEA put Kt at 1.1 for the R1.7 root; 213 MPa at
   24 cards and 262 at 30 came from a 1.2 mm arm 42 mm long. v2 is thinner and longer (stress ∝ t/L²), which cost
   36 % of the clamp force and 4 mm of handle and bought SF 1.72 / 1.40. The weave itself was not touched.
4. **The load model matters more than the mesh.** V1 learned not to prescribe a displacement on a strip; V2 prescribes
   none: the stack is a lever balanced on the rib, so the pads carry F/2 each and the rib −F — a self-equilibrated loop
   with the floor rail in it. That answered an open question for free: the floor's share of the compliance is 0 %
   (the lower body is 9–11 mm deep, not the 4 mm rail the brainstorm assumed).
5. **The tooth tilts ~6° at 24 cards and the cards dip into the notch.** A cantilever's end rotates; the stack leaves
   the mouth kinked by that angle. Cosmetic, binder clips do it too, but the renders can't show it and the first
   article should look at it. A parallelogram flexure would hold the tooth level at the same stress and was rejected
   only because it needs two 0.6 mm arms.
6. **G-code tests and the 3D simulation agree with the CAD to the discretisation:** 0.0007 mm maximum gouge, 0.003 mm
   Hausdorff in the 2D kerf simulation; 0.10 mm (< 1 voxel) in CAMotics with all 16 probes passing. The test rig
   itself needed two fixes before it was right (a tab zone counted as uncut wall; a bounding box that joined the two
   tab footprints) — both are rig bugs, recorded in the script history, not program bugs.
7. **Cost (R10: ≤ $20 at 24, ≤ $10 at 100) is missed, by 1.5× and 1.7×.** One setup cut V1's fixed cost almost in half,
   but the 1/8 in end mill slotting 2.4 m through 12.7 mm plate makes machine time the biggest per-part line
   (~$8.70). The quote names the fix (a 3/16 in tool for the 3.8 mm channel, 1/8 in only for the 3.4 mm features).
8. **Two carried-over tools had to be fixed or extended** (`TOOL_CHANGES.md`): the POV-Ray helper could not render from
   a relative output path at all, and it could not show a second object — the loaded render above is the FEA-deformed
   surface with a 24-card stack, exported by a new script.
9. **Estimates that remain estimates:** card modulus (3 GPa), paper-on-anodize friction (0.30), card mass (1.55 g).
   Holding margins are 7–37×, so a 2× error in any of them changes no conclusion; R4 (no card damage, ≤ 1 % strain at
   the rib) is a functional-test item on the drawing, not a proven number.
10. **Fatigue:** 160 MPa at 24 cards is above 6061-T6's endurance limit; estimated life ~10⁵ cycles, 50× R9's
    2 000. 7075-T6 (+$1.50/part) makes it unlimited and is the recommended alloy for keepers that live full.

## Media
| | |
|---|---|
| ![hero](02_design/media/raytrace/tab_v2_povray_blue.png) | ![fea](03_fea/media/fea_v2_24_cards.gif) |
| ![cam](06_cam/media/op10_sim.gif) | ![toolpaths](06_cam/media/toolpaths.png) |
| ![drawing](04_drawings/preview.png) | ![camotics](06_cam/tests/camotics/sim_stock_povray.png) |
| ![cycles](02_design/media/raytrace/tab_v2_cycles_blue.png) | ![principle](01_brainstorm/media/weave_principle.png) |
| <video src="02_design/media/raytrace/tab_v2_povray_blue_turntable.mp4" controls></video> | <video src="03_fea/media/fea_v2_30_cards.mp4" controls></video> |

MP4 versions sit next to each GIF. Ray-traced images: POV-Ray (hero, raw iso, v1 red, loaded) and Blender Cycles (blue hero, black iso).

## Reproduce everything
```bash
export QT_QPA_PLATFORM=offscreen; CAE=~/miniconda3/envs/cae/bin/python
cd 01_brainstorm && $CAE sizing.py && cd ..
cd 02_design && SAFT_VERS="v1 v2" freecadcmd build_tab.py && $CAE check_profile.py && $CAE render.py \
   && $CAE ../tools/render_povray.py v2/SAFT-V2-TAB_v2.stl media/raytrace/tab_v2_povray_blue.png --color anodize-blue --turntable 36 && cd ..
cd 03_fea && $CAE run_fea.py v1 v2 && $CAE animate_fea.py v2 24_cards v2 1_card v2 30_cards v1 24_cards \
   && $CAE export_deformed.py v2 24_cards && cd ..
cd 02_design && $CAE ../tools/render_povray.py ../03_fea/v2/tab_24_cards_deformed.stl media/raytrace/tab_v2_loaded_24cards.png --extra ../03_fea/v2/cards_24_cards.stl:paper && cd ..
cd 06_cam && $CAE gen_gcode.py && (cd tests && $CAE run_tests.py && $CAE ../../tools/camotics_check.py camotics/spec.json) && $CAE animate_cam.py && cd ..
cd 04_drawings && $CAE make_drawing.py && freecadcmd export_dxf.py && cd ..
cd 05_quote && /usr/bin/python3 build_quote.py && cd ..
/usr/bin/python3 tools/build_site.py
```
Tool versions: FreeCAD 1.0.0, Gmsh 4.15.2, CalculiX 2.23, LinuxCNC rs274 2.9.4, CAMotics 1.3 (camsim), POV-Ray 3.7,
Blender 4.3.2, shapely 2.2, trimesh 5.1.1, inkscape, pandoc.

## Against the Zircon v1 benchmark rows
| Row | Exercised by |
|---|---|
| DFM review and redesign | brainstorm §"kerf vs card", the topology inversion, v1→v2 |
| Machine capability check | `check_profile.py` (tool reach), T2 envelope test, 4×D reach note |
| Release drawing with GD&T | 04_drawings (graphical GD&T; AP242 semantic PMI still not writable from FreeCAD 1.0) |
| RFQ-to-quote | 04_drawings/RFQ.md → 05_quote |
| 3D-to-CAM, CAM programming | 06_cam, derived from the exact section, one setup |
| Tool changes | 3 tools, rest machining, tool table for rs274 |
| Tool modification | TOOL_CHANGES.md (Python layer only) |
