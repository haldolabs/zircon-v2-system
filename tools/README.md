# tools/ — verified helpers carried over from the V1 run

Use, improve, or ignore; record what you did in `../TOOL_CHANGES.md`. All paths assume `~/miniconda3/envs/cae/bin/python`
unless noted. Everything here ran on this host on 2026-10-15.

| File | What it does | Run |
|---|---|---|
| `build_site.py` | every `.md` under the project → styled `.html` twin + `index.html` with media thumbnails | `/usr/bin/python3 build_site.py` (system python, uses pandoc) |
| `gdt_symbols.py` | GD&T / surface-finish / AWS weld symbol library for script-drawn SVG drawings; `proof_sheet()` renders every glyph with the fonts on this host | `/usr/bin/python3 gdt_symbols.py` → `gdt_proof_sheet.svg/.png` |
| `svg_drawing_example.py` | the V1 A3 release drawing generator (3 views, dims, FCFs, notes, title block, PDF via inkscape) — a template, hard-coded to the clip | `/usr/bin/python3 svg_drawing_example.py` (needs a `02_design/v2` tree) |
| `fea_runner_example.py` | Gmsh (C3D10) + CalculiX static run, hand-calc comparison, JSON results — template with the line-BC lesson built in | `python fea_runner_example.py v1 v2` |
| `animate_fea_example.py` | von Mises heat-field animation (GIF/MP4/PNG) from CalculiX `.frd` + `.inp` | `python animate_fea_example.py v2 24_sheets` |
| `gcode_tests_example.py` | 5-part G-code test rig: rs274 parse, envelope vs `vf2.ini`, 2.5D kerf sim vs CAD, Op20 analytics, cycle time | `python gcode_tests_example.py` (expects `../SAFT-V1-CLIP_OP10.nc` layout) |
| `animate_cam_example.py` | animates the kerf simulation; Op20 setup diagram | `python animate_cam_example.py` |
| `camotics_check.py` | **3D voxel material-removal check**: writes a `.camotics` project, runs `camsim`, compares the stock STL to a CAD target by sections + ray probes | `python camotics_check.py spec.json` (spec format in the docstring) |
| `render_raytrace.py` | Blender Cycles product render (+ `--paper N`, `--turntable N`) | `blender -b -P render_raytrace.py -- --stl x.stl --out x.png --color anodize-blue` |
| `render_povray.py` | POV-Ray render (~5 s/frame), `--up y\|z`, `--turntable N` | `python render_povray.py x.stl x.png --color raw --up z` |
| `vf2.ini`, `tool.tbl` | Haas VF-2 travel model + tool table for `rs274` | used by the test rig |

Machine-specific numbers (travels, work offsets, cutter sizes) live in `vf2.ini` and the example scripts' headers; change
them for a different machine rather than editing the logic.
